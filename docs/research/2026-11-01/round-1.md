# 1.15 round 1: driver report (build 5572e05, argonia-play-ie, 2026-11-02)

Batch: tests/journeys/batches/1.15-round-1.yaml. Run dir: out/batch/1.15-round-1/20261102T001443 (world-panel retry: out/batch/1.15-round-1/20261102T002531).
Machine stopped at the end. Frame time (bridge probe, upland-night creature spot, not the densest panel vantage): mean 16.7 ms, p99 17.4 ms, 60 fps.

## world-panel: not run (harness: cow crash, rerun on the marker build)
The scene's first `cow ARG_Province 26 -17` crashed the game twice (22.7 s; retry 00:25), EXCEPTION_ACCESS_VIOLATION executing at a 0x014A.../0x0155... address; crash heads in the run dirs. No panel stills. Per the planner: rerun with d55ab69's marker-based panel on the next deploy. Other `cow`s in the batch (creature-spots, six of them) did not crash, so the crash is first-cow-from-base-save specific.

## rock-booth: PASS (runner), evidence unprovable
6 stills, still_ok 0 each. Reader: all six problem or unjudgeable: camera at the player's back, base hidden by fog, foliage or scale; rock03 and rock05 show pale flat-shaded polygon masses (missing texture or oversized mesh); rock02 a black shard in the sky; rock06 shows no rock. Harness: the booth framing cannot show sunk/gap/hollow-back; needs a camera per rock at ground level. World finding (vegetation lane): pale untextured rock masses in rock03/05 to be checked.

## creature-spots: FAIL at upland-night (teleport tolerance), 6 stills confirmed
Teleport z 14052 landed at 14734-14785: the spot's z is ~700 units (10 m) below the generated ground (harness/data: spot z from the older ground; the other spots landed 60-160 below their z, falling to ground). Fix owed: regenerate spot z from the ground. The journey does not persist its actor reads; I re-read by hand (cow, setpos z+800, actors within 2801 units):
water-day: Large Sun-Blessed Toad 655 | water-night: Moss-Foot Croaker 172, Crocodile 2350, Alit 2775 | marsh-day: Kotu Gava 399, Jungle Centipede (dead) 960 | marsh-night: Giant Centipede 659 and 1013, Crocodile 2699 | upland-day: Jungle Rattler (dead) 936, Hackwing (dead) 2551 | upland-night: Mudrunner 935, Forest Drake 1660. Den (kaj-thux) not reached (journey stopped).
Reader: marsh-day ok (giant bug in swamp, vibe-02); upland-day ok, no Nordic; water-night ok-dim; water-day opaque yellow-ochre fog (weather lane); marsh-night almost black with a stray blue blob (weather/materials); upland-night camera faces a trunk. Only one creature visible in six stills, so habitat check rests on the reads: Crocodile on marsh-night at 2.7 km and Alit in water-night are plausible; no mismatch spotted. Harness: night stills too dark, spots need a camera toward the creature.

## claywater-walk, claywater-look: FAIL (expected), 6 + 11 stills confirmed
Both stop at entering the station house: GetInWorldspace ARG_Province stays 1 (the door does not take; the camera is stuck against a green slab and thatch mound at the door, stills 05/06 and look 11 identical). Gap measured: huts (look 04, 05, 10) meet new ground and water cleanly, no pad edge, no float; several stills show no buildings or people (walk 01-04, look 01, 02, 06, 08: places not under the camera or not placed); look 07 has a solid black wedge and a sawtooth slope (ground lane); look 09 jagged stone wall, shrine base slightly sunk. Nothing fixed.

## L5 temporal strip: not taken (no panel vantage reached).

## Findings by lane
- harness: first cow crash (world-panel); creature-spots z stale and actor reads not persisted; booth and night framing; still_ok needs ~/.argonia/venv python (numpy).
- ground: sawtooth slope and black wedge at the Claywater clay cut; spot z 10 m under ground at upland-night.
- weather: day water fog opaque ochre; marsh night black.
- vegetation: pale untextured rock masses (rock03, rock05).
- creatures: reads plausible; Kotu Gava, Mudrunner, Forest Drake, Hackwing and Rattler spawn as expected kinds.

