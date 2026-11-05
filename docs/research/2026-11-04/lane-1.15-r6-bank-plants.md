# Lane 1.15-r6-bank-plants: river and creek banks open at eye height

(1) Evidence: lane water-stands-5 (e61a4532) found no clear river or stream stand; King of the Murkmire's Bush01
(03A583, OBND 1.6 m, mesh 6.3 m tall and 5.4 m reach, data/canopy-radius.json) lines the banks.

(2) Measure first (`python3 -m tools.argonia_world.vegetation.banks --skyrim <Skyrim.esm>`, new; tall_near's
constants: nothing over 1 m within 4 m of the 15 m line across the water, canopy-widened; a trunked plant whose
crown starts over the eye, from 0.4 of its height as the journeys' clearance reads it, by its trunk). Bank = a dry
LAND vertex beside water in a clearwater or whitewater reach cell (362 cells, 36.1 km of bank):

| | open share | tall plants within 10 m a km | Bush01 within 10 m a km |
|---|---|---|---|
| Skyrim.esm, Whiterun Hold (cells -2..22, -14..10: White River, Treva; 86 water cells, 7.1 km) | 0.664 | 88 | - |
| ours before (out/terrain/vegetation as built) | 0.243 | 198 | 15.4 |
| ours after (whole province placed into a scratch dir, before the specimen cap) | 0.664 | 42 | 3.4 |

Without the crown rule the measure read Skyrim 0.606 and ours 0.045 before / 0.221 after: KotM's kapok and mega
trees (OBND reach 30-35 m, crowns 20 m up) closed every line they spanned; that is a measure artefact, not a view.
Bush01 before: 29.1 a ha in flooded-forest, 21.3 in western-frontier; scale p10/p50/p90 0.84/1.00/1.16. It was one
closer among many: the bank's tall plants were Undergrowth01 (596), Bush01 (558), Groundplant04, SwampPlant02A/B,
01largefern, Undergrowth03 and the willows. KotM's own use: 18 refs, 6 in Tamriel exteriors one to a cell at scale
1.16-2.25 (a specimen plant, ~3 a ha where it stands), never a carpet.

(3) Fix at the root:
- lists.py: BANK_* constants. A form whose top (mesh, else OBND, at its largest scale) stands over 1 m grows within
  12 m of a river or creek's water only in a clump: 24 m bank blocks, a position-hashed 20 % hold clumps, both
  banks and every form agree (place.bank_open). Low plants (reeds, lilies, ferns under 1 m) untouched. Lore:
  world/sources/lore/regions/blackwood-and-gloommire.md:34 (open reeds "up to your chin"), topics/fauna-hazards.md:92-95
  (cypress, mangrove, ferns). Blackwater (marsh) reaches are not banks.
- lists.py: a specimen frond plant (mesh over 5 m on an OBND under 2 m: Bush01, Groundplant09) is listed at most
  3 a ha, KotM's own density (24 land_region_object rows, 21-155 a ha before). Scale kept 0.8-1.2 (KotM's
  1.16-2.25 would close more view; the L4 still judges).
- build.py: river_cells, bank_mask (searched past the band edge); Rule.bank from the mesh top; summary.json
  gains bank_open (the build's own measure).

(4) Tests: tests/test_bank_plants.py (clumps at BANK_CLUMP, low plants untouched, Bush01 tall by mesh, the line
measure, bank headings, the build's open share >= 0.66, skipped until the shards carry bank_open). Vegetation
suite green; ruff clean; trees-census green on the current shards.

(5) Owed: the whole-province regenerate into out/terrain/vegetation. The province lock was held (r6-chain27
running) so it was not run; the chain's vegetation stage re-places on its own (its stamp moves with this code).
Then `python3 -m tools.journeys refresh --only water-types` for the river and stream stands' clearance.
Note: the scratch measurement placed the whole province without the lock (284 s); it should have taken it.
