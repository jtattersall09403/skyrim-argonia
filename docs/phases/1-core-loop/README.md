# Part 1: The first place

**Goal.** One real place, complete, played by the owner in the studio: Claywater Station with people who talk
in a Morrowind window, a quest followed from the journal alone, the sheet underneath everything, carrying and
reading, rest as the only save, death and the vastei pile, and combat on the tuned souls-like stack. It proves
the two things the game is for (the world and its places; the story and its people; decision
[0027](../../decisions/0027-build-in-the-order-of-the-usps.md)) on this host, with every foundation the content
is written against in its final shape, so Part 2 deepens and never replaces.

The place is **Claywater Station** and its 8×8-cell block (built natively in 0.4 §d), plus the
proving ground. The exit is the owner's verdict in 1.7.

**The thread.** Each system gets its **first rung at its final interface**: the real records, the real co-save
family, the real view and the real formulas (decision 0023 §2):

| Verb | First rung here | Made whole in |
|---|---|---|
| talk | three Claywater people with lines written afresh by the writing skills (0024): greeting, hyperlinked topics, disposition bands, Goodbye | 2.5 |
| carry, equip, read | one weapon class, one armour set in Morrowind slots, a container, a book; burden tiers | 2.3 |
| quest | one Claywater quest written through `quest-write`, generated into records, followed from the journal by directions, no markers | 2.12 |
| grow | skill use in anger → vastei → a pending level → rest → the sitting | 2.8 |
| die | wake at the last rest; the vastei pile; take it back | 2.8 |
| save | rest is the only save; the suspend save; a save/load round trip of every family | 2.17 |
| fight | the 0.0 stack wired to the sheet, the DS1 pad layout, lock-on, one archetype at fixed danger | 2.7 (the combat map) |

**What is left out on purpose.** Barter (2.6); the combat map and anything built from DS1 (2.7); our rules for
climbing, swimming and boats (the mods are in the stack from the start, owner 2026-10-29, so the player can climb,
swim and sail at the first place as the mods ship; 2.13 and 2.15 build the rules); every UI screen beyond the
dialogue window, the journal, our HUD, the chart and the theme (2.2); magic, crafting, stealth (Part 2). A gap found here that needs
a whole system is noted in that system's Part 2 brief, never built now.

**The world track runs beside this part.** 2.W1–2.W4 start as soon as 0.4 passes and load the build VM;
this part loads the GPU box. They share nothing but the pipeline (0.4 §a).

## The world track's in-game sample (owner, 2026-10-29: "sample smartly")

2.W1–2.W4 prove their data at L1 on every cell; in game they are checked by **one small sample chosen to hit the
likely pitfalls**, not by walks of the whole province. One journey, `world-sample`, run once per world-track
change set on one machine, a still per stop and a state read where a number decides:

