# Install step: the world map (1.2 §e, route 2; decisions 0005 C9, 0014)

Made on the player's machine after the mods are laid and before the first launch. Every output is a derived file,
written into the player's mod folder, never shipped or committed. The build VM runs the same commands on the cached
mods into `out/argonia_map/argonia-map`, which `stack.py stage` lays as the overlay `argonia-map`.

Needs: Python with the `py:` pins in `infra/build-vm/toolchain.lock` (numpy, pillow); Flat World Map Framework
(29932, FOMOD Lite 1.9.990) laid with its "FWMF for Fantasy Paper Maps" package; the chart rendered from our data.

1. **The chart.** `python -m tools.chart render` writes `out/chart/sketch-4096.png` and `index.json` (the sketch
   layer: paper, coast, major rivers and roads, the border, the seven cities; no player marker).
2. **The overlay.** `python -m tools.chart fwmf --fwmf <mods>/flat-world-map --out <mods>/argonia-map` writes:
   - `meshes/terrain/arg_province/arg_province.32.0.0.btr`: FWMF's Tamriel block 0,0 with its paper quad moved to
     the chart's centre (4096, 4096 units) and scaled to its half side (262,144 units, 128 cells a side), both quads
     pointed at our textures, and Tamriel's own land and water shapes hidden;
   - `textures/terrain/arg_province/argonia-chart.dds` (the sketch, 4096 px DXT1, north up) and `back.dds` (our dark
     paper round it);
   - `SKSE/Plugins/FlatMapMarkersSSE.json`: ARG_Province whitelisted at the paper's height (180,000);
   - `argonia-map.json`: what was written and from where.
   Exit 1 means the block did not verify; a `FwmfChanged` stop means FWMF's Tamriel block is not what was measured
   (a new FWMF version): stop the install and report it.
3. **Order.** `argonia-map` above `Argonia LOD (generated)` and `flat-world-map` (its block 0,0 replaces the LOD's).
   Argonia.esm's WRLD override carries FWMF's map camera (269,488 to 435,000 units, pitch 90) and map offset.
4. **Verify in game.** From any Argonia scene open the Map: the parchment chart fills it (Gideon, Soulrest, Lilmoth,
   Blackrose, Archon, Stormhold, Thorn inked), and nothing of Skyrim's map (no Whiterun, no hold emblems).

Measured on the build VM (2026-10-30): block 710,800 bytes (3 Tamriel shapes hidden), chart DDS 8.4 MB.
