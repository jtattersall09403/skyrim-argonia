# The owner's second walk of the new world: feedback and its delivery

The owner's feedback of 2026-11-13, in his words, numbered by line (L2 to L30). Pictures named `tmp/...` are in the
main tree's `tmp/` (`/home/ubuntu/skyrim-argonia/tmp/`). Rule of the round: the world is rebuilt once after every
lane has landed; the LOD (trees and textures only) is rebuilt once, last, after every read-back and check.

## The feedback

L2. Is the new relief being read into/displayed correctly in the atlas? I can't tell.
L3. Opening the new world card and then doing a new game did not drop me at the start point of the new world, it dropped me at the previous start point in the hold of the barge by Lilmoth. The shout to travel worked though to take me to the new world start point.
L4. With the shout though, some menus were too wide to fit on screen (e.g. walk check spots)
L5. Grass: looks green and normal now.
L6. Flaoting things: those horizontal trees/stumps still read as hovering because they now just have their lowest point seated on/touching the ground/rocks, but the lowest point is like a tiny little root thing, not their proper bulk.
L7. Didn't find any missing textures.
L8. New music is in and is great!
L9. There was no music when I teleported to "D5, the highest danger: Murkwood cypress swamp" though. Also there's loads of this incredibly tall grass around that spot that you just can't see at all in which is very annoying, place that at a smaller scale.
L10. Aroudn the D1 place, I couldn't find any creatures - but there were some birds floating around, which then flew into and clipped through the land! Oh i did eventually find a cute crab though which felt appropriate. I love the look of this region btw. Water appearance though - the water looks clear, see tmp/image copy 15.png, but when I jump in it the splash is a swampy dark black-ish colour, see tmp/image copy 16.png. I tihnk I get that black splash in all water, I tested it in coastal sea as well for example.
L11. There were also still some trees seated too high (their roots touching the ground but the base of their trunks like hovering up above it). I don't know how to give you exact coordinates for an example.
L12. Some other non tree pieces still seated wrongly too - e.g. this one in that same D1 region, for a kind of sandy rocky piece, sited and rotated wrongly so you can see into its hollow side tmp/image copy 17.png. This happens a lot elsewhere with cliff pieces as well for example. Can we do some general audit of all pieces to find issues like this and fix them all?
L13. Hackwing in D1 hit a *little* too hard, took off about 80% oor 90% of my level 1 character's health in one hit. The crabs were OK though.
L14. In that D1 region, music didn't change when I got into combat. Pretty sure music should always change to a combat-y one when in combat?
L15. These bamboo frondy trees have a very strange flourescent turquoise colour tmp/image copy 18.png. It doesn't look at all realistic. Can you either recolour that tree type to something that looks natural (do an off-game loop with visual checking) or if that does't work after a few rounds then just drop them? Do this without having to rescatter all the other trees.
L16. Distant land textures still look weird - they have these strange hard edged light squares on them for example. Look at the distance in tmp/image copy 14.png. 
L17. Animations for creatures - how can we check and correct these? e.g. by the start spot there was a cool looking giant maned flying serpent thing. But it was un-animated. It moved around in the air but just as one solid static mesh that rotated and slid around, not as an animated animal.
L18. Has FreeClimb climbing been turned off? I don't seem to be able to climb any rocks or trees or anything I tried it on in the new world.
L19. Third person camera, I seem to be able to put the camera underground (like if I move the mouse all the way up to look up, with the zoom out a bit)! Presumably this isn't how it works in base skyrim?? And even if I bring the zoom in a bit so it doesn't go underground, it often still gets occluded by whatever's on the ground, like flowers and plants etc. This makes it very annoying trying to look up.
L20. Fresh black water creatures: Banujha Basin - water looks correctly black, at least one creature (giant stripy wormy thing) did swim and came on land and attacked me. Had another one of those un-animatied feathered giant flying serpent things I described above. Around this teleport spot I aslo noticed some weird tree LOD - trees that looked like one type at a bit of distance transforming into a *completely* different-shaped tree when you got closer. This may be an issue elsewhere as well. Audit and fix.
L21. Paths are hard to follow: they often get covered up by grass or ground cover for patches/stretches.
L22. Spawning bandit in the Aphon coast region didn't walk on land correctly, kept clipping in and out of it.
L23. Swam around in the Aphone coast waters for a while from the teleport spot, couldn't find any swimming creatures.
L24. Regional differences are excellent now. Really feel distinctive.
L25. I couldn't loot the bandits' bodies after killing them, fix that. I also couldn't with some creatures but that may have been intentional (e.g. the orange crabs)
L26. "Night insects at dusk: Nushara Bayou reeds" - couldn't see any insects (torch bugs or flies) at any hour around that spot. I did find one very lonely torchbug in Ultherus swamp though!
L27. Can't figure out how to get to walk check spots 2 of 2 in the argonia travel power menu
L28. Couldn't find lots of the creatures you said I was supposed to be able to find (e.g. the giant leeches, the otters, but lots of the others too). I did find some creature types, but lots I couldn't find. Do we have enough spawn density, or a bug somewhere that's stopping them being placed/spawning? in general for the world to feel alive I do think we need a lot of creatures (like a baseline high level of little critters and benign/prey creatures in all regions, like skyrim has, then with an increasing number and toughness of hostile creatures across the danger bands)
L29. I don't think as a player you have any way of knowing which region you're in? How does skyrim do it?
L30. Still some hard edges between ground textures, e.g. right at the Aunike Ridge travel spot (the "scrub" one), see tmp/image copy 19.png. I'd guess this may be related to the harsh square distant textures/LOD thing from above as well/

