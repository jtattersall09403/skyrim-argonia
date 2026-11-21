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
subject is seen, the subject fills under 3% of the frame while another piece fills more, the camera stands on or
inside its own subject, the camera is under the ground or inside a piece (a tree's crown or trunk), no ground is
drawn, one piece covers half the lens, or a piece within 200 units of the lens covers over 4% of it (a leaf, a sail,
a post). The thresholds are named in one place, `tools/places/look/capture.py`. `at` then tries again by itself: the other sides, further, higher, the canopy cut,
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
it is. A model that did not load is drawn as a box of its bounds, hatched and labelled: a fault of the place. Every
view's `census` says what the page holds and drew: pieces sent (against the numbers' count), models loaded, pieces
drawn as stand-ins with each failed model and why, models with nothing drawable (a furniture marker), effects and
helpers hidden, instances drawn in the frame by kind, and the
page's own errors; a mismatch is a `warn`. `--once` takes the asked
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
| `playwalk [<from> <to>] [--plan] [--changed] [--stride u] [--again] [--full]` | The place walked as a player meets it, as a tour on its built walkable mesh (below). |

## Playwalk: the place as a player walks it

`playwalk` with no names walks the place as a TOUR: one closed walk from where the player arrives (the landing,
else a road's end that leaves the place, else a quest arrival) through the centre (the landing, else the middle of
the stalls, else of the doors), past every door's arrival, stall, crafting station, the Hist and its sap pool (one
stop) and every quest spot, once each, and back. The stops are ordered by walking distance over the mesh (nearest
neighbour, then 2-opt). A stretch already walked costs three times as much to walk again, so the tour loops where
the mesh allows and retraces only where there is no other way; a station within 400 units of one already shot is
not shot again. One tour is walked per island of the mesh an arrival stands on, and a place whose tour is longer
than 90000 units is cut into two or three tours that each leave and return to the centre. A thing on no arrival's
island is listed "CANNOT BE WALKED TO" with where and how the mesh breaks, and walked to the break (one look
there). A street with a building beside an unwalked stretch that no station is within 600 units of gets a short
spur to the end of that stretch. Each route is the shortest walk over the BUILT mesh's triangles (`playwalk.astar`,
straightened inside the corridor), so it climbs the stairs and crosses the bridges a person would. A mesh older than
the place files is said STALE and every strip is marked so; with no built mesh the place's paths are walked instead
and the plan says "walked on the place's paths, not the mesh". `playwalk <from> <to>` walks one route (names as for
every verb, plus `landing`, `centre`, `market`) with a station every 256 units and the old full look set.
`--full` plans one route from the arrival to every thing and along every street, every route with the old look set
(about 15 times the looks of a tour). `--plan` prints the plan only: the count of routes, stations and looks, each
route with its stops.

