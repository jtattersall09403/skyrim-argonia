# Place truth: what every measured number means

Every number and verdict a drafter is shown about a place: what it means, the one place it is computed, what holds
it true, its tolerance and its limits. Two checks hold the tools true:

- **Golden place**: `tools/tests/fixtures/truth_place.json`, each piece with its expected class, fault, lowest point
  and unit role, each land point with its expected height; asserted by `tools/tests/test_places_truth.py` (57
  assertions, about a second), run by the gate whenever a measuring module changes (`tooling/gate_map.toml`).
- **Agreement on the real drafts**: `python -m tools.places truth <place> [--sample N] [--tier ...]`, no build, no
  browser, no lock. Tiers: `ground`, `pieces`, `kinds`, `fresh`. Exit 1 on any disagreement.

## Ground

| Number | Meaning | Computed | Held by | Tolerance | Limits |
|---|---|---|---|---|---|
| ground height at (x, y) | the game's land triangle under the point (the quad split along its diagonal), over the place's ground bundle with every land row applied | `seat.Ground.height` (used by units, the look scene, draft check, ground, sap, fit) | golden `land_expect`; `truth --tier ground` against an independent global-vertex reference at a grid and at every land vertex | 1 unit | none known |
| land row dz | a vertex's change from the ground as loaded. One vertex is one global vertex: a dz on a cell's edge moves every cell's copy. Two rows naming one vertex must give the same dz; it is applied once | `seat.Ground.apply_patches`, the build's `plan_land` | golden (shared vertex counted once, a clash listed, an edge vertex read alike from both cells) | exact | the studio page (`web/js/edits.js`) still reads an edge vertex from the cell whose row names it: `truth` lists every edge vertex named in one cell's row only, so the row can carry both copies |
| built height | the height the place layer's LAND override stores | `build.plan_land` (VHGT: 8-unit steps) | `truth --tier ground` against the reference, when the shard is newer than the place files | 4 units | a dz that is not a multiple of 8 is rounded by the game's format; the drafts hold many such (jal-veesa 42 of 107) |
| water at (x, y) | the cell's water height, else the space's default | `seat.Ground.water` | golden (the boat afloat) | exact | none |

## Pieces

| Number | Meaning | Computed | Held by | Tolerance | Limits |
|---|---|---|---|---|---|
| piece box | the model's extent (its mesh, else the record bounds) turned by the ref's rotation and scale; world axis-aligned | `look.geom.aabb` over `Scene.bounds_of` / `seat.model_bounds` (one cache, `out/places/footprints.json`) | golden (upside-down mound); `truth --tier pieces`: look box, draft check box and draft geom box, every piece | 2 units | a box, not the mesh: a tree or cliff's box is mostly air (the overlap check knows `BIG_IRREGULAR`) |
| record box | the base record's OBND, scaled, unturned: what the build's overlap check tests | `draft.overlap.box`, the C# builder | build overlap check | exact | deliberately the record's bounds, not the mesh's: named "record box", never "box" |
| pose | position, rotation, scale | the place file; seated z by `seat.seat_all` | `truth --tier pieces`: file, scene (seated) and the built plan (`shards/<place>/plan.json`) | 1 unit, 0.001 rad | |
| lowest_over_ground | the box's lowest point less the highest ground under its 3 x 3 bottom points | `look.geom.probe_piece` | golden (house 220, post -15, mound 0, plank 200) | 1 unit | the box's bottom, not the mesh's lowest vertex |
| held_by | what the piece's underside rests on by the floating rule: a solid box under any part of its plan whose top is within 24 under to 160 over its lowest point, highest top first; never a tree | `look.geom.probe_piece` via `Boxes.under_box` | golden (deck on inset posts) | exact | |
| floats | no chain of resting reaches the ground (24 units); a hanging thing hangs from a box around its top, a wall-fixed thing (lantern, sconce, window, sign, door) from a box it touches; a boat floats when its hull's bottom is within 160 under the water | `look.geom.grounding` / `faults`, shared by `look probe` and `draft check` | golden (lantern in the air, plank 200 up, boat afloat, deck on posts, wall lantern) | 24 units | effects, markers, critters, clouds and lights hold nothing up |
| buried | a plant when more than 60% of it is under the lowest ground under it; a door, window or floor when more than half; anything else when its top is 64 under | `look.geom.is_buried` | golden (fern 10% and 80%, a piece 20,000 under) | exact | indoors the floor is the room's walkable mesh |
| unsupported end | a walked span's end (bottom middle of its long axis) more than 48 over the ground with nothing grounded under it | `look.geom.faults` | golden (plank) | 48 units | |

## Classes

| Number | Meaning | Computed | Held by | Limits |
|---|---|---|---|---|
| a base's class | one of building body, deck, post, steps, door, hanging fixture, light, effect, marker, plant, tree, rock, ground piece, water, boat, furniture, clutter, span, railing, wall part, ruin; `thing` when no rule matched | `tools/places/classify.py` (`classify`, `kind_of`); every word list the tools use lives there | golden (every piece); `truth --tier kinds` lists every contradiction between the classifier, units' roles, the look tool's `solid` and draft geom's `solid`, and every fallback base with its count | words in edid and model path: a new source's naming may need a rule (the fallback list says which) |
| unit role | body, deck, posts, steps, door, hanging, on, railing of a house, walkway, bridge or dock | `units.derive` | golden (house of body, deck, two posts; lights and the mound never a body, deck or post; firewood never a post; the Hist a ground piece) | from boxes and contact at the source's positions |

## Freshness (`truth --tier fresh`)

- A place dir that differs from its commit: units, draft check and truth read the working tree; the studio draws the
  committed files. Said per place.
- A bundle older than the catalogue: a base added since reads as missing until the bundle is rebuilt.
- The built shard older than the place files' last commit: its heights and poses are not compared.
- The compiled builder older than its C# source, or another checkout's.
