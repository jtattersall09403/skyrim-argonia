# 0038: The pivot: Black Marsh & Valenwood is the world; we mod our story on top

**Status:** decided by the owner, 2026-11-05. Supersedes 0001, 0004, 0005, 0009–0011, 0013, 0016, 0017,
0019–0023, 0026–0031, 0033 and 0036 (deleted; their text is in git history before this commit).

## Context

The first week (2026-10-27 to 2026-11-05) built a total conversion: a generated province, our own SKSE systems,
our own UI and HUD, DS1-measured combat, a relational world database, an agent-driven in-game test harness and a
five-part schedule. The owner's verdict: "basically that experiment failed", "the current repo's process stack
has ballooned out of control". The owner asked for a complete pivot, as much deleted as possible, and a process
as light as possible.

## Decision

1. The game is **vanilla Skyrim SE + Black Marsh & Valenwood + the Nexus collection xyf1u3 (soulslike combat)
   + FreeClimb + Magic Expanded**, with BM&V as the **default world**: a new game goes straight into our own
   opening in Black Marsh (Enderal-style, no Helgen; owner, 2026-11-05), and the vanilla main quest, dragons, civil war, couriers and radiant quests shut down.
2. Once that works on the play machine, the work is **our storyline, quests and factions modded on top of
   BM&V's world** with minimal tweaks (NPCs, items, bosses, creatures added, removed or changed).
3. **Process:** agents avoid in-game testing; the owner tests. A small number of building blocks are proved
   once (one NPC's dialogue changed, a few quest triggers, a few script types, a placement on existing navmesh,
   and so on) and everything else is built from them without individual testing.
4. **Kept:** the build VM (on demand, a few hours a day) and the g6.xlarge spot play machine; the interrupt-proof rule (0037);
   the streaming setup; the lore dossiers and the story design; the quest and dialogue skills; the no-assets
   rule (0003); the pinned runtime (0002); no Nordic element reaching the player (0006, now applied to what
   our plugin adds); nothing levelled against the player (0035); AWS under $100 (0008).
5. **Deleted:** everything else, including the world database and generator, the SKSE plugins, the UI, the
   plugin YAML of the generated world, the journeys, scenes and bridge, the chunk briefs, ledgers and the five-part
   schedule, the LOD and pool jobs, the old AWS archives (LOD, shader caches, saves, worktrees) and the S3 cache
   of mods no longer listed.

## Consequences

- The plan is [PLAN.md](../PLAN.md); status is [PROGRESS.md](../PROGRESS.md); rulings are
  [owner-rulings.md](../owner-rulings.md).
- The play machine was terminated with its disk on the same day (the owner's AWS cleanup) and is recreated from
  the scripts in Phase 0; nothing the new goal needs was lost, since the stack is rebuilt from the manifest and
  the private bucket's mod archives.
