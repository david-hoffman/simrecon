UV ?= uv
PYTHON ?= python3
VERIFY_ARGS ?=

.PHONY: check verify sync quality coverage-clean lint format types tests coverage-combine coverage-json coverage-html coverage-report wheel wheel-import audit

# Fast feedback uses the same locked sync and quality commands as full verification.
check: sync
	$(MAKE) --no-print-directory quality UV="$(UV)"

quality: lint format types

# The wrapper records each required phase; it does not replace or skip the gate.
verify:
	$(PYTHON) scripts/verify.py --uv "$(UV)" --make "$(MAKE)" $(VERIFY_ARGS)

sync:
	$(UV) sync --locked --all-groups

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
