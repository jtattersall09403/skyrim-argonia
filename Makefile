# The one gate: `make check` runs lint, the unit tests and the no-assets guard.
PY := $(firstword $(wildcard $(HOME)/.argonia/venv/bin/python) python3)
RUFF := $(firstword $(wildcard $(HOME)/.argonia/venv/bin/ruff) $(shell command -v ruff) python3 -m ruff)

.PHONY: check guard lint unit adaptation questtext questform reach hooks deploy plugin plugin-check plugin-seed map

check: guard lint unit adaptation questtext questform reach
	@echo "CHECK GREEN"

guard:
	@python3 tooling/guards/no_assets.py --tree

lint:
	@$(RUFF) check -q tooling tools infra .claude

unit:
	@$(PY) -m pytest -q tooling/tests tools/tests; rc=$$?; [ $$rc -eq 0 ] || [ $$rc -eq 5 ]
	@bash skse/check.sh

# The adaptation ledger's whole-set checks (phase 2): places, edits, prerequisites, danger, capacity, lore, 0006, 0035.
adaptation:
	@$(PY) -m tools.argonia_world.adaptation_check

# The slice quests' player-visible text, from the story data (review-writing section E): see tools/argonia_world/quest_text_check.py.
questtext:
	@$(PY) -m tools.argonia_world.quest_text_check check

# Every staged quest record compiled to the quest form and checked, against story/data/questform_owed.json
# (docs/design/quest-form.md); the example form passes.
questform:
	@$(PY) -m tools.questform gate

# Those compiled forms played by the paper game's walker: every quest reaches a completed ending from a new game,
# against tools/playtest/reach_owed.json (docs/design/paper-playtest.md).
reach:
	@$(PY) -m tools.playtest reach --compiled --gate

hooks:
	@bash tooling/guards/install_hooks.sh

# Our plugin (decision 0018): plugin/Argonia (Spriggit YAML, the source) -> out/Argonia.esp; the check adds the round
# trip (serialised back, no diff) and the read-back table docs/research/skyrim/argonia-esp-records.md.
plugin:
	@bash tools/ArgoniaPlugin/plugin.sh build

plugin-check:
	@bash tools/ArgoniaPlugin/plugin.sh check

# Regenerate plugin/Argonia from tools/ArgoniaPlugin/shutdown.json and the staged load order's winners.
plugin-seed:
	@bash tools/ArgoniaPlugin/plugin.sh seed

# Our plugin and compiled scripts onto the play machine (infra/gpu-box/deploy.sh); run under tooling/job_guard.sh.
deploy:
	@bash infra/gpu-box/deploy.sh $(DEPLOY_ARGS)

# The offline BM&V map (tools/bmv_map): out/bmv-map/index.html from Black Marsh.esm's LAND and the census; never committed.
map:
	@$(PY) -m tools.bmv_map.build build && $(PY) -m tools.bmv_map.build verify
