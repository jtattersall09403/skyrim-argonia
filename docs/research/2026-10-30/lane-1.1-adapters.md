# Lane 1.1-adapters: ArgoniaCore's adapters on skse/core (report and hand-off)

Dated 2026-10-30. The lane stopped at the context mark. Commit `0c53bee`. Test level: L2 now, L4 drafts owed.

## Hand-off

**Done and committed (0c53bee):**
- **New skse/core modules:** `seam` (`include/argonia/core/seam.h`, `src/seam.cpp`) and `talk` (`talk.h`, `talk.cpp`), with tests `core.seam` and `core.talk`.
  - `seam::State` holds every family's state. `seam::bind` registers all 9 families on `families::Registry`: META, STAT, DISP, JRNL, ITEM, DETH, QSTA, TOPC and the new QWCH (watched quests, in `schema/families.json` and the round trip). `test_roundtrip` now binds through `seam::bind`, which is what the plugin registers: 11 schemas.
  - `WorldFacts` answers the condition vocabulary over the co-save and an `Engine` interface.
  - `Session` covers the action natives (through `actions::run`), the journal, watch and unwatch, and `step()`, which gives the orders for each watched quest.
  - `install` puts the hooks into the router and proves that a second registration is refused.
  - The seven attribute mirrors follow av-audit.md.
  - `talk::Conversation` provides greeting, `offered`, `answer`, `deliver`, onDelivered actions, intents decoded by the twin, and a schema-valid `dialogue.state`.
  - `talk::fixture_store()` loads only the written lines into the game.
- **`forms.h`:** world id to FormID, generated from the `formid` table by `tools/argonia_world/forms_table.py`. It is registered in `core_tables.render`, so `--check` covers it, and written by `make plugin` (one line in `pipeline.py`).
- **ArgoniaCore** (`skse/ArgoniaCore/src/{core.h,engine.cpp,dialogue.cpp,natives.cpp,main.cpp}`):
  - The co-save goes through the registry. The old META-only path is gone.
  - 24 natives in `papyrus/ArgoniaCore.psc`, the 10 quest natives included.
  - The quest adapter steps the watched quests on each fact change: a native, the TESDeathEvent, the TESContainerChangedEvent, a topic heard, a Sleep/Wait or Loading menu closing, a season turn. It applies SetObjectiveCompleted and SetStage through `DispatchMethodCall`.
  - The MenuOpenCloseEvent sink blocks the Dialogue Menu as the backstop and opens our conversation.
  - `OpenDialogue` is the native the perk fragment calls (`papyrus/ARG_PRKF_DialogueIntercept.psc`).
  - The view host (`Push` / `ViewState` / `ViewIntent`) logs each push whole. The PrismaUI binding is owed to 1.2 §0.
  - The attribute AVs are mirrored on load and on each set. `EnsurePerk` adds the intercept perk to the player.
  - The season's weather globals are written (`weather::on_day`).
- **schema_gen fix** (`tools/schema_gen/emit_cpp.ts`): MSVC failed on the `max` macro and C4456. The twin now emits `(std::numeric_limits<double>::max)()` and one variable name per field. `messages.h` was regenerated; `messages.ts` is unchanged.

**Measured:**
- `bash skse/check.sh`: 100 % of 27 tests passed, peak RSS 342 MB.
- The schema_gen node tests: 4 passed.
- `test_core_tables`: 6 passed.
- **MSVC** (the skse_build.ps1 path with `-ModDir C:\argonia\no-deploy`, because the game was up at the main menu): SKSE-BUILD OK windows-dev, ctest 27/27, `ArgoniaCore.dll` 1,254,912 bytes. No `warning C` lines came from our sources. The DLL was **not deployed** to MO2.

**Left, in order:**
1. **The perk child** (deliver-small, still running at hand-off). Its files are uncommitted:
   - `tools/argonia_world/hooks_records.py` and its test
   - `tools/ArgoniaGen/PerkRecords.cs`
   - the edits to `Generate.cs`, `README.md` and `intermediate.py`
   - `plugin/Argonia/Perks/` and `Keywords/ARG_Speaker - 000853`

   Its two formid rows (`hook.speaker` 0x853, the perk) and `forms.h` are already in 0c53bee. Next: check its result (the YAML shows the Activate entry with RunImmediately and ReplaceDefault, HasKeyword ARG_Speaker on tab 1, and fragment 0), run plugin-check, then commit those paths.
