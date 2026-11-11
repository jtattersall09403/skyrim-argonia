# New world walk check (nw-02)

The owner's walk of the new Black Marsh world. It sits apart from `docs/owner-walk-checks.md`, which is the walk list
for the Black Marsh & Valenwood game; ticks go here, in the same way. This is the walk after round 3: everything in
the owner's walk 5 feedback of 2026-11-10 on the built world was changed and the whole world rebuilt (terrain build
20261111T053723Z). The off-game read-back is `out/newworld/verify/report.md`
(`tooling/job_guard.sh run nw-verify -- python3 -m tools.newworld.verify`).

---

**What this is.** Black Marsh as a whole world of our own, rebuilt after your walk 5 notes: the ground has more
shape and differs region by region, water kinds look different and rivers run, roads are repainted, the ground cover
is broken up, the air is warm and differs by region, there is more low mist, trees are drawn far away, the map pans
to the edges, and land and sea carry on beyond the borders. You are only looking: nothing here is a quest. Helstrom
the city is not in this world yet: it is laid in after you have walked the world.

**Cost.** The play machine costs about $0.80 an hour while it runs; this walk is about an hour. It stops itself when
idle.

**Getting there.** Open the **"Argonia: New World"** card in Moonlight. Start a new game (or load any save), open the
console with the key under Esc and type `coc ArgoniaNWStart`. You arrive on dry ground in the Valley of Storms, just
south of Stormhold. To jump to any other place, type `coc ANW` and the place's name with no spaces or dashes (for
example `coc ANWLilmoth`, `coc ANWFortGysilla`, `coc ANWUzuTegh`): every one of the 258 places has its own named
cell, and you land on dry ground beside it. The checks below give the exact names. The old `cow ArgoniaBlackMarsh X Y`
commands were the fault you reported: the game cannot address this world's southern cells that way, and took
Helstrom's numbers to open sea far to the north. Do not use them.

**Commands for looking around** (type in the console, then close it):

- `tgm`: you cannot be hurt. `tcl`: walk through anything and fly where you look (type again to stop).
- `player.setav speedmult 400`: run four times as fast (`player.setav speedmult 100` puts it back). Flying with
  `tcl` at more than about four times speed can outrun the game's loading of the land ahead; the crash you had in
  walk 5 was in that loader, on a cell that held only land, water and the walking mesh, with nothing of ours named.
- `tfc`: a free camera that flies away from your body (`tfc 1` also freezes time); `sucsm 500` sets how fast it
  flies. Type `tfc` again to come back.
- `tm`: hide the HUD and menus for a clean look (type again to bring them back; the console still opens).
- `set gamehour to 6` (dawn), `set gamehour to 12` (noon), `set gamehour to 22` (night): the time of day.
- Weather now comes from the region you stand in, by itself. To force one of a region's own weathers, type
  `help ANW_W_ 4` to list them with their numbers (the names read region type, north/middle/south, and Fair, Cloudy,
  Mist, Rain, Storm or Steam), then `fw` and the number shown, for example the number beside
  `ANW_W_GreenMarsh_Middle_Mist`.
- `tg` hides and shows grass, `tt` hides and shows trees: use them only to see the ground underneath.
- M: the map menu.

## The checks

Reply on the issue with the letter of any check that did not look right, what you saw and where (name the place, or
give `getpos x` and `getpos y` from the console). A screenshot helps. Each check names the walk 5 note it answers.

- [ ] **A. Teleports.** (Your note: the coordinates were wrong.) `coc ANWLilmoth`, `coc ANWGideon`, `coc ANWThorn`:
      each lands you on dry ground beside that place, not in water, under the ground or out at sea.
- [ ] **B. Water kinds.** (Your note: all water looked the same.) Visit black swamp water (`coc ANWWalkSwamp`), green
      marsh water (`coc ANWWalkMarsh`), a river (`coc ANWWalkRiver`), a stream (`coc ANWWalkStream`), a pond
      (`coc ANWWalkPond`), an estuary (`coc ANWWalkEstuary`) and the open sea (`coc ANWWalkSea`). The swamp is dark
      tea-brown, opaque and still; the marsh is opaque algae green and still; the pond is clear green and still; the
      river is brown-green and visibly running; the stream is clearer and quicker; the estuary is silty green-brown;
      the sea is a warm blue-green.
- [ ] **C. Flow.** (Your note: all flowing the same way.) At the river and the stream in B, and on the river
      south-west of Helstrom's site (`coc ANWWalkHelstromRiver`): the ripples drift downstream, toward the sea or the
      larger water the channel joins, and follow the channel round its bends (the direction changes a little from
      one stretch to the next: the game sets it per cell). Swamp, marsh and pond do not drift at all.
- [ ] **D. Water seams.** Where two kinds of water meet (follow the river in C into the marsh; fly from the estuary
      out to sea): one surface at one level, and the colour changes gradually, with no straight line or square.
- [ ] **E. Water's edge, near and far.** (Your notes: flicker between water and land, straight hard edges, in free
      camera and on the map.) At `coc ANWWalkSwamp` and `coc ANWWalkSea`, walk the shore, then fly up and away with
      `tcl` or `tfc` and look back along the shore from a distance: the land does not flicker against the water,
      and the far shore follows the land's shape instead of running in long straight lines or squares. The ground
      far off does not flicker either.
