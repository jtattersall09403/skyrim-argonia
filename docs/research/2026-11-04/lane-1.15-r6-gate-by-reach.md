# Lane 1.15-r6-gate-by-reach: the gate runs only what a change reaches

## Measured
- Inside the pre-batch (lane-1.15-r6-fast-loop-2): gate median 330 s, p90 361 s (9 runs, 2873 s in all, 5.4 %).
- One full gate, step by step, run one step at a time on the build VM at load 8 (other lanes building), 2026-11-04 08:40:
  guard 6 s, lint red 0 s (a ruff finding in another lane's dirty file), unit 638 s (rc 2: red from other lanes' dirty files),
  budget 1 s, links 1 s, records 0 s (red: PROGRESS 1.15 status wording, not this lane), ledger 0 s, world 25 s,
  plugin-check queued over 10 min behind other lanes' `make plugin` / `navmesh` on out/.plugin.lock (its own time is
  ~123 s idle, fast-loop-2), skse and immersion and ui not reached before this report. A full `make check -j` was started
  twice and lost (a spot reboot at 08:34 and a 15 min wait under load); `unit` is the sink at 638 s under load.

## The tool
`tooling/check_reach.py --since <sha|ref|auto> [--plan] [--record]`; `make check-reach SINCE=<sha>` (default origin/main,
so lanes' old use is unchanged; tooling/reach_tests.sh is now unused). A declared RULES map (path glob -> steps; `unit` means
the nearest `tests/` dir or sibling test_*.py). Changed = `git diff --name-only <sha>` plus untracked. An unmapped path (or
Makefile) runs `make check`, the conservative default. It prints each step as RUN (with the path that reads it) or skip
(no changed path reads it), then per-step seconds and REACH GREEN/RED. Steps run via `make <step>`, so the locks and
FAIL logic are the gate's own.

## Tests (tooling/tests/test_check_reach.py, 6 pass)
docs-only -> links + records only; water-only -> lint, unit (tools/argonia_world/water/tests only) and world, not
plugin-check; unmapped path and Makefile -> everything; CLAUDE.md -> budget; skyrim_units.py -> the whole unit step.

## Wiring
r5_prebatch.sh `step gate` is now `check_reach.py --since auto --record`: the sha and time of the last green gate sit in
~/.argonia/round/gate-green (written only by a green run on a clean tracked tree); missing or older than a day runs the
full `make check`. chain.sh calls the pre-batch, so it needed no edit.

## Saving on this round's changes (969fe19b~1..HEAD, 39 paths)
The map reaches 9 of 12 steps (not skse, ui, guard-only none): lint, unit (11 test dirs, not tools/stream, infra, ui),
budget, links, records, ledger, world, plugin-check, immersion; skips skse and ui and the node/cloudflare half of unit.
Two paths were unmapped (tests/test_round_retro.py, the navmesh .cs) and are now rules. Estimated cut for this change
set about 3 of 12 steps and about a third of unit; the bigger saving is a round whose changes are docs, journeys or
water (seconds to 1-2 min instead of 330 s). Not measured end to end: the red state of other lanes' files blocked a clean
full-vs-reach comparison today.
