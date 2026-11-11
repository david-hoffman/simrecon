# Validate declared NumPy kinds as well as storage width

**Version 1.0**

- ID: 20261103T052754Z-ce04-c1-declared-numpy-kinds
- Date: 2026-11-03T05:27:54.656907+00:00
- Task: [CE04](../tasks/c-equivalence-known-parameters.md)
- Role: C1 implementation, coordinator transcription
- Topic: platform-specific input representation
- Status: confirmed

The implementation worker supplied the following evidence-linked lesson. It is
withheld from D until D saves its independent assessment.

Standard NumPy dtype validation must distinguish the declared floating kind from
its storage size. In this macOS environment `longdouble` reports8 bytes and a
`float64` display name, while its dtype character remains`g`; `clongdouble`
similarly retains`G`. A width-only whitelist admitted those excluded carrier and
modulation declarations. Explicit declared-kind validation corrected the public
rejections. Separately, comparing a float16 array directly with the float32
maximum triggered an overflowing comparison cast under strict arithmetic;
checking the copied binary64 components preserved permitted float16 inputs.

Evidence: C1/diagnosis01.log records the dtype identities. C1/focused01.log
records both excluded-kind nonrejections and the permitted-float16 failure;
C1/focused02.log and focused03.log no longer report those failures. This is
platform-specific observed evidence, not a claim about every NumPy build.
