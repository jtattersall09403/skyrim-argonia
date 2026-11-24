# Our own buildings inside drafted places, and how their doors work

Research for owner calls #93/#94, 2026-11-24. Nothing generated, bought or downloaded. Tags: [M] measured on this machine, [INF] inference, [TRIAL] only a trial in game settles it.
Scratch scripts and tables (doors.json, doors_cls.json, doorrefs.json, coll.json): `/tmp/claude-1000/-home-ubuntu-skyrim-argonia/044f6198-1702-4213-9f22-0f888669a49a/scratchpad/bd/`.

## 0. Live docs, what I confirm, and the one doc to edit

Covered already: `docs/decisions/0041`, `.claude/skills/place-system`, `place-plan`, `place-site`, `place-adapt`, `place-rooms`, `place-streets`, `place-change`, `place-check`, `docs/design/place-studio.md`, `docs/design/consistency.md`, `docs/research/new-art/buildings.md` (A.2b entrances, B.7 authored room navmesh) and `PROPOSAL.md` track G.

- CONFIRMED: buildings.md B.7 "a space with no `copy_of` is already a legal row": `build.py:920` takes `plugin=None` when `copy_of` is absent.
- CONFIRMED: PROPOSAL.md "47% of doors are Nordic-ruin": Helstrom's 17 of 17 house load doors are `01loaddoorArg` = `dungeons\nordic\doors\animated\mediumdoor\ruinsmediumdoorload01.nif` [M].
- SUPERSEDED/ADDED: buildings.md says place drafting "door pairing is records (place-rooms)"; the drafting side is bigger than records: ids, people, stock and paths all key on door and room ids (section 1.3). buildings.md A.2b "cave mouth with the door model hidden inside" is PARTIAL: vanilla cave doors are visible frame models with collision (section 6), not hidden.
- No live doc says how an own building enters a place. Doc to edit: `docs/research/new-art/buildings.md`, a new section "I. Placing our buildings in drafted places" taking sections 1 to 5 of this note, plus one line in PROPOSAL.md track G. Once built, the recipe moves into `place-adapt` and `place-rooms` as a clean recipe.

## 1. What a "building" is in a drafted place today [M]

### 1.1 The rows
From `newworld/places/jal-veesa` (`place.json`, `spaces/*/refs.jsonl`, `people.jsonl`, `paths.jsonl`, `quests.jsonl`) and `tools/places/units.py`:

| Part | Where it lives | Fields that tie it together |
|---|---|---|
| Shell (and deck, posts, steps, rails, hanging lamps) | `spaces/exterior/refs.jsonl`, kind `building`/`static`/`light` | `src` (source ref), `cluster` (b01..), `seat {mode, dz, on}`; Jal-Veesa houses are 14 to 38 refs each (Elders hut 14: body1 deck1 door1 on7 railing4; Egg-Tenders 38) (`units jal-veesa`) |
| Door ref | same file, kind `door` | `door {to_space, to_ref, to_pos, to_rot, arrival [x,y,z]}`, `flags [persistent]`, `seat {on: <shell id>}`; base e.g. `King of the Murkmire.esp:0259D2` ThatchHutDoor01 at scale 1.1 |
| Door's partner | interior `refs.jsonl` row with `src` = source door; its `door.to_pos` = the exterior arrival | `pair_doors` (`build.py:~1040`) |
| Interior | `spaces/<space>/space.json` `{copy_of: "<source_id>/<cell edid>", name, door_from, parent, room}` + `refs.jsonl` holding only our changes | cell copied at build (`build.py:920-1010`); `room` = the source door that picks one room of a shared cell |
| Walking mesh | not in the place files: carried at build from the source (`wholesale.navmesh: "source"`, `carrynav.py`) | outline zones per deleted/moved/added piece |
| Streets | `paths.jsonl` rows | `from` = door id (source id else ours), `to` |
| People | `people.jsonl` | `home` space, `bed {space, ref: <source key>}`, `routine[].at {space, ref}`; the bed ref is a SOURCE key in the copy (`King of the Murkmire.esp:1BCAFB`) |
| Quest spots, promises | `quests.jsonl` (`ref: door.mn02.vosh-leera-house`, `pos`), `promises.jsonl` (`refs`), `states.jsonl` | by ref id |
| Household, stock | database `household.home_space`, `stock_container (place_id, space_id, ref_id)` | by space and ref id |
| Names | `space.json.name` = what the door shows (place-studio.md) | `draft.room_names` |

A unit (`units.py:derive`) is grouped by contact, not by a declared id: a body is a `building`-class piece of at least 300 by 300 with a door within 16 of its box; deck, posts, steps, doors and what hangs on it join it. Id `house.<RoomSpaceId>`.

### 1.2 What already works for "add a building" (case c)
Jal-Veesa's market house is already an added building: `draft.add` row 0 (MurkmireHouse01, KoM `15731E`, `dz -38`) plus row 1 (door `MudHutLDoor02` `093D0D`, `on` the shell, `dz 94.4`, `room {copy_of: "kingofthemurkmire.altenmeerhleellocation/AltenGeneralStore", door, space, arrival}`). `draft add` (`draft/adds.py`) copies the room, pairs the doors, lays a 128-wide spur path from the arrival to the nearest path (`adds.py:spurs`) and seats the shell on its true footprint. So the machinery for our building is the same machinery with our base keys.

Measured wrinkle: in 2 of Jal-Veesa's 4 room-doors `draft.add[].room.arrival` is 5 to 6 km away from the built row's `door.arrival` (door 1: add says y -517288, row says -511038; the row is the one the hands set). The add row's arrival is a stale duplicate once hands have moved it; an agent editing a swap must edit the committed row, not trust the add row.

## 2. The sequences for a swap

Verbs that exist: `look delete <piece|unit>`, `look place <base> x,y[,z] --rot --why`, `look move|turn|sink <unit>`, `look duplicate`, `look steps`, `look land`, `draft.add` rows + `draft add <place>`, `draft.room_names`, `draft wholesale --rooms`, `draft clearance/names/people/primitives/stations`, `look commit [--answers n]`. There is no "swap" or "relabel" verb: "relabel" is a promise verdict and a prose change, never geometry (`grep relabel` finds only `promises.py`).

Common first steps (skill `place-plan`, `place-adapt`): read `place_card`; in `draft.plan.structures` give the source building a `kept` verdict whose `why` says "swapped to our <building id>"; read `units <place> --joints` for what meets the old building (steps, walkway ends).

### (a) Keep the source interior, new shell [narrow; skills place-adapt, place-site]
1. `look delete` ONLY the old body piece (and deck/posts the new shell supplies itself): not the unit, because deleting a unit deletes its doors, rooms and what hangs on it (place-adapt "Prune").
2. `look place <our shell base> x,y --rot <old rot> --why`; seat from our model's own `foot` (`seat.model_bounds`).
3. `look move` the existing door ref (and its arrival) to our recess; its id, `door.to_ref`, space, people, quests, paths all stay valid.
4. `look sink <unit> --until-feet-buried` or mounds (`look land`) for our stilts/skirt; `look steps` from the new porch; `draft clearance`.
5. Check: `units --joints`, `probe --all`, build, `check` (below).
This is the narrowest swap: nothing keyed to the interior changes.

