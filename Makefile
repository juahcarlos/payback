.PHONY: bootstrap lint test

UV ?= uv
COV_FAIL_UNDER ?=

bootstrap:
	@command -v $(UV) >/dev/null 2>&1 || \
		(pip install --user uv && echo "uv installed")
	$(UV) sync --group lint --group dev


lint: bootstrap
	$(UV) run ruff check .
	$(UV) run mypy .


test: bootstrap
	$(UV) run pytest \
		--cov=app \
		--cov-report=term \
		--cov-report=xml \
		$(if $(COV_FAIL_UNDER),--cov-fail-under=$(COV_FAIL_UNDER))
