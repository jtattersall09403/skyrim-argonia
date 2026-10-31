# Lane: respawn until cleared (1.5, owner's correction 2026-10-30)

Brief: enemies in clearable places respawn after death or rest **until the whole place is cleared**, then never.
18f7174 set the 41 to `never` and 4aabb98 retired `untilCleared`; this lane undoes that, native-first. Build VM only.

## What changed

1. **Data.** `core_respawn_class` has `until_cleared` again (schema + jsonl; the statblock FKs stand);
   `core_tables.py` and `tables_progression.h` regenerated. The 41 clearable-place actors are `untilCleared`; the
   Claywater crocodile stays `never`, the deserter and bog dogs `onRest`; named people in clearable places stay
   `never`. Check `respawn-clearable` now fails an `onRest` actor in a clearable place (must be `untilCleared` or
   `never`); L1 in `test_respawn.py` (41 rows, the check's failure message, the class table).
2. **"Cleared", natively.** One LCTN per clearable place (`ARG_Loc_*`, 5 records, keyword `ARG_LocType_Clearable`
   / `hook.loc-clearable`; `life_records.py`, `ActivatorRecords.cs` writes `Location`). A persistent actor homed in
   a clearable place gets ACHR XLCN = that LCTN (`place_build._ref_record` `persistentLocation`; `PlacedRefs.cs`),
   so the engine's `GetEditorLocation` names its place. The rule "cleared = every `untilCleared` actor of the place
   dead at the same moment" is `respawn::newly_cleared` in skse/core (L2 `test_respawn.cpp`: one of two dead is not
   cleared; both is; already cleared is not again; onRest/never/no-place never clear).
3. **Runtime** (`skse/ArgoniaCore/src/life.cpp`). Roster: Respawn-flagged actors; editor location keyworded
   clearable -> `untilCleared` with that place, else `onRest`. `ClearedNow()` reads each place's native
   `BGSLocation::IsCleared()`, applies the core rule, and on a newly cleared place sets `cleared`/`everCleared` and
   `AddChange(ChangeFlags::kCleared)` as Papyrus `Location.SetCleared` does. It runs on every death (any killer) and
   inside `RosterNow()` (rest and wake), so `to_reset` skips a cleared place's actors. Clearable ECZN stay
   `NeverResets`, so vanilla's reset never brings them back either. **No co-save family:** the cleared flag is a
   saved form change (`ChangeFlags::kCleared`, the bit vanilla saves) - to be confirmed in game across a load.
4. **Journey** `tests/journeys/rest-respawn-cleared.yaml` + scene `jungle-root-hollow` (4 `untilCleared`
   creatures): kill one, rest, it is back and `GetLocationCleared` 0; kill all four, cleared log + 1; rest, none
   back. **Draft (`runner: 0`)**: no clearable place is built yet (only Claywater has `build_ref` rows); with
   `runner: 1` the `--dry` lint passes except the four `ARG_Ref_JungleRootHollow*` refs "not in our plugins".
   Flip to `runner: 1` when the place is built. Listed in `checks.md`.

## Gate and build

`make check`: GREEN in 2 m 52 s (437 pytest, 33/33 C++, plugin regenerate twice identical). ArgoniaGen
`dotnet build` 0 errors. The Windows compile (`job_guard.sh run --gpu respawn-cleared -- infra/gpu-box/skse_build.sh
build windows-dev`) got the lock and failed at ssh: `Could not resolve hostname none` (argonia-play stopped; this
lane may not start it). **The DLL is not compiled**: `life.cpp`'s CommonLib calls (`BGSLocation::cleared`,
`everCleared`, `AddChange`, `GetEditorLocation`, `HasKeyword`) are unproved by a compiler.

## game-15: deploy and run

- First, with the machine up: `tooling/job_guard.sh run --gpu respawn-cleared -- infra/gpu-box/skse_build.sh build
  windows-dev` at 313a8a9 or later; a compile error there is this lane's.

- Deploy: `Argonia.esm` from this commit (5 LCTN, 1 KYWD added) and the ArgoniaCore DLL from
  `skse_build.sh build windows-dev` of this commit (job `respawn-cleared`).
- Run: `rest-respawn` (unchanged expectations: deserter back, crocodile dead), `grow-at-rest`, `die-and-recover`.
- Read in the ArgoniaCore log: `respawn: roster of N flagged actors (0 in clearable places)` - 0 is right until a
  clearable place is built.
- Not runnable yet: `rest-respawn-cleared` (draft). Unverified until then: `AddChange(kCleared)` survives a
  save/load, and `GetLocationCleared` reads our flag.
