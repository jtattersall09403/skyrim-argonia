# Lane 1.12-items: item icons, the visible sword, the starting kit (owner look 1)

Brief: `docs/research/2026-11-01/briefs/1.12-items.md`. Rows: the three `lane 1.12-items` rows of
`docs/phases/1-core-loop/checks.md` (owner look 1).

## Root cause (one cause, two symptoms)

The probe (`tests/journeys/batches/probe-items.sh`, argonia-play-ie, 2026-11-01) equipped our `ARG_Weap_SteelSword`
and Skyrim's Iron Sword (0x12EB7) on ArgoniaWalk. `GetEquipped` was 1 for both. The iron sword drew in the hand and in
Wind UI's grid and paper doll. The steel sword had no mesh in the hand and an empty grid cell.

- Wind UI renders each inventory icon from the item's 3D model (windui.md: "icons rendered from each item's 3D
  model"). It has no separate icon source, so an item with no mesh has no icon.
- Our sword's record named `Model: Argonia\weapons\steel-sword.nif`, and no such file exists anywhere.
  `tools/argonia_world/items_records.py` `model_path` turned every item row whose asset was the old project's `.glb`
  (`packages/character-assets/files/...glb`) into `Argonia\<path>.nif`. Its docstring promised that "the installer
  makes the .nif on the player's machine (0014)", but no such installer step exists (no code reads a `.glb` to make a
  mesh). Under 0006 we make no art, so none ever will. This hit 200 of the 511 item rows, among them every weapon and
  armour piece of the sets. The armour ARMA records had the same invented path, the `DefaultRace` alone (the player is
  Argonian) and no first-person model. The weapon had no first-person model either.
- **Why 1.12 called it done:** no check equipped the sword at the play camera and looked at the hand, and no check
  read the grid for an icon. The 1.12 journeys checked `GetEquipped` (state), which is true for an invisible item. The
  L1 tests asserted only that the path ended in `steel-sword.nif`, and never that a file supplied it.

## The fix (the class, not the one sword)

- `items_records.look()`: a row with a vanilla `meshes/` path keeps it. A `.glb` row takes its look from the
  base-game record its `value_from` names (`Skyrim.esm:SteelSword`). An analogue's base record or a premium item's
  own row also works. The result is passed as `template`.
- ArgoniaGen `Items.cs` reads the template from the master as an overlay and looks it up by EditorID. A weapon copies
  its mesh, its first-person model (the 1st-person static), its sounds, its impact set and its block material. Armour
  uses the base record's own ARMA list, so every race fits and first person works, along with its ground model and
  its sounds. Our invented ARMA records are gone. AMMO is new: the arrow's mesh, projectile, damage and flags. A
  Morrowind medium set takes its base records' engine armour type. A stand-in slot (pauldrons, greaves: no base
  piece) shows nothing, rather than another slot's mesh.
- Combat numbers: a weapon whose class has no `weapon_class_combat` row (only longBlade has one) keeps its base
  record's damage. Nothing was guessed or retuned, and the class's motion values are still owed (2.7 §b).
- L1 guard (`test_no_item_record_names_a_mesh_nothing_supplies`): no item record in the committed plugin names an
  `Argonia\` mesh, and every WEAP has a model and a first-person model.

## The kit

`data/quarantine/start.json` `player.kit` holds a steel sword, a steel mace, a scimitar, a hunting bow, 40 steel flight
arrows and the Imperial light set (cuirass, boots, bracers, helmet). The steel helmet was dropped because its horns
read Nordic (proof 1 still). The kit goes into the Player override's items (`RaceRecords.Player`), so a new game from
the main menu carries it in place of the master's items. `base_save.py` still strips the coc's engine test kit, which
the proof 1 still showed being added on top (iron armour, 86 kg). It then gives the kit back by `additem`: argoniabase
and ArgoniaWalk carry exactly the kit (17.6 kg).

## Evidence

Copied to `out/batch/lane-1.12-items/` (main tree). Batch: `tests/journeys/batches/lane-1.12-items.sh`.
- probe/: before the fix. Our steel sword gave an empty hand and a blank grid cell; Skyrim's iron sword drew normally.
- proof3/ (deploy of c721f4d, new game by base_save): `kit-counts.txt` has every kit item at count 1 (arrows 40)
  with no additem, and the carried weight is 17.6 kg. `inventory.png` has 9 of 9 cells drawn. A `reader` passed the
  icons and the kit, and saw no Nordic piece.
- proof4/: each kit weapon readied (`IsWeaponOut` 2) in third person. `IsPC1stPerson` stayed 0 by every route tried
  (pad, keyboard F, the camera wheel; the console has no `cgf`).
- make check: CHECK GREEN (500 passed) on the code commit c721f4d.

Rows: icons proven; kit proven; sword row still owed. Its cause is fixed, and the drawn weapons show in third person.
The row also owes first-person stills, which need a route into first person (a bridge `pov` command in
skse/ArgoniaBridge is outside this lane's paths; or find what holds the camera in third person).

## Left open / for other lanes

- The first-person toggle: `Toggle POV` is unbound on the pad (controlmap.py) and keyboard F did nothing in game
  (`IsPC1stPerson` stayed 0). The proof uses the console's `cgf "Game.ForceFirstPerson"`.
- Pauldrons and greaves of the steel set (Morrowind-only slots) show nothing when worn, because no base piece exists
  for them.
- Weapon classes other than longBlade carry vanilla damage until 2.7 §b measures their motion values.

## Third-person close stills (planner: first person dropped; proof5)
`close()` in the batch sets noon, zooms with the wheel, freezes the camera (tfc) and turns the player. The reader's
verdicts: bow PASS, clear; scimitar weak PASS; mace partly; sword FAIL (the turn took the player out of frame). A
sandstorm weather fogged every frame, and the wheel zoom did not bring the camera close. The row stays owed. Next:
force clear weather (`fw` to a clear WTHR), leave the setangle turn out, and use the bridge `booth`-style free-camera
framing around the player. Pauldrons and greaves show nothing and were never in the kit.
