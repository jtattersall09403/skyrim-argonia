# 0042: The new world is the project

**Status:** decided by the owner, 2026-11-26.

## Context

The first week (2026-10-27 to 2026-11-05) built a total conversion with its own systems, UI and test harness. The
owner judged it failed and had it thrown away. From 2026-11-05 the project was our story modded onto the world of
the Black Marsh & Valenwood mod (BM&V), and from 2026-11-08 a second worldspace of our own, built from Project
Tamriel's map of Black Marsh, was made beside it. The BM&V version proved the mod stack, the quest form and its
blocks, the dialogue method and the way a story is fitted to a world. Its world covers only part of Black Marsh,
and by 2026-11-22 its quests had been retired in favour of the new world's main quest.

## Decision

1. **The project is the new world**: our own worldspace of the whole of Black Marsh, with the mod stack (vanilla
   Skyrim SE, the soulslike collection xyf1u3, FreeClimb, Magic Expanded), our story, quests, factions and places
   built in it. A new game goes straight into our own opening there, with no Helgen, and the vanilla systems that
   would carry Skyrim's story into it are shut down ([0012](0012-vanilla-skyrim-is-quarantined.md)). It is the one
   thing we deliver.
2. **BM&V is a mod we depend on, not the world.** Its places, with those of King of the Murkmire and Skyrim, are
   the source places ours are carried from ([0041](0041-a-place-is-its-source-carried-whole-and-adapted-by-hand.md)),
   and its pieces dress them. Its world, its people's talk and its quests get no more work; its plans are kept
   unedited in [docs/archive/](../archive/README.md).
3. **Process stays light**: agents avoid testing in game when the owner can, and post an owner check instead; each
   kind of change is proved once as a building block and the rest is built from it.
4. **Everything proved on the way stays**: the stack, the quest form and the generic builder, the skills, the place
   studio, the rulings and every other decision in this folder.

## Consequences

- The plan is [PLAN.md](../PLAN.md) and the phases are the new world's own files in [phases/](../phases/README.md),
  kept under their names and in the owner's words.
- The repo keeps the name "the new world" (`newworld/`, `tools/newworld/`) for the worldspace.
- Code that only served the BM&V version (its card, its talk tools, its quest records) is retired as a piece of
  work of its own, listed in [PROGRESS.md](../PROGRESS.md).
