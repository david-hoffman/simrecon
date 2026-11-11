# Read resolved optional declarations in test expectations

**Version 1.0**

- ID: 20261106T133205Z-ce07-coordinator-resolved-optional-test-expectations
- Date: 2026-11-06T13:32:05.272402+00:00
- Task: [CE07 public workflow](../tasks/c-equivalence-workflow.md)
- Role: coordinator
- Topic: test-fixture default interpretation
- Status: confirmed
- Observation: Two finite-search reuse fixtures omitted optional `use_time0_carriers`. A keeper indexed their raw dictionaries after the public call and raised `KeyError`, although the approved and existing independent fixture resolver default was `True`. Reading the resolved expectation preserved explicit `False` alternatives and all scientific assertions. A fixture-only source-free probe reproduced the cause. After the one-expression fix, four search keepers and four raw-to-image siblings passed as postimplementation supplemental evidence; they did not recreate original test-first evidence.
- Evidence: [optional workflow contract](../contracts/c-equivalence-workflow-v1.md), [corrected public keeper](../../tests/test_c_workflow_numerical.py), and [independent fixture resolver](../../tests/c_workflow_oracle.py). The task evidence root retains `public/C1-test-default-defect.json`, `A1-correction-7/one-file-test-correction.diff`, the original accepted checkpoint `5461a70c5ed0382702b4678f4badf79ff1aeaa6e5da11d5782e5246dde9fab0b` and revised checkpoint `55457aa7e7fa6d088f2c45c81a6cfa37e7444d55f0088430b3345ef87d575a41`. Task Python3.13.12 source-free fixture and eight public-example checks exited0.
- Suggested action: Read the existing independent resolved fixture configuration for optional expectations. Qualify test-only branch logic using permitted fixtures while preserving caller inputs and the distinction between feature absence and unexecuted assertions. This lesson grants no new edit or test authority.
