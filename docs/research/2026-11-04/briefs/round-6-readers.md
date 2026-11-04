# Round 6 reader briefs (pre-written so readers launch the moment stills land; one reader per group, ≤ 40 lines back)

Common: read each PNG with the Read tool; answer per still `PASS|FAIL|UNSURE <still> — what it shows, the checklist hits`; then one verdict line per journey; then up to 5 findings worth a fix. First person and no HUD unless the journey says otherwise. Anything a player would see at the play camera that looks broken is a finding (neon or glowing foliage, pale washed-out trunks, stretched textures, floating or sunken objects, white tiles or marbling in water, a Nordic element, a fog wall where the scene should read).

Scans (owner 19:05 #41, 0036 amended): a stop with `scan: N` has N stills `<n>-<name>-s<k>.png` at headings h0 + k·360/N (s0 is the stand's own aim, the same image as `<n>-<name>.png`; the headings are in the journey's `done.json` and report.json `scan`). Judge the whole scan: name the heading (k and degrees) that shows the subject best, give PASS or FAIL on that heading, and name the heading the stand should take (`stand heading: <deg>`) when it is not s0, so the driver retakes inside the run and the generator re-aims. A scan where no heading shows the subject is a framing FAIL with the nearest heading named. Readers launch per journey from `done.json` (run_batch `--on-done`), not at the round's end.

## Group A: trees (the booth stills, tests/journeys/batches/1.15-round-6-booth.txt)
Per form the question on its line of the booth list. The pairs decide causes: Willow05 against 01Willow (only the KotM willow neon → leaf wrap; both → weather/shader); Swamp01 against Undergrowth01 (the card yellower → vertex tint). Then world-panel stops 6-9 (deep-river corridor), 10-12 (deep-sink basin), 2 (lagoon reflections): no neon lime willows, no olive or yellow-green cast at noon beyond the canopy's own colour, no pale trunk, no streaked bark.

## Group B: sky and light (sky-ab, world-panel noon and dawn)
Noon clear-dry: deep blue zenith, sparse cloud, no veil, no yellow or olive cast over the open scene (the lagoon is the control; the corridor and sink basin are the question). Dawn 06:30 clear-dry at the two sky-ab vantages: a coloured dawn (rose-orange horizon, blue-slate zenith), no cream wash, no grey veil. Dawn mist (world-panel 03, 05, 07, 09): mist with depth, and now light shafts where canopy or mist allows (volumetric lighting re-enabled): say whether shafts show and whether the grey veil of the round-5 bisect is back.

## Group C: water (water-types 7 stops, river-steps 8 stops)
Seven waters distinct: sea turquoise (Tropical Skyrim's), green marsh, black swamp near-black, river flowing, stream clear, tarn cold teal, brackish rim between; water fills the middle of the frame (the stands were re-aimed clear of canopy and fronds: say if any still sits in foliage); near and far water read as water, no marbling, blotch or white tiles. River-steps: at the three steps no piece in the air, none facing uphill, no hanging sheet edge; dry beds at the three gullies; the lake and tarn show no drift between the paired stills.

## Group D: ground, roads, rocks (ground-materials, road-look, rock-booth)
Ground at -9 27 and -50 8 midday: matte, no sheen on slopes or roads, no wide flat field of the mossy-pebble texture, textures resolved (no purple, no missing). Roads on the Blackwood Road: a worn lane with a soft paint edge, a shallow trough, no wall or bench beside it. Rocks: each of six stills shows its rock seated in the slope, not floating, not sunk to its waist.

## Group E: creatures (creature-spots 7, creatures-kinds 4)
Daylight, no fog wall, a creature in frame 15-25 m off, a Black Marsh kind on ground or water its kind allows; at the den the hackwing beside its den; at the pen two guar. The runner's actor lists are the evidence: an empty list with no creature in frame is a spawning or timing finding, actors listed but not in frame is a framing finding.

## Group F: Claywater (claywater-walk 8, claywater-look 11) and navmesh-paths
The quest board on dry footing; the well; the docks' deck over the water with the poler on it; the station-house door and hut doors flush with the lifted ground; no walkway or tower stray; no sign the common stands in water. navmesh-paths is a state read (found share), no still to judge beyond the frame-time stop.
