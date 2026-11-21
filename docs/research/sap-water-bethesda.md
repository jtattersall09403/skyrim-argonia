# How Bethesda made small still pools and coloured liquids (for the Hist sap pool)

Measured 2026-11-21 with Mutagen over the catalogue's load order (Skyrim.esm, Update, the DLCs, Tropical Skyrim, King
of the Murkmire and the rest), each record as its load-order winner has it. Values: opacity 0..100, reflectivity,
fresnel, fog above water far plane (units over which shallow turns to deep), the three noise layers' wind speeds.

## Water types

| record (winner) | use | opacity | refl. | fresnel | fog far | noise speeds | shallow / deep |
|---|---|---|---|---|---|---|---|
| Skyrim.esm DefaultVolcanicWater (Tropical Skyrim) | Eastmarch hot-spring pools | 93 | 0.98 | 0.07 | 140 | 0.014 0.029 0.045 | (111,103,53) / (119,101,28) |
| Dawnguard DLC1BloodWater; Dragonborn DLC2dunKolbjornBlood | blood pools, barrels: a thick coloured liquid | 100 | 0.55 | 0.07 | 30 | 0 0.003 0.01 | (69,18,14) / (12,4,3) |
| Skyrim.esm MurkyWater (Update) | murky still water | 100 | 0.55 | 0.25 | 60 | 0.016 0.02 0.02 | (26,19,19) / (9,9,6) |
| Skyrim.esm DefaultMarshWater (Tropical Skyrim) | marsh | 30 | 0.23 | 0.05 | 110 | 0.007 0.007 0.007 | (56,53,37) / (77,61,36) |
| Skyrim.esm BlackreachWater (Update) | Blackreach | 100 | 0.55 | 0.35 | 290 | 0.022 0.012 0.065 | (40,72,89) / (21,104,102) |
| Skyrim.esm PuddleWater / PuddleWaterLiteFog | the puddle activators | 100 | 0.51 / 0.71 | 0.2 | 10 | 0.051 0.036 0.011 | (11,13,12) / (11,15,15) |
| Skyrim.esm DefaultIntWaterAnkleHeightStill / WaistHeightStill | still interior pools | 100 | 0.6 | 0.05 | 120 / 300 | 0.07 0.1 0.06 | (44,58,55) / (6,9,9) |
| Dawnguard LavaSettings; Skyrim.esm LavaWater | lava | 100 | 1 / 0.84 | 0.23 / 0.63 | 10 / 1000 | slow / fast | orange / red |
| King of the Murkmire DefaultHistSapWater | the mod's Hist sap | 100 | 0.79 | 0.07 | 140 | 0.014 0.029 0.045 | (162,82,2) / (141,60,5) |

No Soul Cairn water type exists in Dawnguard (the Soul Cairn has none); the Eastmarch hot springs use
DefaultVolcanicWater. King of the Murkmire's DefaultHistSapWater (and DefaultIchorWater) is DefaultVolcanicWater
field for field (same noise textures, directions, speeds, specular) recoloured, with opacity raised to 100,
WaterReflectionMagnitude cut from 0.14 to 0.02, the displacement turned off and the shallow and deep colours nearly
equal: in a 3-unit skin that is an even opaque orange disc, whatever the game does.

The look-governing rest of DefaultVolcanicWater (the template): specular power 543, sun sparkle magnitude 0.88 /
power 1725, displacement start 0.7, force 0.1, velocity 0.85, falloff 0.8, dampener 0.98, noise UV scales
2210 / 652 / 217 and amplitudes 0.18 / 0.14 / 0.20 over textures/water/defaultwater.dds, wind directions 312 / 278 /
56 (they disagree: still), noise falloff 5580, reflection magnitude 0.14, no current. DLC1BloodWater: specular power
1329, sparkle 3.08, displacement 0.1 / 0.4 / 0.85, UV 0 / 1123 / 290, amplitude 0 / 0.1 / 0.1, reflection magnitude
0.58, material Skyrim.esm:012F40.

## Placed water activators (ACTI with a water type)

| activator | model | bounds (x, y, z) |
|---|---|---|
| Skyrim.esm WaterPuddleLiteFog 0FD0DC, WaterPuddleFlow 0FE091, WaterPuddleDefaultIntAnkleStill 0FD0D7 | water/waterpuddle01.nif | -154..148, -152..199, -2..0 (-10 for the ankle-still one) |
| Skyrim.esm WaterPuddleLongFlow 10DE15, WaterPuddleLongDefailtIntAnkleStill 10DE14 | water/waterpuddlelong.nif | -256..238, -764..582, -2..0 |
| Skyrim.esm Water1024* (Marsh, Deepwood, ShadowmeresPool, DefaultIntAnkleStill...) | water/water1024.nif | 1024 square |
| Dawnguard LargeRainBarrel_BloodWater01, Blood_RainWaterBarrel | clutter barrels | a barrel's top |
| King of the Murkmire WaterPuddleHist 3D870E, Water1024HistSap 1655D9 | waterpuddle01 / water1024 | as vanilla's |

Vanilla has one round puddle mesh; a pool's size is its scale. Placement depth (how far vanilla seats a puddle under
its rim) was not measured ref by ref; the names say it: ankle-height (fog 120) and waist-height (fog 300) still
pools, and the puddle's own bounds dip 2 to 10 units.

## What we made of it

Our water type is DefaultVolcanicWater (Bethesda's own small still pool, the record the mod recoloured), changed only
in what makes it sap: tools/places/own_bases.py says the values and why. The bowl's depth (64 units, knee-deep, between
the ankle and waist pools) gives the fog distance (56) something to turn dark over.
