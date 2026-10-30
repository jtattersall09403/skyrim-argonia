# Lane 1.5-build: grow, die, rest, save on the build VM (report and hand-off)

Dated 2026-10-30. The lane stopped at the context mark. Test level: L2 and L3 done; MSVC and L4 owed.

## Hand-off

**Done and committed:**
- **The sitting messages** (48c12a6): `ui/schema/sitting.ts` adds the `sitting.state` push and the `sitting.buy` and `sitting.done` intents. The twins are regenerated.
- **The core `life` module** (4bfe537, f2582ea). Files: `skse/core/{include/argonia/core/life.h,src/life.cpp,tests/test_life.cpp}`. It is pure logic over `seam::State`:
  - engine facts become use events:
    - weapon-class world id → skill;
    - armour class by the most pieces worn;
    - `HealthWatch` damage, because TESHitEvent carries none;
    - hit, struck plus block, kill, cast, unlock;
  - `use()` banks the gain into STAT;
  - `rest_at`: the ruling, the wake point, the per-rest counters, the roster reset, and the sitting opened when a level is pending;
  - the sitting view state and its intents; `close` takes one pending level;
  - `die`: one pile, which replaces the old one, wake at the last rest, counts as a rest for respawn;
  - `take_pile` (2 m, same space) and `pile_name` ("Vastei (N)");
  - `suspend_due`: quit or stream drop always; the pause hub and the interval after 300 s, never in combat. The new constant `rest.suspend_save_interval_s` is in `core_constant`;
  - `install`: the progressionOff and deathIntercept hooks, and the levelUpMenu and playerDeath handlers;
  - `at_units`/`to_units`. `units_per_metre` is now generated into `tables_progression.h` from `skyrim_units.py`.
  - The test `core.life` is the L2 run of the 1.5 journey: uses → pending level → rest → sitting → buy, refusals, cap → done → die ×3 → take → every family round-trips.
