---
name: place-system
description: The map of Argonia's place skills. What a place draft of ours is, the order of work from a place's record to the owner's studio check with the sub-skill for each step, who decides what, the working method (eyes and hands first, heavy steps at milestones, fix the tool when a fault class appears), the hand-over bar, and how lanes work beside each other. Read it first, before drafting, changing, checking or handing over any place of the new world.
---

# The place system

Every place skill is one step of one path. This page is the path and says which skill to open; each skill holds
the recipe for its step.

## What a place draft of ours is

A place of the new world is drafted from a **source place** (a town, camp or ruin of a plugin we hold) onto our
real ground, as the place files under `newworld/places/<place_id>/`. The draft starts from the source as a
connected whole (its arrangement, the links between its structures, its patrols, routines and ownership) and is
reshaped, pruned and added to until it reads as the place's record. Structures move whole and are put where our
ground matches theirs; pieces are seated by sinking them into the ground. The tools write every place file; the
drafter's calls go in the `draft` block of `place.json`. The file contract is `docs/design/place-studio.md`;
never write mod record or asset content into a place file.

## Who decides what

- **The place record is the brief.** `python3 -m tools.newworld.place_card <place_id>`: summary, `look`, people,
  promises (`gives`), dangers, hooks and the `source` note. The source is a pool of pieces and a layout; whatever
  of it the record does not support is dropped.
- **The drafter** makes the calls the tools cannot measure: the source, the plan, the anchor, what is dropped or
  replaced, rooms' names, what is placed by hand.
- **The tools** measure and lay everything else, and their checks are the floor, never the finish.
- **The owner judges look.** He edits and notes the place in the studio; what he changed is never moved again.

## The order of work, and which skill to open

| Step | What | Skill |
|---|---|---|
| 1 | The place's record: what it is, what it promises, its danger | `place-research` |
| 2 | Choose the source, read it, write `draft.plan`, judge each source structure | `place-plan` |
| 3 | Where it sits on our land; fit, the source's ground carried under it (`draft ground`), units planned on it, seating, clearance, pieces dropped or replaced | `place-site` |
| 4 | Streets, decks, bridges, flights, joins and door arrivals | `place-streets` |
| 5 | Rooms: copied whole or in part, added buildings, inner doors, room names | `place-rooms` |
| 6 | Beds, routines, guards, services, travel stops, the law and the jail | `place-routines` |
| 7 | Lights, hanging lanterns, Hist sap pools, stations, a shrine's Hist, primitives | `place-dressing` |
| 8 | Quest things' first spots, things a story needs placed by hand, the needs and sight test | `place-story` |
| 9 | Look and probe in the studio's 3D scene; hands-on fixes; the hand-over look | `place-look` |
| 10 | `draft check`, the build, the build's checks | `place-check` |
| 11 | Who each person is | `place-people` |
| 12 | What the place holds, every promise delivered | `place-stock` |
| 13 | Any change to a drafted place; the owner's notes and edits | `place-change` |
| 14 | The owner finalises a save: record, build, lessons, report | `place-lessons` (the finalise chain) |

Steps 2 to 8 are one whole draft, `python3 -m tools.places draft <place_id>`, run once; each skill says what its
part of that draft does and how to judge it. After the first draft every change is narrow (`place-change`).

Which skill for a common job:

| Job | Open |
|---|---|
| A first draft | `place-plan`, then 3 to 10 in order |
| Moving one house or one structure | `place-look` (`move`, `sink`, then `look commit`); the rule is in `place-site` |
| A failed streets check | `place-streets` |
| Adding a room, or copying part of one | `place-rooms` |
| A floating lantern or any floating piece | `place-look` (`probe`, `section`), then `place-dressing` for lanterns |
| A quest thing with no spot | `place-story` |
| The hand-over look | `place-look`, "The hand-over look" |
| A build or check failure | `place-check`, then the skill that owns the failing part |
| An owner's note | `place-change` |

## The working method

- **Eyes and hands first.** Work as a designer does: look (`look overview`, `at`, `section`), measure (`look
  probe`), change one thing (`look move`, `sink`, `turn`), look again. Measure for truth, look for judgement.