Stations stand on the mesh: one every 768 units on a tour (`--stride u`), and always at each stair or ramp foot and
head, each bridge or walkway start, middle and end, each doorway, the approach to a door (320 units before it) and
the end of each stop; turns and deck edges are not stations on a tour. At an ordinary station, from a person's eye:
ahead and 20 degrees down (80 degrees across at 4:3, the game's first-person view, in the neutral fill), and left
or right where a building stands within 600 units to that side and no earlier look took it (every house is seen
once from the way past it). The full set (ahead, down, up, left, right, back and the two forward diagonals) is
taken only at a doorway (the door from the walk, then from the doorstep, the way back), the foot and head of
stairs and ramps, a bridge's or walkway's start and middle, a quest spot, the Hist and its pool, and where the tour
first enters the place; a bridge, walkway, stair or ramp station within 700 units of an earlier full-set station,
and a doorstep within 700 of one, takes the short set (a door: ahead, down, back); the approach to a door is
ahead only. Where a stop is a thing (a stall, a station, the Hist), the eye faces it from the end of the walk. A
`<from> <to>` route and `--full` keep a station every 256 units (768 on `--full`), and at each: ahead, down, up,
left, right, back, and at stairs, bridges, doorways and turns the two forward diagonals.

Each look is judged by its id buffer. A capture fault (the camera in a piece, one thing nearer than 100 units over
60% of the frame, no ground drawn) is shot again from a nudged spot (along the walk up to 64 units, sideways on the
mesh), else struck through in red with its reason. The same evidence names faults of the place, marked PLACE in
orange: every spot near the station inside one piece (the way passes through it); a wall filling the view ahead at
a doorway (the door opens onto a wall); no boards under a bridge's middle looking down (a gap); in a room, the void
seen.

Out, under `out/places/look/<tree>/<place>/playwalk/<route>/` (a tour is `tour`, or `tour-1`.. when there are
several; a spur `spur-<street>-<n>`): `strip-NN.jpg` (JPEG at quality 88; one row a station, a column a look, at
most 8 stations a strip), `forward.jpg` (the walk facing ahead), `map.png` (the route over the mesh, numbered),
`tiles/` (every look full size, PNG) and `table.txt`/`table.json` (each look's file, verdict and the three things
filling most of the frame). The plan's counts are the first line of the output and the seconds and megabytes the
last. A route already shot as planned is skipped on a rerun (`--again` shoots it anew), so an interrupted walk
resumes. `--changed` walks only the routes passing within 1000 units of a structure changed since this checkout's
last playwalk.

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
7. Judge the whole with the place's survey and `playwalk` (the tour, then `playwalk --rooms`) once the numbers
   are clean.

Every call appends a line to `out/places/look/<tree>/session.log` (verb, arguments, image, milliseconds). A sequence that
has worked by hand on several places is the record from which a pipeline step is written; nothing becomes a step
before that.

## What a capture guarantees, and what it does not

`python -m tools.places look truth` proves the guarantees on a golden scene of coloured-box models whose answers are
known (`tools/tests/fixtures/look_truth`), against a ray caster of its own: about two minutes, one daemon of its own,
one line per check and a report (`truth.json`) with each failure's image. `look truth <place> --sample 40` audits a
real draft: forty pieces at random across kinds (effects and helpers aside), each by the tool's own `at`, must be
drawn in frame with every drawn pixel inside their box's projection, and, when at least 90% of the piece is seen, the
silhouette's centre within 5% of the frame of the box's. Run it when the look tool or the studio's
drawing code changes; `LOOK_TRUTH=1 pytest tools/tests/test_places_look_truth.py` runs the same.

Guaranteed, each by an assertion:
- Every piece is drawn where its record puts it (its silhouette within 2 px of its projected boxes from the side,
  above and the eye); `--top` is north-up; a section's ground line sits at the row the heights say, on flat ground,
  a slope and land raised or lowered by several land rows (they add), and its scale is the stated units per pixel.
- An eye camera stands at eye height over the ground or deck under the camera itself, never under the ground and
  never inside a piece, on a slope, a mound, by a deck, beside a wall and under a crown.
- `seen`, `fills` and the first occluder agree with the oracle within 0.04, 0.01 and exactly; the verdicts for a
  subject behind a crown, seen from on its roof, small and far, or behind a leaf at the lens are `failed`.
- `pick` returns the piece drawn at the pixel, a pool included.
- Every piece sent is counted; a model that fails to load is a listed, hatched stand-in; markers are hidden unless
  `--helpers`.
- A look draws the place files as they stand in the working tree, as the numbers read them: a change to the files,
  a commit, an undo or a restore shows at the next look without a restart (a new ground or source bundle reloads
  too, not yet asserted), and every
  answer names the state it drew (`drew`: the files' hash, the commit, whether the tree differs, the bundles'
  stamps). Each checkout has its own daemon, port and draft bundles; looks in one millisecond keep separate files.
- A room draws every piece of its source room.

Not guaranteed: the viewer draws no grass unless asked, no effects (fire, fog, mist, glows), and its light is not
the game's; placed water is the studio's approximation of its surface, and a section shows no line for a flat water
sheet seen edge-on; a section's land is the drawn ground line, not the page's surface (flat land is edge-on); the
pictures are software-rendered, seconds a view on a warm daemon and minutes for the first load of a large place.

## The machine

The first call starts the daemon (its own studio server and one headless Chromium, software GL) and
loads the place; later calls reuse both. The daemon leaves after 15 minutes without a call, browser and server with
it (`look stop` ends it at once). Its session lives on disk, so a restart picks up where it was.
