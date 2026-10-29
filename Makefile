# The one gate. `make check` runs every target in parallel and ends with one list of the reds.
RED := .git/check-red
PARTS := guard lint unit budget links skse
# A failing part records its name, then fails.
FAIL = || { echo $@ >> $(RED); exit 1; }

.PHONY: check hooks $(PARTS)

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

# skse/core and the bridge protocol: pure C++ unit tests built natively on the build VM (0.3 §b).
skse:
	@bash skse/check.sh $(FAIL)

hooks:
	@bash tooling/guards/install_hooks.sh
