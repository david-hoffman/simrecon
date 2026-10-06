# OTF-CALIBRATION — private operation-time failure control

**Version 1.0.** Coordinator intake/testability decision within authorized K25, October 6, 2026. This is a declared production-caller boundary for tests, not a new public API, scientific operation or required transform backend.

The owned runtime module `simrecon._otf` provides a private callable `_transform(working_psf, origin_yx)`. The first argument is the operation's normalized float64 working array and the second is its validated origin tuple. Every valid call reaching transfer computation uses this collaborator. All transform algorithms and fast paths live behind it; NumPy FFT, SciPy FFT and independently correct alternatives remain possible. This statement adds no exact floating-point sum-one promise or intermediate normalization tolerance.

The collaborator produces the complete complex transfer in the contract's shifted signed-bin order. Tests call public `prepare_otf` and replace the private collaborator solely to control operation-time faults; they assert invocation so K25 evidence cannot pass without exercising the fault. No test calls the collaborator as a replacement for public-entry behavior.

A `FloatingPointError` raised at this declared numerical boundary maps to `SimreconError` code `otf_transform_failure`. A correctly shaped nonfinite transfer is also rejected as `otf_transform_failure`. An injected `MemoryError` or explicitly unrelated `LookupError` propagates. These are the controlled examples of the existing K25 guarantees; they select no unspecified broad catch policy. All rejection paths retain K08/K26 input preservation and caller arithmetic policy/no handled arithmetic RuntimeWarning. Invalid result shape/dtype is not a new public-input scenario.

A/B may read this declaration before checkpoint acceptance. Do not infer a seam from implementation; none exists at declaration. C owns its runtime definition within `src/simrecon/_otf.py`. The private name creates no caller compatibility or public export promise. The scientific contract K01–K29, public signature and allowed algorithms remain unchanged.
