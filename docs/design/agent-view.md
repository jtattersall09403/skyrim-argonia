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
by its spot id, a unit (`house.SeekhatEldersHut`, `dock.03`: tools/places/units.py), or a point `x,y` (`x,y,z`). An unknown name answers with the structures there are.

## Inside a room

`look <place> in <room> <verb> ...` runs any verb inside a room: the room is named by its space id or the name its
door shows (`in "Vosh-Leera's House"`). The page enters the room as the studio does and draws the pieces the build
keeps (the source cell's copy with our rows over it, kept to its room and its cut; a room added from another place
of our mods is read from that place's source). The room's floor (the walkable mesh its source cell was built with,
kept to the cut) stands in for the ground: heights, floats and a door's ground are measured from it, and `door`
names the room's way out, standing where the way in lands.

- The room is drawn in its own lighting (the cell's). `--lit` adds a neutral fill over it for judging shape.
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
| `pick <png> <px> <py>` | What is drawn at a pixel of a look (from the image's id buffer: the piece, its base, model, structure; a marker or a model that did not load says so), then what lies behind it along the ray with each one's lowest point over the ground, and the ground point the pixel falls on. |
| `measure` | The place's table, numbers only: every unit's (`units <place>`: each house's floor, the ground under it, its deck and the gap between, its doors and steps; each dock, walkway and bridge with its joins), each house's eaves over the ground (an estimate from its box), each tree's root collar against the ground, each loose piece's lowest point; each flagged by its rule (floor under the ground, through its deck, a door off its floor, eaves under 150, a collar more than 60 under the ground, an end with nothing under it). |
| `probe --mesh [<a> <b>]` | The built walkable mesh (the navmesh of the place's newest build: its own draft check, else the shared build): its islands, each with its triangles and the doors and street points on it, the doors and street points off the main network by the build check's own rule (a street sampled every 64 units, `walk.off_network`; a door off when its navmesh is an island, `walk.islands`), so its count is the check's; with two things, whether a walk joins them (a structure measured from its door's arrival, else its largest deck) and, if not, where the mesh breaks between them (the two open edges, the gap across and the height step, `height step` or `missing strip`, and the pieces there). Says `STALE` when a place file is newer than that build. The first call on a build reads it whole (a few minutes on a village); later calls are quick. |

What holds a piece up: something whose top is from 24 units under its lowest point to 160 over it (a post rising
through a deck holds the deck; a house's roof far above does not). A tree holds up nothing from below, but a
lantern, sconce or sign hangs from what its top is inside, and a flower, vine or pot is held by the trunk or wall it
grows on. The world's own trees and rocks around the place count. Effects (mist, fire, spray) are never faults.

## Views

Each view prints a PNG path and what it shows, from an id buffer drawn with the image: `subject_seen` (the share of
the subject's own projected pixels visible and inside the frame), `subject_fills` (its share of the frame),
`occluders` (the three biggest pieces over the rest, by piece and kind), the land, water and sky shares, and
`capture`. A capture is `failed`, with `why` in the JSON and in a red banner across the image, when under 35% of its
subject is seen, the camera is under the ground or inside a piece (a tree's crown or trunk), no ground is drawn, or
one piece covers half the lens. `at` then tries again by itself: the other sides, further, higher, the canopy cut,
until a capture is good or it says no good one is to be had and why (`failed_tries` lists each with its image). A
thing much taller than wide is framed whole, and a second view shows its base. An eye camera stands at a person's
eye over the walkable mesh where it is loaded, else a deck, bridge or walkway, else the ground, never inside a piece.
Light is not judged from the viewer: the game lights a place differently.

Labels are on by default: structure ids where they stand, a 1.8 m figure at the
subject, a north arrow, the side seen from, red outlines on what `probe --all` faults. `--grid` adds the ground grid
with its spacing (off by default: it hides the place). `--plain` drops all of them. Every view is 1920x1440 (4:3):
a single view, each panel of an orbit, a walk and an overview; `--size WxH` sets it (per panel). Every label, line,
figure and outline is drawn in proportion to the width (768 wide is the unit), so a label reads the same at any size.
`orbit` and `walk` save each panel as its own file (`<name>-N.png`) and the sheet as an index of the same panels at
640x480; `pick` takes pixels of the full-size image. `--grass` the grown grass, `--lit` a neutral
fill light. What the game never draws (editor markers: x-markers, heading, idle, furniture and patrol markers;
collision boxes, triggers, occlusion planes, light bulbs) is left out; `--helpers` shows it, each labelled with what
it is. A model that did not load is drawn hatched and labelled: a fault of the place. `--once` takes the asked
view only, without retries. `--mesh` lays the built walkable mesh over any view: each island in its own colour (the main network green) with its id, door arrivals as squares and street points as dots, white on the main network and red off it by the check's rule; a section keeps the triangles in its slab.

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
| `survey [<structure or unit> ...] [--changed]` | One contact sheet per thing named, else the whole place: near and far from the four compass sides at eye level, two high obliques, a top view with the crowns cut, sections on two axes with the ground line and a height scale, in the neutral fill, and one tile in the place's own light (labelled "viewer light, not the game's"). Every tile is drawn at 1280x960 and saved as its own file, `tiles/NN-<side>-<near|far|high|top|lit>.png` or `tiles/NN-section-<axis>.png` (with its id buffer, drawn 384 wide and enlarged, so `pick` works on it), carrying its side, distance and score; a failed tile is retried once, else struck through with its reason. The sheet is the index: the same tiles at 640x480, four across (2560 wide); `pick` on a sheet answers from the tile under the pixel. Beside the sheet, `table.json` and `table.txt` list what each tile shows with each tile's file; all under `out/places/look/<tree>/<place>/survey/<thing>/`. Read the tiles one by one for detail, the sheet to choose which. `--changed` takes only the structures whose rows changed since this checkout's last survey. Prints one line per thing: its sheet and its failed tiles. The tiles go in one page call: seconds a structure on a warm daemon. |
| `playwalk [<from> <to>] [--plan] [--changed] [--stride u] [--again]` | The place walked as a player meets it, on its built walkable mesh (below). |

## Playwalk: the place as a player walks it

`playwalk` with no names plans the place's routes: from where the player arrives (the landing, each road's end
that leaves the place, a quest arrival) to the centre (the landing, else the middle of the stalls, else of the
doors); from the centre to each door's arrival, each stall, each crafting station, the Hist and its sap pool and
each quest spot; and along each street. Each route is the shortest walk over the BUILT mesh's triangles
(`playwalk.astar`, straightened inside the corridor), so it climbs the stairs and crosses the bridges a person
would. A thing the mesh cannot reach from the arrival is listed "CANNOT BE WALKED TO" with where and how the mesh
breaks, and the route is walked to the break. A mesh older than the place files is said STALE and every strip is
marked so; with no built mesh the place's paths are walked instead and the plan says "walked on the place's paths,
not the mesh". `playwalk <from> <to>` walks one route (names as for every verb, plus `landing`, `centre`,
`market`). `--plan` prints the plan only: routes, lengths, stations, how many are new.

Stations stand on the mesh: one every 256 units on a named route (768 on a whole place, `--stride u`), and always
at each stair or ramp foot and head, each bridge or walkway start, middle and end, each doorway, each turn sharper
than 45 degrees and each stretch within 150 units of a deck edge with a drop beside it. A station seen on an
earlier route (same spot, same heading) is not shot again; the table names where it was. At each station, from a
person's eye: ahead, 20 degrees down, 20 degrees up, left, right, back, and at stairs, bridges, doorways and turns
the two forward diagonals; 80 degrees across at 4:3 (the game's first-person view), in the neutral fill.

Each look is judged by its id buffer. A capture fault (the camera in a piece, one thing nearer than 100 units over
60% of the frame, no ground drawn) is shot again from a nudged spot (along the walk up to 64 units, sideways on the
mesh), else struck through in red with its reason. The same evidence names faults of the place, marked PLACE in
orange: every spot near the station inside one piece (the way passes through it; indoors, a ceiling lower than a
person); a wall filling the view ahead at a doorway (the door opens onto a wall); no boards under a bridge's middle
looking down (a gap); in a room, the void seen.

Out, under `out/places/look/<tree>/<place>/playwalk/<route>/`: `strip-NN.png` (one row a station, a column a
look, at most 8 stations a strip), `forward.png` (the walk facing ahead), `map.png` (the route over the mesh,
numbered), `tiles/` (every look full size) and `table.txt`/`table.json` (each look's file, verdict and the three
things filling most of the frame). A route already shot as planned is skipped on a rerun (`--again` shoots it
anew), so an interrupted walk resumes. `--changed` walks only the routes passing within 1000 units of a structure
changed since this checkout's last playwalk.

Rooms: `in <room> playwalk` and `playwalk --rooms` (every room, one line each). A room copied whole and unchanged
gets the entering set at each door: just inside, looking in, left and right. A room we changed (a cut, source
pieces struck, pieces added or moved, a quest spot, a person's work spot in it; from the place files,
`playwalk.room_kind`) gets that, then one station at each thing changed and each spot (ahead, down, left, right,
walked from the first door) and one look at each side of a cut. Every room look is tested for the void.

Reading a strip: read the forward filmstrip first (does the walk read as a way?), then each row: what the player
sees stepping there. A struck tile in red is the camera's: judge nothing from it. An orange PLACE tile is a fault to
fix at its station. Bare ground is not a fault: the viewer draws no grass. Light is not judged.

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

1. `overview`, `probe --all` and `measure`.
2. For each fault, a `section` through it; `pick` anything in the image that is not what the probe named.
3. `snapshot` before trying a fix; act with a hand and its `--view`; `probe <thing>` to prove it held.
4. When two fixes compete, `compare` them on the same view, keep the better, `restore` it.
5. `survey --changed` after every structure placed or changed; `survey` of the whole place after each group; judge
   only from good captures, and of each ask whether it shows what it was meant to.
6. `playwalk <from> <to>` across every stair, bridge, door or street you changed, straight after the change.
7. Judge the whole with the place's survey and `playwalk` (every route, then `playwalk --rooms`) once the numbers
   are clean.

Every call appends a line to `out/places/look/<tree>/session.log` (verb, arguments, image, milliseconds). A sequence that
has worked by hand on several places is the record from which a pipeline step is written; nothing becomes a step
before that.

## The machine

The first call starts the daemon (its own studio server and one headless Chromium, software GL) and
loads the place; later calls reuse both. The daemon leaves after 15 minutes without a call, browser and server with
it (`look stop` ends it at once). Its session lives on disk, so a restart picks up where it was.
