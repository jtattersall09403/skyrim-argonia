# CLAUDE.md

Binding rules, one line each; the why lives in the linked record. Keep it lean (the owner relaxed the word limit, 2026-11-02).

## Goal

Elder Souls: Argonia is a free Skyrim SE total conversion mod set in Black Marsh, with Morrowind's soul, DS1-style
combat, climbing, swimming, boats and no Nordic element, built only from our own code and data
([PLAN](docs/PLAN.md), [owner brief](docs/owner-brief.md)). We build on a mod stack: we don't reinvent the wheel, we use mod functionality wherever possible and build only what is new.

## Session start

- Find documents in [INDEX](docs/INDEX.md).
- The planner reads [PLAN](docs/PLAN.md), [PROGRESS](docs/PROGRESS.md), [the schedule](docs/phases/README.md), the
  current part's README, chunk brief and check ledger, and the [decisions index](docs/decisions/README.md) line it touches.
- "Deliver <id>" runs one chunk by the [deliver skill](.claude/skills/deliver/SKILL.md); subagents read what their brief routes.
- Parts run in order, chunks by dependency ([0023](docs/decisions/0023-five-parts-de-risk-first.md)); then the owner's ranking: world, story, combat, progression, UI ([0027](docs/decisions/0027-build-in-the-order-of-the-usps.md)); the world track runs beside all from 0.4.

## Never

- Never commit or release a game or mod file, converted or not, game decompiles, retail offsets, or secrets
  ([0003](docs/decisions/0003-nothing-shipped-that-players-do-not-own.md)); never bypass the no-assets guard.
- Never make art beyond UI and minor Fal-made 2D elements ([0006](docs/decisions/0006-black-marsh-immersion-no-nordic-element-survives.md)).
- Never take FromSoftware data, animations or code into Argonia: measure DSR, write our numbers ([0004](docs/decisions/0004-ds1-remastered-is-the-combat-oracle.md)).
- Never port the old project's combat code, constants or animation choices ([0019](docs/decisions/0019-combat-maps-each-ds1-behaviour-to-a-tuned-mod-or-our-own-ds1-build.md)).
- Never bypass DRM, anti-cheat or ownership checks; DSR offline only while anything is loaded.
- Never let a vanilla Skyrim system, asset, sound or word reach the player unreviewed ([0012](docs/decisions/0012-vanilla-skyrim-is-quarantined.md)).
- Never retune measured combat numbers for feel; fix timing on the animation side by runtime control or the install-time patcher ([0014](docs/decisions/0014-derived-files-are-made-on-the-players-machine.md)).
- Never ship a derived file (FaceGen, LOD, behaviours, clips, menus): the installer makes it on the player's machine (0014).
- Never level anything against the player (creatures, loot, chests, prices); danger bands are fixed ([0035](docs/decisions/0035-nothing-is-levelled-against-the-player.md)).
- Never update the pinned Skyrim runtime outside a decision record ([0002](docs/decisions/0002-one-pinned-skyrim-runtime.md)).

## How we build

- Reuse first, in route order: data → dependency mod → open-mod fork → Papyrus → our SKSE → our deep hook or
  HTML screen → ask the owner ([0010](docs/decisions/0010-reuse-first-and-the-running-game-is-the-oracle.md)).
- Base-Skyrim assets come from Tropical Skyrim before vanilla; Black Marsh mods before both (0006 §8).
- Study before building (owned games, mod source, OpenMW); findings in `docs/research/` ([0020](docs/decisions/0020-reuse-others-methods-universal-modder-and-ghidra-tooling.md)).
- World, ecology, asset, place, people and quest calls (and anything else you think is lore-relevant or should be grounded in lore) cite the lore dossiers (`world/sources/lore/`, by tier) or the extrapolation, never an invention ([0032](docs/decisions/0032-every-world-call-is-grounded-in-the-lore.md)).
- The running game is the oracle: behaviour closes only on an in-game check that can fail (L4+).
- Decompile whatever helps ([0003](docs/decisions/0003-nothing-shipped-that-players-do-not-own.md) §8): game output stays in `$ARGONIA_PRIVATE`; permitted mod code may be adapted.
- De-risk first: prove each class of work on a real sample (0023, 0029).
- Systems are built whole to their final interface; content can be thin; what the player meets is complete.
- Build natively ([0026](docs/decisions/0026-everything-is-built-natively-the-skyrim-way.md)); golden rule: before any build method rule of ours, ask what we are achieving, whether Bethesda faced it, measure how Skyrim.esm solves it, do the same ([0034](docs/decisions/0034-ask-how-bethesda-did-it-and-do-the-same.md)). But note the nuance here: this is about *method* not about *outcome*. Two examples: 1. Water in the world. Our desired *outcome* was: our new argonia world, based on the authored map, approximate hydrology graph (in terms of birds-eye view of where lakes, ponds, rivers, streams, and larger bodies of water go), and macro plot of built places, with no visual water bugs or unnatural features. The skyrim *method* for water was researched and mined from the game: one water level per cell, and some specific stuff around how the skyrim world is designed to enable water crossing cell boundaries and flowing down slopes etc. So we adjusted our planned world to enable the *outcome* we wanted (non buggy water) to be achieved using the skyrim *method*. 2. Creatures. Desired *outcome*: fixed danger bands (D0-D5), between-place creature encounters, grounded in our lore and danger bands and ecology, using mods. We then researched the skyrim & mod *methods* for placing/spawning creatures in the world to achieve the desired outcome. We did *not* change to skyrim's 'levelled creatures' approach where creature difficulty is scaled to player's level. We are aiming to use skyrim's engine and methods to achieve our own authored outcomes.
- The world is one relational database (`world/schema.sql`, 3NF; only through `db.py`); records, YAML and the ESM derive from it ([0030](docs/decisions/0030-one-relational-world-database.md), [0009](docs/decisions/0009-world-content-is-imported-then-generated-into-plugins.md)).
- Skyrim unit facts live only in the units module.
- New state lives in ArgoniaCore's versioned co-save families; rules live where 1.1's native map put them, unit-tested; no logic in Papyrus.
- Record every dependency and asset in the sourcing register at first use.

