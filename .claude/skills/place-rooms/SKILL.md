---
name: place-rooms
description: A place's interiors - the source's rooms carried with their door pairs and arrivals, a building's rooms added from one other source, inner and back doors, cuts and strips, locks and the name each room's door shows. Use when the baseline's rooms are carried, when a story needs a room the source lacks, when a room keeps too much or too little, and when a room's name is wrong.
---

# Rooms

Step 5 of the place path ([place-system](../place-system/SKILL.md)). Stages: `add`, `names`.

## Carried rooms

`draft wholesale <place_id> --offset <u> --rooms` (`place-site`) gives every laid source door its room: the copy of
the source cell, the pair of doors, the way out landing where the source landed it. A cell several houses share is
the one room behind its way out; a cell whose ways out all serve one building is copied whole
(`--whole <room,...>`). A copied room keeps the source's lights and its source navmesh when that is one island
reaching every arrival and every piece of furniture; else the build meshes it again and says why.

Strip what the record does not want from a room: the door's `room.drop` `{source ref id: why}` (a container of
levelled treasure, a king's guards, traps), `room.strip` `{base editor id: why}` (every piece of a base), Nordic
pieces judged as outside (`place-site`). Part of a large cell is copied by a cut, `room.cut` `{"box": [x1, y1, x2,
y2]}`; close every opening the cut leaves with the kit's own door or wall piece.

## A building's rooms from one other source

The building is placed by `place-adapt`. Its door row carries `room`: `copy_of` `<source_id>/<cell>`, `door` (the
cell's way out), `space` (our space id), `arrival` (in front of the door, on the walk it is reached by: `[x, y]` on the ground, `[x, y, z]` on a deck or a
ship), `drop`.
Where the door opens onto a porch, set the door `on` its building and the arrival at the porch's foot. Run
`python3 -m tools.places draft add <place_id>`: it copies the room, pairs the doors and removes every further way
out. A room's own inner door (a cellar off a hall) is kept by copying the cell whole.

## A room inside another, a back door

- A room behind a door inside another (a strongroom off a hall) is a `draft.add` door standing in that room,
  `space` set, with `room` and an `arrival` [x, y, z] on the room's floor.
- A further way in is a pair of added doors: one in the room, one outside naming it in `pair`, each with `arrival`.
- Put every inner door on a wall whose floor the source's navmesh covers.
- A door's lock is its row's `lock` ({level, key, flags}); the key's keeper is a stock row (`place-stock`).

## Look inside

Every room is looked at before hand-over (`place-look`, Inside a room): `look <place> in <room> overview`, `probe
--all` (an opening onto the void is closed with the kit's own piece), `playwalk --rooms`.

## Room names

The tools name each room (`docs/design/place-studio.md`, Room names): the promise kept in it, else its household's
head ("Ixtul-Bei's House"), else the source's name unless it is a builder's leftover. A room nothing names is your
call in `draft.room_names` `{space: {name, why}}`, named for what a player finds inside. Run `draft names
<place_id>` after any change to who lives or works where.

Enforced by the checks: every room named, no leftover name, no two alike (`draft check`); doors paired and rooms
reached (the build's `doors` check); a copy holds to the source room it keeps (`rooms`).
