UV ?= uv
PYTHON ?= python3
VERIFY_ARGS ?=

.PHONY: check verify sync quality coverage-clean lint format types tests coverage-combine coverage-json coverage-html coverage-report wheel wheel-import audit
.PHONY: preflight

# Fast feedback uses the same locked sync and quality commands as full verification.
check: sync
	$(MAKE) --no-print-directory quality UV="$(UV)"

quality: lint format types

# The wrapper records each required phase; it does not replace or skip the gate.
verify:
	$(PYTHON) scripts/verify.py --measurements-required --uv "$(UV)" --make "$(MAKE)" $(VERIFY_ARGS)

sync:
	$(UV) sync --locked --all-groups
	$(UV) run --locked --no-sync python scripts/prepare_imagej_reader.py

# Cheap prerequisite health only; check and verify retain their complete phases.
preflight: sync
	@echo "preflight: uv executable $(UV)"
	$(UV) --version
	$(UV) run --locked --no-sync python -c "import sys, platform; from pathlib import Path; from importlib.metadata import distribution; print('preflight: python', sys.executable, platform.python_version(), platform.platform(), 'prefix', sys.prefix, flush=True); sys.version_info[:3] == (3, 13, 12) or sys.exit('preflight: expected Python 3.13.12'); Path(sys.prefix).resolve() == (Path.cwd() / '.venv').resolve() or sys.exit('preflight: expected current-worktree .venv'); import simrecon, numpy, h5py; print('preflight: imports', [(m.__name__, distribution(m.__name__).version, str(distribution(m.__name__).locate_file('')), m.__file__) for m in (simrecon, numpy, h5py)], flush=True); Path(simrecon.__file__).resolve() == (Path.cwd() / 'src/simrecon/__init__.py').resolve() or sys.exit('preflight: simrecon import is outside current-worktree src/simrecon')"
	$(UV) run --no-project --with hatchling==1.32.4 python -c "import sys, platform; from pathlib import Path; from importlib.metadata import version; print('preflight: isolated python', sys.executable, platform.python_version(), 'prefix', sys.prefix, flush=True); Path(sys.prefix).resolve() != (Path.cwd() / '.venv').resolve() or sys.exit('preflight: build dependency environment is not isolated'); import hatchling; print('preflight: hatchling', version('hatchling'), hatchling.__file__, flush=True); version('hatchling') == '1.32.4' or sys.exit('preflight: expected hatchling 1.32.4')"

coverage-clean:
	$(UV) run --locked coverage erase
	rm -rf artifacts/coverage dist
	mkdir -p artifacts/coverage

lint:
	$(UV) run --locked ruff check src tests scripts

format:
	$(UV) run --locked ruff format --check src tests scripts

types:
	$(UV) run --locked pyright

tests:
	$(UV) run --locked coverage run -m pytest

coverage-combine:
	$(UV) run --locked coverage combine

coverage-json:
	$(UV) run --locked coverage json

coverage-html:
	$(UV) run --locked coverage html

coverage-report:
	$(UV) run --locked coverage report

wheel:
	$(UV) build --wheel

wheel-import:
	$(UV) run --no-project --with ./dist/simrecon-0.1.0-py3-none-any.whl python -c "import simrecon; print(simrecon.__file__)"

audit:
	$(UV) audit --locked
