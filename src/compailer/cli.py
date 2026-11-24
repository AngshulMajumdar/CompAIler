import argparse
import json
import os
from pathlib import Path
import shutil
import sys
from . import __version__
from .engine import run
from .models import download,default_path
from .runtime import check
import tempfile

def main():
    if sys.argv[1:]==['model','download']:
        print(download()); return
    if sys.argv[1:]==['doctor']:
        with tempfile.TemporaryDirectory() as tmp:
            result=check('#include <stdio.h>\nint main(void){puts("ok");return 0;}\n',Path(tmp),'wasi',[{'input':'','output':'ok\n'}])
        print(json.dumps({'version':__version__,'cpu_only':True,'model_exists':default_path().exists(),
            'wasi_compiler':shutil.which(os.environ.get('COMPAILER_WASI_CC','clang-14')),
            'wasi_smoke_passed':result['passed'],'diagnostics':result['diagnostics'],
            'native_compiler':shutil.which('tcc') or shutil.which('gcc'),'bubblewrap':shutil.which('bwrap')},indent=2))
        raise SystemExit(0 if result['passed'] else 2)
    p=argparse.ArgumentParser(description='CompAIler: CPU model-assisted C repair and compilation. Also: compailer doctor; compailer model download')
    p.add_argument('--version',action='version',version=__version__)
    p.add_argument('source',type=Path)
    p.add_argument('--spec','--requirement-file',dest='spec',type=Path,required=True)
    p.add_argument('--tests',type=Path,required=True)
    p.add_argument('--extra-tests',type=Path)
    p.add_argument('--work-dir',type=Path,default=Path('compailer-output'))
    p.add_argument('-o','--output',type=Path,default=Path('a.wasm'),help='Validated binary destination; default a.wasm')
    p.add_argument('--backend',choices=['wasi','native'],default='wasi')
    p.add_argument('--compiler',help='Native C compiler executable (default tcc, then gcc)')
    p.add_argument('--model',type=Path,help='Existing GGUF; otherwise checksum-verified auto-download')
    p.add_argument('--proposal-cache',type=Path,help='Explicit reproduction mode using prior proposals for these exact inputs')
    a=p.parse_args()
    # Invalidate a prior deliverable before attempting a new build.
    if a.output.resolve()==a.source.resolve(): p.error('Binary output must differ from source')
    if a.output.exists(): p.error('Output already exists; choose a new binary destination')
    compiler='wasi' if a.backend=='wasi' else (a.compiler or shutil.which('tcc') or shutil.which('gcc') or 'tcc')
    try:
        report=run(a.source.read_text(),a.spec.read_text(),json.loads(a.tests.read_text()),a.work_dir,
            compiler=compiler,model=a.model,proposal_cache=a.proposal_cache,
            extra_tests=json.loads(a.extra_tests.read_text()) if a.extra_tests else None)
        if report['passed']:
            a.output.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(a.work_dir/('program.wasm' if compiler=='wasi' else 'program'),a.output)
        print(json.dumps({k:v for k,v in report.items() if k!='final'},indent=2))
        raise SystemExit(0 if report['passed'] else 1)
    except (ValueError,OSError,RuntimeError,KeyError) as exc:
        print('CompAIler: '+str(exc),file=sys.stderr); raise SystemExit(2)
