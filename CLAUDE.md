# CLAUDE.md

Binding rules, one line each; the why lives in the linked record. Keep under 1,100 words.

## Goal

Elder Souls: Argonia is a free Skyrim SE total conversion set in Black Marsh, with Morrowind's soul, DS1
combat, climbing, swimming, boats and no Nordic element, built only from our own code and data
([PLAN](docs/PLAN.md), [owner brief](docs/owner-brief.md)).

## Session start

- The planner reads [PLAN](docs/PLAN.md) in full, then [PROGRESS](docs/PROGRESS.md), then the current phase
  file in `docs/phases/`, then the [decisions index](docs/decisions/README.md) line for anything it touches.
- Subagents read what their brief routes.
- Phase 0 starts with [P0](docs/phases/P0-bootstrap.md); do the phases in dependency order.

## Never

- Never commit or release a game or mod file, converted or not, decompiled code, retail offsets, or secrets
  ([0003](docs/decisions/0003-nothing-shipped-that-players-do-not-own.md)); the no-assets guard is not bypassed.
- Never make art beyond UI and minor Fal-made 2D elements ([0006](docs/decisions/0006-black-marsh-immersion-no-nordic-element-survives.md)).
- Never take FromSoftware data, animations or code into Argonia: measure DSR, write our own numbers ([0004](docs/decisions/0004-ds1-remastered-is-the-combat-oracle.md)).
- Never bypass DRM, anti-cheat or ownership checks; DSR only offline while anything is loaded.
- Never let a vanilla Skyrim system, asset, sound or word reach the player unreviewed ([0012](docs/decisions/0012-vanilla-skyrim-is-quarantined.md)).
- Never retune measured combat numbers for feel; fix timing on the animation side.
- Never update the pinned Skyrim runtime outside a decision record ([0002](docs/decisions/0002-one-pinned-skyrim-runtime.md)).

## How we build

- Reuse first, in route order: data → dependency mod → open-mod fork → Papyrus → our SKSE → our deep hook or
  HTML screen → ask the owner ([0010](docs/decisions/0010-reuse-first-and-the-running-game-is-the-oracle.md)).
- Base-Skyrim assets come from Tropical Skyrim SSE before vanilla; Black Marsh mods before both (0006 §8).
- Study before building: owned games, mod source, OpenMW's source, reference ports; record findings in `docs/research/`.
- The running game is the oracle: behaviour closes only on an in-game check that can fail (L4+).
- Ghidra is a scalpel: targeted headless scripts for a named question; output stays in `$ARGONIA_PRIVATE`.
- Every system is built to its final interface; content can be thin, systems ship whole.
- World data lives in `world/` and is generated into records; Spriggit YAML in `plugin/` is reviewed, the ESM is a build output ([0009](docs/decisions/0009-world-content-is-imported-then-generated-into-plugins.md)).
- Skyrim unit facts live only in the units module.
- New state lives in ArgoniaCore's co-save; rules live in the pure C++ core with unit tests.
- Record every dependency and asset in the sourcing register in the same commit that first uses it.

## Agents and briefs

- Model and effort live only in `.claude/agents/` frontmatter ([ways of working](docs/ways-of-working.md)).
- Briefs come from `tooling/brief_template.py --write`: Lane, Paths, Acceptance (runnable or measured), Report path, Test level, Route.
- One deliverable per context; at the context marker commit what is green and write the hand-off note.
- One builder per place, plugin module or UI view at a time; no swarms.
- No `sleep` or polling; long jobs under `job_guard.sh` in the background; waits return within 270 s.
- Return at most 25 lines; the full report goes to the brief's report path.

## Testing and the gate

- Test at the cheapest sufficient level (L1 data, L2 unit, L3 UI harness, L4 in game, L5 clip with a reason, L6 owner).
- `make check` is the one gate (≤ 3 min); run only what the change can reach; a red is re-proved by its one test.
- Prove the screenshot oracle is live; stop after 3 identical failures and diagnose; a crash is a failure.
- Batch GPU-box checks; stop the GPU box when the batch ends.

## The owner

- Owner check-ins via `tooling/owner_inbox.py --post`: plain English, one check per bullet, how to reply, costs.
- Nothing measurable goes to the owner; the owner plays packets and rules on the open calls.
- Blocker = cannot do the action, or sees it at the play camera (including a Nordic element); else polish: one quick fix, then the backlog.
- Ask the owner only on hard-to-reverse calls; record every ruling in a decision and the owner brief.

## Costs

- Stop machines when idle; report AWS month-to-date and Claude usage in every check-in; stay under $100/month of AWS ([0008](docs/decisions/0008-infrastructure-aws-london-under-100-a-month.md)).

## Docs

- The repo holds the current state, git the history: rewrite in place, delete the superseded.
- Decisions hold the why, phase files the work, PROGRESS the status, research the evidence.
