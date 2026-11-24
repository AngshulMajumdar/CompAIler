"""CPU model repairs complete C functions; deterministic code handles integration."""
import os
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import time
from .runtime import check
from .syntax import functions,topology,context,c_tokens

POLICY={'version':1,'model':'Qwen2.5-Coder-7B-Instruct Q4_K_M','gpu_layers':0,'threads':int(os.environ.get('COMPAILER_THREADS', '4')),
        'context_tokens':8192,'seed':172,'temperature':0,'passes':1,'extra_retry_budget':3,
        'output':'one_complete_C_function','preserve_passing_scenarios':True,
        'accept_neutral_compiling_changes':True,'heldout_feedback':False}

def canonical(text):
    return re.sub(r'/tmp/aicc-function-[^/]+/candidate\.c','candidate.c',text)

def replace_function(source,name,raw):
    blocks=re.findall(r'```(?:c|C)?\s*\n(.*?)```',raw,re.S)
    if len(blocks)>1:raise ValueError('Expected one C block')
    code=(blocks[0] if blocks else raw).strip()
    emitted=functions(code)
    if len(emitted)!=1 or emitted[0]['name']!=name:raise ValueError('Expected only the assigned function')
    f=emitted[0]
    if code[:f['start']].strip() or code[f['end']:].strip():raise ValueError('Unexpected code outside function')
    original=functions(source);target=next(f for f in original if f['name']==name)
    tokens=lambda s:[t[0] for t in c_tokens(s)]
    if tokens(target['signature'])!=tokens(emitted[0]['signature']):raise ValueError('Function signature changed')
    revised=source[:target['start']]+code+source[target['end']:]
    after=functions(revised)
    if [f['name'] for f in after]!=[f['name'] for f in original]:raise ValueError('Function structure changed')
    for before,now in zip(original,after):
        if before['name']!=name and before['text']!=now['text']:raise ValueError('Another function changed')
    return revised

def passing(report):return {i for i,t in enumerate(report['tests']) if t['passed']}

def prompt_for(source,name,requirement,report,expanded=False,previous=None):
    fs=topology(source);by={f['name']:f for f in fs};target=by[name]
    decl,_,_=context(source,[name]);decl=re.sub(r'\n{3,}','\n\n',decl).strip()
    related=set(target['calls'])|{f['name'] for f in fs if name in f['calls']}
    interfaces='\n'.join(by[n]['signature']+';' for n in sorted(related))
    helpers=''
    if expanded:
        helpers='\nRead-only dependency bodies:\n'+'\n\n'.join(by[n]['text'] for n in sorted(related))[:3000]
    failures=[{'input':t['input'][:350],'expected':t['expected'][:350],
               'actual':t['stdout'][:350],'exit':t['returncode']} for t in report['tests'] if not t['passed']][:1]
    return ('Program behavior:\n'+requirement+'\nShared declarations:\n'+decl
       +'\nRelated function interfaces (do not implement these):\n'+interfaces+helpers
       +'\nAssigned function '+name+':\n```c\n'+target['text']+'\n```\n'
       +'Compiler diagnostics:\n'+canonical(report['diagnostics'][-1000:])
       +'\nVisible integration failure (other functions may also be faulty):\n'+json.dumps(failures)
       +('\nPrevious replacement failed:\n'+json.dumps(previous)[-1800:] if previous else '')
       +'\nCorrect the assigned function according to the stated program behavior. Check its conditions, '
        'bounds, arithmetic, state updates and return value. Fix every actual fault in this function. '
        'If it is correct, reproduce it unchanged. Preserve the EXACT function signature and all interfaces. '
        'Return ONLY this one COMPLETE C function in a ```c block. No JSON, patches, explanations, '
        'includes, globals or other function definitions. Do not hardcode example answers.')

