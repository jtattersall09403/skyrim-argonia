# The agent view: eyes and hands in the place studio

An agent works on a place the way a designer does: it looks at the place in 3D from where it needs to, measures,
changes one thing, looks again, and judges. The tool is `python -m tools.places look <place> <verb> [args]`
(`tools/places/look/`). It drives the owner's own studio (the same models, ground, water and edit operations)
through a page mode with no interface, `/?place=<id>&agent=1`, in one headless browser kept warm between calls.

Two rules decide which verb to reach for:

- **Measure for truth, look for judgement.** Whether a piece is held up, buried or floating is a number: `probe`.
  Whether a place reads well, a street is open or a group of huts looks right is a picture: the view verbs.
- **Name what to look at; the tool places the camera.** Never fly a camera: name a structure, a piece, a door, a
  person, a quest thing or `x,y`, and a side of the compass.

## Names

A thing is named by any of: a structure (its cluster id: `b04`, `s06`, `landing`), a piece id or its last
characters (`GS6YH2YT`), a door by the room it leads to (`SeekhatEldersHut`), a person by id or name, a quest thing
by its spot id, or a point `x,y` (`x,y,z`). An unknown name answers with the structures there are.

## Inside a room

`look <place> in <room> <verb> ...` runs any verb inside a room: the room is named by its space id or the name its
door shows (`in "Vosh-Leera's House"`). The page enters the room as the studio does and draws the pieces the build
keeps (the source cell's copy with our rows over it, kept to its room and its cut; a room added from another place
of our mods is read from that place's source). The room's floor (the walkable mesh its source cell was built with,
kept to the cut) stands in for the ground: heights, floats and a door's ground are measured from it, and `door`
names the room's way out, standing where the way in lands.

- The room is lit by its own lighting (the cell's, as the game lights it). `--lit` adds a neutral fill over it, for
  judging the shape of a dark room; judge the light itself without it.
- `overview` of a room: straight down with the ceiling cut away (`--ceiling u` over the floor, 330 by default), and
  one eye-level view from where the way in lands. `at --high` and `--top` cut the ceiling too; `at --eye` stands
  the camera on the room's floor, never behind a wall or a door.
- `probe --all` in a room adds **openings onto the void**: from points spread over the walkable floor, at eye
  height, six looks with a background no model has; every way out of the shell (a cut room's edge left open, a
  hole) is listed with the side it lies to, where it meets the room's box and the floor points that see it. A
  piece of the kit fixed to the wall or pillar its box touches (an arch, a bust in a niche) is held.

## Numbers

| Verb | For |
|---|---|
| `probe --all` | Every fault in the place: a piece that **floats** (its lowest point over the ground under it, and no chain of resting reaches the ground), a **missing base** or an **unresolved** model (a stand-in box), a bridge or walkway **end** with nothing under it, a **door** with no ground before it. Run it first, and after every change. |
| `probe <thing>` | Per piece: its box, each foot's height over the ground (negative: buried), what it rests on, its nearest neighbours and the gap to each; a span's two ends; a door's ground. |
| `pick <png> <px> <py>` | What is at a pixel of a look: the piece, its base, model, structure, and its lowest point over the ground; and the ground point the pixel falls on. |
| `probe --mesh [<a> <b>]` | The built walkable mesh (the navmesh of the place's newest build: its own draft check, else the shared build): its islands, each with its triangles and the doors and street points on it, the doors and street points off the main network by the build check's own rule (a street sampled every 64 units, `walk.off_network`; a door off when its navmesh is an island, `walk.islands`), so its count is the check's; with two things, whether a walk joins them (a structure measured from its door's arrival, else its largest deck) and, if not, where the mesh breaks between them (the two open edges, the gap across and the height step, `height step` or `missing strip`, and the pieces there). Says `STALE` when a place file is newer than that build. The first call on a build reads it whole (a few minutes on a village); later calls are quick. |

What holds a piece up: something whose top is from 24 units under its lowest point to 160 over it (a post rising
through a deck holds the deck; a house's roof far above does not). A tree holds up nothing from below, but a
lantern, sconce or sign hangs from what its top is inside, and a flower, vine or pot is held by the trunk or wall it
grows on. The world's own trees and rocks around the place count. Effects (mist, fire, spray) are never faults.

## Views

Each view prints a PNG path. Labels are on by default: structure ids where they stand, a 1.8 m figure at the
subject, a north arrow, the side seen from, the ground grid and its spacing, red outlines on what `probe --all`
faults. `--plain` drops them, `--size WxH` sets the image (768x576 by default), `--helpers` shows the editor's light
bulbs and collision boxes, `--grass` the grown grass. `--mesh` lays the built walkable mesh over any view: each island in its own colour (the main network green) with its id, door arrivals as squares and street points as dots, white on the main network and red off it by the check's rule; a section keeps the triangles in its slab.

Trees hide what stands under them. `--no-canopy` cuts away every tree crown, Hist and hanging moss or vine over
head height at the subject (250 units over its ground) and keeps their trunks and roots; `--high` and `--top` cut
it by themselves when the canopy hides more than half the subject from the camera (the answer says so, with what
hid it), and `--canopy` keeps it.

| Verb | For |
|---|---|
| `section <thing> --axis` or `section <x1,y1> <x2,y2>` | The truth of heights at a glance: an orthographic side-on cut along a line, with the ground profile, the water, a height scale, each crossed piece outlined by its own mesh in the slab (a flight's treads too, which a side view sees edge-on) and its height over the ground. The first look at anything a probe calls floating, and the proof after it is seated. `--slab u` sets how much either side of the line is kept (96). |
| `at <thing> [--from n..nw] [--eye\|--high\|--top]` | One framed look at a thing from a side: oblique by default, from a person's eye, from high, or straight down. For judging a structure. |
| `orbit <thing>` | The same thing from north, east, south and west on one sheet: what one side hides. |
| `walk <from> <to>` | Six eye-level frames along the place's streets and paths between two doors or points: whether the way is open and reads as a street. |
| `overview` | The whole place obliquely and from above, every structure labelled: where to look next. |

## Hands

`move <thing> dx dy dz`, `turn <thing> deg` (clockwise from above, about the thing's middle), `sink <thing>
[units | --until-feet-buried]`, `delete <thing>`, `duplicate <thing> [dx dy] --why "<why the copy is here>"`,
`steps <from deck, structure or door> <to point or thing> [--why ...]`. `move` and `sink` answer with each deck
piece's walked top over the ground before and after (`decks`). A copy gets its own id, its own reason (`--why`,
required) and its own seat where it stands: a seat on the ground keeps its rule, measured afresh there; a piece the
original stood on that is not copied is never the copy's (it goes on what is under it, else on the ground at the
original's height over it). `steps` lays one flight the way the streets stage does: the place's own steps pieces
first, then its decks' kit, hung square off the deck's edge facing the point with its top tread at the deck's
height, its foot where a tread meets the ground; it answers with the piece, its top and its foot. Each is one stroke of the studio's
own ops (`ref.move`, `ref.remove`, `ref.add`, the same kind of change as the owner's), kept in a scratch session
(`out/places/look/<tree>/<place>/session.json`; each checkout, the main tree or a lane's worktree, has its own daemon, session and port) and never written to the place files or the owner's saves. A seated piece
keeps its seat rule: its height moves with its seat's `dz`. Pieces are seated by sinking them into the ground;
nothing is stretched. Add `--view <view verb...>` to any hand for the same look before and after, side by side.

`undo` takes back the last stroke; `snapshot <name>` keeps the session's state; `restore <name>` returns to it;
`compare <a> <b> <view verb...>` shows one look at two states side by side (`now` is the current state); `reset`
empties the session.

`commit -m "<why>"` makes the session permanent: its strokes go into the committed place files through the same
`edits.apply` an owner's finalised save takes (`edits.apply_agent_save`), recorded as the agent's draft edits, not
the owner's: the save is kept at `newworld/places/<place>/agent-edits/<save_id>.json` (`by: agent`, `final: false`)
and listed in `place.json` `agent_saves_applied`; no word gets the owner's tier and no preference is written. A stroke
that touches a row an owner's finalised save touched is left out whole and listed in `left_for_owner`. The session
(and its snapshots) is then emptied; commit the place files by path.

## Working a place

1. `overview`, then `probe --all`.
2. For each fault, a `section` through it; `pick` anything in the image that is not what the probe named.
3. `snapshot` before trying a fix; act with a hand and its `--view`; `probe <thing>` to prove it held.
4. When two fixes compete, `compare` them on the same view, keep the better, `restore` it.
5. Judge the whole with `orbit` and `walk` once the numbers are clean.

Every call appends a line to `out/places/look/<tree>/session.log` (verb, arguments, image, milliseconds). A sequence that
has worked by hand on several places is the record from which a pipeline step is written; nothing becomes a step
before that.

## The machine

The first call starts the daemon (its own studio server and one headless Chromium, software GL) and
loads the place; later calls reuse both. The daemon leaves after 15 minutes without a call, browser and server with
it (`look stop` ends it at once). Its session lives on disk, so a restart picks up where it was.