## Session 1b (build aa118a1, argonia-play-ie, 2026-11-02)

Run dirs: out/batch/adhoc/20261102T005956 (rock-booth 02-, creature-spots 03-; its world-panel failed at the first-person expectation), world-panel out/batch/adhoc/20261102T011213/01-world-panel-1-20261102T011214 (PASS, 37 stills, all still_ok 0), strip out/batch/1.15-round-1/strip/strip-mist.png (frames mist-6 ... mist-8). Machine stopped. Frame time (300 frames, deep-sink-basin shore, forest, third person): mean 16.7 ms, p99 17.6 ms, max 31.5 ms, 60 fps (not measured at a separately chosen densest vantage).

Harness fixes made: (1) the vocab cache was stale (tools/fetch_vocab.py rerun) so the lint rejected every ARG_Ref_Panel* marker; (2) the panel's position expects used `pos.0/1/2`, the read gives `pos.x/y/z` (tools/argonia_world/panel.py and the journey fixed); (3) the first-person step blocked the run: the F toggle is now taken after the first moveto with `F 300 engine` and is not asserted; (4) the runner's bare console lines retry 30 s on "main thread did not run the task" (the lines after a moveto hit the loading thread). Findings: the camera is third person with our HUD showing in every still (IsPC1stPerson stays 0 after F on either route; `tm` does not hide our HUD): the panel is third person, a harness note; first person and hidden HUD need a bridge control. `cow` was never used; no crash in 36 moves.

world-panel readers (12 each): ok: 10 deep-sink-basin shore noon, 11 its dawn (mist visible, dark), 14 flooded-forest shore noon, 22 northern-transition shore noon; everything else problem. Recurring: untextured pale lavender/white/purple trunk bases, flowers and plants (deep-river 06-09, flooded-forest 14-19, tidal-delta 30-31, 33; materials); one repeated orange leaf swathe on slopes (04, 05, 12, 13; materials/ground); stretched moss wall (20, 21; camera against a slope, harness plus ground); coastal-lagoon shore 02, 03 blown-out haze or camera at water level (weather/harness); black voids (07, 23, 35, and 07:30 of the strip; ground or materials); flat opaque white water with hard bank edges (08, 09, 24, 29; ground/water); smooth cone and pyramid slopes (28, 29, 36, 37; ground); camera inside foliage (26, 27, 34, 35; harness); dawn mist grey and flat, no god rays anywhere, no sea fog at tidal-delta, western-frontier not read as cool cloudy forest (weather); northern-transition drooping conifer-like trees lean Nordic (vegetation, check).

L5 strip (06:00 to 08:00, ARG_Weather_mist at deep-sink-basin shore): reader verdict not demonstrated: no visible burn-off or clear brightening, white ground patches pop between frames, a solid black rectangle at 07:30 (weather, materials). Possible harness cause: set gamehour with a forced weather does not transition.

rock-booth: 6 stills confirmed; reader: no rock identifiable in any (01, 02, 04 steep slope views; 03, 05 no rock; 06 inside ferns); pale untextured tan masses in 05, 06 unconfirmed. Still unprovable: raise DIST in tools/argonia_world/vegetation/booth.py and aim at the rock ref.

creature-spots: PASS, 7 stills confirmed, actor reads in report.json: water-day Crocodile 680 and dead Jungle Centipede; water-night Salt Crocodile 688, Crocodile 2295; marsh-day Kotu Gava 479; marsh-night Jungle Centipede 1237; upland-day dead Jungle Centipede; upland-night Jungle Rattler 913, Alit 1771; den: Giant Snake 951 (not loaded) in a list of 80 mostly Skyrim NPCs from the wrong cell (den teleport reads vanilla actors; spot or list is wrong; creatures lane). Reader: no creature clearly in frame but Kotu Gava (marsh-day); water-day and night too foggy or dark, upland stills blocked by the player; upland-night shows a white snow-like slope (ground/materials). No Skyrim animal seen. Marsh-night: a Jungle Centipede and no crocodile now; kinds fit the habitats.
