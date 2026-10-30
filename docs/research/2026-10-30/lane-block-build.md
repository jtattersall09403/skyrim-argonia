# Lane block-build (0.4 §d, Claywater Station, build-VM side): hand-off at the context mark

## Hand-off: what is done
- **4739988 (this lane):**
  - `world/schema.sql`: a new "built places" block with three tables.
    - `build_cell`: exterior, own or borrowed, with a review column.
    - `build_ref`: piece or base, metres, door_to, owner, npc_id, socket_id, thing_id, host_ref_form_key, disabled, actor.
    - `build_person`: the vanilla template, race, speaker, sandbox radius and respawn.
  - Claywater's rows through db.py: 5 cells, 124 refs, 5 people. Each of the four people also has two `npc_day_block` rows: a sandbox from 06:00 to 21:00 and a sleep from 21:00 to 06:00.
  - `tools/ArgoniaGen/PlacedRefs.cs`: one REFR/ACHR mapping (teleport, owner, lock, disabled, linked, enable parent). Generate.Cell now uses it.
  - `PlaceCells.cs` writes CELL overrides of a master: an ArgoniaWorld.esm exterior or a borrowed interior.
    - It copies the master's CELL record and attaches only our refs. Persistent exterior refs go to the WRLD top cell.
    - It reads ArgoniaWorld.esm from `$ARGONIA_WORLD_ESM`.
  - MISC writer (Items.cs). `tools/argonia_world/place_build.py`: the place layer. It is **not yet registered and not yet run.**
- **Children:**
  - 686d95f: `ArgoniaGen index` reads `Data/argonia-mesh-lists`, which cuts Claywater's unresolved pieces from 12 to 3. Also adds `ArgoniaGen cells` → out/cells-scan.json (931 cells, 1.37 GB peak).
  - 52e3063 and 3020691: the PACK writer on the vanilla Sandbox (01C254) and Sleep (019717) templates, `packages.py`, and the NPC_ keywords/packages/flags/voice/outfit fields. 8 tests pass. That child committed through a temporary index, against the lane rules.
  - cb08931: the fixtures `ARG_ProvingGround` (108 refs, persistent `ARG_PG_*Marker`s) and `ARG_Booth`, plus `tests/scenes/proving-ground.txt` and `duel-ring.txt`. 6 tests pass. The layer is not registered.
- **Interiors decided** (from the cells-scan survey; the reader still judges stills):
  - The station house borrows King of the Murkmire's `893374` "Dareel-Jei's House" (LilmothApothecaryHouse). It has no Nordic model. DawnstarBrinasHouse has 9 Nordic models (the farmhouse interior kit and mounted heads), so it fails the look review.
  - The three huts borrow their old KotM hosts: 0A5A8A, 0C702C and 09B49D.
  - The KotM residents in those cells and the Elder's Hut's second door are disabled. The displayed names are ours. The ledger stands on table 893382, about 1.15 m up.

## What is left, in order
1. Register the layers in `intermediate.build` (tools/argonia_world/intermediate.py:~190), after the regions layers:
   - `place_build.layers(alloc, alloc.world, resolver, regions_api.wrld_record()["formKey"])`;
   - `fixtures.layer(alloc, resolver)`.
2. In pipeline.py, set `ARGONIA_WORLD_ESM=out/ArgoniaWorld.esm` in ENV for `generate`, and build the world before generate when it is missing.
3. Run `make plugin` and fix the first-run reds. Expected ones:
   - PlaceCells needs a `name` override for borrowed cells: the record carries `name`, but `Shell()` does not set it yet (PlaceCells.cs:~75).
   - The ACTI writer's `keywords` and `activateTextOverride` field shapes (ActivatorRecords.cs).
   - `place_build.py:_people` needs an `npc_day_block` attribute `from`. Use `b["from"]`, or check whether the row object supports item access.
   - Unresolved pieces: there are 3 composites, but the rows already replace them with KotM mud-hut pieces and BM&V's farmhouse01. Check with `pieces check` once the gate passes `--places`.
4. Fill the quest aliases. In quest_gen.py:qust, set alias `forcedRef` from `place_build.placed(w)`. In QuestRecords.cs:~57, set `ForcedReference`.
5. Hooks for the ledger read and the well-head and mortar-tub activations: 1.4's ArgoniaCore runtime. Name the ACTI/BOOK FormKeys in the core's thing table.
6. The scour pool (2.5 m or more at the clay cut, 281.5, 3058.5):
   - The ground there is 35.24 m and the channel 33.28→32.68 m (reach.169-1660, depth 1.2 m).
   - It needs a LAND override in the place layer (not written yet) or a hydrology row from the water lane.
