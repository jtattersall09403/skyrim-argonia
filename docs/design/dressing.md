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
   ground point, with at least 8 units of wood above it, no wood within 160 units below it or below four points a
   lantern's half-width round it (leaf cards have no body; a lantern hangs through a low crown), and a lantern's width
   clear of the trunk (its axis and radius measured 1.4 to 2.5 m up, over the root flare). The six thickest, 60 units
   apart, are kept per base in its own frame. Output: `newworld/sources/dressing/hang_points.json`, a committed
   source keyed by base with its mesh's digest; a run measures only new or changed meshes, and `check` lists a placed
   tree base not yet measured. The place tools read the same rules (`tools/places/draft/hang.py`, place-dressing).
2. **The kind.** A kind whose habitat is `hang` (`hanging-hist-lanterns`: King of the Murkmire's rope lanterns
   `DLC2DarkElfLantern05Rope` and `04Rope`, self-lit by their glow shell, with no light reference, as the mod places
   them) hangs only from placed trees. Its numbers are the source mod's own, measured: King of the Murkmire hangs 23
   lanterns in 10 of its 93 cells, all inside its huts and houses, 1 to 5 to a carrying cell (`per_carrier`), so
   its rate is 24.7 per 100 cells (`bound_per100`). A built place hangs its own (place-dressing's hanging lanterns).
3. **Where.** In the kind's region (Murkwood, where the wild world's living Hist trees stand), a cell within two
   cells of a built place, never a held cell, is eligible when it holds a carrier: a tree whose editor id names Hist
   (tree, trunk or gland) or a tree in a Hist grove, with a hang point the longest lantern fits. Of the eligible
   cells, the share the rate gives (`bound_per100` over the mean count per carrier) carries, chosen in a digest
   order; one carrier in each takes a count drawn from `per_carrier`, each lantern on its own hang point.
4. **How it hangs.** The hang point is posed by the tree's rotation, scale and final position (`refs/flora`, after
   the edits); the lantern hangs from it by its rope's top (its mesh's highest vertices), with a free yaw and no
   tilt. It is refused over water or a road, with less than 60 units of air between its bottom and the ground, or
   inside a neighbouring tree's solid core (the inscribed sphere of its bounds); trees standing within 3 m of the
   carrier are parts of the same tree (a Hist is built of trunk, crown and glands) and are not neighbours.
5. **The check.** Each hanging thing's anchor is within 5 cm of its own hang point of a tree that stands after the
   edits; it has the air, ground and road clearance of step 4; a carrier holds at most the source's largest count,
   one carrier a cell; each region's count per 100 eligible cells is within tolerance of the bound.

## Hist sap

Every living Hist of a built place has a still pool of thick amber sap at its roots (Lore:Hatching_Pools), made from
Skyrim's own water machinery and nothing of ours but records and ground (research:
[sap-water-bethesda](../research/sap-water-bethesda.md); records and values: `tools/places/own_bases.py`; the stage:
`tools/places/draft/sap.py`, place-dressing).

- **The water.** `ArgoniaHistSapWater`: Bethesda's Eastmarch hot-spring water (DefaultVolcanicWater, as Tropical
  Skyrim has it), its noise textures, directions and displacement kept; amber colours (shallow 196,128,24, deep
  86,40,6, reflection 150,106,44), opacity 70, fog far plane 56, reflectivity 0.6, fresnel 0.25, reflection magnitude
  0.35, noise at half the hot spring's speed, no current, no damage. Each place that has a pool carries its own copy
  (the place layer's writer, `Own.cs`).
- **The pool.** `ArgoniaHistSapPool`: vanilla's round puddle (WaterPuddleLiteFog's model and bounds) with that water,
  scaled to the tree.
- **The bowl.** The rim is the lowest ground under the pool's outline, the surface 4 units under it, the floor a
  cosine from the rim to 64 units under the surface at the middle, higher ground round it eased down over 128 units.
  The dig only lowers, at most 105 units, and keeps dry land 8 units over our water, so a pool near the water is
  shallower.
- **Never on open water.** A Hist standing in our water has its pool on the nearest dry bank at its foot; with none
  within 600 units of its crown it has no pool, place.json `sap.none` says so, and the place's plan says how it shows
  its sap.

**The in-game check** (the lead posts it as an owner check at the next deploy that carries a rebuilt place; a driver
agent may take the stills). Stand at the rim of Jal-Veesa's Hist pool (the big Hist in the middle of the village) by
day, clear weather: one still at eye height from the rim looking across, one from a few steps back at a low angle,
one from above (a deck). Good: the surface moves slowly (ripples drifting, not still glass, not a running river); the
sky shows as a sheen at the low angle; at the rim the bank shows through the sap; the middle is darker brown-amber
than the rim; no edge of the pool hangs in the air or stops at a step; it reads as liquid in a hollow, not a flat
coloured disc. Then the same at outpost m11-m63, whose Hist stands at the water: its pool is on the bank, never on
the river. If it reads wrong, change only `own_bases.py` and rebuild the places:
- too opaque, a painted disc: lower `Opacity` (70 -> 50) and raise `FogAboveWaterDistanceFarPlane` (56 -> 80);
- too glassy or clear, like water: raise `Opacity` (-> 85), lower `WaterReflectivity` (0.6 -> 0.45);
- too orange or too bright: darken `ShallowColor` toward (170,104,20) and `DeepColor` toward (60,28,4);
- no sheen at a low angle: raise `WaterFresnel` (0.25 -> 0.35) and `WaterReflectionMagnitude` (0.35 -> 0.5);
- moving like water rather than sap: halve the three `NoiseLayer*WindSpeed` again.
