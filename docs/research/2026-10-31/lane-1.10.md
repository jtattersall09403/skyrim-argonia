# lane-1.10: the player character

**Cause** (the brief's diagnosis, confirmed in the data): Skyrim.esm's Player (0x7) is NordRace (013746) with
HairMaleNord01 (051507) and five Nord tint layers (presets 98, 103, 135, 138, 143); base_save.py's
`player.setrace ArgonianRace` swapped race and body and kept those, so a Nord head and hair sat on an Argonian body.

**Read of Skyrim.esm** (an ArgoniaGen probe, not kept): ArgonianRace (013740) male defaults are MaleHeadArgonian,
MaleMouthArgonian, MaleEyesArgonian, BrowsMaleArgonian00; an Argonian's "hair" head parts are its horns and frills
(HairArgonianMale00-10). Ten male race presets; ArgonianMalePreset06 (0B2E10) is the natural one: dark green
SkinTone (54,78,33 at 0.66), FeatherColorBlack frills, pale markings, HairArgonianMale05, blue eyes, scars.
Preset05 has blue face paint and blue feathers; preset03 a yellow skin tone. No Black Marsh or Tropical Skyrim
plugin in our stack carries Argonian head parts or presets, so the vanilla race's own parts are the source.

**Fix at the source** (route 1, data):
- data/quarantine/start.json `player`: Player's formKey, the race and the preset (edid checked).
- tools/argonia_world/intermediate.py `player_layer`: one NPC_ override record.
- tools/ArgoniaGen/RaceRecords.cs `Player`: Player copied from Skyrim.esm (without its localized FULL/SHRT: the
  strings are in the BSA; the save's player name stands), race set, the preset's head parts, feather colour, texture
  lighting, morphs, face parts, tints and weight copied whole, as the race menu does; HeadTexture cleared so the face
  uses the race's default texture and matches the body (no neck seam). No FaceGen: the engine builds the player's
  face at run time (0014).
- infra/gpu-box/base_save.py: no setrace; it fails if the new game's player is not ArgonianRace.

**L1**: tools/argonia_world/tests/test_player_record.py, 2 passed: the generated record
(plugin/Argonia/Npcs/Player - 000007_Skyrim.esm.yaml) is ArgonianRace with the four Argonian parts, no Nord hair,
FeatherColorBlack, no head texture, a dark green skin tone, none of the Nord's tint presets; player_layer from
start.json and its formKey guard.

**L4 owed**: no game machine (London g6 reclaimed; Stockholm waits on the owner's IAM edit). The batch
tests/journeys/batches/lane-1.10.sh deploys (base_save.py remakes argoniabase and ArgoniaWalk), proves the oracle,
runs journey player-look (GetIsRace, then back, side and front stills at the play camera) from ArgoniaWalk and reads
argoniabase's race. A `reader` then judges the three stills: an Argonian head, no Nord features, natural colours,
no seam at the neck. Risk: the third-person orbit staying put during setangle (run_journey.py's note) is assumed
for the side and front stills; if the camera follows, a `tfc` free camera step replaces it.
