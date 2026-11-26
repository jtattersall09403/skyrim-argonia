# The plan: Elder Souls: Argonia

Read this whole at the start of every session, then [PROGRESS.md](PROGRESS.md) and the current phase's file in
[phases/](phases/README.md).

## 1. What we are building

A free Skyrim SE mod, playable by the owner over the stream and released in time as one mod with its
dependencies, made of:

1. **Vanilla Skyrim SE** at the pinned runtime (1.7.104, SKSE 2.3.1; [0002](decisions/0002-one-pinned-skyrim-runtime.md)).
2. **Our own world of Black Marsh** ("the new world" throughout the repo: `newworld/`, `tools/newworld/`): one
   worldspace of the whole province, generated from Project Tamriel's map of Black Marsh, with its 24 regions and
   258 places, its ground, water, plants, creatures, weather and distant view. A new game starts in it through a
   start quest of our own, and the vanilla systems that would still fire are shut down
   ([0012](decisions/0012-vanilla-skyrim-is-quarantined.md)).
3. **Places carried from source places.** Each of our places has one source place in a mod we depend on (Black
   Marsh & Valenwood, King of the Murkmire) or in Skyrim, carried whole onto our ground and adapted by hand
   ([0041](decisions/0041-a-place-is-its-source-carried-whole-and-adapted-by-hand.md)), then edited by the owner
   in the place studio. We make no art except music.
4. **Soulslike combat** from the Nexus collection
   [xyf1u3 "Soulsborne Combat"](https://www.nexusmods.com/games/skyrimspecialedition/collections/xyf1u3), plus
   **FreeClimb**, and magic on Skyrim's five schools (what magic we add is the owner's open call, #105).
5. **Our story**: the main quest and the faction lines ([story/](../story/README.md)), written for this world
   inside the Morrowind-level ceiling and built as data in the one quest form.

### A short history

- **2026-10-27 to 11-05:** a total conversion with its own generated world, systems, UI and test harness. It
  failed and was thrown away (see [0042](decisions/0042-the-new-world-is-the-project.md)).
- **2026-11-05 to 11-26:** our story modded onto the world of the Black Marsh & Valenwood mod. It proved the mod
  stack, the quest form and its blocks, the dialogue method and the skills. Its plans are in
  [archive/](archive/README.md).
- **2026-11-08 on:** the new world, begun beside the BM&V work and, since 2026-11-26, the whole project
  ([0042](decisions/0042-the-new-world-is-the-project.md)).

## 2. How we work

- **The binding rules are [CLAUDE.md](../CLAUDE.md)**, one line each. This file is the plan; PROGRESS.md is the
  status; each phase is one file in [phases/](phases/README.md), in the owner's words, added to as it goes;
  decisions hold the why; [research/](research/README.md) holds facts worth keeping; the owner's rulings are in
  [owner-rulings.md](owner-rulings.md) and, for story and writing, [owner-bar](../story/design/owner-bar.md).
- **Everything done more than once is a skill** that reads as a clean recipe: `world-build` and `world-lod` for
  the world, `place-system` and its sub-skills for places, `quest-system` and its sub-skills for story, quests
  and dialogue.
- **The owner works in three windows and the game.** The [Atlas](https://claude.ai/artifact/SwMRMPndRrXfEKtTuodNsb)
  shows the province and its places; the place studio (https://studio.jacktat-play.stream) is where he opens,
  edits and finalises each drafted place; the story explorer is where he reads the story and leaves notes. He
  walks the built world on the play machine. Agents do not test in game when he can: they prove work off game
  and post one owner check.
- **The world's ground is a fixed base.** It is never regenerated unless the owner asks; a change is a local
  patch, and `tools/newworld/rebuild.sh` runs only the stages a change made stale. A world rebuild runs only when
  he asks.
- **One world, told the same everywhere** ([consistency](design/consistency.md)): place records, lore, story,
  quests, people and drafted places agree at all times.
- **Costs:** AWS under $150 a month; Claude usage reported as a percentage of the weekly allowance; machines
  stopped when idle.

## 3. Machines and the play path

- **Build VM** `argonia-build` (London, on demand, Linux, about 8 to 10 hours a day): Claude Code, the Python
  tools, Spriggit, the world build, the place studio's server, the stack fetch and stage; drives the play machine
  over SSH (`infra/gpu-box/run.sh`).
- **Play machine** `argonia-play` (g4dn.xlarge on demand, Windows;
  [0039](decisions/0039-the-play-machine-is-a-g4dn-on-demand.md)): Skyrim, MO2, Sunshine and Moonlight-Web behind
  Cloudflare Access, the Creation Kit for the Papyrus compiler and FaceGen, xEdit and houseCARL as checkers, the
  LOD tools. It stops itself when idle.
- **The owner plays** at `play.<domain>`: the Worker starts the machine, Moonlight-Web streams it, a Sunshine
  card launches the game, saves sync to S3. Details: [infra/README.md](../infra/README.md).

## 4. The phases

Each phase is one file in [phases/](phases/README.md) and ends when the owner says so. Status is in
[PROGRESS.md](PROGRESS.md).

| Phase | What |
|---|---|
| [nw-01](phases/nw-01-map-extraction.md) | the map extracted and researched: places, regions, cultures, roads, danger |
| [nw-02](phases/nw-02-textures-plants-scatter-water.md) | the world textured, planted, watered, navmeshed and with LOD, walkable in game |
| [nw-03](phases/nw-03-build-helstrom.md) | Helstrom drafted from its source, and the place studio |
| [nw-03b](phases/nw-03b-ecology-creatures.md) | ecology: creatures, hostile people, harvestables |
| [nw-04](phases/nw-04-mine-similar-places.md) | a source place mined and matched for every place |
| [nw-05c](phases/nw-05c-factions-overhaul.md) | the main plot, the main quest's records and the faction plots |
| [nw-06](phases/nw-06-build-slice-places.md) | the slice places: the opening act's places and one of each type in the opening region |
| [nw-07](phases/nw-07-build-opening-act.md) | the opening act built |
| [nw-08](phases/nw-08-build-slice-2-places.md) | the second slice: places and opening quests for a selection of factions |
| [nw-09](phases/nw-09-build-quest-places.md) | the remaining major quest places |
| [nw-10](phases/nw-10-implement-major-quests.md) | the rest of the main and faction quests |
| [nw-11](phases/nw-11-build-everywhere-else.md) | everywhere else |
| [nw-12](phases/nw-12-implement-remaining-quests.md) | the remaining quests |

Beside the phases run two proposals awaiting the owner: magic ([research/magic/PROPOSAL.md](research/magic/PROPOSAL.md))
and new art ([research/new-art/PROPOSAL.md](research/new-art/PROPOSAL.md)).

## 5. Risks, named

- **Scale.** 258 places, each drafted by one agent and reviewed by the owner; the slice phases exist to make the
  recipe right before it is run widely.
- **Rebuild cost.** A world rebuild and its LOD are long jobs on a small budget; they run once, when asked,
  rehearsed on the small test world first.
- **New faces** need FaceGen from the Creation Kit; templates avoid it where a unique face is not worth it.
- **The stack on the pinned runtime**: a mod with no 1.7.104 build is swapped for an equivalent or dropped,
  recorded in `mods/README.md`.

## 6. What is deliberately not in this plan

Art of our own other than music; our own UI, HUD or stats system (our own SKSE plugin only where no mod, record
or script does the job); agent-driven in-game journeys; voice acting; an installer for other players (later, if
the owner wants one).