- [ ] **F. The map.** (Your notes: hard edges and bad water on the map, light squares, cut off at the edges.) Press
      M: the water on the map follows the shores, with no flicker as you pan and no pale square patches on the land;
      you can pan to every edge of the province (the island in Topal Bay in the east, the oceans to the south and
      west, the land to the north and north-west) and zoom out to see most of it at once. Say also whether the map
      looks right for haze: it is drawn without fog now.
- [ ] **G. Beyond the borders.** (Your note: land beyond our borders, W, N and NW.) From the western border
      (`coc ANWUmpholo`, then fly west) and the north (`coc ArgoniaNWStart`, then fly north): low hilly land carries
      on past the border instead of the world ending (it has no places in it). From the east coast
      (`coc ANWBalaKarag`) look out to sea: open water to the horizon, with no edge.
- [ ] **H. Trees far away.** (Your note: trees invisible at a distance, fading in from nothing.) In the Arnesian
      jungle (`coc ANWThorn`) and Murkwood (`coc ANWTzelHaar`), stand still and look out, then fly up: trees, palms,
      mangroves and swamp trees are drawn far off as flat cut-outs and no longer appear from nothing as you come
      near; cliffs are drawn far off too. Told plainly: most fallen logs, stumps and boulders still appear only
      within about 100 to 150 metres, because their full shapes are too heavy to draw far off and no lighter shape of
      them exists (we make no art); small plants, ferns, reeds, grass and small stones also appear only near you, as
      in Skyrim, though from further than before.
- [ ] **I. Roads.** (Your note: triangular patches, hard joins, harsh dark flat roads.) Walk the road out of
      `coc ANWLilmoth`, `coc ANWGideon` and `coc ANWUmpholo` (where a main road meets a path): one continuous, lighter
      earth or gravel track with a grassy or pale edge fading into the ground; no square or triangular patches cutting
      into it, no hard join where its surface changes, no grass growing in its middle, nothing standing on it.
- [ ] **J. Swathes.** (Your note: large swathes of the same ground cover.) At `coc ANWHirecan` and `coc ANWKorydon`,
      walk away from the road: the ground and its grass change every few metres to a few tens of metres, never one
      cover as far as you can see.
- [ ] **K. Ground by region.** (Your note: more texture and ground cover variety between regions.) Compare the ground
      and grass at `coc ANWLilmoth` (coast), `coc ANWTzelHaar` (dark forest floor), `coc ANWChasepoint` (red clay),
      `coc ANWNacydes` (hills) and `coc ANWRainbreakerKeep` (gravel and heather on Skeith Isle): each reads as a
      different country.
- [ ] **L. Relief by region.** (Your note: more variety of relief between regions, within the lore.) Stand on open
      ground at `coc ANWTzelHaar` (Murkwood: root hummocks underfoot), `coc ANWKorydon` (Ultherus Swamp: broken rings
      of firm ground), `coc ANWAunikeCrown` (Aunike Ridge: long scarps), `coc ANWArchon` (Nushara Bayou: thin ridges
      running north to south), `coc ANWAroxhu` (Okuwun-Rahei: round clay mounds), `coc ANWMeliton` (Blackwood: steep
      hills standing out of the bog) and `coc ArgoniaNWStart` (Valley of Storms: winding ravines). Each region's
      ground has its own shape; most of Black Marsh is still low. Name any region that still feels like its
      neighbour.
- [ ] **M. Warm air, by region.** (Your note: too cold and grey; warm, steamy, tropical, differing by region and
      latitude.) At noon (`set gamehour to 12`), wait a little for each region's own weather to settle, and compare:
      `coc ANWAroxhu` (Okuwun-Rahei green marsh: golden, humid, pale gold-green haze), `coc ANWKharaxos` (Banujha
      blackwater swamp: amber-brown and close), `coc ANWTzelHaar` (Murkwood rainforest: green and dim),
      `coc ANWFortChalkmoth` (Chixathe mesa: crisp, blue distance), `coc ANWBalaKarag` (east coast: silver sea haze),
      `coc ANWSoulrest` (south coast: milky and warm), `coc ANWGiovesse` (west coast: golden), `coc ANWLilmoth`
      (islands: bright turquoise air) and `coc ArgoniaNWStart` (the north by Morrowind: clearer and whiter than the
      south). None is blue-grey and cold. Then `set gamehour to 7` at the marsh: a warm dawn.
- [ ] **N. Low mist and ground fog.** (Your note: more of the low drifting fog, stronger, over marsh and swamp.) At
      `coc ANWWalkSwamp` and `coc ANWWalkMarsh`, `set gamehour to 6`: thicker, more solid drifts of mist below eye
      level over the water and its banks than before, lying in a warm ground fog that thins higher up, with the sky
      and its clouds still clear above. At noon in fair weather it has thinned, and under trees there are sunbeams
      through a light haze. After rain (force a region's Steam weather as described above) it is thickest. There is
      none out at sea, and none indoors. If the sky ever looks like a flat grey or cream sheet, press End, open
      Exponential Height Fog and untick "Enable Exponential Height Fog", and tell us: that one setting turns the
      ground fog off and puts the game's own fog back.
- [ ] **O. People and creatures go round things.** Near Lilmoth (`coc ANWLilmoth`), type `player.placeatme 00023ABE`
      (a wolf), let it chase you through trees and round rocks, then along the road: it goes round trunks and
      boulders instead of running into them, follows the road, and does not get stuck or wander into the water. The
      walking mesh used to ignore every tree, rock and cliff; it is now cut round them, and plants and rocks are kept
      from overhanging roads.
