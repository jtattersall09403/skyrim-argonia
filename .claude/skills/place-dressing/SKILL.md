---
name: place-dressing
description: A place's dressing - lights with their fixtures, lights on what we add, rope lanterns hung from the Hist and its trees, each living Hist's sap pool, crafting stations added by their workers, a promised shrine's Hist, and the source's collision boxes and triggers. Use when a light, lantern, sap pool, station or invisible wall is judged, missing or wrong, including a lantern floating in the air.
---

# Lights, lanterns, sap and stations

Step 9 of the place path ([place-system](../place-system/SKILL.md)). Stages: `lights`, `hang`, `sap`, `stations`,
`primitives`. Each runs on the place as it stands (`draft <stage> <place_id>`) and is then looked at; what the
baseline carried from the source (its lights with fixtures, its lanterns, its collision boxes) stays as it came.

## Lights

- A light belongs to its fixture: the nearest lantern, sconce, window or fire within 128 units in the source. It
  stands at its source offset and goes when the fixture goes; `draft check` fails a light more than 16 units off.
- What we add is lit as Skyrim lights it: an added forge carries LightForgeFire01 in its own frame (`draft check`
  fails an unlit added forge); an added smelter or alchemy lab carries none. Added walks and steps are lit at the rate
  the source lit its own, usually none.
- A guard's torch is stock (`place-stock`).

## Hanging lanterns

A place's Hist and the trees within 15 m carry King of the Murkmire's rope lanterns (`DLC2DarkElfLantern05Rope`,
`04Rope`, self-lit), 1 to 5 per tree (`newworld/sources/dressing/kinds.json`), each on a hang point of the tree's
mesh, seated `on` the tree. Run `draft hang <place>` (dry run:
`python3 -m tools.places.draft.hang <place>`) after a tree is moved, turned or swapped. A lantern floating in the
air means its tree moved: `look probe` it, then `draft hang`. `draft check` fails a lantern not on a limb of its
tree. A source's own hanging lanterns come with the baseline.

## Hist sap

Every living Hist has a still pool of its own amber sap at its roots: our `ArgoniaHistSapPool` (vanilla's round
puddle) carrying our water type `ArgoniaHistSapWater` (tools/places/own_bases.py), in a bowl the `sap` stage digs
(`land.jsonl` rows `by` "sap"): the surface a few units under a level rim, the floor falling smoothly to 64 units at
the middle, so the water has depth to shade. Never on open water: a Hist standing in our water has its pool on the
nearest dry bank at its foot, or none (place.json `sap.none`, and the draft's plan says how the place shows its
sap). A pool placed by hand on the trunk is kept, and so is one at the tree's foot whose sap reaches the trunk (where
roots or rocks hide the trunk's own ground, bring the pool out to the side the player comes from). A Hist built of
a crown over trunk bases is one Hist with one pool. Run `sap` after a Hist is added, moved, swapped or dies. `draft
check` fails a living Hist with no pool that `sap.none` does not list. How the pool must read in the game, and which
field to change if it does not: [dressing](../../../docs/design/dressing.md), Hist sap.

A pool the record's look promises that is not a Hist's (black mud, a still pond) is the same puddle outline with the
water type that reads as it (Skyrim's `WaterPuddle`, `PuddleWater`, near black, for black mud), set by hand as an
exterior row seated `stilts` on a flat low spot between roots, clear of streets, houses and the water line.

## Stations and a shrine

- The `stations` stage adds each promised crafting station the source lacks by the person who works it, as Skyrim's
  towns do (the smith's yard as Riverwood's outside the smithy, the alchemy lab with the apothecary, the enchanter
  with the spell trader, the cooking pot at the inn), from bases carrying the station's keyword in the place's style
  (`draft.style_order` for a place of another people). The place's own outdoor station is worked before one added in
  a room. Look at each (`stations.added`); move one with `draft.add` and `draft.roles`.
- A promised shrine blessing is carried by the source's Hist or shrine, a Hist placed by hand, else a young Hist the
  tools add in the town's middle; look at it.

## Collision boxes and triggers

The baseline carries the source's collision boxes; `draft primitives` keeps one that touches a kept piece (a
balcony wall, a doorway plug) and drops one that met only the source's ground or a pruned piece (look with
`--helpers`). A wall for a ledge people would fall from is added with its own reason. A trigger whose script reaches no kept piece is dropped; a trap's trigger
stays with its trap. The build's `primitives` check enforces both.
