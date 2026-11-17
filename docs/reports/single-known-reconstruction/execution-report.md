# Opt-in single-storage known reconstruction

`reconstruct_known(..., precision="single-mixed-v1")` accepts independently declared complex64 prepared bands and returns complex64 filtered quadratures with a signed float32 image. Coordinates and image accumulation remain float64. Double remains the default; preparation, parameter search and full-workflow integration are separate stages. See the [usage guide](../../usage/c-known-reconstruction.md) and [scientific contract](../../contracts/single-known-reconstruction-v1.md).

The completed execution table contains three fresh processes per mode for each of four fixed 16-voxel reconstructions. EE01–03 have nine conditionally qualified single observations inside their predeclared fixture envelopes. Double has a separate unqualified accuracy certificate; EE04 tests storage and dtype only. These results establish neither physical recovery nor general FFT internal precision.

All 24 valid observations ran on clean revision `5bb025839608c55c8caf97d215dd057f401c1707`, tree `d6911fbf44ae4f5e664a8145d6aa27b4615cef50`, after the accepted120 parent. Two additional EE03-double-r2 attempts failed the unchanged 50 ms missing-RSS rule and remain ineligible, even though their numerical children completed and exited 0. Their raw failures and completed diagnosis are preserved. All numerical children, private namespaces and proxies are closed.

| Case | Mode | Call median [range], ms | Retained backing, bytes | Terminal peak range, KiB |
| --- | --- | --- | --- | --- |
| EE01 | double | 4.534606 [4.221918, 4.689908] | 9272 | 80636–81564 |
| EE01 | single | 3.955800 [3.350841, 12.385269] | 8920 | 80704–81100 |
| EE02 | double | 1.395332 [1.250752, 2.344090] | 7272 | 80728–81056 |
| EE02 | single | 2.968492 [2.896372, 3.139725] | 6920 | 80844–81128 |
| EE03 | double | 5.190523 [4.880171, 7.193265] | 9280 | 81088–81472 |
| EE03 | single | 4.443795 [3.800229, 7.042478] | 8928 | 80928–81112 |
| EE04 | double | 13.101660 [12.658911, 15.253548] | 6343840 | 87212–87392 |
| EE04 | single | 11.460553 [8.925589, 12.627797] | 6343488 | 87144–87572 |

The matched setup deliberately retains both valid input schemas, raw/source arrays and original transfer records in both modes. EE04 adds an ordinary large Fortran-order transfer table and its legitimate old-double reshape copies. The observed retained-payload difference is 352 bytes in each fixed case; it does not predict full-workflow memory savings. Profiling costs remain in timing/RSS, the cgroup is shared, and three tiny trials provide no general speed or peak-memory benefit claim. Native terminal high-water is kernel-reported usage through child exit; whether every bootstrap/pre-exec peak survives exec remains unresolved. It is distinct from sampled RSS, call timing and retained payload. No baseline subtraction supplies an isolated algorithm peak.

Following assembly, two test modules received narrow standard-library typing corrections, accepted by fresh blind B at checkpoint `7629dc8ef7df9de0d2a31ee727e0490f6f80b479`. Their runtime assertions, call arguments and scientific references retain their prior scope. Canonical types and all three affected cases passed. The archived source set and `current_source_matches` fields describe the assembly-time source set; measurements were neither rerun nor relabeled as the later publication revision. Exact final verification and fresh D assess that later candidate separately. A subsequent reporting-only change explicitly sets Coverage exclusions to an empty list, so typing-only source is included under the existing zero-exclusion gate. It changes no numerical code, dependency, test oracle or archived material. Final D also assesses this third source-material delta; the original measurement and assembly-time source labels remain unchanged.

The portable [raw archive](execution-runs.json) retains all 61 actual attempts (35 qualification and 26 formal), emitted fixed artifacts, explicit absences, source versions and finite prerequisite bodies. Its `ASSEMBLED_RAW_UNVERIFIED` status identifies file-only assembly; exact publication-commit verification and independent acceptance are recorded separately. The technical tables below retain exact reference widths, error bounds, signed values and raw outcome classifications.

<details>
<summary>Technical execution tables and exact error records</summary>

