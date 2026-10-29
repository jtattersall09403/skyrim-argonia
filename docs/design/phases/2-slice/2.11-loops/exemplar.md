<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.11-loops/exemplar.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Exemplar quest (2.11 e)

LF83, the two charges at Claywater Station (`quest.local.lf83`), authored whole as data; the recipe it
produced is [docs/quests/87-written-quest-recipe.md](../../../quests/87-written-quest-recipe.md).

- Logic: `world/sources/quests/local-imperial-fringe.json` (stages 10, 20, 30 complete, 90 failed).
  Advances on `topicHeardFrom`; fails forward when either keeper dies.
- Words: topics, facts, pool lines and Livia's and the poler's overrides under `world/sources/dialogue/`;
  journal and objectives in `world/sources/text/journal/local-imperial-fringe.json`, compiled to
  `packages/text-catalogue/src/generated/journal-text.ts`.
- Gates: `worldgen.quests --check` 0 errors; prose linter green on both files; text-reviewed by a reader.
- Driver: `packages/narrative/src/data/scripts/lf83.json`, played by the one host (`driver/worldHost.ts`)
  through the published dialogue bundles from a new game and every save point (complete, poler dies,
  Livia dies); `worldHost.test.ts`, `driver/cli.ts`.
- Tools changed on the way: `dialogue_lines` makes every `topicHeardFrom` topic a speaker's required
  topic; `dialogue_rewrite` keeps a quest-conditioned derived line and does not re-judge kept answers
  against a moved pool line; `place_text` emits journal text; the driver takes `opening` and `asks`.
