# Lane 1.15-r6-stepped-pools-2: the pool-keep rule lands, roads and bridge seats exempt

Status: shipped. The rule is in terrain/water_field.py, the exemption in terrain/generate.py (`pool_exempt`), the gate's ceilings are lowered in water/edges_census.py, and there are 5 L1 tests in terrain/tests/test_stepped_pools.py. Nothing was generated into out/: the next chain's land pass makes the ground. The L4 check at the three stands goes in the planner's batch. The terrain LOD half is owed at the final step.

## The rule (from lane 1.15-r6-stepped-pools)
- In cells beside a level step, no lift raises a sample by more than FACE_GRADE (2.0 m) per sample of distance from the raster water.
- A clipped line keeps its need and falls from it at WALL_GRADE (6 m per sample).
- The hollow lift is capped the same way.
- New: `water_field(..., exempt=)` keeps the full lift on two kinds of ground:
  - each road's corridor (routes/shape.corridor, the core plus POOL_EXEMPT_M = 14 m: the 6 m causeway shoulder and the roads census's 8 m bank band);
  - each step bridge's deck span (shape.deck_span) and seat (a disc of to_m + half_width_m + SEAT_EXEMPT_M = 30 m about the seat's end).
- Trials on scratch grounds (`terrain generate --out`, about 470 s each):
  - roads and seats both at 30 m: 93 far steps, which misses the bar of 90;
  - both at 14 m: 83 far steps, but gideon-step end 1 sat 0.35 m off its deck (red);
  - roads at 14 m and seats at 30 m: the landed trial.

## Census, before (the round chain's main ground, 06:57, the code before this lane) and after (the landed scratch ground)
| | before | after |
|---|---|---|
| kept steps with no lower water within 12 vertices (of 203) | 183 | 83 |
| foot, vertices p10/50/90 | 13/33/33 | 1/4/33 |
| buried held cells (of 2,449) | 1654 | 1232 |
| red lines | 0 | 0 |
| (-50,47) wet / footprint | 0.4 % / 8.1 % | 13.3 % / 8.1 % |
| (-47,16) wet / footprint | 0.5 % / 2.8 % | 6.3 % / 2.8 % |
| (-59,-12) wet / footprint | 0.7 % / 2.2 % | 3.5 % / 2.2 % |

## Roads census (`routes census`), before and after
| | before | after |
|---|---|---|
| highest bank p99 (bar 0.429) | 0.357 archon-gideon | 0.357 archon-gideon |
| bank max grade | 0.394 | 0.394 |
| m under water outside a ford | 0 | 0 |
| causeway m | 7492 | 7174 |
| seats off their deck, max (bar 0.30) | glenbridge-step end 0: 0.31 | glenbridge-step end 0: 0.31 |

- The glenbridge-step seat is the failure that was already there; the lane leaves it unchanged. Every other seat stays at or under 0.23 m.
- The lane without the exemption had cartwrights-cross-fig-market, gideon-ridge-runners-post and glenbridge-the-road-nisswo-house at 0.70, 1.01 and 1.06. All three are now under the bar.
- `routes check`: the one fail ("flat road" share of 0.059 before, 0.053 after) was already there and is not this lane's.

## Skyrim.esm's bars, carried over (probes/vanilla_hanging_edges.py)
- Upper pool bed range: 3.43 m at p50, 8.04 m at p90, 17.0 m at most.
- Cell fall: 6.7 m at p50, 23.3 m at p90.
- The lower thalweg is under the lower level by vertex 0, 6 and 33 (p10, p50, p90).
- The face falls about 2.0 m per vertex.
- In Skyrim.esm, 36 of 77 kept steps have no lower water within 12 vertices. Ours is now 83 of 203.

## Gate
- `edges-census`: FOOT_FAR_MAX goes from 183 to 83 and BURIED_MAX from 1654 to 1232.
- `make plugin PLAN=1` names ground, terrain, water and what follows them as runs. The worktree's out/ is empty, so the plan cannot show which stages this change alone re-keys.
- Ruff is clean, and the 5 L1 tests pass with test_shore_floor.
