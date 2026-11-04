# Lane 1.15-r6-creatures

Status: done (L1, L2); L4 owed to the planner's batch (checks.md rows 152, 153).

## Plan or engine: the plan is not short
`python3 -m tools.argonia_world.creatures plan-check` (new, `creatures/plan_check.py`): for each creatures-kinds stop,
the whole-province plan's spawn refs within two cells (8,192 units) of the stand, the class's kinds their lists can
yield, the distinct kinds expected when the engine draws one entry per ref (entries level 1, chance none 0), P(>= 4),
spawn points within 90 m and the stand's eye line. Exit 0 only when all three meet the bar. Measured, 2026-11-04:

| Stop | Spawn refs (own class) | Kinds possible | Expected | P(>=4) | Within 90 m | Eye line |
|---|---|---|---|---|---|---|
| coastal-lagoon (31, 11) | 8 (1) | 18 | 5.37 | 0.973 | 4 | clear |
| northern-transition | 15 (15) | 23 | 12.06 | 1.0 | 10 | clear |
| western-frontier | 14 (14) | 23 | 11.14 | 1.0 | 9 | clear |

The round-5 stands measured the same way gave 5.37 / 9.56 / 15.04 expected. The live 2 / 0 / 1 is therefore the
engine's spawning or the read (actors not yet spawned at the read, or names not matching `among`), not the plan.
If the batch reads fewer than 4 again, the report.json `<class>` lists show which: empty lists = spawning or timing;
actors present but unmatched = the name match in `kinds_found`.

Plan side changed: the kinds stand ranking (`tools/journeys/gen.py _kinds_spawns`) now prefers, after the class on
13+ of 25 cells, the most spawn refs of the class's own lists within the read's radius. The lagoon is thin: only 8
dry land/shore lagoon spawns lie 3+ cells from a place in the whole province; the best with a clear 15-25 m stand
still has 1 own-class ref (the rest flooded-forest/interior-swamp D4, whose lists share lagoon kinds), hence 0.973.

## creature-spots reframed (`creatures/journey.py`)
Six stops (water, marsh, upland; two each, different cells) and one den, all by day (13:00 / 11:00, den 12:00),
`sw`+`fw Argonia.esm|0x000E9B` (ARG_Weather_clear_dry) each step with a `read weather` expectation. Each stand is
dry, 15-25 m from its point (`place(..., band=(15, 25))`), clear eye line, facing it, and its point is the nearest
spawn or predator to it. Evidence: `read actors 2801` (40 m) `listed.0 ne null` (fails when none) plus the list kept.
Refresh log: water-a 23.0 m (next spawn 76.9), water-b 20.0 (73.5), marsh-a 20.0 (44.8), marsh-b 18.0 (27.2),
upland-a 15.0 (27.5), upland-b 20.0 (45.3), den-hackwing 20.0 (24.4). `journeys refresh`: 0 not clear, 0 stale.

## Lore and levelling
Unchanged: bands fixed (D1-D4 wild, D5 set pieces), lists all level 1, `creatures check` unlevelled rule (0035);
spawn grounding per 74-ecology as cited in place.py (0032). No list, band or roster row changed.

## Tests
creatures + journeys tests: 92 passed (3 new in `test_plan_check.py`); `run_journey --dry`: creature-spots 7 steps
ok, creatures-kinds 4 steps ok.

## L4 asks for the planner's batch
- journey:creature-spots: 7 stills. Reader: daylight, no fog wall, a creature in frame 15-25 m off, a Black Marsh
  kind on ground or water it allows; den: the hackwing beside its den. State: each `listed` non-empty, weather clear_dry.
- journey:creatures-kinds: 4 stills + `kinds >= 4` at each class. Reader: the spawn's creature or kin in frame; guar
  pen shows two guar. On a red, judge by the kept lists as above (engine vs name match).
