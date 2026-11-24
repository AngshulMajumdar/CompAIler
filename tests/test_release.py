import json
from pathlib import Path
import pytest
from compailer.runtime import check,validate_source,execute_wasi
from compailer.engine import run,validate_tests
from compailer.function_model import replace_function
from compailer.syntax import functions

GOOD='#include <stdio.h>\nint main(void){int n;if(scanf("%d",&n)!=1)return 1;printf("%d\\n",n+1);return 0;}\n'
TESTS=[{'input':'4\n','output':'5\n'},{'input':'-2\n','output':'-1\n'}]

def test_wasi_execution(tmp_path):
    r=check(GOOD,tmp_path,'wasi',TESTS)
    assert r['passed'],r

def test_no_host_filesystem(tmp_path):
    source='#include <stdio.h>\nint main(void){FILE *f=fopen("/etc/passwd","r");puts(f?"BAD":"DENIED");return 0;}\n'
    assert check(source,tmp_path,'wasi',[{'input':'','output':'DENIED'}])['passed']

def test_fuel_exhaustion(tmp_path):
    r=check('int main(void){volatile int n=0;while(1)n++;return 0;}',tmp_path,'wasi',[{'input':'','output':''}])
    assert r['compiled'] and not r['passed']
    assert r['tests'][0]['returncode']!=0

@pytest.mark.parametrize('source',[
 '#include "/etc/passwd"\nint main(void){return 0;}',
 '#define H </etc/passwd>\n#include H\nint main(void){return 0;}',
 '#inc\\\nlude "/etc/passwd"\nint main(void){return 0;}',
 '#include_next <stdio.h>\nint main(void){return 0;}',
 'int main(void){__asm__(".incbin /etc/passwd");return 0;}',
 '%:include "/etc/passwd"\nint main(void){return 0;}',
])
def test_reject_unsafe_compilation(source):
    with pytest.raises(ValueError):validate_source(source)

def test_release_and_manifest(tmp_path):
    r=run(GOOD,'Increment input.',TESTS,tmp_path)
    assert r['passed'] and r['unchanged'] and r['new_model_calls']==0
    assert (tmp_path/'corrected.c').read_text()==GOOD
    assert (tmp_path/'program.wasm').exists()
    with pytest.raises(ValueError,match='new work directory'):
        run(GOOD,'Different spec',TESTS,tmp_path)

def test_failure_withholds_release(tmp_path):
    # Replay a structurally valid but wrong CPU proposal, with no way to satisfy contradictory tests.
    from compailer import local_search,dependency_search
    old1=local_search.POLICY['maximum_rounds'];old2=dependency_search.POLICY['maximum_rounds']
    local_search.POLICY['maximum_rounds']=0;dependency_search.POLICY['maximum_rounds']=0
    source='int main(void){return 0;}'
    cache=tmp_path/'cache';cache.mkdir()
    (cache/'original.c').write_text(source);(cache/'repaired.c').write_text(source)
    (cache/'report.json').write_text(json.dumps({'history':[]}))
    try:
        r=run(source,'Print impossible output.',[{'input':'','output':'not printed'}],tmp_path/'out',proposal_cache=cache)
        assert not r['passed']
        assert not (tmp_path/'out/corrected.c').exists()
        assert not (tmp_path/'out/program.wasm').exists()
        assert (tmp_path/'out/candidate.c').exists()
    finally:
        local_search.POLICY['maximum_rounds']=old1;dependency_search.POLICY['maximum_rounds']=old2

def test_signatures_and_boundaries():
    source='int helper(int n){/* } */return n;}\nint main(void){return helper(0);}'
    assert [f['name'] for f in functions(source)]==['helper','main']
    with pytest.raises(ValueError,match='signature'):
        replace_function(source,'helper','int helper(long n){return n;}')

@pytest.mark.parametrize('tests',[[],[{'input':'x'}],[{'input':1,'output':'x'}]])
def test_require_behavioral_tests(tests):
    with pytest.raises(ValueError):validate_tests(tests)


def test_output_limit(tmp_path):
    source='#include <stdio.h>\nstatic char b[65536];\nint main(void){for(int i=0;i<20;i++)fwrite(b,1,sizeof b,stdout);return 0;}\n'
    r=check(source,tmp_path,'wasi',[{'input':'','output':''}])
    assert r['compiled'] and not r['passed']
    assert len(r['tests'][0]['stdout'])<=1024*1024
    assert r['tests'][0]['returncode']!=0


def test_search_repairs_failed_program_in_subprocess(tmp_path):
    # Real worker processes must start cleanly after the parent initialized WASI.
    import subprocess,sys
    source='#include <stdio.h>\nint main(void){printf("%d\\n", 1 + 1);return 0;}\n'
    cache=tmp_path/'cache';cache.mkdir()
    for name in ['original.c','repaired.c']:(cache/name).write_text(source)
    (cache/'report.json').write_text(json.dumps({'history':[]}))
    (tmp_path/'source.c').write_text(source)
    (tmp_path/'intent.txt').write_text('Print the integer three.')
    (tmp_path/'tests.json').write_text(json.dumps([{'input':'','output':'3\n'}]))
    result=subprocess.run([sys.executable,'-m','compailer',str(tmp_path/'source.c'),'--spec',str(tmp_path/'intent.txt'),
        '--tests',str(tmp_path/'tests.json'),'--proposal-cache',str(cache),'--work-dir',str(tmp_path/'work'),
        '-o',str(tmp_path/'result.wasm')],capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stdout+result.stderr
    report=json.loads((tmp_path/'work/report.json').read_text())
    assert report['passed'] and not report['unchanged'] and report['new_model_calls']==0
