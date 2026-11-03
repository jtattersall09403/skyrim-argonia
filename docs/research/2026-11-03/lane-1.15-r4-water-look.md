# Lane 1.15-r4-water-look: the WATR records diffed against Skyrim.esm

Round 4 batch one: nine stills showed far water marbled and blocky white-and-dark. The brief blamed the WATR split.

## The diff (out/ArgoniaWorld.esm, 03 Nov 01:03, the batch's build, against Skyrim.esm)

- **Subrecords.** All seven types carry exactly their template's subrecords (DefaultWater: NNAM x3, ANAM, FNAM, SNAM, DATA, DNAM, GNAM, NAM0, NAM1; DefaultRiverWater: the same with MNAM instead of SNAM), plus FULL. NNAM, FNAM, SNAM/MNAM, DATA, GNAM, NAM0 and NAM1 match byte for byte. The noise maps are vanilla `textures/water/defaultwater.dds` (Skyrim - Textures7.bsa). (Corrected round 5: Tropical Skyrim lays a loose `textures/water/defaultwater.dds`, and Update.esm and Tropical Skyrim override the DefaultWater these copied; water-types.md finding A.)
- **Fields that differ, all ours by design (layer.py TYPES):**
  - ANAM opacity: 35 to 90, against 30 (still) and 50 (river).
  - DNAM floats 8 and 9: above-water fog near and far. Near is 0 (the river template has -10); far runs 60 to 150 (vanilla 110 and 150).
  - DNAM 10 to 12: shallow, deep and reflection colour. Ours are brighter than vanilla's (37,52,37 / 5,16,5 / 103,122,117), and **their alpha byte was 0xFF where vanilla's is 0** (removed).
  - DNAM 33 and 35: the fog amounts.
  - DNAM 36 and 37: underwater fog near and far. Near is 0 (vanilla -500 and -1400).
- **Unchanged by the split.** No other DNAM float differs, so the noise layers' winds and scales, the specular, the fresnel and the displacement are the template's. The four still types are byte-identical in shading to round 3's (`git log -p` of layer.py: only the FormKey order and the river template changed).

## The cause

The WRLD record, not the WATR records. Tamriel carries NAM2 = NAM3 = DefaultWater and NAM4 (the LOD water height) = -14000, its DNAM default water height. ARG_Province carried NAM2 only: no NAM3 (LOD water type) and no NAM4 (`tools/ArgoniaGen/WaterRecords.cs:48`, which set only `ws.Water`).

The engine therefore drew distant water with no LOD water type at height 0. Every far cell whose terrain LOD lies under 0 shows that untyped plane, tiled per LOD quad. That matches "at distance", "tiled" and "blocky". Round 4's ground (s11 to s17) changed which LOD quads fall under 0, which explains why it is new since round 3.

This is inferred from the record diff and the engine's WRLD contract. It is not yet proven in game.

## Changed

- `WaterRecords.Load`: sets NAM3 to the sea type and NAM4 to DNAM's default water height, as Tamriel does. The colours are written with alpha 0.
- `test_water_writer.py`:
  - every WATR subrecord is checked against its template, byte for byte, apart from the fields named above;
  - WRLD NAM3 equals NAM2, and NAM4 equals the default water height;
  - a new test checks that every texture the WATR records name resolves in the vanilla BSA index.

## Measured

The ArgoniaGen build is clean. `test_water_writer.py`: 4 passed in 106 s.

## Owed in game

journey river-steps (its still-body and river stops; header checklist extended), ledger row in docs/phases/1-core-loop/checks.md.
Needs the province plugin rebuilt (WRLD) and the LOD rerun on it before the batch.
