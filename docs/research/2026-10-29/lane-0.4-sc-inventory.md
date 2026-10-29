# Lane 0.4 §c: the immersion inventory v1 (decision 0006 §1)

## What was built
- `tools/immersion/inventory.py`: orchestrates, streams rows, merges verdicts, writes the inventory and its counts. It is also the gate part (`--gate`, plus `--bind` / `IMMERSION_BIND=1`).
- `tools/immersion/InventoryDump/` (a .NET 10 + Mutagen 0.54.4 sibling of ArgoniaGen; ArgoniaGen itself is untouched):
  - `dump` builds one streaming pass per plugin into an id-and-edge graph. It uses no link cache and keeps no records. Each record contributes its own links (nested excluded; the winning override's links replace earlier ones), plus these structural edges: cell to its contents and back, cell to its worldspace, topic to its lines, quest to its topics.
  - `archives` gives Mutagen's own BSA listing and the UI translate keys.
  - `fixture` writes two tiny plugins with no game data.
- `tools/immersion/bsa.py`: a header-only SSE BSA lister (reads the name tables, never file data; no Wine).
- `data/immersion/verdicts.jsonl` holds our verdicts keyed by row id; it is committed and empty now. `counts.json` (committed) is the measured record.
- Makefile: one `immersion` part.

## Reachability
- The `world` seeds are our plugin's own new records. Overrides are not seeds: the quarantine's 1,860 quest overrides first seeded 110k rows, and that was wrong.
- The `start-quest` seeds are quests whose winning override is start-game-enabled.
- `engine` covers what the engine shows unplaced: menu SWFs, UI keys, GMST, MUST and LSCR.
- Root lookup order: `--root`, `$ARGONIA_PLUGIN`, `Data/Argonia.esm`, `out/plugin/Argonia.esm`, `out/Argonia.esm`. The run found `out/Argonia.esm` from the §a lane.
- Limits in v1: exterior-cell adjacency is not modelled (each exterior cell is reached on its own), and no condition or story-manager analysis is done.

## Measured (2026-10-29, build VM, vanilla profile)
- Load order: 10 plugins (5 official masters, 4 CC files present, `_ResourcePack.esl`), with `out/Argonia.esm` as root.
- Rows: 189,936 (189,022 records, 53 menus, 861 UI strings, 0 views: `ui/` is absent and handled).
- Reach: world 5, start-quest 0 (the quarantine turns every start-enabled quest off), engine 3,244, unreached 186,687. 3,249 rows are reachable and unreviewed.
- SWF count: 53 menus, equal to the interface BSA's `.swf` listing (53). Two independent readers agree on every archive: `bsa.py` and Mutagen's archive reader, checked on every run.
- Fixture test: every record the block references is reached as `world`; the start quest and its topic as `start-quest`; an unused static is unreached.
- Memory:
  - Full run: 868 MB peak RSS, 40–57 s.
  - Tests: 131 MB peak, 2–4 s, 7 passed.
  - `--gate`: 1.7 s.
- Earlier OOMs: `bsa.py` called `f.read()` on the remainder of each multi-GB archive, and the first dump used Mutagen's LinkCache with ResolveSimpleContext. Both are fixed. The .NET runtime config also sets workstation GC, ConserveMemory=7 and HeapHardLimit=3 GB.
- `make check`: green, 1m17s, `immersion` part included.
- `--bind` exits 1 on the real inventory (3,249 failing rows) and is proved by `test_bind_fails_on_reachable_unreviewed_row` and `test_bind_fails_on_replace_without_passing_check`.

## Where the inventory lives (decision 0003)
- `data/immersion/inventory.jsonl` (50.7 MB) is gitignored. It holds vanilla editor IDs and paths derived from game files, `data/README` forbids anything derived from a game file, and its size is also over the guard's 1 MB limit.
- Rows hold identifiers only: no names, text or file bytes.
- Committed: `counts.json`, `verdicts.jsonl` and `.gitignore`.

## Re-run when the dependency mods land
- `systemd-run --user --scope -p MemoryMax=3G python3 tools/immersion/inventory.py` is a one-command re-run. It picks up every plugin in `$ARGONIA_GAME_ROOT/Data` (`$ARGONIA_PLUGINS_TXT` fixes the order).
- The real-masters run is never in the gate. The gate reads the existing inventory, or `counts.json` where there is none.

## Open
- Mutagen has no row in `data/sourcing-register.json`. It was first used by ArgoniaGen in 0.1, and the register is outside this lane's paths.
- Per-string rows from `.STRINGS` files are not emitted; text surfaces are the record rows (BOOK, MESG, INFO…, GMST `s*`) plus the UI translate keys.
