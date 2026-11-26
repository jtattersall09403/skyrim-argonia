# 0018: The Creation Kit is a tool (Papyrus compiler, FaceGen), not the workflow

**Status:** decided 2026-10-27 (owner offered to add the Creation Kit from Steam and asked whether Claude Code
needs it, "isn't that how mods normally get made?").

## Context

Most Skyrim mods are made by hand in the Creation Kit (CK), Bethesda's free Windows editor for Skyrim owners. It
is a point-and-click GUI: an agent cannot use it the way a person does, and it has no headless mode. But the CK's
output is just plugin records, and code libraries (Mutagen, Spriggit) write the same records directly. The CK
also ships things we need regardless of how records are written.

## Decision

1. **The Creation Kit is installed on the play machine**, from the owner's Steam library, at the build matching
   the pinned runtime ([0002](0002-one-pinned-skyrim-runtime.md)).
2. **Records are written as data**: Spriggit YAML in `plugin/`, built to the ESP on the build VM. That makes the
   work reviewable, repeatable and agent-friendly. xEdit and houseCARL are the checkers. The CK is never the
   place where content is authored.
3. **The CK is used for**, each a scripted job and never hand work:
   - **Papyrus compiling:** the reference `PapyrusCompiler.exe` and the base script sources ship with the CK, and
     our scripts compile against them. This alone makes the CK required.
   - **FaceGen export** for a face the templates do not cover; for players, the installer's own step
     ([0014](0014-derived-files-are-made-on-the-players-machine.md)).
4. **How Claude interfaces with it:** through files (plugins in, logs out), its command-line switches
   (`-GenerateLips` and similar where they exist), and automation scripts on the play machine with screenshots as
   the oracle.
5. The CK's EULA terms (non-commercial, for owners, ZeniMax licence to the mod, required notice) are in
   [legal-and-sourcing.md](../legal-and-sourcing.md).
