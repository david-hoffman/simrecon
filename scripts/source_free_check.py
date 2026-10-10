"""Run Python or pytest with source-free diagnostic rendering inherited by children."""

from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
from pathlib import Path


def command(mode: str, arguments: list[str]) -> list[str]:
    """Construct argv with pytest's source and local-variable output disabled."""
    if mode == "python":
        if any(item in ("-I", "-S", "-E") for item in arguments):
            raise ValueError("Python -I, -S and -E disable the inherited diagnostic environment")
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
    """Make sitecustomize available to this command and Python subprocesses."""
    result = os.environ.copy()
    site = Path(__file__).resolve().parent / "source_free_sitecustomize"
    previous = result.get("PYTHONPATH")
    result["PYTHONPATH"] = str(site) + (os.pathsep + previous if previous else "")
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
