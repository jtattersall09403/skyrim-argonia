# Regional dressing: ground colour and small signature things

Each region reads as its own place at the player's feet: its own flower colour in the grass, and small things found
there and nowhere next door. Both change records only: no terrain, tree, scatter-placement or LOD rebuild.

## Ground-cover colour

1. **Census.** `python -m tools.newworld.dressing.grass_census` reads every grass (GRAS) the New World load order
   offers (Skyrim, Update, the DLC, Black Marsh, Valenwood, King of the Murkmire, Depths of Skyrim, Tropical
   Skyrim, and Flower Fields SE as an asset-only grass source; last wins), resolves its mesh and textures as the game does (the assets audit's resolver) and measures
   its diffuse texture's opaque pixels: the share of each hue family among saturated pixels, and white. A grass is a
   flower grass when one family passes its floor (yellow, white and orange 5%, since dry grass tips are pale and
   warm; violet, blue, pink and red 1.2%). Output: `newworld/sources/dressing/grass_census.json`, a committed source, rerun when a grass-bearing plugin
   of the load order changes (the check builds it when it is missing).
2. **The colour.** Each land region's colour is its identity sheet's `ground.family`
   (`newworld/sources/identity/regions.json`, grounded in the region's look notes).
3. **The palette.** In `tools/newworld/world/texture.py`, each region's own grass lists (`REGIONS[...]["grass"]`)
   carry its colour's flower grass on every grassy material it names, beside its own leaf grasses; a flower grass is
   listed in one region only. Every other grassy material takes its province's list for the material's role
   (`ROLE`: moss, reeds, forest, dry, beach; `ROLES` per province), so no grass list is shared by every region and
   each role keeps its habit (moss low, reeds tall). Where two neighbours of one province still share too much, one
   of them takes its own list on a role's materials (leaf grasses no neighbour uses). The material table stays under
   255 entries (the paint's one-byte index).
4. **What keeps it Skyrim-like.** Only the lists change: the materials, their blend, the swathe and hard-edge
   rules of the ground paint (walk-5 ground research) and each grass record's own density are untouched.
5. **The check.** `python -m tools.newworld.dressing.ground_colour`: no flower grass in two regions; a region's
   flower grasses are of its sheet's family; a sheet family the load order has a free flower grass for is met;
   neighbouring regions (`newworld/sources/identity/adjacency.json`) never show the same flower colour; the share of
   land grass types two neighbours have in common (shared over union) is at most 0.6. A family no complete land
   grass carries is listed as unmet: the sourcing gap to close with a grass mod, searched as
   [creature-mod-search](../research/creature-mod-search.md) does for creatures.

## Small signature things

1. **The kinds.** `newworld/sources/dressing/kinds.json`: each kind's regions (one or two, never neighbours), its
   bases (`plugin:edid` from the held mods), its dressing habitat, its Skyrim sort and its rate. Each kind cites the
   identity sheet's `signature.thing` it delivers or the lore line it rests on.
2. **Which bases.** A base is in the load order, every mesh and texture resolves, it has no distant LOD, and it is
   small (bounds half-extent at most 160 units) or an effect or spawner (MSTT, ACTI) a player walks through: nothing
   the navmesh must cut round, nothing seen from afar.
3. **How many.** A kind's rate is references per 100 cells where its habitat holds ground, at most Skyrim's own
   outdoor rate for the same sort (`python -m tools.newworld.dressing.measure`, Skyrim.esm's Tamriel cells:
   `newworld/sources/dressing/skyrim_measures.json`); a cell holds at most six. A find, not a carpet.
4. **Where.** By hyperlocal habitat on the ecology stage's cell view: canopy, forest (near placed understorey),
   open, rock, slope (15 to 35 degrees), marsh, reeds (near placed reeds and ferns, or marsh), shore (within 12 m of
   water). Never on a road, in water, in a built place's held cells or a landing's cell.
5. **Ids and bytes.** Each reference's id is the `dressing` idspace row's first id plus the digest of its identity
   (cell, kind, ordinal), probed on a collision; every draw is seeded by cell and kind, so a rerun writes the same
   bytes.
6. **The stage.** `dressing` runs after the navmesh and before `esm`, writes `out/newworld/plugin/dressing/`
   (`cy<+NNN>.jsonl`, `manifest.json`, `check.json`) beside `refs/`, and is read only by `esm` as plain REFR.
   `python -m tools.newworld.dressing.place check` judges the kinds and the placement.

## Hanging things

1. **Hang points.** `python -m tools.newworld.dressing.hang_points run` reads each placed tree base's mesh once
   (`refs/flora/bases.json`, the canopy and understorey classes) and keeps its wood, telling leaf cards from bark by
   texture name (leaves, twigs, fronds, moss, vines) and shader (two-sided or vertex alpha without a bark texture). A
   hang point is the underside of a near-horizontal limb (a wood face pointing down) 2.5 to 7 m above the mesh's
   ground point, with at least 8 units of wood above it, no geometry of the mesh within 160 units below it or below
   four points a lantern's half-width round it, and a lantern's width clear of the trunk. The six thickest, 60 units
   apart, are kept per base in its own frame. Output: `newworld/sources/dressing/hang_points.json`, a committed
   source keyed by base with its mesh's digest; a run measures only new or changed meshes, and `check` lists a placed
   tree base not yet measured.
2. **The kind.** A kind whose habitat is `hang` (`hanging-hist-lanterns`: King of the Murkmire's rope lanterns
   `DLC2DarkElfLantern05Rope` and `04Rope`, self-lit by their glow shell, with no light reference, as the mod places
   them) hangs only from placed trees. Its bound is the source mod's own rate (`bound_per100`: King of the
   Murkmire's lanterns per 100 of its cells), since Skyrim has no outdoor measure for it.
3. **Where.** In the kind's regions, a tree (as the edits stage leaves it in `refs/flora`) is eligible when it stands
   within two cells of a built place, at a road's edge (6 to 40 m from its centre line) or in a Hist grove, and never
   in a held cell. A cell with an eligible tree draws its count by Poisson at the kind's rate, at most two a cell, one a
   tree.
4. **How it hangs.** The hang point is posed by the tree's rotation, scale and final position; the lantern hangs
   from it by its rope's top (its mesh's highest vertices), with a free yaw and no tilt. It is refused over water or a
   road, with less than 60 units of air between its bottom and the ground, or inside a neighbouring tree's solid
   core (the inscribed sphere of its bounds).
5. **The check.** Each hanging thing's anchor is within 5 cm of a hang point of a tree that stands after the edits;
   it has the air, ground and road clearance of step 4; at most two hang in a cell; each region's count per 100
   eligible cells is at most the kind's bound.
