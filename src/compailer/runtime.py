"""Compiler guardrails and capability-limited test execution."""
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess
import tempfile

HEADERS = set('stdio stdlib string ctype limits math stdint stdbool stddef errno inttypes assert float time'.split())
MAX_OUTPUT = 1024 * 1024

def validate_source(source):
    if len(source.encode()) > 100_000:
        raise ValueError('Source exceeds 100 KB')
    if '??' in source or '\x00' in source:
        raise ValueError('Trigraphs and NUL bytes are unsupported')
    # Splice first, then remove comments while preserving line structure.
    source = re.sub(r'\\\r?\n', '', source)
    source = re.sub(r'/\*[\s\S]*?\*/|//[^\n]*', lambda m: '\n' * m.group().count('\n') or ' ', source)
    if re.search(r'\b(?:asm|__asm|__asm__|_Pragma|__has_include)\b|##|%:|\.incbin', source):
        raise ValueError('Assembly and dynamic preprocessor operations are unsupported')
    for line in source.splitlines():
        if not line.lstrip().startswith('#'):
            continue
        m = re.match(r'\s*#\s*(\w+)\b(.*)', line)
        if not m:
            raise ValueError('Unsupported preprocessor directive')
        directive, rest = m.groups()
        if directive == 'include':
            header = re.fullmatch(r'\s*<([a-z0-9]+)\.h>\s*', rest)
            if not header or header[1] not in HEADERS:
                raise ValueError('Only documented standard angle-bracket headers are supported')
        elif directive not in {'define','undef','if','ifdef','ifndef','elif','else','endif','error','line'}:
            raise ValueError('Unsupported preprocessor directive: ' + directive)

def compile_limits():
    resource.setrlimit(resource.RLIMIT_CPU, (20,20))
    resource.setrlimit(resource.RLIMIT_AS, (1024**3,1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16*1024**2,16*1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0,0))

def execute_wasi(binary, stdin):
    import wasmtime as w
    cfg=w.Config(); cfg.consume_fuel=True
    cfg.cranelift_opt_level='none'
    engine=w.Engine(cfg); store=w.Store(engine)
    store.set_fuel(50_000_000)
    store.set_limits(memory_size=256*1024**2, instances=1, memories=1, tables=1, table_elements=10000)
    stdout=bytearray(); stderr=bytearray(); overflow=[False]
    def capture(target):
        def write(data):
            if len(target)+len(data)>MAX_OUTPUT:
                overflow[0]=True
                return -1
            target.extend(data)
            return len(data)
        return write
    code=0
    with tempfile.TemporaryDirectory(prefix='compailer-stdin-') as tmp:
        inp=Path(tmp)/'stdin'; inp.write_text(stdin)
        wasi=w.WasiConfig(); wasi.argv=['program']; wasi.stdin_file=str(inp)
        wasi.stdout_custom=capture(stdout); wasi.stderr_custom=capture(stderr)
        # Intentionally no preopens, inherited environment, sockets, or host imports.
        store.set_wasi(wasi); linker=w.Linker(engine); linker.define_wasi()
        module=None
        try:
            module=w.Module.from_file(engine,str(binary))
            instance=linker.instantiate(store,module)
            instance.exports(store)['_start'](store)
        except w.ExitTrap as exc:
            code=exc.code
        except (w.Trap,w.WasmtimeError,RuntimeError) as exc:
            code=-1; stderr.extend(str(exc).encode()[:4096])
        finally:
            store.close()
            linker.close()
            if module is not None: module.close()
            engine.close()
            cfg.close()
    if overflow[0]:
        code=-1; stderr.extend(b'Output limit exceeded')
    return {'returncode':code,'stdout':stdout.decode(errors='replace'),'stderr':stderr.decode(errors='replace')}

# Native programs execute in the prototype's bubblewrap+seccomp sandbox.
from .native_sandbox import execute as execute_native

def check(source,work,compiler,tests):
    work=Path(work); work.mkdir(parents=True,exist_ok=True)
    binary=work/'program'; binary.unlink(missing_ok=True)
    report={'compiled':False,'diagnostics':'','tests':[],'passed':False}
    try:
        validate_source(source)
        path=work/'candidate.c'; path.write_text(source)
        wasi=compiler=='wasi'
        cc=os.environ.get('COMPAILER_WASI_CC','clang-14') if wasi else compiler
        if not shutil.which(cc):
            raise RuntimeError('Compiler unavailable: '+cc)
        cmd=[cc,'-Wall','-Werror',str(path.resolve()),'-o',str(binary.resolve()),'-lm']
        if wasi:
            cmd[1:1]=['--target=wasm32-wasi','--sysroot='+os.environ.get('COMPAILER_WASI_SYSROOT','/usr'),'-Wl,--max-memory=268435456','-Wl,-z,stack-size=8388608']
        if wasi: cmd.insert(-1, '-Wno-unused-function')
        with tempfile.TemporaryFile() as log:
            built=subprocess.run(cmd,stdout=log,stderr=log,cwd=work,
                env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'TMPDIR':str(work.resolve())},
                timeout=25,preexec_fn=compile_limits)
            log.seek(0); report['diagnostics']=log.read(65536).decode(errors='replace')[-6000:]
        report['compiled']=built.returncode==0
        if not report['compiled']: return report
        for case in tests:
            actual=(execute_wasi if wasi else execute_native)(binary,case['input'])
            actual.update(input=case['input'],expected=case['output'],passed=actual['returncode']==0 and actual['stdout'].strip()==case['output'].strip())
            report['tests'].append(actual)
        report['passed']=bool(tests) and all(t['passed'] for t in report['tests'])
    except (ValueError,RuntimeError,OSError,subprocess.TimeoutExpired) as exc:
        report['diagnostics']+='\n'+str(exc)
    return report
