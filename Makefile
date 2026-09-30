UV ?= uv

.PHONY: verify
verify:
	$(UV) sync --locked --all-groups
	$(UV) run --locked coverage erase
	rm -rf artifacts/coverage dist
	mkdir -p artifacts/coverage
	$(UV) run --locked ruff check src tests
	$(UV) run --locked ruff format --check src tests
	$(UV) run --locked pyright
	$(UV) run --locked coverage run -m pytest
	$(UV) run --locked coverage combine
	$(UV) run --locked coverage json
	$(UV) run --locked coverage html
	$(UV) run --locked coverage report
	$(UV) build --wheel
	$(UV) run --no-project --with ./dist/simrecon-0.1.0-py3-none-any.whl python -c "import simrecon; print(simrecon.__file__)"
	$(UV) audit --locked
