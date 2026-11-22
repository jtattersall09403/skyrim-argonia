---
name: place-story
description: What the stories need of a place - first spots for every quest thing and quest person at the place, things a story needs placed by hand (a sealed jar, a locked chest, a map marker), each quest state of the place (a sick Hist, a dead Hist ending) built and shown in the studio, and the needs judgement and sight test that prove a player would recognise each. Use in every place draft, when a quest placement at a place changes, and when a quest thing has no spot.
---

# Quest things and the stories' needs

Step 8 of the place path ([place-system](../place-system/SKILL.md)). Stages: `quests`, `add`.

Every quest thing and person at the place stands where a player finds it and recognises it: placed by hand, then
sight-tested at eye level from where the player comes (`look <place> at <spot> --stand x,y`: the eye at that point).

## Quest things get first spots

Every quest placement at the place gets a first spot without being asked: the `quests` stage
(`python3 -m tools.places draft quests <place_id>`, or `quest-draft <place_id>`) drafts a row in
`quests.jsonl` from the placement's words on the place's rows and walking mesh. The owner's rows (no `drafted`) are
never changed. Read its `unresolved` list and look at each spot (`look at <spot id>`); move a first spot by hand onto the thing the
words name (a guard at the fire, the key holder at the door) and commit it. A quest thing with no spot
after the stage names nothing the place holds: give the place the thing the words name, or fix the words.

A quest person who lives in the place is cast as the place's person in that role: one person, never two
(`place-people`).

## A thing a story needs, placed by hand

A `draft.add` row: `space` (a room) or none (outside), `need` (the need's seq), `name` where the player must read
it (a container), `tier`, `why`; owner, lock, key and contents are a stock row (`place-stock`). Choose a base the
source or the marsh's mods hold that reads as the thing. Point the need's `rests` at it. Outside, it stands on
ground that carries its whole footprint; the tools move one that does not, and `draft check` fails one with no
ground under part of it. A thing set on another names that row's id in `on` with `dz`. A map marker a story names is
a row on `Skyrim.esm:000010` with `map_marker` (the name the map shows).

## Needs and the sight test

1. `python3 -m tools.places needs open <place_id>` lists the needs not yet judged. Judge each from the player's
   side only: met when it is in the place files and a player told nothing would know it by its look, its game label
   (a room's name, a map marker, a named thing), what stands by it, or a named person who tells them. A building that
   could serve is not met: say what narrow addition (a name, a lock, a thing, a person's spot) closes the gap.
2. `python3 -m tools.places sight <place_id>` prepares what a player sees at each need's spot; one fresh `reader`
   says what each spot is before being shown the needs; record each need's result with
   `python3 -m tools.places needs sight <place_id> <seq> --result recognised|"not recognised" --said "<the reader's words>"`.
3. `python3 -m tools.places needs check <place_id>` passes.

## Quest states

A quest that changes the place (a sick Hist, a dead Hist ending, a person moved or switched off) gives the place a
state, and each state is built with the place: `newworld/places/<place_id>/states.jsonl` (`tools/places/states.py`),
one row per state, exactly one `default` (the game's start):

`{id, name, default?, set_by: {quest, stage | ending(s), flag}, parents: {<enable parent ref>: true|false}, hide: [people or quest refs switched off], moves: {<id>: [x, y, z]}, key: [refs], why}`

1. The promise list's `[state]` sentences say which states the quests need. The quest record keeps what sets each.
2. Show a state by enable parents, as the game does: the source's own living/dead parent where it has one (King of
   the Murkmire's villages carry one), else a marker added as the parent. Each ref of the state carries
   `enable_parent` `{ref, flags}`: `"0"` shows with the parent, `SetEnableStateToOppositeOfParent` shows without it.
3. **A dead Hist (an ending):** the tree's dead twin (King of the Murkmire's `*Dead` Hist beside each living one) on
   the opposite flag; the living tree, its sap pool, its clutch of eggs and its lanterns on the living flag, so the
   eggs go with the tree and the pool goes cold; the village's people the ending switches off in `hide`.
4. **A sick Hist:** what the sources hold for it: King of the Murkmire's dead roots set round the living tree, its
   bark darkened (main-plot's sick Hist); the living sap pool kept or swapped for a dull one; the healed state, if a
   quest heals it, is the same parent the other way.
5. `key` names the refs that make the state recognisable; the promises check fails a state sentence with no state
   row and a state with no key shown in it.
6. Check each state as the player sees it: `python -m tools.places states <place_id>` lists them and what each hides;
   `look <place> at <key ref> --state <state>` for a capture per state; the owner chooses it in the studio's Quest
   state switch (both views), where his edits are marked with the state they were made in.
