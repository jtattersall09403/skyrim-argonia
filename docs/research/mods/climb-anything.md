# Climb anything big enough: what Free Climb reads and what the 1.15 world must give it (2026-11-01)

Owner ruling: owner-brief.md:265. Source read: Eelta/FreeClimb at 8a48ffe (2026-10-10, same as the pinned 0.5.0,
data/dependencies.json id "freeclimb"), cloned to scratch (not in the repo), plus the installed mod
`~/.argonia/stack/MO2/mods/freeclimb/` (FreeClimb.ini, DLL strings). The README documents none of the surface test;
the source does. Measurements: a throwaway script over tools/navmesh/{esm,nif,meshes}.py (bhkRigidBody layer byte at
body+4, mass at body+180), run with ~/.argonia/venv/bin/python3.

## Live docs
Covering it: docs/research/native-map.md:239-240 (G35.1/G35.2, "what it reads UNVERIFIED") and :402 (open question);
docs/phases/2-slice/2.13-swim-and-climb.md:21-34 (climbing as FreeClimb base); reuse-audit.md:257.
Confirmed: GPL, 1.7.104, settings reach speed and stamina (Movement/Stamina in FreeClimb.ini). Resolved here:
the climbable test is data-driven (collision layer + normal), so G35.2 is "fully" by data, no fork. Doc to edit:
native-map.md G35.1/G35.2 and :402 (replace UNVERIFIED with the findings below); 2.13 brief gets one line.

## 1. How Free Climb decides (VERIFIED from source)
- One ray test classifies a hit: src/Plugin.cpp:439-492 (`GameWorld::ray`). The ray filter is layer kCharController
  (:457). `climbable` ("stable") is true when the hit body's COL_LAYER is kStatic, kGround or kTerrain (:484), or when
  layer is kTrees/kClutter/kWard/kProps AND (tree OR the reference's base form is a STAT) AND the body is a fixed-motion
  entity, and for trees also response kSimpleContact (:486-492). No whitelist of forms, materials or keywords: the
  material is never read.
- Refused: any other layer (AnimStatic 2, Transparent 3, NonCollidable 15, Debris, Biped, Water, Trigger, doors);
  moving or dynamic clutter/props; clutter/props whose base is not a STAT (MSTT, ACTI, FURN); ActorZone triggers (ignored,
  :361, :415); self hits (:473-479). Also refused at the gate: player swimming, mounted, sneaking (Plugin.cpp:732-742;
  sneak lifts with ClimbSneakEnabled).
- Angle (Core.h:2172-2181 `wall.valid`): attach needs normal.z in [-0.15, MaxNormalZ] and the normal facing the
  player (horizontal dot forward < -0.65). Default MaxNormalZ 0.70 = surfaces steeper than 45.6 deg from flat; while
  tracking up the wall -0.45..0.94 (overhangs, crests, roofs: Core.h:1495, 2182). Below 45.6 deg the player simply walks.
- Support / narrowness (Core.h:2189-2200): four probe heights (6, 32, chest 70, grip 112 units) each need a second
  valid hit 10 units to a side, within 45 units, normal dot > 0.70. So a climbable face must be at least ~10 units
  wide and not jagged below 0.7 cosine. Curved trunks and rocks pass; spikes and bars do not.
- Ledge/top: top-out needs a standable footprint (standingFloor 8x8, Core.h:2615), body clearance, and the top within
  grip+28 = 140 units of the hand position per mantle (Core.h:2619); the climb itself has NO height cap. Cost is stamina
  only (ini Stamina: MovingPerSecond 10, RequiredToGrab 12; Enabled=0 removes every cost, per $FC_STAMINA_HELP).
- Reach 110 units, GrabMaxSnap 60 (FreeClimb.ini [Detection]).

## 2. Settings versus our own code
- Clamps (src/UserSettings.cpp:44-48): Reach 40-160, GrabMaxSnap 5-60, GroundJumpHeight 0-88, MaxNormalZ 0.2-0.75.
  Defaults are already at or near the clamp ceiling for "anything": the one useful change is MaxNormalZ 0.70 -> 0.75
  (attach from 41.4 deg), optional. Reach could rise to 160 for tall-grass/tree-bark tolerance, optional.
- Nothing in settings widens the layer set, drops the fixed-motion test, or adds forms. That is the only place an
  SKSE adaptation (route 3, fork; GPL ok per reuse-audit.md:257) is needed: add kAnimStatic (2) and MSTT/any fixed
  body to `stable` at Plugin.cpp:484-492, and only if the world cannot be fixed instead. Wet slip, burden stamina, a
  hand-off to our Acrobatics bands are Core.h/Plugin.cpp rules, also fork or ArgoniaCore side (2.13 a).
- Wall run is on by default (ini WallRunEnabled=1); 2.13:30 wants it off (old 0152). Set WallRunEnabled=0.

## 3. What the world must provide (1.15 rebuild)
- LAND, all slopes: VERIFIED by logic, UNVERIFIED in game. The ground lane limit is 75 deg (lane-1.15-ground.md:23);
  normal.z = cos 75 = 0.26, inside [-0.15, 0.70]; the engine's LAND collision is layer Terrain/Ground and both are in
  `stable`. LAND facets are 128-unit triangles, so the ±10 support probe always agrees. 82.9 deg (VHGT int8,
  world-rebuild-options.md:21,72) is the hard ceiling and also climbs. Slopes under 45.6 deg are walked, not climbed:
  that is correct, but note 45-60 deg is 14 % of vanilla vertices (skyrim-does-it-this-way.md:60) and the slope
  band 45.6 to ~60 deg will be a "scramble" that FreeClimb will not take; a designed cliff face wants > 55 deg.
  In-game check needed: attach test on a 60, 75 deg LAND face (L4).
- Placed rock meshes: need only that the NIF's bhkRigidBody is layer 1 (Static) or 13 (Terrain) with mass 0, which is
  how every Skyrim.esm rock is built (§4). No keyword, no material. Measured on ours:
  - the 20 ARG_Rock STATs (rocks.py:23-42): 20/20 layer 1, mass 0 -> climbable (BM&V NIFs in ~/bmvtmp/out/meshes).
  - BM&V landscape/rocks, 312 NIFs: 199 layer 1, 38 layer 13, 1 layer 1 with mass 1.0 (IvyPine), **74 NO collision
    (24 %)**; landscaping/rocks 72: 70 layer 1, 2 none; vvardenfell/rocks 28/28 layer 1. A no-collision mesh cannot be
    climbed (no ray hit) and cannot be walked on, so the placer must not pick it, for any reason.
- Trees: TREE records climb when the trunk body is layer 9 (Trees) fixed with simple-contact response, or layer 1 (Static)
  (Plugin.cpp:483-492). Skyrim.esm TREE (150 meshes): 35 layer 9, 19 layer 1, 32 layer 15 (plants, never climbable),
  64 no collision. Tropical Skyrim TREE (51 meshes): 13 layer 9, 28 layer 1 (3 with a second mass-1 body), 1 layer 15,
  9 none. STAT trees climb equally if layer 1. The engine's simple-contact response on layer 9 is UNVERIFIED (no
  response byte read); layer 1 trees avoid that test.
