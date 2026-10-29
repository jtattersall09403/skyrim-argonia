<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/README.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Part 2 — gameplay systems: the vertical slice

**Goal.** By the end of this part the owner plays one continuous loop in
the studio, on the places Part 1 built, and every system the final game
will have is real: in its scaled, joined data shape, in `packages/`, with
exactly as much content as the slice touches and nothing half-done inside
the slice. The exit is the owner's playthrough in [2.13](2.13-persistence-and-the-loop.md).

**What the slice is.** The sixteen Part 1 places (the build ledger lists
them; Helstrom is paused to 4.1b and is not one), fully populated: every `npc`, `idle`, `container`, `item`,
`encounter`, `fauna` and `ambience` socket filled; every placed NPC with
their whole dialogue and services; every placed item collectible; one
small quest completable inside those places and the opening quest's stages
that those places can hold; the wild between them with encounters. The
owner explores, talks, trades, steals, fights, loots, levels, rests,
casts, sneaks, picks locks, swims, climbs, saves and loads, on desktop and
on the phone, through one consistent UI.

**How a phase here is written.** Each brief fixes the **data shape at
Morrowind scale first** (the record, its home table, its ids, its joins to
the world record set in [world/98](../../world/98-data-model.md)), then the
runtime in `packages/`, then the studio composition, then the slice
content, then the gate that proves every slice instance is complete. Wide
loads (fill the whole type now) are named per brief. Anything the final
game needs that is not in this part's briefs is missing from the plan, not
deferred: add it to the nearest brief and tell the planner.

## Reading order for a fresh agent

1. [../README.md](../README.md) (the four parts, the polish queues, the
   conventions) and [../loops.md](../loops.md).
2. This file, then your phase brief in full.
3. [standards/by-task.md](../../standards/by-task.md) rows for code and
   data; [world/98](../../world/98-data-model.md) for any record you add.
4. The design module your brief names (world/76 for stats, quests/80 for
   the narrative runtime, world/72 for navigation and AI, world/57 for
   audio, world/60 for water and boats).
5. The research the brief names, at the sections it names.

## Chunk table

