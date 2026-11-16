import sys, os, json, hashlib, inspect, platform, importlib, site
from pathlib import Path
import numpy as np
import scipy
from scipy.fft import ifftn
import simrecon
from simrecon.reconstruction import known_parameters as kp
def identity(p):
    p=Path(p);b=p.read_bytes()
    return {"path":str(p),"resolved":str(p.resolve()),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
root=Path("/workspace/work/issue-120")
assert sys.version_info[:3]==(3,13,12) and __debug__ and sys.flags.optimize==0
assert Path(sys.prefix).resolve()==root/".venv"
assert Path(simrecon.__file__).resolve()==root/"src/simrecon/__init__.py"
mods=[importlib.import_module(n) for n in ("numpy._core._multiarray_umath","scipy.fft._pocketfft.pypocketfft","sitecustomize")]
paths=[sys.executable,str(root/".venv/pyvenv.cfg"),kp.__file__,str(root/"uv.lock"),str(root/"pyproject.toml")]
paths += [m.__file__ for m in mods]
paths += [str(p) for p in sorted((Path(sys.prefix)/"lib/python3.13/site-packages").glob("*.pth"))]
facts={"status":"METADATA_IMPORT_PROVENANCE_ONLY_NO_FFT_OR_ARRAY_WORKLOAD","head":"f3db41747423786a7a49aadc428eaec0d03fdd5d","parent119":"2393e4a8473a4741902aca2aaa70b589bb33353a","python":sys.version,"executable":sys.executable,"prefix":sys.prefix,"platform":platform.platform(),"machine":platform.machine(),"byteorder":sys.byteorder,"debug":__debug__,"optimize":sys.flags.optimize,"dontwritebytecode":sys.dont_write_bytecode,"versions":{"numpy":np.__version__,"scipy":scipy.__version__},"module_origins":{m.__name__:m.__file__ for m in mods},"ifftn_signature":str(inspect.signature(ifftn)),"ifftn_documentation":ifftn.__doc__,"files":[identity(p) for p in dict.fromkeys(paths)],"sys_path":sys.path,"environment":{k:os.environ.get(k) for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","BLIS_NUM_THREADS","PYTHONPATH","PYTEST_PLUGINS","PYTHONDONTWRITEBYTECODE","PYTHONMALLOC","MALLOC_ARENA_MAX","LD_PRELOAD","NPY_ARRAY_API","SCIPY_ARRAY_API")},"limits":"No FFT/numerical qualification, backend workspace/internal precision/native error theorem, physical admission, or measurement. Imported file origins are not a loaded-ABI or universal dispatch certificate; actual calls and finite controls remain separate."}
print(json.dumps(facts,indent=2))