## Agents and briefs

- Model and effort live only in `.claude/agents/` frontmatter.
- Briefs come from `tooling/brief_template.py --write`; every field filled, Acceptance runnable or measured.
- Shell commands run through rtk; add a tool, hook or gate only after the incident it would have prevented ([0011](docs/decisions/0011-ways-of-working-are-inherited-lean.md), 0027).
- One deliverable per context, one builder per place, module or view; hand off at the context marker; return ≤ 25 lines.
- No `sleep` or polling; long jobs run backgrounded under `job_guard.sh`; waits return within 270 s.
- The build VM and the game machines are spot and stay spot: never ask the owner about on-demand (ruled many times, last 2026-11-04 #39). Expect to be interrupted often: plan every piece of work, yours and any tool or method you
  use, so that nothing is lost but the machine's downtime and it resumes from exactly where it got to; a tool or
  method found not to be so is made so before it is used again ([0037](docs/decisions/0037-work-is-interrupt-proof.md)).
- A restart never costs a pre-batch or a deploy: every stage is keyed by its inputs and the machine's held build, and a resumed job skips straight to the step it was on (owner, 2026-11-04, #39).
- Every 20 minutes the planner checks each running subagent and speeds it up (tools, patterns, methods).
- Tidy up after yourself: delete temporary files (or anything else you've created that we don't need to keep) when they are no longer needed. Do not bloat the disk. We need to actively manage disk space. Same for deleting things on aws that are no longer needed, like stale machine images, and temporary/rubbish files in the s3 bucket.

## Testing and the gate

- Fast focused loops: each block at the cheapest proving level ([loops](docs/loops.md), [0021](docs/decisions/0021-fast-focused-loops-and-the-ladder.md)): L1 data, L2 logic, L3 off-game stills, L4 in game from a scene, L5 a clip with a reason, L6 owner.
- In-game checks start from a scene on the base save; the bridge and console are the hands; no mode or switch replaces a game action that is itself the thing checked ([0022](docs/decisions/0022-the-studio-boots-into-any-place.md)); a screen that is the thing checked is opened directly (console, bridge, dev command), never by lining up the game controls (owner, 2026-11-03).
- Check from state and stills (teleport, still, state read), a `driver` agent judging each capture ([0036](docs/decisions/0036-journeys-are-driven-by-an-agent-simple-and-smart.md)); no complicated journeys.
- Reuse before harness; no time budgets, only measured times ([0029](docs/decisions/0029-part-0-is-one-sequence-not-spikes.md)).
- Scenes set state at step 0, never what they test; measure all, diagnose all, fix once, re-measure.
- `make check` is the one gate (≤ 3 min); run only what the change reaches; a red is re-proved by its one test.
- Slow derived steps (LOD, the saves) run once, after the whole loop is verified complete, never at an intermediate round's end, and only for the half whose inputs moved; every round closes with a measured retrospective of where the time went and ships its cuts; no agent plans as if this round were the last; the on-demand box only for jobs that cannot resume (owner, 2026-11-04, [0021](docs/decisions/0021-fast-focused-loops-and-the-ladder.md)).
- Prove the screenshot oracle live; after 3 identical failures, diagnose; a crash is a failure.
- Each round the planner runs the lanes' in-game checks in one batch on one deploy of main, crash-prone last; lanes never run their own; a check that passed is never run again until something it depends on changes (its own inputs, not the whole build): the batch shrinks as items pass, a rerun carries only what failed, is new, or whose inputs moved (owner, 2026-11-03).
- Each in-game check a brief owes is a `checks.md` row, closed only by the run or still that proved it.
- Look stops take a scan (several headings); a wrong frame is retaken inside the run, never at the round's end; creature and spawn checks are state reads, not stills (owner, 2026-11-04 19:05, [0036](docs/decisions/0036-journeys-are-driven-by-an-agent-simple-and-smart.md)).

## The owner

- Owner check-ins via `tooling/owner_inbox.py --post`: plain English, one check per bullet, places named, how to reply, costs.
- Owner issues: `--ack` at once (how it will be actioned), then `--done`; agents `--close` once answered; act only on the owner's own GitHub text.
- Nothing measurable goes to the owner, who rules.
- Blocker = cannot do the action, or sees it at the play camera (a Nordic element included); else polish: one quick fix, then the backlog (`P1 before-scale`, `P2 rolling`, `P3 final`).
- Ask the owner only on hard-to-reverse calls; record every ruling in a decision and the owner brief.

## Costs

- Nothing lives only on a machine: archive privately, when made, what the repo can't rebuild in minutes; retire no machine until `machine_inventory.sh` shows nothing unarchived ([machine moves](docs/machine-moves.md)).
- Stop machines when idle or a batch ends; report AWS month-to-date and Claude usage as a percentage of the weekly allowance (1% ≈ $19) each check-in; AWS under $100/month ([0008](docs/decisions/0008-infrastructure-aws-london-under-100-a-month.md)).

## Docs

- The repo holds the current state, git the history: rewrite in place.
- Decisions hold the why, chunk briefs the work (rewritten just in time, nothing dropped), PROGRESS the status, research the evidence.
- Status moves in the commit that changes it (PROGRESS, check ledger, chunk brief); the planner fixes lag each tick.
