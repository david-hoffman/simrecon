# Absolute error statistics need their own representable scale

**Version 1.0**

- ID: 20261027T101839Z-pr53-coordinator-independent-error-scales
- Date: 2026-10-27T10:18:39.960398+00:00
- Task: https://github.com/david-hoffman/simrecon/pull/53
- Role: coordinator
- Topic: numerical evaluation and oracle design
- Status: confirmed
- Observation: With fifteen residuals of -2^-600 beside matching 2^500 signals, absolute L2, root-mean-square, maximum and mean errors are representable nonzero floats while relative L2 legitimately rounds to zero. The previous evaluator reported all four absolute errors as zero. A real public evaluate regression reproduced it; the corrected driver passes that keeper and the retained module. The original frozen study's six relative errors changed by at most 1.1102230246251565e-16 when re-evaluated without refitting.
- Evidence: Code checkpoint 51c1975eab072a29f0a820fd2493eec5663ec9a7; tests/test_full_noisy_study.py::test_prediction_metrics_preserve_tiny_absolute_errors_beside_large_common_signal; docs/studies/full-noisy-study-2026-10-26/evidence/post-correction-reevaluation.json. Actual driver Python 3.13.12, NumPy 2.5.3 and SciPy 1.18.1; the existing source-free pytest keeper and retained module passed.
- Suggested action: For error-reporting changes, preserve independently available absolute statistics before common-signal scaling can erase them. Judge error assertions at the statistic's own scale while retaining legitimate zero relative error. This is a bounded numerical lesson, not a new recovery threshold or editing authorization.