## Lanes

| Lane | Lines | Owns |
|---|---|---|
| seat | L6, L11, L12 | `tools/newworld/place/` seating and its checks; the audit of every placed kind |
| flora | L15, L20 | `newworld/sources/flora/`, the LOD plan (`world/lodplan.py`, `lod_models.json`), grass records |
| ground | L16, L21, L30, L9 (tall grass) | `tools/newworld/world/texture.py`, `roadpaint.py`, the terrain LOD's textures |
| eco | L10 (creatures, birds), L13, L17, L22, L23, L25, L26, L28 | `newworld/sources/ecology/`, `tools/newworld/ecology/`, `dressing/` |
| air | L9 (music), L14, L10 (splash), L29 | `newworld/sources/music/`, `NewWorldMusic.cs`, `world/water_types.py`, region names for the player |
| stack | L2, L3, L4, L18, L19, L27 | the start, `travel_menu.py`, the mod stack's settings, the Atlas |

## Delivery

One row per line, filled as each lane lands: the cause found, the change, the proof.

| Line | Cause | Change | Proof |
|---|---|---|---|
| L2 | The Atlas's heightmap is the terrain build's own (sha equal; 600 cells, median gap 0.1 units); the page never named its build | `map_page.py` refuses a heightmap not the build's own, names the build, and shows height in metres under the pointer | `relief_data()`: build 20261111T100156Z, -80 m to 73 m |
| L3 | The start marker was a temporary ref, so MQ101's lookup found nothing at a new game and fell back to the barge hold | `NewWorld.cs` writes it persistent in the persistent cell; esm check and read-back row "start marker persistent"; `start_check.py` names each card's start | small esm green, marker persistent; `start_check` FAIL New World card before |
| L4 | Vanilla message box lays one row that never wraps; rows up to 328 characters | `travel_menu.py`: labels of 24 characters at most, rows of 96 or less, every list paged with More and Back | `travel_menu check`: 76 pages, widest row 96; 7 tests |
| L5 | Praise | none | none |
| L6 | Logs seated by their lowest vertex, a root tip; the seater's rotation was the transpose of Skyrim's | `place/audit.py`: a log's bulk median at the ground, a stump's foot ring 0.25 m in, else refused; Skyrim's rotation | main 4,967 bulk hovers; small world after 0; tests |
| L7 | Praise | none | none |
| L8 | Praise | none | none |
| L9 | Music: combat outranked explore and had no track that could play (L14). Grass: KoTM cattails stand 273 to 369 units against Skyrim's tallest 90 | as L14; over-tall grasses replaced by the shorter grass of their family; `grasscheck` | read-back `music` 38520/38520 explore; `grasscheck` 7 over 90 before, 0 after |
| L10 | Creatures: D1 spot had 0 within 2 cells. Birds: a walking chicken-rig race. Splash: BM&V's splash mesh names a texture nothing ships | creatures as L28; birds become Skyrim's flying critters; the `argonia-skse` row lays Skyrim's own `watersplash.nif` from the player's Meshes0.bsa above bmv (bmv's stage key unchanged, so its copy is not re-laid) and `assets_audit engine_overrides` gates the class on the load order's winner | D1 now crab 42 m, rat 59 m; `engine_overrides` 1 before, 0 after |
| L11 | Trees seated by a source pivot sink; downhill trunk side in the air | trunk foot ring's highest point 0.1 m under the ground; a trunk over a bank is refused | main 76,250 trunk hovers; small world 0 |
| L12 | Rocks judged by a shrunk box and turned only when an open side was measured | each open rim found and buried 0.05 m, at the best of 16 yaws, else refused; audit is the place check | main 9,282 hollow shows; small world 0 |
| L13 | The band ability added damage on top of the mod's own blow (hackwing 60) | `toughness.py measure` reads each record's blow; the ability brings it to the band's target (D0, D1 7.5) | peak blow D1 8; test |
| L14 | Track conditions run on a subject a music track lacks; Skyrim's run on PlayerRef, so no combat track played | `NewWorldMusic.cs`: world condition on PlayerRef | MUSCombat 0 ours before, 7 after on the small world |
| L15 | KoTM bamboo's leaf texture is itself teal (hue 136) | `recolour.py` recolours it at staging into `argonia-recolours`; no tree moved | three reader rounds; shaded hue 79, inside neighbours' 70 to 103 |
| L16 | Far terrain textures are baked from the overbright paint (L30) | the paint's change; the terrain LOD rebuilds from it | the paint's proof; the far land at this walk |
| L17 | The serpent's skeleton is not driven by its behaviour's clips (3% bone match); 3 more broken | `anim_audit.py` in the ecology check; serpents rebound, wisp to Skyrim's, wyvern and centipede dropped | 4 failing before, 0 of 286 after |
| L18 | Not found offline: FreeClimb loaded and ready; refusals not logged | Diagnostics=1 in the freeclimb row | the next walk's FreeClimb.log |
| L19 | SmoothCam's default turns off pitch zoom | SmoothCam.json laid with `enablePitchZoom: true` | the owner's walk check |
| L20 | Five stale billboards (moss bases dropped after the LOD; two renamed bases) | `lodplan.far_form` in the LOD check; fresh tree LOD | main 5 stale, 0 unlike |
| L21 | Grass-bearing weight on the road surface up to 1.99 under the engine's additive read | the paint's change; texcheck `road_surface_grass_max` <= 0.1 | 1.992 FAIL before, 0.035 PASS after |
| L22 | From the walk's own save (Autosave2 of 12:50, walk-2 ESM F675AD74): the met bandits are our ecology copies placed in Aphon Isle (ANW_Region_aphon_isle cells -67,-184 and -67,-188), none made by a script (the save's only 2 created actors stand in interiors). A living Khajiit bandit stood 22 units under flat land (land 408, navmesh 416, actor 386); another 5 to 7 under; an archer swam 138 units over the seabed in the sea. So the actor sank under its land collision, not following the navmesh. Precision only filters controller-against-controller collision (Hooks.cpp:1915-1935), so it is not the cause | `tools/newworld/ecology/bodies_repro.py` writes two console batches that kill and read the same refs | the repro's log |
| L23 | Water creatures at a third of Skyrim's rate; none promised near the spot | water at Skyrim's walked rate; the spot's promises placed within 200 m | dreugh 78 m, sea otter 151 m |
| L24 | Praise | none | none |
| L25 | From the walk save: one bandit died (Boss1HRedguardM, Aphon Isle), saved 5 units under flat land, with no havok-move change (the ragdoll never settled on the ground), and was never looted; the creatures that died elsewhere (mud crabs, boars, kotu gava, hackwing) saved 5 to 28 units over the land and were looted. No crab died in the save. Precision's kill impulse is capped and halves the downward part (PrecisionHandler.cpp:428-436), so it cannot drive a body through land. Leading cause: the body lies in the land, so the look ray meets the ground first | world writer clears Summonable, Unique, Essential, Protected and a kitted copy's template; `loot_check.py`; `bodies_repro.py` | 10 faults before, 0 after; the repro's log |
| L26 | Torchbugs' spawner runs 20:00 to 23:00 only | the spot promises torchbugs and gnats within 200 m; the walk check names the hours | torchbug 63 m, gnats 43 m |
| L27 | As L4: More and Back fell off the screen | as L4 | as L4 |
| L28 | Density over all LAND (half empty) cut to a third; spots' own cells empty; two spots in unbanded cells | Skyrim's rate per navmeshed cell times the band; promised kinds placed within 200 m; two spots moved | 7,663 actors against 5,979; 0.89 to 0.97 of Skyrim per class |
| L29 | No location records: nothing named a region | one LCTN per region, parent "Black Marsh", on every exterior cell | `location` 0/38520 before, 256/256 small world |
| L30 | Opacities written as stacking, the engine adds them: 20.7% of vertices overbright; writer and both checks read stacking | `texture.py` writes weights as opacities; texcheck reads additively with `over_share`, `over_p99` | texcheck FAIL before, PASS on the small world |

