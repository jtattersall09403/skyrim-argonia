# New world walk check (nw-02)

The owner's walk of the new Black Marsh world, posted once the off-game read-back passes in full
(`tooling/job_guard.sh run nw-verify -- python3 -m tools.newworld.verify`; the table is `out/newworld/verify/report.md`).
It sits apart from `docs/owner-walk-checks.md`, which is the walk list for the BM&V game; ticks go here, in the same way.
Posted 2026-11-09 as issue #56 after the read-back passed 50/50.

---

**What this is.** Black Marsh is now a whole world of our own, made from the Project Tamriel map: its own land,
ground textures, trees and plants per region, rocks and cliffs, roads, water of the right kinds, ground mist,
far-distance scenery (LOD), the world map and a navmesh (the walkable layer people and creatures use to find their
way). It is a separate plugin with its own Moonlight card, so your Black Marsh & Valenwood game is untouched. You are
only looking: nothing here is a quest.

**Cost.** The play machine costs about $0.80 an hour while it runs; this walk is about an hour. It stops itself when
idle.

**Getting there.** Open the **"Argonia: New World"** card in Moonlight. Start a new game (or load any save), open the
console with the key under Esc and type `coc ArgoniaNWStart`. You arrive on dry ground in the Valley of Storms, just
south of Stormhold. To jump to any other place, type `cow ArgoniaBlackMarsh X Y` with the cell numbers given below.

**Commands for looking around** (type in the console, then close it):

- `tgm`: you cannot be hurt. `tcl`: walk through anything and fly where you look (type again to stop).
- `tfc`: a free camera that flies away from your body (`tfc 1` also freezes time, good for looking at one moment);
  `sucsm 500` sets how fast it flies (try 200 to 1000). Type `tfc` again to come back.
- `player.setav speedmult 400`: run four times as fast (`player.setav speedmult 100` puts it back).
- `tm`: hide the HUD and menus for a clean look (type again to bring them back; the console still opens).
- `fov 90`: a wider view (`fov 70` is the default).
- `set gamehour to 6` (dawn), `set gamehour to 12` (noon), `set gamehour to 22` (night): the time of day.
- `fw 0C821E` forces fog, `fw 00081A` clear sky, `fw 0C821F` overcast rain, `fw 0C8220` storm rain (`fw` is a
  forced change; wait a few seconds for it to settle).
- `tg` hides and shows grass, `tt` hides and shows trees: use them only to see the ground underneath.
- M: the map menu.

## The checks

Reply on the issue with the letter of any check that did not look right, what you saw and where (the cell numbers
show in the console with `getpos x` and `getpos y`, or just name the place). A screenshot helps.

- [ ] **A. Arriving.** After `coc ArgoniaNWStart` you stand on dry land, not in water or under the ground, and the
      game did not stall.
- [ ] **B. Ground textures blend.** Walk or fly over a few hundred metres anywhere: grass, mud, sand and rock fade
      into one another. You should not see straight lines, squares or hard edges between two ground textures, and no
      large patch of one texture repeating for a long way.
- [ ] **C. Grass on the ground.** Most land has grass or low plants growing out of it (not bare painted ground),
      except on rock, roads, beaches and mud flats.
- [ ] **D. Each region looks like itself.** Visit three: Murkwood round Helstrom (`cow ArgoniaBlackMarsh -8 -148`),
      the Kotherra mangroves round Gideon (`cow ArgoniaBlackMarsh -52 -167`) and the Arnesian jungle round Thorn
      (`cow ArgoniaBlackMarsh 60 -125`). Each has its own mix of trees and plants, and inside each there is a good
      variety, not the same tree over and over.
- [ ] **E. Trees and rocks sit properly.** Look closely at the foot of trees, bushes and rocks on slopes: trunks go
      into the ground (no floating roots, no trunk buried halfway); rocks have no open, hollow back facing you; cliff
      pieces face out of the hill with their open side hidden against it. Nothing is bright purple (a missing
      texture); look in particular at a fern and a mangrove in the Kotherra mangroves (D), whose textures we repoint.
- [ ] **F. Roads are clear.** Follow a road for a while (the road south from Stormhold is a good one): nothing grows or
      stands on the road itself, and its edges are dressed with the odd stone or marker as in Skyrim.
- [ ] **G. Water types.** Visit: black swamp water in the Banujha Basin (`cow ArgoniaBlackMarsh -25 -195`); green
      marsh water in Okuwun-Rahei (`cow ArgoniaBlackMarsh 55 -168`); a river in the Tulmek Washes
      (`cow ArgoniaBlackMarsh 15 -207`); a stream in the Kotherra mangroves (`cow ArgoniaBlackMarsh -55 -163`); a pond
      in Blackwood (`cow ArgoniaBlackMarsh -73 -130`); an estuary on the Sea of Mists (`cow ArgoniaBlackMarsh -50 -239`);
      the open sea (`cow ArgoniaBlackMarsh 77 -150`). Each looks like its kind (dark, green, clear, sea), the river and
      stream visibly flow, and ponds, marsh and swamp lie still.
- [ ] **H. Flow goes the right way.** On the river and the stream in G, the water runs downstream toward the sea or
      the larger water it joins, not uphill or back on itself. (Where a river bends, the direction changes from one
      cell to the next: that step is a limit of the game's water, not a fault.)
- [ ] **I. Water's edges.** At the sea, a river and the swamp in G: the ground goes from bed, to wet edge, to bank, to
      land, with plants and stones that suit each kind of water (beach at the sea, mud and reeds at the swamp).
      Trees do not stand in the river or stream; they stand in water only in swamp, mangrove and drowned forest.
- [ ] **J. Mist.** In the Banujha swamp (G), `set gamehour to 6`: low drifting mist below eye level over the water
      and wet ground. `set gamehour to 12` with `fw 00081A`: thin or gone. `set gamehour to 22`: back again. There is
      no mist out at sea.
- [ ] **K. Weather.** `fw 0C821E`, then `fw 0C821F`: fog and rain both look like Black Marsh's own, not snow or a
      Skyrim sky.
- [ ] **L. The distance.** Fly up high with `tfc` and `sucsm 1000` and look out: distant land, trees and water are
      drawn (LOD), with no holes, no floating squares and no sudden pop where near meets far.
- [ ] **M. The map.** Press M anywhere in the new world: the map shows Black Marsh's land, you can pan and zoom to the
      edges, and the settlement markers are there (only Stormhold is known at the start; `tmm 1` reveals them all).
- [ ] **N. People can get around.** Optional: near Lilmoth (`cow ArgoniaBlackMarsh 33 -224`), type
      `player.placeatme 00023ABE` (a wolf), let it chase you and run round trees and along the road: it follows,
      not stuck or walking into the water at random.
- [ ] **O. Relief (your call).** The terrain follows the region research: most of Black Marsh is low and nearly
      flat, like BM&V's own marsh (10 to 25 m of height in most regions), with more relief only in the uplands and
      mesas (Chixathe mesa at Fort Chalkmoth, `cow ArgoniaBlackMarsh 37 -142`; the Aunike ridge at Aunike Crown,
      `cow ArgoniaBlackMarsh -8 -179`). If you want more hills or higher
      mesas anywhere, say where; it is a change to the region table, then one rebuild.
