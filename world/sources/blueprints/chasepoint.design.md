# Chasepoint (`place.mercantile-coast.chasepoint`): design

Chasepoint is a Type 1 road station (`road-station-village`, M2). Its culture is argonian with secondaryCultures [imperial]. The source is 0117 change set d6178109, lead ruling a. This design is Part A of three (layout and kits). Claywater Station is an Imperial station with an Argonian landing beside it. Chasepoint is an Argonian salvage hamlet. The hamlet inherited a single Imperial stage and its yard.

## Site

- Record: `world/sources/catalogue/places-mercantile-coast.json:3109`;
  positionM [686.1, 6105.9]; services [trader]; sockets
  `evidence.chasepoint.foreign-timber-tally`, `post.chasepoint.way-station`;
  notable slot `station-keeper`; contents: a wreck-household family band, a
  merchant and a tier-2 loot cache (salvage held back from the count).
- Promise ledger: `world/sources/placement/promises/place.mercantile-coast.chasepoint.json`
  (32 rows, written by the lead-ruling run; derivedFrom sha of the catalogue
  after d6178109).
- Ground (`tooling/.reports/16k/place.mercantile-coast.chasepoint/map.txt`):
  a low plateau at 7 m between two tracks. The coast track
  (`track.track.mercantile-coast.coast-road`) runs north-south at x 675-686
  on the east lip of the plateau. The province road (Bog causeway / Lake road) lies 29 m further
  east at x 715-730 and 2 m lower. The swamp `body.398-3352` (level 5.01 m) lies
  46 m off. The sea is out of sight to the south ("two fields away").
- Neighbours: Soulrest 355 m (the city that the station serves), Hist-less fringe 102 m,
  Topal salt pans 201 m, Quinrawl anchorage 395 m. Nothing is built yet within
  2 km. Claywater (same type, other region) is the only sibling.
- Lore: `world/sources/lore/soulrest.md:20` (Imperial administrative
  layers, most mixed city), :31 (Chasepoint the neighbour east); UESP
  Lore:Soulrest.
- On the road: the stage fronts the coast track. The way out joins the
  province road at the bend.
- Record defect filed: promise row `thing-plank-crossing` is derived from
  assetPlan[0] `kotm-plank-house`, which is a house family and not a crossing (the
  generator's slug-to-noun map reads "plank" as a crossing). The plank homes fill the row here.
  A REQUEST row stands in the part A report.

## Intent

Two or three Argonian wreck-salvage households live here. They hold hereditary rights to the wreckage that comes ashore on the coast to the south, out of sight of the stage. They keep an Imperial road stage that they never built. The stage's walls stand and its yard locks. The households count, stack and own everything. Foreign timber cut square in other provinces lies in tarred stacks inside a stone yard wall. Rope dries in the old stable. Only the Imperial building on the bend has a straight ridge. Its thatch and the plank homes around it show that Argonians hold it now. The setting is humid coast lowland (mercantile-coast, fringe marsh). The palette is grey plaster, weathered driftwood and tar-dark timber. Green scrub presses on the wall.

## Walk-through

1. Approach from the province road at the bend. The stage's straight ridge
   and the square yard wall show over the scrub. A lettered post at the fork
   names Soulrest and the coast.
2. The track: the stage's door faces it, with a lantern by the door. A salvage
   stall under an awning stands beside the door (the trader).
3. The yard gate: inside the wall stand timber stacks and the drying shed (the
   old stable) with rope and nets. The families' locked chest stands beside it. The tally board (evidence socket) stands here too.
4. The homes: two plank houses stand south of the yard on the dry plateau. Each
   door is lit and each house has a small yard of baskets and pots. The households watch the
   track from their steps.
5. The way out: the track runs on toward the coast road and the unseen sea.

## Quest beats

Five local quests name Chasepoint in `anchorPlaces`. The quest rows are in `docs/quests/index/local-mercantile-coast.md`:46, 64, 65, 70, 109. All five quests are local tier (medium). Each beat is built from what stands here, or rewritten. Local quest rows carry no `sockets[]`. Only the main and faction files carry `sockets[]`. The fillers are the layout uids below.

| Quest | Beat at Chasepoint | What must physically exist | Decision | Filled by |
|---|---|---|---|---|
| LM38 Whatever the Sea Lost | wreck goods on sale before the owners know | a salvage stall with goods out, the trader | build | the stall under its awning by the stage door; the trader service |
| LM56 The Sunken Causeway Survey | the last stage the survey reached | the road stage the survey used, its door on the track | build | the stage (`stage`), door onto the coast track |
| LM57 The Stage That Was Not Paid | two families claim the stage-keeper's post | the Legion stage and two separate households | build | `stage`, `home-a`, `home-b` |
| LM62 What the Salvage Coast Owes | rescued crew kept working the salvage | a yard where salvage is stacked and worked, a shelter for the crew | build | the walled yard, its timber stacks and the drying shed (`shed`) |
| LQ29 A Wreck with Living Cargo | relics held back from the count | a hidden salvage cache | build | the tier-2 loot cache and the tally board (evidence socket) |
