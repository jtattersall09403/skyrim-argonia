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
- Test: tools/argonia_world/tests/test_loading_weights.py simulates 1,000 loads with the engine's uniform pick over
  the eligible LSCRs. The crocodile is 1 of 12 rows (~8%) and no mesh is over a third.
- The data does not explain "almost always crocodiles". The in-game read of which LSCR shows is owed.
- The Hist subject is 5 of 12 rows (~42%). Its test is a strict xfail: a content call for the planner.
- The squash is in loadingmenu.swf (Flash), so the HTML harness cannot show it. It is owed as a still at the
  2352x2172 phone viewport.

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

## Inventory and character sheet views (finding 7), built by a child agent
- New views ui/views/{inventory,charsheet}, with their schema and fixtures; the C++ header is regenerated.
- Inventory: 10 category tabs that LB/RB cycle (pad-only glyphs at the row's ends), a list with an empty icon slot
  per row, an always-shown detail panel with Use/Drop, and a carry-weight bar with gold.
- Character sheet: Attributes/Skills/Perks tabs, a side column (level, pools) and a one-line description of the
  focused row.
- The pad layout borrows methods from OpenMW (research agent, source studied and deleted):
  - inventorywindow.cpp:1060-1084 (LB/RB tabs), :140-153 (pad glyphs);
  - itemview.cpp:228-250 (d-pad in the item view);
  - windowmanagerimp.cpp:2782 (button legend);
  - statswindow.cpp:736 (a read-only sheet with no row focus: ours adds row focus).
- Not yet: the views are not in skse/core/include/argonia/core/views.h kViews, and ArgoniaCore does not route
  InventoryMenu or StatsMenu to them. Until it does, the custom card shows SkyUI there. X (Drop) needs a nav action.

## Harness evidence
- Loop: 28 runs, 0 fails, 32.2 s.
- `--smoke`: 0 fails. `make ui`: 23/23. `make check-reach`: green.
- Full `python -m tools.ui_harness`: 16 fails, all in existing views (child's run), none in the new ones.
- Reader on 9 stills: inventory, charsheet, the System pane (both viewports) and the journal PASS.
- Magic and dialogue are "not paper": both are frame-style by design (theme.css). That is a call for the owner.
- The reader saw two marks on magic: the amber focus, plus a blue-filled Flames row. My unverified guess is that the
  blue fill is the readied spell, in --frame-select.
- Bottom rows clip at the scroll edge on v5. Tabs wrap unevenly on v5-unfolded. Both are polish.

## Owed in game
- checks.md: two owed rows.
- tests/journeys/menu-sweep.yaml, run twice: after `-Ui windui` and after `-Ui custom`.
- The load-screen step at the 2352x2172 stream.
