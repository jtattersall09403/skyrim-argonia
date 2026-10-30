# Lane fixes-2: game-10's fixes (the gate's DSC red, the journal notice, LF83's thing hooks, the HUD hide, the crocodile), and the coc-start character

Commits: 1f459e6 (stack.py masters), 2dab64e (the rest). Test level L1/L2; every in-game check goes to game-11.

## 0. Priority (from game-11): the character at game ready
- Cause (game-11): base_save.py starts the game with `coc` from the main menu. That never sends kNewGame, so the
  sheet stayed uninitialised, no carrier was written, and TK Dodge's perk lock refused every roll.
- Fix: `OnGameReady` calls `NewCharacter()` first. In core, `ensure_character` (sheet.h) makes the studio character
  only while the sheet is uninitialised; a sheet that exists is never replaced.
- L2: test_combat `character_made_at_game_ready`. With no sheet, the character is made and the carriers are
  written (writes non-empty). A second ready keeps the sheet.

## 1. The gate's red: "Dark Souls Combat.esp is listed but not found"
- Cause: `stack.py combat B` restages the build VM's profile, which is the plugins.txt that plugin-check reads.
  `masters`, which copies those plugins into the build VM's Data, was not run after it. So the profile and Data
  named different sets until A was restaged. When this lane started, the profile was A (restaged 10:29) and held
  no DSC.
- Fix (1f459e6):
  - `cmd_install` runs `cmd_masters` after the stage, for every set (A, B, B2).
  - `cmd_masters` lays only the staged set's plugins. It records what it copied in Data/argonia-masters-copied.txt
    and takes out an earlier set's plugins and mesh lists.
- L1: 2 tests in tools/tests/test_stack_combat.py:
  - B lays DSC.esp and its mesh list; back to A, both are gone and argonia-plugins.txt names A only.
  - install's order is stage, then masters, then push.

## 2. The "journal updated" notice
- Logic (core journal):
  - `notify` gives one notice per logged entry or found clue. The same quest's second notice within
    `notice_merge_seconds` (2 s) is merged: a clue and the stage it sets give one notice.
  - `live` keeps notices for `notice_life_seconds` (6 s).
  - Both constants are core_constant rows (module journal).
  - L2: test_journal.
- Adapter (ArgoniaCore views.cpp `JournalNotice`, run on the main thread):
  - The engine's own HUD message, `RE::SendHUDMessage::ShowHUDMessage("Journal updated")`. It shows in the HUD's
    message block, which is not one of the hidden clips.
  - A `journal` notice in our HUD state's `notices`.
  - The SKSE mod event `ArgoniaJournalNotice`, with strArg "<quest> entry|clue" and numArg the stage or objective.
  - Raised by `AddJournalEntry` (entry) and by FactsChanged's SetObjectiveCompleted (clue).
- Bridge: ep_events.cpp now records SKSE mod callbacks as kind `mod`, matched by the event name.
  tools/bridge.py has `JOURNAL_NOTICE_EVENT`. A journey asserts it with
  `event: {kind: mod, match: ArgoniaJournalNotice}`.

