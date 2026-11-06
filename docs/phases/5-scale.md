# Phase 5 and on: scale

Status: [PROGRESS.md](../PROGRESS.md). The plan: [PLAN.md](../PLAN.md). Edit this file as the phase goes; it is the phase's whole brief.

*Write this phase plan after phase 4 is complete*. The goal is to take stock of where we are up to by this point, what has been proven to work from the building blocks, what kinds of minor edits to the BM&V world we can do reliably, and anything else that's relevant. Then we use that information to build out the scale plan, going through the rest of the main quest, the factions, minor quests, and any system overhauls/additional modifications the owner wants at this point (e.g. potentially UI, music). This will very likely become several phases - your goal will be to plan out the most sensible order in which to deliver them, based on dependencies, importance to the player, and risks.

The same blocks and skills, in the owner's order: the main quest's acts II and III and the three endings; the
four deep faction lines, then the standard ones and the detectives' faction
([0025](../decisions/0025-a-detectives-faction.md)); regional and standalone quests; bosses and creatures by danger
band; items. Each milestone is one owner test.

- **Loop**: design the loop architectures that agents should follow in these phases that you author at this point. e.g. from earlier phases: "read the files that the game will consume and verify (to the extent that you can) that everything you intended to implement has been implemented correctly. If not, diagnose, fix, then repeat this loop until your read of the built game files (esm and plugin and whatever else) does meet this bar. But do not run the actual game yourself, just read/mine from the game files that you build. *Then* pass on to the owner."
- **The wider minor questlines (placeholder, owner 2026-11-05).** After the authored lines are built, a build-out of new
  minor, regional and standalone quests for BM&V's places towards Morrowind's density (old design target: about 20
  quests per km²), planned at this point from what Phase 2's capacity measure and ledger show is free; written with the
  same skills and the same whole-set checks so they never clash with the authored lines.
- **The world map (owner, 2026-11-06: leave it until this phase).** The in-game world map is still Skyrim's map with
  BM&V's markers drawn on it, and Black Marsh North.esp's map marker for Lilmoth (`0934A4`) is named "Lolmoth". Make our
  own map of Black Marsh (or fix the one BM&V ships, if it has one) and correct the marker's name, as part of this phase.
