# 0040 Place records fit the story and the ground; sources serve the record

Date: 2026-11-19 (#80). Status: accepted.

## Context

The owner found the Act I drafts far from their records, a capital (Helstrom) with 17 people, a town (Jal-Veesa)
drafted from an Imperial stone fort, and Hist pools of plain water. An audit of all 258 place records
(`~/.argonia/audit/`, re-runnable) grouped 405 findings by cause. The owner ruled: no place moves; the main quest
is delivered as he authored it; the record is the brief; sources make places easier to build; a Hist pool is sap;
fix causes, never symptoms.

## Decisions, one per cause

1. **Population.** A record's population is the researched estimate inside its settlement tier's range, never the
   source's people count. The database build stops overwriting it (`tools/newworld/build_db.py`, the
   `population_after` path); the 47 records off their tier and the 6 out of order with their peers take the
   estimate; tiers order capitals and cities above towns above villages above outposts. A draft fills its people to
   the record; a small source is topped up, never the record cut down.
2. **Water and siting.** A record's water words name only water the ground has within reach (the Atlas raster and
   the built world agree, or the world is the fault). The 9 places with marginal claims and the 8 stale `on_water`
   flags are corrected in the record; place-research checks claims against the ground before writing them.
3. **Hist pools.** Every Hist pool in a record and a draft is a pool of Hist sap (the sap stage). Five records
   are reworded.
4. **Sources.** The allocated source is a first idea. Each place the main quest uses is re-judged now (place-build,
   "Choose the source") and takes its closest match or is built from the asset pool; every other place's source
   note is rewritten as a first idea that names its closest match or says "from the pool". The allocation is not
   recomputed.
5. **Disposition and gives.** A friendly place gives no fights inside it (its fights move to the dangers near it);
   a hostile or abandoned place offers no services; a second treasure is kept only where the record gives a reason.
   The 44 places are corrected and place-research checks this when it writes.
6. **The Atlas.** Symbols, tiers, roads and regions are read from the corrected records; the 7 that disagree are
   fixed at their record, then the Atlas and the story explorer are republished.
7. **The story.** The main quest is fixed (main-plot.md and the MN records); records and drafts are fitted to it.
   Other lines' overviews and quests are checked against the corrected records and take only the changes the
   records force.

## Consequences

The research skill and the database build hold decisions 1 to 5 as rules, so no new record repeats the faults.
The Act I drafts are finished against the corrected records.
