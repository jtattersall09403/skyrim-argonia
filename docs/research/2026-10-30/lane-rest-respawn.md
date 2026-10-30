# Lane: rest respawn runtime (1.5, owner 2026-10-30)

Brief: the runtime half of the respawn ruling ([respawn-rulings](respawn-rulings.md)). Build VM only.

## What changed

1. **Clearable places never reset.** `combat_records.home_clearable` (from `place_build_hostility.clearable` of the
   actor's home place) adds `"flags": ["NeverResets"]` to the archetype's ECZN; `tools/ArgoniaGen/CombatRecords.cs`
   `Zone` parses `flags` into `EncounterZone.Flag` (Mutagen 0.54.4 has `NeverResets`). L1:
   `test_respawn.py::test_clearable_home_zone_never_resets` (the deserter's zone has no flag; the same archetype
   with its home made clearable gets `NeverResets`). Today the only archetype (the deserter) is not clearable, and
   no placed ref yet carries an `encounterZone`, so the flag is the second guard the rulings name, not the
   mechanism: every clearable place's actor is `never` (check `respawn-clearable`).
2. **Rest respawns the respawnable.** The rule lives in `skse/core` (`respawn::to_reset`: `onRest` in, `never`
   out; L2 in `test_respawn.cpp` and `test_life.cpp` for rest and for the wake). The adapter
   (`skse/ArgoniaCore/src/life.cpp`) only calls the engine:
   - roster = every persistent placed actor whose base has the NPC_ `Respawn` flag
     (`ACTOR_BASE_DATA::Flag::kRespawn`), the compiled `onRest`. It replaces the `hook.respawn-*` keyword lookup,
     which no NPC_ ever carried, so the old roster was always empty (logged now: `respawn: roster of N flagged
     actors`).
   - reset = the engine's per-actor cell-reset step: `Actor::Resurrect(true /*resetInventory*/, true)` for the
     dead, then `MoveToEditorLocation`. CommonLib has no exposed whole-cell reset; a cell reset would also refill
     containers, which the ruling forbids. Containers and `never` actors are never touched.
   - no new co-save state: the flag is in the plugin.
3. **`untilCleared` retired:** row and `until_cleared` column gone from `core_respawn_class` (schema + jsonl),
   `core_tables.py` and `tables_progression.h` regenerated, `ClearedSet` and the location-cleared read removed,
   the `ARG_Respawn_*` keywords no longer generated (`life_records.py`). Their formid rows stay (never reused).
4. **L4 journey** `tests/journeys/rest-respawn.yaml` (scene `claywater-ambush`): camp spot at step 0, kill the
   crocodile by its pool and the deserter by console, rest, then the deserter is alive within 15 m of the ambush
   marker (its positions before and after kept) and the crocodile `GetDead` is 1. `run_journey.py --dry`: ok.

## Gate

`make check`: GREEN in 3 m 39 s (over the 3-min budget; load average high from other lanes, my change adds about 1 s of tests); C++ 33/33 passed; ArgoniaGen `dotnet build` 0 errors; `make plugin` dropped the two `ARG_Respawn_*` keyword YAMLs.

## game-14 must deploy and run

- Deploy: the new `Argonia.esm` (ECZN flags; no `ARG_Respawn_*` keywords) and the ArgoniaCore DLL from
  `skse_build.sh build windows-dev` of this commit.
- Run: `rest-respawn` (new), then re-run `grow-at-rest` and `die-and-recover` (both rest or wake and now reset
  flagged actors with an inventory reset).
- Read in the ArgoniaCore log: `respawn: roster of N flagged actors` with N >= 1 at load; `respawn: K actors reset`
  at the rest.
- Unverified until then: that `Resurrect(true, true)` on a persistent dead actor in a loaded exterior brings it
  back with its base inventory, and that the roster sees our persistent refs at data load.
