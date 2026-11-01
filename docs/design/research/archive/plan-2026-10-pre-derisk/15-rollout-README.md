<!-- imported unchanged from elder-souls-argonia docs/research/archive/plan-2026-10-pre-derisk/15-rollout-README.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Phase 15 — rollout by region packet (sketch; 16k's exit rewrites it, with the roadmap and the template)

**What Phase 15 is.** The rest of the province, built one region packet
at a time with the skill set the
[16k place loop](../../../phases/16-foundation-and-places/16k-place-loop.md) proved
(decision [0099](../../../old-decisions/0099-places-are-built-in-a-loop-until-the-skill-is-proven.md)),
once every system a packet needs exists (decision 0062 §6: after 9, 10b,
10c, 13, 12, 12b and 14). It opens when 16k's exit bar is met: every type
on the owner's signed list has passed unattended twice in a row. Status
lives in PROGRESS.md; the order lives in `roadmap.md`; each packet is a
chunk from `packet-template.md`. Both are written at 16k's exit ([polish backlog](../../../phases/P-polish/backlog.md) Item 8), the template to the spec in
the 16k loop ([16k-place-loop.md](../../../phases/16-foundation-and-places/16k-place-loop.md)), with
the template decision per minor type.

**Files in this folder (after 16k's exit):** `roadmap.md` (ordered
packets, scope, types, owed structures, owner-guided flags),
`packet-template.md` (the brief every packet copies), one brief per
packet as it opens.

## The rhythm every packet follows (the 16k rhythm, 0099)

1. **Built per place with the place skill**, unattended: the packet's
   places from the 16g record; the co-design quest pass (quests 90 §65b);
   `place` steps 0–5 per place (tier A interiors enterable, every
   promise a placed socket, 0103); the route structures and berths the
   packet owes (a packet that leaves one `pending: packet` fails its gate).
2. **Completed**: the owed systems applied *in the packet* with their own
   skills, filling the sockets the places placed: assembled interiors at
   reserved doors (Phase 12's skill), fauna, encounters and fixed loot
   (13), navmesh and combat-space probes (10b), balance against compiled
   numbers (10c), streaming budgets (14), the soundscape (12b).
3. **The owner's walk**, one fix round per walk, as in a 16k slice.
4. **Freeze**: the packet's density declared against ruling 11's budget;
   quest briefs and placements consistent; the packet marked done in
   PROGRESS.md.

Every catalogue run in a packet follows the CLAUDE.md golden rule "Prove
on a sample, validate on a fresh batch, scale once", and every per-packet
stage (re-derive, export, vegetation patches, ground control) runs with
the `--places` selector, full runs
only at freeze
([16h catalogue audit](../../../research/phase16/16h-catalogue-wide-steps-audit.md)).

Major cities and the opening-scene places (`ownerGuided: true`) are their
own packets with extra rounds; no skill runs unattended on them (0062 §9).

## What is still to decide (16k's exit answers these in the roadmap)

- Packet size, once the skills run clean per type.
- Whether a packet whose every type is automation-ready needs an owner
  walk per place or one per packet.
- The order: contiguous regions along the road legs, opening-scene
  packets first for the playable start, or by quest milestone.
