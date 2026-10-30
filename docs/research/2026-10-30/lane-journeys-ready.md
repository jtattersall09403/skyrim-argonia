# Lane journeys-ready (2026-10-30)

Build VM only; the game machine was not touched. Every owed journey now passes `run_journey.py --dry`;
`tests/journeys/batches/game-13.yaml` is written by `run_batch.py --write-owed` (32 items, save-changing last).

## Converted (runnable, `--dry` ok)

attributes, cosave, quest-board, dialogue-intercept, grow-at-rest, die-and-recover, rest-is-the-only-save,
suspend-save, fight-archetype, fight-damage-builds, fight-lock-on, fight-roll-burden, ui-sweep, w3-interior-sun,
w3-road-hops, w3-weather-stills, water-swim. claywater-look, claywater-walk and first-place were already runnable.

- dialogue-intercept: the 2.W5 block no longer holds. ARG_Speaker (0x853) is on four NPC_ records
  (plugin/Argonia/Npcs: WellKeeper = Livia, N1, N13, LandingSPoler).
- quest-board: lf83-components and lf83-endings already run the main path and the staged endings. quest-board now
  runs only what they leave out: fail-forward 92 after the player's own blows kill Livia.

## Owed steps (`owed:`, listed in each report; the journey runs on past them)

- No bridge setter: `core` refuses setters by design. Owed: SetAttribute and its clamps (attributes), the novice
  and god builds (fight-damage-builds), and the run to a pending level and the sitting (grow-at-rest). Vastei is
  earned by blows instead of SetVastei.
- Missing reads: TDM's lock target (fight-lock-on), a pile count (die-and-recover), the INI [Interface] compass
  and marker flags, a per-frame i-frame trace, a land texture (LTEX) read under the player (w3-road-hops), and the
  Community Shaders log name.
- Missing props or data: the ui-sweep prop menus (chest, merchant, book, lock, trainer, alchemy table) and the
  MCM pad path; a second interior and a bit-15 control cell; a jungle view; road-leg hops. The hops are derived
  data, so they belong in tools/world_sample.py's generator.

## Dropped old drafts (world-sample covers them)

- water-steps-stills: stop 4's reader (s04-bottom-of-reach: no z-fighting, no visible sheet line) and stop 5.
- water-look: the colour reader lines at stops 4 (fresh green-brown) and 6 (black-brown marsh).
- nav-paths-200: stop 12 (20 seeded path pairs plus a swim path, `nav` reads within 1.5x).
- w3-weather-skip.md: stop 11 (a 7-day skip and the quarantine).
- w3-road-hops gates: stop 9 (gate push, segment push). The signpost is stop 10.

Left as drafts, with a pointer to this report: water-budget (it needs a per-budget plugin swap),
water-npc-swim, nav-npc-walk and nav-sandbox-20 (they need a travel or sandbox package order that the console
lacks). Stale reference: docs/phases/1-core-loop/2.W3-regions-roads.md:73-76 still names the .md drafts.

## Runner additions (tools/run_journey.py, tools/run_batch.py; L2 tests in tools/tests)

- `relaunch: {save: X, scene: false}`: resumes where the save left the player (suspend-save).
- `{kept: name, plus: n}`: compares against a change from a kept value (a hit's damage).
- Step saves: after each passed step the runner runs console `save argj-<id>-<step>` and removes the previous
  one (`Bridge.delete_save`). The kept values go to out/resume/<id>.json. `--from <step>` and `--only <step>`
  run from the step save. run_batch takes `--from/--only <item>[:<step>]`. Journeys that count or test saves set
  `step_saves: false`: cosave, rest-is-the-only-save, suspend-save, menus-quit.
  RISK, unproved in game: the console `save` may be refused by the chargen block that the cosave draft names.
  The first game lane checks that `argj-*.ess` appears.
- `run_batch --owed` lists each journey's status (draft, never, failed or passed) from out/batch summaries and
  out/runs reports. `--write-owed <batch.yaml>` writes every runnable journey that has not passed; save-changing
  journeys (a relaunch, or `batch_last: true`) go last, and soaks and `must_fail` fixtures are left out.
  **Game lanes compose their batch this way** and rewrite it after game-12's results land.

## Gate

`make check`: tests 398 passed. One red is not this lane's: budget (`CLAUDE.md is 1100 words; the budget is 1100`).
