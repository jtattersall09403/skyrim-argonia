# The schedule: five parts, de-risk first

This folder is the **schedule**:
- one master file (this one);
- one folder per part, each with a README holding its chunk table;
- one brief per chunk.

Status lives only in [../PROGRESS.md](../PROGRESS.md). The why of any rule lives in
[../decisions/](../decisions/README.md). Design lives in `docs/design/` (imported from the old project) and in
the briefs that build it. Decision [0023](../decisions/0023-five-parts-de-risk-first.md) made this plan and
records why it differs from both the old four parts and this repo's first P0–P10 plan.

## The principle

We **de-risk** before we scale. Each class of work is proved on a real, fully realised sample until the owner
is confident the rest is leg-work; then the leg-work is done sideways. The parts run in the order of remaining
uncertainty:

| Part | De-risks | Ends when the owner can say |
|---|---|---|
| [0 Foundation](0-foundation/README.md) | that agents can build, test and stream Skyrim from AWS; the go/no-go spikes | "I dropped into the studio on my phone and teleported around" |
| [1 The core loop](1-core-loop/README.md) | that every system can join on this host, and that DS1 combat feels right through the stream | "this is the game I want; it is worth building" |
| [2 The slice](2-slice/README.md) | that the province can be generated and every system exists whole on the slice places | "I played the slice in the studio; every system is real; the world is leg-work" |
| [3 The game shell](3-shell/README.md) | that a player installs, starts a new game and lands in the slice | "I started a new game and reached the open world; a stranger installed it" |
| [4 Build out sideways](4-buildout/README.md) | nothing new: packets scale what is proven | "the whole province is populated, every quest completes, and it is released" |

**Part 1's exit is the last cheap moment to change host** (decision 0001's fallback is OpenMW). Its owner
verdict is about four things:
- combat feel through the stream;
- the dialogue window;
- whether the UI holds together;
- "is this the game".

Thin content is expected and is not part of the verdict.

All testing happens in **the studio** (decision [0022](../decisions/0022-the-studio-boots-into-any-place.md)).
It is the real game with a dev panel that boots straight into any place and only observes or teleports. Part 3
builds the real front door once the slice works.

## Rules that keep the slice honest (no refactor later)

1. **Final-shaped from the first line.** Every system lives in what ships: `Argonia.esm`, our SKSE DLLs and our
   PrismaUI views. No mode, flag or switch stands in for a game action (0022 §4). Part 1's thin thread is each
   system's first rung at its final interface. Part 2 deepens it and never replaces it.
2. **Scaled data shapes, thin content.** Every record type is designed for Morrowind-scale counts: one home
   table, stable ids, references by id, an integrity gate. It joins the imported world record set
   (`docs/design/world/98-data-model.md`) and is filled with only what the slice touches. A design that works
   for ten NPCs and not a thousand is a defect.
3. **What the player meets is complete.** A placed NPC has their whole dialogue and services. Every placed item
   is usable. Every socket in a slice place is filled. Thin means *few places*, never *half-done places*.

**Wide loads.** Where filling a whole type costs little more than the slice's share, fill it now. That covers:
- the whole worldspace's terrain, water, roads and navmesh;
- every weapon and armour;
- every race, class and birthsign;
- every faction's rules and every spell effect.

Where content needs judgement per instance (dialogue, quests, place population), fill only the slice. Each brief
names its wide loads.

## Polish: three queues and a rule

**A blocker** is a defect where the player cannot do the action (stuck, falls through, crash, lost save,
unreachable control), or sees it at the play camera in normal play (floating, a limb through a wall, a visible
pop, a Nordic element). A blocker is fixed by the chunk that finds it, before its owner check.

**Everything else is polish:** one quick fix, then a row in [backlog.md](backlog.md) with one of three tags:

| Tag | Done when | Why that moment |
|---|---|---|
| `P1 before-scale` | chunk 4.1, before any packet | every place, packet or screen built after it replicates it (a kit mapping, a UI token, a data-shape wart, a world-builder defect, a performance architecture gap) |
| `P2 rolling` | inside the Part 4 packet that touches it | it scales with content (regional palettes, dialogue voice, place dressing, encounter tuning) |
| `P3 final` | chunk 4.6; `optional` rows may never be done | it is cosmetic and global, and the game ships without it |

Agents file rows where the table says. The planner may move a row up, never down without the owner.

## Loops

See [../loops.md](../loops.md) and decision [0021](../decisions/0021-fast-focused-loops-and-the-ladder.md):
- the ladder L1–L6;
- one lane testing a feature and its joins;
- eyeless journeys on two runners;
- measure, diagnose, fix once, re-measure.

Each brief's **Loops** section names its subsets and their levels, the joins it owns, its journeys, and any L5
reason.

## The parts in one view

**Part 0, [Foundation](0-foundation/README.md).**
- 0.1 the repo, the ways of working, the build VM and the import;
- 0.2 the go/no-go spikes G1–G10 and the GPU box;
- 0.3 the pinned stack, permissions and the installer;
- 0.4 the bridge, the studio and the two runners;
- 0.5 the record pipeline, the vanilla quarantine and the immersion inventory.

