# The one gate. `make check` runs every target in parallel and ends with one list of the reds.
RED := .git/check-red
PARTS := guard lint unit budget links world plugin-check skse immersion
# The build VM's pinned venv (infra/build-vm/toolchain.lock) when present: numpy, pytest, pyyaml.
PY := $(firstword $(wildcard $(HOME)/.argonia/venv/bin/python) python3)
# A failing part records its name, then fails.
FAIL = || { echo $@ >> $(RED); exit 1; }

.PHONY: check hooks plugin db chart navmesh $(PARTS)

check:
	@rm -f $(RED)
	@$(MAKE) -k -j --no-print-directory $(PARTS) || true
	@if [ -s $(RED) ]; then echo "CHECK RED: $$(sort $(RED) | tr '\n' ' ')"; rm -f $(RED); exit 1; else echo "CHECK GREEN"; fi

guard:
	@python3 tooling/guards/no_assets.py --tree $(FAIL)

lint:
	@if [ -x $(HOME)/.argonia/venv/bin/ruff ]; then $(HOME)/.argonia/venv/bin/ruff check -q tooling tools; \
	elif command -v ruff >/dev/null; then ruff check -q tooling tools; \
	elif python3 -m pyflakes --version >/dev/null 2>&1; then python3 -m pyflakes tooling tools; \
	else python3 -m compileall -q tooling tools >/dev/null; fi $(FAIL)

unit:
	@$(PY) -m pytest -q --ignore=tooling/tests/test_word_budget.py tooling/tests tools; rc=$$?; [ $$rc -eq 0 ] || [ $$rc -eq 5 ] $(FAIL)

budget:
	@python3 -m pytest -q tooling/tests/test_word_budget.py $(FAIL)

links:
	@python3 tooling/check_links.py $(FAIL)

# The world database (decision 0030): the load with every constraint and the named checks; no tool reads world/ itself.
world:
	@python3 -m tools.argonia_world.db check && python3 tools/argonia_world/check_world_reads.py $(FAIL)

# out/world.sqlite for DuckDB, pandas or the sqlite3 shell.
db:
	@python3 -m tools.argonia_world.db build

# skse/core and the bridge protocol: pure C++ unit tests built natively on the build VM (0.3 §b).
skse:
	@bash skse/check.sh $(FAIL)

# The immersion inventory's counts (decision 0006 §2); binding from 2.17 with IMMERSION_BIND=1.
immersion:
	@python3 tools/immersion/inventory.py --gate $(FAIL)

# Records (0.4 §a): world -> intermediate JSON -> ArgoniaGen (Mutagen) -> out/Argonia.esm -> Spriggit plugin/Argonia/.
# One build at a time: two lanes' parallel builds raced on out/ (2026-10-29); the second waits for the lock.
plugin:
	@mkdir -p out && flock out/.plugin.lock $(PY) tools/ArgoniaGen/pipeline.py plugin

# FormIDs append-only, pieces resolved, regenerate twice identical, plugin/ current, Spriggit round trip byte-identical.
plugin-check:
	@mkdir -p out && flock out/.plugin.lock $(PY) tools/ArgoniaGen/pipeline.py check $(FAIL)

hooks:
	@bash tooling/guards/install_hooks.sh

# The parchment chart (2.W4 §c): out/chart/ layers, copies, tiles, index and the L1 checks; not in the gate (~100 s,
# ~1 GB); the gate's part is tools/chart/tests (the sample's pinned hash). Pelagiad: python -m tools.chart fetch-font.
chart:
	@$(PY) -m tools.chart render

# The navmesh (2.W4 §b): the province's NAVM and NAVI (tools/navmesh, DotRecast), then out/ArgoniaWorld.esm with
# them, verified byte for byte; not in the gate (tens of minutes); the gate's part is plugin-check's four-cell hash.
navmesh:
	@mkdir -p out && flock out/.plugin.lock $(PY) tools/ArgoniaGen/pipeline.py navmesh