## 3. LF83's three thing hooks
- Data: the table `thing_hook` (quest, thing, hook activate|read, sets_flag) with 3 rows.
  - `thing_hooks.py` resolves each thing to the record it is placed as: build_ref base, then formid entity key.
  - It refuses a row whose thing or flag the quest lacks.
  - It renders `things_table.h` (through core_tables, so the gate's --check covers it).
- The records:
  - The well head and the mortar tub carry the keyword ARG_ThingHook and the verb "Examine".
  - ARG_Perk_ThingHooks (hidden) has an Activate entry on that keyword: Run Immediately, Replace Default.
  - Its fragment ARG_PRKF_ThingHook.psc makes one native call, `ArgoniaCore.ThingActivated(akTargetRef)`.
  - EnsurePerks gives the perk (world id hook.thing-activate).
- The ledger: dialogue.cpp's menu sink, on the Book Menu opening, reads `BookMenu::GetTargetForm()`. No Papyrus.
- Core: `things::hook_for(record world id, how)` gives the flag. `MeetThing` sets it through the `setFlag`
  action, then FactsChanged follows, so the clue completes and the notice shows.
- Tests:
  - L2 test_things: the three hooks, a record met the other way, a record that is not a thing, the table sorted.
  - L1 test_thing_hooks: the hooks resolve, the perk is wired to the keyword, the ACTIs carry it, and a flag the
    quest does not write fails on purpose.

## 4. The vanilla HUD hide
- Why "0 out of HudElements" (probable): CommonLib's `IsObject()` does include display objects, so the old match
  by our mark failed for another reason I could not see off-game.
- HUDMovieBase.SetMode sets each listed element's `_visible` to `hasOwnProperty(mode)`. Each hidden clip now gets
  three locks, and each one hides it alone:
  1. Its mode members are deleted (`router::kHudModes` and any `...Mode` or `...Playback` member found by
     VisitMembers), so no mode shows it.
  2. Its `_alpha` is set to 0, which mode changes never touch (the way TrueHUD hides vanilla bars).
  3. Its HudElements entry is removed, matched by identity (GFxValue ==, the same object), our mark, or `_name`
     (`router::hud_list_removals`).
- The Views line now also gives "modes cleared M, alpha 0 K, members <clip>{...}" after the old text, so a lock
  that fails can be diagnosed from one read.
- L2: test_router (removal by any of the three matches, highest index first; mode names, and member names that are
  not modes).

## 5. The crocodile
- Measured off-game:
  - KotM's CrocodileWaterRace (000A01) has DATA flags 0x02504040: Swims, no Walks.
  - Its WKMV, RNMV and SWMV all point to movement type 0x0D8C5E.
  - Its graph is vanilla `Actors\Slaughterfish\SlaughterfishProject.hkx`. Skyrim - Animations.bsa holds 32
    slaughterfish files: attacks, idles, recoils, a stagger, `swim_*` and turns, and **no walk or run clip**. So
    with Walks it will move on land on its swim clips (it will slide). Recorded in the creature_hunt row.
- Data: the table `creature_hunt` (npc, way walk|shallows, den_ref_id, combat_style).
  - Default (b) `walk`: a RACE override in Argonia.esm. RaceRecords.cs copies KotM's record whole and adds Walks.
    The den is the bank den.
  - Fallback (a), one row: `way=shallows, den_ref_id=ref.claywater-station.crocodile-den-shallows`. The new marker
    is 6 m from the pool's centre, floor about 31.8 m, about 1 m under the 32.84 m surface. The actor then stands
    at that den and there is no RACE override.
  - Both ways: our CSTY ARG_CSTY_MeleeAmbush (`place_build.COMBAT_STYLES`, our own numbers; Dueling).
- L1: test_creature_dens (walk is the default, with the override and the style; shallows is one row away, at
  wading depth, with the actor at the den and no override).

## Gate and builds
- MSVC windows-dev green on 2dab64e: ctest 33/33, ArgoniaCore.dll 1,731,584 bytes, SKSE-BUILD OK.
- skse/check.sh 33/33.
- `make plugin` twice: Argonia.esm sha256 d8b94622... both times.
- `make check` is **red, but not from this lane's paths**:
  - `plugin-check`: the ArgoniaWorld.esm sample hash (acdd07217db8, manifest 0e319eafda84). This comes from
    another lane's uncommitted change to the world in the shared tree (plugin/.../ARG_Province RecordData.yaml,
    vegetation).
  - `unit` test_stack_combat `each_combat_set_lays_its_rows`: 'nemesis' extra, from the uncommitted
    data/dependencies.json (game-11's).
  - `unit` test_world_sample: falls top_z 17091.5 -> 18010.3, from terrain or ground data, not touched here.
  - The DSC "listed but not found" red is gone.
- game-11 was told what to deploy and check (SendMessage).
