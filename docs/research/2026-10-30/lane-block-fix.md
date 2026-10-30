# Lane block-fix (2026-10-30): Claywater's block blockers cleared before the owner's verdict

## Done
1. **The preference rule (the root cause).** `pieces.py` sorted a mesh's base records by load order alone, so a
   later DLC record that reuses a vanilla mesh won. Dragonborn's volcanic-ash walls and woodpile are the case.
   - The order is now data, in `data/pieces-preference.json`:
     - a kit's own mod for its mesh folder (`meshes/argonia/`, `tesak1243/`, `argonianweapons/` → KotM;
       `gv_meshes/` → Argonian Lake House; the two HTBM folders → their plugins);
     - then the Black Marsh mods, then Tropical Skyrim, then vanilla (Skyrim.esm, Update.esm), then other mods;
     - the DLCs and Creation Club come last, unless a kit row names their own `dlc01/` and `dlc02/` folders.
   - Inside a tier the old tie-breaks stand: later load order, then the placed kind, then the lowest FormID.
   - It lives in data/, not world/db: it is a build rule over the dependency manifest's plugins, not a world fact.
     It also keeps clear of `world/schema.sql`, which holds the vegetation lane's uncommitted edits.
   - Test: `test_resolver_never_lets_a_dlc_variant_win_unless_a_kit_names_it`. It covers the ash wall
     (vanilla beats the ash and snow variants), a dlc02 mesh (Dragonborn beats Sailable Ship), a rock (KotM, then
     Tropical, beats Depths of Skyrim) and Tropical before other mods. The old floor test now uses Black Marsh.esm.
