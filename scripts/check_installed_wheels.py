"""Check the product and development wheels in isolated temporary caller environments."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PRODUCT_PROBE = """\
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import sysconfig

import simrecon

expected = {
    'AcquisitionBands', 'AcquisitionModeError', 'ModeEvent', 'TwoDPlaneInputs',
    'prepare_acquisition_bands', 'reinterpret_2d_planes', 'DataBlock', 'DatasetInfo',
    'EstimatedParameters', 'ImagejSeries', 'ImagejWriteReport', 'KnownReconstruction',
    'OpticalTransfer', 'OtfError', 'ParameterEstimationError', 'PreparedBands', 'PreparedOtf',
    'RawAcquisition', 'ReconstructionError', 'SimreconError', 'WriteReport', 'WorkflowError',
    'WorkflowReconstruction', 'declare_acquisition', 'declare_otf', 'estimate_parameters',
    'export_imagej', 'harmonize', 'inspect', 'prepare_bands', 'prepare_bead_otf', 'read',
    'reconstruct_known', 'reconstruct_workflow', 'sample_otf', 'write',
}
assert len(simrecon.__all__) == 36 and set(simrecon.__all__) == expected
assert all(callable(getattr(simrecon, name)) for name in expected)
assert Path(simrecon.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
for name in ('simrecon_devtools', 'simrecon._delivery', 'simrecon._pytest_policy',
             'pytest', 'coverage', 'ruff', 'pyright'):
    assert importlib.util.find_spec(name) is None, name
assert not any(name.startswith('simrecon_devtools') for name in sys.modules)
dist = importlib.metadata.distribution('simrecon')
assert not any('devtools' in name or '_delivery' in name or '_pytest_policy' in name
               for name in map(str, dist.files))
scripts = {entry.name: entry.value for entry in dist.entry_points
           if entry.group == 'console_scripts'}
assert scripts == {'simrecon': 'simrecon.cli:main'}
cli = str(Path(sysconfig.get_path('scripts')) / 'simrecon')
help_result = subprocess.run([cli, '--help'], capture_output=True, text=True, timeout=30)
assert help_result.returncode == 0, help_result.stderr
assert all(command in help_result.stdout for command in ('inspect', 'convert', 'export-imagej'))
missing = subprocess.run([cli, 'inspect', 'absent.mrc'], capture_output=True, text=True, timeout=30)
assert missing.returncode == 1 and not missing.stdout, missing
assert json.loads(missing.stderr)['code'] == 'io_error', missing.stderr
print('installed product: 36 exports, console CLI, runtime-only environment', simrecon.__file__)
"""

DEVTOOLS_PROBE = """\
import importlib.util
from pathlib import Path
import subprocess
import sys
import sysconfig

import simrecon_devtools.delivery
import simrecon_devtools.pytest_policy

assert importlib.util.find_spec('simrecon') is None
for module in (simrecon_devtools.delivery, simrecon_devtools.pytest_policy):
    assert Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
delivery = str(Path(sysconfig.get_path('scripts')) / 'delivery')
result = subprocess.run([delivery, 'doctor', '--check'], capture_output=True, text=True, timeout=30)
assert result.returncode == 23 and result.stdout == 'installed doctor caller\\n', result
observed = Path('doctor-call.txt').read_text()
assert str(Path.cwd()) in observed and '--sandbox read-only' in observed, observed
assert 'Run with --check: report only and do not write files.' in observed, observed

cases = {
    'pass': ('def test_case(): assert True\\n', 0, '1 passed'),
    'skip': ('import pytest\\ndef test_case(): pytest.skip("controlled")\\n', 1, '1 skipped'),
    'xfail': ('import pytest\\n@pytest.mark.xfail(reason="controlled")\\n'
              'def test_case(): assert False\\n', 1, '1 xfailed'),
    'xpass': ('import pytest\\n@pytest.mark.xfail(reason="controlled", strict=False)\\n'
              'def test_case(): assert True\\n', 1, '1 xpassed'),
}
for name, (source, status, outcome) in cases.items():
    path = Path('test_' + name + '.py')
    path.write_text(source)
    result = subprocess.run([sys.executable, '-I', '-m', 'pytest', '-q',
                             '-c', 'pytest.ini', str(path)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == status and outcome in result.stdout, result
print('installed devtools: doctor caller and strict pytest pass/skip/xfail/xpass outcomes')
"""


def run(command: list[str], caller: Path, environment: dict[str, str]) -> None:
    """Run one required installed-wheel check and preserve failing diagnostics."""
    subprocess.run(command, cwd=caller, env=environment, check=True, timeout=180)


def main() -> int:
    """Install each sole wheel separately, without editable packages or checkout imports."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uv", default="uv")
    args = parser.parse_args()
    root = Path.cwd().resolve()
    product_wheels = list((root / "dist").glob("*.whl"))
    devtools_wheels = list((root / "artifacts/devtools/dist").glob("*.whl"))
    if len(product_wheels) != 1 or len(devtools_wheels) != 1:
        parser.error("expected one product wheel and one separate development wheel")
    with zipfile.ZipFile(product_wheels[0]) as wheel:
        if any(
            "devtools" in name or "_delivery" in name or "_pytest_policy" in name
            for name in wheel.namelist()
        ):
            parser.error("product wheel contains repository development utilities")
    environment = os.environ.copy()
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    with tempfile.TemporaryDirectory(prefix="simrecon-installed-wheels-") as directory:
        caller = Path(directory).resolve()
        if caller.is_relative_to(root):
            parser.error("installed-wheel caller must be outside the checkout")
        constraints = caller / "constraints.txt"
        run(
            [
                args.uv,
                "export",
                "--project",
                str(root),
                "--locked",
                "--all-groups",
                "--no-emit-local",
                "--no-hashes",
                "--output-file",
                str(constraints),
                "--quiet",
            ],
            caller,
            environment,
        )
        for name, wheel, probe in (
            ("product", product_wheels[0], PRODUCT_PROBE),
            ("devtools", devtools_wheels[0], DEVTOOLS_PROBE),
        ):
            print(
                "installed-wheel input:",
                wheel.relative_to(root),
                "sha256=" + hashlib.sha256(wheel.read_bytes()).hexdigest(),
                flush=True,
            )
            prefix = caller / name
            python = prefix / "bin/python"
            run([args.uv, "venv", "--python", sys.executable, str(prefix)], caller, environment)
            run(
                [
                    args.uv,
                    "pip",
                    "install",
                    "--python",
                    str(python),
                    "--constraint",
                    str(constraints),
                    str(wheel),
                ],
                caller,
                environment,
            )
            if name == "devtools":
                (caller / "pytest.ini").write_text(
                    "[pytest]\naddopts = --strict-config --strict-markers -ra "
                    "-p simrecon_devtools.pytest_policy\nstrict_xfail = true\n"
                )
                bin_dir = caller / "bin"
                bin_dir.mkdir()
                codex = bin_dir / "codex"
                codex.write_text(
                    f"#!{python}\n"
                    "import sys\nfrom pathlib import Path\n"
                    "Path('doctor-call.txt').write_text(' '.join(sys.argv[1:]) "
                    "+ '\\n' + sys.stdin.read())\n"
                    "print('installed doctor caller')\nsys.exit(23)\n"
                )
                codex.chmod(0o755)
                environment["PATH"] = str(bin_dir) + os.pathsep + environment.get("PATH", "")
            run([str(python), "-I", "-c", probe], caller, environment)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
