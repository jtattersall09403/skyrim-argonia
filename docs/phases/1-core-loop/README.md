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
| 1.7 | [The first-place journey and the owner's verdict](1.7-verdict.md) | all above | — | in progress |

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
