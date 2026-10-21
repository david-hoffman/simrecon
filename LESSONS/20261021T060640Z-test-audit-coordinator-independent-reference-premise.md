# A product error allowance can hide reference bias

**Version 1.0**

- ID: 20261021T060640Z-test-audit-coordinator-independent-reference-premise
- Date: 2026-10-21T06:06:40.486096+00:00
- Task: [test audit](../docs/tasks/test-audit-linux-ci.md)
- Role: coordinator
- Topic: oracle-preservation correction
- Status: confirmed
- Observation: A retained reconstruction comparer permits product error up to budget plus estimator-to-analytic discrepancy. Returning the estimator therefore passes without independently bounding that discrepancy. The removed direct estimator-versus-phantom qualification supplied a separate premise.
- Evidence: Native independent D round1 report `artifacts/test-audit-ci/final-D/final.txt` on c257fa9a8f3039506f6f589cad79facf17c94bbb; exact baseline function source SHA2567828698fdae24c794aa018e53e868b87685324cbccdf7c7bb3f6990a4010546a; unchanged restoration23focusedcases passed.
- Suggested action: Restore the existing direct qualification byte for byte and obtain renewed exact full gates and fresh final review. Calling the same general reference is insufficient evidence of redundant qualification.
