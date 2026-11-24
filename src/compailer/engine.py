"""Shared model, expression-search, dependency-search and validation pipeline."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from .runtime import check,validate_source
from .syntax import functions,c_tokens
from .function_model import FunctionModel,repair as model_repair
from .local_search import function_pool,repair as local_search
from .dependency_search import repair as dependency_search
from .models import download

def signatures(source):
    return [(f['name'],[t[0] for t in c_tokens(f['signature'])]) for f in functions(source)]

def validate_tests(tests):
    if not isinstance(tests,list) or not tests or len(tests)>200:
        raise ValueError('Supply between 1 and 200 input/output tests')
    for t in tests:
        if not isinstance(t,dict) or not all(isinstance(t.get(k),str) for k in ('input','output')):
            raise ValueError('Each test must have string input and output fields')
        if any(len(t[k].encode())>65536 for k in ('input','output')):
            raise ValueError('Each test input and output must fit in 64 KB')

def run(source,requirement,tests,output,compiler='wasi',model=None,proposal_cache=None,extra_tests=None):
    validate_source(source); validate_tests(tests)
    if not isinstance(requirement,str) or not requirement.strip() or len(requirement)>20000:
        raise ValueError('Provide a behavior specification of at most 20,000 characters')
    extra_tests=extra_tests or []
    if extra_tests: validate_tests(extra_tests)
    all_tests=tests+extra_tests
    validate_tests(all_tests)
    wanted=dict(signatures(source)); output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    # Never reuse partial search checkpoints for different inputs or configurations.
    manifest={'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'requirement':requirement,
              'tests':tests,'extra_tests':extra_tests,'compiler':compiler,'model':str(model),
              'proposal_cache':str(proposal_cache)}
    m=output/'input_manifest.json'
    if m.exists() and json.loads(m.read_text())!=manifest: raise ValueError('Use a new work directory for different inputs')
    m.write_text(json.dumps(manifest,indent=2)); (output/'original.c').write_text(source)
    for n in ('program','program.wasm','corrected.c','report.json'): (output/n).unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix='compailer-baseline-') as tmp:
        baseline=check(source,Path(tmp),compiler,all_tests)
    calls=0
    if baseline['passed']:
        selected=source
    else:
        if proposal_cache:
            cache=Path(proposal_cache)
            if (cache/'original.c').read_text()!=source: raise ValueError('Proposal cache source mismatch')
            model_report=json.loads((cache/'report.json').read_text())
            if not all(e['request']['prompt'].startswith('Program behavior:\n'+requirement+'\n') for e in model_report['history']):
                raise ValueError('Proposal cache requirement mismatch')
            model_source=(cache/'repaired.c').read_text()
        else:
            path=Path(model) if model else download()
            print('Loading CPU-only model',flush=True)
            llm=FunctionModel(path)
            try: model_report=model_repair(llm,source,requirement,tests,compiler,output/'model_stage')
            finally: llm.llm.close()
            calls=model_report['calls']; model_source=(output/'model_stage/repaired.c').read_text()
            (output/'model_stage/program').unlink(missing_ok=True)
        pool=function_pool(source,model_report)
        pool={n:[code for code in variants if signatures(code)==[(n,wanted[n])]] for n,variants in pool.items()}
        print('Searching local expressions',flush=True)
        local_search(source,model_source,pool,tests,compiler,output/'local_search')
        seed=(output/'local_search/repaired.c').read_text()
        print('Searching dependency transactions',flush=True)
        dependency_search(source,seed,pool,all_tests,compiler,output/'dependency_search')
        selected=(output/'dependency_search/repaired.c').read_text()
    if signatures(selected)!=signatures(source): raise ValueError('Final function signature guard failed')
    with tempfile.TemporaryDirectory(prefix='compailer-final-') as tmp:
        final=check(selected,Path(tmp),compiler,all_tests)
        if final['passed']:
            shutil.copy2(Path(tmp)/'program',output/('program.wasm' if compiler=='wasi' else 'program'))
            (output/'corrected.c').write_text(selected)
    (output/'candidate.c').write_text(selected)
    report={'passed':final['passed'],'compiled':final['compiled'],'tests_passed':sum(t['passed'] for t in final['tests']),
            'test_count':len(all_tests),'new_model_calls':calls,'cached_model_proposals':bool(proposal_cache),
            'unchanged':selected==source,'gpu_layers':0,'backend':compiler,'final':final,
            'scope':'All supplied tests must pass; this is not a proof for unseen inputs.'}
    (output/'report.json').write_text(json.dumps(report,indent=2))
    return report