## After the rebuild

Commands from the lanes still owed, in order, after the full rebuild:

1. `python3 -m tools.newworld.start_check`: PASS for both cards.
2. `infra/gpu-box/lod.sh map` and `lod.sh send`, then `infra/gpu-box/deploy.sh`; `infra/gpu-box/places_deploy.sh` if the places belong on the card.
3. `python3 infra/gpu-box/stack.py stage` (lays `argonia-recolours`, SmoothCam.json, FreeClimb Diagnostics=1, Skyrim's own splash over BM&V's): staged green 2026-11-13; `stack.py push`, then `infra/gpu-box/run.sh ps 'C:\argonia\infra\stack.ps1 on -World NewWorld'` and `... on -World Argonia`; bring `~/.argonia/stack/installed-NewWorld.json` level.
4. `tooling/job_guard.sh run --gpu nw-lod-selftest -- infra/gpu-box/lod.sh selftest`, then `tooling/job_guard.sh wait nw-lod-selftest`.
5. `NW_LOD=1 LOD_FORCE="texgen dyndolod" tooling/job_guard.sh run --gpu nw-lod -- infra/gpu-box/lod.sh stage`, then `tooling/job_guard.sh wait nw-lod`; `out/newworld/lod/check.txt` shows 0 stale billboards.
6. Atlas: `python3 -m tools.newworld.map_page`, publish `out/newworld/map/index.html` to https://claude.ai/artifact/SwMRMPndRrXfEKtTuodNsb.
7. `python -m tools.newworld.place.audit refs out/newworld/plugin/refs/flora`: 0 in every class.
8. After the owner's climb: read `C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data\SKSE\FreeClimb.log` on the play machine.
