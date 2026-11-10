# Hand-over: the owner's walk 5 feedback on the built new world

For a fresh orchestrator session. Written 2026-11-10 by the nw-03 session, at the owner's request, so the work on
the built world is planned with what nw-03 changed and depends on. The owner's feedback is quoted whole below;
the file it came from is `tmp/walk-5-feedback-2026-11-10.md` (section "New world, built"; the pictures it names
are beside it in `tmp/`). The quest half of that file is another session's.

## What nw-03 delivered that this work stands on

- **Helstrom is built as a place layer** over the world file (`out/places/plugin/ArgoniaNWPlaces.esp`, from
  `newworld/places/helstrom`): drafted from BM&V's Helstrom, people named, stocked, lit, with travel, every build
  check passing. It is not deployed to the play machine: the owner ruled that the first deploy follows their
  walk of nw-02 and their first real finalise.
- **A place is changed narrowly** (CLAUDE.md, "How we build"): by the drafter stage that owns the change, on the
  standing files, never by a whole redraft, never over the owner's studio edits. `python -m tools.places draft
  <stage> <place>`; the skill is `place-build`.
- **The place studio** (https://studio.jacktat-play.stream) shows the built ground, grass, paths, lights by day
  and night, people's routes on the built navmesh, and the Atlas. It reads the ground bundle
  `out/places/bundles/ground.helstrom`, whose stamp must match the deployed world file.
- **World data now in the database** (`tools.argonia_world.db.open("newworld")`, sources under
  `newworld/sources`): the travel network (`docs/design/travel-network.md`), the four danger facts per place and
  the ground band per cell (`docs/design/danger.md`), people, the stocking scale and place wealth, stock.
- **The Atlas** is republished at https://claude.ai/artifact/SwMRMPndRrXfEKtTuodNsb (built by
  `python3 -m tools.newworld.map_page`; republish to that link after a rebuild). Its water edits are the record
  in `newworld/sources/water_overrides.json`; the pull keeps what the file holds.

## Dependencies: what a change to the world does to nw-03

| A change to | Means for the built places |
|---|---|
| Relief (heights) near a place | The place's ground bundle is re-extracted and the place re-seated by the `seating` stage; where the fit no longer holds (water and land under clusters, slopes under buildings) the `fit` or `pieces` stage for those clusters, then `streets`, the build and the check. Settle relief before the owner hand-edits a place; keep relief changes away from built places where the lore allows, or list each built place they touch. |
| Water level, water bodies, shore | Same as relief, plus the landing: Helstrom's pier, ship and bank join are fitted to today's bank and water (deck heights, one flight of steps). |
| Land textures and road painting | The studio paints a place's paths the way `tools/places/build.py` paints them (same texture choice, 96-unit feather). The owner made the same complaint in both places ("harsh", flat roads): fix the painting once, in the build's rule and the world's road painting together, and the studio follows. |
| Grass and ground cover sets | The studio draws grass from the land textures' grass records; a change shows there after the ground bundle is re-extracted. |
| World navmesh | Places' navmesh is generated against the world's and joined at the seams; a world navmesh rebuild is followed by the place build and check (`navmesh`, `streets`, `doors`). |
| Trees, plants, rocks (world refs) | A place's clearance (`clear.jsonl`) names world refs; a re-scatter is followed by the `clearance` stage. |
| Regions, biomes, danger | Cell danger and the places' reward bands are derived (`tools/newworld/danger.py`, `place_danger.py`); wealth and loot tiers follow. Re-derive, do not hand-edit. |

The build machine is shared: world builds and place builds write under `out/`; run one heavy job at a time under
`tooling/job_guard.sh`, and never rebuild the world while a place build or the studio's finalise is running.

## The feedback, in the owner's words

- In free camera fly mode only: Edges between water and land are bad. Texture fighting of some kind: flickers
  between water and land displayed. And water's edge appears as hard straight lines. Example at tmp/image copy
  8.png. How does skyrim do this? But also I can just 'fly' around with the character using tcl and setting the
  speed multiplier.
- Also bad hard edges in the map view, see tmp/image copy 9.png for example. The water that does appear looks
  bad and flickers/changes as you pan around, and also not all water is on there either, and I'm not sure it's
  the right colours/textures either for our different water types. There are various weird light coloured
  square land textures too.
- That flicker issue happens on land as well actually. Sort of weird thing
- Map feels/looks truncated at its edges, particularly west, south and east. e.g. I can't pan over to view the
  island in the eastern sea (topal bay) or all the way south or west to see those oceans properly either
- Think we need LOD for the land beyond our borders? W, N and NW
- Textures look good from character view in terms of no hard edges, generally, but there are some issues on and
  around roads sometimes, e.g. triangular patches cutting into the road with hard edges, very hard edges between
  different types of road textures. The roads themselves also look like very 'harsh', like often these very
  harsh dark black flat textures, not sure it looks great.
- There are some large swathes of all the same ground cover/grass - probably too large.
- Teleport coordinates you gave me are wrong. e.g. cow ArgoniaBlackMarsh -8 -148 was supposed to be Helstrom but
  it dropped me in the sea miles north outside the map
- LOD - think something not right about it. Many (but not all) trees area completely invisible from distance,
  including large ones, and then fade into visibility out of nothing when you get close! Same for ground cover,
  rocks, scatter, grass. Makes the place look quite weird beyond a short radius around the player and feel very
  odd to move around.
- Let's have more of the volumetric fog! I like the low-lying below eye level atmospheric cloudsdrifts we get
  sometimes (done the skyrim native Hjaalmarch way); let's have more of them and make them stronger. They add
  great atmosphere, especially to the green marsh and blackwater swamp water areas and surrounds.
- the light and atmosphere feels too "cold" and grey. I want our province to feel like a warm atmospheric steamy
  tropical region, like somewhere in Borneo or southern India mostly. The specific combinations of lighting and
  haze should vary within our province by region - e.g. I'd expect it to be different in blackwater swamp areas
  vs green marshy areas vs river corridors Vs highlands Vs islands Vs each coast. And vary somewhere by
  latitude, e.g. the northern area by the Morrowind border we would expect to have a different climate and
  atmosphere to the interior and both different again to the south coast. Research what an appropriate
  atmosphere should be for each of our regions (based around the borneo and southern India examples), then
  research how games generally achieve those effects, then investigate and reason about how to implement our
  desired feel in a Skyrim native way (and using volumetrics from community shaders where appropriate), then
  implement it.
- G. Water types, and H. Flow goes the right way: don't think this has worked. All water I could find
  everywhere I checked all looked the same: slowly flowing, all in basically the same direction, all the same
  colour. (but different plant types so something is working in terms of classifying it).
- I randomly had a crash while testing, there is a crash report on the play machine
- O. Relief (your call) - I think we could have a little more variety. I don't want to depart too far from the
  lore and the region research, I want to remain consistent with it but I am finding that a lot of the province
  feels kind of same-y. Sorting out the water types and climate types above will help, but I think we would also
  benefit from some more variety between regions in terms of relief, such that each region feels more different
  from the others than it does currently. Can we do more with texture and grass/groundcover sets variety between
  regions as well (on top of the tree-set-variety we currently have)? in addition to the BM&V textures you can
  use Tropical Skyrim textures too.

## A suggested order, with the reasons

1. **What changes the ground first**: relief variety (O), water kinds and flow (G, H), the water's edge (the
   flicker and the straight lines, in the world and on the map). These decide the land and water every place is
   seated on, so they come before any more places are built and before the owner hand-edits Helstrom. Helstrom is
   then brought level by the narrow stages in the table above, and its checks run.
2. **What dresses the ground**: road painting (with the studio's same rule), texture and grass variety by region,
   the large swathes of one ground cover. Independent of relief once the heights are settled; the place layer
   follows by re-extracting the ground bundle.
3. **What is seen from afar**: level of detail (trees, rocks and scatter appearing from nothing: the play
   machine's DynDOLOD preset builds ours alone, `infra/gpu-box/lod.ps1`), land beyond the borders, the map's
   edges and its water. After 1 and 2, since each is generated from the finished world.
4. **Atmosphere, in parallel with all of it**: the warm, steamy, regional weather and light, and more low fog.
   It touches weather, climate, image space and region records, not the ground. Note for the studio: its night
   view reads the worldspace's climate and weather from the ground bundle, so a new climate shows there after a
   re-extract.
5. **Small and separate**: the wrong teleport coordinates (Helstrom's place record gives its cell and world
   position; the place layer's cells are in `out/places/shards/helstrom/plan.json`), and the crash report on the
   play machine.

## Rules the owner set in the nw-03 session that bind this work too

`docs/owner-rulings.md`, entries of 2026-11-09 and 2026-11-10: no "worth a look" lists (fix it); no timing or
frame-rate measurement on the build machine; nothing proven is proved again; the owner judges look; a place is
changed narrowly; delivery lanes on Opus 5.5 at medium effort and code review on Fable 5.2 at medium, the lead
planning and orchestrating; the build machine is never left idle and the play machine stops itself.
