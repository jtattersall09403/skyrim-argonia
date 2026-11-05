# Lane 1.15-r3-machine: what the build VM could not see, measured on the game machine

Build 7fa57b6 on argonia-play-ie, 2026-11-02 06:20-06:40 UTC, base save `argoniabase`. Inputs: [round 2](round-2.md),
[r2 textures](lane-1.15-r2-textures.md), [weather](../2026-11-01/lane-1.15-weather.md). Machine stopped, lock released.

## 1. Lavender surfaces: not a missing texture

Method: refs within 4,000 u of the panel markers 04 (coastal-lagoon-high, 28544,208896), 16 (flooded-forest-high,
36736,200704) and 20 (interior-swamp-high, 53248,36864) were read from `out/ArgoniaWorld.esm` and `out/Argonia.esm`.
That gave 40 base forms (Black Marsh.esm STATs, King of the Murkmire TREEs and STATs, one ARG rock). Their MODLs were
read from the mod plugins and their 64 texture slots from `data/mesh-textures.json`. Each texture was then looked up
on the machine as a loose file under `Data\` or by listing the BSA's name table (a PowerShell reader, `C:\argonia\bsa.ps1`;
BSArch is not installed on this machine).

- 36 are loose. 28 are in loaded archives: `_ResourcePack.bsa` 10 (`_ResourcePack.esl` is in `Skyrim.ccc`, so it
  loads although it is absent from `sResourceArchiveList2`), `King of the Murkmire.bsa` 6 (plugin active), and
  `Skyrim - Textures1/3/5.bsa` 12. Only BM&V's truncated normal string `textures\nor` resolves nowhere (already known).
- One lavender object was identified exactly. At flooded-forest-shore (-3666,24998) at 06:30, the saturated blue plant
  on the right is ref 0FA56A27, base `01mossDUPLICATE001` (Black Marsh.esm 0x17BD15), mesh
  `landscape\plants\florahangingmoss02aaa.nif` (loose). The NIF's BSLightingShaderProperty names
  `textures\landscape\grass\ReachGrassObj01.dds` and `_N.dds`, and both are loose on disk. The deployed file is BM&V's
  4096² DXT3, and its mean block colour is olive (61,66,33). So the file exists and is green, yet the plant draws blue.
- **Cause class:** a shader- or material-side fault, not a path. The candidates are a normal map drawn as diffuse
  (lavender is tangent-space blue), a shader flag that this stack (Community Shaders 1.9.1) renders wrongly, and
  vertex colours. Not measured. **Textures lane:** stop adding keep globs for these. Next, booth the one base
  (`bridge.py booth` with 0x17BD15's load-order id) twice, once with CS's `CommunityShaders.dll` set aside and once
  with it in place. Diff the NIF's shader flags and vertex-colour flag against a mesh that draws correctly
  (`ferny3`/FernLarge03).

## 2. Ground tan slabs

The 19 Argonia TXST diffuses (`TEXTUREPACK\landscape\*.dds`) are loose on the machine at the exact paths: 512² DXT3,
**mip count 0**. The slabs are not a missing ground texture. The terrain LOD on the machine
(`Data\meshes\terrain\arg_province`, `textures\terrain\arg_province`) is dated 2026-10-31 22:52. That is before the
ground s14-s16 rebuilds in the deployed ArgoniaWorld.esm (2026-11-02 04:49). Candidate: LOD from older heights
standing above the new terrain. Toggling LOD (`tll`) at vantage 16 was not conclusive, because the camera moved
between the two frames. **Ground lane:** rebuild terrain LOD from the deployed ESM (`lod.sh`) and re-shoot 04, 16 and
20. Add mipmaps to the TXST diffuses (shimmer at distance).

## 3. God rays and height fog

- The CS log loads 5 Argonia overrides. VolumetricLighting is loaded with its override applied, and
  `SkyrimPrefs.ini` has `bVolumetricLightingEnable=1` and `iVolumetricLightingQuality=1`.
- **ExponentialHeightFog: "ExponentialHeightFog.ini failed to load, feature disabled".** The release asset was laid at
  `Data\Features\` and `Data\ExponentialHeightFog\`, not `Data\Shaders\...`: the archive has no `Shaders/` root
  and the `community-shaders-height-fog` row in `data/dependencies.json` has no `pick_to`. **Weather lane:** add
  `"pick": ["Features", "ExponentialHeightFog"], "pick_to": {"Features": "Shaders/Features", "ExponentialHeightFog":
  "Shaders/ExponentialHeightFog"}` (stack.py:441), re-lay, and confirm "Loading Feature: 'ExponentialHeightFog'".
- HNAM is set on all 9 ARG weathers in the deployed Argonia.esm (Update.esm VOLIs 0x0D51-0x0D64).
- The dawn weather is what hides the sun. The bridge `weather` read at the coastal-lagoon-shore at 06:00 gave
  `ARG_Weather_wet_rain`, transitioning from **`SkyrimClearCO`** (vanilla). At flooded-forest-high,
  `fw ARG_Weather_clear_dry` gave way to `ARG_Weather_storm` after a moveto. The climate `ARG_Climate_black_marsh` lists
  Skyrim.esm 0x081A and 0x012F89 at 13 % each, plus monsoon_overcast 27, storm 20 and wet_rain 27. No sunny ARG weather
  is in the fallback list, and region lists override `fw`. **Weather lane:** the dawn check must `sw` a sunny ARG
  weather after the moveto and read it back. Review the two vanilla weathers (decision 0012).
- A `weather` read of `current: null` means a menu is open, which pauses the sky. It happened here behind a message
  box. Close menus before reading.

## 4. HUD: `core HudShow off` answers "usage"

Repro: `bridge.py core HudShow off|on|OFF` all returned `usage: hud <on|off>`, and `core MessageBox off` echoed
`"OFF"`. Cause: `natives.cpp:367` passed `RE::BSFixedString a`, and BSFixedString is a case-insensitive pool that
returns the casing first interned ("off" becomes "OFF"), so `views.cpp:682`'s exact compare always fails. Fix:
pass `*arg` (branch `fix/hudshow-arg`, 5c9f812, pushed; not built or deployed).

## 5. Rock booth: the journey names refs from another build

The first booth ref `ArgoniaWorld.esm|0xDD1A03` was read in game at (-223571.7, 261255.2, 37789.6), angle
(0, 0, 201.9), scale 0.99. That is the same as the deployed ESM, but its base is King of the Murkmire 0x03A57E, not
`ARG_Rock_gl_rock09` (0C0008), and it has no tilt (the journey says 49.3°). The stand point is 2,297 u from it, not
304, and it aims 116° away. The nearest 0C0008 ref in the deployed ESM is 61.5 km away. The journey was generated
from round-1 shards (66e4f70), and the placement has re-rolled since. **Harness or vegetation lane:** regenerate
rock-booth from the deployed `out/ArgoniaWorld.esm` in the same build as the deploy, and assert the base and tilt at
step 0 (`prid` plus the base read).
