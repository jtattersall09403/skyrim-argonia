# The plan: Elder Souls: Argonia, on Black Marsh & Valenwood

Written 2026-11-05 at the owner's pivot ([decision 0038](decisions/0038-the-pivot-bmv-is-the-world.md)). The
first week built a total conversion with its own generated world, systems, UI and test harness; that experiment
failed and was thrown away. This plan starts again. Read it whole at the start of every session, then
[PROGRESS.md](PROGRESS.md).

## 1. What we are building

A free Skyrim SE mod set, playable by the owner over the stream, made of:

1. **Vanilla Skyrim SE** at the pinned runtime (1.7.104, SKSE 2.3.1; [0002](decisions/0002-one-pinned-skyrim-runtime.md)).
2. **Black Marsh & Valenwood (BM&V)** as the **default world**: a new game starts in Black Marsh through an
   Alternate Start-style mod, and the vanilla systems that would still fire are shut down (the main quest, dragon
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
- **Prove a building block once, then reuse it everywhere.** Phase 2 proves each kind of change on one example
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
Phase 2 run in any order. Nothing is estimated in advance; each phase records what it measured.

### Phase 0: the play machine is back and vanilla Skyrim streams

- Pick the region: the spot placement score and interruption band for a g6.xlarge in London and Paris (and any
  other European region at a similar price); the least-interrupted wins. Recreate `argonia-play` there
  (create.sh, setup.ps1: driver, Steam, MO2, Sunshine, Moonlight-Web, the tunnel; machines.conf and the Worker
  updated to the region). The owner logs Steam in once; Skyrim is pinned to build 24914197.
- The play page starts it, the vanilla card runs, saves sync, idle-stop stops it.
- **Owner test:** play vanilla for ten minutes from the phone and the Mac.

### Phase 1: the stack, in BM&V as the default world

The owner's first walk is the whole stack *inside* Black Marsh, so the stack and the default world are one phase.

- **The stack.** `mods/dependencies.json` holds the new list: core (SKSE, Address Library, USSEP, Pandora, OAR,
  the DLL fixes), the collection's 31 mods as rows, FreeClimb, Magic Expanded, BM&V (the ModDB archive from the
  private bucket), Alternate Start - Live Another Life, houseCARL. `stack.py fetch --record` fills the hashes;
  `stage` applies the FOMOD choices; `push` and `stack.ps1 on` lay the hard links; Pandora runs on the machine.
