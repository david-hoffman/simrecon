# Q5 tiny vector expectations — unexecuted source

Each literal canonical byte string is in tiny-hash-vectors-v1.json. Expected identity is (literal name, literal shape, literal canonical dtype, SHA256(literal canonical bytes)); actual accepted streaming identity must equal both that tuple and the actual frozen RM84 identity result. All three chunk controls (16,31,64B) run actual identity and finite helpers. Frozen public-value fingerprints compare source/layout/endian values to an independent tiny array from literal canonical bytes; cross-vector relations below require type/shape/signed-zero distinctions. No workflow or peak claim.

| Vector | Source encoding | Mode | Expected shape | Canonical encoding | Finite |
| --- | --- | --- | --- | --- | --- |
| width-b1 | \|b1 | direct | [2] | \|b1 | true |
| width-i1 | \|i1 | direct | [2] | \|i1 | true |
| width-u1 | \|u1 | direct | [2] | \|u1 | true |
| width-i2 | <i2 | direct | [2] | <i2 | true |
| width-i4 | <i4 | direct | [2] | <i4 | true |
| width-i8 | <i8 | direct | [2] | <i8 | true |
| width-u2 | <u2 | direct | [2] | <u2 | true |
| width-u4 | <u4 | direct | [2] | <u4 | true |
| width-u8 | <u8 | direct | [2] | <u8 | true |
| width-f2 | <f2 | direct | [2] | <f2 | true |
| width-f4 | <f4 | direct | [2] | <f4 | true |
| width-f8 | <f8 | direct | [2] | <f8 | true |
| width-f16 | <f16 | direct | [2] | <f16 | true |
| width-c8 | <c8 | direct | [1] | <c8 | true |
| width-c16 | <c16 | direct | [1] | <c16 | true |
| scalar-0d | <f8 | direct | [] | <f8 | true |
| numpy-scalar | <f8 | numpy_scalar | [] | <f8 | true |
| grid-C | <f8 | direct | [2,3] | <f8 | true |
| grid-F | <f8 | fortran | [2,3] | <f8 | true |
| positive-stride | <f8 | positive_stride | [3] | <f8 | true |
| negative-stride | <f8 | negative_stride | [6] | <f8 | true |
| grid-big-endian | >f8 | direct | [2,3] | <f8 | true |
| complex-big-endian | >c16 | direct | [1] | <c16 | true |
| empty-0x3 | <f8 | direct | [0,3] | <f8 | true |
| empty-0x4 | <f8 | direct | [0,4] | <f8 | true |
| grid-row | <f8 | direct | [1,6] | <f8 | true |
| negative-zero | <f8 | direct | [1] | <f8 | true |
| positive-zero | <f8 | direct | [1] | <f8 | true |
| nan | <f8 | direct | [1] | <f8 | false |
| positive-infinity | <f8 | direct | [1] | <f8 | false |
| negative-infinity | <f8 | direct | [1] | <f8 | false |
| complex-nan | <c16 | direct | [1] | <c16 | false |
| complex-infinity | <c16 | direct | [1] | <c16 | false |

| Public fingerprint left | Right | Expected equal |
| --- | --- | --- |
| grid-C | grid-F | true |
| grid-C | grid-big-endian | true |
| width-c16 | complex-big-endian | true |
| scalar-0d | numpy-scalar | false |
| negative-zero | positive-zero | false |
| grid-C | grid-row | false |
| width-b1 | width-u1 | false |
| empty-0x3 | empty-0x4 | false |

All input/reference arrays have at most 32 elements and 512 declared bytes; actual largest literal backing/array is 6 float64 elements (48B). The positive/negative stride views keep that exact 48B backing. The width-f16 vector has two 16B zero values (32B), checking encoding width only; no claim of nonzero extended-float or cross-platform padding equivalence. All complete vector data, including raw NaN/infinity/signed-zero bit patterns, is frozen source. Finite=false is an expected tiny semantic result, not a scientific workflow failure.
