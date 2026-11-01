<!-- imported unchanged from elder-souls-argonia docs/research/rendering/volumetric-bars/README.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Volumetric visual bars

The reference pictures the WebGPU volumetric features (decisions 0111, 0112) are judged against by the `reader` agent; owner-supplied 2026-10-02, not shipped assets. Fire has no picture: its bar is https://threejs.org/examples/webgpu_volume_fire.html. Owners of new bars add a row here.

| File | What it is the bar for | Feature that uses it | Judged how |
| --- | --- | --- | --- |
| fog-over-water-1.png | Fog and mist lying over water | froxel fog | reader compares a studio capture at a water view with the picture |
| fog-over-water-2.png | Fog and mist lying over water | froxel fog | same |
| fog-over-water-3.png | Fog and mist lying over water | froxel fog | same |
| fog-over-water-4.png | Fog and mist lying over water | froxel fog | same |
| fog-local-light-scattering.png | Fog with local light scattering around lights | local light scattering | reader compares a capture beside a lit fixture in fog |
| god-rays-canopy-exterior.png | God rays outside under a tree canopy | god rays | reader compares a capture under canopy at low sun |
| god-rays-large-interior.png | God rays in a large church-like interior | god rays, froxel fog | reader compares a capture inside a large hall |
| god-rays-overhead-shaft.png | Overhead external light falling into an area | god rays | reader compares a capture under an opening |
| god-rays-general.png | General god-ray look | god rays, froxel fog, local light scattering | reader compares the overall look |
| god-rays-small-interior-1.png | God rays and light in a small interior | local light scattering, froxel fog | reader compares a capture inside a small room |
| god-rays-small-interior-2.png | God rays and light in a small interior | local light scattering, froxel fog | same |
| marsh-mist-reference-nexus-33017.jpg | Low marsh mist QUALITY bar: soft, layered, below eye level (ours also lies over the water). Source https://staticdelivery.nexusmods.com/mods/110/images/33017-5-1362912648.jpg (Nexus Skyrim mod 33017 gallery image, owner-supplied 2026-10-03; the WebP re-encoded to JPEG at half size) | marsh mist (packages/game-core/src/air/marshMist) | outdoor-fx loop sheet row 1 (apps/world-studio/scripts/outdoor-fx-loop.mjs); reader judges the fog only |
| cap-cloud-trial-billboards-r3.jpg | Evidence, not a bar: mountain cap cloud as billboard puffs, best round (about 50 % of the target look) | none (walk 11 cap-cloud trial, do-not-ship, see decision 0124) | not judged |
| cap-cloud-trial-sheets-r7.jpg | Evidence, not a bar: mountain cap cloud as sheets (30-35 % of the target look, +231 % frame cost) | none (walk 11 cap-cloud trial, do-not-ship, see decision 0124) | not judged |
