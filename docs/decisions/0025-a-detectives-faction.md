# 0025: A detectives' faction, rival to the Shadowscales and the Night-Reed Chapter

**Status:** decided 2026-10-27 (owner: "let's have a detectives faction! As rivals to those two. Solving murders
and thefts, with quests escalating up from petty crimes to some big grand murder mystery finale. It will need
to be grounded in lore and our lore extrapolation"; not to be created now, but planned so it happens at the
right point without the owner having to remember). Numbered 0018 on the side branch where it was recorded.

## Decision

1. **A new joinable faction** whose members solve crimes in Black Marsh, set against the Shadowscales (the
   assassins) and the Night-Reed Chapter (the thieves). Its name, founding, patrons and headquarters come from
   the lore pass below, not from this record.
2. **Its line escalates by case** from petty crimes to a **grand murder-mystery finale**. Its structure comes
   from the old repo's quest foundation and faction designs (imported in 0.1 §f), which already cover much of
   what such a line needs; the principles in `quest-write/principles/questlines.md` and `investigation.md`
   (and their research packs) are applied on top.
3. **Grounded in lore.** Before design, the lore pass reads the imported lore dossiers and the lore
   extrapolation (`world/sources/lore/`, `world/sources/lore/extrapolation/`) and the Shadowscales and
   Night-Reed records, and writes the faction's place in 4E 201 Black Marsh as an extrapolation entry with
   sources and confidence. Who would pay for detectives here, and why they are trusted, must have an answer
   the lore supports.
4. **Built with the writing skills** (decision 0024): a line record, then quest records through `quest-write`
   (MURDER, THEFT, FRAUD, MISSING and RECKONING principles), `quest-review`, then dialogue.
5. **The systems it needs ship whole in Part 2:** evidence-gated topics, presenting evidence, accusation and the
   rival factions' reactions. 0.1 §i checks what the imported quest system and condition vocabulary already
   cover; 2.5 and 2.12 build what is missing, since every MURDER, THEFT and FRAUD quest uses it too.

## When

- **0.1 §i:** the coverage check of investigation support.
- **2.4 §c:** the lore pass and the faction record (33 factions: the imported 32 plus this one).
- **2.5 §a, 2.12 §a:** the missing investigation support, whole.
- **4.1 §d:** the line record (ranks, cases per rank, recurring cast and rival, the finale and the clues seeded
  for it), reviewed by `quest-review`, written with the packet template so every region packet plans the cases
  it hosts.
- **4.2, 4.3:** cases are built in the packets that host them; the finale when its region's packet lands.
