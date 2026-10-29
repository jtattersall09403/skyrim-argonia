# 0028: The land is Tropical Skyrim, made through Skyrim's own systems; we author data, the engine does the rest

**Status:** decided 2026-10-29 (owner, in the 0.1 session): "The old repo recreated a load of stuff for how we
built the land and placed everything on it and frankly it didn't work brilliantly. I want us to build our world
natively in skyrim's system. The land itself (terrain, textures, grass, trees, vegetation, rocks, scatter, etc)
should be tropical skyrim (not the black marsh & valenwood mod any more). As much as possible should use whatever
skyrim's inbuilt systems and engine is for all of this." The owner asked how much we must tell the game and how
much it does by itself. This record answers that and binds the world track to it.

## What Skyrim does by itself, and what must be data

Skyrim has no runtime procedural world: the engine reads records and placed references. But several of those
records are **rules the engine applies everywhere**, so authoring a few rules covers the province; and the
Creation Kit holds a **generator** that turns region rules into placed references once. The split:

| Layer | Who does the work | What we author | What we never author |
|---|---|---|---|
| **Terrain heights** | the engine renders LAND | LAND records from the frozen heightfield (2.W1); local sculpts under buildings | any mesh of ground |
| **Ground textures** | the engine blends up to six layers per quadrant | which LTEX goes where, by land-cover class, painted into LAND | the textures (Tropical Skyrim's) |
| **Grass and groundcover** | **the engine, fully**: each land texture carries grass types (GRAS) and the engine scatters them at runtime wherever that texture is painted | nothing beyond the texture choice; density only through `iMinGrassSize`-class settings and the grass records Tropical Skyrim already attaches | a single grass reference |
| **Trees, shrubs, rocks, scatter** | **the CK region generator** (region → Objects tab: object list, density, slope and height bands, clustering, water avoidance), run once, scripted; it writes ordinary REFRs | region records (REGN) with their object lists and densities per land-cover class; a region map of the province | a hand-placed tree outside a place |
| **Weather, fog, sky, lighting** | **the engine**: each region's weather list picks weather by chance and time; each WTHR carries fog near and far, sky colours, image space; climates set day length and sun | REGN weather lists, a few WTHR/CLMT/IMGS records (Tropical Skyrim's weathers as the base, Black Marsh variants added), Community Shaders presets | a per-cell fog volume |
| **Mist and volumetrics** | Community Shaders (volumetric lighting and fog from the weather) and the weather fog | placed mist FX references only where a place wants them (hollows, over water), by the region generator's object list where a region is "misty" | hand-placed mist across the province |
| **Water** | the engine renders cell water at the cell's height | cell water heights and WATR types from the hydrology graph; rapids and falls pieces as REFRs; the flowmap painted by the CK's tool (scripted) | water meshes |
| **Navmesh** | NPCs walk NAVM | generated (our DotRecast job; the CK's generator as check), decision 0026 §4 | hand navmesh |
| **Distant land and trees (LOD)** | the engine renders the LOD files | nothing: xLODGen and DynDOLOD make them on the game machine and the player's machine (0014) | LOD files in the repo |
| **Places** | the engine | buildings, props, doors, markers, NPCs as REFRs (0026 §3), built by an agent the way a modder does | nothing |

So the world track authors **four kinds of data**: the heightfield into LAND; land-cover into LTEX paint;
regions (their map, object lists, weather lists); the hydrology into cell water and placed water pieces. Then it
runs **three generators once**: the CK's region generator for objects, our navmesh job, and the LOD tools. The
old project's placement machinery (scatter converters, groundcover rules, vegetation patches, tree cards,
quality bands) is not reproduced; its *data* (the flora rules, the land-cover classes, the hydrology graph) is
read only to fill the region and texture records.

## Decision

1. **The land is Tropical Skyrim** (SSE 78044, the owner's 2026-10-27 base-asset ruling, now made the whole land):
   terrain textures, grass, trees, shrubs, rocks, scatter, weather textures and sky come from Tropical Skyrim's
   replacements of the vanilla records. Because Tropical Skyrim replaces vanilla files in place, **our records
   reference the vanilla base forms** (vanilla LTEX, TREE, STAT, GRAS, WTHR ids) and the player's Tropical Skyrim
   install makes them tropical. We ship no Tropical Skyrim file and no vanilla one (0003); the quarantine (0012)
   reviews each vanilla form we reference for a Nordic tell that Tropical Skyrim does not replace.
2. **Black Marsh & Valenwood, Xanmeer, King of the Murkmire and the other Black Marsh mods are no longer the land.**
   They remain sources for what Tropical Skyrim lacks and the land is not: Argonian architecture and clutter,
   creatures, the odd marsh plant a place wants by hand. Decision 0006 §8's order is rewritten: for the land,
   Tropical Skyrim then vanilla; for buildings, props and creatures, the Black Marsh mods then Tropical Skyrim then
   vanilla.
3. **Regions are the unit of authorship.** The province is divided into regions by land-cover and climate class
   (from the imported region, climate and flora data), each a REGN with its object list (which vanilla tree, shrub,
   rock and flora forms, at what density, on what slopes and heights, how far from water), its weather list and
   its map name. The CK's region generator, scripted on the Windows game machine (0018), places the objects once;
   the output is reviewed as a diff of REFRs, like every generated record (0009). Hand placement is for places only.
4. **Grass is never placed.** It follows the painted land texture. Density and distance are game settings and the
   player's INI, set by the installer's recommended settings and the graphics baseline (0.3 §d).
5. **Weather, fog and light are region weather lists over Tropical Skyrim's weathers**, with Black Marsh variants
   (mist, tannin haze, storm) as our own WTHR records, and Community Shaders for volumetrics. No per-cell mist
   except where a place or region rule asks for it.
6. **The proof is G4 and then 2.W1–2.W4 on the whole province:** G4 builds the Claywater block this way (textures
   painted, one region with its object list generated by the CK, Tropical Skyrim loaded, grass appearing on its
   own); 2.W1–2.W4 do every cell.

## Consequences

- 0006 §8 rewritten as in §2; 0026 §3's vegetation bullet now says the CK's region generator is the placer.
- 0.2 G4: Tropical Skyrim is in the stack from the first in-game look; the block's trees and rocks come from a
  region record through the generator, not from a converter.
- 2.W1 paints vanilla LTEX forms by land-cover class (no BM&V textures); 2.W3 authors the regions and weather
  lists; 2.W4 runs the generator, the navmesh job and the LOD tools, and the old flora and groundcover rules feed
  region object lists rather than a scatter converter. The `scatter converter` of PLAN §4 is gone.
- The risk moves from "our placement machinery" to "the generator's output in dense jungle against the cell
  budget", measured by 2.W6 and thinned by region density, never by hand.
