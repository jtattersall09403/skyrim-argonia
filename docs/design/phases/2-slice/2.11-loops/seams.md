<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.11-loops/seams.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 2.11 seams (level 4)

Every § Seams row of [2.11-quests-journal-map](../2.11-quests-journal-map.md) as a scripted headless session in
`packages/scene/src/narrative/seams-session.test.ts` (scene runner, `walkNarrativeDeps`) and
`apps/game/src/seams-session.test.ts` (game runner, `gameNarrativeDeps`). The rows, the rig and the fixture quests
live in `packages/scene/src/testing/narrativeSeams.ts` and `seamQuests.json` (fixture quests, no per-quest code).
Each session stages the blocks below it (stores, catalogues, Claywater's dialogue bundle), plays only its join, and
ends in `roundTrip`: snapshot, restore into a fresh rig, snapshot again, compare equal, and compare the journal view.
Each row is proved red by cutting its one join (`SeamJoin`); the break is named below.

## Seam table

| Seam | Join played | Break that proves it red |
|---|---|---|
| talk → stage → journal → notice | `dialogue-commits-to-quests` | the dialogue host built without its `quest` (a chosen topic commits knowledge only) |
| talk → stage → journal → notice (the notice) | `quest-events-raise-notices` | the session's `listen` not wired to the HUD notice queue |
| stage → flag → place stance → greeting | `stance-blocks-published` | the walk's stance view given no hostility blocks (`block: () => undefined`, as the apps pass today) |
| complete → favour paid → price | `walk-favours-to-narrative` | the session built without the walk's favours store (`favours` undefined, as the studio passes today) |
| complete → rank → sanctuary | `derived-stance-to-disposition` | `answeredDisposition` called without the narrative's derived stance (the walk passes none today) |
| stage → overlay → refs | `overlay-places-published` | the walk's overlay given no places (`overlay: { places: [] }`, as the apps pass today) |
| discover → journal link → map pin | `discovery-to-quest-reads` | the quest world's `discovered` not reading the discovery tracker |
| grant marker → map | `marker-catalogue-published` | the walk's marker catalogue empty (`markers: { catalogue: [] }`, as the apps pass today) |
| clear a place → placeCleared → stage | `amends-clear-stance` | the crime walk's `onPlaceCleared` not wired to the stance view (no app passes it today) |
| steal → ledger → crime quest stage | `ledger-to-quest-reads` | the quest world's `owing` not reading the crime ledger |
| read document → knowledge → topic → stage | `documents-teach-topics` | the read not joined to the documents' `teaches` (documents.json has no such field and the item session's read teaches nothing today) |
| opening and closing the journal, map and factions screens from play | `narrative-to-pause-deck` | the pause deck built without the narrative screens (no `granted` or `factions`) |
| every stage of every authored quest → save → load → equal | `narrative-families-saved` | the quests family left out of the save registry (`everyStageSaves`, from every save point of the world scripts) |

## Verb × seam

| Verb | Seam rows |
|---|---|
| talk | talk → stage → journal → notice; talk → stage → journal → notice (the notice); stage → flag → place stance → greeting; opening and closing the journal, map and factions screens from play |
| collect | complete → favour paid → price; stage → overlay → refs |
| deliver | complete → favour paid → price |
| clear | clear a place → placeCleared → stage |
| steal | steal → ledger → crime quest stage |
| enter a hostile place | stage → flag → place stance → greeting; complete → rank → sanctuary |
| pay a favour | complete → favour paid → price |
| walk a direction | discover → journal link → map pin; grant marker → map; opening and closing the journal, map and factions screens from play |
| discover | discover → journal link → map pin |
| read | read document → knowledge → topic → stage |

## Gaps the seams name (the apps' composition today)

- The game composes no narrative: `gameNarrativeDeps` exists, GameWorld does not mount it.
- The studio passes no favours, stance blocks, overlay places, markers or quests; `onPlaceCleared` and the derived stance are unwired (`narrativeJoins` holds the wiring).
- documents.json carries no `teaches`; the item read teaches nothing.
- The journal lists quests in key order (`views.ts:33`), which a load sorts: the list reorders after a load. Owner: the 2.11-ui-gaps lane; the round trip compares quests as a set until it lands.
