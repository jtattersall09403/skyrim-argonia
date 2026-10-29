<!-- imported unchanged from elder-souls-argonia docs/decisions/0131-one-check-gate.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0131 — One check gate: `npm run check` replaces preflight, the runner and docs:check; heavy checks live in the tool that owns the data

**Why:** a lean gate that stays fast and light; committed generated data going
stale was the commonest red, so `regen.py --check` catches it. **Supersedes:** the preflight paragraphs of 0106 (decisions 3 and 9, edited
in place) and every other record's preflight, `--runner` and `docs:check` rule.

## Decisions

1. **One gate, `npm run check`** (`tooling/repo-standards/check.mjs`). It runs
   typecheck; every vitest workspace; `regen.py --check` (every committed
   generated artefact recomputed into a temp dir and diffed, every stale file
   listed; `--fix` writes them); the docs check, prose lint, credits,
   site-refs, python-deps and bundle-load checks; the python contract tests
   (world-schema, repo-standards, kit_compress, water); and the placement and
   workbench unit tests on small synthetic fixtures (`-m "not heavy"`).
   Jobs run in parallel, every job runs to completion, and the summary lists
   every red. Budget: at most 3 min wall and 4 GiB own peak on this machine.
2. **CI runs the same command.** On push to main, from a clean clone: `npm ci`,
   `npm run check`, then the build and deploy. There is no sharded copy, no
   nightly suite and no separate runner. CI is as fast as the local gate.
3. **Heavy real-data checks live in the tool that owns the data** and run
   when its inputs change, never as a suite. A generator CLI takes `--check`
   through `tooling/repo-standards/freshness.py` (a hash stamp of its inputs
   against its manifest; recompute and diff only when the inputs changed) and
   is registered with `regen.py`. `wb.py publish` validates its own place
   (blueprint validation, the place gates, bundle validation). A test that
   reads the vault, the province or the live blueprints carries the `heavy`
   marker; a collection guard fails any unmarked test that opens those paths.
4. **Who runs it.** The planner's `check` agent runs the code review
   (`review_gate.py`, once per batch; parallel rounds scope theirs with `--open <id> --paths`, `ES_BATCH=<id>` on the check, `--close <id>`) and then `npm run check` once
   per batch under `job_guard.sh`. Lanes run only the tests beside their
   change. A test red on HEAD is fixed first by whoever meets it.
5. **A gate earns its place by what it catches per second.** A check that
   catches nothing a cheaper check or its owning tool would not, or that has
   never failed, is deleted. Each new gate is made to fail on purpose once
   (edit one generated file, edit one input of one `--check` tool) before it is
   trusted (standard 14).
6. **Nothing else gates a commit.** No preflight, time rules, docs-only
   exemption, separate `docs:check` script or name-only freshness test; the
   gate is `npm run check` and each tool's own `--check`.

7. **Amendment (owner, 2026-10-20): the review is triggered by size, not once
   per round.** A batch code review is due when landed commits in shipped code
   (`packages/` and `apps/`, no generated files, never `lanes/` or a live
   working tree) since the last review stamp pass 1,500 changed lines (added +
   deleted), or before any pod pass is launched, whichever comes first; the
   close pass covers the tail. `lane_status.py` prints the count and `due` or
   `not due` on its last line, reading `reviewedHead` from the review stamp.
   Why: one review over 21 lanes gave 46 findings, a five-child fix lane, and
   pod passes that filmed code the review then changed. A review costs about
   10 min of CPU plus one agent, so below ~1,000 lines it is waste, and above
   ~2,000 lines the findings interact.

From 0106 stand: one review per batch (decision 13), the gates that never go
(decision 9, with `npm run check` in place of the full runner), miners
merge per asset, measured throttles, rulings as rows.
