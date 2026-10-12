"""Disposable phase commands that redirect outputs without writing protected bytes."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from verification_fixture_tools import PHASES
from verification_fixture_tools import main as receipt_main


def fingerprint(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def main() -> int:
    status = receipt_main()
    if sys.argv[1:] == ["--version"] or Path(sys.argv[0]).name == "uv":
        return status
    phase = next((arg for arg in sys.argv[1:] if arg in PHASES), None)
    configuration = json.loads(os.environ.get("OUTPUT_PROTECTION_ACTION", "{}"))
    if phase != configuration.get("phase"):
        return status

    root = Path.cwd()
    target = root / configuration["target"] if configuration.get("target") else None
    identity_loss = configuration.get("identity_loss")
    if identity_loss:
        (root / identity_loss).unlink()
    before = fingerprint(target) if target else None
    destination = root / configuration["destination"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    kind = configuration["kind"]
    if kind == "directory-alias":
        if destination.exists():
            destination.rename(root / configuration["saved"])
        assert target is not None
        destination.symlink_to(target, target_is_directory=True)
    else:
        destination.unlink(missing_ok=True)
        if kind == "alias":
            assert target is not None
            destination.symlink_to(target)
        elif kind == "regular":
            destination.write_bytes(b"ordinary ignored phase-created output\n")
        elif kind == "unwritable-directory":
            destination.mkdir()
        else:
            raise ValueError(f"unknown disposable action: {kind}")
    after = fingerprint(target) if target else None
    observation = {"phase": phase, "kind": kind, "before": before, "after": after}
    with (root / "actions.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(observation) + "\n")
    # Both streams contain real phase output after the redirect. The fixture
    # never opens an alias destination for writing.
    print(f"output protection action completed in {phase}")
    print(f"output protection stderr from {phase}", file=sys.stderr)
    return int(configuration.get("status", status))


if __name__ == "__main__":
    sys.exit(main())
