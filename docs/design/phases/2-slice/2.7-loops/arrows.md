<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.7-loops/arrows.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 2.7a2: arrows answer the surface they hit

One row per measurement; the re-measure runs the same commands. Records:
`world/sources/registries/physical-materials.json` (14 materials, module 75 §54-55);
rule: `packages/game-core/src/combat/arrows/surfaceResponse.ts`; wiring: `packages/character/src/Arrows.tsx`.
Untagged colliders count as soil, so every drawn floor that is not soil tags its collider (the sandbox arena floor is `stone`); a tag is `userData.physicalMaterial` on the rigid body's object or an ancestor. An arrow that cannot go in (embed 0) lies flat on the surface (`packages/game-core/src/combat/arrows/restingPose.ts`).

| Measure | Command | Bar | Measured (2026-10-19) |
|---|---|---|---|
| Schema, families, integrity | `python3 -m pytest packages/world-schema -q` | green with the new family | 21 passed |
| Material view fresh, table valid | `python3 -m pytest tooling/world-generation/worldgen/test_material_views.py -q`; `python3 regen.py --check --tool material-views` | pass; current | 4 passed; 1 tool current |
| Rule and records | `npx vitest run packages/game-core/src/combat/arrows` | a test per each of the 14 materials, record-loading test | 24 tests pass (14 per-material, record load, sums to 1, slow arrow rests, ricochet monotonic in obliquity, depth by speed, helpers) |
| Arrow flight unchanged | `node apps/combat-sandbox/scripts/probe-arrow-flight.mjs` (after a sandbox build, under the job guard) | exit 0, gravity 19.62 | exit 0: `{"speed":5,"angleDeg":80,"samples":80,"massKg":0.09706,"gravityScale":2,"measuredGravity":-19.62,"apexRiseMeters":0.5767,"elapsed":1.3167,"descentSpeed":-20.81,"dropMeters":10.713}` |
| Contacts by material in the runtime | `node apps/combat-sandbox/scripts/probe-arrow-materials.mjs` | stone glances, wood sticks, metal breaks, foliage passes, glanced arrow skips on the stone floor and rests flat, then the post behind foliage holds; every contact names its collider | exit 0, see below (2026-10-20) |
| Scenario gate | `npm run visual:check -w @elder-souls/combat-sandbox -- arrow-materials` | PASS | PASS, 4 `combat.hit` landings (soil after the glance, wood, metal's break, the rear post) |

`probe-arrow-materials.mjs` output (outcome, obliquity, pinned roll, speed in, speed out, kept):
stone ricochet 80.0 deg, 0.30, 44.96 -> 20.23 m/s (0.45, the record's) at (-3.20, 1.30, 3.15) on `arrow-target-stone`; the glanced arrow then: stone ricochet on `arena-floor` 70.7 deg, 21.22 -> 9.55 m/s at (-0.65, 0, -3.76), stone rest 68.5 deg, 9.40 m/s at (0.43, 0, -6.74), lying flat;
wood stick 0.5 deg, 0.50, 44.96; metal break 0.9 deg, 0.50, 44.94; foliage passThrough 0.5 deg, 0.50, 44.96 -> 40.46 (0.90);
wood stick (the post behind the screen) 1.0 deg, 40.44 m/s.

## Capture and reader

Strips (hit frame and 1.1 s later, cropped and 3x enlarged from the 400x225 tiny stills):
`lanes/2.7/a2-arrows/strip-stone.png`, `strip-wood.png`, `strip-metal.png`, `strip-foliage.png`.

Reader verdict (`lanes/2.7/a2-arrows/reader-verdict.md`, two passes): inconclusive from the stills. Wood shows a small
dark tick on the post that persists and is absent in the stone strip (consistent with a stuck shaft); stone, metal and
foliage cannot be told, because the scene's label panel and the HUD cover the plate, the screen and the rear post and a
shaft is 3 px at this size. No arrow in mid-air, no clipping. The outcomes are therefore proved by the contact probe above
(which reads the runtime's own contact per arrow), not by the stills. Open: a larger capture with the label panel clear of
the target row (the full-size capture was refused by the job guard's load gate three times).

Re-capture (lane 2.7a2b-capture): full size, 1600x900 (`--no-video --clean --hidpi`; `--clean` hides the HUD and the scenario
label), stills at the hit and 1.35 s later, strips `lanes/2.7/a2b-shots/arrow-strip-<material>.png` and 2x crops
`arrow-zoom-<material>.png`; the foliage screen is 0.35 opaque so the post behind shows. Reader verdict
(`lanes/2.7/a2b-shots/arrow-reader-verdict.md`): wood MATCH (shaft stuck in the post), foliage MATCH (shaft in the post behind
the screen), stone MATCH weak (slab clean, the glance itself not visible), metal MATCH by absence (plate clean, no
fragments). 2.9xc2 tried a record run on a pod (RTX 4000 Ada) for flight and break: the recording was rejected because
the run's live still screenshots stalled the screencast and dropped the frame marker. Fixed (a recorded run cuts its
stills from the retimed recording), and the record run PASSES. Reader (`lanes/2.9x/c2b-shots/reader.md`): wood GREEN,
foliage GREEN, metal GREEN if a vanished arrow is the break (no fragments drawn), stone was RED (the glanced arrow seemed to hang in
mid-air in front of the post: it was stuck tip-down in the untagged stone floor 7 m behind the post, read as soil, propped at its flight angle with no shadow; 2.9xo tagged the floor and laid resting arrows flat, still `lanes/2.9x/o-shots/still-stone-after.png`). Flight is a few-pixel dot at 800x450, not readable.
2.9xc2c (`--hidpi`, 2x crops of the target row at 15 fps; `lanes/2.9x/c2c-shots/reader.md`): stone shows its glance,
wood sticks, foliage shows one tile in flight and then the post behind, and metal shows no arrow at all. Still RED for flight.
Mechanism: `--hidpi` does not reach the recorder (`recorderViewport` stays 800x450, `capture-visual-scenarios.mjs:122`). At
45 m/s an arrow crosses the target row in about 6 simulation frames, a few pixels each. Flight needs the recorder at the
hidpi size or a slowed scenario clock. Metal "vanish" is an owner call in the packet; stone mid-air goes to lane 2.9xo. Arrows are a few pixels and the two stills are 1.35 s apart, so flight and break are not shown; the contact probe
stays the proof of the outcomes.
2.9xp (hidpi record on a pod, `lanes/2.9x/p-shots/arrows/`): the recorder size cannot be made hidpi. With `recordVideo.size` doubled the 1600x912 video holds the 800x450 picture in its top-left and a grey canvas elsewhere (reader), so flight is as small as before; the size change was reverted. Reader: stone PARTLY (arrow in flight about 22 frames, 20 px, a slow lofted arc), wood PARTLY (3 px stuck dot), foliage PARTLY (one frame, 15 px, passes through), metal RED (no arrow in any frame). Next: a closeup camera on the target row (`--closeup` already renders at 2x) or a slowed scenario clock, not the recorder size.

2.9xs (slowed clock, held 2x stills, `lanes/2.9x/s-shots/arrows/`, sheets `flight-*-sheet.png`, `reader-arrows.md`): mechanism of the unseen flight: the probe arrow leaves at 45 m/s from 2 m in front of the target, so the world contact comes 0.05-0.08 s later (metal: contact at flight t 0.067 s, tip at z 3.04, logged in `arrow-samples.json`), about two 30 Hz frames. `VISUAL_SLOW=6` slows the sim clock six times and `VISUAL_HOLD_STILLS="from:to:step"` shoots held 2x frames (no recorder; the 30 fps frame evidence does not apply). Reader: stone PARTLY (arrow in 7 frames, 30-40 px, glance reads faintly), wood PARTLY (15 frames, stuck stub about 8 px), foliage PARTLY/RED (9 frames, pass not shown, no stub on the post behind), metal RED: the arrow is present in about 8 frames (frames 2-9) but black on a near-black plate, so unreadable; at contact it vanishes with no fragment, flash or stub (outcome `break` removes it). So metal is not unseen from being culled or spawned off-frame: it is in frame and lost to contrast and to the vanish at contact. In all four the arrow enters from the frame's top edge (the shoulder camera sits behind the launch), so the launch is not followed. Next: owner call whether a break shows fragments or a flash; a lighter plate colour and a side camera on the target row for the record run
