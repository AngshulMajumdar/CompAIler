"""CPU compiler/test-guided search around original and local-model function proposals."""
import concurrent.futures
import multiprocessing
import difflib
import os
import hashlib
import json
import math
from pathlib import Path
import re
import tempfile
import time
from .runtime import check
from .syntax import functions,c_tokens

POLICY={'version':1,'workers':int(os.environ.get('COMPAILER_WORKERS', '4')),'beam_width':3,'maximum_rounds':16,
        'numeric_constants':[0,1,2,3,4,5,10],'heldout_feedback':False,
        'operators':'comparison, arithmetic, assignment, member, literal swap, call deletion, model function crossover'}
_tests=None;_compiler=None
def worker_init(tests,compiler):
    global _tests,_compiler
    _tests=tests;_compiler=compiler

def fitness(report):
    if not report['compiled']:return (-1,-1,-1,-1,-1.0)
    passed=sum(t['passed'] for t in report['tests']);valid=0;prefix=0;matches=0;loss=0.0
    for t in report['tests']:
        valid+=t['returncode']==0
        expected=t['expected'].split();actual=t['stdout'].split()
        for a,b in zip(expected,actual):
            if a!=b:break
            prefix+=1
        matches+=sum(b.size for b in difflib.SequenceMatcher(None,expected,actual,autojunk=False).get_matching_blocks())
        loss+=abs(len(expected)-len(actual))
        for a,b in zip(expected,actual):
            if a==b:continue
            try:loss+=min(2.0,abs(int(a)-int(b))/(1+abs(int(a))))
            except ValueError:loss+=2.0
    return (passed,valid,prefix,matches,-round(loss,8))

def evaluate(source):
    with tempfile.TemporaryDirectory(prefix='aicc-search-') as tmp:
        try:r=check(source,Path(tmp),_compiler,_tests)
        except Exception as e:r={'compiled':False,'diagnostics':str(e),'tests':[],'passed':False}
    return fitness(r),r

def digest(source):return hashlib.sha256(source.encode()).hexdigest()

def function_pool(original,model_report):
    pool={f['name']:{f['text']} for f in functions(original)}
    for e in model_report['history']:
        raw=e['generation']['raw'];blocks=re.findall(r'```(?:c|C)?\s*\n(.*?)```',raw,re.S)
        code=(blocks[0] if len(blocks)==1 else raw).strip()
        try:
            fs=functions(code)
            if len(fs)==1 and fs[0]['name'] in pool and not code[:fs[0]['start']].strip() and not code[fs[0]['end']:].strip():
                pool[fs[0]['name']].add(code)
        except ValueError:pass
    return {k:sorted(v) for k,v in pool.items()}

def neighbors(source,pool):
    fs=functions(source)
    members=sorted({t[i+1][0] for f in fs for t in [c_tokens(f['text'])] for i in range(len(t)-1)
                    if t[i][0] in ['.','->'] and re.fullmatch(r'[A-Za-z_]\w*',t[i+1][0])})
    comparisons=['<','<=','>','>=','==','!='];arithmetic=['+','-','*','/','%'];compound=['=','+=','-=','*=']
    seen=set()
    def emit(start,end,new,kind,function):
        old=source[start:end]
        if old==new:return None
        changed=source[:start]+new+source[end:];h=digest(changed)
        if h in seen:return None
        seen.add(h)
        return changed,{'kind':kind,'function':function,'start':start,'end':end,'old':old,'new':new}
    for f in fs:
        name=f['name'];base=f['body']+1;body=source[base:f['end']-1];tokens=c_tokens(body)
        for code in pool.get(name,[]):
            try:
                replacement=functions(code)[0]
                if [t[0] for t in c_tokens(replacement['signature'])]!=[t[0] for t in c_tokens(f['signature'])]:continue
            except ValueError:continue
            item=emit(f['start'],f['end'],code,'function_crossover',name)
            if item:yield item
        for i,(token,a,b) in enumerate(tokens):
            alternatives=[]
            if token in comparisons:alternatives=comparisons
            elif token in compound:alternatives=compound
            elif token in arithmetic:alternatives=arithmetic
            elif token.isdigit():alternatives=[str(n) for n in POLICY['numeric_constants']]
            elif i and tokens[i-1][0] in ['.','->']:alternatives=members
            elif token in ["'('","')'","'['","']'","'{'","'}'"]:
                alternatives=["'('","')'","'['","']'","'{'","'}'"]
            for new in alternatives:
                item=emit(base+a,base+b,new,'token',name)
                if item:yield item
        # Parameter/coefficient permutation in return expressions; no output-derived literals.
        for m in re.finditer(r'\breturn\s+([^;{}]+);',body):
            nums=[t for t in c_tokens(m[1]) if t[0].isdigit()]
            for i,left in enumerate(nums):
                for right in nums[i+1:]:
                    if left[0]==right[0]:continue
                    expr=m[1];new=expr[:left[1]]+right[0]+expr[left[2]:right[1]]+left[0]+expr[right[2]:]
                    item=emit(base+m.start(1),base+m.end(1),new,'return_literal_swap',name)
                    if item:yield item
        # Delete standalone call statements; this removes duplicated effects or stray output.
        for i,t in enumerate(tokens):
            if not re.fullmatch(r'[A-Za-z_]\w*',t[0]) or i+1>=len(tokens) or tokens[i+1][0]!='(':continue
            if i and tokens[i-1][0] not in [';','{','}']:continue
            depth=0
            for j in range(i+1,len(tokens)):
                if tokens[j][0]=='(':depth+=1
                elif tokens[j][0]==')':
                    depth-=1
                    if depth==0:
                        if j+1<len(tokens) and tokens[j+1][0]==';':
                            item=emit(base+t[1],base+tokens[j+1][2],'','delete_call_statement',name)
                            if item:yield item
                        break

