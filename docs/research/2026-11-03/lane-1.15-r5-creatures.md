# Lane 1.15-r5-creatures: never fewer creature kinds per region than Skyrim or the Black Marsh mod

Owner #37 (2026-11-03 08:55): "We must have at least as many kinds per equivalent-sized region as those."
Brief: `docs/research/2026-11-03/briefs/1.15-r5-creatures.md`. Measure: `creature-kinds-per-region.md`.

## What was wrong

- The region classes' lists came from `roster.R` habitats written by ground type alone
  (`tools/argonia_world/creatures/roster.py:65`), so the drier classes and the coast drew few kinds: coastal-lagoon
  12, northern-transition 13, western-frontier 15, and D2/D3 land lists of 4 (coast) to 11 kinds.
- Nothing measured the bar, so nothing failed. `checks.MIN_KINDS = 12` was a typed floor, not Skyrim's number.
- `creature_region` (103 rows, seven legacy region names) sat beside `creature_region_class`; no tool read it.
- Settlements held no kept animals: the mod and Skyrim place 5 domestic kinds per settled region.

## The measure, as code (0034)

- `python3 -m tools.argonia_world.vanilla.creatures --bars` (`vanilla/creatures.py` `skyrim_kinds`, `mod_kinds`,
  `kind_bars`) reads Skyrim.esm (+ Update.esm cells) and Black Marsh.esm and writes counts only to
  `data/creature-kind-bars.json`. It reproduces the research note: Skyrim Coast 14, Fall Forest 17, Mountains 18,
  Reach 18, Pine Forest 20, Snow 20, Tundra 22, Volcanic Tundra 16, Tundra Marsh 10. Black Marsh.esm's main
  worldspace has 26 kinds. Its second worldspace has 20; the note had 19, and the difference is one vanilla fox ref.
  The mod side also records the most kinds any n×n window holds (9 cells 12, 25: 14, 169: 23, 289: 25, 441+: 26).
- The bar (`creatures/checks.py` `bar_for`, `kind_bars`). Each class is measured by its largest land region. The
  Skyrim bar is the biome region nearest it in cells, and never below Skyrim's least-varied region of 600 or more
  cells (Coast 14). The mod bar is the main worldspace's densest window of that area, or the whole worldspace (26)
  past 1,127 cells. Every D2 and D3 land list must also hold at least 12 kinds.
- The check runs in the world gate: named check `creature-kinds-bar` (`tools/argonia_world/checks.py`) in
  `db check`. It is numpy-free, because the planner imports in `creatures/checks.py` now load inside their functions.

## Before / after (kinds a walker meets: lists plus apex dens; dry = D2/D3 land list)

| Class | cells | Skyrim bar | mod bar | before | after | dry before → after |
|---|---|---|---|---|---|---|
| coastal-lagoon | 2,783 | 18 (Mountains) | 26 | 12 | 26 | 4 → 12 |
| northern-transition | 2,354 | 18 (Mountains) | 26 | 13 | 26 | 11 → 14 |
| western-frontier | 2,179 | 18 (Mountains) | 26 | 15 | 26 | 11 → 14 |
| flooded-forest | 1,435 | 20 (Snow) | 26 | 25 | 29 | 9 → 13 |
| interior-swamp | 535 | 17 (Fall Forest) | 26 | 23 | 28 | 7 → 12 |
| rootland | 350 | 16 (Volcanic Tundra) | 25 | 22 | 25 | 11 → 13 |
| deep-sink-basin | 145 | 14 (floor) | 23 | 22 | 27 | 7 → 12 |
| tidal-delta | 17 | 14 (floor) | 14 | 16 | 24 | 5 → 12 |
| deep-river-corridor | 40 | 14 (floor) | 14 | 15 | 23 | 5 → 12 |

The bars measured at HEAD before the change: 28 reds. After: none. The lagoon bar is 18, not the brief's 14 from
WeatherCoast: its largest land region is nearer the inland regions in size, so the stricter number holds.

## What changed

- `roster.WIDEN` adds 71 (creature, class) rows. Each carries its lore citation in `creature_region_class.why`
  (0032): fact ids from `topics/loading-facts.md` or the `fauna-hazards.md` sections.
- New wild kinds, all from mods already in the stack (sourcing register rows updated):
  - red hooped tree-viper (`fact.tree-viper-lookalike`): Cipactli `mihailsnakeVIPER`, mesh `mihailviper.nif`.
  - pad-sa shark (`fact.pad-sa-sharks`): Here There Be Monsters `HTBMSharkEnc` and `HTBMSharkLargeEnc`, mesh
    `shark2.nif`, in lagoon, delta and river water.
  - Black Marsh.esm's own `shark` and `1LurkerShark` were not used: they carry the vanilla slaughterfish race and
    the mod ships no shark mesh. No leopard, panther, rhino, selkie, dragling, megalania or red wolf.
