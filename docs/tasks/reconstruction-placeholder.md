# RECONSTRUCTION-PLACEHOLDER: public reconstruction stage

**Version 1.0** Git versions revisions. This is a narrowly requested architecture scaffold, not a numerical reconstruction contract. Status and checkpoint accounting live in [ARCHITECTURE-INTAKE's Current state](architecture-intake.md#current-state).

## Contract

- Parent work: architecture intake. Intended baseline: UML checkpoint `44c7273c24d76962487ec117cc3a8e730a0a827a` on `codex/architecture-intake`.
- Owner instruction: "It should be in the diagram (and code) even as a placeholder." This explicitly requests a code placeholder during architecture review. It does not approve the broader architecture, an image/OTF data model, or a scientific algorithm.
- Read-back assumption: expose `simrecon.reconstruct(image, otf, parameters)` and always raise `NotImplementedError` with message `Reconstruction is not implemented.` No defaults, processing, input validation, file access, or fallback result.
- Public interface: `from simrecon import reconstruct`; three required inputs named `image`, `otf`, and `parameters`, accepted positionally or by keyword. Each accepts a Python object; future numerical types are unsettled. The function returns no value because it raises.
- Inputs/outputs/errors: three supplied objects; unconditional `NotImplementedError`; no scientific result. Do not inspect or mutate supplied objects. Unsupported units, shapes, estimators, tolerances, and scientific errors are outside this placeholder.
- Integration boundary: this is a separate scaffold task from the first MRC intake/conversion slice. Conversion reads, harmonizes, and writes image data directly; it does not call `reconstruct` or require OTF input. The placeholder does not supply a successful end-to-end reconstruction, and raw data must not be passed through and labeled as reconstructed output. No conversion implementation or integration test is authorized by this contract.
- Expected-result source: owner's explicit placeholder request plus the read-back code-only behavior above. No legacy-output or paper oracle is needed for a non-numerical stub.
- Permitted product scope: one small pristine reconstruction module and public package export. Fresh A authors one public-interface test; fresh B reviews it before C. C must not change reviewed tests or checks. Fresh D reviews the exact passing candidate. No new data classes, adapters, CLI reconstruction command, algorithms, dependencies, exclusions, workflow changes, or doctor patch.
- Documentation scope: show both the successful conversion route and the separate reconstruction route in the main UML pipeline; keep actual placeholder failure separate from future numerical behavior.
- Checks: existing canonical `make verify UV=/Users/davidhoffman/.local/bin/uv`; 100% measured supported statements/branches for all owned runtime. Import and call the public entry point; no scientific executable tests.
- Execution budget: pending owner answer to whether the intake's unlimited allowance extends to this placeholder-only slice, or a separate 30-minute cap applies. No historical setup allowance is reused. Default two A/B rounds and one C repair after initial C apply to this new scope; no prior placeholder attempts have occurred.
- Completion: main diagram contains the reconstruction stage; public stub exists; reviewed public test and canonical full verification pass; fresh D accepts; real owner budget/approval evidence and final candidate results are recorded. No merge/release or numerical implementation.

| Scenario ID | Requested input/context and observable outcome | Expectation source | Test mapping supplied by A and checked by B |
|---|---|---|---|
| P1 | Import `reconstruct` through `simrecon`, supply three explicit objects, and receive `NotImplementedError` with the declared message, without a returned reconstruction or input mutation. Positional and named invocation are two forms of the same stub operation. | Owner's placeholder request and the code-only read-back above | Pending fresh A/B |
