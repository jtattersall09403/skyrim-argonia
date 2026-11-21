# The province as the story sees it

A digest of the new world's database (Project Tamriel's Black Marsh, built as our own worldspace) for the people who write its story. It is generated, never edited by hand: change the database or the generator and regenerate. The other files in this folder (the numbered lore-system notes) are written by hand and are not part of the digest.

Made 2026-11-21 from database revision `bfa78f4b5986781a` (the first 16 hex digits of a SHA-256 over `newworld/story/data/schema.sql` and every `newworld/story/data/db/*.jsonl`, in name order).

    python3 -m tools.newworld.story_digest [--out story/design/world]

| File | Lines | What it holds |
|---|---|---|
| [province.md](province.md) | 574 | The province in one read: the regions and what borders what, water, the travel network, the peoples, power and law, danger, what it offers, a table of every place, and where the data is silent. |
| [regions/althii-archipelago.md](regions/althii-archipelago.md) | 591 | Althii Archipelago: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/aphon-isle.md](regions/aphon-isle.md) | 153 | Aphon Isle: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/arnesian-jungle.md](regions/arnesian-jungle.md) | 293 | Arnesian Jungle: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/aunike-ridge.md](regions/aunike-ridge.md) | 141 | Aunike Ridge: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/banujha-basin.md](regions/banujha-basin.md) | 406 | Banujha Basin: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/barsaebica.md](regions/barsaebica.md) | 378 | Barsaebica: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/benthic-yobesh.md](regions/benthic-yobesh.md) | 293 | Benthic Yobesh: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/blackwood.md](regions/blackwood.md) | 217 | Blackwood: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/cape-percar.md](regions/cape-percar.md) | 465 | Cape Percar: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/chixathe-mesa.md](regions/chixathe-mesa.md) | 423 | Chixathe Mesa: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/hatandros-bight.md](regions/hatandros-bight.md) | 302 | Hatandros Bight: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/kotherra-mangroves.md](regions/kotherra-mangroves.md) | 262 | Kotherra Mangroves: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/lake-ulaish.md](regions/lake-ulaish.md) | 251 | Lake Ulaish: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/murkwood.md](regions/murkwood.md) | 345 | Murkwood: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/nha-enasa.md](regions/nha-enasa.md) | 303 | Nha Enasa: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/nushara-bayou.md](regions/nushara-bayou.md) | 311 | Nushara Bayou: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/okuwun-rahei.md](regions/okuwun-rahei.md) | 575 | Okuwun Rahei: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/padomaic-ocean.md](regions/padomaic-ocean.md) | 137 | Padomaic Ocean: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/sea-of-mists.md](regions/sea-of-mists.md) | 102 | Sea of Mists: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/skeith-isle.md](regions/skeith-isle.md) | 179 | Skeith Isle: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/topal-bay.md](regions/topal-bay.md) | 99 | Topal Bay: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/tulmek-washes.md](regions/tulmek-washes.md) | 610 | Tulmek Washes: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/ultherus-swamp.md](regions/ultherus-swamp.md) | 141 | Ultherus Swamp: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [regions/valley-of-storms.md](regions/valley-of-storms.md) | 377 | Valley of Storms: its nature, peoples, places in full (what each promises, what it will be built from, whether it is built), what ranges it, and its hooks. |
| [people.md](people.md) | 214 | Everyone the data names, and names the place notes give. |

How it is made: every sentence is either a note quoted as the database holds it or composed from rows; the HTML comment after each paragraph names the rows (`place:<id>`, `place_note:<place>/<aspect>`, `region_note:<region>/<aspect>`, `culture:<id>`, `place_give:<place>/<seq>`, `place_source:<place>/<rank>`, `travel_route:<from>/<to>/<mode>`, and so on). Hooks are each place's hooks note, then every sentence of its other notes (and its region's) that names a tension, shortage, rivalry, mystery or loss. Roads are read from the road graph, place to place through junctions. A place is built when its draft has written newworld/places/<id>/ledger.jsonl.

Counts: 258 places, 24 regions, 18 cultures, 654 hooks, 165 named people.
