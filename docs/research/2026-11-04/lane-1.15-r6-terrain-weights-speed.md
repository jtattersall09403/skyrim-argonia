# Lane 1.15-r6-terrain-weights-speed: the texture-weight pass, same bytes, fewer seconds

## Change (tools/argonia_world/terrain/material.py)
- `value_noise`: the hash runs once per lattice node the window spans (period^-2 of the vertices), gathered back; x interpolated on each lattice row, then rows gathered. The same hash of the same nodes and the same float32 operations per vertex.
- `_weights`: each class works only over the bounding box where its blend weight is non-zero (outside, it adds 0), and its one-hot stroke is added at the winning texture alone instead of an (R, C, n_tex) one-hot product.
- No rule, constant or stop moved. `_keys` and `nearest_wet` are unchanged.

## Measured (build VM, current inputs, out/tws harness, no lock)
- cProfile, row cy 0 (the Builder row with its material_row and tint windows): before 15.1 s (`_weights` 11.7, value_noise 4.5, _hash 4.0, _tie 2.3, nearest_wet 2.3). After 6.7 s (`_weights` 3.5, value_noise < 0.3, nearest_wet 2.3, _keys 2.8).
- Wall time per row, before / after: cy -20 13.9 / 6.6 s; cy 0 (shore, wet 0.50) 17.2 / 5.9 s; cy 40 (marsh, slope 8.5) 16.7 / 6.5 s; cy 90 (hill, dh 41 m) 6.0 / 4.4 s. Median before about 15 s, after about 6.2 s: 2.4x.
- Whole province estimate: 262 rows x 6.2 s / 4 CPUs, about 410 s plus pool overhead, against about 1070 s (1508 s measured).

## Byte identity
- Per row, sha256 of the seam-fixed weights plus keep sets, and of every cell dict (layer alpha bytes, vhgt, vnml, vclr). Before = after on all four rows: -20 726e90818f37b602/1cf8897edcb8e421, 0 ea06dd32c60ec2b0/74dd624b198b65a2, 40 6d48d8e6d1c57422/8246637a939a3c48, 90 9fea087ae1b4dfb7/e9139bb73927b8bd.
- `terrain build --sample` output (every file except stats.json), HEAD and new: both 4cf17785c8774a0b.
- Terrain tests: 65 passed. The rules' numbers did not move, so the riverbed share and the alpha bars cannot change: the bytes are identical.

## Remains
- nearest_wet (2.3 s, 4 calls) and _keys are now the sink. The tint window in build.py recomputes a window inside material_row's window, about 40 % of a row. Memoising it is build.py's call (outside these paths).
- This code edit moves the code stamp, so the next build rebuilds every row once (about 410 s).