2. **The Papyrus compile is not run.** Put `skse/ArgoniaCore/papyrus/ArgoniaCore.psc`, `ARG_PRKF_DialogueIntercept.psc` and `papyrus/generated/ARG_QF_LF83.psc` into a separate in-folder. Then run `records_jobs.ps1 -Stage papyrus` there; it needs no GPU and no display. `records_jobs.sh papyrus` takes only `papyrus/*.psc`.
3. **Deploy the DLL** with `skse_build.sh build windows-dev` once the game is down.
4. **The L4 drafts are not written:** `tests/journeys/{cosave,quest-board,dialogue-intercept,attributes}*`. The hands they use:
   - `Families`, `FamilyDigest`, `SaveCount`: the co-save round trip.
   - `JournalEntries`, `GetFlag`, `KnowsTopic`, `GetDisposition`, plus GetStage: the quest board.
   - `RouterLog`, `ViewState`, `ViewIntent`: the dialogue intercept, with MenuOpenCloseEvent never showing the Dialogue Menu.
   - `GetAttribute`/`SetAttribute` against the console `GetAV Fame` … `IgnoreCrippledLimbs`: the attributes.

   The dialogue-intercept draft needs Livia's NPC_ record carrying ARG_Speaker, which waits on 2.W5. Until then it is owed.
5. **The skse-build journal section is not written.** It should record that MSVC needs NOMINMAX-safe generated code and that deploy is skipped while the game runs.
6. One /code-review pass: the diff is past 1,500 lines (2,392).

**Reds and gaps:**
- **`core_tables --check` is red from another lane.** The LF83 fix lane's uncommitted `dialogue_line` rows make `fixture_topics.h` stale. It is not from this lane, and `make check` was not run in full.
- **Stated losses:**
  - A day change while walking is seen only at the next menu close or load.
  - `npcAlive` is unknown for an NPC that is not loaded, unless a reference row exists.
  - Settlement standing, local variants and prices live in QSTA (keys `place#variant`, `price#service`) until 2.6 and 2.12.
  - An unmet person's base disposition is 0, because the NPC rows hold no authored base.
  - The Store is the generated fixture. The record sidecar loader is owed to 2.W5.

## Continuation (2026-10-30, second context)

**Done:**
- **The intercept perk** was already committed in 8dacfe1, by the last context's child. `make plugin-check` passed
  on it (exit 0, 290 MB peak RSS) once the water lane's rows were in.
- **The Papyrus compile is owed.** argonia-play has no CK: no `Papyrus Compiler\PapyrusCompiler.exe` under the
  game folder or anywhere on C:, and no `appmanifest_1946180.acf`. `records_jobs.ps1` stops at
  `Need $pc 'the Creation Kit ...'`, and the owner-setup step "Add the Creation Kit to the Steam library" is still
  unticked. `records_jobs.sh papyrus [files|dirs]` now takes a list. With no list it compiles `papyrus/`,
  `papyrus/generated/` and `skse/ArgoniaCore/papyrus/` into one in-folder, so a fragment finds ArgoniaCore.psc.
  There are no .pex hashes yet.
- **Four L4 drafts** in `tests/journeys/`: `cosave`, `quest-board` (main run and two fail-forwards), `attributes`,
  and `dialogue-intercept` (blocked on 2.W5's ARG_Speaker on Livia's NPC_). They are in 0.3 §d's format, because
  `tools/run_journey.py` does not exist.
- **The skse-build journal section** covers the MSVC `max` macro, no deploy while the game runs, and the missing CK.
- **/code-review (high) over 18c0053..HEAD:** 10 findings; 9 fixed, 1 a stated loss.
  - The stale conversation: OpenDialogue now resets `talk` before each open.
  - Duplicate quest orders: `seam::InFlight`, with `in_flight_once` as its test.
  - Every vanilla Dialogue Menu was closed: now only an ARG_Speaker's is (`talk::speaks`), and the rest are left
    open with a warn line.
  - Gold changes did not re-step the quests: they do now.
  - The greeting's notes were swallowed: they are now logged (`greeting_notes`, with a test).
  - The fixture conversion was duplicated: there is now one `talk::fixture_rows`.
  - `form_at`'s case fold matched non-letters: it now folds ASCII letters only, with a test.
  - Natives were missing: `TakeItem`, `GiveGold` and `TakeGold` are added.
  - `records_jobs.sh`'s default missed sources: it now covers all three folders.
  - **Stated loss:** disposition reads the base Personality, not the effective one. No effect writes the attributes
    yet; the comment now says so.
- **Measured:**
  - `bash skse/check.sh`: 27/27, 387 MB peak RSS.
  - MSVC no-deploy build (`-ModDir C:\argonia\no-deploy`): SKSE-BUILD OK, ctest 27/27, 0 `warning C` lines.
    `ArgoniaCore.dll` is 1,315,840 bytes, SHA256 202701DAE1F6731C96472C690B6B8A93686D55E4411BEB3C1B071B16D1607E57.
- **The deploy was handed to game-3** (a658d578d34038e38): the command, the SKSE log lines and the co-save lines to
  check. game-3 will deploy at the next game-down slot. `Version()` through the bridge waits on the .pex.

**Left:**
- The CK install on argonia-play, then `records_jobs.sh papyrus` and the .pex hashes.
- game-3's deploy lines.
- The L4 runs, once `run_journey.py` exists.
- The effective Personality, owed to the spell chunk.
- `form_at`'s linear scan (P2 rolling), which matters only once the formid table holds the world.
