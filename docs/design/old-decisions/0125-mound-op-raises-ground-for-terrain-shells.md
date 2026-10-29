<!-- imported unchanged from elder-souls-argonia docs/decisions/0125-mound-op-raises-ground-for-terrain-shells.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0125 — The `mound` layout op: a hill a terrain shell is set into, flat or ramp

Status: accepted (16k walk 11, places-a lane; commits 7139432b, 4d80f7dd).
Extends [0101](0101-building-pads-are-typed-patches-with-retaining-walls.md) (pads) and travels as
[0102](0102-a-place-carries-its-own-ground-and-hands-over-nothing-it-can-check-itself.md) requires.

## Context

Jungle Root Hollow's cave mouth (`rockcaveentrance02`) is an open-backed
shell: vanilla buries 83-87 % of its cave mouths' backs in the heightmap and
King of the Murkmire sets its mouths at the foot of a rise ringed with cliff
pieces. The frozen ground there is flat, so the back stood open. A 0101 pad
only levels a footprint to within 2 m of the ground; it cannot build a hill.
The owner asked for "a small hillock to embed the piece in".

## Decision

1. A layout op `{"op": "mound", "uid", "polygonM", "profile", "datumM" |
   "rampM", "blendM", "why", "sources"}` (`pad_overlay.mound_op_errors`,
   lifted out of `ops` by `layout.split_mounds`) is one op with two
   profiles. `flat` (the default) holds its polygon at an absolute
   `datumM`; `ramp` takes `rampM` `[[x0, z0, h0], [x1, z1, h1]]` and sets
   each point to the height interpolated linearly along that segment (held
   at h0 and h1 beyond its ends), so a hill rises from natural ground to a
   shell's back without terraces. Either blends back to the frozen ground
   over `blendM`.
2. Bounds: the datum (a ramp's high end) stands at most
   `MOUND_RAISE_MAX_M` = 15 m over the highest frozen ground under its
   corners; `blendM` 2-30 m. Like a pad it sets the ground to its profile,
   cutting where the ground stands higher as well as raising (Gang
   Ground's strand mound cuts the bluff toe at x 3951-3955), and mounds
   apply in id order, each over the ground the previous one left.
3. Water: a mound never rises out of mapped water. The bundle export
   refuses a mound with any corner or 2 m grid sample inside its polygon
   on wet ground (`mound_op_errors(..., is_wet)`), because water is frozen
   and a hill in a channel would change it. The four mounds on the tree
   (Bog Iron's three spoil banks, Root Hollow's `m-hill`) pass.
4. It travels in the place bundle (0102): the export writes it as a ground
   overlay of kind `mound` (`pad_overlay.mound_overlay`, `hardM` 0, applied
   with the run pads), and the runtime applies it at load
   (`packages/game-core/src/terrain/heightOverlays.ts`). The frozen
   terrain is never edited.
5. The workbench reads the same overlay (`pads.mound_overlays`,
   `opcache.pad_env`), and `Scene.view()` and `scan._without` keep the
   mound ops, so every check and every `wb.py bpy` shot sees the hill
   (4d80f7dd: shots had drawn the frozen ground with no hill).
6. The gate that judges a mound is `openBackRule`
   (`workbench/open_back.py`): every open ray of the shell's back must be
   closed by ground at its box entry or by a closed neighbour across it,
   sampled up to 7/8 of the shell's height (4d80f7dd: the 3/4 sample
   passed a 48.3 m hill under a hollow that runs to 51 m).

## Consequences

- A mound is authored only to embed a terrain shell or a spoil bank, with
  its `why` and `sources`; it is not a general terraforming tool.
- Tests: `worldgen/test_mound_op.py` (bounds, water, overlay shape, both
  profiles; it holds `packages/game-core/src/terrain/__fixtures__/ground-overlays-mounds.json`,
  which `heightOverlays.test.ts` asserts, so the twins agree),
  `placement-workbench/tests/test_scene_mounds.py`, `test_open_back.py`.
