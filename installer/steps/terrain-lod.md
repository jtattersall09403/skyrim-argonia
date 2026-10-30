# Install step: distant terrain (xLODGen terrain LOD; 2.W4 §c, decisions 0014 §4, owner: keep xLODGen)

Made on the player's machine after the mods are laid and before the first launch. Every output is a derived file,
written into the player's mod folder `Argonia LOD (generated)`, never shipped or committed. The game machine runs the
same steps through `infra/gpu-box/lod.sh run prepare terrain collect` (lod.ps1 drives the GUI).

Needs: xLODGen (sheson, beta 132, `xlodgen` in data/dependencies.json; a free tool the player downloads, nothing of
it shipped); our ESMs laid; `LODSettings\ARG_Province.lod` (16 bytes, written by `infra/gpu-box/lodsettings.py` from
our land: xLODGen lists a worldspace only when this file exists, and the game reads it to place the LOD).

1. **Prepare.** The profile laid with no LOD mod and our ESMs; `LODSettings\ARG_Province.lod` in Data.
2. **Terrain LOD.** Run `xLODGenx64.exe -sse -lodgen -o:"<mods>\Argonia LOD (generated)\"`, tick ARG_Province only,
   Terrain LOD on, Objects LOD, Trees LOD and Occlusion off, Generate. It ends with "LOD generation done." Measured
   on the g4dn (game-13): about 26 min, 14,545 files (levels 4/8/16/32, 256 px diffuse and normal), 346 MB.
3. **Order.** `Argonia LOD (generated)` below `argonia-map` (the chart's block 0,0 replaces the LOD's level-32 block).
4. **Verify in game.** From the Claywater scene look out over the marsh: distant land has shape to the horizon, with
   no holes and no hard edge.