def repair(original,model_source,pool,tests,compiler,output):
    output.mkdir(parents=True,exist_ok=True);start=time.monotonic();cache={};trace=[]
    checkpoint=output/'checkpoint.json'
    if checkpoint.exists():
        saved=json.loads(checkpoint.read_text());assert saved['original_sha256']==digest(original)
        beam=saved['beam'];trace=saved['trace'];start_round=saved['round']+1
        for node in beam:cache[digest(node['source'])]=tuple(node['fitness'])
    else:
        worker_init(tests,compiler)
        beam=[]
        for label,source in [('local_model',model_source),('original',original)]:
            score,report=evaluate(source);cache[digest(source)]=score
            beam.append({'source':source,'fitness':score,'path':[],'seed':label})
        beam.sort(key=lambda n:tuple(n['fitness']),reverse=True);start_round=1
    best=beam[0];checked=0
    journal=output/'evaluations.jsonl'
    with concurrent.futures.ProcessPoolExecutor(mp_context=multiprocessing.get_context('spawn'), max_workers=POLICY['workers'],initializer=worker_init,initargs=(tests,compiler)) as workers:
        for round_number in range(start_round,POLICY['maximum_rounds']+1):
            if best['fitness'][0]==len(tests):break
            jobs=[];provenance=[];submitted=set()
            for parent_index,parent in enumerate(beam):
                for candidate,edit in neighbors(parent['source'],pool):
                    h=digest(candidate)
                    if h in cache or h in submitted:continue
                    submitted.add(h);jobs.append(candidate);provenance.append((parent_index,edit,h))
            print('SEARCH_ROUND',round_number,'candidates',len(jobs),'best',best['fitness'],flush=True)
            winners=list(beam)
            with journal.open('a') as log:
                for source,(parent_index,edit,h),(score,report) in zip(jobs,provenance,workers.map(evaluate,jobs,chunksize=8)):
                    checked+=1;cache[h]=score
                    log.write(json.dumps({'round':round_number,'sha256':h,'parent':digest(beam[parent_index]['source']),
                                          'edit':edit,'fitness':score,'compiled':report['compiled']})+'\n')
                    parent=beam[parent_index]
                    node={'source':source,'fitness':score,'seed':parent['seed'],'path':parent['path']+[edit]}
                    if score>tuple(best['fitness']):
                        best=node;(output/'current.c').write_text(source)
                        print('SEARCH_IMPROVED',checked,score,edit['kind'],edit['function'],flush=True)
                    winners.append(node)
                    winners=sorted(winners,key=lambda n:tuple(n['fitness']),reverse=True)[:POLICY['beam_width']]
            beam=winners;best=beam[0]
            trace.append({'round':round_number,'candidates':len(jobs),'best':best['fitness']})
            checkpoint.write_text(json.dumps({'original_sha256':digest(original),'round':round_number,'beam':beam,'trace':trace},indent=2))
            if not jobs:break
    worker_init(tests,compiler);score,final=evaluate(best['source'])
    (output/'repaired.c').write_text(best['source'])
    result={'policy':POLICY,'passed':final['passed'],'final':final,'seed':best['seed'],'edits':best['path'],
            'rounds':trace,'evaluated_this_session':checked,'seconds':round(time.monotonic()-start,3)}
    (output/'report.json').write_text(json.dumps(result,indent=2));return result
