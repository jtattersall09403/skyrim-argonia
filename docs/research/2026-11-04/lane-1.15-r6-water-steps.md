# Lane 1.15-r6-water-steps: river steps, still water, the water types' far look

Status: L1/L2 done; L4 owed to the planner's batch. Owner play test 3 findings 19 (pieces in the air, uphill, hanging
sheet edges) and 20 (still water drifting).

## Measured on Skyrim.esm (0034)
`python3 -m tools.argonia_world.water.probes.vanilla_piece_seat`: the FX bases' OBND z (unscaled) are rapids line
-560/+589, ring -728/+733, skirt -475/+3258, mist -290/+362. Against the two waters of the 51 dressed Tamriel steps,
vanilla seats every piece so its OBND's foot reaches the lower water: the line's bottom at the lower water (median
+17 u, 50 of 111 at or under it), the skirt's (38 of 49) and the ring's (45 of 49) under it. The tops stand well
over the upper water (spray bounds), so the rule reads the origin, not the top.

## The seat rule (steps.py OBND_Z, judge.seat, `water check seat`)
Every piece against its own step: origin no more than BED_TOL_U (30 u) over the upper water or under the lower; not
facing uphill (more than 90 deg off its chain's yaw); its scaled OBND foot at or under the lower water + 30 u (no
hanging sheet edge). `steps.place` re-seats a piece whose foot cannot reach (the rapids line at a narrow channel's
width scale) by sizing it to the drop; emit counts these in plan.json `reseated`.

On the round-5 close build's DB and ground (out/terrain/ground-f32.npy):
- before (the r5 stream): `water check seat: 759 pieces; reds above upper 0, below lower 0, uphill 0, hanging 123`
- after `water emit`: `water check: 2280 bodies ... 10607 cells, 0 with two levels; 2265 steps, 0 without a chain;
  28 dry reaches` / `water check seat: 759 pieces against their chains; reds {all 0}; re-seated 123` /
  `water check placement: 759 pieces on 203 steps; reds {}`

## Still water (finding 20)
The still types' winners carry a drift (NAM0): DefaultWater 0.22/0.22, DefaultMarshWater 0.15/0.29,
DefaultMarshWaterTransition 0.07/0.37, DefaultWaterCold 0.22/0.22; Skyrim's own still record MurkyWater is 0/0/0.
layer.flow_set now sets NAM0 to 0 on every still type but the sea (lake, marsh, cold, brackish; black is already 0).
The writer test asserts: every still type but the sea has NAM0 0 and no flow-map flag; every river and creek type
carries its template's NAM0 (or the turned one); every body kind (STILL_KINDS, pond, pool) maps to a still type and a
river's own cell to a flowing one.

## River-steps journey
gen.river_steps now takes its three gullies from the build's dry reaches (the chosen ones first, then the first
whose bed takes a clear stand) and asserts the two still cells are still bodies. `journeys refresh --only
river-steps`: 8 vantages, 4 moved, 0 not clear (before: gully-1 stood in water, gully-3 not clear). Stops: steps
(-50,47) s 19.6 m, (-47,16) w 19.5 m, (-59,-12) s 19.5 m; gullies reach.97-2505 (-60,-15), reach.1071-374 (-29,51),
reach.1078-739 (-27,40); still lake (-36,-8), tarn (-62,24). `journeys check`: 0 stale.

## Tests
water tests: 37 passed before the seat test; test_judge 13 passed with it. ruff green on water/ and gen.py.

## L4 asks for the planner's batch (deploy after `water emit` and the plugin build)
1. river-steps journey, all 8 stills, reader judging the header checklist: no piece in the air or facing uphill, no
   hanging sheet edge at the three steps; dry beds at the gullies; no drift on the lake and tarn (a pair of stills
   some seconds apart, or a short clip: drift is motion, the reason for a clip).
2. checks.md row 157: water-types' sea stop and one far vantage read turquoise sea; distant water the same type.
