# 0026: Places are rebuilt natively, the way Skyrim modding is meant to be done; the old project gives content, never machinery

**Status:** decided 2026-10-28. The owner, after the Claywater Station deep dive:
- "getting our old one to work properly in threejs was a nightmare. Really don't want to reverse engineer that
  whole bad patchy buggy system. Want to just do it properly in whatever way skyrim modding is intended to be done,
  from day 1."
- Asked whether to rebuild Claywater natively or convert its layout: "rebuild natively, and that's what we'll do
  for all places going forward as well".

## Context

The old repo built places in three.js from Skyrim and Skyrim-mod meshes. To make them stand up there, it grew its
own machinery: pads and settle, datums, snaps, mounts, binds and sockets as layout ops, kit compression, its own
water and mist shaders. Claywater Station alone is 381 layout ops. Converting those ops one for one into Skyrim
records would carry that machinery's faults into a host that already has its own native way of doing every part.

Every piece the old places used came from Skyrim or a Skyrim mod, so a native match always exists. The only open
cases are a mod we may not depend on, a mod that will not load on the pinned runtime, or a piece that looks
different under Tropical Skyrim's textures. That last one is a look check, not a missing piece.

## Decision

1. **What we take from the old repo is content:**
   - the frozen heightfield, the hydrology and where rivers run;
   - each place's design note, story and "why here?";
   - which pieces a place uses and roughly where they stand (the layout as a reference);
   - the people: records, homes, workplaces, daily routines, services and factions (§6).

   **We take none of its machinery:** no pads, settle, datums, snaps, mounts, binds, kit compression, three.js
   water or mist, and no converter that replays layout ops.
2. **Places are rebuilt natively, by an agent working the way a Skyrim modder works**, for Claywater Station and
   every place after it:
   - **Terrain** is LAND data from the heightmap, the same records the Creation Kit's heightmap import makes,
     with land textures painted by land-cover class.
   - **Ground under a building** is shaped by direct landscape edits in that place's cells, as a modder sculpts it
     in the CK. There is no overlay system. The edits belong to the place (old 0102 and 0140 still hold: a place
     carries its own ground and is edited in place by its own layer).
   - **Buildings and props** are ordinary placed references (REFRs) of the source plugins' base records, resolved
     by mesh path from plugin data, with load doors linked to their interiors (old 0114).
   - **Trees, rocks and scatter** are placed by region rules, as the CK's region generator places them.
   - **Then navmesh (§3), then distant LOD.**
   - **The design is the specification; the old layout is a guide.** The agent rebuilds the place from its design
     note, using the old positions as a reference. It judges vantage stills against the design and fixes until
     they match.
3. **Navmesh: tes4skyrim's method first.** It generates navmesh from the world's own collision, from code, so
   it fits the pipeline and scales to the province. Its compiled part runs on the Windows game machine. The
   Creation Kit's generator is the check and the fallback. The proving step comes first: round-trip one CK
   navmesh through Mutagen and confirm NPCs walk it, then generate.
4. **Water is Skyrim's own** (WATR records, cell water, placed planes, the vanilla rapids and falls pieces),
   tuned to look good with Community Shaders. Nothing reproduces the old water's look.
5. **Mist and light are Skyrim's and Community Shaders':**
   - outdoors, Community Shaders' volumetric lighting and fog, each weather's fog, and placed mist effects in
     hollows and over water;
   - indoors, sun shafts through windows that follow the sun are researched first (2.W3). If no current mod or
     Community Shaders feature gives them, **well-placed static light beams, set to the time of day, are
     accepted** (owner, 2026-10-28).
6. **People carry over from the old repo wholesale, then get reviewed:**
   - their records, homes, workplaces, routines and services are imported as data;
   - their dialogue is rewritten by the writing skills (0024).

   **Whole-body templates.** An NPC's appearance comes from one template NPC that supplies race, head parts,
   skin, weight and height together (TPLT with the traits flag), never a face alone. The owner hit face and body
   mismatches before. Each person gets a full-body still, and a reader checks it for neck seams and skin-tone
   mismatches.

## Consequences

- 0.2 G4 builds the Claywater block natively under these rules, and it is kept as Part 1's place. Its
  "every layout op resolves" check is replaced: every piece the design uses resolves to a base record (L1).
- 0.5's kit-id mapper becomes a **piece resolver** (old kit id or mesh path → source plugin and base record, read
  from plugin data). It is a lookup the builder uses, not a converter.
- 2.W5 and 4.2 rebuild every place by the same recipe; the `world-builder` skill holds it.
- 0018 still holds: records are written by code, and the CK is a scripted tool. Its CK jobs run on the Windows game
  machine rather than under Wine.
- The risk "a piece has no match in Skyrim" is dropped from every brief.
