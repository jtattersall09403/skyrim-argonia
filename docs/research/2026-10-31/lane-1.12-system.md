# Lane 1.12-system (2026-10-31): stats, perks and the sitting; the System pane, quit, favourites

No game machine: L1/L2 here; every in-game row is in tests/journeys/system-perks.yaml for the coordinator's batch.

## The perk point and the level-up window (§4)
- Rule (skse/core life): `perk_points_for(levels)` and `SittingReply::perk_points`, set when sitting.done closes
  the sitting: one per level taken. Unit test in test_life (done.perk_points == 1; 0 on a buy; never negative).
- Engine (ArgoniaCore life.cpp `GrantPerkPoints`): adds to the player's `GameStateData::perkCount`, the count Wind
  UI's list shows as "Perk points %d", and logs `perks: N perk point(s) granted at the sitting, M to spend`.
- Wind UI's LevelUpWindow: the engine's level-up is never ready, because character XP is off by data (P4). As a
  guard at each close, if `PlayerSkills::CanLevelUp()` is ever true, the XP is cleared and logged as an error
  (`perks: the engine's level-up was ready`). The batch reads that the line is absent, and that no LevelUp Menu event
  comes.

## Quit to the main menu (§7): the cause, and the fix
- Cause: QuitWatch saves on the first menu close after the engine's `quitGame`/`resetGame` flag is set. But the
  Journal's `QuitToMainMenu` handler is not that flag. In game-21, setting resetGame and closing the Journal did not
  reach the main menu. So no close event ever saw the flag, and no save line came: in game-22 the only new line was
  the callback's own. This is code-proven only. Which flag the vanilla handler sets is still unread, and it no longer
  matters.
- Fix: when the Journal Menu opens, ArgoniaCore swaps the `QuitToMainMenu` entry in its FxDelegate for a wrapper.
  The wrapper writes the suspend save on the main thread, then calls the engine's own handler.
  `QuitWatch::on_quit_called` latches the save, so it is written once per quit (unit-tested).
- What the batch must read:
  - `saves: the Journal's QuitToMainMenu wrapped` when the Journal opens;
  - `...QuitToMainMenu called; suspend save due`;
  - `saves: ArgoniaSuspend written (quit)`;
  - the MainMenu menu event.

  menus-quit.yaml and system-perks.yaml both expect these lines. The ArgoniaCore build is MSVC only (the windows-dev
  preset): the change is not compiled here. The batch's build is the first compile.

## dev-favorite (§7)
- `find_any` now takes a form key, `000840:Argonia.esm` (the steel sword, world/db/formid.jsonl), through
  TESDataHandler::LookupForm. That key is the same in every load order. The parser is `to_form_key` in the bridge
  protocol, and test_protocol covers it. Load-order ids still work. Editor ids miss weapons at run time.

## The System pane (§7)
- Keyboard: Escape opens the Journal's System page. Pad: Start, then RB to System, the last tab. Both are steps in
  system-perks.yaml, with reader stills.
- Labels: Skyrim's capitals come from its translation table (interface/translate_english.txt, measured: `$SYSTEM`
  is SYSTEM and `$QUIT` is QUIT). The new recipe tools/ui_theme/labels.py, run from build.py at install (0014),
  rewrites all-capital values in sentence case: 129 of them on the local Skyrim. Short forms of three letters or
  fewer are kept.
- Squash: the retheme's SCALE_MODE now sets showAll for tweenmenu.swf and quest_journal.swf. The tests are in
  tools/ui_theme/tests (14 pass).
- OWED: the touch menu button. It is a HUD element (ui/views, views.cpp), which is another lane's, and the runner
  has no touch action yet.

## The CSF skill set (§4)
- `PLAYER_SKILL_AV` in skyrim_units, read with the world DB `skill` table, generates `tables_mirrors.h`, which is
  where kSkillMirrors now comes from. It also generates data/csf/SKSE/Plugins/CustomSkills/SKILLS.json: 27 skills,
  14 by vanilla AV and 13 as CSF skills. Each CSF skill has 5 GLOBs and one placeholder perk ("No perks yet", level
  100) as its one-node tree.
