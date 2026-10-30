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
