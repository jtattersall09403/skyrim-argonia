# The one gate. `make check` runs every target in parallel and ends with one list of the reds.
RED := .git/check-red
PARTS := guard lint unit budget links world plugin-check skse immersion
# A failing part records its name, then fails.
FAIL = || { echo $@ >> $(RED); exit 1; }

.PHONY: check hooks plugin db $(PARTS)

check:
	@rm -f $(RED)
	@$(MAKE) -k -j --no-print-directory $(PARTS) || true
	@if [ -s $(RED) ]; then echo "CHECK RED: $$(sort $(RED) | tr '\n' ' ')"; rm -f $(RED); exit 1; else echo "CHECK GREEN"; fi

guard:
	@python3 tooling/guards/no_assets.py --tree $(FAIL)

lint:
	@if command -v ruff >/dev/null; then ruff check tooling tools; \
	elif python3 -m pyflakes --version >/dev/null 2>&1; then python3 -m pyflakes tooling tools; \
	else python3 -m compileall -q tooling tools >/dev/null; fi $(FAIL)

unit:
	@python3 -m pytest -q --ignore=tooling/tests/test_word_budget.py tooling/tests tools; rc=$$?; [ $$rc -eq 0 ] || [ $$rc -eq 5 ] $(FAIL)

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
plugin:
	@python3 tools/ArgoniaGen/pipeline.py plugin

# FormIDs append-only, pieces resolved, regenerate twice identical, plugin/ current, Spriggit round trip byte-identical.
plugin-check:
	@python3 tools/ArgoniaGen/pipeline.py check $(FAIL)

hooks:
	@bash tooling/guards/install_hooks.sh