| # | Stop | Catches |
|---|---|---|
| 1 | Claywater block, on the road in | heights vs heightfield (probe), grass on the paint, region trees, road surface |
| 2 | The steepest limited cliff (2.W1's worst cell) | the cliff ramp, seams, texture stretching |
| 3 | A cell corner where four cells meet on a slope | seams in height, normals and texture |
| 4 | One stepped river reach with rapids | step lines hidden, z-fighting, flow look |
| 5 | One waterfall | the falls piece seated on the step |
| 6 | One marsh basin | the designed marsh level, no floating or missing water |
| 7 | One lake shore and one coast | banks, the sea default at 0, the apron through the haze |
| 8 | The densest vegetation cell | frame time against the 0.2 §d bar, no Nordic flora (incl. the three vanilla rocks) |
| 9 | One border segment and one exit gate | the player cannot leave; the closed-road message |
| 10 | One signpost at a junction | sign text and arms |
| 11 | Weather: a 7-day skip at the Claywater block | the region's weather cycles; the light is green-gold |
| 12 | Navmesh: an NPC walks Claywater, 20 random path requests across the block and one swim | walkable ground, door and water links |
| 13 | A distant view from a high point | terrain and tree LOD, no missing tiles |

A failing stop is diagnosed, the whole class fixed once at L1, and the stop re-run; a new stop is added only after
a defect the sample missed (0011 §2). The briefs' longer owed lists (1,000 probe points, 30 step stills, 200 paths)
are met by the L1 checks plus this sample.

## Starting state (2026-10-31)

Part 0 is not closed: 0.2–0.4 are in progress (the g6 frame times, the timed loop row and the owner's Claywater walk
are owed) and Part 1 runs beside them. Every chunk here is built at L1–L3; in game, most journeys have passed at
least once and the reds are listed in each PROGRESS row. Game machines are named in `infra/gpu-box/machines.conf`:
argonia-play (the play machine, Paris) and argonia-play-london (agents' checks). Status: [PROGRESS](../../PROGRESS.md),
the Status column below and `checks.md`.

## Chunk table

| Id | Chunk | Depends on | Lane-able beside | Status |
|---|---|---|---|---|
| 1.1 | [The game-state seam](1.1-game-state-seam.md) | Part 0 | 1.2 §a | in progress |
| 1.2 | [The UI, stage one: Pelagiad, the paper theme, the dialogue window, the journal, our HUD and the chart](1.2-ui-foundation.md) | 1.1 schema | 1.3 §a | in progress |
| 1.3 | [Talk and carry, on the sheet](1.3-talk-and-carry.md) | 1.1, 1.2 dialogue window | 1.6 (wiring draft) | in progress |
| 1.4 | [One quest through the journal](1.4-one-quest.md) | 1.3, 1.2 journal, 0.1 §i | 1.5 | in progress |
| 1.5 | [Grow, die, rest, save](1.5-grow-die-rest-save.md) | 1.3 | 1.4 | in progress |
| 1.6 | [Fight on the tuned stack, wired to the sheet](1.6-fight-on-the-stack.md) | 1.3 sheet | 1.4, 1.5 | in progress |
| 1.8 | [A play machine you can rely on](1.8-a-play-machine-you-can-rely-on.md) | — | 1.9–1.16 | todo |
| 1.9 | [The front door and loads](1.9-the-front-door-and-loads.md) | — | 1.10 | todo |
| 1.10 | [The player character](1.10-the-player-character.md) | — | 1.9 | todo |
| 1.11 | [Our HUD, rebuilt from the old game's](1.11-our-hud.md) | 1.9 (loads) | 1.13 | todo |
| 1.12 | [Menus: the system menu, the pause menu, quit, favourites, touch](1.12-menus.md) | 1.11 (the theme's HUD pass) | 1.13 | todo |
| 1.13 | [The chart](1.13-the-chart.md) | — | 1.11, 1.12 | todo |
| 1.14 | [Death, the pile and respawn](1.14-death-and-the-pile.md) | — | 1.13 | todo |
| 1.15 | [The world track's close](1.15-the-world-tracks-close.md) | 1.8 (the play machine) | 1.16 | todo |
| 1.16 | [The owed integration checks](1.16-the-owed-integration-checks.md) | 1.9–1.14 | 1.15 | todo |
| 1.17 | [Frame rate and the screen numbers](1.17-frame-rate-and-the-screen-numbers.md) | 1.8, 1.15 | — | todo |
| 1.7 | [The first-place journey and the owner's verdict](1.7-verdict.md) | 1.1–1.6, 1.8–1.17 | — | in progress |

## Part 1 exit (the owner signs)

- The one batch of in-game checks (`tests/journeys/batches/all.yaml`, crash-prone last) is green, first-place among
  them, with the memory climb per loop measured (the soak is dropped, owner 2026-10-30).
- The owner played the thread in the studio and gave the verdict, with the measured stream latency written
  beside it:
  - **The place:** does Claywater Station feel like Black Marsh, up close and from the road?
  - **The talk:** does the window feel like Morrowind?
  - **The quest:** could you follow it from the journal alone?
  - **The game:** is this the game you want?
  - **Combat:** good enough to carry on with on the tuned stack? (Its map is 2.7.)
- A **yes** opens Part 2's systems track (the world track is already running). A **no** triggers a re-plan on
  Skyrim: a written comparison of the options, costed.
- The planner re-estimates Parts 2–4 from Part 1's measured cycle times.

## Round two: from the first play test to the verdict (2026-10-31)

The first round built every chunk 1.1–1.6 and the world track at L1–L3, and most of it in game. The owner's first
play test ([owner-playtest-1.md](../../research/2026-10-31/owner-playtest-1.md)) and the ledger audit
([ledger-audit.md](../../research/2026-10-31/ledger-audit.md): 56 proven, 38 owed, 9 dropped) left what 1.8–1.17
do. Each is **one session's work**, taken one at a time by the owner, in this order:
- first what stops play: 1.8 the machine, 1.9 loads, 1.10 the Nord head;
- then what the owner sees: 1.11 the HUD, 1.12 menus, 1.13 the chart, 1.14 death;
- then what proves the rest: 1.15 the world track, 1.16 the owed checks, 1.17 frame rate;
- then 1.7, the packet and the verdict.

Where two chunks touch the same view, the order above keeps one builder per view. 1.1–1.6 and 2.W1–2.W4 stay in progress until the Round-two chunk that closes their last owed row marks them done.

### How a chunk session runs
The owner starts a fresh session with **"deliver <id>"** (for example "deliver 1.8"). The session follows the
[deliver skill](../../../.claude/skills/deliver/SKILL.md):
1. read where things stand from the records;
2. post the owner's calls first;
3. run the loop on the chunk's `checks.md` rows until each is proven or ruled;
4. move the brief, PROGRESS, this table and the ledger in the same commits as the work.
A chunk that doesn't finish leaves its hand-off in the brief's Starting state.

### The owner's follow-up notes (tmp/owner-message.md, owner-message-2.md): where each is answered
| Note | Answered in |
|---|---|
| SkyLink AI's approach for our tools | 1.16 |
| 98 dependency mods, slim if not needed | done: the stack is 70 mods (stack.py) |
| Water "falls back to one level": designed levels only, drop stray puddles | 1.15 |
| The hand-drawn map: the old repo's? | 1.13 |
| Sample smartly; no long walks; no quest playthrough in game; headless playthrough only | the rules in CLAUDE.md and "How a chunk session runs" |
| The Morrowind attributes and skills mod (nexus 60199) as a foundation, in our theme | 1.16 |
| Permission requests | done (owner) |
| Parallelism: whatever works best | done (owner-brief) |
| World map finalised | 1.13 |
| Livia to bed at night | proven (livia-sleep, checks.md 1.3) |
| The crocodile in and working | proven (croc-den) |
| Judging Black Marsh feel | the owner, at 1.7 |
| Screen technology chosen for real | 1.17 |
| The DS combat trial | proven (combat-trial-a, checks.md 1.6) |
| The hour-long stability test: last, never a gate | [backlog](../backlog.md), P3 final |
| Things said to be not built get built | 1.8–1.17 |
| The faster machine: the owner tests at 45–53 fps before ruling | 1.17 |