- stack.py stages data/csf as the mod `argonia-csf`. The tests are in tools/argonia_world/tests/test_csf_records.py.
  The CSF schema is in csf-config.md. CSF needs no AVIF record.
- The batch must read:
  - CustomSkills.log loads 13 skills with no "Parse errors";
  - the placeholder perk cannot be taken.

## The perk text (§4)
- 273 reachable perks are reworded, with the numbers unchanged. They cover 18 vanilla trees plus Dawnguard's
  Vampire Lord and werewolf trees. The data is in world/db/perk_text.jsonl and the perk_text table, and
  data/immersion/verdicts.jsonl holds 273 `restyle` verdicts.
- Reader pass 1: 1 Nordic tell (Dragon Armor) and 0 number changes. Pass 2: 0 tells and 0 number changes.
  test_perk_text has 6 tests.
- WITHHELD, for a ruling: the PERK override deep-copies each vanilla record into plugin/Argonia YAML. That would put
  273 vanilla records in git (0003). So the layer is not wired in intermediate.py.
- The owed route is one of:
  - an install-time override (0014), with tools/ArgoniaGen `PerkRecords.Override` already written;
  - a runtime name and description set in ArgoniaCore.

  The text does not reach the player until one of them lands.

## Open, from the coordinator's probe
- One-handed, Two-handed, Archery and Pickpocket show at 0 in Wind UI's stats pane, which is a vanilla tell. It is
  not solved here.
- Proposed: the same install-time override route renames or hides those AVIFs. Wind UI reads the engine's AVIF list,
  and CSF cannot remove vanilla skills.
- The mysticism mirror row is left to the magic lane.

## Gate
- `make check`: exit 0 (job chk). skse ctest is 33/33. tools/ui_theme has 14 tests, all passing. Both journeys lint
  clean.
- `make plugin` regenerated plugin/Argonia with the CSF records: 2787 YAML files.

## Follow-ups (coordinator)
- **Perk text, install-time route (0014).** `python -m tools.argonia_world.perk_plugin` reads the perk_text table
  through db.py and the player's Skyrim.esm and Dawnguard.esm. It writes out/perks/argonia-perks/ArgoniaPerks.esp
  (ArgoniaGen `perks`) in about 2 s. deploy.sh runs it as the `perks` step, and stack.py stages it as the mod
  `argonia-perks` above our ESMs.
- What was checked:
  - a dry stage of the lod group listed it in plugins.txt and modlist.txt; the full 8-group stage was not run;
  - test_perk_plugin finds 273 overrides. Only FULL, DESC and EPF2 (the button label) differ. Skyrim.esm records are
    compared byte for byte; Dawnguard records only by signature and size;
  - every number in DESC matches the vanilla text;
  - plugin/Argonia/ is unchanged;
  - a reader went over the 11 candidate rows (the four post-pass-2 rows could not be singled out) and found 0 hits.
  - The step is documented in installer/steps/perk-text.md.
- **Touch menu button.** The HUD has a "Menu" button under the minimap: at least 44 px, frame tokens. It sends
  `hud.menu`, and ArgoniaCore's `OpenTweenMenu` (engine.cpp) shows the Tween Menu. dialogue.cpp gained one line,
  the routing.
  - Off-game: the stills (out/ui/stills/hud/minimap0@{720p,1080p,v5-folded,v5-unfolded}) passed the reader.
    The ui harness had 0 fails over 156 stills.
  - Not seen: the effects stack and the minimap together.
  - The batch must read `views: the HUD menu button opened the TweenMenu` and the TweenMenu event. Whether PrismaUI
    passes touch to the HUD is unproven, and the tap itself is owed (the runner has no touch).
  - No wait/rest button: skipped to keep the control clean.
- **world-reads:** the perk paths now go through db.py. `make world` is green.
- **Gate:** the only red left is `budget`: CLAUDE.md is 1134 words against 1100, which came in at 63a7ad1 and is not
  this lane's.
