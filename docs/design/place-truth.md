# Place truth: what every measured number means

Every number and verdict a drafter is shown about a place: what it means, the one place it is computed, what holds
it true, its tolerance and its limits. Two checks hold the tools true:

- **Golden place**: `tools/tests/fixtures/truth_place.json`, each piece with its expected class, fault, lowest point
  and unit role, each land point with its expected height; asserted by `tools/tests/test_places_truth.py` (57
  assertions, about a second); the golden meshes (`fixtures/truth_meshes.json`, written by
  `truth_meshes_make.py`: boxes and rings, no game asset) by `tools/tests/test_places_shape.py`, run by the gate whenever a measuring module changes (`tooling/gate_map.toml`).
- **Agreement on the real drafts**: `python -m tools.places truth <place> [--sample N] [--tier ...]`, no build, no
  browser, no lock. Tiers: `ground`, `pieces`, `kinds`, `fresh`. Exit 1 on any disagreement.

## Ground

| Number | Meaning | Computed | Held by | Tolerance | Limits |
|---|---|---|---|---|---|
| ground height at (x, y) | the game's land triangle under the point (the quad split along its diagonal), over the place's ground bundle with every land row applied | `seat.Ground.height` (used by units, the look scene, draft check, ground, sap, fit) | golden `land_expect`; `truth --tier ground` against an independent global-vertex reference at a grid and at every land vertex | 1 unit | none known |
| land row dz | a vertex's change from the ground as loaded. One vertex is one global vertex: a dz on a cell's edge moves every cell's copy. A cell's rows add (the studio writes a patch against their sum); two cells' copies of one edge vertex must give the same dz, else the build refuses it | `seat.Ground.apply_patches`, the build's `plan_land`, `web/js/edits.js` | golden (a cell's two rows adding at one vertex, two cells' copies that disagree listed as a clash, an edge vertex read alike from both cells) | exact | the studio page (`web/js/edits.js`) still reads an edge vertex from the cell whose row names it: `truth` lists every edge vertex named in one cell's row only, so the row can carry both copies |
| built height | the height the place layer's LAND override stores | `build.plan_land` (VHGT: 8-unit steps) | `truth --tier ground` against the reference, when the shard is newer than the place files | 4 units | a dz that is not a multiple of 8 is rounded by the game's format; the drafts hold many such (jal-veesa 42 of 107) |
| water at (x, y) | the cell's water height, else the space's default | `seat.Ground.water` | golden (the boat afloat) | exact | none |

## The rule: meshes, never boxes

Tools reason about pieces by their meshes: every height, foot, end, surface, overlap and verdict is read from the
model's triangles in the piece's pose, through `tools/places/shape.py`. A box is only ever a first reject (two pieces
whose boxes do not meet are not compared further). A model that cannot be read is listed by name (`shape.unread()`,
`python -m tools.places.shape <place>`) and measured by its box, said so on its probe row (`"mesh": false`).

