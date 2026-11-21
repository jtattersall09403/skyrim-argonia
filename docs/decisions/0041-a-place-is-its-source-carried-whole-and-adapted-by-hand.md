# 0041 A place is its source carried whole and adapted by hand

Date: 2026-11-21 (#80, #82). Status: accepted.

## Context

Places were drafted by a stage pipeline: each house group of the source fitted to our ground on its own, every
piece re-seated, pieces dropped by rule, then streets, door arrivals and a walking mesh generated from nothing, and
agents mending the result. On 2026-11-21 two trials drafted places the other way: the source carried whole and
adapted by hand (issue #82).

- **Jal-Veesa**, against the pipeline's draft of the same place from the same source: the build's checks 13 of 17
  green against 12; street failures 55 against 241; people and patrol failures 10 against 41; door arrival failures
  1 against 4; stair and bridge end faults 5 against 14. About 5 hours against about 48; of 612 source pieces about
  580 kept as built.
- **Karsh-Naal Camp**, from a re-chosen source (King of the Murkmire's Ree-An-Wo in place of an orc stronghold): 17
  of 17 green, about 9 prunes and a dozen additions; the stronghold, judged first, was about a fifth usable.

The pipeline took apart a place that already worked and spent its effort putting back what it broke (fitted groups
pulled apart so bridges and stairs no longer met; streets and meshes rebuilt where the source's worked). The owner
saw the comparison, took the places over in the studio and ruled the carried-whole method the way places are built
(docs/owner-rulings.md, 2026-11-21), with one agent owning a place.

## Decision

1. The source is chosen by looking at candidates as places against the record: within the footprint over half its
   pieces kept as built, the quests' rooms present or cheap from one other source; main-quest places get their
   closest match. A source may serve several places; each is adapted to feel its own.
2. The drafter decides how much of the source's ground to bring (all of it, a structure's own platform or terrace,
   or none); our water line never moves.
3. A tool lays the baseline: every source piece inside the footprint at one transform and height, the chosen
   ground, and what works in the source carried with it (rooms, door pairs, walks, patrols, furniture, lights,
   ownership, its own walking mesh: `draft wholesale`, `wholesale.navmesh: "source"`).
4. The drafter adapts it by hand, looking: fits it to our ground, relabels, prunes, moves and adds; people go on the
   source's own furniture; quest things where a player finds them. Rules only where a rule does well (sap pool,
   lights, stations, plant clearance), then looked at.
5. The checks run once at the end; a finding seen to be right as built is accepted with its reason.
6. One `place-drafter` agent owns a place and is continued, never replaced.

## Consequences

- The place skills are one recipe for this method (`place-system` and its sub-skills, `place-adapt` new).
- The pipeline's fitting, seating, piece-dropping and street-laying stages stay only for the four drafts made with
  them (Helstrom and three outposts) and go when the last is redrafted (docs/design/place-studio.md, Stages kept
  only for drafts awaiting redraft).
- Tool faults the carry exposes are mended in the tool, once, with a test.
