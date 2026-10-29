<!-- imported unchanged from elder-souls-argonia docs/decisions/0056-armour-is-blended-to-the-wearer-not-deformed-to-fit.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0056 — Armour is blended to the wearer, not deformed to fit

**Status** accepted · **Supersedes** [0055](0055-a-collar-overlaps-the-neck-rather-than-meeting-it.md) ·
**Evidence** the [archived record](../research/archive/armour-neck-seam/0056-as-recorded.md),
`docs/evidence/races/armour-neck-check.measured.json`

## Why

A cuirass is not one mesh for all wearers. Skyrim ships male and female
meshes and `_0` / `_1` weight pairs for armour exactly as for bodies, and the
engine averages them by the actor's `NAM7` weight. A vanilla cuirass that
covers the neck embeds the neck-bearing body part
(`MaleUnderwearBodyArmor` / `FemaleUnderwearBodyArmor`), whose neck loop is a
bit-for-bit copy of the matching body's (iron: 0.000000000 difference over
the 26-vertex loop, all four pairs). Blended to the wearer's weight and taken
from the wearer's sex, the seam is **exact by construction**. Loading one
mesh for everybody and deforming its embedded skin to fit is assembling what
the authors never designed to fit.

## The decision

**One GLB per piece per sex, carrying `_1` geometry with `_0` as a glTF morph
target; the runtime sets `morphTargetInfluences = 1 − weight`.** That is
Skyrim's own model and three.js supports it natively.

- `armour.json` declares a per-sex base path without the `_0` / `_1` suffix.
  It is declared, never inferred: Bethesda uses several naming conventions
  (`iron/male` + `iron/f`, `studded/male` + `studded/female`, `elven/m` +
  `elven/f`, `steel/` + `steel/f`, and bare suffixes for dwarven, orcish and
  daedric).
- `armour.items.json` is at `schemaVersion: 2` with per-item
  `assets: { male, female }`, `sha256` and `coversBipedSlots`.
- **Coverage is per sex**: the male steel cuirass takes the forearms (slot
  38) and the female one does not, so `coversBipedSlots` is a map and
  `armourCoverage(piece, sex)` reads it.
- `races.json` publishes each build's `bodyWeight`.
- `armourMounting.ts` is sex-agnostic: it takes an already-resolved scene.

## What `neck_seam.py` keeps

The snap and lift (`NECK_LIFT`, `raise_polyline`, the snapping path of
`find_collar_rings`) are retired. `mesh_boundary`,
`closest_point_on_segments` and `vertex_weights` stay, shared with
`build_character.py`, which still carries duplicate copies to fold in.

## The gate

`validate_neck_rings` asserts only what the build cannot make true by
construction, three ways, each the signature of a defect that has shipped:

1. a ring that is a bit-for-bit copy of a reference neck must be the
   **wearer's own** (a male cuirass on a female wearer is refused);
2. the two sexes must not produce the **same** ring;
3. a declared weight pair must **move**: a morph that measures the same at
   both ends is a piece stuck at maximum weight.

Iron, studded and ebony embed the body's neck and are proved to 0.000002
units. The others close the neck with their own raised opening, and a neck
tapers, so comparing such a ring with the body's says nothing true; the gate
is silent there and says so. Their verdict is a line of sight against a real
wearer's skin, head included, measured on the shipped GLBs by
`scripts/measure-neck-seam.py`, which blends each piece to the wearer's
`bodyWeight` first. The gate was watched going red on the shipped defect
(a female cuirass pointed at the male mesh) before it was trusted;
`pipeline/test_build_armour.py` holds that case and five others.

The remaining open authored-opening cases are queued in the
[polish backlog](../phases/P-polish/backlog.md) with their causes. Elven has
no embedded skin; its throat opening (a raised gorget whose ring sits about
121 mm forward of the neck axis) is its own seam.

## Icons

`render_icon` in `blender/build_armour.py` hides every object that is not the
piece, so the reference bodies loaded for the batch never appear in an icon.
