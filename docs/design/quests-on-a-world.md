# Putting a quest system onto a world

How to take a written quest system (lines, quests, factions, people) and make it play in a world someone else built,
with small edits to that world. This is the recipe as it stands; it is kept current in the same commit as any change
to the method, and it is the source the post-Phase-4 skills are cut from. It states how to do the work, never how
the method was arrived at.

## 1. Measure the world first

- **Census tables** of the loaded world, one row per thing, each with its form key and position: settlements and
  their cells, map markers, doors and interiors, placed people (`bmv_talker`), walk-in shell buildings and the
  navmesh inside each (`bmv_shell`), containers, flora, books, corpses, hostile placements.
- **Read the winner.** A record's live version is the last plugin in the load order that overrides it, never the
  master alone; every override copies the winner.
- **Navmesh and surfaces are the ground truth for placement.** A spot is usable only if the winning navmesh covers
  it (for people) or a modelled surface carries it (for things: the surface reader gives the mesh top). Height alone
  is not enough; a cell with no navmesh hosts no people.

## 2. Allocate the whole system at once

- Every line gets its seat and hubs, every quest its host places and cast, chosen together so no two lines compete
  for a place or a person unless the design wants them to meet.
- One ledger of world edits, each edit once, linked to every quest that needs it; a checker fails a quest hosted on a
  place that does not exist, an edit one quest makes and another undoes, or a place over capacity.
- Places are called by the names the player will see (the world's names, or a rename edit).

## 3. Write each quest only in proven shapes

A quest is stages joined by triggers, gated by conditions, firing effects, on top of world edits. Only shapes proven
once in game are used (the block set: `docs/design/blocks.md`). A step that needs an unproven shape is rewritten
into proven ones that keep its point; only when no rewrite keeps the quest's spirit is a new block built and proved.

| Needed | Proven way to do it |
|---|---|
| a quest that starts when the player arrives somewhere | Start Game Enabled with an empty stage 0; the giver's opening line sets the first stage, or the previous quest's ending starts it |
| a quest gated on another quest's progress | a stage condition on the opening line (C-stage) |
| a trigger area that should also check time, detection or who is present | an unconditioned trigger area gated only by its prerequisite stage; the extra check moves to an AI package's schedule, a condition on a dialogue line, a death trigger's fail-forward, or the crime engine |
| "do it unseen" | a detection condition on a line, or theft or pickpocket judged by the crime engine |
| "after dark" | a time condition on a line, or a package schedule that only puts the person there at night |
| an escort reaching a place | a follow package on the person, and a trigger area the player enters at the destination |
| "bring N of a kind of thing" | N of one named item through the item block |
| several things that must all happen | one hidden stage per thing, each checking the others before setting the joint stage |
| any of several people dying | a death trigger on each person's alias setting the same stage, behind a guard |
| removing people from a scene | disable them through their own enable parents; never kill in a dialogue fragment |
| a fight or a brawl | a fixed-level enemy and a death trigger, or a Speech or gold alternative |
| a person the player must not lose | essential; the record still names a fail-forward for its checker |
| a person picked out to speak | a condition on their placed reference, the reference made persistent |
| a named person standing in the world | our own base templated on the world's (look and behaviour kept, our name and fixed level) |
| standing with a faction | a global the endings add to |

Every main quest offers at least two ways through using different named skills; every stage says plainly what to do.

## 4. Edit the world lightly

- **Clean-up:** each host place's jarring or levelled placements are disabled by override, each templated survivor
  set to a fixed level (nothing levelled against the player). A person who has been given talk is kept.
- **New people and things** stand on existing navmesh or a read surface; no new navmesh.
- **Moving a quest spot** within its settlement to the nearest usable ground is a record edit, not a redesign.
- **Doors:** lock, unlock or re-point existing doors first; a new linked pair only where no existing door serves.
- **Overrides** of a world, a cell or a placed reference are made once and shared: every step asks the one lookup
  for the mod's existing override before making a new one.
- **Persistent references** for anything a quest alias or a condition names.

## 5. Build and read back

- One builder file per quest line, called in a fixed order so form ids never move; Papyrus fragments compiled with the
  game's compiler; editor ids unique.
- A read-back per line, from the built plugin and the compiled scripts: every stage, journal, objective, fragment,
  alias, trigger area, enable parent, condition and line against the record.
- The whole plugin is re-seeded once after merging parallel work, and every read-back runs on that one build before
  it is deployed; nothing is tested in game by the builder.

## 6. Give everyone something to say

Every person who can be talked to is named, given a short backstory, a personality and their own true topics,
through the `talk-write` skill: facts from the loaded world (the world wins over a lore line it contradicts),
directions as routes of two to four landmarked steps, a cool first greeting and warmth only with regard, names by
the naming rules, rumours that point to a quest only while it can start.

## 7. Quest dialogue

Written per speaker from the record (`dialogue-write`), reviewed once (`text-review`), with cool, middle and warm
bands separated by the engine's relationship rank, and a short greeting for anyone a quest ending leaves standing.