2. **The 31 hand overrides, now by rule.** All 31 (30 walls and the woodpile) resolve to the bases 1.7-prep set by
   hand, checked row by row before reverting. They are back to `piece` with their original `why`, and the
   regenerated cell shows no base change for them. The mountain flower keeps its explicit `base` (KotM's redwort):
   it is a swap, not a resolution.
   - The rule moves 23 of the 267 meshes the world uses. Claywater's built cell gains these:
     - barrel02 → KotM `Barrel02StaticMoss` (was Depths of Skyrim);
     - bucket01 → vanilla `Bucket01` (was Sailable Ship, so Argonia.esm drops the Sailable Ship master);
     - the tanning rack → vanilla `CraftingTanningRackMarker` (was a Hearthfire house-part MISC on that mesh).
   - Unbuilt places gain KotM's rocks over Depths of Skyrim's, and vanilla over Dawnguard and Dragonborn variants.
3. **The stable.** `ref.claywater-station.stable` now places HTBM Curse of Cipactli's `CIPHTBMVillageHut3`. That is
   the Argonian village awning hut, an 8.2 m square open shelter. Its base origin sits like rtstables01 (OBND z
   -64 against -63), so the same z holds. Rejected:
   - KotM's Blackwood `stable.nif`: a platform base, 5.9 m below its origin;
   - `MudHutCover01`: 5.6 m, too small for the plot.
4. **The plant names.** These are host-ref overrides in the borrowed cells, positions from the cell scan. No
   Skyrim plant name is shipped and no record is copied:
   - 01AA8B, the hanging Frost Mirriam (family hut) → HTBM's hanging moss B2 (516170) at 0.3, hung from the
     bundle's hook (no Black Marsh hanging-herb flora exists);
   - 01AABD, Hearthfire's Dragon's Tongue planter → KotM's redwort (0608B0) in the same pot, as KotM dresses the
     sibling pot;
   - 01AADD (family hut) and 8933E9 (station-house table), loose Dragon's Tongue → HTBM's bog beacon (70CFBE,
     reviewed keep).
   - One path stays: a random Dragon's Tongue from KotM's common ingredient basket (CONT 01AA59 through vanilla
     LVLI 10C1F8, store hut). It is polish, P2 rolling, recorded in its verdict.
5. **Found and fixed: borrowed cells were never committed.** `.gitignore`'s `*.esp` hid Spriggit's
   `<cell> - <id>_King of the Murkmire.esp/` folders, so all four borrowed cells' overrides were out of `plugin/`.
   I added `!plugin/Argonia/**/*.esp/` beside the existing `.esm/` exception. The four cells are tracked now.

## Measured
- `inventory.py --block claywater`: 1,130 block rows (1,127 keep, 2 restyle, 1 replace) and 0 unreviewed.
  - Open blockers: only the station house (0396A1 restyle and the 029CB0 door replace, both waiting on
    claywater-look's still). The DragonsTongue restyle is P2.
  - The drop from 1,254 rows: the paths removed here, plus game-7's uncommitted quest shelling, which was in the
    tree when the plugin was built.
- `make plugin`: green (Argonia.esm 458,338 bytes). It built ArgoniaWorld.esm with the vegetation inputs (470,508
  refs) and did not run out of memory.
- `make check`: CHECK GREEN, 311 passed. Plugin regenerated twice identical, plugin/ current, Spriggit round trip
  byte-identical.

## The station house: the swap (applied on the planner's ruling)
The candidate is the house King of the Murkmire builds for this very interior. The borrowed cell 893374
(LilmothApothecaryHouse) leads out by door 8933E1 to exterior door 889070. Beside that door stands
`MurkmireHouse01Yellow` (8933E3, `argonia/blackwood/house1.nif`, 9.3 × 6.8 × 10.7 m, 5.9 m of it below the
origin). Its parts are the door `MudHutLDoor02` (093D0D, already the interior's door base), the doorframe
`MudHutDoorway02B` (0CE602) and the platform stairs (157332). The offsets are KotM's, read from its exterior. The
door stays on the old socket, facing 212°. z is the ground at the socket (37.53 m) plus KotM's height over its own
ground (432 u).
- Other candidates of the right size:
  - KotM `MurkmireHouse05` (21.4 × 16.0 × 11.3 m), `MurkmireHouse02` (16.9 × 15.0) and `MurkmireThatchHouse02`
    (17.1 × 12.5);
  - Black Marsh.esm `01cyrodilhouse2` (Cyrodiil farmhouse, 16.3 × 15.8).
  - The farmhouse is 20.1 × 10.1 m. house1 is smaller, so the b1 stone walls enclose a larger yard.
- Applied (planner ruling) through db.py: these rows. b1 and b1-door replace their `piece`/`base`; b1-door keeps its door_to,
  socket and persistent fields:

```
{"id": "ref.claywater-station.b1", "base": "8933E3:King of the Murkmire.esp", "x_m": 316.62, "y_m": 3068.74, "z_m": 36.87, "yaw_deg": 32}
{"id": "ref.claywater-station.b1-door", "base": "093D0D:King of the Murkmire.esp", "x_m": 318.2, "y_m": 3066.4, "z_m": 38.2, "yaw_deg": 212}
{"id": "ref.claywater-station.b1-doorframe", "base": "0CE602:King of the Murkmire.esp", "x_m": 318.62, "y_m": 3066.0, "z_m": 39.3, "yaw_deg": 212}
{"id": "ref.claywater-station.b1-stairs", "base": "157332:King of the Murkmire.esp", "x_m": 319.45, "y_m": 3064.26, "z_m": 37.6, "yaw_deg": 302}
```
  The two new rows take cell_id `cell.claywater-station.exterior` and persistent false. 8933E3, 0CE602 and 157332
  have keep verdicts. 0396A1 and 029CB0 are no longer reached from the block.
- `place_build._arrival`: an exterior door now steps out away from its own building (`<b>-door` → `<b>`, whether a
  piece or a base), else from the nearest piece. The house is now a base row, and the stairs would have been nearest.
  b4 to b6 arrive unchanged (no YAML diff).
- After: `make plugin` twice gives Argonia.esm sha f62ff0624cd06714… both times (458,466 bytes). The block
  inventory has 1,131 rows: 1,130 keep and 1 restyle (Dragon's Tongue, P2), with 0 unreviewed and 0 open blockers.
  `make check` is CHECK GREEN with 312 passed, and plugin-check is green.

## Owed
- claywater-look (game lane): stills of the stable plot (the awning hut), the family hut's rack and pot, and the
  station house (now KotM's Blackwood house) from the road and at its door.
- The quest YAMLs under plugin/Argonia/Quests/ (31 new) and the counts' share from quest shelling belong to
  game-7's uncommitted quarantine change. I did not commit them.
