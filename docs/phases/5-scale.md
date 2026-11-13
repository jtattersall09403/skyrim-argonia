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
- **The world map, if Phase 4's W-wrld-map is not enough.** If the native map still shows Tamriel or draws BM&V
  bare after the MNAM and lodsettings fix, generate terrain and object LOD for the four worlds with xLODGen on the
  play machine from the owner's own files (nothing committed, decision 0003). A 2d parchment map with fog of war (the
  old repo's route: Flat World Map Framework, Nexus 29932, plus Flat Map Markers and our own fog-of-war chart over the
  map menu, `git show 93253542`) is days of work, needs a paper image per world (an owner ruling: we make no art) and
  its 1.7.104 support is unknown; only if the owner asks for it after seeing the native map.
- **Before release: the creature mods become masters (owner ruling 2026-11-12).** The creature mods whose records
  ArgoniaNewWorld.esm now copies (mods/sourcing-register.json rows with `permission_condition`) become real masters
  of our world file, their records referenced rather than copied, so their mods are dependencies of ours and none of
  their assets is shipped.

## Spellmaking, later (owner, 2026-11-13)

Morrowind let the player make spells of their own. The owner would like it back, unlocked through the story in a way
that belongs to Argonia, "later on, with it added to the plan". It needs a plugin of our own (allowed where no mod,
record or script does the job). The proposal, with what mods have done it and what ours would need, is at the end of
[choice-and-consequence](../research/writing/choice-and-consequence.md) once that note lands; nothing is built for
it before the owner picks it up.

