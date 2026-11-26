# 0014: Anything derived from game or mod files is made at runtime or on the player's machine, never shipped

**Status:** decided 2026-10-27 (from the independent plan audit; follows from [0003](0003-nothing-shipped-that-players-do-not-own.md)).

## Context

Several techniques we need produce files derived from Bethesda or mod files: FaceGen heads and tints for new NPCs,
distant LOD meshes and texture atlases (xLODGen, DynDOLOD), behaviour files (Pandora), re-timed or re-annotated
animations, silent voice files for text-only lines, and restyled vanilla menus. Decision 0003 forbids shipping any
of these; the no-assets guard refuses their extensions.

## Decision

1. **Order of preference for every derived need:** (a) avoid the file entirely (runtime behaviour, data, or a
   dependency mod that does it at runtime); (b) author our own original file from scratch (allowlisted, our
   copyright); (c) generate it on the player's machine with the installer from their own files; never (d) ship a
   derived file.
2. **FaceGen.** Skyrim draws an NPC's face from FaceGen files the Creation Kit pre-bakes per NPC; an NPC without
   them gets the "dark face" bug. So: (a) template NPCs (TPLT) that reuse the faces Skyrim and our dependency mods
   already ship, the default for most of our cast; (c) for unique faces, an installer step that generates heads
   from the player's own head parts.
3. **LOD.** A new worldspace has no pre-generated LOD, so its distance would be empty. Terrain LOD meshes are
   built only from our own heightfield, so they are our data and may ship. Terrain LOD textures are made from land
   textures (Tropical Skyrim, mods, vanilla), so the installer generates them with xLODGen. Object and tree LOD:
   the installer runs DynDOLOD, or ships only our own LOD settings; on the play machine we run it ourselves
   (`world-lod`). If player-side object LOD is too heavy, we ship without it and record the visual loss.
4. **Behaviours:** Pandora runs on the player's machine.
5. **Silent voice lines:** for any line on the vanilla dialogue path, the Fuz Ro D-oh dependency (runtime
   silent-line timing) instead of generated files.
6. **Menus and fonts:** the font library (Pelagiad compiled into our own `fonts_*.swf` plus our own
   `fontconfig.txt`) is our file (OFL font, our build) and is allowlisted. Any other vanilla menu change is our own
   original file written from scratch, or an installer-time patch of the player's own file.
7. **The guard** stays strict: only allowlisted files of our own making pass; release file lists are checked;
   installer outputs never enter the repo or a release.

## Consequences

- The installer grows steps: FaceGen (if needed), LOD, behaviours, SWF patches (if any). Each is a scripted,
  logged, re-runnable step on the player's machine.