- Kept animals (`seed.domestic`, `roster.KEPT`): 202 npc rows of kind creature, each with an `npc_statblock` in its
  creature's band and `respawn never` (0035).
  - Two guar at each of the 91 lived-in settlements, Claywater Station included (`fact.glowgill-guar-archon`,
    `fact.guar-glow-tattoos`). The forms are King of the Murkmire's `ALPAGwar01`, `ALPAGwar02Pack` and `ALPAGwar03`.
  - Two bantam guar at each of the 10 Murkmire settlements (naga-kur-deeps, imperial-penal-south;
    `fact.voriplasm-bantam-guar`), form Cipactli `CIPHTBMBantamGuar`.
  - New creature row `creature.bantam-guar`.
- `creature_region` was retired: the table was dropped from `world/schema.sql`, its jsonl deleted and
  `98-data-model.md` updated. `creature_region_class` is the one table.
- Density (6) is unchanged by design (`roster.BANDS`). `creatures check` on SAMPLE_1_15: 8 green, 0 red. Per 100
  cells: forest 125.8 (vanilla 95.87), shore 117.6 (105.16), water 15.3 (8.72), mountain 97.5, open 88.9.
- Tests in `creatures/tests/test_lists.py`: the bar holds, the bar follows area, and kept animals stand at every
  lived-in settlement.

## Owed

- In game (L4): `tests/journeys/creatures-kinds.yaml` checks three region classes by teleport, an actor read
  within two cells and a still. Row in `docs/phases/1-core-loop/checks.md`, owed.
- The build: the lists reach ArgoniaWorld.esm at the next province world build on the build VM. No creature list
  lives in the committed `plugin/` YAML; `records.document` builds 135 lists, 205 fixed actors and 10 zones.
  - The kept animals need build_person and sockets from the place build before they stand in game. They have none
    yet, so until then they are rows only.
- Domestic kinds: two placed against Skyrim's five. Lizard-steed and mouth-plover have creature rows but no form
  in any pinned mod, so the rest needs an owner call.
- Domestic kinds beyond the guar (lizard-steed, mouth-plover): no form in any pinned mod; the coordinator takes it
  to the owner.
- Kept guar in the 85 lived-in settlements that have no layout or build yet: their npc rows stand ready; each gets
  its pen socket and actor when its place is laid out and built (the same `seed.domestic` path).

## Round 5b: the owed parts finished

- **Time of day in the records, the Skyrim way** (`records.day_packages`, `CreatureRecords.cs`, `PackageRecords.cs`).
  - Every wild form is now copied per band: 77 forms, 385 copies. Each copy carries its kind's packages in PKID,
    abroad first, with the template's AI-packages flag (0x20) cleared.
  - The packages template on vanilla's EncCreatureSandboxEditorLocation512 (10F7A5): the Sandbox template 01C254,
    near the editor location. Abroad hours use a 512-unit sandbox. Rest hours use 256 units, as
    EncSlaughterfishSboxEditorLocation256 (0DA751). The hours come from a PSDT schedule, as
    DefaultSleepEditorLoc24x8 (01B210) does.
  - The windows: diurnal 06-20, nocturnal 20-06, crepuscular 04-08 and 17-21. Kinds with `any` keep 10F7A5 itself.
  - Eight PACK records at 0D3F00 onwards.
  - Writer test on the bytes, `creatures/tests/test_day_packages.py`, passes. It runs ArgoniaGen `world` and reads
    back each PACK's PSDT hour and minutes and its Sandbox template (PKCU), and each actor's PKID order and ACBS
    template flags.
- **Kept guar placed.** The place build's own animal socket (kind fauna, zone pen, as upriver-hist-village's
  `fauna-pond-guar`) is written for every lived-in settlement with a layout (6 sockets, 12 rows homed to them).
  - Where the place is built, at Claywater, each guar is a persistent actor REFR (`ref.claywater-station.kept-guar-1`
    and `-2`) with an owned pen marker. `place_build._people` writes its NPC_ on King of the Murkmire's
    `ALPAGwar01`, with the creature den sandbox around the pen all day.
  - The pen stands 22.8 m east of the centre, out of the crocodile's scour pool (35 m off).
  - Bantam guar moved to band D1.
  - `test_creature_dens` picks the crocodile's NPC_ by its EditorID now that the guar are NPC_ too.
- **Lore citations (0032).** Every `creature_region_class.why` now cites the lore dossiers (`roster.LORE`):
  loading-facts fact ids, fauna-hazards sections, and ecology-encounters-loot's region table. None cites
  `74-ecology.md` any more (0 of 234 rows).

## Grounding per row (owner #37, 09:23; coordinator's widening of Acceptance 4)

- `creature_region_class` gains four columns, through `world/schema.sql` and `db.py`: `ecology` (habitat, water,
  diet against the class), `bands` (the fixed bands), `climate` (the class's top four weathers by summed chance
  from `land_region_weather`) and `day_rule` (diurnal, nocturnal, crepuscular or any, from `creature.day_active`).
  `seed.ground` fills all 234 rows.
- Named check `creature-grounding` fails any row without lore (why), ecology, bands, climate or day rule.
- Every row's `why` cites the dossiers (round 5b).
