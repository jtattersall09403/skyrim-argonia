# Lane 1.12-r4-menus (round 4; owner play test 3 findings 6, 7, 8, 10, 11; the owner's card ask of 22:06)

## The menu loop (finding 6)
`python -m tools.ui_harness menus [--only VIEW ...] [--no-stills]` (tools/ui_harness/menus.py) -> out/ui/menus/report.json and stills.
Seven menus (inventory, charsheet, magic, system, journal, chart, dialogue) x four viewports: 28 runs in 32.2 s.
The pad is the in-game path: PrismaUI's `gamepadbuttondown` on window.prismaUi.controls, stood up before load.
Per run: a scripted pad sequence (d-pad, LB/RB, LT/RT) with the focus recorded after each press; a still at the
opening and after the script; a graph from every focusable control in four directions, with reach counted from the
opening focus; fails on a dead press (a control lies that way but focus does not move), a column jump, an opening
with nothing focused, or text contrast under 4.5:1 (WCAG, composited over black).

## Causes found by the loop, fixed at source in ui/views/core/nav.ts
- Magic, the journal and dialogue opened with nothing focused. The first pad press focused the first control in DOM
  order, which was Close on magic. Before: 0 of 32, 0 of 9 and 0 of 10 controls reached from the opening. Fix:
  `settle()`, called from `restore()` after each push, focuses the first row of the view's list (only views that have
  a [data-list]; the chart's d-pad pans). After: 32/32, 9/9 and 10/10 reached.
- Magic's "L" side controls: up/down walked from the row's name, so the press jumped a column. 120 column-jump fails
  over the four viewports. Fix: a side control walks its own column (the `aside` branch in move()). After: 0.

## The System pane (finding 8)
The pane is now a paper sheet in the journal's frame window. Left-hand group headings "Game" and "Leave" use the
journal's `.ghead` style; the entries are ink on paper (ui/views/system/{render.ts,system.css}).
Lowest contrast: 3.16:1 before (the dimmed Load entry), 6.61:1 after.

## Loading screens (findings 10, 11)
- The data was the fault: the Hist (tree, roots, pool, taproot, fruit) was 5 of 12 screens, about 42% of loads.
  Crocodiles were only 1 of 12.
- Fix (commit f9d68cc0): a row's `chance` in data/loading-screens.json becomes a
  GetRandomPercent condition on its LSCR, so the row is eligible on that share of loads. Files:
  tools/argonia_world/intermediate.py loading_screen_layer, and tools/ArgoniaGen/QuestRecords.cs (the generator
  builds).
- The five Hist rows are at 50. Over 1,000 simulated loads: Hist 27.9%, crocodile 11.8%. The test passes with no
  xfail.
- Unmeasured: I have not checked that Skyrim.esm uses GetRandomPercent on any LSCR (golden rule 0034). The engine
  evaluating the condition at each load is an assumption until the in-game row runs.
- The squash is in loadingmenu.swf (Flash), so it is owed as a still at the 2352x2172 phone viewport.

## The two cards (owner 22:06)
- Cards, both shaders on (infra/gpu-box/sunshine-apps.json, make-cards.ps1):
  - "Argonia" runs `-Ui windui`: the profile as laid.
  - "Argonia custom UI" runs `-Ui custom`.
- stack.py (UI_VARIANTS, ui_variant, `plan --ui custom|windui`) writes ui-custom.json beside the profile on each push.
- stack.ps1 play-modded `-Ui custom` sets aside every Data path placed by windui, dear-diary or wood-and-paper, and our
  Dear Diary retheme (argonia-theme) where it overlays them. A path that a lower mod also places is laid again from
  that mod; the dropped rows' plugins leave Plugins.txt.
- Probe on the staged profile: 97 paths set aside, 0 laid again, no plugins. The custom card falls back to SkyUI's BSA
  and the game's own menus wherever our screens are not yet routed. Its loading menu also loses the theme's showAll
  squash fix.
- Test: tooling/tests/test_stack_ui_variant.py. Nothing is dropped from the profile; the owner rules after comparing.

## Inventory and character sheet views (finding 7), and their wiring on the custom card
- The views (ui/views/{inventory,charsheet}) are in the paper theme.
  - Inventory: LB/RB tabs with pad-only glyphs, a list with an icon slot per row, an always-shown detail panel with
    Use/Drop, a carry-weight bar with gold, and a legend (A use, X drop, LB/RB, B).
  - Character sheet: tabs, a side column with level and pools, and a one-line description of the focused row.
- OpenMW methods taken (source studied, then deleted):
  - inventorywindow.cpp:1060-1084 (LB/RB tabs), :140-153 (pad glyphs), :986-1013 (X drops);
  - itemview.cpp:228-250 (d-pad in the item view);
  - windowmanagerimp.cpp:2782 (button legend);
  - statswindow.cpp:736 (a read-only sheet with no row focus: ours adds row focus).
- Wiring (commit 3dd7807):
  - core router `set_custom_ui`: when WindUI.dll is not loaded, the router takes InventoryMenu and StatsMenu (L2:
    test_router custom_ui_card_takes_inventory_and_stats). On the "Argonia" card both stay restyled, so nothing
    changes there.
  - kViews gains inventory and charsheet; `close_intent` closes them on Esc, Tab or B (test_views).
  - core `panes` holds the rules, tested in test_panes: categories, the A verb, stack keys, the order, the sheet from
    the `stats` family grouped Major/Minor/Miscellaneous, and perk refusals.
  - skse/ArgoniaCore/src/panes.cpp is the glue:
    - it fills both states from GetInventory and the perk trees of the mirrored skills;
    - use and drop go through ActorEquipManager and DropObject; perks are taken with AddPerk, spending perkCount;
    - books refuse with a notice (reading from the inventory is owed).
- The pad's X is now the nav action `drop` (nav.ts; keyboard x). The loop proves X sends inventory.drop and that B
  sends view.close on every menu but dialogue.
- Not built on Windows here: the build VM builds only skse/core. The ArgoniaCore glue compiles first at the
  planner's deploy; the APIs were checked against the CommonLibSSE-NG headers in ~/.argonia/commonlib.
- Owed: skills from the Custom Skills Framework have no perk tree here (1.3). The level's progress is 0 until 1.3's
  meter.
- Owed: on the custom card the pad's pane cycle (padcursor.cpp) still assumes Wind UI's windows. In game,
  START + RB must reach our views.

## Harness evidence
- Loop: 28 runs, 0 fails, 43.9 s, including the X and B checks.
- skse/core ctest: 36/36 (panes, router, views, messages).
- `--smoke`: 0 fails. `make ui`: 23/23. `make check-reach`: green.
- Full `python -m tools.ui_harness`: 16 fails, all in existing views (child's run), none in the new ones.
- Reach is red on 4 tests that are not this lane's: tools/argonia_world/terrain/probes/vanilla_roads_measure.py
  (the units test) and tools/tests/test_world_sample.py.
- Reader on 9 stills: inventory, charsheet, the System pane (both viewports) and the journal PASS.
- Magic and dialogue are "not paper": both are frame-style by design (theme.css). That is left to the owner's comparison of the two cards.
- The reader saw two marks on magic: the amber focus, plus a blue-filled Flames row. My unverified guess is that the
  blue fill is the readied spell, in --frame-select.
- Bottom rows clip at the scroll edge on v5. Tabs wrap unevenly on v5-unfolded. Both are polish.

## Owed in game
- checks.md: two owed rows.
- tests/journeys/menu-sweep.yaml, run twice: after `-Ui windui` and after `-Ui custom`.
- The load-screen step at the 2352x2172 stream.
