"""Narrow post-study loaded FFT-module provenance, no precision/workspace theorem."""
import hashlib
import importlib
import json
import pathlib
import sys
import numpy as np
from scipy import fft
np.fft.rfft(np.zeros(4,dtype=np.float32))
fft.ifftn(np.zeros((2,2),dtype=np.complex64),norm='forward',workers=1)
rows=[]
for name in ['numpy.fft._pocketfft','numpy.fft._pocketfft_umath','scipy.fft._basic_backend','scipy.fft._duccfft','scipy.fft._duccfft.basic','scipy.fft._duccfft.helper']:
    try:
        m=importlib.import_module(name);p=pathlib.Path(m.__file__)
        rows.append(dict(module=name,file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),loaded=name in sys.modules))
    except Exception as e:rows.append(dict(module=name,error=type(e).__name__,message=str(e)))
print(json.dumps(dict(probe='one tiny NumPy rfft and SciPy ifftn, source/module provenance only',rows=rows,loaded_fft_modules=[k for k in sys.modules if k.startswith(('numpy.fft','scipy.fft'))],actual_internal_precision_workspace='unknown'),indent=2))