7. Navmesh over the placed collision (tools/navmesh's placed-object input), then the L1 checks.
8. Scenes: `tests/scenes/claywater.txt` (`player.moveto ARG_Ref_ClaywaterStationRoadIn`), `quest-board.txt` (`ARG_Ref_ClaywaterStationQuestBoard`), and `claywater-ambush.txt` (`ARG_Ref_ClaywaterStationAmbushPlayer`). Also the draft `tests/journeys/claywater-walk.yaml` and the look-loop stills list.
9. Run `make plugin` twice to show it is deterministic, then plugin-check and `make check`. Then message game-5.

## Planned values to measure at L4
- Pod doorway and door set-out: 2.6 m (author script `POD_FRONT_M`).
- Gaius's second bed: 1.9 m west of the family bed.
- Ledger height.
- Mortar tub mesh (`clutter/bucket01` stands in).
- Raft: Ferries' `plank_ferry_swamp_02` stands in for snt's raft, which is on no machine.
- Templates: TreasCorpse commoners and WERoadCourierImperial, which have FaceGen in the vanilla BSAs. The crocodile templates KotM `EncCrocodileBlackMarsh01` with no Respawn flag, and its den sandbox has a 20 m radius at the cut.
- KotM's worldspace EditorID is also `ArgoniaWorld`, which may cause an EditorID clash with ours on `cow`/`coc`.

## Reds and things not run
- `make plugin`, plugin-check and `make check` have not been run since 4739988. The new code paths are inert until step 1. The `Generate.Cell` refactor should write byte-identical refs, but this is unproved.
- Authoring script (not tracked): ~/.argonia/author_claywater.py. It regenerates the rows from the old layout and ~/.argonia/claywater-hosts.json, an extract of out/cells-scan.json.

## Continuation (2026-10-30, the second context)
- **Rename** (84ffd1f). The WRLD EditorID is now `ARG_Province`, because King of the Murkmire's worldspace is also
  `ArgoniaWorld`. ArgoniaWorld.esm keeps its file name.
  - The terrain sample manifest was re-pinned deliberately to `d53e7471…`: two builds identical, and re-measured
    after the pool with no change.
  - Also renamed in the scenes and journeys, navmesh_ck.ps1, 2.W1 and 0031. That commit also carries the owner's
    staged 2.W1 edits.
- **The layers registered; ARGONIA_WORLD_ESM set** (`pipeline.master_world`: out/ArgoniaWorld.esm is built before
  generate). Both are in the shared files that game-6 commits, together with its MUSC and link fixes.
  - First `make plugin`: green, 2:59, 1.12 GB peak.
  - `place:claywater-station`: 2 ACTI, 1 BOOK, 3 MISC, 5 NPC_, 9 PACK, 9 STAT, and 11 CELLs (4 borrowed KotM
    interiors with our names, 7 ArgoniaWorld.esm exteriors) holding all 124 refs. `place:fixtures`: 2 CELLs.
- **First-run reds fixed** (84ffd1f):
  - The borrowed cell's name.
  - The ACTI verb and keywords are now optional.
  - `b.from_`.
  - The Spriggit round trip differed in 8 cell-children group headers: the master's stamp 0x3552/1 was copied by
    DeepCopy. Fixed by zeroing it in PlaceCells.Shell.
- **Aliases.** LF83 has 13 of 14 aliases forced to placed refs. `thing.lf83.landing-walls` is a set of buildings, so
  it has none.
- **Scour pool** (b960b9e). It is a `build_ground` row, a ceiling bowl:
  - Floor 30.3 m (2.5 m below the planned 32.84 m surface), 3 m flat, side rise 0.5, centred 6.5 m north of the cut
    in the channel.
  - `terrain/place_ground.py` applies it in `Sources.heights`, before the water's regrade.
  - The water plan was re-run with `--write-db` (52 s, 0.98 GB). It changed 39 water_regrade rows, all of
    reach.169-1660.
  - game-6 added place_ground's stamp to `_terrain_stamp`.
- **Navmesh** (b960b9e). `tools/navmesh/placed.py` makes the built places' exterior refs into OBND boxes.
  - The masters' meshes are not on the build VM, so these are record bounds, not mesh collision: a doorway is solid.
  - 76 of 101 refs have a box. The other 25 are markers, items and our own STATs, which have no OBND.
  - ArgoniaNav rasterises each box solid (RasterizeBox), with the heightfield's range grown to hold it. Without
    that, a box was clipped to a false top inside itself.
  - checks.py lets a vertex stand on a box top.
  - Claywater block: green, 0 over, 136 islands (120 on the ground only), under-30° coverage 0.969 (0.976 on the
    ground only), 13 s, 230 MB. The NAV sample's hash is unchanged.
- **Scenes and journeys** (1e3f2f2): the scenes `claywater`, `quest-board` and `claywater-ambush`; the journeys
  `claywater-walk` (8 steps) and `claywater-look` (11 vantage stills for the reader). Both journeys load in the
  runner; neither has been run in game yet.
- **1.4's Starting state** now lists the well-head, mortar-tub and ledger hooks as owed.
- **For L4:**
  - Our 10 STATs carry no OBND.
  - The activators have no keyword or verb.
  - The NPC_ EditorIDs come from npc ids (`ARG_Npc_N1`, `ARG_Npc_N13`).
  - The pool's look at the clay cut needs judging.
