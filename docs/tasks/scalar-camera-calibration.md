# NS03-C: scalar camera calibration from primary-camera images

Version1.0. The owner requested the full noisy simulation and explicitly selected “Images only” for phase/carrier inference. This authorizes the necessary estimator and concrete synthetic primary-camera acquisitions, without an extra information-source or document approval. No human numerical execution/review budget was set. This task implements only [scalar camera calibration](../contracts/scalar-camera-calibration-v1.md).

## Independent scope and baseline

This pure finite-statistic estimator depends on the already approved scalar camera law and existing library errors/NumPy conventions. It does not call or depend on the new simulator runtime, source generator, optical operator or memory changes. Thus its A/B/C/D work is an independent authorized slice in its own worktree while prerequisite PR53 platform/cleanup completion continues. Its starting source is the exact PR53 candidate; final integration cannot claim missing prerequisite evidence as passed. This does not start the dependent joint optical fit or full workflow.

Inputs are only primary-camera dark/blank/flat repeated images plus opaque provenance. Actual illumination levels and camera coefficients are not estimator inputs. The selected first generator recipe is eight two-dimensional 512×512 frames for each group:24frames,50331648 raw float64 bytes. Those exposure counts/levels are synthetic choices, not human budgets or measured instrument facts. Actual forward values stay evaluator-only. Relative-flat-count units are available separately from the optional photon-transfer electron gain.

## Route and ownership

High risk: numerical/statistical meaning, a new public interface, independent moment oracles, range and information outcomes. Fresh native blind A, fresh native blind B, restricted C, fresh independent D. Model choice gpt-6.1-sol/high per existing calibration guidance, provisionally; actual attribution and absent metering remain unknown. Disable optional memory/delegation where supported. A/B receive public contract and named approved public interfaces only, never implementation/history/Currentstate/coverage maps/LESSONS. Source-free diagnostic inheritance precedes every Python/import/pytest probe.

A owns only tests/test_scalar_camera_calibration.py and optional tests/scalar_camera_calibration_fixture.py. C owns only src/simrecon/_scalar_camera_calibration.py and additive exports in src/simrecon/__init__.py; no test/fixture/check/workflow/discovery/coverage/lock/policy edits or unrelated interface changes. B/D assess only. Coordinator owns contract/task/PROJECT, usage/evaluation presentation, environment setup, native launches, evidence, exact checkpoints and completion cleanup. Direct record construction has only the contract's stated promise.

## Checks, evidence and completion

Use one isolated locked Python3.13.12 environment per worktree, existing NumPy/SciPy stack, no dependency change. Cheap interpreter/platform/lock/install/import preflight precedes dependent probes. Use the existing scripts/source_free_check.py unchanged without reading its implementation in blind roles. Focused locked Ruff lint/format, Pyright and public-entry pytest during work; source-free required for blind Python execution. Exact full-candidate make verify UV=/Users/davidhoffman/.local/bin/uv is the final local gate before any own push/open PR. No publication, merge, release or external messages are authorized by this record.

Inherit the continuing scientific chain's binding100% native Coverage.py executable-line and branch-destination targets globally/perowned package/perowned file on each required Ubuntu24.04/macOS15 platform. Include never-imported files/relevant subprocesses, no exclusions/skips/platform union. Distinct language-level statement metric unsupported. Behavior/risk review remains mandatory and a percentage proves no behavioral completeness. PROJECT's advisory default for unrelated tasks is not a migration of this chain.

Record exact source/test/contract/config/lock/environment/tool/artifact inputs and native counts. Preserve all attempts, diagnosis/repair/review charges and unknown measurements. One concise live Currentstate remains with the parent full-simulation coordinator; artifacts/image-only-camera-calibration-20261023/coordinator-pointer.json supplies the local pointer and evidence links, with no competing state. Prepare tracked task/usage pointers before final verification; final candidate hashes/results stay outside tracked bytes.

Coordinator cleanup inventories only positively identified task-created scratch after owned writers close, preserving tracked fixtures, original evidence, incoming/internal links and referents/ancestors and still referenced environment pins. Actual destructive behavior retains its own high-risk route and proof; no age/name pruner or cleanup permission follows for C. Return own scratch/process/reference facts at each role handoff.

Full simulation remains incomplete after this slice: actual raw-bead joint phase/carrier/kernel fitting, continuous nonperiodic inverse execution, specimen fitting and full noisy assessment remain separate concrete contracts.
