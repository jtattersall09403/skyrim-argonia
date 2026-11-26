# 0042: The new world is the project; the Black Marsh & Valenwood version is retired

**Status:** decided by the owner, 2026-11-26. Supersedes [0038](0038-the-pivot-bmv-is-the-world.md).

## Context

From 2026-11-05 the project was our story modded onto the world of the Black Marsh & Valenwood mod (BM&V), and
from 2026-11-08 a second worldspace of our own, built from Project Tamriel's map of Black Marsh, was made beside
it. The BM&V version did what it was for: it proved the mod stack, the quest form and its blocks, the dialogue
method and the way a story is fitted to a world that already exists. Its world covers only part of Black Marsh,
and by 2026-11-22 its quests had already been retired in favour of the new world's main quest.

## Decision

1. **The project is the new world**: our own worldspace of the whole of Black Marsh, with the mod stack, our
   story, quests, factions and places built in it. It is the one thing we deliver.
2. **The BM&V version is retired.** No more work goes into its world, its people's talk or its quests. Its
   plans are kept unedited in [docs/archive/](../archive/README.md).
3. **BM&V stays as a mod we depend on**: its places, with those of King of the Murkmire and Skyrim, are the
   source places ours are carried from ([0041](0041-a-place-is-its-source-carried-whole-and-adapted-by-hand.md)),
   and its pieces dress them.
4. **Everything proved on the way stays**: the stack, the quest form and the generic builder, the skills, the
   place studio, the rulings and every other decision in this folder.

## Consequences

- The plan is [PLAN.md](../PLAN.md) and the phases are the new world's own files in [phases/](../phases/README.md),
  kept under their names and in the owner's words.
- The repo keeps the name "the new world" (`newworld/`, `tools/newworld/`) for the worldspace.
- Code that only served the BM&V version (its card, its talk tools, its quest records) is retired as a piece of
  work of its own, listed in [PROGRESS.md](../PROGRESS.md).
