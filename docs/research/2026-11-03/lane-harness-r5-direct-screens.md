# Lane harness-r5-direct-screens (2026-11-03)

Owner ruling: a screen under check is opened directly; a game action is driven only when the action is the thing checked.

## What the bridge offers (route 0010)
No open-menu-by-name, activate-by-id or barter command (skse/ArgoniaBridge/src: events, input, state, world, nav, dev only).
The engine console does: `<ref>.activate player` (no aim, no key). So the direct opener is that line plus an event check.

## New actions (tools/run_journey.py, linted, unit-tested)
- `show: <ref | {ref, menu, view}>`: console activate, up to 3 tries; fails unless a menu opens (the named one) or the view reads a body.
- `dialogue: <ref>`: NPC placed 110 u before the player (no turn, no aim), activate, holds on `ViewState dialogue`.
- `lockpick: <ref>`: console activate first (a script activate skips the lock, 151959, so it opens the container: closed), then
  the engine's own pick (`open`); fails unless a "Lockpicking Menu" opening is seen. UNPROVEN live: no Lockpicking opener exists in
  console or bridge, so the lockpick step still depends on the aimed E fallback. A true fix needs a bridge/Core command that shows
  LockpickingMenu on a ref (C++, game machine to prove): owed to the planner.

## Rewritten steps
menus-look `lockpicking` (lockpick), chart-zoom `speak-livia` (dialogue). chart-zoom `barter` already used the direct
`dialogue.service` ViewIntent and fails unless WindUIMenu opens within 8 s; its failure was the dialogue never opening, fixed by speak-livia.
Stills and expects kept.

## Classification of remaining crosshair steps (talk/open/strike/rest)
Screen-under-check (candidates to switch to `dialogue:` next): claywater-talk, magic-pane, ui-probe, ui-sweep (Livia), quest-board,
journal-dialogue, dialogue-intercept (intercept is the check: keep talk there), lf83-* (the quest facts are checked, dialogue is the
means: switch). Action-under-check (keep): strike (combat), rest (the rest action), dialogue-intercept, world-sample crosshair
reads (the crosshair is the check). Not switched here: the brief named three steps; switching needs a live run to prove each.

Test: tools/tests/test_run_journey.py (3 new), make check-reach green, --dry green for both journeys.
