# Lane 1.15-r4-water-colours: our seven WATR records back to vanilla's values

Cause: layer.py TYPES overrode opacity, the three colours and the fog (the diff in lane-1.15-r4-water-look.md); round 3, which had vanilla DefaultWater everywhere, read as water, and round 4's shore stills read marbled, blotchy, black and green (0034: measure Skyrim.esm and do the same).

Reverted (before in layer.py, after = the template's): opacity 35/40/60/90 to 30 (DefaultWater) or 50 (DefaultRiverWater); shallow/deep/reflection colours (74,112,104 etc., alpha was 0xFF) to vanilla's (37,52,37 / 5,16,5 / 103,122,117, alpha 0); fog above near 0 to the template's (river -10), far 60-150 to 110/150; fog above and under amounts to the template's; fog under near 0 to -500 and far 220-1200 to -1400. Every other DNAM field was already the template's.
Now only EDID and FULL (the name) differ. TYPES is name-only; the writer (tools/ArgoniaGen/WaterRecords.cs) no longer reads the override keys.
Test: test_water_writer.py asserts every non-EDID/FULL subrecord equals the template byte for byte (including all of DNAM and ANAM).
Owed in game: river and basin shore stills (checks.md row, journey river-steps): near water reads as water.
