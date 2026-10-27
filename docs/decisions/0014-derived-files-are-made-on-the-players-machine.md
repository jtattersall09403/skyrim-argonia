# 0014: Anything derived from game or mod files is made at runtime or on the player's machine, never shipped

**Status:** decided 2026-10-27 (from the independent plan audit; follows from 0003).

## Context

Several techniques the plan needs produce files *derived* from Bethesda or mod files: FaceGen heads and tints
for new NPCs, distant LOD meshes and texture atlases (xLODGen/DynDOLOD), behaviour files (Pandora), re-timed or
re-annotated animations (annotations live inside `.hkx`), silent voice files for text-only lines, restyled
vanilla menus (Scaleform `.swf`), and a font library built into Skyrim's font SWF format. Decision 0003 forbids
shipping any of these; the no-assets guard refuses their extensions. Morroblivion's installer ("deploys
converted material from the user's own games") is the community precedent: tolerated, not licensed.

## Decision

1. **Order of preference for every derived need:** (a) avoid the file entirely (runtime behaviour, data, or a
   dependency mod that does it at runtime); (b) author our own original file from scratch (allowlisted, our
   copyright); (c) generate it on the player's machine with the installer from their own files; never (d) ship
   a derived file.
2. **Animation timing (P5):** (a) runtime: our SKSE plugin scales playback speed inside measured windows (graph
   variables, Payload Interpreter/AMR, animation-event-driven speed changes) and opens/closes our own timing
   windows from animation events, so DS1 timings are met without editing clips; (c) if a window cannot be met at
   runtime, an **install-time patcher** applies our annotation/timing deltas (a small diff we author) to the
   player's own copy of the clip. Proven in P1 gate G9 on one roll, one attack and one parry.
3. **FaceGen (P1-S4, P9).** Skyrim's engine does draw faces itself, but for NPCs it draws them from FaceGen files
   the Creation Kit pre-bakes per NPC (a head mesh and a tint texture); an NPC without them gets the "dark face"
   bug. Only the player's face is built live (the race menu). So: (a) **template NPCs** (TPLT) that reuse the
   faces Skyrim and our dependency mods already ship (no new files: the default for most of Argonia's cast);
   (c) for unique faces, an installer step that generates heads from the player's own head parts. Chosen in G4.
4. **LOD (P3-WP3.8).** Skyrim's engine draws distant land and objects itself, but from pre-generated LOD files
   per worldspace; a new worldspace has none, so its distance would be empty. **Terrain LOD meshes** are built
   only from our own heightfield, so they are our data and may ship; **terrain LOD textures** are made from land
   textures (Tropical Skyrim, mods, vanilla), so the installer generates them with xLODGen (light). Object/tree LOD: the
   installer runs DynDOLOD or ships only our own LOD *settings*, with documented RAM/time; for the owner's GPU box
   we run it there. If player-side object LOD is too heavy, ship without object LOD and record the visual loss.
   Measured in P3-WP3.8.
5. **Behaviours:** Pandora runs on the player's machine (already the plan).
6. **Silent voice lines:** (a) the PrismaUI dialogue view shows text without audio; for any line still on the
   vanilla path, the **Fuz Ro D-oh** dependency (runtime silent-line timing) instead of generated files.
7. **Menus and fonts:** every major screen and the HUD are our own original PrismaUI views (decision 0017). For
   any remaining vanilla screen, in this order: (a) a PrismaUI replacement; (b) our own original SWF written
   from scratch (allowlisted) and injected through Infinity UI or loaded as a replacement menu file of our own
   making; (c) an installer-time patch of the player's SWF. The **font library** (Pelagiad compiled into our own
   `fonts_*.swf` plus our own `fontconfig.txt`) is our file (OFL font, our build): allowlisted. Tooling: JPEXS
   FFDec (Java, Linux) to inspect vanilla SWFs and build our own; acceptance for any SWF is an L4 screenshot sweep.
8. **The guard** stays strict: only allowlisted files of our own making pass; release file lists are checked
   (P10-WP10.1); installer outputs never enter the repo or a release.

## Consequences

- The installer (P2-WP2.3, P10-WP10.2) grows steps: FaceGen (if needed), LOD, behaviours, animation patcher (if
  needed), SWF patches (if any). Each is a scripted, logged, re-runnable step on the player's machine.
- The owner's GPU box is installed by the same installer, so it exercises the player path.
