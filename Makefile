# The one gate: `make check` runs lint, the unit tests and the no-assets guard.
PY := $(firstword $(wildcard $(HOME)/.argonia/venv/bin/python) python3)
RUFF := $(firstword $(wildcard $(HOME)/.argonia/venv/bin/ruff) $(shell command -v ruff) python3 -m ruff)

.PHONY: check guard lint unit hooks deploy

check: guard lint unit
	@echo "CHECK GREEN"

guard:
	@python3 tooling/guards/no_assets.py --tree

lint:
	@$(RUFF) check -q tooling tools infra .claude

unit:
	@$(PY) -m pytest -q tooling/tests tools/tests; rc=$$?; [ $$rc -eq 0 ] || [ $$rc -eq 5 ]

hooks:
	@bash tooling/guards/install_hooks.sh

# Our plugin and compiled scripts onto the play machine (infra/gpu-box/deploy.sh); run under tooling/job_guard.sh.
deploy:
	@bash infra/gpu-box/deploy.sh $(DEPLOY_ARGS)
