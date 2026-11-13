# The block test: the agents' diagnostic for the generic quest scripts

Two small quests that between them use every kind of step a quest form can hold, once each:
`tools/questform/blocktest/blocktest.json` ("Block Test", `ARG_BlockTest`) and `blocktest-two.json` ("Block Test,
the Second", `ARG_BlockTestTwo`). They prove the builder, the reader and the generic scripts (`ARG_QuestStages`,
`ARG_Effects`, `ARG_LineEffects`, `ARG_AliasEffects`) on one quest the agents control, including the operations no
real quest uses yet. They are never in the shipped plugin: the first starts at the first moment of every new game,
so a plugin holding it puts a test quest in every player's journal. The owner's walk is real quests only
([owner-walk-checks](../owner-walk-checks.md) section 12, with its table of which step proves which operation).

## Building it in

- **Off game, every time:** `bash tools/ArgoniaPlugin/plugin.sh questform-test` seeds the two forms and the example
  opening into a scratch plugin, reads it back, compares it with the forms and runs questcheck on it. The gate
  (`make check`) checks both forms alone and as a set.
- **In game, to diagnose a fault:** `bash tools/ArgoniaPlugin/plugin.sh seed --blocktest` (or
  `QUESTFORM_BLOCKTEST=1` for the seed tool) builds the eleven quests and the block test into `plugin/Argonia`. That
  tree is never committed or deployed to the owner's game: seed again without the flag before anything ships.

## What each step proves

Start a new game and walk east along the shore from the barge's pier, about 350 m, to Lilmoth's fishing dock. Steps 1
to 9 in one game, in order; 10 and 11 each in a game of their own.

| Step | Do | Proves |
|---|---|---|
| 1 | Wait on the dock | a person who speaks first (the force-greet), a speaks-first line's results as it begins (give gold, give an item, a message box), a start by the game at a shown stage |
| 2 | Look at the compass, the map, the keeper and the barrel | objective markers on a person and on a thing in a container |
| 3 | Take the token from the barrel | a take trigger (the game's own script) and its message |
| 4 | Ask the keeper the three questions | lines gated on having spoken before, the player's race and the player's sex |
| 5 | Hand in the token; ask to be made a senior hand; ask about the crab | take an item, set and add to a number, join a faction; a line gated on faction, rank, number, skill and stage, setting a rank and changing regard; switch a creature on, unlock a door |
| 6 | Kill the mudcrab in the ship; ask the keeper about the crab | a death trigger; lines gated on a person alive and dead |
| 7 | Leave the ship by its door | a use trigger; one quest starting another (StartQuest) |
| 8 | Talk to the walker, then the keeper, then the walker | a quest moved by another quest's stage; a line gated on the speaker, regard, rank and gold, taking gold; lock a door, switch off, a message; a quest completed |
| 9 | Speak to the keeper once more | a line open only after the quest has ended |
| 10 | Make the walker fight; kill her | the speaker turning hostile; a minor quest failed by a death with no message |
| 11 | Save on the dock, kill the keeper, load | the death watch's faction message, the failed ending, the message shown once |
