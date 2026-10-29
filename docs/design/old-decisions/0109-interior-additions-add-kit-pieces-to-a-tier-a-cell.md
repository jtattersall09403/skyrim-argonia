<!-- imported unchanged from elder-souls-argonia docs/decisions/0109-interior-additions-add-kit-pieces-to-a-tier-a-cell.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0109 — Interior additions: a builder may add kit pieces to a tier A cell

**Status:** accepted (planner ruling). Extends
[0103](0103-tier-a-interiors-ship-in-16k-and-every-promise-is-a-placed-socket.md)
decision 3 (a tier A cell is copied verbatim) and follows
[0104](0104-the-world-is-one-normalised-record-set-promises-are-fulfilled-by-placed-interactables.md)
(one home per fact). How an interior is lit, windows and daylight
included, is [0123](0123-interiors-are-lit-by-their-sources-windows-and-beams.md).

## Why

Seven King of the Murkmire tier A cells (KeebaHouseFisher, -Crafter,
-SnailMinder, -Elder, LilmothGlassworksOverseerHouse,
LilmothIronworksOverseerHouse, LilmothPlantationStorehouse) read dim. Their
author lit them for Skyrim, where the cell's directional-ambient cube does
most of the work; we do not import that cube, and the plugin places few
lights with small radii (2.5–4.6 m). Raising the ambient fill passes the
dark bar but leaves the room flat (0–4 % source-led, § 7 of
`doors-interiors-sockets.md`). The room needs more sources, and before this
record no builder could add a fixture to an interior cell:
`kit-interiors/substitutions/<cell>.json` only stands in for a missing refId.

## Decision

1. **Home.** `world/sources/placement/kit-interiors/additions/<cellId>.json`
   is the one home of a cell's additions: `{schemaVersion: 1, cellId,
   additions: [{id, assetId, pos: [x, y, z], rotZDeg, zone, why}]}`. `id` is
   stable, `<cellId>:add:<slug>`; `pos` is metres in the cell's own frame
   (the placements' frame); `zone` is one of bed, table, hearth, work, door,
   store, shrine; `why` is one line, the resident's reason.
2. **Additions only add.** An addition places a published interior kit piece.
   It never moves or removes a plugin reference; a missing plugin piece is a
   substitution, never an addition.
3. **Export.** `worldgen/export_interior_bundle.py` (`load_additions`) reads
   the file after the substitutions and appends each addition to
   `placements[]` with `source: "addition"`, sorted by id. It refuses an
   `assetId` in no published kit, a duplicate or foreign id, an unknown zone,
   a missing `why` and a `pos` outside the box around the plugin placements'
   bounding spheres. Additions stand outside the `refCount` sum and out of the
   absent-master placement votes (R45). The lighting rule
   (`interior_light.apply_light_rule`) then runs over them like any placement:
   a piece whose kit manifest carries a `light` gets it.
4. **Lighting design rule** (for the builder who writes the file): every
   living zone (bed, table, hearth, work, door) has a flame fixture within
   2 m, and there is at least one lit fixture per 12 m² of walkable floor.
   Prefer the plugin's own fixture kinds (candles, candle-horns, lanterns),
   placed where a resident would put them: on the table, beside the bed, on
   the hearth wall, and inside by the door. Verify with `light_balance`
   source-led ≥ 70 % and the `render-interior` readers (readable, warm, lit
   by its sources). A cell's fixtures are sized by n = ceil(walkable
   area / (0.6 π r²)) and capped at 30. Over `ROUTE_MODE_AREA_M2` (2000 m²)
   of reached floor the cell is measured in route mode: only the 6 m corridor
   either side of the walked door-to-socket paths is lit-measured, and
   additions outside that corridor are refused by `interior_seat`
   (`doors-interiors-sockets.md` § 7).

5. **Damp cells** (caves, barrows, root hollows: `kind` `damp` in the
   interior light record). Besides fires, a damp cell may light a zone with
   glowing fungus: the emissive mushroom pieces of the `interior-kotm-v1`
   and `dungeon-root-v1` kits, placed in clusters on the floor and the root
   walls where nothing lives (zone `store`). A piece whose kit row carries no
   mined `light` only glows, so a dark zone then still needs a flame or a
   light-carrying piece to pass gate `interiors.dark`.

5a. **Daylight-class plugin lights.** A LIGH whose base editor id matches a
   pattern in `packages/game-core/src/interior/interiorLightClasses.json`
   (`DefaultSunlight*`, `*Daylight*`: the plugin's sun omnis) stands in for
   the sky, so it follows the sky's daylight share (`skyShare`) and is dark
   at night. One rule row, read by the runtime (`isDaylightLightBase`,
   `InteriorLighting.lightIntensity`) and by the render
   (`interior_render.daylight_base`; the night row hides these lights), so
   the two cannot drift. A cell the night leaves dark is lit by raising its
   fixtures (rule 5), never by keeping the sun omni on. The night ambient
  has two parts, both in `interiorNightLight.json`: the moon hemisphere
  through the windows and a constant fill floor of 0.06 irradiance
  (decision 0123 rule 2).

A cell's additions are designed by the builder of the place that claims it,
from the interior kits' mined lights.
