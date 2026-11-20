---
name: place-look
description: The drafter's eyes and hands in the studio's own 3D scene, outside and inside a room - probe for faults, section, at, orbit, walk and overview to judge, move, turn, sink, delete, duplicate and lay steps in a scratch session, compare fixes and commit the session into the place files as the agent's draft edits; and the hand-over look every place passes before the owner sees it. Use for any floating, buried or missing piece, any piece or structure to move, and before handing a place over.
---

# Look, probe and act

Step 9 of the place path ([place-system](../place-system/SKILL.md)), and the inner loop of every other step. The
tool is `python -m tools.places look <place> <verb> [args]`; its contract is `docs/design/agent-view.md`.

## Which verb

- **Measure for truth, look for judgement.** Whether a piece is held up, buried or floating is a number: `probe`.
  Whether a place reads well, a street is open or a group of huts looks right is a picture.
- **Name what to look at; the tool places the camera**: a structure (`b04`), a piece id or its last characters, a
  door by its room, a person, a quest spot id, a unit (`house.SeekhatEldersHut`, `dock.03`), or `x,y`.

## Reading a capture

Every view answers, per image, what it shows: `subject_seen` (the share of the subject's own pixels visible and in
the frame), `subject_fills` (its share of the frame), `occluders` (the three biggest things over the rest), and
`capture: good` or `failed` with `why`. A capture fails when under 35% of its subject is seen, the camera stands
inside or under something, no ground is drawn, or one piece covers half the lens; its image then carries the reason
in a red banner and `at` tries again by itself (other sides, further, higher, the canopy cut) until one is good, or
says no good capture is to be had and why. A failed capture is a fault of the camera, never of the place: judge
nothing from it. Of every capture you keep, ask whether it shows what it was meant to. Light is not judged from the
viewer: the game lights the place differently.

| Need | Verb |
|---|---|
| Every fault in the place | `probe --all` (floats, missing base, unresolved model, walkway end with nothing under it, door with no ground) |
| One piece's feet, rest and neighbours | `probe <thing>` |
| Heights at a glance; proof a piece is seated | `section <thing> --axis` or `section <x1,y1> <x2,y2>` |
| Judge a structure from every side at once | `survey <place> [<structure or unit> ...]`, `survey <place> --changed`: the sheet is the index; read each tile in `survey/<structure>/tiles/` (1280x960, listed with its score in `table.txt`) for detail |
| One more look at a structure | `at <thing> [--from n..nw] [--eye\|--high\|--top]` (1920x1440; `--grid` adds the ground grid, off by default), `orbit <thing>` (each panel its own file) |
| The numbers of every house, deck, door, tree and loose piece | `measure` |
| See what stands under trees | any view with `--no-canopy` (from high or above it is cut by itself when the canopy hides most of the subject) |
| Is the way open | `walk <from> <to>` |
| Where to look next | `overview` |
| What is at a pixel | `pick <png> <px> <py>`: what is drawn there, then what lies behind it |
| What the game never draws (markers, collision boxes, triggers) | any view with `--helpers`, each labelled |
| Why a door or deck is cut off; where the built mesh breaks | `probe --mesh [<a> <b>]`; any view with `--mesh` (doors and street points judged by the build check's own rule) |
| Anything inside a room | `in <room> <verb> ...` (below) |

## Working a fault

1. `overview`, `probe --all` and `measure`; the measure table's flags are the fault list to start from.
2. For each fault a `section` through it; `pick` anything in the image the probe did not name.
3. `snapshot <name>`; act with a hand and its `--view`: `move <thing> dx dy dz`, `turn <thing> deg`, `sink <thing>
   [units | --until-feet-buried]`, `delete <thing>`, `duplicate <thing> [dx dy] --why "<why>"`, `steps <deck,
   structure or door> <point or thing>`. A structure named by its unit id (`units <place>`, `place-site`) moves, turns or sinks whole, and a house's body
   is never moved without its deck unless `--piece` is given; `move` and
   `sink` answer with each deck's height over the ground before and after, which is the number to judge. A copy
   is seated where it stands and carries the reason you give it. `steps` lays one flight of the place's own kit
   from the deck edge facing the point down to the ground. Seat by sinking; never stretch.
4. `probe <thing>` to prove it held, and `survey <place> --changed` after every structure placed or changed
   (seconds a structure on a warm daemon); `survey <place>` of the whole after each group. When two fixes compete, `compare` them on one view, keep the better,
   `restore` it; `undo` takes back a stroke.
5. `look commit -m "<why>"` writes the session into the place files as the agent's draft edits
   (`agent-edits/<save_id>.json`), never over a row of an owner's finalised save (those strokes are listed in
   `left_for_owner`). Commit the place files by path.

Faults with a known cause:

- **Missing bases** across many pieces: the draft bundle is older than the catalogue. Rebuild it with
  `python -m tools.places draft_bundle <place_id> --force` and probe again.
- **A lantern in the air**: its tree moved; `draft hang` (`place-dressing`).
- **A piece floating over a dropped floor or a moved deck**: sink its whole structure, never the piece alone.

A `streets` run or a whole draft rewrites the place files: commit the look session first and use no hand until it
ends, or its strokes are lost.

## Inside a room

`look <place> in <room> <verb> ...` runs every verb inside a room, named by its space id or the name its door
shows; `door` names its way out. The room is drawn in its own light; `--lit` adds a neutral fill for judging shape.

1. `in <room> overview`: from above with the ceiling cut away, and from where the way in lands at eye height.
2. `in <room> probe --all`: floating and unresolved pieces, a door with no floor, and every **opening onto the
   void** (a cut room's edge left open, a hole in the shell), each with the side it lies to and where. An opening
   seen only from floor behind a closed door is one the player meets only by opening it: say which.
3. `in <room> at <thing> --eye` for what a player sees; `in <room> walk door <thing>` from the way in.
4. The hands work there as outside; a copy keeps its height.

## The hand-over look

Before a place goes to the owner (the bar in `place-system`):

1. `probe --all` reports nothing.
2. `survey <place>` and `survey <place> <structure>` for each structure, every tile good or struck through with
   its reason; a `walk` along the main streets; for each room a story needs, its `in <room> overview` and `probe --all`.
3. Read every image. Match each sentence of the record's `look` to an image that shows it; name each line not yet
   met in the hand-over.
4. Judge the whole: does it read as the record's place sitting naturally on our land? If not, go back to the skill
   that owns what is wrong.

## The machine

The first call starts the daemon (its own studio server and a headless browser), which leaves after 15 minutes
idle (`look stop` ends it). Each checkout has its own daemon, session and port. Every call is logged to
`out/places/look/<tree>/session.log`.
