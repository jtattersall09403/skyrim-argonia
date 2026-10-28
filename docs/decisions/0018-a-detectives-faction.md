# 0018: A detectives' faction, rival to the Shadowscales and the Night-Reed Chapter

**Status:** decided 2026-10-27 (owner: "let's have a detectives faction! As rivals to those two. Solving murders
and thefts, with quests escalating up from petty crimes to some big grand murder mystery finale. It will need
to be grounded in lore and our lore extrapolation"; not to be created now, but planned so it happens at the
right point without the owner having to remember).

## Decision

1. **A new joinable faction** whose members solve crimes in Black Marsh, set against the Shadowscales (the
   assassins) and the Night-Reed Chapter (the thieves). Its name, founding, patrons and headquarters come from
   the lore pass below, not from this record.
2. **Its line escalates by case** from petty crimes to a **grand murder-mystery finale**. Its structure comes
   from the old repo's quest foundation and faction designs (imported in P0-WP0.6), which already cover much
   of what such a line needs; the principles in `quest-write/principles/questlines.md` and `investigation.md`
   (and their research packs) are applied on top.
3. **Grounded in lore.** Before design, the lore pass reads the imported lore dossiers and the lore
   extrapolation (`world/sources/lore/`, `world/sources/lore/extrapolation/`, imported in P0-WP0.6) and the
   Shadowscales and Night-Reed records, and writes the faction's place in 4E 201 Black Marsh as an
   extrapolation entry with sources and confidence. Who would pay for detectives here, and why they are trusted,
   must have an answer the lore supports.
4. **Built with the authoring skills** (0017): a line record, then quest records through `quest-write` (MURDER,
   THEFT, FRAUD, MISSING and RECKONING principles), `quest-review`, then dialogue.
5. **Systems it needs ship whole in P4:** P4-WP4.0 checks that the imported quest system, condition
   vocabulary and journal design already cover evidence-gated topics, presenting evidence and accusation, and
   the rival factions' reactions, and adds only what is missing (WP4.8, WP4.18).

## When

- **P4-WP4.0, WP4.8 and WP4.18:** any missing investigation support, and the faction record (33 factions).
- **P7-WP7.6:** the lore pass and the line record are written with the P9 packet template, so every region
  packet plans the cases it hosts.
- **P9:** cases are built in the packets that host them; the finale is built when its region's packet lands.
