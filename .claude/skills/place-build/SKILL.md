---
name: place-build
description: Draft one place of the new world from its source place (any plugin we hold) onto our real ground - fit, seating, vegetation clearance, streets, interiors, people - as the place files the studio and the build read. Use for each place's first draft, and to redraft after the ground or the recipe changes.
---

# Draft a place from its source

The tools do the measuring; you make the calls they cannot. Everything you decide goes in the `draft` block of
`newworld/places/<place_id>/place.json`; the tools write every other place file. The contract (file shapes,
seat rules, ids) is `docs/design/place-studio.md`. Never write mod record or asset content into a place file.

## Inputs

- `place.json`: `place_id`, `source_id`, `similar` (nw-04 fills these). Our record: `db.open("newworld")`, tables
  `place` (position, siting, population, summary) and `place_give` (what the place promises the player).
- The bundles `out/places/bundles/src.<source_id>` and `ground.<place_id>`
  (`python -m tools.places extract ...`). The ground bundle's stamp must match the deployed world file.
- Skyrim's town rules: `docs/research/skyrim/town-life.md`.

## 1. Read the source's character

1. `python -m tools.places draft <place_id>` once with an empty `draft` block, then
   `python -m tools.places draft render <place_id>` and look at `out/places/renders/<place_id>/source.png`.
2. Name in a few lines: where its water is and what stands in it (the landing, stilt houses, shallows); how its
   streets run between the doors; which buildings are entered and where they lead (`place.json` `fit.clusters_info`,
   `ledger.jsonl`); how close its plants come to buildings, streets and doors (`place.json` `clearance`).

## 2. Choose where it sits on our land

1. Look at `draft.png`: our rivers, banks and dry ground round the record's position.
2. The landing goes on our real bank of real water; the town's dry ground on our dry ground; the whole source at
   its true size. If the record's position does not serve, set `draft.anchor` `[x, y]` (game units) to the
   point the source's middle should take, on the ground that does. Set `draft.rot_deg` only when the search
   turns the town against the way it faces its water.

## 3. Draft and read the fit

1. `python -m tools.places draft <place_id>` then `draft render <place_id>`; compare `side-by-side.png`: the same
   cluster ids sit in the same order, facing their street and their water.
2. In `place.json` `fit.clusters`, a cluster with a high `cost_after` sits badly (wrong side of the water, on a
   slope). When moving the anchor or the turn would serve the whole town better, do it and redraft.
3. Read `land.jsonl`: each patch has its reason. A patch is the last resort; when one cluster carries several,
   prefer a better anchor or turn over the patches.

## 4. Settle what the cost cannot

- **Nordic bases** (decision 0006): `ledger.jsonl` lists each dropped one. For each base, find a piece of like
  size and use from a non-Nordic source we deploy (`python -m tools.places search query "<what it is>"`, or the
  catalogue `out/places/catalogue/bases.jsonl`), and set `draft.replace` `{old: new}`, or
  `{old: {base, turn_deg}}` when the new model's front faces another way (compare the bounds' long axis). A door
  that leads indoors is always replaced, never dropped. Drop decorative pieces with no equal.
- **Leftovers**: `draft.drop` `{source ref id: reason}` for anything the source placed that our place must not have.
- **Promises the source lacks**: `place.json` `stations.missing` lists crafting stations the record promises
  with none in the source; add each with `draft.add` `[{base, pos, rot_z, kind, why}]` beside the person who
  works it. A service person's workplace that the default gets wrong: `draft.roles` `{role: {space} | {pos}}`.
- Nothing levelled is ever placed (decision 0035); the tools drop it and list it.

## 5. Check and iterate

1. `python -m tools.places draft check <place_id>` must PASS: every source ref accounted for, seated by its
   rule, buildings on ground no steeper than the source's, water and land as the source had them, every door on
   a path, every promised service given, a bed for everyone.
2. Render again and look: does it read as the same town sitting naturally on our land? If not, go back to 2.
3. `python -m tools.places seat <place_id>` must report 0 refs moved.

## 6. Record

1. Correct the record's radius to what was built: `place.json` `radius_m` into the place's research record
   (`newworld/sources/research/places/*.json`, `footprint_radius_m`), then `python -m tools.newworld.build_db`.
2. Commit `newworld/places/<place_id>/` and the record change by path.
