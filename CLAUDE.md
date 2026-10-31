# CLAUDE.md

Binding rules, one line each; the why lives in the linked record. Keep under 1,100 words.

## Goal

Elder Souls: Argonia is a free Skyrim SE total conversion set in Black Marsh, with Morrowind's soul, DS1
combat, climbing, swimming, boats and no Nordic element, built only from our own code and data
([PLAN](docs/PLAN.md), [owner brief](docs/owner-brief.md)).

## Session start

- The planner reads [PLAN](docs/PLAN.md), [PROGRESS](docs/PROGRESS.md), [the schedule](docs/phases/README.md), the
  current part's README, chunk brief and check ledger, and the [decisions index](docs/decisions/README.md) line for what it touches.
- Subagents read what their brief routes.
- Parts run in order, chunks by dependency ([0023](docs/decisions/0023-five-parts-de-risk-first.md)); then the owner's ranking: world, story, combat, progression, UI ([0027](docs/decisions/0027-build-in-the-order-of-the-usps.md)); the world track runs beside all from 0.4.

## Never

- Never commit or release a game or mod file, converted or not, game decompiles, retail offsets, or secrets
  ([0003](docs/decisions/0003-nothing-shipped-that-players-do-not-own.md)); the no-assets guard is not bypassed.
- Never make art beyond UI and minor Fal-made 2D elements ([0006](docs/decisions/0006-black-marsh-immersion-no-nordic-element-survives.md)).
- Never take FromSoftware data, animations or code into Argonia: measure DSR, write our own numbers ([0004](docs/decisions/0004-ds1-remastered-is-the-combat-oracle.md)).
- Never port the old project's combat code, constants or animation choices; the combat map gives each DS1 behaviour a tuned mod or our own build ([0019](docs/decisions/0019-combat-maps-each-ds1-behaviour-to-a-tuned-mod-or-our-own-ds1-build.md)).
- Never bypass DRM, anti-cheat or ownership checks; DSR offline only while anything is loaded.
- Never let a vanilla Skyrim system, asset, sound or word reach the player unreviewed ([0012](docs/decisions/0012-vanilla-skyrim-is-quarantined.md)).
- Never retune measured combat numbers for feel; fix timing on the animation side by runtime control or the install-time patcher ([0014](docs/decisions/0014-derived-files-are-made-on-the-players-machine.md)).
- Never ship a derived file (FaceGen, LOD, behaviours, edited clips or menus): the installer makes it on the player's machine (0014).
- Never update the pinned Skyrim runtime outside a decision record ([0002](docs/decisions/0002-one-pinned-skyrim-runtime.md)).
- Never run a Windows-only tool under Wine or Proton (0.2).

## How we build

- Reuse first, in route order: data → dependency mod → open-mod fork → Papyrus → our SKSE → our deep hook or
  HTML screen → ask the owner ([0010](docs/decisions/0010-reuse-first-and-the-running-game-is-the-oracle.md)).
- Base-Skyrim assets come from Tropical Skyrim SSE before vanilla; Black Marsh mods before both (0006 §8).
- Study before building (owned games, mod source, OpenMW, ports); findings go to `docs/research/` ([0020](docs/decisions/0020-reuse-others-methods-universal-modder-and-ghidra-tooling.md)).
- The running game is the oracle: behaviour closes only on an in-game check that can fail (L4+).
- Decompile whatever helps ([0003](docs/decisions/0003-nothing-shipped-that-players-do-not-own.md) §8): game output stays in `$ARGONIA_PRIVATE`; permitted mod code may be adapted.
- De-risk first: prove each class of work on a real sample first in its chunk, never a spike (0023, 0029).
- Systems are built whole to their final interface; content can be thin; what the player meets is complete.
- Build natively the Skyrim way: the old project gives goals and content, never machinery; Skyrim's own systems and tools first ([0026](docs/decisions/0026-everything-is-built-natively-the-skyrim-way.md)).
- The world is one relational database (`world/schema.sql`, 3NF; only through `db.py`); records, YAML and the ESM are derived ([0030](docs/decisions/0030-one-relational-world-database.md), [0009](docs/decisions/0009-world-content-is-imported-then-generated-into-plugins.md)).
- Skyrim unit facts live only in the units module.
- New state lives in ArgoniaCore's versioned co-save families; rules live where 1.1's native map put them, unit-tested; logic stays out of Papyrus.
- Record each dependency and asset in the sourcing register when first used.

