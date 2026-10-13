# Generate documentary reference fixtures

From the worktree root, use the locked project interpreter:

```sh
.venv/bin/python scripts/generate_reference_fixtures.py otf
.venv/bin/python scripts/generate_reference_fixtures.py reconstruction
```

Each command emits one complete JSON document on standard output. Exactly one
selector is required. The exporter accepts no scientific inputs, settings,
tolerance or output-path option. It computes and serializes the document before
writing. Import, scientific or output failure gives a nonzero exit status without
fallback. The exporter creates no files or directories.

## Capture, consume and clean up

The caller owns storage. This standard-library example runs both selectors,
captures each document inside a `TemporaryDirectory`, checks subprocess success,
parses and renders the case names while the context exists, then observes cleanup.
Run it from the worktree root with the locked interpreter:

```sh
.venv/bin/python - <<'PY'
import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

exporter = Path("scripts/generate_reference_fixtures.py").resolve()
environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
for selector, collection, identity in (
    ("otf", "fixtures", "id"),
    ("reconstruction", "entries", "name"),
):
    with TemporaryDirectory(prefix="reference-fixtures-") as temporary:
        directory = Path(temporary)
        capture = directory / "reference.json"
        with capture.open("wb") as stream:
            subprocess.run(
                [sys.executable, str(exporter), selector],
                cwd=directory,
                env=environment,
                stdout=stream,
                check=True,
                timeout=240,
            )
        document = json.loads(capture.read_bytes())
        print(selector, ":", ", ".join(case[identity] for case in document[collection]))
        assert capture.is_file()
    assert not directory.exists()
    print(selector, ": temporary capture removed")
PY
```

Consume or render any needed arrays inside the context. A failed command can leave
partial output in the caller's capture; check its status before parsing. The
context removes that capture on exit, including when an exception propagates.

## Scientific interpretation

The [fixture export contract](../contracts/reference-fixtures-v1.md) defines exact
preservation. The exporter uses the unchanged independent science helpers, compact
formulas and historical metadata. It reads no documentary JSON payload.

The OTF (optical transfer function) family contains `delta-odd`, `uniform-even`,
`asymmetric-even`, `asymmetric-translated`, `separable-mixed` and `singleton`, in
frozen helper order. The [case notes](../references/scientific/otf-calibration-fixture-notes.md)
give the normalized negative-exponential formulas, signed modes, origins and
spacings. Historical display values round binary64 `sqrt(3)/2` before weighting.
Their documentary `uint8` labels and original Fourier-transform consistency
residuals remain historical. Use independently derived high-precision formulas
for accuracy assessment.

Reconstruction contains `commensurate-recovery` followed by `fractional-estimator`.
The frozen helper evaluates acquisitions, full complex transfer, object truth,
stored-data estimator and denominator/budget measurements at 85 Decimal digits.
The auxiliary point spread function and real object samples are each rounded to
binary64 before conventional convolution. Each output starts at `0.0`; kernel y
visits `0..6` outside kernel x `0..8`, with separate multiplication and left-folded
addition. This native `7 × 9` unit-brightness unilluminated observation is distinct
from a phase average. The [comparison report](../reports/reconstruction-comparison.md)
explains the fractional estimator's example physical limitation. It supplies no
new acceptance threshold or universal bias bound.

Historical creation labels, input hashes, observation fields and checkpoint
claims retain their original meaning. These documents are independent reference
data, not product outputs or new role acceptance. Reconstruction's creation label
predates its historical B4 acceptance; the retained comparison identifies checkpoint
`B4:82bcbfe1a41cc5d0439e89d0dbb0bebf7e5b315b37801617cf7b57ed04c8602b`
and verdict digest
`fa131979cdab582d43e5b637593706b397ba4fb40062ec676b741034f2045cdd`.

Record fresh command/status, candidate commit/tag/dirty inputs, generator/helper/
contract/test/oracle/lock/config/check/interpreter/platform identities and output,
scientific-representation and acquisition digests separately in generation
evidence. Current observations must not replace historical fields. Compare every
parsed field with exact types, order, strings and binary64 bits before retirement.
Whole-file byte equality and scientific equality are separate observations.

## Historical resolution

The original documentary blobs remain addressable by exact Git revision and path:

| Family | Revision | Path | Whole-file SHA-256 |
|---|---|---|---|
| OTF | `a44e9d0c67403d5a001340b65ba04ea2f559256a` | `docs/references/scientific/otf-calibration-fixtures-v1.json` | `ba2dcd790738cf950b184995e1c12935266ddaa1738c9f874b46a6dd442c9dcf` |
| Reconstruction | `5e231d3d27dfd843de776de5ac80d3d46c0c5727` | `docs/references/scientific/reconstruction-fixtures-v1.json` | `64decad0389d332100bee202a02a8bafacd1c942e324dff992babccb8ca88541` |

For example, inspect the pinned OTF blob and check its digest without creating a file:

```sh
git show a44e9d0c67403d5a001340b65ba04ea2f559256a:docs/references/scientific/otf-calibration-fixtures-v1.json
git show a44e9d0c67403d5a001340b65ba04ea2f559256a:docs/references/scientific/otf-calibration-fixtures-v1.json | shasum -a 256
git show 5e231d3d27dfd843de776de5ac80d3d46c0c5727:docs/references/scientific/reconstruction-fixtures-v1.json | shasum -a 256
```

A shallow checkout may lack these revisions. Historical references identify these
exact blobs and digests; current generation does not recreate original acceptance.
Permanent exporter checks use compact preservation digests and independent
mathematical formulas without requiring Git history as their sole oracle.