# EE113 execution evidence

ASSEMBLED RAW / UNVERIFIED. Independent scientific, code/protocol and final gate review remain required.

| Case | Mode | Runtime observations | Eligible attempts | Call median seconds | Terminal median KiB / bytes | Retained median bytes |
| --- | --- | --- | --- | --- | --- | --- |
| EE01 | double | matched_three_runtime_observations | 3 | 0.004534606 | 80988 / 82931712 | 9272 |
| EE01 | single | matched_three_runtime_observations | 3 | 0.0039558 | 80980 / 82923520 | 8920 |
| EE02 | double | matched_three_runtime_observations | 3 | 0.001395332 | 80740 / 82677760 | 7272 |
| EE02 | single | matched_three_runtime_observations | 3 | 0.002968492 | 81040 / 82984960 | 6920 |
| EE03 | double | matched_three_runtime_observations | 3 | 0.005190523 | 81240 / 83189760 | 9280 |
| EE03 | single | matched_three_runtime_observations | 3 | 0.004443795 | 80936 / 82878464 | 8928 |
| EE04 | double | matched_three_runtime_observations | 3 | 0.01310166 | 87312 / 89407488 | 6343840 |
| EE04 | single | matched_three_runtime_observations | 3 | 0.011460553 | 87336 / 89432064 | 6343488 |

| Purpose / ID | Attempt | Disposition | Raw child classification | Runtime eligible |
| --- | --- | --- | --- | --- |
| formal / EE01-double-r1 | 1 | completed | complete | True |
| formal / EE01-single-r1 | 1 | completed | complete | True |
| formal / EE01-single-r2 | 1 | completed | complete | True |
| formal / EE01-double-r2 | 1 | completed | complete | True |
| formal / EE01-double-r3 | 1 | completed | complete | True |
| formal / EE01-single-r3 | 1 | completed | complete | True |
| formal / EE02-double-r1 | 1 | completed | complete | True |
| formal / EE02-single-r1 | 1 | completed | complete | True |
| formal / EE02-single-r2 | 1 | completed | complete | True |
| formal / EE02-double-r2 | 1 | completed | complete | True |
| formal / EE02-double-r3 | 1 | completed | complete | True |
| formal / EE02-single-r3 | 1 | completed | complete | True |
| formal / EE03-double-r1 | 1 | completed | complete | True |
| formal / EE03-single-r1 | 1 | completed | complete | True |
| formal / EE03-single-r2 | 1 | completed | complete | True |
| formal / EE03-double-r2 | 1 | failed | complete | False |
| formal / EE03-double-r2 | 2 | failed | complete | False |
| formal / EE03-double-r2 | 3 | completed | complete | True |
| formal / EE03-double-r3 | 1 | completed | complete | True |
| formal / EE03-single-r3 | 1 | completed | complete | True |
| formal / EE04-double-r1 | 1 | completed | complete | True |
| formal / EE04-single-r1 | 1 | completed | complete | True |
| formal / EE04-single-r2 | 1 | completed | complete | True |
| formal / EE04-double-r2 | 1 | completed | complete | True |
| formal / EE04-double-r3 | 1 | completed | complete | True |
| formal / EE04-single-r3 | 1 | completed | complete | True |
| qualification / F01 | 1 | completed | complete | False |
| qualification / F01 | 2 | material_invalidated | missing | False |
| qualification / F01 | 3 | completed | complete | False |
| qualification / F01 | 7 | completed | complete | False |
| qualification / F02 | 4 | completed | complete | False |
| qualification / F02 | 8 | completed | complete | False |
| qualification / F03 | 5 | completed | complete | False |
| qualification / F03 | 9 | completed | complete | False |
| qualification / F04 | 6 | completed | complete | False |
| qualification / F04 | 10 | failed | missing | False |
| qualification / F04 | 11 | completed | complete | False |
| qualification / E01 | 1 | completed | complete | False |
| qualification / E01 | 2 | completed | complete | False |
| qualification / O01 | 1 | completed | complete | False |
| qualification / O01 | 5 | completed | complete | False |
| qualification / O02 | 2 | completed | complete | False |
| qualification / O02 | 6 | completed | complete | False |
| qualification / O03 | 3 | completed | complete | False |
| qualification / O03 | 7 | completed | complete | False |
| qualification / O04 | 4 | completed | complete | False |
| qualification / O04 | 8 | completed | complete | False |
| qualification / L01 | 1 | completed | complete | False |
| qualification / L01 | 8 | completed | complete | False |
| qualification / L02 | 2 | completed | complete | False |
| qualification / L02 | 9 | completed | complete | False |
| qualification / L03 | 3 | completed | expected_malformed_child_record | False |
| qualification / L03 | 10 | completed | expected_malformed_child_record | False |
| qualification / L04 | 4 | completed | complete | False |
| qualification / L04 | 11 | completed | complete | False |
| qualification / L05 | 5 | completed | complete | False |
| qualification / L05 | 12 | completed | complete | False |
| qualification / L06 | 6 | completed | complete | False |
| qualification / L06 | 13 | completed | complete | False |
| qualification / L07 | 7 | completed | complete | False |
| qualification / L07 | 14 | completed | complete | False |

