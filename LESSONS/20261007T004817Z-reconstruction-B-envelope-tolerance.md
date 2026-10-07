# Observed numerical margin does not define the acceptance bound

**Version 1.0**

- ID: 20261007T004817Z-reconstruction-B-envelope-tolerance
- Date: 2026-10-07T00:48:17.821006+00:00
- Task: [Known-parameter reconstruction](../docs/tasks/known-parameter-reconstruction.md)
- Role: B; wording handed off verbatim and evidence checked by coordinator
- Topic: numerical test oracle
- Status: confirmed for this contract-envelope counterexample; not a supported-backend defect claim
- Observation: A small observed numerical error does not justify a tighter acceptance gate. Check tight assertions against both the final public error envelope and permitted prerequisite backward error; this review constructed a valid prerequisite result that the tighter reconstruction assertions reject.
- Evidence: Local retained `artifacts/reconstruction-execution/B1-final.txt`, SHA256 `48cd7e7cc95ffc55943320c6c5c84cd2d80068f7f48b83017b6140ea33e823e0`; full independent B1 verdict and arithmetic-probe evidence in the same ignored execution directory. B1 certificate reports maximum norm(f)/norm(b)=1.66932048e-13 < 128*7*2^-52=1.98951966e-13, with reconstruction mode error1.20008e-11 and image error2.40044e-11 below the approved7.98264e-8 budget. These exceed the authored2e-12/2e-11 assertions. [Approved accuracy contract](../docs/contracts/known-parameter-reconstruction-v1.md#range-errors-and-accuracy). Native reviewer environment Python3.13.12,NumPy2.5.3,SciPy1.18.1,macOS27arm64. The ordinary independent calculation passed the tighter bounds; it did not invalidate the permitted counterexample.
- Suggested action: Bound assertions by approved public numerical guarantees, retaining independent sign/gain/normalization discrimination and exact checks for exact guarantees. A stricter requirement needs intake. This entry grants no policy, scope or budget change.
