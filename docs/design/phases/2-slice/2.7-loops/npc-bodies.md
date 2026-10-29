<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.7-loops/npc-bodies.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 2.7m2: slice NPC bodies

Survey of every slice person (89 in `living.json`) on the production actor,
headless: `npm run look:npc -- --all --out <dir>` (`tooling/visual-look/npc.mjs`,
about 4 s a person; front, side, back, head close-up, plus `facts.json`).
Before sheets: `lanes/2.7/m2-shots/before/` (the tree without this lane's
fixes); after: `lanes/2.7/m2-shots/after/`; montages beside each.

| Class | NPCs | Mechanism | Fix at source |
|---|---|---|---|
| A. Human-tan arms, legs and shoulders on every Argonian and Khajiit in clothes (wrong-race skin) | 89 (every outfit has a piece with a `_wearerSkin` shape: 43 shipped GLBs) | `build_armour` ships the wearer-skin shape untextured; `gltfpack` dropped its now-unused `TEXCOORD_0`, so the wearer's skin material sampled one texel | `kit_compress.py:282` `-kv` under `keepVertexAttributes`; `publish_characters.py:52-55` armour and cloth policies keep attributes; `publish_characters.py:100` the structure gate compares wearer-skin UVs raw vs shipped (was red on 43 files before the republish) |
| B. Head floating over a neck gap (Swims-The-Channel-Twice) | 10 women in `marsh-native-wrap`, `-kilt`, `-rags` (female builds stop 0.34 source units below the body's neck; single-sided shell, its neck faces point inward) | the torso piece hid the race body, and the piece carries no visible neck | `armourMounting.ts:281` `leavesNeckBare`, used at `:192`: a torso piece whose top stops more than 1.5 % of body height under the body's top leaves the body drawn beneath it |
| C. Head a different colour from the body | 82 (face donor's tint differs from the record's skin-tint donor) | the donor FaceGen head has the donor's skin baked in; the body took another donor's tint | `look.ts:80` the body wears the face donor's tint when a donor head is worn; `npc_roster.py:1409` writes face donors' tints into `lookTints.json` |
| D. Donor hair, horns and frills through helmets | 15 helmet wearers whose donor hair is not in the build's slot table | armour hides body meshes by `meshBipedSlots`; the donor head's meshes were never in it | `build_faces.py:259` records each kept mesh's NIF partitions in `faces.json`; `look.ts:101` merges them into the worn build; `PeopleLayer.tsx:271` passes that build |

Checked and not defects (reader adjudication with evidence): the dark headwrap
of face donor Shahvee (hair texture 95 % opaque by its alpha), the orcish
helmet's own horsehair plume, war paint baked into a donor head, garment
pattern on Bright-Frill's bodice, hornless donors.

## Measure

| Measure | Command | Bar | Measured (2026-10-19) |
|---|---|---|---|
| Sheet time | `npm run look:npc -- --npc npc.<id>` | < 30 s | 4-7 s one person; 89 in 347 s (max 7.5 s, median 3.7 s) |
| Body defects | reader close over `after-montage/m00-m22` plus the neck close-ups of class B | 0 | 0 (three readers, borderline flags settled by a fourth: DEFECTS 0) |
| Tests | `vitest run packages/game-core/src/actors packages/game-core/src/people/look.test.ts packages/scene/src/people`; `pytest pipeline/test_publish_characters.py test_kit_compress.py test_build_faces.py`; `pytest worldgen/test_npc_roster.py test_living_twins.py` | pass | 99 + 24 + 3 + 47 pass |
| People in motion | `visual:check -- people-in-motion` (scenario person-villager-wander, RunPod pod) | pass | PASS: max jump 0.04 m, foot/root median 0.707 (p10 0.495, p90 0.805), states IDLE/TURN/WALK |
| Dress flicker in motion | `look:npc -- --motion` for the ten class-B women (lanes/2.7/m5-report.md), reader over `lanes/2.7/m5-shots/motion/` | 0 flicker | 0: ten of ten CLEAN (`reader-verdict.md`); nine tops leave the back bare, steady, read as the garment's design |

Reader checklist per sheet: head joined (no gap or band at the neck); hands,
feet, tail, eyes present; scale; head and body one skin colour, no human skin
on a beast race; no hair or horns through a helmet, no skin through cloth.
