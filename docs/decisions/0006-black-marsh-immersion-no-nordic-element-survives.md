# 0006: Black Marsh immersion: no Nordic element survives; Pelagiad, new music, a 100% audit; Fal for minor art

**Status:** decided 2026-10-27 (owner: "It will be very immersion breaking for there to be Nordic design
elements sneaking into our Black Marsh game"; wants Pelagiad throughout, new music, a full audit and overhaul
of UI and art elements, an agentic approach that covers everything 100%; Fal allowed for minor new art).

## Decision

1. **The immersion inventory.** Every player-perceivable element is a row in one generated inventory
   (`data/immersion/inventory.jsonl`), produced by enumerating, not by searching:
   - every record our load order can show the player (WEAP, ARMO, MISC, BOOK, NPC_, CREA-equivalents, STAT,
     FURN, ACTI, DOOR, CONT, LIGH, FLOR, TREE, GRAS, LTEX, TXST, WTHR, CLMT, IMGS, SOUN/SNDR, MUSC/MUST,
     MESG, GMST strings, LSCR loading screens, SPEL/MGEF names and icons, PERK, RACE, CLAS, FACT, QUST,
     DIAL/INFO, WOOP, SHOU, LCTN, REGN, VTYP voice types);
   - every UI surface (each vanilla menu SWF in the pinned set, each PrismaUI view, the main menu, loading
     screens, HUD, fonts, icons, cursor, message boxes);
   - every audio surface (music tracks and types, ambience, UI sounds, combat barks, NPC voice types,
     creature sounds);
   - every text surface (strings shown anywhere, item names, book texts, loading tips).
   Each row carries: source (plugin/file), where the player can meet it, a **verdict** (`keep` /
   `restyle` / `replace` / `hide` / `remove`), the replacement's id, evidence (screenshot path or record
   diff), and the check that proves it.
2. **Coverage is measured, not believed.** The gate fails if any reachable row has no verdict, or a
   `replace`/`hide`/`remove` row has no passing check. Reachability comes from our own load order and the
   world (what is placed, sold, dropped, spawned or shown), computed by the generator.
3. **Visual judgement** is done by independent `reader` agents on in-game captures with a Nordic-tells
   checklist (knotwork, dragon motifs, Nordic runes, horned helmets, Skyrim seal, Sovngarde/Dragonborn
   wording, snow/pine palettes, Nordic voice accents) and by the owner on sampled packets.
4. **Font:** **Pelagiad** (SIL OFL; OpenMW's free twin of Magic Cards) everywhere: vanilla menus via
   `fontconfig.txt`/font SWF replacement, PrismaUI views via web font. Shipping Pelagiad is permitted by OFL
   with its licence file.
5. **Music:** new music for every music type (explore by region and time, combat, dungeon, town, menu,
   death, discovery). Sources in order: (a) permissively licensed existing music (CC0/CC-BY, credited);
   (b) owner-commissioned; (c) Fal-generated, with the AI-use constraints below. Vanilla Skyrim music never
   plays.
6. **New art:** UI elements and minor tweaks only (owner rule). Restyling existing meshes by retexturing is a
   "tweak"; new meshes are not made. **Fal** may generate minor 2D art (icons, UI ornaments, the paper map
   base, loading-screen paintings, book illustrations) when no sourced asset fits. Every Fal output is
   recorded with its prompt and model in the sourcing register.
7. **AI-use constraint.** Some mod authors forbid use of their assets in mods "that make use of AI" (King of
   the Murkmire's terms), and Nexus requires AI-content disclosure (since 2026-07-31). Argonia's code, text and
   any Fal art are AI-made, so: the sourcing register records each dependency's AI clause; any mod whose terms
   forbid AI-made companions is either cleared in writing by its author or dropped (docs/legal-and-sourcing.md).
   The Nexus page discloses AI use.

## Consequences

- The immersion audit is a cross-cutting track (T-IMM in [PLAN.md](../PLAN.md)), not one late phase: the
  inventory exists from P2, every phase's new elements enter it, the slice (P7) and every content packet
  (P9) pass it, and P8 drives the whole inventory to 100% before release.
- Vanilla Skyrim *systems* that are Nordic by nature (dragons, shouts, Dragonborn, Sovngarde, Helgen, the
  civil war) are handled by decision 0012.