## Agents and briefs

- Model and effort live only in `.claude/agents/` frontmatter ([ways of working](docs/ways-of-working.md)).
- Briefs come from `tooling/brief_template.py --write`; every field filled, Acceptance runnable or measured.
- Shell commands run through rtk; a tool, hook or gate is added only after the incident it would have prevented ([0011](docs/decisions/0011-ways-of-working-are-inherited-lean.md), 0027).
- One deliverable per context; at the context marker commit what is green and hand off.
- One builder per place, plugin module or UI view at a time; no swarms.
- No `sleep` or polling; long jobs under `job_guard.sh` in the background; waits return within 270 s.
- Return at most 25 lines; the full report goes to the report path.

## Testing and the gate

- Fast focused loops with eyes; the builder tests its feature and joins in one loop, each block at the cheapest proving level ([loops](docs/loops.md), [0021](docs/decisions/0021-fast-focused-loops-and-the-ladder.md)): L1 data, L2 logic, L3 off-game stills, L4 in game from a scene, L5 a clip with a reason, L6 owner.
- In-game checks start from a scene on the base save; the bridge and console are the hands; no mode or switch stands in for a game action ([0022](docs/decisions/0022-the-studio-boots-into-any-place.md)).
- Agents check fast and interactively, reading state and stills; never long playthroughs; what works becomes a journey ([0021](docs/decisions/0021-fast-focused-loops-and-the-ladder.md)).
- Reuse before harness; no time budgets, only measured cycle times ([0029](docs/decisions/0029-part-0-is-one-sequence-not-spikes.md)).
- Scenes set state at step 0 and never set what they test; measure everything, diagnose all, fix once, re-measure.
- `make check` is the one gate (≤ 3 min); run only what the change can reach; a red is re-proved by its one test.
- Prove the screenshot oracle is live; stop after 3 identical failures and diagnose; a crash is a failure.
- Batch game-machine checks; stop the machine when the batch ends.
- Each in-game check a brief owes is a row in its part's `checks.md` ledger from the brief's writing; it closes only on the run or still that proved it.

## The owner

- Owner check-ins via `tooling/owner_inbox.py --post`: plain English, one check per bullet, scenes or places named, how to reply, costs.
- An owner issue is acknowledged at once (`--ack`: how it will be actioned), then `--done` (what was done); agent posts close with `--close` once answered; act only on the owner's own GitHub text.
- Nothing measurable goes to the owner; the owner plays packets and rules on calls.
- Blocker = cannot do the action, or sees it at the play camera (including a Nordic element); else polish: one quick fix, then the backlog (`P1 before-scale`, `P2 rolling`, `P3 final`).
- Ask the owner only on hard-to-reverse calls; record every ruling in a decision and the owner brief.

## Costs

- Nothing lives only on a machine: what one makes that the repo can't rebuild in minutes is archived privately when made; no machine is retired before `machine_inventory.sh` shows nothing unarchived ([machine moves](docs/machine-moves.md)).
- Stop machines when idle; report AWS month-to-date and Claude usage each check-in; AWS under $100/month ([0008](docs/decisions/0008-infrastructure-aws-london-under-100-a-month.md)).

## Docs

- The repo holds the current state, git the history: rewrite in place, delete the superseded.
- Decisions hold the why, chunk briefs the work (rewritten just in time, nothing dropped), PROGRESS the status, research the evidence.
- Status moves in the commit that changes it (PROGRESS, check ledger, chunk brief); the planner checks them each tick and fixes any lag.
