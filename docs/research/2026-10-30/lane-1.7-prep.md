# Lane 1.7-prep (2026-10-30, about 03:20 to 04:25 UTC): hand-off at the context mark

## Done (committed)
- **dec1c2b: the bridge reads.** `core <Native> [arg]` (core::bridge_call, a whitelist of the ArgoniaCore.psc reads
  plus ViewIntent and SittingIntent, with every setter refused three times) and `papyrus-queue`.
  - Client side: `Bridge.core`, `papyrus_queue` and `save_bytes`. `Bridge.call` no longer str.formats its line.
  - Tests: ctest 30/30, test_bridge 14 passed.
  - MSVC windows-dev, 0 warnings. ArgoniaBridge.dll is 844,800 bytes and ArgoniaCore.dll 1,481,216 bytes, both in
    C:\argonia\skse\out\windows-dev. game-6 has the paths and deploys them.
- **853e9a8: the journeys.** `tests/journeys/first-place.yaml` (34 steps, in 1.7's order), `tests/scenes/first-place.txt`
  and `tests/journeys/soak.yaml`.
  - run_journey gains `--dry`, kept values (`keep` and `{kept: x}`, `{x.i}` in actions), `soak()` and `judge_soak()`.
  - 13 L2 tests. `--dry` validates both files.
- **This commit: immersion.**
  - `inventory.py --block claywater` and a bounded block walk in InventoryDump (`block` and `block_via`), with a
    fixture test.
  - 1,254 block rows, all with a verdict: 1,246 keep, 6 restyle, 2 replace, 0 unreviewed.
  - The whole-profile reach is 107,012 rows (world 101,659), because the transitive walk over-reaches. The block
    walk is the honest count.
  - Run: 1:00, 1.23 GB peak, under MemoryMax=3G.
- **Fixed in data (build_ref, 32 rows, through db.py; plugin/ regenerated):**
  - 30 dry-stone walls and the large woodpile now use the vanilla base. The resolver had picked Dragonborn's
    volcanic-ash texture swap (pieces.py takes the last plugin by mesh).
  - The purple mountain flower is now KotM's ArgoniaRedwort01.
- **The packet draft:** `verdict-packet-draft.md`. It is complete except for the latency and the Parts 2-4 number.

## Blockers and open items
1. **Blocker:** ref `stable` (Riften's rtstables01). Replace it with a KotM or HTBM piece, or disable it. A still decides.
2. **Blocker candidate:** b1, the station house (farmhouse01 under Black Marsh.esm's textures), and b1-door
   (FarmhouseLDoor01). claywater-look's stills decide.
3. **Polish, P2:** two Skyrim plant names (Frost Mirriam and Dragon's Tongue) in the borrowed huts. Fix by disabling
   the host refs.
4. **Class:** pieces.py's resolver prefers the last plugin with the mesh, so an alternate-texture variant can win.
   The fix at source is to prefer a record without MODS. Not done (outside this lane).
5. **`make plugin` ran out of memory** building ArgoniaWorld.esm on the 2.W4 lane's uncommitted vegetation inputs
   (1.5 GB heap). Argonia.esm was regenerated against the committed world (sha 037ee922) by the pipeline's own
   functions. Its sha is 5823320a…, and only the 32 refs changed.
6. **Owed at L4 (game-6):**
   - deploy the DLLs, then run first-place twice;
   - tune the face-and-press-E poses and the pile pickup (no runner action faces a ref);
   - the `grown` step checks that the place's fights earn a level, and fails with its reason if they do not;
   - the vanilla generic voice barks through VTYP are the quarantine journey's.
7. **The Parts 2-4 number:** the planner sums Part 1's lane wall times from PROGRESS. Not invented here.
8. **The scene-author skill** does not yet mention `--dry`, `keep` or soak.