**Part 1, [The core loop](1-core-loop/README.md)**, on Claywater Station and the proving ground:
- 1.1 the game-state seam;
- 1.2 the UI foundation;
- 1.3 talk, trade and carry;
- 1.4 fight;
- 1.5 grow, die, rest, save;
- 1.6 a quest;
- 1.7 move: climb, swim, sail;
- 1.8 the owner's verdict.

**Part 2, [The slice](2-slice/README.md)**, in two tracks side by side.
- **World track:**
  - 2.W1 terrain and apron;
  - 2.W2 water;
  - 2.W3 regions, weather, light, roads and the route graph;
  - 2.W4 vegetation, navmesh and LOD with the map image;
  - 2.W5 the slice places, in two waves;
  - 2.W6 performance and the world walk.
- **Systems track:**
  - 2.1 the sheet;
  - 2.2 the UI whole;
  - 2.3 items;
  - 2.4 people;
  - 2.5 dialogue;
  - 2.6 trade and services;
  - 2.7 combat;
  - 2.8 progression, rest and death;
  - 2.9 magic;
  - 2.10 crafting;
  - 2.11 stealth and crime;
  - 2.12 quests, journal and map;
  - 2.13 swim and climb;
  - 2.14 marsh specials;
  - 2.15 boats;
  - 2.16 sound and music;
  - 2.17 persistence and the playthrough.

**Part 3, [The game shell](3-shell/README.md).**
- 3.1 boot, main menu, loading, settings and controls;
- 3.2 character creation;
- 3.3 the opening;
- 3.4 install, release and the owner's permanent setup;
- 3.5 first playable.

**Part 4, [Build out sideways](4-buildout/README.md).**
- 4.1 before scale;
- 4.2 region packets;
- 4.3 narrative lines;
- 4.4 assembled interiors;
- 4.5 systems depth;
- 4.6 final look, polish and release.

## Conventions (binding on every part folder)

- **The chunk table.** A part README holds it: one row per chunk, the first cell its id and the second the
  linked brief, which `tooling/brief_template.py --chunk <id>` reads.
- **What a brief carries:**
  - its goal and a **Starting state** (what exists, what is red, what to keep);
  - **Re-check before starting** (versions and prices that may have moved) and **Read first**;
  - its deliverables with acceptance (runnable or a number) and its wide loads;
  - **Loops**;
  - the **owner check** (plain English, scenes named, how to reply);
  - risks and fallbacks, and what is deliberately out of scope, where the chunk has any (a missing section means
    none known).
- **Just in time, nothing dropped** (0023 §7). Design content (formulas, counts, rules, rulings) is written now,
  in the brief that will build it. The agent that closes a chunk does three things in one commit:
  - replaces the chunk's Starting state with one **Outcome** paragraph (what shipped, where it lives, what is
    owed and to whom);
  - rewrites the next chunk's Starting state and steps from what it learned;
  - files any owner ruling in the brief it settles, written as the current rule.
- **Who does what.** One chunk per session. The planner plans and judges; `deliver` and `world-builder` build
  (ways-of-working).
- **The owner is hands-on** for every city and for the opening's places; no skill runs unattended on them.
- **Closing a part.** A part closes with:
  - a routing audit of its folder (the `routing-audit` skill);
  - its PROGRESS rows `done` with evidence;
  - the next part's Starting state written;
  - an owner check-in with costs;
  - a re-estimate of the remaining parts from measured cycle times.

## What depends on what

| This | before | because |
|---|---|---|
| 0.2 G10 (where the rules run) | 1.1 | it decides how ArgoniaCore hosts the rules |
| 0.4 studio and runners | every L4 check and owner check after Part 0 | nothing is tested through the new-game flow |
| 0.5 pipeline | Part 1 and everything after | records are generated, never hand-made |
| 1.8 the owner's verdict | Part 2 | the host is confirmed before the world and systems are built at scale |
| 2.W5 wave 1 of the slice places | 2.4 people onwards | people, loot and quests live in those places |
| 2.1 the sheet | 2.4 people, 2.7 combat, 3.2 character creation | every actor and formula reads it |
| 2.3 items | 2.6 trade, 2.7 loot, 2.11 theft | they move items |
| 2.4 people | 2.5 onwards | each one talks to, trades with, fights, robs or questions an NPC |
| 2.7 combat | 2.8 death and respawn, 2.9 cast interrupts, 2.11 sneak blows | they read combat state |
| 2.17 save round trip | Part 3 | the continue flow loads what the slice saves |
| 3.4 installer | 3.5 the stranger's install | a first playable that only the owner's box can run is not de-risked |
| 4.1 world-builder proved, packet template written | 4.2 packets | a packet runs the proven skill unattended on minor types |
| 4.2 packets holding a quest's places | 4.3 that quest's line | a quest needs its places built |

Chunks run as side lanes when their files are disjoint, which is the point of Part 2's two tracks. Only one lane
drives the GPU box at a time (`job_guard.sh --gpu`).
