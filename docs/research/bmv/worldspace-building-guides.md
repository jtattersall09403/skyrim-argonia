# Worldspace-building guides, rivers, texturing, LLM evidence, Black Marsh resources (web research, 2026-11-01)

Live docs covering the topic: decisions 0028 (land through Skyrim's systems), 0031 (ArgoniaWorld.esm), phases/1-core-loop/2.W2-water.md.
Nothing here contradicts them; findings below mostly add risks. Edit target for any action: 2.W2-water.md (water) and the 2.W1/2.W3 part READMEs (texturing).
Search tool returned thin results; every claim is marked with source and date. Nothing was verified in game.

## Findings first
1. No public guide exists for a generated 126x126-cell worldspace. Community practice is heightmap -> TESAnnwyn -> CK, then hand sculpt and hand paint. Treat our approach as unprecedented; there is no "known good" recipe to copy.
2. Pipeline sources are old (2012-2018, LE/early SE): Beyond Skyrim "World Heightmap Creation" says: greyscale (16-bit RAW) -> TESAnnwyn -> CK import, max 4096x4096, recommends <4K, and warns of a "sinking into ground" glitch on wide (x) worlds. Our 126 cells is far below that limit, so that bug is not a concern.
3. Texture painting: NO auto-paint tool for Skyrim LAND records (by slope/height/noise) was found. The CK is hand paint only. We are therefore building the first one; the standard from other engines (Unreal "auto material" rules by height/slope) is the right model. Layer limit: sources disagree (4 / 6 / 7 / UESP says CS allows 9 incl. base BTXT). A quadrant over its limit shows a black texture; deleting the dominant layer causes black-texture bugs. Check our writer's per-quadrant layer count against the engine's real cap (6 per CK reports).
4. Hard texture edges: in SE the usual causes are (a) alpha layers authored with hard weights, (b) terrain parallax disabling the engine's normal blending (Terrain Parallax Blending Fix, nexus SSE 88261), (c) alpha-test vs alpha-blend on land meshes (AutoBlend, github Cl3mus33/AutoBlend). Community Shaders has Terrain Blending (SSE 147616), Terrain Helper (143149) and Terrain Variation (148123) that break up tiling/hard edges at render time. These are player-side options, not data fixes; our data fix must be soft opacity ramps (feather weights across several vertices) and noise-broken class borders.
5. Water, sloped: the only community method found is tilted/stitched water activators plus raised banks/rocks to hide edges; "water activators do not know about each other" (Nexus forum 9104428, ~2020). The editor does not render activators properly and needs a cell refresh. Flow is a WaterType property (Linear Velocity, Flowmap on/scale). There is no CK flowmap generation tool; hand-paint only (Step forum 11744). So our stepped-plane design is the same family as community practice; seams and gaps are expected unless planes overlap and edges are buried in terrain.
6. Black water causes found (all LE/SE forum-grade evidence, low confidence):
   - Depth-of-field setting makes water black (Steam discussion, undated).
   - fWaterSSRIntensity=0.0001 fixes the dark line looking out over water (same source). Test by toggling SSR in Skyrim.ini / Community Shaders.
   - Cell flag "Has Water" and XCLW must be consistent; XCWT should be a known-working WATR (Step forum 16761). Our cells are HasWater with no XCLW (2.W2 "Starting state"): worth setting XCLW explicitly and XCWT.
   - Water LOD is part of terrain LOD meshes (DynDOLOD does not make it; xLODGen does), so missing/odd distant water points to the xLODGen run.
   - ENB/CS water shaders and water mods interact; Water for ENB 2.05 added CS particle support. Test with all graphics mods off to separate our data from shader behaviour.
   Hypothesis from this (not confirmed): placed Water1024 activators use the activator's own WATR, and a plane at the wrong WATR/depth or with SSR/refraction on a thin plane (no depth below it) reads black from low angles. Reproduce with SSR off first.
7. Region-generator use is already in 0028; nothing found contradicting it. Enderal critique (blog.radiator.debacle.us, 2021, a critic not a developer) says teams without terrain control end up spamming clutter: relevant to the "hollow misplaced rocks" and cheerful look.
8. LLM agents building worldspaces: NO evidence found of anyone using Claude Code/GPT to generate a Skyrim or Bethesda worldspace. Results were marketplace skill listings (mcpmarket.com, github HermeticOrmus/claude-code-game-development, mulosbron/worldgen-skills, a Udemy course): intended capability, not measured results. No benchmarks. Treat as hype. The real lesson is the same as ours: the agent needs a measured oracle (in-game stills), since generated geometry that passes data checks fails visually.
9. Black Marsh & Valenwood (ModDB black-marsh-valenwood): ModDB returned 403 to fetch; search snippets only. It bundles both regions; a commenter fixed pink grass by copying one grass texture over another, which implies it ships its own grass textures. Black Marsh ESPs were reportedly moved into a "Valenwood New Lands" mod after a takedown (Nexus image page 103849). Permissions NOT found; not verified whether it ships LTEX+GRAS. Do not rely on it (0028 already drops it).
10. Tropical Skyrim: the main mod is Soolie's (Nexus LE mod 33017, SE companions 36153 removes 15,000 trees, 33128 immersion). The AceeQ edition by tamikonelf (Nexus LE 69382) added more grass and edited water colours. Permissions text not retrieved. Check the exact SSE page named in the sourcing register for permissions before any asset reuse. Project Rainforest SE (sa547, Nexus SSE 20636, LE 93800) is NOT compatible with Tropical Skyrim; page says anyone may make patches; redistribution terms not retrieved. No Black Marsh swamp/mangrove-specific flora resource found in these searches.

## Likely causes of our reported symptoms (hypotheses to test)
- Same-texture swathes + hard edges: land-cover classes assigned as blocks; add noise-perturbed borders, soft weights, and secondary layers by slope/curvature/moisture. Not an engine limit.
- "Cheerful tropical beach": Tropical Skyrim's palette is the cause; swamp needs dark mud/peat LTEX, murky WATR colours and fog/weather (0028 weather rows), not only land texture.
- Floating planes / gaps: consistent with the community note that activators don't join; bury plane edges in terrain and overlap tiles.

## Not found / gaps (searches thin)
- Falskaar/Wyrmstooth/Enderal/Darkend/Midwood Isle/Project AHO technical postmortems: none located. Wyrmstooth Monthly Modder interview (elderscrolls.bethesda.net/en-EU/news/monthly-modder-jonx0r) exists; its answers were not read.
- xEdit/Mutagen auto-paint scripts: none. Hoddminir blog (hoddminir.blogspot.com, 2012 and 2021 "Region generation part I landscape") may hold hand-paint/region workflow; not read.
- Flowmap generators: none.

## Sources
- https://wiki.beyondskyrim.org/wiki/Arcane_University:World_Heightmap_Creation
- https://ck.uesp.net/wiki/Creating_a_Custom_Worldspace_with_LOD
- http://hoddminir.blogspot.com/2012/02/from-heightmap-to-worldspace-in-skyrim.html
- https://forsakenaskyrimmod.wordpress.com/2018/03/18/a-new-heightmap/
- https://www.nexusmods.com/skyrim/mods/56029 (Blender heightmaps)
- https://www.nexusmods.com/skyrimspecialedition/mods/42726 (NTN CK tutorials)
- https://forums.nexusmods.com/topic/9104428-how-to-make-a-small-river-that-flows-down-a-slope/
- https://ck.uesp.net/wiki/WaterType
- https://stepmodifications.org/forum/topic/11744-generate-water-flow-maps/
- https://stepmodifications.org/forum/topic/16761-missing-water/
- https://www.nexusmods.com/skyrim/mods/61837 (Skyrim Water Glitch Fix)
- https://forums.nexusmods.com/topic/7977203-water-lod-cutted/
- https://en.uesp.net/wiki/Tes5Mod:Mod_File_Format/LAND ; https://ck.uesp.net/wiki/Talk:Landscape ; https://forums.nexusmods.com/topic/1532898-how-to-texture-a-landscape
- https://www.nexusmods.com/skyrimspecialedition/mods/147616 ; /88261 ; /143149 ; /148123 ; https://github.com/Cl3mus33/AutoBlend
- https://github.com/mulosbron/worldgen-skills ; https://github.com/HermeticOrmus/claude-code-game-development ; https://mcpmarket.com/tools/skills/terrain-system-development
- https://www.moddb.com/mods/black-marsh-valenwood ; https://www.nexusmods.com/skyrimspecialedition/images/103849
- https://www.nexusmods.com/skyrim/mods/33017 ; /69382 ; https://www.nexusmods.com/skyrimspecialedition/mods/36153 ; /33128
- https://nexusmods.com/skyrimspecialedition/mods/20636 (Project Rainforest SE)
- https://www.blog.radiator.debacle.us/2021/05/open-world-rpg-design-notes-from.html

Covered: docs 0028, 0031, 2.W2-water.md · Skipped: repo code and game (read-only web brief); full-page reads of most forum threads (search snippets only; ModDB 403)