- **The ArgoniaCore adapters** (0f3eaa4). Files: `skse/ArgoniaCore/src/life.cpp`, plus `core.h`, `main.cpp`, `natives.cpp`, `CMakeLists.txt`.
  - Sinks: TESHitEvent, TESDeathEvent (kills), TESSpellCastEvent, TESLockChangedEvent (counted only while the Lockpicking Menu is open), TESEnterBleedoutEvent → playerDeath, MenuOpenCloseEvent (the pause hub's suspend save).
  - Vanilla gain is switched off at runtime (useMult and offsetMult 0 on the 18 vanilla skills). An AVIF override would ship vanilla records.
  - The engine's own save points are off (`bSave*:SaveGame`), and the chargen save block is held except around our own `BGSSaveLoadManager::Save`, written to `ArgoniaRest` and `ArgoniaSuspend`.
  - The player is made essential (the Respawn – Soulslike pattern). Death places the pile with `PlaceObjectAtMe` (persistent) and renames the base. The wake uses SetPosition in the same space, else MoveTo the rest spot. Pools are restored, `BleedoutStop` is sent and the roster is reset.
  - Skill and pool mirrors are written.
  - The roster is our persistent ACHRs whose base carries `ARG_Respawn_*`.
  - **13 natives** in `ArgoniaCore.psc`: RestAt, RestNotice, TakeVastei, SittingIntent, SuspendSave, Get/SetVastei, GetPendingLevels, GetLevel, GetSkill, PileState, WakePoint, SittingOpen.
  - `papyrus/ARG_PRKF_RestIntercept.psc`: Fragment_0 is the rest, Fragment_1 is taking the pile.
- **The sitting view** (3551f0a, by the child): `ui/views/sitting/`, `ui/fixtures/sitting.json`, harness and L1 registration. The child also added "sitting" to `screens` in `ui/schema/tests/validate.test.ts`.
- **The L4 drafts** (feb4b87): `tests/journeys/{grow-at-rest,die-and-recover,rest-is-the-only-save,suspend-save}.yaml`.

**Left, in order:**
1. **The records: done.** 1.6-wiring committed both lanes' shared files as dbf8da4. `make plugin` is deterministic, `plugin-check` is green and `make check` is green (265 passed). The commit holds:
   - `life_records.py` and its test, `ActivatorRecords.cs`, the `Reading.cs` scan, `formids.py` (`GMST_EDID`);
   - the `game_setting` table and its rows, the intermediate lines, and the regenerated plugin/ and forms.h;
   - 1.6's own change: the formid table's CHECK in `world/schema.sql` now admits engine-named GMST EditorIDs.

   The records:
   - KYWD: `ARG_RestSpot`, `ARG_VasteiPile`, `ARG_LocType_Settlement`, `ARG_LocType_Dungeon`, `ARG_Respawn_OnRest`, `ARG_Respawn_UntilCleared`;
   - ACTI: `ARG_CampSpot` (`Furniture\Bedroll\BedrollGround.nif`, verb "Rest") and `ARG_VasteiPileActivator` (world id `death.vastei-pile`, `Clutter\SoulGem\SoulGemPetty01.nif`, verb "Take");
   - PERK: `ARG_Perk_RestIntercept`;
   - GMST: `fXPPerSkillRank` = 0 is a new record (it is in no master); `iHoursToRespawnCell` (0D3646) and `iHoursToRespawnCellCleared` (0D3647) are overrides set to 1,000,000.

   Still owed: a quarantine review of the two vanilla model paths (0012), and the sourcing register.
2. **MSVC.** The first build (msvc-15) gave 4 errors, all fixed in 0f3eaa4:
   - `byCharGenFlag` now goes through `GetGameStatsData()`;
   - `RestoreActorValue` now takes 2 arguments;
   - `std::max` became `(std::max)`.

   The rebuild did not run: argonia-play was stopping and SSH timed out. Next: `tooling/job_guard.sh run msvc -- bash infra/gpu-box/skse_build.sh build windows-dev`. Note that it copies into the MO2 mods folder; use `-ModDir C:\argonia\no-deploy` while the game runs.
3. **Wiring.**
   - `EnsurePerk` adds only the dialogue perk. `ARG_Perk_RestIntercept` must also be added to the player (a two-line change in `engine.cpp` or `LifeGameReady`).
   - The sitting view's PrismaUI binding is 1.2 §0's, behind `Push("sitting")`.
   - The bridge's stream-drop hand should call `SuspendSave("stream_drop")` (game-3).
4. **The Papyrus compile** (waits on the CK, as for 1.1) and the `.pex`.
5. **The L4 runs** of the four drafts, after `bat camp` exists or with a placed `ARG_CampSpot`.
6. **One /code-review pass.** The lane diff is about 2,100 lines, so one pass is owed.

**Reds and gaps:**
- `bash skse/check.sh`: 28/28 green, peak RSS 400 MB. `make ui` is green, per the child.
- `make check`: green (265 passed), run by 1.6-wiring on dbf8da4.
- **`tests/journeys/cosave.yaml` (1.1's) uses a console `save`.** With rest as the only save, the chargen block may refuse it. It should save by resting.
- **Stated losses:**
  - Hit damage reads low when the target regenerates between hits (HealthWatch). S16a decides on the HandleHealthDamage hook.
  - `hunted` is not read; 2.11 owns stealth.
  - Spells count without CheckCast's had-effect check; 2.9 owns it.
  - Lock level and ceiling are 2.11's, so every picked lock counts.
  - Medium armour has no marker yet.
  - The 12 skills on Custom Skills Framework are not mirrored (1.3's globals).
  - The pile's halo and wisps (the vanilla effect shaders) are not applied yet; the soul-gem mesh shows alone.
  - Waking in another space after a load, with no rest since the load, wakes in place (logged).
  - The bleedout kneel may show for a frame before the fade (S17a).
