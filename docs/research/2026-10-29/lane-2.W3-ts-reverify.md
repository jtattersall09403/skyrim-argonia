# Lane 2.W3-ts-reverify: Tropical Skyrim SE re-verification of region forms and weathers
Mutagen (overlay, 231 MB peak) over Data/Tropical Skyrim.esp: 70 TREE, 1 STAT, 38 WTHR overrides.
Not overridden before: STAT rocks RockL01 018199, RockL01Wet 0BB8BC, RockPileL03FieldGrass01Moss 024E4A; WTHR OvercastRain 0C821F, OvercastRainMA 10A231, StormRain 0C8220 (also our storm/squall templates), StormRainFF 10A23C, FogCO 10A235.
Applied via db.py: rain -> OvercastRainTU 10A242 (rain-ma merged); storm-rain -> StormRainTU 10A241 (storm-ff merged); fog-co -> fog-vt FogVT 10A7A7; storm/squall templates -> 10A241.
Exception: the 3 rocks (TS has no rock STAT; restyle, if any, is a file the synced Data lacks). Owed: L4 rock still.
Result: 3 not overridden (the intended rock exceptions), 0 weathers; script scratch chk.py. make plugin ok; plugin-check green.
make check red only elsewhere: unit test_unit_facts_live_only_in_the_units_module (untracked tools/chart/), lint, skse (other lanes' dirty files).
