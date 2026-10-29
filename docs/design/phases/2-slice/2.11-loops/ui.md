<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.11-loops/ui.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Quest UI screens (2.11 ui-gaps)

Code: `packages/ui/src/screens/` (Factions, Journal, Dialogue join terms, PauseDeck), `packages/ui/src/map/` (granted markers, directions note), `packages/ui/src/hud/` (quest and system notices), `packages/scene/src/narrative/views.ts` (view builders), `packages/scene/src/ui/boundaryNotice.tsx`. Fixtures in `apps/ui-lab/src/screens/`.

## The rule

- Every gap in `lanes/2.11-ui-crawl/table.md` is built in `packages/ui` and shown in ui-lab. Each screen is shown on desktop, phone, fold-inner and fold-outer, in light and dark, with touch, pad and mouse.
- The screens read the session narrative only. `views.ts` turns stores into plain view data (`journalViewOf`, `factionsViewOf`, `grantedMarkersOf`, `favoursOf`, `questNoticeListener`, `narrativeScreensOf`); no screen writes a store (0149).
- The journal lists quests in the order of their first journal entry (`atMinute`, then entry order). Quests with no entry follow, by id. A load does not reorder them, so the seams compare the journal strictly (`packages/scene/src/testing/narrativeSeams.ts`).
- Both apps mount one recipe:
  - The studio uses `walkNarrativeDeps` plus `narrativeJoins` (`apps/world-studio/src/character/CharacterMode.tsx`).
  - The game uses `gameNarrativeDeps` (`apps/game/src/GameWorld.tsx`).
- The edge-of-the-province line is a `system` HUD notice (`BoundaryNotice`), with cue `cue.hud.notice-system`.

## Eyes

- `ui_lab_check.mjs` runs the automatic bars:
  - layout (clip, overflow, overlap, hinge);
  - token lint;
  - pad focus order;
  - open time;
  - catalogue resolution.
- `reader` agents judge the shots each round (`lanes/2.11-ui-gaps/reader-*.md`).

## Measured

| Measurement | Bar | Result | Elapsed | Capture |
|---|---|---|---|---|
| ui-lab check, 10 new screens | every automatic bar | PASS, 150 shots | 348 s | tooling/.reports/ui-lab/shots/ |
| ui-lab check, round-3 fixes (8 screens) | every automatic bar | PASS | 258 s | same |
| `npm test -w @elder-souls/ui` | all green | 426/426 | 24 s | |
| ui-lab vitest | all green | 2/2 | 9 s | |
| scene narrative vitest | all green | 53/54; the red is a dialogue-data seam (tag-keeper does not open), outside this lane | 17 s | |
| reader rounds | every screen PASS | see `lanes/2.11-ui-gaps/report.md` | | reader-r3.md |

## Not yet published to the browser

- The apps pass these as empty because nothing publishes them to the browser yet:
  - quest records;
  - the marker catalogue;
  - overlay places;
  - hostility blocks;
  - the documents registry.
- The publish belongs to the quest-data publish step.
- Favours feed the narrative but are not on the sheet in the apps: there are no person or service name text ids yet.
