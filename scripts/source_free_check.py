"""Run Python or pytest with source-free diagnostic rendering inherited by children."""

from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
from pathlib import Path


def check_interpreter_options(arguments: list[str]) -> None:
    """Reject disabling interpreter options before the Python program boundary."""
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument in ("-", "--") or not argument.startswith("-"):
            return
        if argument.startswith("--"):
            index += 2 if argument == "--check-hash-based-pycs" else 1
            continue
        flags = argument[1:]
        for position, flag in enumerate(flags):
            if flag in "ISE":
                raise ValueError(
                    "Python -I, -S and -E disable the inherited diagnostic environment"
                )
            if flag in "cm":
                return
            if flag in "WX":
                if position == len(flags) - 1:
                    index += 1
                break
        index += 1


def command(mode: str, arguments: list[str]) -> list[str]:
    """Construct argv with pytest's source and local-variable output disabled."""
    if mode == "python":
        check_interpreter_options(arguments)
        return [sys.executable, *arguments]
    return [
        sys.executable,
        "-m",
        "pytest",
        *arguments,
        "--tb=line",
        "--no-showlocals",
        "--assert=plain",
    ]


def environment() -> dict[str, str]:
    """Prepend each diagnostic token once, preserving other inherited entries."""
    result = os.environ.copy()
    site = str(Path(__file__).resolve().parent / "source_free_sitecustomize")
    previous = result.get("PYTHONPATH")
    paths = previous.split(os.pathsep) if previous else []
    result["PYTHONPATH"] = os.pathsep.join([site, *(path for path in paths if path != site)])
    plugins = result.get("PYTEST_PLUGINS")
    names = plugins.split(",") if plugins else []
    result["PYTEST_PLUGINS"] = ",".join(
        ["pytest_plugin", *(name for name in names if name != "pytest_plugin")]
    )
    return result


def main() -> int:
    """Execute a bounded subprocess and preserve its exit status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("mode", choices=("python", "pytest"))
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    arguments = parser.parse_args()
    if not math.isfinite(arguments.timeout) or arguments.timeout <= 0:
        parser.error("--timeout must be finite and positive")
    try:
        argv = command(arguments.mode, arguments.arguments)
        result = subprocess.run(argv, env=environment(), timeout=arguments.timeout, check=False)
    except subprocess.TimeoutExpired:
        print(
            f"Source-free command failed: TimeoutExpired: {sys.executable} "
            f"({arguments.mode}) exceeded {arguments.timeout:g} seconds",
            file=sys.stderr,
        )
        return 1
    except (OSError, ValueError) as error:
        print(f"Source-free command failed: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    return result.returncode if result.returncode >= 0 else 128 - result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
