# Owner play test 3 (2026-11-02, Paris g6.xlarge, round-3 build, the nine region saves; comment on #37 at 21:35 UTC)

The owner's words first, verbatim, then the triage (blocker = cannot do the action or seen at the play camera; else
polish) with the owning chunk and the fix. Rulings from the same comment are in the owner brief (2026-11-02 rows).

## The findings, as written

1. One of the saves should be in claywater
2. Saves load in first person - should be Third person
3. Lots of plank boardwalk things and sort of plank stair towers placed randomly and haphazardly in a load of places
4. Tree seating - many have bases hovering in mid air (trailing roots touch ground)
5. Some weird tree colours - some like a neon blue green, some weirdly washed out and pale (definitely not intentional)
6. Menu control oddities - there are a lot. I can't remember them all. You need a good fast way of being able to properly test and loop over them and fix.
7. Inventory and character sheet and magic navigation is bad on pad
8. Contrast and colours and left hand headings on system menu - bad
9. We want height fog for below eye level ground/water hugging mist banks/clouds/drifts using community shaders
10. Loading screen seems to almost always be crocodiles
11. Loading screen text is horizontally squashed on mobile (unfolded viewport)
12. Map - now is the correct one. In the same style as the map already is, in the undiscovered/fog of war bits of it, add broad brush outlines of the province, dots for the majority cities and their names, and the major roads. Do it so it looks like a rough sketch map, which you're then filling in with detail as you explore and discover.
13. Creature encounters - felt very sparse, and I only found hackwings and giant centipedes, nothing else. Thought we were supposed to have a very large variety, benign and hostile, varying by region and danger band and geography, etc.
14. Map text and marker sizes on zoom - behave weirdly. Move around/don't zoom properly.
15. Camera behaviour when hit - does something mad, like dips underground or something
16. Flat mossy pebble texture - I am guessing it might be a fallback - something from BM&v. It's used very extensively, often there are huge fields of it, and it's like shiny and totally flat and looks bad.
17. "Shiny" reflective land textures generally - e.g. on hillsides - have lots of these, look unnatural
18. Weird lighting and can't see the sky. Overdone fog? Too much of the bad kind (blocking the sky, making the light weird), not enough of the good kind (cool low lying below eye level drifting volumetric misty clouds)
19. Water flowing - even in bodies of water that are supposed to read as still they have a flowing effect on them
20. Rivers messed up. Really badly. Especially on sloping land. I thought we were supposed to have resolved this by doing them the "Skyrim way" and by adjusting our land to enable it. Simplify whatever we are trying to do. Currently we have like random rapid and waterfall pieces hovering in the air and flowing the wrong way, bits of hovering river surface, all that stuff. You can change our hydrology graph and plan for where water should go if it makes it easier. We could just have water in flat cells, and simpler falls/rapids between them when there are two flat enough cells adjacent for example.
21. Roads poorly implemented - just flat texture
22. Claywater huts - no doors!
23. Claywater station house - there's no house or stables
24. Claywater people - can't talk to any of them except Livia Varinus. And she only has the barter topic.
25. Claywater well - texture at base is fighting land texture
26. Map UI pane appears over dialogue UI pane for some reason
27. "Talk" popup appears during combat with people (e.g. the deserter near Claywater)
28. Searching dead Livia Varinus opened dialogue!
29. Purple roadsigns - the sign bits on the poles, some untextured lilac colour
30. Rivers on map don't match reality. Map presumably needs to be rebuilt off our new terrain and waterways.
31. Claywater has like landings and dock stuff badly placed (e.g. underwater).
32. Not sure the between region plant and tree variation has been done well, different regions felt pretty similar
33. Freeclimb on trees was buggy - e.g. can't handle uneven surfaces or slightly overhangs; at rest often the player head or limbs clipped into the tree
34. My default character needs a lot of gold so I can try buying things in claywater.

