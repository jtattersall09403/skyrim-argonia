---
name: place-system
description: The map of Argonia's place skills. What a place draft of ours is (its source carried whole and adapted by hand), the order of work from a place's record to the owner's studio check with the sub-skill for each step, who decides what, the working method, the hand-over bar, and how the lead briefs and continues the one agent that owns a place. Read it first, before drafting, changing, checking or handing over any place of the new world, and before briefing a place agent.
---

# The place system

Every place skill is one step of one path. This page is the path and says which skill to open; each skill holds
the recipe for its step.

## What a place draft of ours is

A place of the new world is its **source place** (a town, camp or ruin of a plugin we hold, chosen as the closest
match to the place's record) carried onto our ground **whole**: every source piece inside the footprint at one
transform and height, the chosen part of the source's ground under it, and what already works in the source
carried with it (rooms and door pairs, walks, patrols, furniture and idle markers, lights with fixtures, ownership,
its own walking mesh). The drafter then **adapts it by hand**, looking, until it reads as the record: adapt to our
ground, relabel, prune, move, add. The Hist's sap pool, lights, stations and plant clearance are laid by their
stages, and each is looked at.

The draft is the place files under `newworld/places/<place_id>/`; the drafter's calls go in `place.json`'s `draft`
block, hand changes through `look commit`. The file contract is `docs/design/place-studio.md`; never write mod
record or asset content into a place file.

## Who decides what

- **The place record is the brief.** `python3 -m tools.newworld.place_card <place_id>`: summary, `look`, people,
  promises (`gives`), dangers, hooks and the `source` note. What the record does not support is pruned; what it
  needs and the source lacks is added.
- **The drafter** makes the judgement calls: the source, how much of its ground to bring, the transform, every
  adaptation, where an added building stands, people's spots, quest spots, what is accepted after looking.
- **The tools** lay the baseline, carry what works, measure and check. Their checks are the floor, never the finish.
- **Hand placement is authoritative** for every later tool (`place-change`).
- **The owner judges look.** He edits and notes the place in the studio; what he changed is never moved again.

## The order of work, and which skill to open

| Step | What | Skill |
|---|---|---|
| 1 | The place's record: what it is, what it promises, its danger | `place-research` |
| 2 | Read the record as the brief; make the promise list (record, people, quests, each quest state); choose the source against it; pin it; write `draft.plan` | `place-plan` |
| 3 | How much of the source's ground to bring; the baseline laid at one transform; the source's rooms, walks and mesh carried; the place fitted to our ground (mounds, sinks, banks) | `place-site` |
| 4 | Adapt to the record: relabel, prune, move, add (an added building placed where it can be walked to) | `place-adapt` |
| 5 | Rooms: carried, added from one other source, inner doors, names | `place-rooms` |
| 6 | The walking mesh carried from the source; what a hand change does to it; spurs to what is added; patrols | `place-streets` |
| 7 | People on the source's furniture: beds, work spots, sleep, guards, services, the law | `place-routines` |
| 8 | Quest things and persons placed where a player finds and recognises them; the sight test; each quest state built and checkable | `place-story` |
| 9 | The rules then a look: sap pool, lights, lanterns, stations, collision boxes | `place-dressing` |
| 10 | Look, probe and act in the studio's 3D scene; the hand-over look | `place-look` (the inner loop of every step) |
| 11 | Verify once at the end: draft check, seat, build with the carried mesh, the seventeen checks, the promises check green | `place-check` |
| 12 | Who each person is (names, households), after the people are placed at step 7 | `place-people` |
| 13 | What the place holds, every promise delivered | `place-stock` |
| 14 | Any change to a drafted place; the owner's notes and variants | `place-change` |
| 15 | The owner finalises a save: record, build, lessons, report | `place-lessons` (the finalise chain) |

Steps 3 to 13 build against the promise list: each turns its rows `built` with their evidence, and `draft check`
fails what is still unsaid or unbuilt, so nothing promised is first found missing at the end.

Which skill for a common job:

| Job | Open |
|---|---|
| A first draft | `place-plan`, then 3 to 11 in order |
| Moving, sinking or deleting a structure | `place-look` (the hands, `look commit`); what counts as a structure is in `place-site` |
| A post or leg short of our ground | `place-site` (mounds, sinks) |
| A source thing that makes no sense for our place | `place-adapt` |
| A building or room the story needs | `place-adapt`, then `place-rooms` |
| A streets, doors or people check failing | `place-streets` or `place-routines`, as `place-check`'s table says |
| A quest thing with no spot | `place-story` |
| An owner's note | `place-change` |

Read `docs/design/consistency.md` before any work: one world, told the same everywhere, and which side changes when two disagree.

## The working method

- **One agent owns a place**, the `place-drafter` agent, from the record to the hand-over (or one change to a
  drafted place), and works through it iteratively: do, look, judge, do more. Its context compacts itself and the
  lead continues it with its history, so running short of room is never a reason to stop or hand over.
- **A short STATE.md** for the place (at most 50 lines, current truth: what the place is, the source and transform,
  what is done, the last check verdicts, what is next, decisions made) lives beside its notes and is kept current.
- **Eyes and hands first.** Look (`look overview`, `at`, `section`), measure (`look probe`), change one thing, look
  again. Measure for truth, look for judgement.
- **Every change is tested against "did this break something that worked?"**: a joint that met, a door that
  landed, a walk that ran, a person's spot that was reached.
- **Real shapes, not boxes.** A piece is its mesh in its pose: its feet, the surfaces stood on, its eaves, a tree's
  root collar, a stair's end lines. A box is only a first reject.
- **Many captures from many sides**, at eye level and from above, with sections on two axes. Routine before and
  after looks at a small size; full size for a final judgement. A place is never judged from one or two views.
- **Question every capture.** Ask whether it shows its subject (out of frame, behind a crown, the camera inside a
  solid); a failed capture is retaken. Nothing is called missing or broken until a `look probe` agrees. When
  something looks impossible, suspect the viewer first (`look truth`).
- **No grass, no light in the viewer.** Bare ground, flat ground paint and slab-like terrain are not faults; light
  is not judged, added or removed from what the viewer shows: a doubt about light goes to the owner's in-game check.
- **Heavy steps once.** `draft check`, the build and `check` take minutes each and share the machine-wide lock: run
  them at the end, under `tooling/job_guard.sh`, after committing the place files by path.
- **Fix the class, not the case.** When a tool misleads, blocks or cannot show what is needed, mend it with its test
  (or name the fault exactly for a tool lane) and say it once in the skill that owns it; then carry on.
- **Never bend a place to a check, or a check to a place.** A check that disagrees with how Skyrim does it is the
  tool's fault. A finding seen to be right as built is accepted with its reason (`place-check`), never hidden.

## The time log

While a pass is open (`timelog <place> pass start`, which creates the log; nothing is written outside one, and only from the worktree that started it), every `python -m tools.places` verb appends a row to `newworld/places/<id>/timelog.jsonl` when it ends (what, how long,
its queue wait under job_guard). The drafter adds the meaning: `timelog <place> phase "<step>"` at each step of the
order of work above (plan, site, adapt, streets, rooms, routines, story, dressing, stock, check, walk loop, fixes after
lead's read, `tool fix: <tool>`, waiting on lead) and `timelog <place> pass start|end "<ask>"` around each pass the
lead sends. `timelog <place> report [--md]` gives wall time by phase and by kind of activity, the ten longest commands,
builds, full walks and each pass's elapsed time; the drafter's hand-back carries its table, so the lead and the owner
see where a place's time went. The log is committed with the place and read by nothing else.

## The hand-over bar

A place is drafted to this bar; the owner may open and edit it in the studio as soon as its files are committed,
with builds and checks run beside his editing:

1. `look <place> probe --all` reports nothing open (accepted faults listed with their reasons).
2. `draft check` PASS, `needs check` PASS, `seat` 0 refs moved, the build's seventeen checks green with accepted
   findings named, `units` and `units --joints` read and every flag mended or accepted (`place-check`).
3. `look survey` of the place and of every structure read; the playwalk tour walked and read (its strips and map
   whole, full size where a strip is doubtful and at every door, stair, bridge end and quest spot) and every room's
   entering view read; no PLACE tile and no "cannot be walked to" left. A place that passes its checks but has not
   been walked is not done: a full walk, the issues fixed and only their views recaptured until none is left, then
   a full walk again, until one is clean (`place-check`).
4. Every sentence of the record's `look` matched to an image that shows it; a line not yet met named.
5. Every named person with a role has a bed, a work spot and a sleep package; every quest thing and person at the
   place has a spot a player finds and recognises (`place-story`).
6. A place sharing its source with a place laid earlier passes `look <place> versus <other>` read whole (the same
   views of both on one sheet), confirming what its plan's `differs` fixed.
7. The owner captures taken (each side at eye level, each structure the record names, each room a story needs).
8. The final build and check come after the LAST edit of any kind to the place's files; `python3 -m tools.places
   handover <place_id>` says "built check current" (the consistency stage's rule, `edits/` aside).

## Planner sessions: how the lead runs place work

- **Brief a `place-drafter`** with: the place id and its record; the source chosen, or the ask to choose it by
  `place-plan`; the path of the place's STATE.md; what "done" is (the hand-over bar above: every check, the read
  survey, the captures); the owner's rulings that bear on it. Never offer running short of room as a reason to stop.
- **Continue the same agent** with SendMessage for more work on its place, after a compaction and after the owner's
  notes; start another only when the first cannot be reached. Never two agents on one place at once.
- **Split only tool work** into separate lanes (`deliver`): a tool fault the drafter names becomes a tool lane while
  the drafter carries on.
- **A brief never asks for a full gate**: a lane runs the scoped gate its change reaches.
- **Hand the place to the owner's studio first**: as soon as its files are committed it is his to open and edit;
  builds and checks run beside his editing, never before it.
- **Read the final captures yourself** before telling the owner anything; a passing check is not a look.
- **Record your own calls** as "decided by the lead, for the owner to confirm" in `docs/owner-rulings.md`; when
  unattended, decide and carry on: never ask or wait.

## Lanes beside each other

Each checkout (the main tree or a lane's worktree) has its own look daemon, session and port and builds its own copy
of the C# place builder. The heavy steps (5 to 7 GB each) share one machine-wide lock
(`tools/places/heavy_lock.py`); nothing heavy runs beside a world rebuild. Touch nothing in the place while a build
or `draft check` is running.

## How the skills learn

The owner's finalised edits run `place-lessons`, which rewrites the sub-skill that owns each fault class.
