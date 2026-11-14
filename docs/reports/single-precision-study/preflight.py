"""SP112 read-only environment evidence; run only with granted Ubuntu interpreter."""
import contextlib
import hashlib
import io
import json
import os
import pathlib
import platform
import resource
import subprocess
import sys

import numpy as np
import scipy


def read(path):
    try:
        return pathlib.Path(path).read_text()
    except OSError as e:
        return str(e)


def command(args):
    p = subprocess.run(args, text=True, capture_output=True, timeout=10)
    return dict(argv=args, status=p.returncode, stdout=p.stdout, stderr=p.stderr)


def environment():
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        np.show_config()
        scipy.show_config()
    return dict(
        executable=sys.executable, python=sys.version, platform=platform.platform(),
        os_release=read('/etc/os-release'), numpy=np.__version__, scipy=scipy.__version__,
        numpy_file=np.__file__, scipy_file=scipy.__file__, backend=stream.getvalue(),
        threads={k: os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS']},
        allocator={k: os.environ.get(k) for k in ['LD_PRELOAD','PYTHONMALLOC','MALLOC_ARENA_MAX']},
        host_meminfo=read('/proc/meminfo'), cpu=read('/proc/cpuinfo').split('\n\n')[0],
        cpu_count=os.cpu_count(), cgroup={k:read('/sys/fs/cgroup/'+k) for k in ['memory.max','memory.current','memory.peak','memory.swap.max','memory.swap.current','cpu.max','pids.current']},
        proc_status=read('/proc/self/status'), pid=os.getpid(),
        git_head=command(['git','rev-parse','HEAD']), tree=command(['git','rev-parse','HEAD^{tree}']), dirty=command(['git','status','--porcelain=v1']),
        git_diff_sha256=hashlib.sha256(subprocess.run(['git','diff','--binary'],capture_output=True,check=True).stdout).hexdigest(),
        lock_sha256=hashlib.sha256(pathlib.Path('uv.lock').read_bytes()).hexdigest(),
        uv=command(['uv','--version']), shared_interference='exclusive coordinator window; unrelated host workload unknown',
        backend_workspace='unknown', allocator_version=platform.libc_ver(),
        resource_native=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        rss_native_unit='Linux KiB', rss_conversion=1024,
    )

if __name__ == '__main__':
    print(json.dumps(environment(), indent=2))
