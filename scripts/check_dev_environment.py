"""Report local development readiness without installing or contacting services.

Run from a checkout root with a seed Python 3.10 or newer. Project dependencies
are probed only through that checkout's .venv/bin/python.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path

PYTHON_PROBE = """\
import importlib
import importlib.metadata
import json
import platform
import sys

result = dict(executable=sys.executable, version=platform.python_version(), prefix=sys.prefix)
result['imports'] = {}
try:
    for name in ('simrecon', 'numpy', 'h5py'):
        module = importlib.import_module(name)
        result['imports'][name] = dict(path=module.__file__,
            version=importlib.metadata.version(name))
except Exception as error:
    result['error'] = type(error).__name__
print(json.dumps(result))
"""


class Readiness:
    """Collect independent local probe results and retain a failing status."""

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout
        self.failed = False

    def fail(self, name: str, category: str, detail: str, next_step: str) -> None:
        """Print a classified failure and the applicable operator action."""
        self.failed = True
        print(f"FAIL {name}: {category}: {detail[:4000]}\n  next: {next_step}")

    def probe(self, name: str, command: list[str], next_step: str) -> str | None:
        """Run a bounded local command with no shell or bytecode writes."""
        selected = command[0]
        executable = shutil.which(selected)
        # Explicit non-executable paths must reach the PermissionError diagnostic.
        if executable is None and not Path(selected).exists():
            self.fail(name, "missing executable", selected, next_step)
            return None
        path = Path(executable or selected).absolute()
        print(f"{name}: executable={path}; resolved={path.resolve()}")
        try:
            result = subprocess.run(
                [executable or selected, *command[1:]],
                capture_output=True,
                text=True,
                errors="replace",
                timeout=self.timeout,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "GIT_OPTIONAL_LOCKS": "0"},
                check=False,
            )
        except subprocess.TimeoutExpired:
            self.fail(name, "timeout", f"exceeded {self.timeout:g} seconds", next_step)
            return None
        except PermissionError as error:
            self.fail(name, "permission failure", f"errno={error.errno}", next_step)
            return None
        except OSError as error:
            self.fail(
                name, "execution failure", f"{type(error).__name__}; errno={error.errno}", next_step
            )
            return None
        output = (result.stdout + "\n" + result.stderr).strip()
        if result.returncode:
            self.fail(name, "nonzero command", f"status={result.returncode}", next_step)
            return None
        return output


def positive_timeout(value: str) -> float:
    """Accept only finite positive subprocess deadlines."""
    timeout = float(value)
    if not math.isfinite(timeout) or timeout <= 0:
        raise argparse.ArgumentTypeError("timeout must be finite and positive")
    return timeout


def check_python(check: Readiness, root: Path, setup: str) -> None:
    """Check the actual worktree interpreter, prefix and installed imports."""
    output = check.probe(
        "worktree Python", [str(root / ".venv/bin/python"), "-I", "-B", "-c", PYTHON_PROBE], setup
    )
    if output is None:
        return
    try:
        observed = json.loads(output)
        version, prefix = observed["version"], observed["prefix"]
        imports = observed["imports"]
        print(
            f"worktree Python: expected=3.13.12 observed={version}; "
            f"executable={observed['executable']}; prefix={prefix}"
        )
        for name, identity in imports.items():
            print(f"import {name}: version={identity['version']} path={identity['path']}")
        if version != "3.13.12":
            check.fail("worktree Python", "wrong version", str(version), setup)
        if Path(prefix).resolve() != (root / ".venv").resolve():
            check.fail("worktree Python", "wrong worktree", str(prefix), setup)
        if "error" in observed:
            check.fail("worktree imports", "uninitialized dependencies", observed["error"], setup)
        elif (
            Path(imports["simrecon"]["path"]).resolve()
            != (root / "src/simrecon/__init__.py").resolve()
        ):
            check.fail(
                "simrecon import", "wrong worktree/import", imports["simrecon"]["path"], setup
            )
    except (ValueError, KeyError, TypeError) as error:
        check.fail("worktree Python", "invalid probe output", type(error).__name__, setup)


def main() -> int:
    """Report local readiness and explicit deferred evidence, returning failure status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uv", default=os.environ.get("UV", "uv"))
    parser.add_argument("--java", default=os.environ.get("SIMRECON_JAVA", "java"))
    parser.add_argument(
        "--timeout",
        type=positive_timeout,
        default=10.0,
        help="seconds per local subprocess (default: 10)",
    )
    args = parser.parse_args()
    check = Readiness(args.timeout)
    root = Path.cwd().resolve()
    setup = (
        'Follow docs/operations/bootstrap.md; then make sync UV="$UV" with SIMRECON_JAVA selected'
    )
    print(
        f"host: OS={platform.system()} release={platform.release()} "
        f"architecture={platform.machine()}"
    )
    print(f"checkout: {root}")
    print("Platform qualification: not checked; verification matrix is Ubuntu 24.04/macOS 15")
    git = check.probe("Git", ["git", "--version"], "Install Git; see docs/operations/bootstrap.md")
    if git is not None:
        print(f"Git: {git}")
        for label, options in (
            ("root", ["rev-parse", "--show-toplevel"]),
            ("HEAD/tree", ["rev-parse", "HEAD", "HEAD^{tree}"]),
            ("branch", ["rev-parse", "--abbrev-ref", "HEAD"]),
            ("tracked state", ["status", "--porcelain", "--untracked-files=no"]),
        ):
            identity = check.probe(
                f"checkout {label}", ["git", *options], "Use the intended Git checkout root"
            )
            if identity is not None:
                print(f"checkout {label}: {identity or 'clean'}")
                if label == "root" and Path(identity).resolve() != root:
                    check.fail(
                        "checkout",
                        "wrong worktree",
                        "run from checkout root",
                        "cd to checkout root",
                    )
    make = check.probe(
        "Make", ["make", "--version"], "Install Make; see docs/operations/bootstrap.md"
    )
    if make is not None:
        print(f"Make: {make.splitlines()[0] if make else 'empty version output'}")
    uv = check.probe(
        "uv", [args.uv, "--version"], "Select uv 0.12.19; see docs/operations/bootstrap.md"
    )
    if uv is not None:
        version = re.match(r"^uv (\d+\.\d+\.\d+)(?:\s|$)", uv)
        observed = version.group(1) if version else "unreported"
        print(f"uv: expected=0.12.19 observed={observed}")
        if observed != "0.12.19":
            check.fail(
                "uv",
                "wrong version",
                observed,
                "Select uv 0.12.19 with --uv or UV; see bootstrap.md",
            )
    java = check.probe(
        "Java",
        [args.java, "-XshowSettings:properties", "-version"],
        "Select JDK 21.0.7 with --java or SIMRECON_JAVA; see bootstrap.md",
    )
    if java is not None:
        properties = dict(
            re.findall(
                r"^\s*(java\.(?:version|vendor|runtime.version))\s*=\s*(.*?)\s*$",
                java,
                re.MULTILINE,
            )
        )
        print(
            "Java: expected=21.0.7; "
            + "; ".join(
                f"{key} = {properties.get(key, 'unreported')}"
                for key in ("java.version", "java.vendor", "java.runtime.version")
            )
        )
        if properties.get("java.version") != "21.0.7":
            check.fail(
                "Java",
                "wrong version",
                properties.get("java.version", "unreported java.version"),
                "Select JDK 21.0.7; see docs/operations/bootstrap.md",
            )
    check_python(check, root, setup)
    print(
        "DEFERRED: JDK source-launcher and authenticated reader inputs: "
        "run unchanged make preflight"
    )
    print("NOT CHECKED: connectivity, native stored login, completed sign-in and role capability")
    print(
        "NOT CHECKED: isolated hatchling build environment and full verification; "
        "see make preflight/verify"
    )
    print("LOCAL NOT READY" if check.failed else "LOCAL READY (deferred checks remain required)")
    return int(check.failed)


if __name__ == "__main__":
    raise SystemExit(main())
