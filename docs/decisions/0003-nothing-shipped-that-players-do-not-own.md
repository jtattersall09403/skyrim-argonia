# 0003: The repo is public and ships only our own code and data; players supply every game and mod

**Status:** decided 2026-10-27 (owner: distribution "must only be playable if you own the base game(s)";
"public repo, it holds us to account to make sure we never put anything in it that we shouldn't").

## Decision

1. **The repo and every release contain only:** our source code, our own original data (records we
   generate, text we write, configuration), our original UI assets and permitted fonts (Pelagiad is OFL),
   permitted Fal-generated minor art (decision 0006), docs, and tests.
2. **Never in the repo, a release, a CI artifact, an issue attachment or a published screenshot bundle:**
   - any Bethesda file (meshes, textures, sounds, voice `.fuz`, music, plugins, strings), converted or not;
   - any third-party mod file (meshes, textures, animations, scripts, plugins), converted or not, unless its
     licence explicitly allows redistribution in a derivative and the sourcing register says so;
   - any FromSoftware file or data table (params, TAE, AI scripts, animations, meshes), converted or not;
   - decompiled code or disassembly from any game, retail offsets or decompiler names copied into code
     (CommonLibSSE-NG and Address Library IDs are the community interfaces and are fine);
   - credentials, Steam/Nexus keys, or the owner's game files.
3. **Owned-game ownership is implicit:** our master plugin requires `Skyrim.esm` and the official BSAs from the
   player's Data folder. Morrowind and Dark Souls Remastered/3 are **knowledge sources only** (decision 0004):
   nothing from them is needed at runtime.
4. **Third-party mods are dependencies the player downloads** (Nexus, ModDB) through the installer or a
   Wabbajack/Jackify modlist (P10). We reference their records and mesh paths from our plugin; we do not copy
   their files. Where a mod's terms forbid *requiring* it in another mod or using it with AI-made content,
   we ask the author or drop it (docs/legal-and-sourcing.md).
5. **Enforcement:** a committed `tooling/guards/no_assets.py` (P0-WP0.3) runs in the gate and as a pre-commit
   hook: it refuses binary asset extensions (`.nif .dds .hkx .bsa .ba2 .fuz .xwm .wav .esm .esp .esl .swf .tae
   .flver .bnd .dcx .param` and more), files over 1 MB outside an allowlist, and known decompiler signatures.
   Allowlisted exceptions (our UI images, Pelagiad, generated test fixtures that contain no game data) are
   listed with a reason.
6. **Screenshots and clips** from the game may appear in owner check-ins (GitHub issues) because that is
   ordinary fair commentary of one's own play, but are never committed.
7. **Derived files** (FaceGen heads, LOD, behaviours, re-timed animations, silent voice files, patched menus)
   are made at runtime or on the player's machine by the installer, never shipped (decision 0014).

## Consequences

- Build outputs (the compiled `.esm`, BSAs we pack from our own files, DLLs) are release artifacts produced by
  CI or the build VM and attached to releases only after the guard has checked their contents list.
- The world generator needs Skyrim and mod plugins as *read-only masters* on the build VM; those stay outside
  the repo under `$ARGONIA_GAME_ROOT` (see infra).