- BM&V building walls: UNVERIFIED. Only 7 NIFs are loose in mods/bmv; its architecture meshes are not unpacked (the
  vault tar was unpacked for rocks only). Vanilla architecture is the proxy: Whiterun (640 meshes) 609 layer 1, 24 layer
  3 (Transparent: small gates, fences, tower collision pieces, NOT climbable), 3 layer 2 (AnimStatic: waterwheel,
  drawbridge, NOT climbable), all mass 0. So walls climb; moving parts and fence-collision layers do not.
- Never climbable by construction: our water-edge/river layer parts, plants (layer 15), any mesh with no bhk body.

## 4. Skyrim.esm measurement (decision 0034)
Skyrim.esm STAT/TREE unique MODLs, bhkRigidBody layer (nif.py reader) and mass 0:
| class | n | layer 1 Static | layer 13 Terrain | other |
|---|---|---|---|---|
| Landscape\Rocks + Mountains + cliff names (228) | 228 | 204 | 22 | 2 none (Markarth cliff, Sovengarde base) |
| TREE | 150 | 19 | 0 | 35 layer 9, 32 layer 15, 64 none |
| Whiterun STAT architecture | 640 | 609 | 0 | 24 layer 3, 3 layer 2 |
Vanilla dresses climbable-looking cliffs as layer 1 STAT shells (RockCliff01) with layer 13 for the big mountain skirts
(MountainTrim03, MountainCliffCrevasse): the same classes the climber accepts. Every body is mass 0. Vanilla cliff
shells are 0.7 sunk and tilt with the ground (skyrim-does-it-this-way.md:104-112): that is also what keeps the face
reachable: the shell's rock face, not the LAND, is what the player touches above a few hundred units.

## 5. Changes
Ground lane (1.15 ground):
1. Designed cliff faces at 55-75 deg (the existing 75 cap holds); the 45.6-55 deg band is walkable-or-nothing, do not
   count it as climbable content. Record the cliff mask (cliff-u8.npy, >60 deg) as the climbable-terrain mask.
2. No steps, bridge-like discontinuities or 1-vertex 160 m drops in the cliff mask (support probe needs 10 units of
   continuous face); the existing step-band fix covers it.
Vegetation lane (1.15 vegetation):
3. Rock picker admits only NIFs whose bhkRigidBody is layer 1 or 13 with mass 0: filter out the 24 % of BM&V landscape
   rocks with no collision and any mass != 0 (IvyPine). Add a rocks.py check on the 20 STATs (all pass today).
4. Cliff shells stay layer-1 STATs (rule 2: upright); keep embedding 0.7 so the shell meets LAND without a ledge gap.
5. Trees: prefer TREE/STAT meshes with a layer 1 or layer 9 mass-0 trunk body; drop layer-15 and no-collision forms from
   climbable species (they can stay as flora). Add a per-form `collision_layer` column to the form inventory.
6. A forms test: every form that is meant big (cliff shell, boulder over 2 m, tree) has a climbable layer; report the
   share per class (Skyrim.esm baseline above).
Climbing chunk (2.13), not 1.15:
7. Ship FreeClimb.ini with WallRunEnabled=0 and our stamina bands; MaxNormalZ=0.75, Reach up to 160 optional.
8. Decide fork scope: add AnimStatic (2) and fixed MSTT to `stable`; wet slip, burden stamina; BM&V building wall
   measure once the architecture is unpacked; L4 attach tests: 75 deg LAND, a layer-1 rock, a TREE trunk, a BM&V wall.
9. Doors/AnimStatic parts and layer-3 fences stay unclimbable (a rule, not a bug).

Covered: FreeClimb src (Plugin.cpp, Core.h, UserSettings.cpp), installed mod ini/DLL strings, Skyrim.esm, Tropical Skyrim.esp,
~/bmvtmp rocks, repo research docs. Skipped: in-game attach (no run, read-only); BM&V architecture/trees (not unpacked);
engine response/motion byte for layer-9 trunks.
