# Lane core-wiring (2026-10-30): the ArgoniaCore side that 1.5-build and 1.6-wiring left

Commits: 2bf575c (the wiring), 18c1d3e (verdicts, register, journals), and the review fixes after them. All the
work is L2 on the build VM, plus an MSVC build on argonia-play. Nothing was deployed. game-5 lays the DLLs and runs
the L4 journeys.

## What was done

**From 1.5**
- **The rest perk on the player.** `EnsurePerks` (engine.cpp) adds `hook.rest-intercept`, `hook.dialogue-intercept`
  and `combat.carriers`. A missing perk is logged.
- **The sitting view's binding.** `ViewIntent` is the one intent entry for every view. It is routed by type through
  `router::intent_view` (core, tested). Dialogue intents go to the conversation and `sitting.*` to the sitting, so
  the browser's single `window.argoniaIntent` reaches both. The PrismaUI call itself is still 1.2 §0's, behind
  `Push`/`ViewIntent`, as for dialogue.
- **The bridge-callable suspend save.** ArgoniaCore listens for the SKSE message `SUSP` from `ArgoniaBridge`
  (`core::life::BridgeSuspend`). ArgoniaBridge's endpoint is `core-suspend <quit|stream_drop>`, and `Bridge.suspend_save()`
  is the client call. Both reason paths use `life::suspend_why`, so an unknown word is refused and never forces a
  save in combat. game-4 asked for the bridge half and wrote the conditions (command table row, live
  fail-on-purpose case, journal).
- **cosave.yaml saves by resting** at a camp spot and loads `ArgoniaRest`.

**From 1.6**
- **The carriers.** core `combat::compute` gives the four wired values. ArgoniaCore's `WriteCombat` writes them on
  game ready, equip, a carried change, a skill rank, an attribute change and the sitting's close. The writes are
  coalesced into one main-thread task.
- **The vanilla weapon skills pinned at 0.** These are OneHanded, TwoHanded and Marksman. The Marksman mirror is
  removed.
- **The roll lock.** TK Dodge Addon has its own perk lock: `bUsePerkLock = true` is a `combat_mod_setting` row, and
  ArgoniaCore reads `sDodgeRequiredPerkID` from the staged toml, then gives or takes that perk by burden tier. No
  input filter is needed.
- `tables_combat.h` is generated from `combat_carrier` and `combat_constant`, and `units::weight_per_kg` is added.

**The L4 checks are named in the journeys:** fight-damage-builds, fight-roll-burden, rest-is-the-only-save,
suspend-save, grow-at-rest and cosave.

**Quarantine (0012 §6).**
- **ARG_CampSpot: replace.** `bedrollground.nif` is a furniture marker with no geometry and no collision. It was
  replaced by `bedroll01.nif`, a plain hide with a fur pillow.
- **ARG_VasteiPileActivator: keep.** It is a plain crystal.
- The two sourcing-register rows are added (the base game's borrowed meshes, and TK Dodge's perk lock).
- Both verdicts wait on a still for their check (`check_passed` false).

**The combat journal** is opened at docs/research/journals/combat.md, with the wiring's state, the losses and the
review.

## Evidence

- `bash skse/check.sh`: 29/29. This adds core.combat and new cases in core.life and core.router.
- `make check`: CHECK GREEN, 266 passed, plugin-check identical.
- MSVC (`ARGONIA_MODDIR='C:\argonia\no-deploy' skse_build.sh build windows-dev`): SKSE-BUILD OK, ctest 29/29, 0
  warnings.
  - `C:\argonia\skse\out\windows-dev\dist\SKSE\Plugins\ArgoniaCore.dll` is 1,453,056 bytes.
  - `...\dev\SKSE\Plugins\ArgoniaBridge.dll` is 833,536 bytes.

## Review (/code-review high, 48c12a6..2bf575c)

There were 10 findings. 8 are fixed; the list is in the combat journal.

Bugs found in 1.5's code, beyond the review:
- The skill mirrors used the menu names `Archery` and `Speech`. The engine names are `Marksman` and `Speechcraft`.
- The SkyrimPrefs save points were looked up in the wrong collection.
- The camp spot was invisible.

Not changed:
- `view.close` for the sitting. It cannot be decoded, because ViewId has no `sitting`.
- Skyrim's own Block term. Whether it doubles with `body.block` is an L4 question for fight-archetype.

## Left

1. **game-5: deploy the two DLLs.** Restage Argonia.esm and tk-dodge-re-addon together with the DLL. Then run the
   six journeys at L4.
2. **The quarantine stills**, at rest-is-the-only-save step 0 and die-and-recover. Set `check_passed` when they pass.
3. **Losses.**
   - AR is the Unarmored term only, until the item rows carry a rating (2.7 data).
   - Effects are not in the pass (2.1).
   - Soft requirements are 0 (2.7).
   - Medium armour has no marker (1.3).
4. **Paths outside the brief's list.** `tools/argonia_world/core_tables.py` and its test were changed for the
   generated combat table. `tools/argonia_world/life_records.py` and its test, and plugin/ for the one ACTI, were
   changed for the camp spot fix. Also changed: `skse/ArgoniaBridge/src/ep_state.cpp`, `tools/tests/*bridge*` and
   `docs/research/journals/bridge.md` (at game-4's request), `world/db/combat_mod_setting.jsonl` (the
   `bUsePerkLock` row), and `infra/gpu-box/skse_build.sh` (the `ARGONIA_MODDIR` pass-through for `-ModDir`).
