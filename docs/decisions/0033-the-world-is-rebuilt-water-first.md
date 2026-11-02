# 0033 — The world is rebuilt water-first, by rule, from the lore, once

**Date:** 2026-11-01 · **Status:** accepted (owner rulings in the 1.15 planning conversation; supersedes the
methods of 2.W1 and 2.W2, amends 0028's palette; the evidence is
[world-rebuild-options.md](../research/2026-11-01/world-rebuild-options.md))

## Decision

1. **One water level per cell, the vanilla way.** Every body in the hydrology graph is classified to one height
   per cell (the sea at 0; sea-level inland marsh as its own water type, brackish or blackwater, at 0; lakes,
   lagoons and tarns at their level; rivers flat inside a cell, dropping only at cell edges). A step is joined
   as Skyrim.esm joins its own 80 steps: banks above the upper water, the bed through the shared edge about 100–300
   units under the upper surface, sloping inside the lower cell to below the lower water over one to five
   vertices, a rapids or falls chain on the slope with mist at the foot and rocks on the banks. Where a reach is
   too steep for one step per cell edge, it is a dressed dry gully, as vanilla's mountain streams are. No placed
   water planes. Tides and floods are out; a quest flood is placed planes on an enable parent.
2. **The ground is generated from the prior and the water, by rule, from the lore.** The Tamriel Argonia
   heightmap is the coarse prior, low-passed and de-terraced; the relief profile comes from the dossiers (border
   ranges north and north-west, Blackwood uplands west, Shadowfen's mountain flank and ravines, a low interior, a
   drowned coast), its heights held to the engine's ground-mesh limit with cliffs as placed cliff meshes; the
   water solve constrains the ground (beds, banks, steps, shores); each dungeon record's entrance site is reserved
   and shaped from its landform request before the freeze; roads keep their corridors.
3. **Materials are written by rule to the artist's output.** Per region, a short gradient of land textures keyed
   to height above local water, slope, wetness and noise, with wide soft blends, vertex colour and grass lists:
   the same layer weights a Creation Kit artist paints. **The look is Black Marsh & Valenwood's, whole** (owner,
   2026-11-01, after seeing its worldspaces in our engine): its landscape pack, its ~700 swamp trees, its plants,
   rocks and props as far as they go; asset gaps are filled from the other Black Marsh mods, then Tropical Skyrim
   (the owner checked BM&V's permissions). This amends 0028's palette, not its method.
4. **Light, weather and mist are authored.** Every colour slot per weather and time of day is authored, never
   derived from one tint by a ladder; the image spaces lose their yellow tint; fog near and far are set per
   weather and hour; regions carry weather lists with one global per season set from the game month; mist regimes
   per region come from the hydrology and eco classes, with Community Shaders' height fog, and placed mist
   meshes only where a test shows weather fog is not enough.
5. **The method is region by region against a written bar.** A mood board the owner picks is the look oracle; a
   fixed panel of vantage stills at the play camera is read by a reader with a checklist and the feel question;
   the generator iterates on sample windows rendered off game before any in-game batch; one in-game batch per
   round. The province is generated whole every time; nothing is proven on a smaller worldspace.
6. **Built once, then frozen.** The generated worldspace is frozen in a content-addressed manifest. Place
   seating and later fixes are patches in a patch plugin overriding the cells they touch; the worldspace is
   never regenerated. Claywater and the slice places are re-seated natively on the new ground.
7. **What goes and what stays.** The water planner, the regrade and the land-cover raster as a paint source
   are retired. The hydrology tables, the region records, the vegetation placer (with its rocks sunk and the
   conform sign proved), the navmesh job, the LOD jobs, the ESM writer and the terrain checks stay.

## Why

- The owner's play found the world broken in every class at once (texture swathes and hard edges, hollow rocks,
  hovering and gapped water, black water, a cheerful beach instead of Black Marsh, yellow-green fog). Each was
  traced to a structural cause, not a tuning error: 20,165 placed planes that cannot join; a carved alpine
  sculpt (674 cells over the slope limit) painted one texture per class; a weather ladder.
- Both Opus reviewers and the web research converged on the same shape; no community recipe for a generated
  worldspace exists, so the oracle has to be the running game at a fixed panel.
- The owner ruled: option B with its costs, method D, whole province at once, built once then frozen, BM&V the
  primary look, canon relief, lore grounding (0032), the look as good as Skyrim's own.

## Consequences

- 1.15 is rewritten as the world rebuild and runs before 1.14. 2.W1–2.W4 are superseded; their proven rows stand
  as history, their owed rows are dropped under this record. 2.W5 and 2.W6 build on the frozen world.
- Region sound tables with hydrology-derived emitters go to 2.16; season-driven insects and disease to 2.14;
  infrastructure decay states to the built-places part; dungeon supply and entrance proofs to 2.W5 and 4.4.

## Amendment (2026-11-02): the levels come from the ground

Nine generator sessions of per-cell clamps (bank floors, edge banks, pads) left plates and cell-line shores on every
panel still; a clamp census measured 4–22 % of dry vertices sitting on a bound. Skyrim.esm's lakes sit a median
+3 m above their basin's outlet bed and their shores simply climb (probes `vanilla_lake_sill.py`,
`vanilla_shore_profile.py`). So decision 1 is amended in its order, not its rules: (1) the ground is generated
continuous first (prior, relief, erosion); (2) each body's level is set from that ground: a lake, lagoon, tarn or
pond at its basin's outlet sill, a river by its thalweg quantised at cell edges (at most 65.7 m per edge, the
tallest vanilla step; else a dry gully), one level per cell, neighbouring cells merged into one level as vanilla
does; (3) the ground is adjusted only by smooth carve and lift fields; the per-cell clamps, pads and edge banks
are retired. The hydrology graph still says what water exists and of what kind; the ground says where it stands.
(Lane report docs/research/2026-11-01/lane-1.15-ground.md, sessions 10–11.)
