# 0018: The Creation Kit is installed and used as a tool; records are still written by code

**Status:** decided 2026-10-27 (owner offered to add the Creation Kit from Steam and asked whether Claude Code
needs it, "isn't that how mods normally get made?").

## Context

Most Skyrim mods are made by hand in the **Creation Kit** (CK), Bethesda's free Windows editor for Skyrim owners
(Steam: "Skyrim Special Edition: Creation Kit"). It is a point-and-click GUI: an agent cannot use it the way a
person does, and research found no headless mode (under Proton its render window works, linking and new
triggers crash, dialogue and scene editors are untested). But the CK's *output* is just plugin records, and
code libraries (Mutagen, Spriggit) write the same records directly; universal-modder's Skyrim field note built
quests and dialogue that way. The CK also ships things we need regardless of how records are written.

## Decision

1. **The owner adds the Creation Kit to their Steam library** (free with Skyrim SE); it is installed on the build
   VM (and on the GPU box if a job needs it) with `steamcmd` under the owner's login, at the build matching the
   pinned runtime (decision 0002).
2. **Records are still written by code** (decision 0009): generators + Mutagen → Spriggit → ESM. That is what makes
   the work reviewable, repeatable and agent-friendly. The CK is never the place where content is authored.
3. **What the CK is used for** (each a scripted job, never hand work):
   - **Papyrus compiling:** the reference `PapyrusCompiler.exe` and the base script sources (`Scripts.zip`) ship
     with the CK; our scripts compile against them (0.5). This alone makes the CK required.
   - **Checking our plugin:** loading `Argonia.esm` in the CK under Wine/Xvfb and reading its warnings log is an
     extra L1 check (data errors the CK reports at load).
   - **Navmesh** (0.2 G4, 2.W4): the CK's generator, scripted on the Windows game machine, as the check on
     tes4skyrim's method and the fallback for cells it cannot do (decision 0026 §3), its output captured back to
     Spriggit.
   - **FaceGen export** for development and the owner's GPU box (0.2 G4), if templates do not cover a face; for
     players, the installer's own step (decision 0014 §3).
   - **Water flowmaps** (0.2 G7) if we cannot generate them ourselves.
   - **Previews:** the CK's render window as a quick still check of a cell, when the game itself is not needed.
4. **How Claude interfaces with it:** through files (plugins in, logs out), its command-line switches
   (`-GenerateLips` and similar where they exist), and GUI automation scripts on a virtual display with
   screenshots as the oracle; each automated CK job lives in `tools/ck/` with a test. If a CK job proves too fragile
   under Wine, a temporary Windows spot instance runs it (costed under decision 0008).
5. The CK's EULA terms (non-commercial, for owners, ZeniMax licence to the mod, required notice) are already in
   docs/legal-and-sourcing.md.
