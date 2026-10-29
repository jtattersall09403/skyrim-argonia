<!-- imported unchanged from elder-souls-argonia docs/decisions/0126-scene-states-on-layout-ops.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0126 — Scene states: a layout says which quest state each piece and socket belongs to

Status: accepted (16k walk 11, places-a lane). Data contract only; the
runtime switch belongs to the quest system (Phase 13).

## Context

MQ01 needs `STATE opening.camp={orderly,attacked,aftermath}`
([30-main-quest.md](../quests/30-main-quest.md) MQ01,
[25-quest-place-map.md](../quests/25-quest-place-map.md)): the camp's grave
stakes and dark uxith exist only in the aftermath, witness sockets only in
the attack. No layout op or socket could say which state it belongs to. The
typed vocabulary reads a local variant as `localVariantActive(location,
variant)` ([85-condition-vocabulary.md](../quests/85-condition-vocabulary.md) A6).

## Decision

1. A layout names its state key once, top-level `"stateKey": "<key>"`.
   A `place` or `socket` op may carry `"states": [<value>...]`; absent
   means present in every state. `states` is a layout-only key (never a
   CLI argument).
2. The key and values are checked against the quests' own declarations:
   `worldgen.scene_states.declared()` reads every `STATE key={...}` in
   `docs/quests/*.md`, so the quest docs stay the one home of the values.
   `workbench.layout.load` refuses an undeclared key, a value outside it,
   `states` without a key, or `states` on any other op.
3. The compile (`scene_states.apply`) writes `states` on every compiled
   placement the stated piece became (its parcel's building, its landmark,
   or its assembly member, by the layout's `bind` op) and on each stated
   socket, and `sceneStates {key, values}` on the place. The bundle export
   carries both (`states` on the placement contract, `sceneStates` on the
   site). The bundle `schemaVersion` is not bumped: both fields are
   optional and additive, and every existing record reads the same.
4. The runtime later shows a placement or socket when its `states` is
   absent or holds the place's active variant.

## Consequences

- Tests: `worldgen/test_scene_states.py`.
- Documented in the workbench rules (`wb.py explain`).
