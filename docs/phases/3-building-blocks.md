# Phase 3: one test quest that proves the building blocks

Status: [PROGRESS.md](../PROGRESS.md). The plan: [PLAN.md](../PLAN.md). Edit this file as the phase goes; it is the phase's whole brief.

**What it is for.** The story is built in Phase 4 from a small set of engine mechanics, the blocks, listed in
[blocks.md](../design/blocks.md) and derived from the Act I records in Phase 2: triggers (what moves a quest stage),
conditions (what gates a trigger or a line), effects (what a stage does) and the world edits under them. This phase
finds a broken block cheaply, in a throwaway test quest, before any story rests on it. If every block works, and the
blocks work wired together, any quest made only of them works (the induction note in blocks.md).

**Starts when** Phase 2's review is finished and blocks.md's stage table is regenerated from the final records; the
block list is then frozen for this phase.

**What gets built.** One test quest, `ARG_BlockTest`, in our plugin on top of BM&V, started by one console command
and finished in about ten minutes. It chains every trigger, condition and effect the slice uses, each once, in one
small place, and includes the engine's known risk cases:
- two triggers firing at once for the same stage;
- a save and reload in the middle of the quest;
- an alias that must fill when the quest starts;
- a persistent reference and an AI package that must win over the NPC's own.

A block with no vanilla precedent (blocks.md's precedent column) gets one extra step of its own in the quest. A block
that uses vanilla's own script unchanged needs no separate proof.

**How it is built.** Records as Spriggit YAML in `plugin/`, built to the ESP on the build VM; Papyrus compiled on the
play machine; the Creation Kit only for the compiler and FaceGen. The shapes used here become the templates every
Phase 4 quest copies.

**Agent check, before the owner.** Read the built plugin and scripts (not the game): every step's stage, condition and
fragment is present and points at the right records. Loop until it does.

**Owner test.** One issue: the console command, where it puts you, and one line per step saying what should happen.
You play it once and reply with any step that did not happen. A broken block is fixed and only that step re-posted; if
it cannot be made reliable it is dropped, and the Phase 2 records that used it are re-authored before Phase 4. A step
that passes is never re-tested.

**Done when** every step has passed in the owner's walk.
