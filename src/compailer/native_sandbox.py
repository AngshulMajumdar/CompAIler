import ctypes
import ctypes.util
import errno
import os
import resource
import shutil
import subprocess
import tempfile

def limits():
    resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

def network_filter(fd):
    lib = ctypes.CDLL(ctypes.util.find_library('seccomp') or 'libseccomp.so.2')
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    lib.seccomp_export_bpf.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.seccomp_release.argtypes = [ctypes.c_void_p]
    ctx = lib.seccomp_init(0x7fff0000)  # default ALLOW
    if not ctx:
        raise RuntimeError('Cannot initialize network filter')
    try:
        for name in ('socket', 'socketpair', 'connect', 'bind', 'listen', 'accept', 'accept4',
                     'ptrace', 'mount', 'umount2', 'bpf', 'io_uring_setup'):
            num = lib.seccomp_syscall_resolve_name(name.encode())
            if num >= 0 and lib.seccomp_rule_add(ctx, 0x00050000 | errno.EPERM, num, 0):
                raise RuntimeError('Cannot configure network filter')
        if lib.seccomp_export_bpf(ctx, fd):
            raise RuntimeError('Cannot export network filter')
    finally:
        lib.seccomp_release(ctx)
    os.lseek(fd, 0, os.SEEK_SET)

def execute(binary, stdin):
    """Fail closed unless bubblewrap and seccomp isolation are available."""
    if not shutil.which('bwrap'):
        raise RuntimeError('bubblewrap is required to execute generated programs')
    with tempfile.TemporaryFile() as filt, tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        network_filter(filt.fileno())
        cmd = ['bwrap', '--die-with-parent', '--new-session', '--unshare-user', '--unshare-pid',
               '--unshare-ipc', '--unshare-uts', '--clearenv', '--setenv', 'PATH', '/usr/bin',
               '--ro-bind', '/usr', '/usr', '--ro-bind', '/lib', '/lib',
               '--ro-bind', '/lib64', '/lib64', '--proc', '/proc', '--dev', '/dev',
               '--tmpfs', '/tmp', '--ro-bind', str(binary.resolve()), '/program',
               '--chdir', '/tmp', '--seccomp', str(filt.fileno()), '/program']
        try:
            result = subprocess.run(cmd, input=stdin, text=True, stdout=out, stderr=err,
                                    pass_fds=(filt.fileno(),), timeout=5, preexec_fn=limits)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = -999
        out.seek(0); err.seek(0)
        return {'returncode': code, 'stdout': out.read(1048576).decode(errors='replace'),
                'stderr': err.read(1048576).decode(errors='replace')}
