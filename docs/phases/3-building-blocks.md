# Phase 3: the building blocks, proved once each

Status: [PROGRESS.md](../PROGRESS.md). The plan: [PLAN.md](../PLAN.md). Edit this file as the phase goes; it is the phase's whole brief.

The block set is Phase 2's, derived from the first act: as few blocks as compose into every quest the act needs.
Each block is built once as a small, real example in our plugin on top of BM&V, proven off game by the agent, then
verified in game by the owner. A block's record and script shapes become the template every later use copies.

- **The authoring route** is settled by the first block: records are written as Spriggit YAML in `plugin/` and
  built to the ESP on the build VM (`spriggit` is installed at `~/.argonia/spriggit`); xEdit and houseCARL on the
  play machine are the checkers; the Creation Kit is used only where nothing else can (FaceGen for a new face; the
  Papyrus compiler). If Spriggit proves awkward for a record type, a Mutagen script replaces it for that type.
- **The base cases:** one example per block, each in its own small test quest started from a console command, so
  the owner can reach it in seconds. The examples are chosen from the act's own needs (Phase 2's list), for example
  a new topic on an existing BM&V NPC, a quest started by entering an area, an NPC from a template placed on
  existing navmesh with a schedule, a boss at a fixed level, a BM&V reference disabled.
- **The inductive step:** one composite test quest that wires every trigger type to a stage that fires every effect
  type, gated by every condition type, including the guarded cases from Phase 2's note (two triggers racing for one
  stage, a save and reload mid-quest).
- **A block that fails** is fixed once; if it cannot be made reliable it is dropped, and Phase 2's records that used
  it are re-authored around the remaining set before Phase 4.
- **Loop**: read the files that the game will consume and verify (to the extent that you can) that everything you intended to implement has been implemented correctly. If not, diagnose, fix, then repeat this loop until your read of the built game files (esm and plugin and whatever else) does meet this bar. But do not run the actual game yourself, just read/mine from the game files that you build. *Then* pass on to the owner.

**Owner test:** one session through the base cases and the composite, from an issue that says the console command
for each, where it is and what should happen. A block the owner finds broken is fixed and re-posted; a block that
passes is never re-tested.
