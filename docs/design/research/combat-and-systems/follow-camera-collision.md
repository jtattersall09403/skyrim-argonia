<!-- imported unchanged from elder-souls-argonia docs/research/combat-and-systems/follow-camera-collision.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Follow camera collision: how the reference games keep walls out of shot

Evidence for 16h check-in 2 item 3 ("the camera clips into buildings") and
for part 2 item 24 (the interior camera). Read by
`packages/game-core/src/camera/followCamera.ts` and
`packages/world-render/src/player/cameraObstruction.ts`.

## What the reference games do

- **Tears of the Kingdom.** An obstruction pulls the camera in. When the way
  clears it does not snap back: it returns gradually and only in response to
  player input (Asher Zhu, reported by
  [80.lv, 2025-09-19](https://80.lv/articles/third-person-camera-movement-trick-in-the-legend-of-zelda-tears-of-the-kingdom)).
- **Skyrim.** The camera is its own collision layer (`L_CAMERA`,
  COLL:00088788) that collides with statics, animated statics and trees; a wall
  zooms the camera in, and the player model blends out when the camera is too
  close ([UESP Skyrim Mod:Mod File Format/COLL](https://en.uesp.net/wiki/Skyrim_Mod:Mod_File_Format/COLL);
  Nexus SSE mods [57864](https://www.nexusmods.com/skyrimspecialedition/mods/57864),
  [19310](https://www.nexusmods.com/skyrimspecialedition/mods/19310)).
  Without wall collision the player sees through walls
  ([Nexus SSE 57692](https://www.nexusmods.com/skyrimspecialedition/mods/57692)).
- **Dark Souls / Elden Ring.** A sphere collider pulls the camera in; players
  report it snagging and bouncing in tight corners
  ([gamedeveloper.com, third-person camera problems](https://www.gamedeveloper.com/design/third-person-camera-view-in-games-a-record-of-the-most-common-problems-in-modern-games-solutions-taken-from-new-and-retro-games)).
- **A ray is not enough.** The near plane has size; sweep a sphere at least
  the near plane's half-diagonal
  ([ndotl, 2014](https://ndotl.wordpress.com/2014/10/18/third-person-camera/);
  [Godot SpringArm3D](https://docs.godotengine.org/en/stable/tutorials/3d/spring_arm.html)).
- **Alternatives for interiors.** Dithering the occluders nearest the camera
  (The Witcher 3), a silhouette through walls (Mario Sunshine) or a cut-out
  view (For Honor), same gamedeveloper.com source. A screen-door dither is a
  `discard` on a Bayer pattern, cheaper than alpha blending
  ([mirzabeig.com, camera dither fade](http://www.mirzabeig.com/tutorials/camera-dither-fade/)).

## What we built (2026-09-24, ledger row "Check-in 2 fixes: runtime")

- `FollowCamera` takes an injected `(from, to, radius) => distance | null`
  query and imports no physics engine. The arm is swept from the pivot
  (player + 1.15 m) to the smoothed orbit position with a 0.3 m ball: it
  pulls in at once, and grows back at 2.5 m/s only while the camera stick
  moves or the player walks.
- The studio answers the query with a Rapier ball cast against the
  camera-blocking group (`packages/game-core/src/camera/cameraCollision.ts`):
  settlement and terrain colliders block, vegetation opts out, sensors and
  moving bodies are excluded by the query flags.
- The player model fades from a 1.2 m arm to nothing at 0.5 m.
- The CPU terrain clamp stays as the fallback outside the collider ring.
- The view aims along a direction, not at a point (2026-09-25, check-in 3):
  the aim is taken from the unobstructed geometry (look target minus the
  full-arm orbit position), smoothed at `lookSmoothing` and renormalised, and
  the pulled-in camera looks along it, so the view pitch no longer changes
  with arm length (it nodded 25 to 71 deg as a wall shortened the arm).

## Water: the surface is a ceiling (owner, 16x)

Skyrim has no swim camera rule: no swim camera setting is documented, its
camera crosses the water plane freely, and players complain that they end up
looking down through the surface at their own diver (UESP forum t=30466,
Nexus Underwater NG 187230). Treating the surface as a ceiling is our design
choice to prevent that, not Skyrim's behaviour (diagnosis:
`lanes/16x/diag/swim-camera.md`). The rules:

1. `FollowCamera.setWater({ surfaceY, headDepth } | null)` is set every frame
   from the swim's water sample (head = body centre + 0.7 m); null out of water.
2. Walking, wading and any head above the surface: no water rule.
3. Swimming at the surface (head depth under 0.3 m): the camera crosses the
   plane freely both ways.
4. Submerged: the camera position stays at or under `surfaceY - 0.35 m`
   (`waterCeilingGap`), so it never looks down through the plane.
5. The clamp slides the camera in along the arm to that line (a shorter arm,
   never under `minArm`); when the pivot is itself above the line, the camera
   drops straight down to it.
6. The ceiling's weight follows head depth from 0.3 m (none) to 0.6 m (whole),
   eased at 4/s (0.25 s), so surfacing and diving never pop.
7. The 0.35 m gap also keeps the camera clear of the wave cut, where the
   underwater look switches on at camera y < surface - 0.08 (`WaterEffects.ts`).
8. The land pitch floor (`minPosPitch`, which keeps the camera off the ground)
   fades out with the ceiling's weight, so under water the camera can go below
   the swimmer and look up.
9. Only the position is clamped; the aim is untouched. The swim steers from the
   orbit pitch (`swimStroke`, `followCameraLookY`), never from the drawn
   camera, so neither the ceiling nor the camera's smoothing changes where the
   stick goes.
10. The underwater look (fog, tint) keys off the camera under the plane, as it
    already does in first and third person.
11. Fog follows a WaterType-style near/far pair per water body, clear near the
    surface and opaque at the far plane (CK wiki WaterType); not built yet.
12. The player fade (1.2 m to 0.5 m arm) still applies; the water rule never
    fades the player.
13. After the ceiling lets go, the arm grows back under the existing
    `returnRate` input gate, with no snap.

Tests: `followCamera.test.ts` (3 m under at pitch 0.6 the camera is at or
under surface - 0.35; at the surface it goes above the plane; the blend over
0.3 to 0.6 m). The combat sandbox's inline camera does not have the rule yet.

## Open

- Interior shells (the stilt hut): near-plane fade of occluders inside a
  shell. The settlement renderer draws buildings as
  `InstancedMesh` buckets, so a fade needs a per-instance attribute and a
  `discard` in the settlement material patch (which CSM re-hooks), on every
  material variant.