The shape of a model (`shape.Model`): a cloud of points laid at most 8 units apart over every triangle with each
face's normal, kept on disk thinned to one point per 6-unit cube, and the model-frame columns (lowest, highest,
highest and lowest walked height per 8-unit square) read from the full cloud; cached by the converted model's content
key in `out/places/shapes/v<version>/` (106 MB for the six drafted places; about 0.17 s a model to build: 75 s for
their 438 models, about 55 minutes for the catalogue's 19,385). In a pose (`shape.Posed`): a 16-unit world grid of
the underside, top and walked surfaces, its feet (local minima of the underside), a span's end lines, a body's floor,
footprint and eaves, a plant's root collar, lean and crown, a hanging thing's hang point.

| Number | Meaning | Computed | Held by | Tolerance | Limits |
|---|---|---|---|---|---|
| feet | where the mesh comes lowest: connected local minima of its underside, each with its middle and height | `shape.Posed.feet` (`look probe`, `units` feet) | golden (L-deck's 3 inset posts, legged house's 4) | 2 (golden), 8 (real) | |
| eaves, floor | a body's roof cells (underside in its top 40%) outside its walls: their lowest underside; the most common lowest walked height over its wall cells | `shape.Posed.body` | golden (legged house: eaves 250, floor 10) | 2 | a roof whose overhang is under 60% of the body's height reads as wall |
| root collar, lean | going up from a plant's lowest point, where its section stops shrinking; the slope of the trunk's slice middles | `shape.Posed.tree` | golden (leaning tree: collar 0 above roots at -40, lean 11.3 degrees) | 8, 1.5 degrees | |
| overlap | two meshes share a 16-unit cell where both their height spans cross | `shape.overlap` | golden (egg beside and under a cliff's overhang: none; inside it: yes; root under a deck between its posts: none; house in a house: yes) | 16 in plan | |
| joints | every walked span's end lines (foot and head, or two ends) against what they meet. An end line is the DECK's: the one walked surface running the span's length, followed slice by slice from its middle (rails, rope tops, post caps and end frames above or beyond the planks are not it); its axis the walk's long axis, or its climb for a flight wider than long; its height the deck's median within a cell of the end edge (the last plank). Against it, another mesh's walked surface past or under the end (`along`, `dz`), else the ground: meets, rests on ground, on its own legs (its own lowest point within 64 of the end on the ground, on another mesh's surface, or set into one all round: a post on a rock), buried end, short of, step to, mid-air. Then per span and piece of another unit: spans overlap; crossed by wall (a wall or body cutting across the walked line, under 64 clear, open walk on both sides); runs into wall (one not resting on it blocking the walk at one end); floor of (a body resting on it, its floor within a step of the deck, over half of the walk or not cutting across it: not a fault); stands on (a piece resting on the walk leaving under 64 clear beside it) or carries (leaving 64 or more: not a fault), each naming what stands there, its share of the walk's width and the clear left | `shape.Posed.ends`, `shape.legs_held`, `shape.cover`, `shape.joints` via `units <place> --joints` | golden (stair resting, stair 40 in the air, bridge meeting one deck and 30 short of the other, a house on a boardwalk; a rope bridge sagging 60 with rails, posts and end frames meeting both platforms within 4; a deck on 600 legs on a rock, and 100 short of it; a hut on three deck pieces; a wall across a boardwalk; a stair foot leaving 100 clear and one blocking the walk) | 2 (golden), 10 (real) | |

## Pieces

| Number | Meaning | Computed | Held by | Tolerance | Limits |
|---|---|---|---|---|---|
| piece box | the mesh's extent in its pose (the plan from the model's hull, exact under any yaw; else the record bounds) | `look.geom.aabb`, `shape.Posed.lo/hi` | golden (upside-down mound, tilted plank); `truth --tier pieces` | 2 units | a first reject only: no verdict is read from it |
| record box | the base record's OBND, scaled, unturned: what the build's overlap check tests | `draft.overlap.box`, the C# builder | build overlap check | exact | deliberately the record's bounds, not the mesh's: named "record box", never "box" |
| pose | position, rotation, scale | the place file; seated z by `seat.seat_all` | `truth --tier pieces`: file, scene (seated) and the built plan (`shards/<place>/plan.json`) | 1 unit, 0.001 rad | |
| lowest_over_ground | the least, over the mesh's own footprint cells, of its underside less the ground under that cell (negative: in the ground) | `shape.Posed.clearance` via `look.geom.probe_piece` | golden (house 220, post -15, mound 0, plank 200; the L-deck's inset post over a slope) | 1 unit (golden), 8 (real models) | |
| held_by | what the piece's underside rests on: in a cell where its underside comes within 48 of its lowest point, another mesh's top within 24 under to 160 over it, or a walked surface (a floor, a deck) within 24 under to a step over it; highest first; never a tree; the box only picks the candidates | `shape.rests_on` via `look.geom.probe_piece`, `grounding` | golden (deck on inset posts, house on a boardwalk) | exact | |
| floats | no chain of resting reaches the ground (24 units); a hanging thing hangs from a box around its top, a wall-fixed thing (lantern, sconce, window, sign, door) from a box it touches; a boat floats when its hull's bottom is within 160 under the water | `look.geom.grounding` / `faults` over `shape.rests_on`, shared by `look probe` and `draft check` | golden (lantern in the air, plank 200 up, boat afloat, deck on posts, wall lantern) | 24 units | effects, markers, critters, clouds and lights hold nothing up |
| buried | a plant when more than 60% of its height is under the lowest ground under it AND more than half of it, cell by cell over its plan, is under the ground there (a stem reaching down under fronds in the air is not buried); a door, window or floor when more than half; anything else when its mesh's top is 64 under | `look.geom.is_buried`, `shape.Posed.sunk_share` | golden (fern 10% and 80%, a piece 20,000 under) | exact | indoors the floor is the room's walkable mesh |
| unsupported end | a walked span's end line (its deck's extreme along its axis, at the last plank's median height: as joints) whose deck underside is more than 48 over the ground (or water) and whose own legs within 64 do not reach it, with no mesh surface within 48 of its walk height a cell and a half round it | `shape.Posed.ends`, `look.geom.end_report` | golden (plank; stair resting and 40 in the air) | 48 units | |

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

## Limits that remain

- Real models' numbers are exact to 8 units in height along a face, 6 in plan for an untilted piece, 10 for numbers
  read from the thinned cloud (a tilted piece, end lines, a collar); the golden meshes are exact to 2.
- The collision mesh is not read: the converted model is the visible mesh. A walked surface is any face within 32
  degrees of level, so a roof's flat top or a table's top counts as walkable.
- Still from the box, to move to `shape.py` next: `units` deck tops (the collision deck rectangle, else the box top),
  its floor, sills and body-through-deck gap; the seat (`seat.py`), the draft's overlap (`draft/overlap.py`, the
  record box the build tests), the rule stages' placing (`clear.py`, `hang.py`, `adds.py`, `sap.py`; the stages kept only for drafts awaiting
  redraft, `fit.py`, `seating.py`, `walk.py`, `bridges.py`, stay on boxes until they go: place-studio.md), a hanging or wall-fixed
  thing's holder (`Boxes.around`, `Boxes.touching`), and the look tool's hands, camera and capture occlusion.