class FunctionModel:
    def __init__(self,path):
        from llama_cpp import Llama
        self.llm=Llama(model_path=str(path),n_ctx=POLICY['context_tokens'],n_threads=POLICY['threads'],
                       n_threads_batch=POLICY['threads'],n_batch=256,n_gpu_layers=0,seed=POLICY['seed'],verbose=False)
    def propose(self,prompt,target,number):
        self.llm.set_seed(POLICY['seed']+number)
        length=len(self.llm.tokenize(target.encode()));maximum=min(1600,max(256,2*length+96))
        start=time.monotonic();print('MODEL_BEGIN',number,'prompt_chars',len(prompt),'max_output',maximum,flush=True)
        r=self.llm.create_chat_completion(messages=[{'role':'system','content':
            'You correct one small C function. Output only its complete C definition with the original signature.'},
            {'role':'user','content':prompt}],temperature=0,max_tokens=maximum)
        g={'raw':r['choices'][0]['message']['content'] or '', 'usage':r.get('usage'),
           'finish_reason':r['choices'][0]['finish_reason'],'max_output_tokens':maximum,
           'seconds':round(time.monotonic()-start,3)}
        print('MODEL_END',number,g['seconds'],g['usage'],flush=True);return g

def ordered_names(source,baseline):
    fs=functions(source);names=[f['name'] for f in fs]
    if not baseline['compiled']:
        line=re.search(r'candidate.c:(\d+)',baseline['diagnostics'])
        if line:
            pos=sum(len(x) for x in source.splitlines(True)[:int(line[1])-1])
            culprit=next((f['name'] for f in fs if f['start']<=pos<f['end']),None)
            if culprit:names.remove(culprit);names.insert(0,culprit)
    return names

def repair(model,source,requirement,tests,compiler,output,control=False):
    output.mkdir(parents=True,exist_ok=True);original=source;history=[];extra=POLICY['extra_retry_budget']
    with tempfile.TemporaryDirectory(prefix='aicc-function-') as tmp:
        work=Path(tmp);best=check(source,work,compiler,tests);baseline=best
        names=ordered_names(source,best)
        # Control probes reproduce the previous protocol: review one region of a passing input.
        if control:names=names[:1]
        for name in names:
            previous=None
            for retry in range(2):
                number=len(history)+1
                target=next(f for f in functions(source) if f['name']==name)
                prompt=prompt_for(source,name,requirement,best,expanded=bool(retry),previous=previous)
                request={'name':name,'retry':retry,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'prompt':prompt}
                path=output/f'call_{number:03d}.json'
                if path.exists():
                    stored=json.loads(path.read_text());assert stored['request']==request
                    generation=stored['generation']
                else:
                    generation=model.propose(prompt,target['text'],number)
                    path.write_text(json.dumps({'request':request,'generation':generation},indent=2))
                entry={'request':request,'generation':generation,'accepted':False,'check':None}
                try:
                    if generation['finish_reason']=='length':raise ValueError('Truncated function')
                    candidate=replace_function(source,name,generation['raw']);entry['candidate']=candidate
                    result=check(candidate,work,compiler,tests);entry['check']=result
                    if not result['compiled']:entry['reason']='compiler_rejected'
                    elif not passing(best).issubset(passing(result)):entry['reason']='regression_rejected'
                    else:
                        entry.update(accepted=True,reason='unchanged' if candidate==source else 'accepted')
                        source=candidate;best=result
                except (ValueError,KeyError,TypeError) as e:
                    entry.update(reason='structure_rejected',error=str(e))
                history.append(entry);path.write_text(json.dumps(entry,indent=2));(output/'current.c').write_text(source)
                print('FUNCTION',number,name,'retry',retry,entry['reason'],'visible',len(passing(best)),flush=True)
                if entry['accepted'] or retry or not extra:break
                extra-=1
                result=entry.get('check')
                previous={'reason':entry['reason'],'error':entry.get('error'),
                          'diagnostics':canonical(result['diagnostics'][-1200:]) if result else '',
                          'replacement':generation['raw'][-1600:],
                          'failed_outputs':[{'input':t['input'][:250],'expected':t['expected'][:250],
                              'actual':t['stdout'][:250],'exit':t['returncode']}
                              for t in result['tests'] if not t['passed']][:1] if result else []}
            # Visit all functions even if visible examples pass before the end of the pass.
        final=check(source,work,compiler,tests)
        if final['passed']:shutil.copy2(work/'program',output/'program')
    (output/'original.c').write_text(original);(output/'repaired.c').write_text(source)
    report={'policy':POLICY,'baseline':baseline,'final':final,'history':history,'calls':len(history),
            'function_count':len(functions(original)),'control_probe':control}
    (output/'report.json').write_text(json.dumps(report,indent=2));return report