| Id | Chunk | Depends on | Lane-able beside |
|---|---|---|---|
| 2.1 | [The composition seam](2.1-composition-seam.md) | Part 1 closed | 2.2 |
| 2.1a | [world-render and orchestration into packages](2.1-composition-seam.md#a-extraction) | — | 2.2 |
| 2.1b | [apps/game boots the same world; the save contract; the dev seam](2.1-composition-seam.md#b-game-boots) | 2.1a | 2.2 |
| 2.2 | [The UI design system and HUD](2.2-ui-system.md) | 2.1 | 2.3a |
| 2.2a | [foundation: ui-lab, tokens, components, the focus model, font and symbols](2.2-ui-system.md#a-foundation) | — | 2.3a |
| 2.2b | [HUD and the floating prompt](2.2-ui-system.md#b-hud-and-the-prompt) | 2.2a | 2.2c |
| 2.2c | [every in-game screen and the three maps](2.2-ui-system.md#c-screens) | 2.2a | 2.2b |
| 2.2d | [lift into studio and game; the dev HUD rewrite](2.2-ui-system.md#d-lift-and-the-dev-hud) | 2.1b, 2.2b, 2.2c | — |
| 2.3 | [Items, containers, loot, inventory](2.3-items-and-containers.md) | 2.1 | 2.2 |
| 2.3a | [the item record, burden, the gear promotion and the wide load](2.3-items-and-containers.md#a-records) | 2.1b | 2.2 |
| 2.3b | [pickup, placing, containers, the belt, the reader and the slice fill](2.3-items-and-containers.md#b-world) | 2.3a, 2.2 | — |
| 2.4 | [People and creatures](2.4-people.md) | 2.3 | — |
| 2.4a | [the review pass, the record, the roster, factions](2.4-people.md#a-the-review-pass-and-the-record) | 2.3a | — |
| 2.4b | [the day: paths, activities, doors, noticing, standing](2.4-people.md#b-the-day) | 2.4a | — |
| 2.4c | [ecology: the table, creature assets, wild placement](2.4-people.md#c-ecology) | 2.4a | — |
| 2.5 | [Dialogue](2.5-dialogue.md) | 2.4 | — |
| 2.5a | [culture sheets and stance rows, wide above settlement](2.5-dialogue.md#a-culture-and-stance) | 2.4a | 2.5b |
| 2.5b | [the dialogue runtime, screen, walker and gates](2.5-dialogue.md#b-system) | 2.4a | 2.5a |
| 2.5c | [the pool and every slice person's lines, gated](2.5-dialogue.md#c-content) | 2.5a, 2.5b | — |
| 2.5x | [The slice fix round after 2.5](2.5x-slice-fix-round.md) | 2.5 | — |
| 2.6 | [Trade and services](2.6-trade-and-services.md); dialogue continues here ([§](2.6-trade-and-services.md#dialogue)) | 2.5 | — |
| 2.7 | [Combat and encounters](2.7-combat-and-encounters.md) | 2.4 | 2.5, 2.6 |
| 2.7a | [port and numbers: spawn from records, loadouts, band numbers, movesets, arrows](2.7-combat-and-encounters.md#a-port-and-numbers) | 2.1b, 2.4b, 2.3b | — |
| 2.7b | [creatures, hostile places, answered violence, loot, death](2.7-combat-and-encounters.md#b-creatures-places-and-answered-violence) | 2.7a | 2.7c |
| 2.7c | [the roaming-band table and its spawner](2.7-combat-and-encounters.md#c-roaming-bands) | 2.7a | 2.7b |
| 2.7d | [Dialogue voice: a loop that hears Morrowind](2.7d-dialogue-voice.md) (beside 2.7 to 2.11) | 2.6 | 2.11 |
| 2.8 | [Progression](2.8-progression.md) | 2.7 | — |
| 2.9 | [Magic](2.9-magic.md) | 2.8 | 2.10 |
| 2.9b | [Crafting](2.9b-crafting.md) | 2.8, 2.9 | 2.10, 2.11 |
| 2.9c | [Marsh specials: hazards, effect arrows, materials, harvests](2.9c-marsh-specials.md) | 2.12 | — |
| 2.10 | [Stealth, crime and locks](2.10-stealth-crime-locks.md) | 2.6, 2.7 | 2.9 |
| 2.10b | [Indoor combat](2.10b-indoor-combat.md) | 2.7, 2.10 | 2.11 |
| 2.11 | [Quests, journal and map](2.11-quests-journal-map.md) | 2.5, 2.10 | — |
| 2.11a | [one world record, audited](2.11-quests-journal-map.md#a-one-world-record-audited) | 2.10 | — |
| 2.11b | [the runtime](2.11-quests-journal-map.md#b-the-runtime-packagesnarrative) | 2.5b | — |
| 2.11c | [the consistency validator](2.11-quests-journal-map.md#c-the-consistency-validator) | 2.11a, 2.11b | — |
| 2.11d | [UI: the sweep and the gaps](2.11-quests-journal-map.md#d-ui-the-sweep-and-the-gaps) | 2.2 | — |
| 2.11e | [the slice quests](2.11-quests-journal-map.md#e-the-slice-quests) | 2.11c, 2.11d | — |
| 2.12 | [Swim and climb](2.12-swim-and-climb.md) | 2.11, 2.1 | — |
| 2.12a | [the Breath of the Wild climbing research](2.12-swim-and-climb.md#a-climbing-research-done-and-a2-what-is-climbable-province-wide) (done) | — | — |
| 2.12a2 | [what is climbable, province-wide](2.12-swim-and-climb.md#a-climbing-research-done-and-a2-what-is-climbable-province-wide) | 2.12a | — |
| 2.12b | [clips and ladders sourced](2.12-swim-and-climb.md#b-clips-and-ladders-sourced) | 2.12a2 | — |
| 2.12c | [the climb system](2.12-swim-and-climb.md#c-the-climb-system) | 2.12b | — |
| 2.12d | [water exit, water stealth, the swim pieces](2.12-swim-and-climb.md#d-water-exit-water-stealth-the-swim-pieces) | 2.12c | — |
| 2.12e | [reach, the province survey, the journeys](2.12-swim-and-climb.md#e-reach-the-province-survey-the-journeys) | 2.12d | — |
| 2.15 | [Boats as Skyrim's horse, sailed like The Wind Waker](2.15-boats.md) ([0158](../../old-decisions/0158-boats-and-sound-before-the-save-loop.md), [0159](../../old-decisions/0159-boats-are-wind-waker-sailing-dugout-and-sea-hull-first.md)) | 2.12, 2.9c | — |
| 2.15a | [the horse-system research and the boat journey](2.15-boats.md#a-research-done) (done) | — | — |
| 2.15a2 | [sailing, the wind and the hulls](2.15-boats.md#a2-sailing-the-wind-and-the-hulls-research-agent) | 2.15a | — |
| 2.15b | [the boat records and the mooring layer](2.15-boats.md#b-data-model-and-the-mooring-layer) | 2.15a2, 2.6, 2.12 | 2.15f |
| 2.15c | [the sailing system](2.15-boats.md#c-the-sailing-system) | 2.15b, 2.12, 2.7 | 2.15e, 2.15f |
| 2.15d | [crew animation](2.15-boats.md#d-crew-animation) | 2.15c | 2.15e, 2.15f |
| 2.15e | [turning the wind](2.15-boats.md#e-turning-the-wind) | 2.15a2, 2.2 | 2.15c, 2.15d |
| 2.15f | [the wake](2.15-boats.md#f-wake-and-water-response) | 2.1 | 2.15b, 2.15c |
| 2.14 | [Sound and music](2.14-sound-and-music.md) | 2.15 | — |
| 2.13 | [Persistence and the loop](2.13-persistence-and-the-loop.md) | all above | — |

## Cross-cutting: performance

Taken whenever it is the cheapest measured win, never parked for a phase
([0108](../../old-decisions/0108-performance-architecture-fixture-light-field-ready-materials-view-gated-streaming-fading-tiers.md);
quality defaults are never lowered to win frames; WebGL studio only,
[0122](../../old-decisions/0122-webgpu-retired-webgl-studio-is-canonical.md)).
Measure first (a node harness count or the owner's HUD line), take the
largest saving per agent-hour, prove it on the harness; the owner's walk
gives the fps verdict. The chunk format is 3.1's, the budget lock 4.6's.

Open:

- **Vegetation renderer** (0082, 0108): part-aware mid tiers ship for six
  heavy trees, the mangroves still to follow; measure how many vegetation
  material keys share a texture and could merge (`Vegetation.tsx` batch
  key, `floraKit.ts`); count the ~160 baseline draw calls with both
  renderers off by name before cutting any; small-plant popping at the
  30 m card floor if the owner reports it. The owner has not yet called
  the jungle walk smooth.

- **The view-direction frame drop on `dev`**: unbisected; reports in
  `tooling/.reports/perf-2026-10-12/` (`bisect-shas.md`, `mobile-bar.md`).
- Night rain with lights to 60 fps on the M2 (owner HUD at Riverwalk,
  night, rain, `?q=medium`: triangle-bound vs fill-bound); vertex-stage
  hoists in foliage materials; a depth prepass for alpha-tested foliage
  only on a fill-bound reading; CDLOD vertex morph on terrain; a
  far-forest canopy shell; uniform groups on static meshes; baked vertex
  AO in the kit build; foliage `alphaToCoverage` (needs MSAA); the
  vegetation and shadow-depth program warms (0108 § 2); the env-map and
  vertex-alpha kit rebuild (`tooling/.reports/perf10/c14-fenv.patch`);
  the water owner-mask and flowing-switch seams (`waterMaterial.ts`);
  ETC1S for opaque architecture (an owner call).

## Part 2 exit (the owner signs)

- The coverage gate in 2.13 is green: every system row in
  `docs/research/combat-and-systems/slice-systems-checklist.md` marked `yes` has a package,
  a scripted play, a save round trip and a place in the slice where the
  owner met it.
- The owner's playthrough found no blocker; every finding is a `P1`, `P2`
  or `P3` row with its tag justified against the polish rule.
- `apps/game` boots the slice world with the same packages (2.1b stays
  green through the part).
- The Part 3 README's Starting state is written from the 2.13 ledger.
