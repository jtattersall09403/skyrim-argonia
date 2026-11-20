---
name: place-rooms
description: A place's interiors - rooms copied from the source whole or as the one room behind a way out, buildings and rooms added from another place of our mods, inner and back doors paired, locks and the name each room's door shows. Use when adding a room or a building a story needs, when a copied room keeps too much or too little, and when a room's name is wrong.
---

# Rooms

Step 5 of the place path ([place-system](../place-system/SKILL.md)). Stages: `add`, `names`.

## Copied rooms

- A cell several houses share is copied as the one room behind its way out (the builder's room rule). A cell whose
  ways out all open into one walkable island is one building with several doors: copied once, each door paired with
  its own door inside. `whole: true` on an added door copies a cell whole when all its ways out serve one house.
- A copied room keeps the source's own lights, shadow casters among them, on the source's bases.
- A copied room keeps its source navmesh only when it is one island reaching every arrival and every piece of
  furniture; else the build meshes it again and says why.
- A room may be stripped of what it must not bring: the added door's `room.drop` `{source ref id: why}` (a container
  of levelled treasure), Nordic pieces swapped by `draft.replace` where an easy swap exists.
- Part of a large cell is copied by a cut: the added door's `room.cut` `{"box": [x1, y1, x2, y2]}` keeps only what
  lies inside the box, the way out is a load door inside it, and the build meshes the cut room's navmesh itself.
  Close every opening the cut leaves with the kit's own door or wall piece. `room.strip` `{base editor id: why}`
  takes out every piece of a base (the cell's enemies, traps, levers and treasure).
- A person works in an added room by the row's `work_for` (the people stage gives them their work stop there).

## A building a story needs and the source lacks

Add it whole from a place of our mods that has it, laid as that place lays it: the exterior piece, then each piece
set on it (door, frame) as a `draft.add` row with `on` (the building row's id) and `dz`, at the source's offsets and
turn, on flat dry ground clear of every solid and off the streets. Leave out a piece set into the wall round the
door. The door carries `room`: `copy_of` `<source_id>/<cell>`, `door` (the cell's way out), `space` (our space
id), `arrival` (in front of the door), `drop`. Where the door opens onto a porch, lay the source's walkway off it and
give it `walk` where its mesh's top is a rail. The `add` stage copies the room, pairs the doors, removes every further
way out and lays a path from the arrival to the nearest street.

## A room inside another, a back door

- A room behind a door inside another (a strongroom off a hall) is a `draft.add` door standing in that room,
  `space` set, with `room` and an `arrival` [x, y, z] on the room's floor.
- A further way in (a back door) is a pair of added doors: one in the room, one outside naming it in `pair`, each
  with its `arrival`.
- Put every inner door on a wall whose floor the source's navmesh covers.
- A door's lock is its row's `lock` ({level, key, flags}); the key's keeper is a stock row (`place-stock`).

## Room names

The tools name each room from the place's data (`docs/design/place-studio.md`, Room names): the promise kept in it,
else its household's head ("Ixtul-Bei's House"), else the source's name unless it is a builder's leftover. A room
nothing names is your call in `draft.room_names` `{space: {name, why}}`, named for what a player finds inside. Run
`names` after any change to who lives or works where, then `clearance` and `streets` after an added building.

Enforced by the checks: every room named, no leftover name, no two alike (`draft check`); doors paired and rooms
reached (the build's `doors` and `rooms` checks).

Each room's people and stock follow as for any room (`place-routines`, `place-people`, `place-stock`).
