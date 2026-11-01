# 0032 — Every world call is grounded in the lore dossiers and the old research record

**Date:** 2026-11-01 · **Status:** accepted (owner ruling, the 1.15 planning conversation)

## Decision

1. **The lore dossiers are the ground for every world, place, people and quest call.** `world/sources/lore/`
   (the province, nine cities, six region dossiers, the topic sheets) and `world/sources/lore/extrapolation/`
   (the province in 4E 201, the gap register, the settlement register) are read before any such call is made, and
   the call cites them by tier (`CANON_EXPLICIT` / `CANON_DERIVED` / `EXTRAPOLATED` / `AGENT_INVENTED`, the lore
   README's rule). Where canon runs out, the extrapolation record answers; a gap is added to the gap register,
   never filled by an unsourced invention. Relief, climate, regions, cultures and what a place looks like are
   lore questions first and taste questions second.
2. **The old project's research record is imported whole** to `docs/design/research/` (source-map §2): the
   terrain, climatology, geomorphology, shoreline, vegetation, rendering, placement, lore-audit and region-review
   evidence the design modules cite. Until now only the combat folder and one lore note had come over, and the
   world design modules carried 35 dangling links to the rest.
3. **A lore claim an agent cannot find is checked against the dossiers' routers before it is called missing**:
   the lore README (filenames are the map), the province overview's router, the gap register and
   `docs/design/world/README.md`. "Not in the repo" is said only after those four and `world/IMPORTED_FROM.md`.

## Why

- The owner (2026-11-01): the border ranges are canon ("Velothi / Valus Mountains … jagged, elevated peaks curve
  near … Stormhold and Thorn"; "Cyrodiilic Uplands & Blackwood"), and the agent's "alpine, not Black Marsh"
  reading of the heightfield was taste overruling canon. "Relief profile should be answered from the lore/canon."
  "Have we set a golden rule about all our decisions being grounded in it? We must do both."
- The dossiers already say what the terrain must keep: Shadowfen is where relief lives (Silyanorn on a mountain
  flank around a waterfall, ravines); Murkmire slopes from the northern uplands to a drowned coast; the Deshaan
  border rises and dries toward Morrowind; the interior is low morass; Blackwood is higher, drier, red clay.
- The old repo's climatology and mountain-synthesis research is where the current 655 m relief came from; an agent
  that cannot read it cannot judge it.

## Consequences

- CLAUDE.md "How we build" carries the one-line rule. The planning record
  `docs/research/2026-11-01/world-rebuild-options.md` is amended: the relief profile is derived from the dossiers
  and the engine's slope limit, not from a "Black Marsh is flat" prior.
- `tools/import_old.py` owns `docs/design/research/` whole, less the old repo's ways-of-working folders
  (agent-ops, agents, engine, infrastructure, process, ui) and the Bethesda text corpus, which stays private.
