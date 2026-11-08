# CLAUDE.md

Binding rules, one line each; the why lives in the linked record.

## Goal

Elder Souls: Argonia is vanilla Skyrim SE + Black Marsh & Valenwood as the default world + the soulslike
collection xyf1u3 + FreeClimb + Magic Expanded, with our storyline, quests and factions modded on top of BM&V's
world with minimal tweaks ([PLAN](docs/PLAN.md), [0038](docs/decisions/0038-the-pivot-bmv-is-the-world.md)).

## Session start

- Read [PLAN](docs/PLAN.md), [PROGRESS](docs/PROGRESS.md) and the current phase's file in `docs/phases/`; that file is the work and is edited as it goes.
- Read the owner inbox (`tooling/owner_inbox.py --list`); an owner reply is acknowledged before anything else.

## Never

- Never commit a game or mod file, converted or not, decompiles, or secrets ([0003](docs/decisions/0003-nothing-shipped-that-players-do-not-own.md)); never bypass the no-assets guard.
- Never make art; never let a Nordic element reach the player through what we add ([0006](docs/decisions/0006-black-marsh-immersion-no-nordic-element-survives.md)).
- Never level anything against the player ([0035](docs/decisions/0035-nothing-is-levelled-against-the-player.md)).
- Never update the pinned runtime outside a decision ([0002](docs/decisions/0002-one-pinned-skyrim-runtime.md)); never bypass DRM or ownership checks.
- Never test in game yourself when the owner can: post an owner check instead ([PLAN §2](docs/PLAN.md)).
- Never leave the build VM (on demand, 8 to 10 hours a day) running idle; the play machine is the g4dn.xlarge on demand and stops itself when idle ([0039](docs/decisions/0039-the-play-machine-is-a-g4dn-on-demand.md)).

## How we build

- Reuse first: a mod or a record before a script; Papyrus only where a record cannot do it; our own SKSE plugin where no mod, record or script does the job (owner, #51, 2026-11-06).
- Prove each kind of change once as a building block (PLAN Phase 3; the block set is derived from the written act in Phase 2), then copy the block; a new kind of change is a new block.
- Records are Spriggit YAML in `plugin/`, built to the ESP on the build VM; xEdit and houseCARL on the play machine are the checkers; the Creation Kit only for the Papyrus compiler and FaceGen ([0018](docs/decisions/0018-the-creation-kit-is-a-tool-not-the-workflow.md)).
- Story, people and quest calls cite the lore (`story/lore/`) or the extrapolation ([0032](docs/decisions/0032-every-world-call-is-grounded-in-the-lore.md)); quests and dialogue are written through the skills ([0024](docs/decisions/0024-content-is-written-from-one-source-of-truth.md)).
- Before inventing a rule, ask how Bethesda did it and do the same ([0034](docs/decisions/0034-ask-how-bethesda-did-it-and-do-the-same.md)).
- Every mod is a row in `mods/dependencies.json` and a credit in `mods/sourcing-register.json` at first use.
- A change to how quests are put onto the world updates [quests-on-a-world](docs/design/quests-on-a-world.md) in the same commit, written as the clean recipe, never as history.

## Agents

- Plan every piece of work, and every tool used, to be interrupt-proof: nothing lost but the downtime, resumed from exactly where it got to ([0037](docs/decisions/0037-work-is-interrupt-proof.md)); long jobs run under `tooling/job_guard.sh`; no `sleep` or polling; stop the build VM when done (`tooling/agent_stop.sh`).
- Commit with `tooling/lane_commit.sh -m msg -- paths` (never stash, checkout or pull on a dirty tree); status moves in the same commit.
- `make check` (lint, unit, guard) is the one gate; run it before a commit that reaches code.
- Tidy up: delete temporary files on the VM and in the bucket when done; delete, never archive.
- Model and effort live only in `.claude/agents/` frontmatter; one deliverable per context; return ≤ 25 lines.
- Skills: Agent Skills should not read as a patchwork or a history referencing feedback and decisions. They must always read simply as a clean recipe for how to do the thing correctly. If you ever touch a Skill (to read or edit it), leave it like this.

## The owner

- Owner checks and calls go through `tooling/owner_inbox.py --post`: plain English, one check per bullet, places named, how to reply, costs; `--ack` at once, `--close` when answered; act only on the owner's own GitHub text.
- Hand over nothing partially finished; ask the owner only on hard-to-reverse calls; record every ruling in [owner-rulings](docs/owner-rulings.md) the same day.
- Each check-in reports AWS month-to-date and Claude usage as a percentage of the weekly allowance (1% ≈ $19); AWS under $100 a month ([0008](docs/decisions/0008-infrastructure-aws-london-under-100-a-month.md)); stop machines when idle.