Rulings in the same comment: use Paris as the only game machine for now (it ran the play test uninterrupted); any
loops involving checks in the game need to be massively optimised and sped up; distant terrain, tree and object LOD
rebuild waits until all of the above is fixed.

## Triage

| # | class | chunk | fix |
|---|---|---|---|
| 20, 19 | blocker | 1.15 water | Simplify to the owner's rule: water only in flat cells at one level, a fall or rapid piece only between two adjacent flat cells with a level step, no river surface on sloping land; the hydrology graph and the terrain may change to make that true; still water gets the still-water type (no flow). |
| 3 | blocker | 1.15 built pieces | The boardwalk and stair-tower rule placed pieces where no path or shore asked for them: remove the rule's output outside authored places and docks; re-seat the kept ones on ground. |
| 4 | blocker | 1.15 vegetation | Tree seating: sink each tree so the trunk base, not the root tips, meets the ground (per-model base offset from the mesh bounds). |
| 5 | blocker | 1.15 vegetation | Neon and washed-out trees: wrong or missing texture sets on some BM&V tree records; audit every placed tree model's textures, fix the paths. |
| 16, 17 | blocker | 1.15 materials | The flat shiny pebble texture is a landscape texture with no normal/specular set up (or a fallback); the hillside shine is the same class. Audit every landscape texture record for its normal map and specular strength; replace the fallback. |
| 18, 9 | blocker | 1.15 light and weather | Our weathers' fog near/far and sky colours block the sky; cut the sky-blocking fog, add Community Shaders' exponential height fog with volumetric fog, ground-hugging, per region. |
| 29 | blocker | 1.15 built pieces | Purple sign boards: a missing texture on the sign mesh; find the asset, ship the texture or swap the mesh. |
| 21 | polish | 1.15 roads | Roads are painted texture only; add the road mesh kit or landscape shaping the Skyrim way (0034: measure how Skyrim.esm builds a road). |
| 22, 23, 25, 31 | blocker | 1.15 §f Claywater | Huts get doors (the hut models with door frames and placed doors); the station house and stables are placed (the Tropical Skyrim imperial farmhouse, as ruled 2026-11-01); the well's base is cleared of fighting ground; docks re-seated to the water level. |
| 24, 28, 27 | blocker | 1.3 | Claywater's people have no dialogue wired (only Livia's barter topic reached the game): the topic routes from the records to every Claywater person; the dialogue intercept must not fire on a corpse (search) nor on a hostile in combat. |
| 13, 32 | polish | 1.15 §g, vegetation | Encounters: the spawn rule's density and the per-region creature lists are thin in the walked regions; raise density and widen the lists per region and band from the ecology research. Region variation: per-region tree and plant sets differ too little; re-draw the sets. |
| 2, 1, 34 | polish | 1.15 region saves, 1.10 | Region saves are made in third person, one of them at Claywater's station; the default character carries 5,000 gold. |
| 15 | blocker | 1.6 | Camera on hit: a camera mod's hit reaction or our lock-on's camera pushes the camera under the ground; find the setting, turn it off. |
| 6, 7, 8 | blocker | 1.12 | Pad navigation of inventory, character sheet and magic; the System pane's contrast and headings; and a fast out-of-game loop over every menu with the pad (the UI is HTML: render each pane off game with pad events, read the focus path) before the in-game proof. |
| 26, 14, 12, 30 | blocker | 1.12 chart | The map pane must close when dialogue opens; markers and labels scale with zoom; the chart is re-rendered from the current terrain and water; under the fog the sketch layer: province outline, the major cities as dots with names, the major roads, in the chart's own style. |
| 10, 11 | polish | 1.9 | Loading screens: weight the model list so no one model dominates; the text's horizontal scale on the unfolded phone viewport. |
| 33 | polish | climbing | FreeClimb on trees: the mod's own mechanics are the modder's (ruling 2026-10-31); what is ours is the tree collision our placement gives it; check the tree models' collision before touching the mod. |