- **Plan the layout before placing.** A structure is a real one: a house with its platform, posts, steps and what
  hangs on it. For each, decide where it stands and at what height from the ground under its whole footprint, so
  its floor and door are clear of the ground, its legs are in the ground by what they need, its door is reached on
  foot and joined decks share a level; decide it for the place as a whole. Neither "the source's height" nor "sink
  until low" is a rule.
- **Real shapes, not boxes.** A piece is its mesh in its pose: its feet, the surfaces a person stands on, its
  eaves, a tree's root collar, a stair's foot and head lines. Judge and place by those; a box is only a first
  reject.
- **Look as you go, not at the end.** After each structure is placed or changed: capture it from several sides and
  distances, at eye level and from above, with a section on two axes; read each capture; mend; then go on to the
  next. After each group of structures, survey the whole place again. A fault found at hand-over was a look
  skipped earlier.
- **Question every capture.** Before reading an image, ask whether it shows its subject: the subject may be out of
  frame, cropped, behind a crown, or the camera may be inside a tree, a mound or a roof. A failed capture is
  retaken from another side or distance; nothing is called missing or broken until a `look probe` agrees.
- **No grass in the viewer.** The viewer draws no grass or ground cover and the game does: bare ground, flat
  ground paint and slab-like terrain are not faults.
- **Light is not judged in the viewer.** The game's light differs. Nothing is called too dark or too bright, and no
  light is added or removed, on what the viewer shows; a doubt about light goes to the owner's in-game check.
- **Mend the tool and the skill as you go.** When a tool misleads, blocks or cannot show what is needed, mend it
  then, with its test, and say it once in the skill that owns it; carry on with the place afterwards. Re-plan when
  what you see disagrees with the plan.
- **Iterate with the light tools.** The inner loop is `look probe`, `look section` and the one draft stage that
  owns the change (seconds to a minute). The whole draft, `draft check`, a `streets` run and the build take 10 to
  40 minutes and queue on the machine-wide lock: run each once, at a milestone, under `tooling/job_guard.sh`.
- **Hand work becomes a pipeline only when proven.** A sequence of look steps that has worked by hand on several
  places is the record from which a draft stage is written; its output is still looked at.
- **Fix the class, not the case.** When a fault is fixed in a draft, change the tool or the skill so that kind of
  fault cannot be handed over again (a check that fails it, or a stage that cannot make it), in the same piece of
  work. A rule a tool enforces is stated in a skill as one line naming the check.
- **Never bend a place to a check, or a check to a place.** A check that disagrees with how Skyrim does it is a
  fault of the tool, mended there.

## The hand-over bar

A place goes to the owner only when all of these are true and seen:

1. `python -m tools.places look <place> probe --all` reports nothing: no piece floats, no missing base, no stand-in
   box, no walkway end with nothing under it, no door with no ground before it.
2. `look overview`, then `section` and `at` of each structure, each image read; every sentence of the record's
   `look` matched to an image that shows it, and a line not yet met named.
3. `draft check` PASS, `needs check` PASS, `seat` reports 0 refs moved, the build's seventeen checks green
   (`place-check`).
4. Every quest thing at the place has a first spot (`place-story`); every person the record and its quests need is
   placed with the completeness `place-routines` sets.
5. Nothing plainly wrong is left: every building and door arrival on ground, no street through a building, no
   island people use, no bridge with one support.
6. The tour and every room playwalked (`look <place> playwalk`, `playwalk --rooms`) and read: no PLACE tile, no
   "cannot be walked to" left.

## Lanes beside each other

Each checkout (the main tree or a lane's worktree) has its own look daemon, session and port; it builds its own
copy of the C# place builder. The heavy steps (the builder process, 5 to 7 GB each) share one machine-wide lock
(`tools/places/heavy_lock.py`, `~/.argonia/locks/places-heavy.lock`): a second heavy step waits for the first.
Nothing heavy runs beside a world rebuild. Commit place files by path before any heavy step; touch nothing in the
place while a `streets` run or a build is going (`place-check`).

## How the skills learn

The owner's finalised edits run `place-lessons`, which rewrites the sub-skill that owns each fault class.
