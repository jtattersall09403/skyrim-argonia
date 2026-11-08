# The plan: Elder Souls: Argonia, on Black Marsh & Valenwood

Written 2026-11-05 at the owner's pivot ([decision 0038](decisions/0038-the-pivot-bmv-is-the-world.md)). The
first week built a total conversion with its own generated world, systems, UI and test harness; that experiment
failed and was thrown away. This plan starts again. Read it whole at the start of every session, then
[PROGRESS.md](PROGRESS.md).

## 1. What we are building

A free Skyrim SE mod set, playable by the owner over the stream, made of:

1. **Vanilla Skyrim SE** at the pinned runtime (1.7.104, SKSE 2.3.1; [0002](decisions/0002-one-pinned-skyrim-runtime.md)).
2. **Black Marsh & Valenwood (BM&V)** as the **default world**: a new game starts in Black Marsh through an
   start quest of our own that skips Helgen and goes straight into our opening (Enderal-style), and the vanilla systems that would still fire are shut down (the main quest, dragon
   attacks, the civil war, the Thieves Guild and other couriers, Skyrim's radiant quests;
   [0012](decisions/0012-vanilla-skyrim-is-quarantined.md)).
3. **Soulslike combat** from the Nexus collection
   [xyf1u3 "Soulsborne Combat"](https://www.nexusmods.com/games/skyrimspecialedition/collections/xyf1u3), used
   out of the box, plus **FreeClimb** and **Magic Expanded** (Morrowind's spells and schools).
4. **Our story on top**: the storyline, quests and factions designed for Argonia
   ([story/](../story/README.md)), adapted to the world BM&V already built, with minimal tweaks: NPCs, items,
   bosses and creatures added, removed or changed. This is the main work and runs for as long as the project does.

Everything the player meets is a record in our own plugin over BM&V and the mods, plus Papyrus where a record
cannot do it. We make no art, no world, no engine code of our own.

## 2. How we work (the whole process)

- **As light as possible.** This file is the plan; [PROGRESS.md](PROGRESS.md) is the status (one line per phase
  and per block); decisions hold the why; [docs/research/](research/README.md) holds facts worth keeping. No chunk
  briefs, ledgers, rounds, journeys or gates beyond `make check` (lint, unit tests, the no-assets guard).
- **Agents do not test in game.** The owner tests. An agent proves its work off game (the plugin loads in xEdit
  or houseCARL without errors, the script compiles, the record diff is what was intended) and then posts one
  owner check: what to look at, where, how, in plain English (`tooling/owner_inbox.py --post`).
- **Prove a building block once, then reuse it everywhere.** Phase 3 proves each kind of change on one example
  (one NPC's dialogue, three ways to start a quest, the script types, a placement on existing navmesh, a faction,
  an item, a boss). Once the owner has verified a block in game, every later use of the same block is built the
  same way and not re-tested individually. Only a new kind of change earns a new block.
- **The build VM is on demand and runs only while an agent works, about 8 to 10 hours a day; the play machine
  is spot and stays spot** ([0008](decisions/0008-infrastructure-aws-london-under-100-a-month.md)). Stop the build
  VM when done (`tooling/agent_stop.sh`); every long job resumes from where it got to after an interruption
  ([0037](decisions/0037-work-is-interrupt-proof.md)) and runs under `tooling/job_guard.sh`.
- **Commit straight to main** with `tooling/lane_commit.sh -m msg -- paths`; status moves in the same commit.
- **Nothing the player does not own is committed** ([0003](decisions/0003-nothing-shipped-that-players-do-not-own.md)):
  mods are rows in `mods/dependencies.json` and are fetched, staged and pushed by `infra/gpu-box/stack.py`.
- **Owner rulings** that still bind are in [owner-rulings.md](owner-rulings.md); new ones are added there the
  day they are made, and hard-to-reverse calls go to the owner as an issue first.
- **Costs:** AWS under $100 a month ([0008](decisions/0008-infrastructure-aws-london-under-100-a-month.md));
  stop machines when idle; each check-in reports AWS month-to-date and Claude usage as a percentage of the weekly
  allowance (1% ≈ $19). Tidy the disk and the bucket; delete rather than archive.

## 3. Machines and the play path

- **Build VM** `argonia-build` (London, m7i-flex.xlarge on demand, Linux, run about 8 to 10 hours a day): runs
  Claude Code, the Python tools, Spriggit, the stack fetch and stage; drives the play machine over SSH
  (`infra/gpu-box/run.sh`).
- **Play machine** `argonia-play` (g6.xlarge persistent spot, Windows, in whichever European region interrupts
  least at a similar price; Paris so far): Skyrim, MO2 as the staging layout,
  Sunshine + Moonlight-Web behind Cloudflare Access, the Creation Kit for the Papyrus compiler, houseCARL and
  xEdit for load-order checks. It was terminated with its disk on 2026-11-05 and is recreated in Phase 0 from
  `infra/gpu-box/create.sh` + `setup.ps1` + `stack.py install`; no image or snapshot of it is kept.
- **The owner plays** at `play.<domain>`: the Worker starts the machine, Moonlight-Web streams it with our
  touch pad (`infra/stream-client`), a Sunshine card launches the modded game, saves sync to S3 every 5 minutes
  and on a spot notice, idle-stop after 15 minutes. Details: [infra/README.md](../infra/README.md).

## 4. The phases

Each phase ends when the owner has played it and said so on its issue. Phases run in order; the blocks inside
Phase 3 run in any order. Nothing is estimated in advance; each phase records what it measured. Each phase is one
file in [phases/](phases/), edited as the phase goes.

| Phase | What | Ends when the owner can say |
|---|---|---|
| [0](phases/0-play-machine.md) | the play machine is back and vanilla Skyrim streams | no owner test: the machine, Steam and the pinned game are checked by the agent; the owner tries the Vanilla card in the first walk (owner, 2026-11-05) |
| [1](phases/1-stack-in-bmv.md) | the stack, in BM&V as the default world | "I started in Black Marsh, fought, climbed, cast a Morrowind spell and nothing from Skyrim followed me" |
| [2](phases/2-first-act-on-paper.md) | the first act written as quest records, and the small composable block set it needs, derived from them | "the act reads right and the block list is enough" (read, not played) |
| [3](phases/3-building-blocks.md) | each block proved once, plus one composite quest for the connectors (the induction) | "I saw every block and the composite work in game" |
| [4](phases/4-first-act-built.md) | the first act built from the proven blocks, with its dialogue | "I played the first act from a new game" |
| [4a](phases/4a-talk-to-everyone.md) | every BM&V person outside Lilmoth gets a backstory and topics of their own (W-talk, proved on Lilmoth's 12), settlement by settlement; runs beside Phase 4 | "I can talk to anyone I meet, and what they tell me is true" |
| 4b (after Phase 4 is accepted) | the method as skills: cut from [quests-on-a-world](design/quests-on-a-world.md), talk-write and the block set, a skill (or set) for putting a quest system onto a new world, world edits included; first the builders' four quest kits and read-backs become one | "an agent with only the skills could do it again on another world" |
| [5 and on](phases/5-scale.md) | scale | "the story is in, milestone by milestone" |

## 5. Risks, named

- The collection's AE-era DLLs may have no 1.7.104 build; the fix is a newer equivalent mod or dropping that one
  behaviour, decided in Phase 1 and recorded in `mods/README.md`.
- BM&V may fight USSEP (missing masters, overridden cells); houseCARL's report and a record-conflict census decide the load order.
- New NPCs with new faces need FaceGen from the Creation Kit; B2 avoids it with templates, and the CK route is
  used only if a unique face is worth it.
- Spot capacity for a g6.xlarge can be scarce; the play page waits and retries, the region is chosen by
  interruption rate, and the owner has ruled the play machine stays spot.

## 6. What is deliberately not in this plan

Our own worldspace, terrain, water, vegetation or LOD; our own UI, HUD or stats system (our own SKSE plugins are allowed where no mod does the job: owner, #51); DS1
measurement; a relational world database; agent-driven in-game journeys and the bridge; voice acting; an
installer for other players (later, if the owner wants one).