| Formal ID / attempt | Accuracy qualified | Reference width | Absolute error upper | RMS enclosure | Signed extrema |
| --- | --- | --- | --- | --- | --- |
| EE01-double-r1 / 1 | False | 0 | 36262546800043596165392101288549017625531042045297/421249179814995007653896491905372694416278109676307661713829789696 | [62905489270421688591446183653149/730750818665451459101842416358141509827966271488, 125810978540843377182892367306299/1461501637330902918203684832716283019655932542976] | [9007198982152201/36028797018963968, 9007198982152201/36028797018963968] |
| EE01-single-r1 / 1 | True | 0 | 5755555034799907019847624396585387692204539157545/784637741399919628452316842796975177556794341050661470208 | [10720556332276687068824120341084204933573/1461501637330902918203684832716283019655932542976, 5360278166138343534412060170542102466787/730750818665451459101842416358141509827966271488] | [16777215/67108864, 16777215/67108864] |
| EE01-single-r2 / 1 | True | 0 | 5755555034799907019847624396585387692204539157545/784637741399919628452316842796975177556794341050661470208 | [10720556332276687068824120341084204933573/1461501637330902918203684832716283019655932542976, 5360278166138343534412060170542102466787/730750818665451459101842416358141509827966271488] | [16777215/67108864, 16777215/67108864] |
| EE01-double-r2 / 1 | False | 0 | 36262546800043596165392101288549017625531042045297/421249179814995007653896491905372694416278109676307661713829789696 | [62905489270421688591446183653149/730750818665451459101842416358141509827966271488, 125810978540843377182892367306299/1461501637330902918203684832716283019655932542976] | [9007198982152201/36028797018963968, 9007198982152201/36028797018963968] |
| EE01-double-r3 / 1 | False | 0 | 36262546800043596165392101288549017625531042045297/421249179814995007653896491905372694416278109676307661713829789696 | [62905489270421688591446183653149/730750818665451459101842416358141509827966271488, 125810978540843377182892367306299/1461501637330902918203684832716283019655932542976] | [9007198982152201/36028797018963968, 9007198982152201/36028797018963968] |
| EE01-single-r3 / 1 | True | 0 | 5755555034799907019847624396585387692204539157545/784637741399919628452316842796975177556794341050661470208 | [10720556332276687068824120341084204933573/1461501637330902918203684832716283019655932542976, 5360278166138343534412060170542102466787/730750818665451459101842416358141509827966271488] | [16777215/67108864, 16777215/67108864] |
| EE02-double-r1 / 1 | False | 0 | 0 | [0, 0] | [-52428801/4194304, 52428801/4194304] |
| EE02-single-r1 / 1 | True | 0 | 1/2097152 | [106690325430121035294974577624884401435611/365375409332725729550921208179070754913983135744, 426761301720484141179898310499537605742445/1461501637330902918203684832716283019655932542976] | [-25/2, 25/2] |
| EE02-single-r2 / 1 | True | 0 | 1/2097152 | [106690325430121035294974577624884401435611/365375409332725729550921208179070754913983135744, 426761301720484141179898310499537605742445/1461501637330902918203684832716283019655932542976] | [-25/2, 25/2] |
| EE02-double-r2 / 1 | False | 0 | 0 | [0, 0] | [-52428801/4194304, 52428801/4194304] |
| EE02-double-r3 / 1 | False | 0 | 0 | [0, 0] | [-52428801/4194304, 52428801/4194304] |
| EE02-single-r3 / 1 | True | 0 | 1/2097152 | [106690325430121035294974577624884401435611/365375409332725729550921208179070754913983135744, 426761301720484141179898310499537605742445/1461501637330902918203684832716283019655932542976] | [-25/2, 25/2] |
| EE03-double-r1 / 1 | False | 35/560942597178067176293051784856918376481692609150976 | 1447927738224234736094042461549601/93490432863011196048841964142819729413615434858496 | [5827537137866601669805558308625/730750818665451459101842416358141509827966271488, 11655074275733203339611116617251/1461501637330902918203684832716283019655932542976] | [-145199028522001/1125899906842624, 7509666208154027/72057594037927936] |
| EE03-single-r1 / 1 | True | 35/560942597178067176293051784856918376481692609150976 | 5094966381233800354132601204447626623829853/560942597178067176293051784856918376481692609150976 | [2324070003165886795907160981485037162881/365375409332725729550921208179070754913983135744, 9296280012663547183628643925940148651525/1461501637330902918203684832716283019655932542976] | [-1081817/8388608, 13987843/134217728] |
| EE03-single-r2 / 1 | True | 35/560942597178067176293051784856918376481692609150976 | 5094966381233800354132601204447626623829853/560942597178067176293051784856918376481692609150976 | [2324070003165886795907160981485037162881/365375409332725729550921208179070754913983135744, 9296280012663547183628643925940148651525/1461501637330902918203684832716283019655932542976] | [-1081817/8388608, 13987843/134217728] |
| EE03-double-r2 / 1 | unavailable / unqualified | unavailable | unavailable | unavailable | unavailable |
| EE03-double-r2 / 2 | unavailable / unqualified | unavailable | unavailable | unavailable | unavailable |
| EE03-double-r2 / 3 | False | 35/560942597178067176293051784856918376481692609150976 | 1447927738224234736094042461549601/93490432863011196048841964142819729413615434858496 | [5827537137866601669805558308625/730750818665451459101842416358141509827966271488, 11655074275733203339611116617251/1461501637330902918203684832716283019655932542976] | [-145199028522001/1125899906842624, 7509666208154027/72057594037927936] |
| EE03-double-r3 / 1 | False | 35/560942597178067176293051784856918376481692609150976 | 1447927738224234736094042461549601/93490432863011196048841964142819729413615434858496 | [5827537137866601669805558308625/730750818665451459101842416358141509827966271488, 11655074275733203339611116617251/1461501637330902918203684832716283019655932542976] | [-145199028522001/1125899906842624, 7509666208154027/72057594037927936] |
| EE03-single-r3 / 1 | True | 35/560942597178067176293051784856918376481692609150976 | 5094966381233800354132601204447626623829853/560942597178067176293051784856918376481692609150976 | [2324070003165886795907160981485037162881/365375409332725729550921208179070754913983135744, 9296280012663547183628643925940148651525/1461501637330902918203684832716283019655932542976] | [-1081817/8388608, 13987843/134217728] |
| EE04-double-r1 / 1 | False | storage only or unavailable | unavailable | unavailable | unavailable |
| EE04-single-r1 / 1 | False | storage only or unavailable | unavailable | unavailable | unavailable |
| EE04-single-r2 / 1 | False | storage only or unavailable | unavailable | unavailable | unavailable |
| EE04-double-r2 / 1 | False | storage only or unavailable | unavailable | unavailable | unavailable |
| EE04-double-r3 / 1 | False | storage only or unavailable | unavailable | unavailable | unavailable |
| EE04-single-r3 / 1 | False | storage only or unavailable | unavailable | unavailable | unavailable |

