# H3 cuFFT Xt documentary feasibility

**Documentary scope only; no runtime/backend activation or final SCI acceptance.**
The note `backend-documentary-note.md`, SHA
`5ba05641f3ce4def1824159a15cb3f832ff44300dc310ae9e4a3b02f6eb4263b`,
was exposed before this author's independent inspection. No blind or independent
review verdict is claimed. This author separately inspected saved primary-source
responses to assess the technical wording rather than taking note conclusions as
scientific proof. No refetch, package, adapter, device probe or execution occurred.

## Versioned versus live evidence

The saved NVIDIA release tables distinguish **CUDA 13.0 Update 3 / cuFFT
12.0.0.61 / runtime 13.0.96**, corresponding Linux toolkit driver 580.126.20,
from observed live **CUDA 13.5 / cuFFT 12.5.0.14 / runtime 13.5.37**, driver
branch R620. CUDA 13.x minor compatibility from 580 does not certify every
feature/JIT/platform; live 13.5 new features/platforms require appropriate
R620-or-later support. These are different documentary anchors, not measured
installed versions or an upgrade recommendation.

Primary local records: `fetch-04-archive-13-0-3-primary.json`, returned
turn676349view2 L22–110; `fetch-01-live-docs.json`, turn999015view2 L18–94.
Both reside under `/workspace/work/campaign/evidence/114/backend-documentary-preparation-1/`.
NVIDIA URLs:
[archive release](https://docs.nvidia.com/cuda/archive/13.0.3/cuda-toolkit-release-notes/index.html),
[observed live release](https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html).

## Conditional boundary adopted for the draft

| Constraint | Primary excerpt and author disposition |
| --- | --- |
| Half hardware/size/layout | Archive cuFFT half section, fetch05 turn890988view1 L156–170: SM75+, power-of-two sizes, one GPU, no real-side R2C/C2R strides, vendor limit “more than 4 billion elements.” Live fetch09 turn666022view2 L156–169 clarifies real-element size for R2C/C2R. Actual boundary arithmetic and any W plan remain unqualified. |
| Rank/batch/API/types | Archive fetch05 turn890988view2 L1332–1360: Xt batched ranks 1/2/3, explicit n/embeds/strides/distances; NULL embeds ignore advanced strides. Precision declarations must match; R2C uses R16F/C16F/C16F. Archive fetch06 turn665915view2 L2084–2097: XtExec uses GPU input/output. Exact plan/operands/ABI are not observed. |
| Paired storage | Archive half2 fetch04 turn676349view3 L10,62–70 and conversion fetch08 turn459075view1 L12–25 identify two half components and nearest-even conversion. This is insufficient to certify a host (...,2) view as a device complex ABI. Real/imaginary order, alignment/endian/copies remain future qualification, no adapter commissioned. |
| Layout side effects | Archive fetch05 turn890988view1 L154,188–193 requires Hermitian C2R input and padded in-place real layout. Follow-up bounded inspection located out-of-place C2R input overwrite in the saved live cuFFT excerpt, fetch02 turn412700view3 L201. It is a live-document boundary, not an archived-fetch06 claim or observed runtime behavior. |
| Normalization | Live cuFFT fetch07 turn551077view2 L2685–2691 says forward/inverse compose to element-count scaling. A future mapping must retain exact sign/axes/normalization and range behavior. No implicit rescaling is selected. |
| Planning/JIT/workspace | Archive fetch06 turn665915view1 L126–139 documents CPU/GPU planning intermediates and cached PTX JIT. Its 8× workspace description is specifically single/double, not a half bound. Live fetch07 turn551077view4 and fetch08 turn459075view6 document plan-specific workspace estimation and caller allocation. No concrete workspace/peak/time is known. |
| Synchronization | Archive runtime fetch09 turn666022view0 L216–249 distinguishes pageable/pinned/direction staging and asynchronous kernel launches. Timing must await actual completion and include transfer/staging/context costs; host dispatch duration and host RSS cannot substitute for GPU elapsed/device peak. |
| Version-specific correctness | Archive release fetch05 turn890988view0 L495–496 names size1 strided R2C/C2R half/bfloat16 issue. Live release fetch07 turn551077view3 L747–758 records fix in 13.1, so it is not presented as unresolved in 13.5. Live13.5 L704–711 separately warns of needed workspace aliasing input/output; 13.2 L738–742 requires NVRTC for LTO kernels. No actual affected plan is assumed. |
| Dependency/platform | Live cuFFT fetch08 turn459075view5 L467–477 specifies compatible nvJitLink/NVRTC for LTO callbacks, no callback selected. Archive Linux guide fetch08 turn459075view3 L70–84 labels its table Update2 with Ubuntu24.04.x x≤3; it does not qualify the study Ubuntu24.04.5 container/GPU/compiler/kernel/driver. |
| Licensing/portability | Archive EULA fetch04 turn676349view1 L68–88 and current EULA fetch09 turn666022view1 L180–243 support conditional SDK redistribution, NVIDIA-GPU application scope and listed cuFFT/runtime/static dependencies. They are proprietary SDK terms with third-party notices, not an open-source grant or compliance verdict. Legacy Mac listing establishes no current Mac execution. |

Primary URLs:
[archive cuFFT](https://docs.nvidia.com/cuda/archive/13.0.3/cufft/index.html),
[live cuFFT](https://docs.nvidia.com/cuda/cufft/index.html),
[half2](https://docs.nvidia.com/cuda/archive/13.0.3/cuda-math-api/cuda_math_api/struct____half2.html),
[half conversion](https://docs.nvidia.com/cuda/archive/13.0.3/cuda-math-api/cuda_math_api/group__CUDA__MATH____HALF__MISC.html),
[sync](https://docs.nvidia.com/cuda/archive/13.0.3/cuda-runtime-api/api-sync-behavior.html),
[Linux](https://docs.nvidia.com/cuda/archive/13.0.3/cuda-installation-guide-linux/index.html),
[archive EULA](https://docs.nvidia.com/cuda/archive/13.0.3/eula/index.html),
[live EULA](https://docs.nvidia.com/cuda/eula/index.html).

Vendor half-execution declarations are documentary feasibility evidence, stronger
than an output dtype alone. They do not audit every butterfly multiplier,
accumulator or workspace precision. Six acquisition axes do not imply a rank6
FFT: transform axes and batches need a future exact qualified mapping. No GPU
purchase/install/wrapper/benchmark or new H3 experiment is authorized here.

## Access, date and source-integrity limits

The saved provenance dates access to 2026-11-17 UTC, with sequence retained and no
invented per-fetch wall clocks. Archive cuFFT publication/update date is unknown.
Archive EULA displays January7,2025; live EULA January26,2026. Archive13.0.3 runtime
sync page itself displays v13.0.2 / October9,2025. URL version is not a substitute
for displayed content version. Search crawl/publication labels are not vendor
release dates. fetch02 failed archive13.5 URL reads do not prove nonexistence;
missing literal matches/search-only sample results are not opened proof.

Direct curl returned CONNECT403/exit22, zero download and no complete HTML. The
saved headers/transfer record and supported-reader excerpts preserve that failure.
Hashes identify local response/excerpt JSON and failed-transfer metadata, not
complete unreceived NVIDIA HTML, vendor authenticity or executable bytes. No
access bypass or unnecessary refetch occurred.

## Matrix disposition

“H3 optional cuFFT Xt: vendor documents restricted GPU half transforms for the
identified CUDA/cuFFT versions. Conditional documentary feasibility only. Actual
device/driver/ABI/plan/internal-precision qualification, numerical usefulness,
synchronized runtime and host/device memory remain UNOBSERVED/UNMEASURED.”

The currently supplied study has no authorized observed GPU route; actual GPU
absence is not established. This is no native-half CPU, full-workflow, speed,
RAM-fit or H1/H2 negative conclusion. A different fresh final SCI must assess the
exact sources, version/currency limits and eventual whole-report wording. This
author's preparation is not selfacceptance.