- **Rebase the collection onto 1.7.104.** The collection was pinned for AE 1.6: DAR is replaced by Open
  Animation Replacer, Nemesis by Pandora, and the AE-era DLLs (Stop On Slash, Elden Counter, Animated Armoury's
  DLL if any) are checked for a 1.7.x build or dropped with a note. houseCARL reports conflicts and missing
  masters; the game reaches the main menu with every DLL loaded (SKSE's log).
- **The start.** Our plugin adds a Live Another Life start option that places the player in Black Marsh
  (LAL's addon pattern: a start quest, a marker in a BM&V cell, a line in the statue's dialogue), the opening
  taken from the story's prisoner work-detail premise in its lightest form. If LAL's addon route fails, the
  seed in `papyrus/ARG_StartQuestScript.psc` (a start-game-enabled quest that moves the player) is the fallback.
- **The shutdown.** Our plugin stops what still fires with LAL: the main quest chain from MQ102 on (no dragon
  ever rises), the civil war, the Thieves Guild, Dark Brotherhood and inheritance couriers, World Interaction and
  radiant quests, bounty letters. Method in route order: Start Game Enabled off in an override, story-manager node
  conditions, a startup script that stops the rest. The allow-list of quests that may run (the mods' own
  controller and MCM quests, LAL's, BM&V's) is written in this phase as `mods/allowed-quests.json`; a console
  `sqs`-style listing after 30 in-game days is the proof the owner can take, and the agent proves the override
  diff in xEdit first.
- **The map.** Skyrim's world map shows BM&V's worldspace when the player is in it (BM&V's own map if it ships
  one; otherwise the vanilla map of that worldspace). Doors and boats to Skyrim are left as BM&V made them.
- BM&V's known gap: 203 of its texture-set records name diffuse textures no archive holds
  ([research/bmv](research/bmv/)); it is left as BM&V ships it unless the owner finds it ugly.
- **Owner test (the first walk):** new game, choose the Black Marsh start, arrive in BM&V; a fight with the
  collection's moveset, a climb, a Morrowind spell from Magic Expanded, a walk between two BM&V places; then wait
  30 days: no dragon, no courier, no civil-war or guild starts; the journal holds only what the allow-list says.

### Phase 2: the building blocks (the proving kit)

Each block is one small, real example built in our plugin on top of BM&V, proven off game by the agent, then
verified in game by the owner. A block's record and script shapes become the template every later use copies.
The first block also settles **the authoring route**: records are written as Spriggit YAML in `plugin/` and
built to the ESP on the build VM (`spriggit` is installed at `~/.argonia/spriggit`); xEdit on the play machine is
the checker; the Creation Kit is used only where nothing else can (FaceGen for a new face; the Papyrus
compiler). If Spriggit proves awkward for a record type, a Mutagen script replaces it for that type.

| Block | The example | What it proves for later |
|---|---|---|
| B1 Dialogue | a new greeting and one new topic on an existing BM&V NPC, conditioned on a global | changing anyone's lines, Fuz Ro D-oh silent voice, conditions |
| B2 NPC | a new NPC (template from a BM&V or vanilla actor, so no FaceGen) placed on existing navmesh with sandbox and sleep packages and a bed | placing people anywhere, schedules, ownership |
| B3 Creature and boss | one creature at a fixed level in a marsh spot; one named boss with a unique inventory | encounters, bosses, [0035](decisions/0035-nothing-is-levelled-against-the-player.md) |
| B4 Quest starts | one quest started three ways: a dialogue topic, entering a trigger volume, reading a note | every quest trigger we will need |
| B5 Scripting | a stage fragment, an alias script (OnDeath), a trigger script, a global-driven condition; compiled on the machine | the script shapes, the compile job, where logic lives |
| B6 Items | one weapon with our stats, placed in a container and given as a reward | items and loot without levelled lists |
| B7 Faction | a faction with two ranks, an NPC in it, a line that changes with rank | faction lines |
| B8 Remove or change | a BM&V NPC disabled; a BM&V reference moved; a BM&V quest's stage changed | editing what BM&V built |
| B9 Journal | a quest with directions written in the journal, no marker | directions, not markers |

**Owner test:** one session through the nine examples, from an issue that says where each one is and what to
do. A block the owner finds broken is fixed and re-posted; a block that passes is never re-tested.

### Phase 3: the story's first act on BM&V

- **The census.** A dump of BM&V's locations, cells, NPCs, factions and quests (Spriggit or xEdit) into
  `story/bmv/`, and a map from our designed regions and places ([story/design/quests/index](../story/design/quests/index/))
  onto BM&V's towns and cells. Where BM&V has no place for a designed one, the quest moves to the nearest BM&V
  place or waits.
- **The opening** (prisoner work detail, the attack, the Veiled Reed) and the main quest's first three or four
  quests, written with the `quest-write`, `quest-review` and `dialogue-write` skills from the story records, built
  with the blocks.
- **One faction line's first two quests** (the owner picks the faction).
- **Owner test:** play the act from the Black Marsh start.

### Phase 4 and on: scale

The same blocks and skills, in the owner's order: the main quest's acts II and III and the three endings; the
four deep faction lines, then the standard ones and the detectives' faction
([0025](decisions/0025-a-detectives-faction.md)); regional and standalone quests; bosses and creatures by danger
band; items. Each milestone is one owner test. New block types (a boat, a dungeon layout, a new kind of script)
are proved as blocks first.

## 5. Risks, named

- The collection's AE-era DLLs may have no 1.7.104 build; the fix is a newer equivalent mod or dropping that one
  behaviour, decided in Phase 1 and recorded in `mods/README.md`.
- BM&V may fight LAL or USSEP (missing masters, overridden cells); houseCARL's report decides the load order.
- New NPCs with new faces need FaceGen from the Creation Kit; B2 avoids it with templates, and the CK route is
  used only if a unique face is worth it.
- Spot capacity for a g6.xlarge can be scarce; the play page waits and retries, the region is chosen by
  interruption rate, and the owner has ruled the play machine stays spot.

## 6. What is deliberately not in this plan

Our own worldspace, terrain, water, vegetation or LOD; our own SKSE plugins, UI, HUD or stats system; DS1
measurement; a relational world database; agent-driven in-game journeys and the bridge; voice acting; an
installer for other players (later, if the owner wants one).
