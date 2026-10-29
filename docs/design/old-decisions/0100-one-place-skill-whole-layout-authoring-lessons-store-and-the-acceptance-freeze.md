<!-- imported unchanged from elder-souls-argonia docs/decisions/0100-one-place-skill-whole-layout-authoring-lessons-store-and-the-acceptance-freeze.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0100 — One place skill; a place is authored as a whole layout and iterated on renders; lessons live in the tools and the skill; an accepted place is frozen

**Status:** accepted. **Extends:**
[0099](0099-places-are-built-in-a-loop-until-the-skill-is-proven.md) (the
loop), [0097](0097-placement-is-authored-in-a-workbench-and-the-pose-record-is-the-output.md)
(the pose record is the output) and
[0098](0098-variety-is-measured-per-settlement-not-by-a-template-cap.md)
(per-settlement bars). **Supersedes:** world 97 C12's compile-placed
dressing. Edits to an accepted place are
[0128](0128-places-are-edited-in-place-never-rebuilt.md); layers on it are
[0140](0140-layers-on-a-built-place-never-rebuild-it.md); what a place hands
over is [0102](0102-a-place-carries-its-own-ground-and-hands-over-nothing-it-can-check-itself.md).

## Decisions

1. **One place skill, `place`, holds the procedure and the grounding.**
   It is what every place slice, fix round and layout change invokes; the
   workbench (`wb.py`, `wb.py explain <topic>`) is its tool manual. It points
   at every binding source with the one line the designer needs from each,
   never a copy. The kit skills (`kit-build`, `modular-runs`,
   `composite-author`, `kit-mining`) are called from it when a kit is
   missing.
2. **A place is authored as one whole layout, then iterated on renders.**
   The builder writes the design record (`world/sources/blueprints/<place>.design.md`:
   site, intent, walk-through, palette, and a brief row per building,
   enclosure, path, light, water edge and dressing group, each with its kit
   piece and its lore or rule pointer) before placing anything. The layout
   (`<place>.layout.json`) is built and edited in one workbench session per
   job (`wb.py session start`, scripted verbs, `wb.py session commit` per
   batch), so the whole place is judged by the gates in one call. One builder
   per place or district decides the design; moving or cutting a place, a
   quest premise or a world rule is the owner's call.
3. **Iteration is a render round.** The builder reads its own renders while
   designing; `reader` agents judge, per view class, only what needs eyes,
   while rules measure geometry. A round is one layout edit and one batched
   read, and every finding of a round is fixed together.
4. **Every fix is a lesson, and a lesson lands in a tool first.** A lesson
   becomes a tool default, a check or a lint rule; only where no tool can
   carry it does it become an in-place edit of the `place` skill or its type
   sheet ([0106](0106-how-we-work-fix-at-source-one-preflight-per-batch-scoped-for-real.md)
   decision 8). Fresh agents never re-learn a fix: the tool carries it.
5. **Dressing is authored to 0098's numbers, and the compile realises it.**
   The designer places dressing in the layout as groups (yard sets per
   building kind); the compile never invents dressing near a building.
6. **An accepted place is frozen; dependencies point one way.**
   `world/sources/placement/accepted-places.json` is the receipt: place id,
   the owner's acceptance, the hash of the compiled settlement record and of
   the place's own patches, and the ground and kit provenance from the
   export. A gate fails the build when an accepted place's compiled record
   would change without a `reopened` entry (owner and reason). Gates added
   after acceptance run on it in report mode only and queue their findings to
   the polish backlog. Publishing is per place, so one place's build never
   recompiles or blocks another. Direction of dependency: frozen world
   (terrain, water, roads, vegetation), then kits, then the place skill, then
   place records and their typed per-place patches, then the later systems
   that fill the sockets the record declares (interiors, people, ambience,
   navmesh). Anything that would move a frozen layer or an accepted place is
   a world-level call for the owner.
7. **Grounding reads are steps, not hopes.** The skill's first step writes
   the place's site section from the catalogue record, the macro plot, the
   quest provisions, the lore dossiers and the register of places already
   built; a record defect found there (services promised without rows, a
   kit the culture does not use, a danger band off its ground) is fixed as a
   rule gap with a test before design, never designed around.

## Why

Before the first real place, the grounding (about 80 sources) was mostly
unreachable from the skills, the workbench placed one piece per command,
lessons lived where the designer never read them, three dressing rules
disagreed, and nothing protected a place the owner had accepted.

## Consequences

- Evidence (the grounding, skill and plan audits) and the superseded
  procedure:
  [place-decision-rounds/0100](../research/archive/place-decision-rounds/0100-as-recorded.md).