### (b) New interior of ours [narrower than a redraft, wider than (a)]
Do (a) steps 1-5, then the interior:
1. Set the room's `copy_of` to our template (section 4), or write the space with no `copy_of` (legal today, `build.py:920`; every ref then lives in the place's own `refs.jsonl`).
2. Re-point people: beds and work stops name SOURCE keys of the old cell, so each `people.jsonl` bed/routine `at.ref` goes to the template's matching slot (`draft people` re-reads; hand rows are authoritative, `place-change`).
3. Stock containers (`stock_container` rows by `space_id, ref_id`) and quest rows naming old refs are re-keyed (`place-stock`); `draft names` for the room name.
4. If the space id is kept the household row (`household.home_space`) and `draft.room_names` need no change. Keep the space id.
Silent breaks otherwise: a bed key that is not in the new cell makes the `people`/`promises` check fail at the end (place-check), not at the edit.

### (c) Add a building where the source had none [`draft.add`, exists]
Row for the shell (`base`, `pos`, `rot_z`, `dz`, `why`, `need`), row for the door (`on` the shell row's minted id, `dz`, `room {copy_of, door, space, arrival}`); `draft add` makes the room, the pair and the spur. Site it by `look walk <door> <middle>` (place-adapt "An added building").

### (d) Re-kit a whole place (every hut of a Root-Folk village) [not narrow; the one case that is nearly a redraft]
Per house, (a) or (b), as a batch, by `look commit` group by group. It is the same verbs repeated, so it stays a hand adaptation of the committed files, never `draft wholesale` again: a plain re-lay is refused on a place with hand edits (place-site step 3) and a whole redraft needs `--force "<why>"` once (place-change). Decide per place whether the shell is swapped (a) with source interiors kept (cheap, the interiors stay Helstrom's) or (b).

### What must be re-seated [M code, INF effect]
- Footprint and door position differ: seat uses the new base's mesh footprint (`seat.model_bounds`, `footprints.json`); `units` re-measures sill against floor and ground before the door (`SILL_TOL 16`), feet against ground (`GROUND_LEG 96`, `DECK_MARGIN 60`).
- Arrival: must stand on ground or deck, off the shell: `check_doors` (`check.py:735-776`) fails "arrival on no navmesh" and "arrival inside <row>" (uses `stands_inside`: box then collision profile).
- Carried walking mesh: `carrynav.py` lines 6-12: a deleted source piece's outline (grown by 64) and an added piece's outline become generated zones; the carried mesh is cut around them and meshed from what stands there. So old footprint triangles go and the new footprint meshes; the door's triangle must be reached from the carried mesh: put the arrival on the way and read `probe --mesh`.
- Street end: the spur is regenerated for ADDED doors only (`adds.py:spurs`); a carried door that moved keeps its `paths.jsonl` row, whose end may now be inside the new porch: re-route it (place-streets "Walks, patrols and spots").
- Plants: `draft clearance` again.

### What the 17 checks and the draft check say (by code)
- `plugin`: base key must exist in a plugin of the load order or in `ArgoniaOwn.esp` through `plan_own`; an `ArgoniaOwn.esp` key reaching the writer unswapped fails the build (`own_bases.py` docstring).
- `seat`, `overlap` (`check.py:637`): a door standing in its own shell passes only if it rests on it (`rests`) or its origin is outside the middle half of the shell box (`FRAME_RING 0.5`, `door_frame`), so a deep recess in a small shell flags unless the door is `seat.on` the shell.
- `doors`: pairing (`partner leads back`), persistent, arrival on mesh, arrival not inside.
- `streets`, `navmesh`, `people`, `services`: door on a path; patrol/work points on the main mesh.
- `nordic` (`check.py:1295`): our base is judged by name (`catalogue.NORDIC` regex): avoid `nord`, `reach`, `pine`, `snow`, `frost`, `ice`, `skyrim`, `farmhouse`, `riften` etc. in edid and model path, or the building reads Nordic.
- `rooms` (`check_rooms`): compares to the source bundle; for a template with no bundle `copied_room_expected` returns None, so no comparison (not a failure).
- `promises`, `stock`: fail at the end for any dangling key.
- Draft check `plan`: every major source structure needs a verdict row; a swap is `kept` with a why.

### What would refuse or silently break today [M unless marked]
1. Name classification. `classify.py` puts any piece whose edid or model path contains `mound`, `mudpile`, `dirtpile`, `/landscape/` or `root` in class "ground piece" BEFORE the body rule: `argonia/rootfolk/househut01.nif` and `argonia/mound/house01.nif` both classify "ground piece" (run: `classify({'kind':'building',...})`). A ground piece is never a house unit's body (units.py `ground_piece`), so a Root-Folk kit named "root" or "mound" gets no unit, no sink, no joints. Names with hut/house/shack/tent/hall/inn and kind `building` classify "building body"; `dome01` or `buildinga` classify "thing" with the `fallback` flag.
2. Catalogue kind. `catalogue.kind()` makes a STAT `building` only if the model path or edid matches `architecture|house|hut|tower|wall|bridge|dock|pier|walkway|building|shack|stilt|ruin`; else `static`, and a static with a body word classifies "thing". Our STAT records need a model path with `architecture` or `hut/house`, or the catalogue must take an explicit `kind`.
3. Own bases cannot carry a new model today: `Own.cs:34-61` writes statics only as a `copy` of an existing record (clear texture) and activators from `model_from`; no `model` field, no DOOR, no CELL. A building of ours needs `Own.cs` to take a model path and a DOOR kind (small change), or a real plugin of ours listed in `mods/dependencies.json` group newworld (the catalogue then reads it like KoM, `catalogue.plugin_list`).
4. Missing base: `draft_bundle.py:215-246` only LISTS `missing_base` in `stamp.missing_bases`; `draft check` does not fail it, so the studio shows a hole and the failure appears at build.
5. Missing or zero bounds: `check_doors` builds its solids only for refs with `bounds` (`check.py:743`), so a base with no bounds is silently not a solid for arrival tests; `units` and seat use bounds too.
6. Stale footprint: `seat.model_bounds` caches by model path forever (`seat.py:194 if m not in _fp`, written to `out/places/footprints.json`); re-exporting a model while iterating keeps the old bounds. Needs an mtime key.
7. Interior from a template: `resolve_copy` (`build.py:323`) needs the source id in `sources.jsonl` / `sources_mined.jsonl` and the cell in a plugin file `_plugin_path` can find (`build.py:1172`); an own cell has neither. The no-navmesh path is fine: a cell with no navmesh is meshed from its collision (`build.py:1300-1345`).
8. Unit grouping: a shell loses its unit if the door is not within 16 (`TOUCH`) of its box (`units.py` bodies rule): a recess door set 40 deep in a thin box is fine (box includes recess), a door standing off a porch rail is not.
9. LOD: statics over 512 units get object LOD from the full model by a DynDOLOD mesh rule within the block budget; otherwise a derived `_lod_0.nif` (`lodmodels.py`, `docs/design/lod.md` lines 28-36). A new shell needs a row in the LOD plan or a stated size; no tool knows it yet [INF: unplanned models fall to the default rule].
10. Atlas: `atlas_state.py` hashes tables `place`, `place_source`, `source_place`, etc. and `network.json`; place FILES are not in it, so a pure swap does not stale the Atlas; changing `place_source`, a place's `look` or adding a library as `source_place` rows does.
11. Assets are never committed (0003): our NIFs live in a mod folder the `Resolver` finds (`resolve.py`: MO2 stack, Data, newworld-assets); a studio on a machine without them draws a placeholder (`nifglb.placeholder`).

## 3. Rules that keep a swap inside the method

- Narrow: (a) is a narrow change (delete one piece, place one, move one door). (b) is narrow if the space id and promise rows are kept (it replaces one room's rows). (c) is already `draft.add`. (d) is a batch of (a)/(b) per house, never a re-lay.
- Expressed as agent edits: `ref.remove` + `ref.add` + `ref.move` ops via `look commit`, and edits to `draft.add`, `draft.plan`, `draft.room_names`; nothing in a refs file by hand (place-change: "An edit made straight in a refs file is no hand").
- Hand placement is authoritative; the owner's rows are changed only to answer a note (`--answers`).
- Survives a world rebuild: place rows are keyed by our ids and `formids.json` mints stable form keys (`Ids("ref:<id>")`); own bases follow `plan_own`'s per-place copies (`stat:own:<key>`). The ground is a fixed base. Only `worldparts` findings reach a place.
- Consistency: a swap changes the place's look; where the record says "clay-mound houses" and we build "root-grown huts", the cheap side (record prose) gives way (consistency.md rung 4).

### The same building across places
Each interior is a per-house CELL (`ANP_<space>`, `ids("space:<sid>")`) built from the template's rows; so each house is dressed apart (its own `refs.jsonl` overrides, owner faction, beds), as Helstrom already does: 18 of Helstrom's 27 spaces copy ONE source cell `bmv.helstrom/01ArgonianHouseinside`, with `room` choosing the room and 18 of its 22 households living there [M, `spaces/*/space.json`, `household`]. That is the existing case of one cell, many houses, so a template cell copied per house is the same mechanism with our cell. Per-place copies of our own bases already exist for the sap pool, and the place shard stays self-contained.

Naming: building id `<culture>-<kind>-<n>` in the library (lower case, no `nord/reach/pine/snow/frost/ice/skyrim/root/mound` words in edid or model path); own base keys in `ArgoniaOwn.esp:000Bxx` (the A01-A05 range is used); per-place edid = ours + `_` + place tag (`own_bases.plan_own`); refs keep minted ids `io.mint(place, "add", key, base)` with `id_base` keeping an id when a base is swapped in place (`adds.py:12`).

## 4. What a building of ours ships with to be draftable

Proposed data shape [INF; nothing like it exists]: `newworld/buildings/<id>/building.json` (committed; no art) with the model files in a mod folder.
```
{ "id": "rootfolk-hut-a", "kind": "house", "culture_tags": ["argonian","root-folk"],
  "size_class": "S", "footprint_m": [w, d, h],
  "shell":   { "base": "ArgoniaOwn.esp:000B01", "model": "argonia/buildings/hut01.nif", "bounds": [[..],[..]],
               "collision": "mopp|box", "kind": "building",
               "plan": [[x,y],...],            // footprint outline in the shell's frame, origin convention
               "front_yaw": 0.0,
               "seat": {"mode": "stilts|ground|clear", "skirt": 96, "leg_len": 160},
               "lod": "meshes/lod/..._lod_0.nif" },
  "parts":   [ {"role": "deck|steps|posts|railing", "base": "...", "pos": [..], "rot_z": 0, "on": "shell"} ],
  "door":    { "base": "ArgoniaOwn.esp:000B10", "model_of": "hinged|flap|double|hatch",
               "pos": [x,y,z], "rot_z": 3.14, "recess": {"w":..,"d":..,"h":..}, "sill_z": 0,
               "arrival_out": [x,y], "lock": null, "show_name_from": "interior" },
  "doors_extra": [ {"role": "back|hatch", ...} ],
  "interior": { "template": "own/rootfolk-hut-a.in", "space_id_prefix": "RootHut", "arrival_in": [x,y,z],
                "slots": {"bed.1": "ref id", "hearth": "..", "work": "..", "chest.1": ".."} },
  "swaps":   { "replaces": ["<source cell or base class>"], "door_side": "front|side", "min_footprint_m": [..], "max_footprint_m": [..] } }
```
and `newworld/buildings/<id>/interior/{space.json,refs.jsonl}` in the same row shape as a place space (bases of ours or vanilla furniture; lights with fixtures; an arrival marker; no navmesh needed, the build meshes from collision). The minimum is: shell model with collision and bounds; door record, its position and recess; interior template; plan outline and front side; seat mode with stilts or skirt; LOD model; a row giving kind and culture tags so `place-plan`'s search (`search query`, the descriptor `text`) and a swap table find it. The `slots` give people and stock a stable key across houses, answering section 2(b)'s re-keying.

Tool changes this needs, listed once: (1) `Own.cs` and `own_bases.py` take a model path and DOOR kind; (2) `catalogue.own_rows` gives explicit `kind`; (3) `classify` reads a catalogue tag for "building body" before its word lists (removes the `root`/`mound` trap); (4) `build.plan_spaces` accepts `copy_of: "own/<id>"` from repo rows; (5) `seat.model_bounds` keyed by mtime; (6) `draft_bundle` missing bases fail `draft check`; (7) the studio loads a model not yet in `bases.jsonl` (buildings.md finding 1).

## 5. Where swaps would pay most [M, `newworld/out/world.sqlite`]

Inhabited places of family settlement/camp/work/military: 172 (population 2116). Rank-0 source is a vanilla-built place (Skyrim winners) for 84 of them (population 856, about 40%); BM&V or King of the Murkmire for 34 (631); the other 54 take another mod.
Vanilla-first by culture (places, population): Shadowfen Border/Stormhold 7 (132; includes Markarth), Gideon Frontier 4 (132; Riften, Ivarstead, Dragon Bridge, Morthal), no culture (camps and mines) 14 (108), Soulrest 4 (106; Solitude), Warden Marches 7 (64), Root-Folk 12 (55; outposts and towers), Clay-Mound 5 (50; Kynesgrove, Darkwater Crossing, Black Briar Lodge), Lilmoth 8 (47), Stone-Sleepers 1 (40; Windhelm), Mine-Burners 5 (30), Island of Blackrose 3 (21), Chime-Keepers 3 (20), Hutan-Tzel 3 (18), Naka-Desh 3 (15), Sedge-Wardens 2 (10).
Four stone cities (Gideon/Riften pop 90, Soulrest/Solitude 90, Stormhold/Markarth 90, Tsonac/Windhelm 40) = 310 people in the Nordic stone sources: the most Nordic, and the worst place to start (large, multi-storey, stone). `source_place.buildings` counts pieces not houses (Riften 4959, Solitude 9316), so use `interiors` (Riften 34, Solitude 31, Markarth 30, Windhelm 27) for houses.
Best first targets by size and style fit: the vanilla farm villages (Morthal 10 interiors, Dragon Bridge 5, Karthwasten 5, Kynesgrove 2, Darkwater Crossing 2; Argonian timber/thatch kit replaces Nordic farmhouse shells; one animated door base, `FarmhouseLDoor01`, accounts for 154 load placements in vanilla), then camps whose source is an Orc stronghold (Largashbur, Mor Khazgur, Narzulbur; Dushnikh Yal is already the source of tribal-camp-m2-m68).
Helstrom (drafted from BM&V's own place): 18 of 27 spaces are the repeated `01ArgonianHouseinside`; 17 of 18 outer doors are the Nordic-ruin `01loaddoorArg`; house door shells `01arghousedoor` (6) and `01argbighousedoor` (2). A door swap alone (17 refs, section 6) would remove the Nordic doors cheaply without touching interiors. Households with a house exist only for drafted places (43 in the table: Helstrom 22, Jal-Veesa 9, Outpost-m13 7, m6 3, m2 1, m11 1), so for the rest use population as the house count.

## 6. DOORS: how Skyrim does them [M]

DOOR records read from Skyrim.esm 244, Update.esm 11, Dawnguard 30, Dragonborn 28, HearthFires 9 (322 in vanilla files), King of the Murkmire 29, Black Marsh.esm 3, Black Marsh North 1, Valenwood.esp 15, Journey to Baan Malur 43: 413 records, 272 distinct models (resolved from the real BSAs and mods; script `doors.py`).
- Flags (FNAM): minimal use 61, hidden 11, no-open-in-combat-search 6, automatic 3 (AutoLoadDoor01, MinUse01, HiddenMinUse01), sliding 1 (NorLabyrinthianLoadDoor01). Open sound (SNAM) on 203, close (ANAM) on 194, loop 1. Sounds are SNDR records picked per DOOR, e.g. KoM mud-hut doors use `DRSWoodSingleLight02Open/Close`, trapdoors `DRSWoodTrapDoorOpen/Close`, imperial `DRSWoodImperialSingle01Open/CloseSD`.
- Animated or static-looking, by the model (NiControllerManager with NiControllerSequence and text keys Open/Close): 305 animated, 84 static, 11 other animation, 13 with no model. In placements: 5523 placed door refs in the Skyrim-family and BM&V plugins, 2669 of them load doors (XTEL): 1978 animated, 612 static, 53 other, 26 no model. KoM: 24 animated, 5 static. That a hinged load door plays Open before the load and a static one loads at once is known engine behaviour [INF from the data, not re-measured].
- Collision: 268 of 272 DOOR models carry `bhkCollisionObject`, 185 MOPP [M], so a DOOR model is a collidable object like a STAT (the 4 without: markers/effects).
- Sizes (OBND of the 127 models actually used as load doors): upright leaves (height 60-400, n=92): width p10 96, median 158, p90 322; height p10 155, median 201, p90 351. Common house leaves: Farmhouse load door 95 x 176 (with its own `DoorBlack` 36-deep box behind the leaf), Whiterun shack 127 x 177, Riften 128 x 176, Solitude house 112 x 190, KoM `MudHutLDoor02` 96 x 176 (and `MudHutLDoor01` 192 x 315), KoM `ThatchHutDoor01` 109 x 148 static, Ashlander `alhutdoor` static. Giants: HHDoor02 832 x 3626 x 776.
- The real door sits on a separate ref in the shell's recess [M]: Riverwood's 7 house load doors are `FarmhouseLDoor01` refs beside shell STATs (`Farmhouse02/04/05/06`, bounds about 900 x 900 x 1000). Offset in the shell's frame (rotation only, `door z - shell z`): Farmhouse02 doors (0, -218 to -257, 0 to 224), Farmhouse05 (0, -256, 224), Farmhouse06 (128, -258, 224); i.e. centred on the front wall at the front face, at floor or porch height. The shell (`farmhouse02.nif`) holds a 4-triangle panel shape `Farmhouse02:7` (98 wide x 401 high, y -214 to -182, `Farmhouse01.dds`); the leaf model is 96 wide x 176 high with a 36-deep `DoorBlack` box (`farmhousedoor01/ldoor01.nif`). So the leaf and its black box occupy the panel's depth: the player sees the real leaf in front; the painted panel is the shape behind it and at distance [M geometry; which is drawn on top in game is INF; TRIAL: stand at 3 m and at LOD].

## 7. "Door as part of the building model, only that bit activatable": possible forms

Activation is per reference, not per mesh part [INF from the engine: the crosshair picks a ref by raycast; no per-shape activation in any record]. Workable forms:

(a) Door panel exported from the same building model, placed as a DOOR ref in the recess. Visually one building, two records. This is how vanilla and KoM do every house (section 6). Costs nothing the pipeline lacks: base DOOR with our model (or a vanilla/KoM leaf), `draft.add` row `on` the shell. RECOMMENDED for every normal house, hall and shop.

(b) The whole building as a DOOR record. Vanilla precedents with large or non-door models [M]: `BoatTravel01/02/03` (Baan Malur: a rowboat 194 x 675 x 153, a longboat 838 x 2184 x 1061, a mast rowboat; static class, MOPP, 176 KB), `ImpWellDoor` (a whole well 322 x 322 x 328, load door), `NMCoffin01`, `HHDoor02` (a 3626-wide gate facade), display cases, a book, a trapdoor ladder. Costs: the whole model highlights and "Enter" shows anywhere on it, the entry position is its origin; collision is the DOOR's own (no static difference: MOPP present for 185 of 272) so walking against walls works [INF]; pathing may treat it as a door [TRIAL]; but the place tools see kind `door`, not `building`: no body, no unit, no seat/footprint rules, nothing sinks it (classify.py `k == "door"` returns "door"), so it needs tool changes. Not recommended for houses. Fits: tents and lean-tos, boats, cave-mouth rock, a one-room shrine, a hide shelter.

(c) Invisible or minimal activator over a painted door. Vanilla: `AutoLoadDoor01` (and MinUse, HiddenMinUse) use `autoloadmarker01.nif`, an editor-marker box 1200 x 1200 x 256 with no collision; its flag is AUTOMATIC (walk in and it loads), 228 loads in Skyrim.esm, 36 in Dawnguard, 21 in Dragonborn, 16 in KoM, 19 in BM&V north, 19 in Valenwood. That is a walk-in trigger, not an "activate" prompt, and its size is a room. Activatable invisible ones: `SDoorManholeCoverInvisible` (Update.esm; `sewerentrancecollision01.nif`, 63 x 54 x 8, effect shader, animated, not automatic) and `SERuinsDoorLoadPhantom01` (empty model `fxemptyobject.nif`, one use). Use of the manhole one as an invisible plate over a painted door is possible only if the plate can be scaled to a door size [TRIAL: scale limits and highlight]. Not recommended as the normal path.

(d) Held leaves by template (recorded, with sizes), by family:
- KoM mud: `MudHutLDoor01` 192 x 65 x 315 (big double, `argonia\mudhuts\door01.nif`, no MOPP), `MudHutLDoor02` 96 x 29 x 176 (animated; 138 load placements in KoM). Thatch: `ThatchHutDoor01` 109 x 26 x 148, static (`argonia\blackwood\shackdoor.nif`, used in Jal-Veesa).
- BM&V/Baan Malur: `alhutdoor` (Ashlander hut, static), `morrowind\sheogorad\velothi\extdoor`, `dagonfeldoor`, `shackdoor`; Black Marsh.esm `01loaddoorArg` (Nordic ruin medium door), `MineDoor01LoadBare1`, `01CAVELOADMOSS` (cave door 335 x 187 x 313).
- Vanilla hinged: Farmhouse 95 x 176, Whiterun shack 127 x 177, Riften 128 x 176, Solitude 112 x 190, imperial wood single 256 x 303, Orc `orcdoor01` 127 x 181; trapdoors (34 trap/hatch/hole models), `TrapdoorLadder01/02`, `ShipTrapdoor01` (34 loads).
- BM&V's own method to re-skin: DOOR records with alternate textures (MODS): Valenwood.esp 14 of 15, Black Marsh.esm 3 of 3, KoM 2 of 29, Skyrim.esm 1 of 244. A retextured vanilla hinged door keeps its animation and sounds with only a texture of ours.

Recommendation by building kind [INF unless noted]: house, hall, shop, smithy: (a) with a hinged leaf by template (retexture via alternate textures, or our model with the vanilla controller names); hut with a curtain or hide flap: (a) with a static-looking load door (`ThatchHutDoor01`-style: no animation, loads at once, 612 of 2669 vanilla load placements are static); tent, shelter, boat: (b); cave/barrow mouth: (a) with the cave-door frame or (b) with a rock; ladder or hatch: (a) with a trapdoor model in a deck.

What an agent places and checks for (a): the door ref in the recess (`on` the shell, `dz` so the sill meets the floor), facing (the door's front faces the arrival; `align.turn_deg`/`to_rot` face away), the teleport pair (`door.to_space/to_ref`, persistent), arrivals on ground both sides (outside `door.arrival` on mesh and out of the shell; inside, the cell's arrival marker), lock (`lock {level, key, flags}`; the key's keeper is a stock row), ownership (place-routines owner faction), the name (`space.json.name`, which is what the game shows), leaf swing clearance: leaf width hinged at one edge sweeps a quarter circle (about 96 to 130 units): nothing within it on the porch or rail.

## 8. Windows, hatches and other entrances recorded as load doors [M]

No DOOR record in 413 is a window, shutter, curtain, flap or tent (search of edid and model path). Real precedents are: trapdoors in decks (`ShipTrapdoor01` 114 x 10 x 104, 34 loads; `TrapdoorLadder01`, 23), sewer and manhole holes (`impsewerhole01`, `riftenrwhallsewerhole01` 142 x 142 x 37, KoM's `OldImpSewerGrateDoor` `mwimparchsewer01.nif` 143 x 144 x 35), ladder-shaped doors (`RiftenRWRoomLadder01` 84 x 43 x 431, static: Skyrim has no climbable ladder, a ladder is a load door), a cave door (`CaveDoorLoad01`, `ImpWoodDoorCaveLoad01`), a mine secret door, a Dwemer lift, a well, a coffin, a book (`DLC2ApoWarpBookDoor`, 38 loads), a porthole and a ship anchor hole. A "climb through a window" would be a small shuttered DOOR model with a teleport pair: no vanilla precedent, so it is [TRIAL].

## 9. Our own door set per kit [INF, built on the precedents above]

| Kit | Leaf | Why |
|---|---|---|
| Root-Folk / mud and clay | KoM `MudHutLDoor02` (96 x 176) or a retextured copy; 192 x 315 `MudHutLDoor01` for a hall | animated, wood sounds, already in the load order |
| Reed and thatch hut (Sedge-Wardens, Seekhat) | `ThatchHutDoor01`-style static load door (curtain or hide flap), our own flap model | no animation to author; loads at once like 612 vanilla loads |
| Halls and meeting places | a double: KoM `MudHutLDoor01`, `XanmeerLDoor01/02` (321 x 293; 425 x 321), or Valenwood's `casexfreelgdoor01` (260 x 296) | animated doubles with sounds |
| Cellar, storehouse, boat hold | `TrapdoorLadder01`, `ShipTrapdoor01`, `OldImpTrapdoor01/02` (KoM, 100 x 100) | the hatch is a DOOR in a deck |
| Cave or burrow mouth | `CaveDoorLoad01`/`01CAVELOADMOSS` frame (335 x 187 x 313) or a rock frame model with a leaf behind it | visible frame, not hidden |
| A door a player must not read as a door (a curtain) | the static flap with `minimal use` flag | quiet crosshair |

Making a leaf by template swap keeps the open animation and sound only if the NIF keeps the controller sequence and node names of the template (`NiControllerSequence` text keys `Open`, `Close` and its node names, as in `riftendoor01.nif`: `RiftenDoorL/R`); a re-modelled leaf must copy the template's hierarchy [INF; the exact node matching is TRIAL].

The three-view check an agent makes (place-look verbs): (1) eye level straight on at 3 m (`look <place> at <door> --stand x,y`): the leaf fills the recess, sill on the ground, the painted panel not showing around it; (2) oblique from each side (`orbit <building>` or `at <door> --from ne|nw`): recess depth against the leaf's plane, no z-fighting with the shell, swing arc clear; (3) a section at door height (`section <door> --axis`) and `probe <door>`: leaf inside the recess, arrival on ground and off the shell; then `probe --mesh` (door and arrival on the main mesh) and `playwalk --rooms` (the entering view). The last row of checks that cannot be done in the viewer is below.

## 10. What only a trial in game settles

1. A model we author with a hinged `Open` sequence: does the open animation play before the load, and do sounds fire (use a template node set).
2. Which of the painted panel and the leaf is drawn on top at distance and at LOD (the farmhouse panel is the same size as the leaf).
3. Collision: walking against a whole-building DOOR and an NPC pathing around or into it; whether NPC AI tries to open it.
4. Crosshair behaviour on a whole-building DOOR (highlight and "Enter" text on any wall).
5. A scaled `SDoorManholeCoverInvisible` plate over a painted door: highlight size and activation.
6. A window-type load door (a shuttered small door model): no precedent.
7. MOPP collision from our own exporter (buildings.md TRIAL 1) for the shell and for a door model.
8. LOD of a new shell through DynDOLOD (block budget; `docs/design/lod.md`).

## Recommendations (each with its evidence)

1. Name library buildings with a body word (`hut`, `house`, `hall`, `shack`) and none of `root`, `mound`, `nord`, `reach`, `pine`, `snow`, `frost`, `ice`, `skyrim`, `farmhouse` in edid or model path until `classify.py` is fixed: evidence: `classify()` run on `rootfolkhouse`/`mound` names (section 2).
2. Make the first proof the cheapest swap: Helstrom's 17 Nordic `01loaddoorArg` doors to a retextured or KoM leaf, no interior change (case a with a door-only swap): evidence section 5. It tests recess, arrival and sounds before any shell exists.
3. Build tool changes 1, 3, 5 and 6 of section 4 first; they are small (Own.cs 85 lines; classify; seat cache; draft_bundle) and are needed by every building.
4. For interiors, start with rows-based templates (`copy_of: "own/<id>"`) rather than a plugin cell: no plugin ordering, no Mutagen reader for our cell, and the same row shape as place spaces; evidence `build.py:920`, `build.py:1300-1345`.
5. Fix the stale `draft.add[].room.arrival` duplicate (section 1.2) when the swap recipe is written: evidence Jal-Veesa 2 of 4.

Covered: docs (decision 0041, place-* skills, place-studio.md, agent-view, consistency, buildings.md, PROPOSAL.md headings), tools/places (units, classify, own_bases, source, build, carrynav, check, hands, edits, draft/adds, draft_bundle, seat, catalogue), newworld/places/jal-veesa and helstrom, world.sqlite, Skyrim and BM&V plugin DOOR and REFR records, door NIFs, Riverwood bundle. Skipped: place-people/stock/routines/story bodies read by grep only; Skyrim.esm door record usage by cell beyond counts; the studio JS; in-game behaviour.

---

# 11. For places NOT yet drafted: where in the drafting flow our buildings, interiors and props go in

The owner's question (24 Nov, second message): sections 1 to 3 above were about editing places already drafted. This section is about places drafted from now on, whose drafters take a source and lay it whole (`draft wholesale`, decision 0041). Tags: [M] measured/read in code, [INF] inference.

## 11.1 Facts from the code that decide the answer

1. The lay is a pure copy loop [M]: `draft/wholesale.py:55-85` walks the source bundle's exterior refs; each kept ref becomes a row with the SAME `base`, the transform applied, `src` = the source id, and `seat free`. Nothing in the loop looks at the base except to drop actors, water and levelled bases. A base substitution is one line at `wholesale.py:~72` (`"base": r["base"]`), and the ledger (`ledger.jsonl`) already records every ref's fate.
2. Everything keyed downstream keys on the SOURCE ref id, not the base [M]: `carry_rooms` (`wholesale.py:177`), door pairs, `people.jsonl` beds (`King of the Murkmire.esp:1BCAFB`), `paths.jsonl` `from`, `stock_container.ref_id`, quest rows. So a swap that keeps the row and `src` and changes only `base` (and a small pose delta) leaves rooms, pairs, paths, routines, stock and promises valid.
3. Units are derived from the SOURCE pieces at source positions (`units.py` docstring: "Membership comes from contact and support among the SOURCE's pieces at the source's positions, carried to the draft by each row's `src`"), so a base swapped at the lay keeps the house unit, its deck, posts, steps and door membership intact.
4. The carried walking mesh does NOT see a base swap [M]: `draft/srcnav.py:place_carry` (lines 233-290) makes a zone only when a source ref is absent from the place (deleted) or its pos/rot differs by more than 10 units / 0.01 (moved), or a place ref has no `src` (added). It never compares `base`. A row with the same `src`, same pose and a different footprint therefore carries the source's mesh unchanged under and round the new shell: a larger shell sits on carried triangles, a smaller one leaves the old footprint un-meshed. This is the one hole in a lay-time swap, fixed by adding "base differs" to that test (zone of old outline plus zone of new outline, no `moved_pairs`): small code, unblocks (B).
5. `fit` (step 3 "Fit it to our ground by hand") works on drafted rows and units AFTER the lay (`units` measures each house's floor, feet and sill against our ground, `place-site` section 4). Seating work is spent on whatever bodies stand at that moment, so swapping bodies before it spends nothing on bodies that will go [M by the order in place-site].
6. A source bundle is a directory of data, not a plugin read at draft time [M]: `src.<id>/` holds `bundle.json`, `bases.jsonl`, `npcs.jsonl`, `spaces/exterior/{refs,navmesh,terrain,...}` and one `spaces/<cell>/` per interior (`ls` of `src.bmv.helstrom`). The place draft reads it with `io.load(f"src.{source_id}")` (`draft/stages.py:88`). The extractor (`extract.py:source_job`, C# Mutagen) is only how the standard ones are made, from a `sources.jsonl` row naming plugins, cells or a location. `draft_bundle.py` already writes `draft.<place>` bundles with the same files (refs, navmesh, terrain, space per room, bases, npcs). So a bundle made from something we authored is plausible: the format exists and a draft bundle is the proof [INF that `Standing` and `check_rooms` accept it unchanged; the `src.<id>` name and `place.json source_id` path are all they look at].
7. Rooms from a source cell come by `copy_of "<source_id>/<cell>"`: `resolve_copy` (`build.py:323`) needs the id in `sources.jsonl`/`sources_mined.jsonl` and a plugin that holds the cell (`_plugin_path`); `check_rooms` reads `bundles/src.<id>/spaces/<cell>/refs.jsonl`. A source with no plugin fails there [M].
8. Own base records exist for the place layer (`own_bases.py`, `Own.cs`): per-place copies under `ArgoniaOwn.esp` keys, swapped at build by `plan_own`, never a model path of ours today [M].
9. The items ladder is decided for our place, not the source: gear and clothing come at step 13 (`place-stock`) [M by skill order]; the draft already drops the source's actors.

## 11.2 Measured: how much sharing a source has

Door-bearing shells in the source's exterior (a load door's nearest big building within 700), by source bundle [M]:
- Helstrom (BM&V): 13 load doors, 5 cells behind them, 3 distinct shells; one shell, `01arghousedoormud`, bears 9 of the 13 doors. One substitution covers 9 houses.
- Seekhat Yol (King of the Murkmire, Jal-Veesa's source): 9 doors, 7 cells, 4 shells; `MurkmirePlatformBase02` bears 6.
- Lilmoth (KoM): 72 doors, 43 cells behind them, 29 shells; the largest groups `MurkmireHouse07Orange` 7, `07Red` 6, `07Beige` 5 (colour variants of one house).
- Riverwood (Skyrim): 7 doors, 6 cells, 6 shells (Farmhouse02 twice): almost no sharing in a hand-built vanilla village.
- Dushnikh Yal (Orc): 2 doors, 1 shell.
So mod-kit sources (BM&V, KoM) repeat bodies heavily and a base-keyed substitution table covers many houses at once (Helstrom 9 to 1); vanilla villages are near one-to-one and need per-structure rows. Interiors: Helstrom's 18 houses share one cell (section 5), so one interior template serves them as well.

## 11.3 The candidate insertion points

### (A) At the source level, before drafting: a re-kitted source of our own
Make once, per source: copy the source bundle, replace bodies and interiors, register the result as an `own.<id>` source that `place-plan` chooses and `draft wholesale` carries whole.
- What it needs: a writer that produces a bundle (refs with our bases, spaces for our interiors, navmesh, terrain, npcs, bases.jsonl) and a `sources.jsonl` row with no plugin (extract skips the C# reader); `resolve_copy`/`check_rooms` for plugin-less sources; `place-plan` search (`sources_match`, `source_place` rows with kind, culture, buildings, interiors) to rank it. The navmesh in it must be re-made under the new footprints [INF: by the build's own Recast from the carried collision, as `tools/navmesh` does for a drafted place; or by `draft_bundle` of a hand-adapted place, which already carries one].
- Saves: every later place on that source starts re-kitted with zero per-place work; `look versus` (hand-over bar item 6) already handles two places on one source; the owner allows shared sources.
- Costs/risks: one more whole-bundle pipeline (a bundle writer, the source pipeline's matching, atlas tables `source_place`/`place_source` change, so the Atlas republishes, `atlas_state.py`); the re-kit is judged once per source and no place's record is in view (promise list rows `show: kept` assume the source's own pieces); a place that needs its quests' rooms from "one other source" mixes kits; the re-kitted place has the "all our buildings the same" look unless variants are in the kit. It duplicates (B)+(D) work into a derived artefact that must be re-made whenever the original source or our kit changes (the bundle's stamp key covers inputs).
- Verdict: the right TARGET for sources the owner sees reused (Helstrom-class sources used by several Root-Folk places), but the most tooling; do it AFTER (B) works, as (B)'s output frozen: i.e. a place drafted with the substitution table, its `draft.<id>` bundle registered as a source (A is "B run once and kept").
- A source authored from our kit alone (a template place) has no layout of its own to carry, which loses the thing 0041 relies on (a layout that already works: walks, streets, patrols, furniture); [INF] low value.

### (B) At the lay (step 3): a substitution table applied by `draft wholesale`
Table keyed by source base (and culture/kind), applied in the lay loop: row keeps `src`, pose and ledger status `placed`, `base` becomes ours, with `replaced_from` kept on the row.
- Like-for-like pieces (props, furniture, lanterns, plants, doors): same footprint class, so seat, mesh and routines are unchanged. Furniture is only safe where the replacement carries the same markers (idle/sit/sleep nodes in the NIF are the model's; a template swap of a bed must keep the node set) [INF]. Doors: leaf swap with a door of the same recess width (section 6 sizes), same base class so `door.to_*` stay valid.
- Building bodies, door-anchored: place our shell so its door position and front equal the source door's, i.e. offset the shell by (source door pose minus our door's local pose), then rows `door`, arrival, street end, spur and carried mesh approach stay where they were [M by facts 2 and 4]. Our shell record in the catalogue carries `door.pos` and `door.rot` (section 4). The source door row is then not moved at all; only the body (and deck/posts if ours has its own) change.
- What each step downstream sees: step 3's fit (`units`, `look sink`, `look land`) is run on our bodies, so seating is done once; routines (step 7) key on the carried interiors' furniture, unchanged if (E) keeps ids; stock (13) unchanged. What the lay must also do: drop source deck/posts/steps that belong to a swapped body (the unit knows them: role body/deck/posts/steps by contact at source positions), or keep them if ours has none.
- Footprint change and the mesh: fact 4's one-line test fix is required; then the carried mesh is cut round old outline and new outline and the build meshes the hole, joined along the carried boundary (`carrynav.py:6-12`). Arrival stays on the carried or regenerated mesh because the door pose is unchanged [M]. A shell much larger than the old one can overrun its neighbours or the street: `overlap` and `streets` checks say so after the lay; the table must state a footprint class ("replaces S, M or L bodies") so it only swaps within about the source footprint (the swap row's `min/max_footprint_m`).
- Saves: no seating spent on bodies that will go; people, paths, stock stay valid; one table row covers every repeat (Helstrom 9 to 1, Lilmoth about 2.5 to 1); the draft is as a place laid whole with our look from the start.
- Costs: the table is a new input to the lay (`draft.kit` in `place.json`, per culture rows), the draft.plan must record it, `look versus` and the ledger report it; wholesale is refused on a hand-edited place, so (B) only runs at the first lay (fine for undrafted places, never for drafted ones, which keep the hand route of sections 2 to 3).
- Verdict: the cleanest place for like-for-like pieces, doors and building bodies.

### (C) At the record level, no place edit: our own copy of a base pointing at our model
`own_bases`/`Own.cs` already make a per-place copy of a base under ArgoniaOwn keys and swap refs at build (`plan_own`): for a vanilla model the world should simply show differently everywhere (a dead Hist, a candle lantern, a Nordic ruin door model used as an Argonian door).
- Needs: `Own.cs` taking a model path (today `copy` only) and DOOR support; the catalogue row (`own_rows`) with our model and bounds so the studio, seat and checks see the real footprint.
- Cost: invisible to the drafter, the studio and the viewer unless the catalogue row replaces the source's base in drafts too (otherwise the draft is judged on the old model and the game shows the new one: a mismatch like the dead Hist, where `own_bases.alt_tex` is the studio's fix); the nordic check and `units` judge the edid/model of what the row says. Good for what is true like-for-like everywhere (a single Nordic door or lantern model to our model of the same size). Bad for bodies (footprints differ, so seating and the mesh were never looked at).
- Verdict: use for small like-for-like pieces only, and have the catalogue make the draft see the replacement, so (C) is (B)'s table in the catalogue (one table, two levels).

### (D) At step 4 (adapt): by hand per structure
The existing `look delete` + `look place` + `draft.add`. Cost per structure: delete, place, seat (the body was seated already by step 3 and is thrown away), move the door, re-route the street end, fix `units --joints`, re-key interiors (section 2). Saves nothing, wastes the step-3 fit on the old bodies. Right for the one-off (a landmark, an owner request, a story building with no source counterpart) and for case (c) additions; wrong as the routine path for repeated bodies.

### (E) Interiors at step 5 (rooms), before step 7 (routines)
Interiors are not a lay concern (the lay carries rooms by `--rooms`); they attach to the door row, so they can swap after the body without touching the exterior. The template must provide, with stable ids, what step 7, 12, 13 key on [M, `place-routines`, `place-people`, `place-stock`]: beds (a `FURN` sleeping base, one per household member; `bed {space, ref}`), work spots and a trader counter, the fire/cook stand, idle and sit markers, containers (`stock_container` rows are by `space_id, ref_id`), lights on fixtures, an arrival marker on the floor, and the room name. Give each a `slot` name (`bed.1`, `hearth`, `work.1`, `chest.1`, `door_out`) and key the template's rows by slot so routine and stock rows written for the source's ids can be mapped to the new ones in one table when `copy_of` is changed to our template; with the same slots the three later steps run unchanged. Where the source cell is a shared multi-room cell (Helstrom's 18 houses, `room` chooses the door), our template is one room per cell and `room` is dropped.
- Saves: interior swap at step 5 (or at the lay by `--rooms` reading a table `source cell -> our template`) never touches the exterior, so the street, mesh and units are untouched; (a) and (b) of section 2 become one table lookup at `--rooms` time.
- Needs: `copy_of "own/<id>"` rows-based (section 4 tool change 4); slot mapping where routines/stock already exist (new drafts have none yet: at `--rooms` time people and stock rows are not yet written for a fresh place, so no re-keying at all [INF from the skill order: people come at step 7, stock at 13]).
- Verdict: interiors go in at `--rooms` (step 3's third command), which is before every person and stock row exists, hence the cheapest moment.

### (F) Props with no source counterpart, and gear
Standards, grave-stakes, sap gear, tribal marks: nothing to substitute, so they are additions by culture rules at step 9 (dressing: `draft stations`, `sap`, `hang`, `primitives`), the existing place-dressing path; their bases come from our catalogue like any other. Gear and clothing are not in the draft at all: step 13 stocks from the items ladder (the source's actors and loose items are dropped or replaced: `levelled`, `actor` drops at `wholesale.py:60-65`), so no source gear ever needs substituting. Costless; nothing to change except catalogue rows and rules by culture.

## 11.4 Recommended flow

| Kind | Where it goes in | How |
|---|---|---|
| Props, furniture (markers kept), lanterns, plants, doors, signs | the lay, step 3 | (B) table: a base-for-base swap with `replaced_from` on the row; the same table can ship at record level for pieces true everywhere (C) |
| Building bodies | the lay, step 3, before the fit | (B) door-anchored substitution by footprint class, source deck/posts dropped if ours has its own |
| Interiors | `--rooms`, step 3's third command (rooms, step 5 for added ones) | (E) `copy_of own/<id>` chosen by the same table row; slots keep routines and stock unchanged |
| Landmarks, story buildings, one-offs, additions | step 4 (D) and `draft.add` | by hand |
| Standards, sap gear, tribal props | step 9 | rules by culture |
| Gear, clothing | step 13 | items ladder |
| A re-kitted source | afterwards, once a kit has proved itself | (A): register a finished place's `draft.<id>` bundle as an `own.<id>` source |

Order inside step 3: choose the source and the fit (step 2/3), `draft wholesale` with `draft.kit` (swaps like-for-like pieces, bodies, doors), `--rooms` (interiors from the same rows), `--walks`, then the hand fit (`units`, `look sink`, mounds), so seating is spent only on bodies that stay.

### What `draft.plan` records (fields)
Today `draft.plan.structures` rows are `{cluster|structure, what, verdict: kept|dropped, why}` (place-plan section 4). Add: `verdict` may also be `replaced` with `by: <building id>` and `interior: kept|ours` (`ours` names the template), and a place-level `kit: <culture kit id>` naming the substitution table in force; `plan.py` and `draft check` must accept the new verdict, and a replaced structure's `why` says the footprint class it was swapped within. `relabelled` stays a prose verdict (no geometry): relabel is a use change and needs no row beyond `kept` with why. The ledger rows get `status: replaced`, `as`, `from_base`.

### Walking mesh, by insertion point
- (B) at the lay: needs the `base`-differs zone in `srcnav.place_carry` (fact 4). Door pose unchanged, so arrival, street end and approach stay valid; only the hole under old/new footprint is re-meshed.
- (C): no mesh change is seen (the model is swapped at build); a footprint different from the catalogue row's is invisible: only for same-footprint pieces.
- (D): zones for deleted and added pieces already exist (`srcnav` rules 2 and the added loop), plus the street end must be redone by hand.
- (E): interiors have their own mesh: a cell with no navmesh is meshed from its collision (`build.py:1300-1345`).
- (A): a re-kitted bundle needs its own mesh made once at registration.

### Promise list and checks
Promises: rows `show: kept` for a body become `kept` with `relabelled`-free evidence (the swapped row's id is the same as the source's, `refs` unchanged); a promise that names a building by its look ("a clay-mound house") is edited in the record prose if our shell reads differently (consistency rung 4). `nordic` check: our bases must not match the Nordic words (section 2); `rooms` check compares copies to the template's bundle, absent for rows-based templates so nothing fails; `doors`, `streets`, `navmesh`, `overlap`, `seat` act on our footprints and say if a swap overran (the fact-4 fix is what keeps `navmesh` green).

## 11.5 Tool changes, in order of need
1. `srcnav.place_carry`: zone when a row's `base` differs from its source's (old outline, new outline, no moved pair). Without it every body swap leaves a wrong mesh. [small; fact 4]
2. A catalogue/own-base path for our models: `Own.cs` model path + DOOR, `own_rows` with bounds and an explicit `kind`, `classify` reading it (removes the `root`/`mound` name trap), `seat.model_bounds` keyed by mtime, `draft_bundle` missing bases fail `draft check` (section 4).
3. `draft wholesale --kit <table>`: the substitution table (props, furniture, doors, bodies by footprint class) in the lay loop at `wholesale.py:~72`, ledger `replaced`, `draft.kit` and `draft.plan` fields, with its test.
4. `copy_of "own/<id>"` from repo rows in `build.plan_spaces`/`draft_bundle`/`check_rooms`, with slot ids; `--rooms` choosing the template from the same table.
5. The studio and `look` loading a model not yet in the catalogue (buildings.md finding 1).
6. (A) last: `bundle` writer and `sources.jsonl` rows without plugins, `sources_match` ranking of own sources, `place_source` rows; Atlas republish.
Inference flags: that `Standing` accepts a bundle not made by the extractor, that routines keyed by slot map cleanly, and that furniture markers survive a template swap are not tested; each is a one-hour probe before building.