Unqualified EE01-double-r1 attempt 1: "unqualified: c128 FFT/scalar program requires separate justification".


Unqualified EE01-double-r2 attempt 1: "unqualified: c128 FFT/scalar program requires separate justification".


Unqualified EE01-double-r3 attempt 1: "unqualified: c128 FFT/scalar program requires separate justification".


Unqualified EE02-double-r1 attempt 1: "unqualified: c128 FFT/scalar program requires separate justification".


Unqualified EE02-double-r2 attempt 1: "unqualified: c128 FFT/scalar program requires separate justification".


Unqualified EE02-double-r3 attempt 1: "unqualified: c128 FFT/scalar program requires separate justification".


Unqualified EE03-double-r1 attempt 1: "unqualified: c128 FFT/scalar program requires separate justification".


Unqualified EE03-double-r2 attempt 1: "accuracy unavailable/unqualified: attempt runtime eligibility is not established; retained failure: outer_field_scope=category/cause retain first 512 characters; actual category characters=10; actual immediate-cause category characters=null\nexception[0].category=\"ValueError\"\nexception[0].message=\"actual controller closure facts\"\nexception[0].frame[0]=\"/workspace/work/issue-113/docs/reports/single-known-reconstruction/execution-driver.py\":1612:\"assemble\"\nexception[0].frame[1]=\"/workspace/work/issue-113/docs/" [retained first 512 of 772 characters; suffix unrecorded: presentation reason bound].


