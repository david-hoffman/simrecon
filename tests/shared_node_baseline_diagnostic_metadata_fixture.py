"""Real standard-library diagnostic callers; metadata never launches a child."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

TIMEOUT_SECONDS = 1.75
CHILD_STATUS = 23
ARGUMENT_MARKER = "A10_PRIVATE_COMMAND_ARGUMENT_62c093"
INLINE_MARKER = "A10_PRIVATE_INLINE_SOURCE_a7184d"


def command_metadata(shape: str) -> object:
    """Keep constructor metadata distinct from the valid wrapper argv."""
    if shape == "string":
        return f"{sys.executable} -c {INLINE_MARKER} {ARGUMENT_MARKER}"
    container, first_kind = shape.split("-", 1)
    first_items: dict[str, object] = {
        "none": None,
        "integer": 8675309,
        "text": sys.executable,
        "bytes": os.fsencode(sys.executable),
        "path": Path(sys.executable),
    }
    items = [first_items[first_kind], "-c", INLINE_MARKER, ARGUMENT_MARKER]
    return tuple(items) if container == "tuple" else items


def main() -> None:
    kind, shape, channel = sys.argv[1:]
    cmd = command_metadata(shape)
    output = b"caller-captured-output"
    stderr = b"caller-captured-stderr"
    # Public constructors retain arbitrary cmd metadata. The type-checker argv
    # restriction describes process invocation, which these examples do not do.
    error: subprocess.TimeoutExpired | subprocess.CalledProcessError
    if kind == "timeout":
        error = subprocess.TimeoutExpired(cmd, TIMEOUT_SECONDS, output=output, stderr=stderr)  # pyright: ignore[reportArgumentType]
    else:
        error = subprocess.CalledProcessError(CHILD_STATUS, cmd, output=output, stderr=stderr)  # pyright: ignore[reportArgumentType]

    attributes_before = error.__dict__.copy()
    args_before = error.args
    command_before = tuple(cmd) if isinstance(cmd, (list, tuple)) else cmd

    def field_checks() -> dict[str, bool]:
        current_cmd = error.cmd
        current_contents = (
            tuple(current_cmd) if isinstance(current_cmd, (list, tuple)) else current_cmd
        )
        value_preserved = (
            error.timeout == TIMEOUT_SECONDS
            if isinstance(error, subprocess.TimeoutExpired)
            else error.returncode == CHILD_STATUS
        )
        return {
            "cmd_identity": error.cmd is cmd,
            "cmd_contents": current_contents == command_before,
            "output_identity": error.output is output,
            "stdout_alias": error.stdout is output,
            "stderr_identity": error.stderr is stderr,
            "duration_or_status": value_preserved,
            "attributes_unchanged": error.__dict__ == attributes_before,
            "args_unchanged": error.args == args_before,
        }

    if channel == "uncaught":
        raise error  # A10_SOURCE_SNIPPET_MUST_BE_HIDDEN_9087e1

    checks = {"before": field_checks()}
    rendered = {"str": str(error)}
    checks["after_str"] = field_checks()
    rendered["exception_only"] = "".join(traceback.format_exception_only(error))
    checks["after_exception_only"] = field_checks()
    try:
        raise error  # A10_SOURCE_SNIPPET_MUST_BE_HIDDEN_9087e1
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as caught:
        rendered["traceback"] = "".join(traceback.format_exception(caught))
    checks["after_traceback"] = field_checks()
    print(json.dumps({"rendered": rendered, "field_checks": checks}))


if __name__ == "__main__":
    main()
