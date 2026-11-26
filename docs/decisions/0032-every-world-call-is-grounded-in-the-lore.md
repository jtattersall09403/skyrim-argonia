# 0032: Every world call is grounded in the lore dossiers

**Status:** decided 2026-11-01 (owner ruling, the world-rebuild planning conversation).

## Decision

1. **The lore dossiers are the ground for every world, place, people and quest call.** `story/lore/` (the
   province, its cities, the regions, the topic sheets) and `story/lore/extrapolation/` (the province in 4E 201,
   the gap register, the settlement register) are read before any such call is made, and the call cites them by
   tier (`CANON_EXPLICIT`, `CANON_DERIVED`, `EXTRAPOLATED`, `AGENT_INVENTED`, the lore README's rule). Where canon
   runs out, the extrapolation record answers; a gap is added to the gap register, never filled by an unsourced
   invention. Relief, climate, regions, cultures and what a place looks like are lore questions first and taste
   questions second.
2. **A lore claim an agent cannot find is checked against the dossiers' routers before it is called missing**: the
   lore README (filenames are the map), the province overview's router and the gap register, then
   `tooling/plan_find.py`. "Not in the repo" is said only after those.

## Why

The owner (2026-11-01): the border ranges are canon ("Velothi / Valus Mountains ... jagged, elevated peaks curve
near ... Stormhold and Thorn"; "Cyrodiilic Uplands & Blackwood"), and an agent's "alpine, not Black Marsh" reading
of the heightfield was taste overruling canon. "Relief profile should be answered from the lore/canon." The
dossiers already say what the terrain must keep: Shadowfen is where relief lives; Murkmire slopes from the northern
uplands to a drowned coast; the Deshaan border rises and dries toward Morrowind; the interior is low morass;
Blackwood is higher, drier, red clay.

## Consequences

- CLAUDE.md "How we build" carries the one-line rule.
