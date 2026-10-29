# The Sealed Vault (place.imperial-penal-south.voriplasm-vault): design

Type 5, dungeon entrance, class lair, entrance `stair-throat`. The owner
chose a full rebuild in 16x (the one exception to decision 0128): every walk-12
op was deleted and the place was designed again from this record.

## Site

- Record: world/sources/catalogue/places-imperial-penal-south.json. Position
  [1697.1, 6681.7], footprint 30 m, D4, discovery `document`, hostile, no
  occupants. Why: a vault lies under a ruined works. Something grew in
  the vault. The people who found it sealed the door two hundred years ago.
  They nailed a note to it.
  Vibe: "rust red, grey stone, faded board"; signature "the vault's old
  wooden door in rusted iron bands, with a nailed board"; mood "sealed and
  posted".
- Lore: world/sources/lore/blackrose.md (the Imperial prison province, works
  built over older stone); world/sources/lore/topics/fauna-hazards.md: the
  voriplasm is a moving pool of green slime that strips a body to the bone
  and leaves only small bones. Quest LR52: "something in a sealed western
  vault eats whatever is put in front of it, then goes quiet".
- Ground (measured 2026-10-14, `wb.py map --heights`, survey probes): a lake
  flat. The lake stands at 0.00 m west of x 1675 and on the shore south-west;
  a marsh pool at 1.16-1.24 m lies 50 m north at (1715-1721, 6632). The dry
  ground rises from 0.7 m at the shore (x 1680) to 3.4 m at x 1752. The coast
  road crosses the window at z 6673. The frozen ground is too low to cut a
  4 m hollow above the lake, so the hollow is dug into a raised spoil berm
  (the owner's rule: raise a berm, never cut deeper when the lake is at grade).
- Ways: the place track meets the coast road at terminal.voriplasm-vault.coast-road
  (1684.6, 6675.6). The track leaves the junction west-south-west along the
  road's line, turns south at (1672.5, 6680) and comes east through the gate
  at (1684, 6701). Nine ways lie within 500 m (site packet). The record's
  boundary is x 1668-1750, z 6668-6728.
- Reference cells, one per composition (docs/world/90 §79.1, `cell_clusters`,
  `plugin-neighbours`):
  - The works curtain: the proving-ground yard run (mwkeep, Tesak's Imperial
    keep): destroyed01, gate, tower, destroyed02 on the mined pairs.
  - The ruin court: King of the Murkmire's small Imperial ruin at
    ArgoniaWorld (-18..-17, -36..-35), 33 refs, 39 x 42 m. Its wall lines,
    columns, fallen pieces, loose blocks and keep rubble are copied at the
    poses the plugin gives them round ruins_14 (plugin-neighbours, radius
    30 m). The foundation plinth and the snow stairs are left out: the court
    stands on the lake flat's own ground.
  - The vault face: Skyrim's Fort Amol (24..25, -7..-6) and Cracked Tusk Keep
    (-14..-13, -22..-21): an impextdoorhole01 set at the foot of an Imperial
    fort face, impextstairs02 flights, rubble at the wall ends.

## Intent

1. Purpose, in a local's words: "the old works by the lake; there is a hole
   in the mound at the far end, with a shut door at the bottom."
2. Mood words and their levers. **Threatening**: one dark doorway at the foot
   of a stone face, bones on the hollow floor, only a faint fungus glow. **Worn**: broken
   walls, fallen columns and rubble, growth over the face. **Hidden**: the
   door is under the visitor's feet; it is seen only from the berm rim.
   The court is screened from the road by the fallen south curtain (a
   grassed rubble bank) and the curtain's broken south end, so it is first
   seen through the gate; only the column tops show over the bank.
3. Kept images. Afar: the broken keep wall and its gate on the lake flat with
   the ruin's columns beyond it. Threshold: from the stair foot, the hollow walled by
   spoil heaps and the dark door ahead, bones underfoot. Heart: at the door,
   the nailed note, the green fungus glow and the dropped tool.
4. Day: grey stone against green, the hollow in shade. Night: no lamp or fire (a lair with no
   keeper); two clumps of glow fungus in the damp at the door's foot give
   the only light. The face can be seen by moonlight. Rain: water runs off the berm into the hollow. The floor stays
   above the lake.
5. Wear: the Imperial works fell and were not rebuilt; the court has lost its
   floor and roof, the vault's front wall is the only face still whole.
6. Scale: the keep walls stand 13 m against a 1.8 m walker; the hollow is 4 m
   deep; the doorway hood is 3.65 m.
7. First-seen object: the keep gate. Reveal: the hollow and its door from the
   rim. Signs of life: the dropped tool and the bones, the note on the door.

## Walk-through

1. **Far** (coast road at the junction, 1684, 6674): the keep's broken curtain
   with its gate, the ruin court's columns over it. Threatening, worn. Keep run.
2. **Approach** (the track west of the wall, 1674, 6697, then through the
   gate into the ruin court to the stair head, 1716, 6692): the gate across
   the track, the court's broken walls and columns, the green spoil berm,
   then the hollow below. Worn, hidden.
3. **Threshold** (the stair foot, 1723.5, 6692, looking east): the hollow
   walled by spoil heaps, bones underfoot and the dark door in the stone
   face lit only by green fungus. Threatening.
4. **Heart** (the hollow floor south-west of the door, 1727.6, 6689.2,
   looking at the door): the planks nailed across the door, the fungus at
   its foot, vines on the face. A shovel stands in the floor where the last
   digger left it. Threatening. The load door.
5. **Reward** (inside the vault, Fort Amol's halls): stone halls with no
   keeper, dark between pools of light: glow fungus in clusters at the door
   and the hall ends, red Hist sap blooms here and there. The great room
   has only the green glow of the beast. Threatening, worn.
6. **Exit** (the stair head looking back west, 1716, 6692): the court and the
   keep wall against the lake. Lonely.

Cameras stand 6 to 12 m off each station at 1.7 m.

## Palette

Grey Imperial fort stone (Skyrim's dungeons/imperial/exterior: walls, doorway
hood, stairs), Tesak's keep stone for the curtain and rubble, King of the
Murkmire's Imperial ruin walls and columns (made for Black Marsh), the Nordic
vine overlays hanging on the face, raw earth on the berm and hollow floor,
lake-flat grass and ferns, bleached bones. Siblings in the region build with
imperial-keep and imperial-farmhouse; this palette shares their keep stone and
adds the ruin families no other place of the region uses.

## Brief

| Thing | Purpose (who, promise, intent line) | Kit piece | Rule or lore |
|---|---|---|---|
| keep run (k-*) | the works' curtain and its gate across the track; far and approach stages; founding "under a ruined works" | imperial-keep: mwimparchwall01destroyed01, wallgate01, walltower01, wall01destroyed02, laid on the mined pairs (5.82, 5.82 and 7.27 m steps), gate at (1684, 6701); k-0 one broken length south of k-1 toward the road | yard run; endFaceRule; openModularEnds 0 |
| fallen south curtain (m-bank, m-bank-w) | the works' road-side wall, fallen and grassed over; screens the court from the road (hidden) | mounds, flat, datum 3.70, blend 2: x 1689-1712, z 6676.6-6677.6; an arm north along the old wall line, x 1685.6-1686.6, z 6679-6684.5 | 0102 place overlay; road sightline rays into the court: junction 0.93 blocked, east road 1.0, west road 0.91-0.95 |
| ruin court (c-*) | the ruined works over the vault; threshold stage; worn | ruin-imperial-v1 KotM ruins_14/15/16/17/17b/17c; KotM's keep rubble and loose blocks | KotM ruin at (-18, -36), poses copied |
| spoil berm (m-berm) | the earth dug out to reach the vault; raises the ground so the hollow can be 4 m deep above the lake | mound, flat, datum 5.80, blend 4, x 1714-1746, z 6676-6708 | 0102 place overlay; cutDatumRule |
| hollow (m-hollow) | the dug pit, 4 m deep; one vertical face, three sloped sides | mound, cut, datum 1.80 (0.56 m over the 1.24 m pool 50 m north), blend 8, x 1725.8-1741.6, z 6685-6699 | owner (b); cutDatumRule |
| keep bed (m-keep) | a level bed under the curtain on the tilted flat | mound, flat, datum 1.00, x 1679.5-1688.5, z 6690-6726 | 97 B3 pad fit |
| face run (f-*) | the vault's front wall exposed by the dig: the one vertical face | ruin-imperial-v1 impextwall01 x2 by the mined pair, bare ends into the slopes | owner (b); endFaceRule |
| face backing (m-rear-face) | holds the berm level behind the face | mound, flat, datum 5.80, blend 2 under the wall | 0102 |
| doorway (v-door) | the vault's one door, at the foot of the face, no step up; promise interior-principal | impextdoorhole01 and its plugin load door | owner (c); 0114 |
| stair (s-*) | the way down the west slope to the door; promise entrance (stair-throat) | impextstairs02 x2 with a 1 m landing | owner (b); modular-runs C |
| stair ramp (m-stair) | a plane under the two flights | mound, ramp, blend 2 | 0102 |
| note (n-note) | the sealing party's note on the door; promise evidence-sealed-vault-warning-board | kotm stockade planks across the door leaf inside the hood, scale 0.93, bearing on both jambs; sign socket | owner (c); record pressures |
| vines (g-vine-1, g-vine-2) | growth over the face either side of the hood; worn | norvinewall01nocol, back on the face plane | type 5 "vines root against the lip" |
| spoil heaps (r-spoil-n, r-spoil-s) | the dig's spoil dumped on the hollow rims; a dark mass round the threshold; threatening | impextrubble02 | owner (b) dig; place skill threatening lever |
| glow fungus (g-1, g-2, g-3) | the lair's natural light, in the damp at the door's foot; threatening, night | glowingmushroomcluster01 within 2 m of the threshold | type 5 lair light; 0102 decision 7 |
| bones, tool | what the vault took and who came last; threatening | yard sets lair-bone-scatter (b1- by the door, b2- at the stair foot), lair-tool-scatter | type 5 bars; fauna-hazards (small bones) |
| track and trail | from the coast road through the gate, the court, up the berm and down the stair | paths | approaches; terminal |

## Interiors

| Door | Shell | Claim |
|---|---|---|
| v-door | impextdoorhole01 (ImpExtDoorhole01, Skyrim.esm) | the claim picks among the cells Skyrim links from this shell (exterior-interior-links.json): Fort Amol 01, Fort Greenwall 03, Broken Tower Redoubt 01 and 02, Cracked Tusk Keep 01, Fort Sungard 02, Fort Greymoor 01, Harmugstahl 01, Liar's Retreat 01. The cell is a lair: natural light only (glow fungus, sap, light through holes) and the 0109 plan |

## Quest beats

LR52 The Sealed Vault (quest.local.lr52), tier 3, medium.

| Quest id | Beat | Need | Decision | Evidence |
|---|---|---|---|---|
| quest.local.lr52 | Find the vault from the road | the keep wall seen from the coast road; the track to the gate | build | route.voriplasm-vault.the-gate-track; terminal.voriplasm-vault.coast-road |
| quest.local.lr52 | Read the note | the note nailed on the doorway hood | build | socket.voriplasm-vault.sealing-note |
| quest.local.lr52 | See what the vault has eaten | bones and a dropped tool on the hollow floor | build | lair-bone-scatter, lair-tool-scatter |
| quest.local.lr52 | Open the door and go down | the load door | build | door.imperial-penal-south.voriplasm-vault.1 |
| quest.local.lr52 | Feed it, face it, take the cache | swarm c2, boss c1, cache l1 | build (cell) | cell sockets |