Unqualified EE03-double-r2 attempt 2: "accuracy unavailable/unqualified: attempt runtime eligibility is not established; retained failure: outer_field_scope=category/cause retain first 512 characters; actual category characters=10; actual immediate-cause category characters=null\nexception[0].category=\"ValueError\"\nexception[0].message=\"actual controller closure facts\"\nexception[0].frame[0]=\"/workspace/work/issue-113/docs/reports/single-known-reconstruction/execution-driver.py\":1612:\"assemble\"\nexception[0].frame[1]=\"/workspace/work/issue-113/docs/" [retained first 512 of 772 characters; suffix unrecorded: presentation reason bound].


Unqualified EE03-double-r2 attempt 3: "unqualified: c128 FFT/scalar program requires separate justification".


Unqualified EE03-double-r3 attempt 1: "unqualified: c128 FFT/scalar program requires separate justification".


Unqualified EE04-double-r1 attempt 1: "EE04 STORAGE/DTYPE ONLY".


Unqualified EE04-single-r1 attempt 1: "EE04 STORAGE/DTYPE ONLY".


Unqualified EE04-single-r2 attempt 1: "EE04 STORAGE/DTYPE ONLY".


Unqualified EE04-double-r2 attempt 1: "EE04 STORAGE/DTYPE ONLY".


Unqualified EE04-double-r3 attempt 1: "EE04 STORAGE/DTYPE ONLY".


Unqualified EE04-single-r3 attempt 1: "EE04 STORAGE/DTYPE ONLY".


All actual attempts, raw failures, aborted/material-invalidated/superseded records and explicit missing reasons are in the portable blob table and restore map. Local absolute paths are provenance only.

EE04 is storage/dtype only. Each double mode retains its separate unsupported c128 FFT/scalar certificate. Single envelopes remain conditional on actual material and same-child fenv. No universal benefit, physical accuracy, internal FFT precision, pristine cache or isolated algorithm peak is claimed.

Common setup retains raw, both q64/q32 declarations, noise, transfer input/seed/original/record, carriers/modulation, legitimate old template and independent new32 record in both modes; result is appended. Original F-order tables can cause legitimate old-double per-order reshape copies. Profiling costs remain in runtime/RSS.

Call timing, self cumulative snapshots, sole direct-child terminal wait4, sampled RSS/HWM, retained owner payload and ROOT whole-private-init closure are separate observations. No baseline subtraction supplies an algorithm peak.

Complete stage terms, interval-distance/far bounds, signal scale, cancellation conditions, pre/call-end/post snapshots, effective context/material/source identities and all raw arrays/streams are retained per attempt in execution-runs.json.

An over-budget child emits a complete observation_failed record on the same stdout where possible; parent interruption may leave partial JSON/unavailable suffix. Complete overflow transport is not promised, and overflow never qualifies.

</details>
