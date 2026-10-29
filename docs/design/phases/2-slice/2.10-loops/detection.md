<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.10-loops/detection.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: detection bands (2.10 § Loops, lane 2.10-b)

Rule (decisions 0151 item 1, 0092; world/76 §118 Sneak row, §120.2): one
notice service (`noticeRate`/`stepNotice`) per observer, nothing shared;
noise = gait × armour class × surface from the detection rows; light = the
light table over the light sample (sun or moon by the clock and weather,
plus the nearest placed light's inverse-square falloff); a noise within
`hearingM` raises suspicion with the cone ignored; beasts add scent within
`scentM`. The eye is the worst observer state mapped by the rows' `eye`.
Eyes: a pod strip of the eye climbing and falling on a lit and a dark
approach (combat `visual:check` group `stealth`), read by a `reader`.

Measures:

- `cd packages/game-core && npx vitest run src/perception`
- `npm run visual:check -w @elder-souls/combat-sandbox -- stealth`

Expected band: world/76 carries no worked detection bands, so the expected
column is built from decision 0092 and the Skyrim dossier, not from any
design table: 0.8 s to engaged for a lit, seen, walking target (0092 item 2)
divided by the light term 0.5 + 0.5 × level (0092 item 1); sneaking: unseen
(never) when spot × direction × light is under the target's elusiveness
(0092 item 1's compare), else one band slower (dossier §2, no number);
beyond the observer's `sightM` a noise gives suspicion only, so never engaged
(0092 item 2). Bands: instant (< 1 s), quick (1–3 s), slow (3–10 s), never
(> 10 s or rate 0). Measured: `timeToNotice` from `noticeRate` with the
runtime's inputs (light through `lightFactorOf` on the rows' light table,
loudness = `movementLoudness`, unarmoured, Sneak 25 / Agility 40, 12 m in
the cone, 0092's E1 distance). Surface: every material's factor is 1 in the
rows (blocker), so one column. Elapsed: the row's measure, wall time.
Generator: `lanes/2.10/b-bands-survey.ts` (`npx tsx` from packages/game-core).

Result (measured 2026-10-21, 648 rows, 1.0 s whole, after the fix below):
514 on band, 134 off. Re-measured after the second fix at source:
hearing and scent alone now cap notice at suspicious (`NoticeTerms.engages`
into `stepNotice`, `NOTICE_TUNING.unseenCeiling` 0.99; 0092 item 2), which
put the sound-or-scent rows on band (225 rows read "unseen, capped at
suspicious"). Observers with no sight at all (`sightM` 0: voriplasm,
swamp-leviathan, one more out of hearing at 12 m) engage on their other
senses, or they could never fight; their 24 rows read off against the
"never" column. Fixed at source on the first run: `noticeRate` had
dropped 0092 item 1's compare (spot × direction × light ≥ elusiveness), so
every sight stimulus accumulated, a crouched Sneak-50 player 1.5 m behind a
warden was engaged within a second and the eye never fell while in view;
with the gate the 71 sneaking rows are on band. Re-measured 2026-10-21 (lane 2.10-j3) after the third fix at source: `unseenCeiling` is 0092 item 2's noise 0.5, not 0.99, and past it only sight climbs (`NoticeTerms.sightRate` into `stepNotice`), so a footstep no longer carries a standing walker in the rear arc from heard to engaged in one frame; the generator now steps `stepNotice` instead of `timeToNotice`. 648 rows: 545 on band, 103 off (band edge 79: dim still/walk/run 12 each read instant for quick, lit still 15, walk 14, run 14 read quick for instant; blind observers 24). Nothing is tuned; the offs
left are two classes, each an owner call:

2. Blind observers (24 rows): should a creature with no sight engage on
   hearing and scent (as now), or stay suspicious like everyone else and
   only fight when struck?

1. Band edge (110 rows: dim still 23, dim walk 26, dim run 28, dark run 8,
   dark walk 3 read instant where quick is expected; lit still/walk/run 22
   for short-sighted creatures read quick where instant is expected): the
   rows' light table gives 0.8125 at dim where 0092's formula gives 0.75,
   and spot 30 creatures run slower than the person reference; the seconds
   sit within 0.3 s of a band edge.

| Archetype | Light | Gait | Surface | Expected band | Measured | Elapsed |
|---|---|---|---|---|---|---|
| archer-warden | dark (0) | still | any (all 1) | quick | quick (1.37 s) | 0.584 ms |
| archer-warden | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.051 ms |
| archer-warden | dark (0) | walk | any (all 1) | quick | quick (1.29 s) | 0.290 ms |
| archer-warden | dark (0) | run | any (all 1) | quick | quick (1.25 s) | 0.077 ms |
| archer-warden | dim (0.5) | still | any (all 1) | quick | instant (0.95 s) **off** | 0.059 ms |
| archer-warden | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.020 ms |
| archer-warden | dim (0.5) | walk | any (all 1) | quick | instant (0.91 s) **off** | 0.046 ms |
| archer-warden | dim (0.5) | run | any (all 1) | quick | instant (0.89 s) **off** | 0.043 ms |
| archer-warden | lit (1) | still | any (all 1) | instant | instant (0.82 s) | 0.149 ms |
| archer-warden | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.042 ms |
| archer-warden | lit (1) | walk | any (all 1) | instant | instant (0.79 s) | 0.039 ms |
| archer-warden | lit (1) | run | any (all 1) | instant | instant (0.78 s) | 0.029 ms |
| battleaxe-warden | dark (0) | still | any (all 1) | quick | quick (1.37 s) | 0.045 ms |
| battleaxe-warden | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.006 ms |
| battleaxe-warden | dark (0) | walk | any (all 1) | quick | quick (1.29 s) | 0.039 ms |
| battleaxe-warden | dark (0) | run | any (all 1) | quick | quick (1.25 s) | 0.039 ms |
| battleaxe-warden | dim (0.5) | still | any (all 1) | quick | instant (0.95 s) **off** | 0.032 ms |
| battleaxe-warden | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.009 ms |
| battleaxe-warden | dim (0.5) | walk | any (all 1) | quick | instant (0.91 s) **off** | 0.032 ms |
| battleaxe-warden | dim (0.5) | run | any (all 1) | quick | instant (0.89 s) **off** | 0.029 ms |
| battleaxe-warden | lit (1) | still | any (all 1) | instant | instant (0.82 s) | 0.028 ms |
| battleaxe-warden | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| battleaxe-warden | lit (1) | walk | any (all 1) | instant | instant (0.79 s) | 0.027 ms |
| battleaxe-warden | lit (1) | run | any (all 1) | instant | instant (0.78 s) | 0.028 ms |
| claw-warden | dark (0) | still | any (all 1) | quick | quick (1.37 s) | 0.042 ms |
| claw-warden | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| claw-warden | dark (0) | walk | any (all 1) | quick | quick (1.29 s) | 0.040 ms |
| claw-warden | dark (0) | run | any (all 1) | quick | quick (1.25 s) | 0.038 ms |
| claw-warden | dim (0.5) | still | any (all 1) | quick | instant (0.95 s) **off** | 0.030 ms |
| claw-warden | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| claw-warden | dim (0.5) | walk | any (all 1) | quick | instant (0.91 s) **off** | 0.029 ms |
| claw-warden | dim (0.5) | run | any (all 1) | quick | instant (0.89 s) **off** | 0.029 ms |
| claw-warden | lit (1) | still | any (all 1) | instant | instant (0.82 s) | 0.031 ms |
| claw-warden | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| claw-warden | lit (1) | walk | any (all 1) | instant | instant (0.79 s) | 0.028 ms |
| claw-warden | lit (1) | run | any (all 1) | instant | instant (0.78 s) | 0.029 ms |
| creature.alit | dark (0) | still | any (all 1) | quick | quick (1.51 s) | 0.069 ms |
| creature.alit | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.011 ms |
| creature.alit | dark (0) | walk | any (all 1) | quick | quick (1.47 s) | 2.508 ms |
| creature.alit | dark (0) | run | any (all 1) | quick | quick (1.45 s) | 0.041 ms |
| creature.alit | dim (0.5) | still | any (all 1) | quick | quick (1.10 s) | 0.013 ms |
| creature.alit | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.008 ms |
| creature.alit | dim (0.5) | walk | any (all 1) | quick | quick (1.08 s) | 0.012 ms |
| creature.alit | dim (0.5) | run | any (all 1) | quick | quick (1.06 s) | 0.011 ms |
| creature.alit | lit (1) | still | any (all 1) | instant | instant (0.97 s) | 0.010 ms |
| creature.alit | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.alit | lit (1) | walk | any (all 1) | instant | instant (0.96 s) | 0.014 ms |
| creature.alit | lit (1) | run | any (all 1) | instant | instant (0.94 s) | 0.012 ms |
| creature.bog-blight | dark (0) | still | any (all 1) | quick | quick (1.49 s) | 0.017 ms |
| creature.bog-blight | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.bog-blight | dark (0) | walk | any (all 1) | quick | quick (1.46 s) | 0.015 ms |
| creature.bog-blight | dark (0) | run | any (all 1) | quick | quick (1.44 s) | 0.015 ms |
| creature.bog-blight | dim (0.5) | still | any (all 1) | quick | quick (1.09 s) | 0.014 ms |
| creature.bog-blight | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.bog-blight | dim (0.5) | walk | any (all 1) | quick | quick (1.07 s) | 0.014 ms |
| creature.bog-blight | dim (0.5) | run | any (all 1) | quick | quick (1.06 s) | 0.014 ms |
| creature.bog-blight | lit (1) | still | any (all 1) | instant | instant (0.96 s) | 0.013 ms |
| creature.bog-blight | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.bog-blight | lit (1) | walk | any (all 1) | instant | instant (0.95 s) | 0.011 ms |
| creature.bog-blight | lit (1) | run | any (all 1) | instant | instant (0.94 s) | 0.011 ms |
| creature.bog-dog | dark (0) | still | any (all 1) | quick | quick (1.47 s) | 0.015 ms |
| creature.bog-dog | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.bog-dog | dark (0) | walk | any (all 1) | quick | quick (1.43 s) | 0.016 ms |
| creature.bog-dog | dark (0) | run | any (all 1) | quick | quick (1.40 s) | 0.016 ms |
| creature.bog-dog | dim (0.5) | still | any (all 1) | quick | quick (1.08 s) | 0.014 ms |
| creature.bog-dog | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.bog-dog | dim (0.5) | walk | any (all 1) | quick | quick (1.05 s) | 0.013 ms |
| creature.bog-dog | dim (0.5) | run | any (all 1) | quick | quick (1.03 s) | 0.013 ms |
| creature.bog-dog | lit (1) | still | any (all 1) | instant | instant (0.95 s) | 0.012 ms |
| creature.bog-dog | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.bog-dog | lit (1) | walk | any (all 1) | instant | instant (0.93 s) | 0.012 ms |
| creature.bog-dog | lit (1) | run | any (all 1) | instant | instant (0.92 s) | 0.012 ms |
| creature.crocodile | dark (0) | still | any (all 1) | quick | quick (1.66 s) | 0.018 ms |
| creature.crocodile | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.crocodile | dark (0) | walk | any (all 1) | quick | quick (1.61 s) | 0.017 ms |
| creature.crocodile | dark (0) | run | any (all 1) | quick | quick (1.57 s) | 0.017 ms |
| creature.crocodile | dim (0.5) | still | any (all 1) | quick | quick (1.19 s) | 0.014 ms |
| creature.crocodile | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.crocodile | dim (0.5) | walk | any (all 1) | quick | quick (1.16 s) | 0.014 ms |
| creature.crocodile | dim (0.5) | run | any (all 1) | quick | quick (1.14 s) | 0.015 ms |
| creature.crocodile | lit (1) | still | any (all 1) | instant | quick (1.05 s) **off** | 0.013 ms |
| creature.crocodile | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.crocodile | lit (1) | walk | any (all 1) | instant | quick (1.02 s) **off** | 0.012 ms |
| creature.crocodile | lit (1) | run | any (all 1) | instant | quick (1.00 s) **off** | 0.013 ms |
| creature.crow | dark (0) | still | any (all 1) | quick | quick (1.91 s) | 0.019 ms |
| creature.crow | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.crow | dark (0) | walk | any (all 1) | quick | quick (1.86 s) | 0.018 ms |
| creature.crow | dark (0) | run | any (all 1) | quick | quick (1.82 s) | 0.018 ms |
| creature.crow | dim (0.5) | still | any (all 1) | quick | quick (1.33 s) | 0.016 ms |
| creature.crow | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.crow | dim (0.5) | walk | any (all 1) | quick | quick (1.30 s) | 0.015 ms |
| creature.crow | dim (0.5) | run | any (all 1) | quick | quick (1.28 s) | 0.014 ms |
| creature.crow | lit (1) | still | any (all 1) | instant | quick (1.15 s) **off** | 0.014 ms |
| creature.crow | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.crow | lit (1) | walk | any (all 1) | instant | quick (1.13 s) **off** | 0.014 ms |
| creature.crow | lit (1) | run | any (all 1) | instant | quick (1.12 s) **off** | 0.014 ms |
| creature.death-hopper | dark (0) | still | any (all 1) | quick | quick (1.91 s) | 0.021 ms |
| creature.death-hopper | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.death-hopper | dark (0) | walk | any (all 1) | quick | quick (1.85 s) | 0.018 ms |
| creature.death-hopper | dark (0) | run | any (all 1) | quick | quick (1.80 s) | 0.018 ms |
| creature.death-hopper | dim (0.5) | still | any (all 1) | quick | quick (1.33 s) | 0.015 ms |
| creature.death-hopper | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.death-hopper | dim (0.5) | walk | any (all 1) | quick | quick (1.29 s) | 0.015 ms |
| creature.death-hopper | dim (0.5) | run | any (all 1) | quick | quick (1.27 s) | 0.015 ms |
| creature.death-hopper | lit (1) | still | any (all 1) | instant | quick (1.15 s) **off** | 0.013 ms |
| creature.death-hopper | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.death-hopper | lit (1) | walk | any (all 1) | instant | quick (1.13 s) **off** | 0.013 ms |
| creature.death-hopper | lit (1) | run | any (all 1) | instant | quick (1.11 s) **off** | 0.013 ms |
| creature.dreugh | dark (0) | still | any (all 1) | quick | quick (1.66 s) | 0.018 ms |
| creature.dreugh | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.dreugh | dark (0) | walk | any (all 1) | quick | quick (1.63 s) | 0.048 ms |
| creature.dreugh | dark (0) | run | any (all 1) | quick | quick (1.61 s) | 0.018 ms |
| creature.dreugh | dim (0.5) | still | any (all 1) | quick | quick (1.19 s) | 0.015 ms |
| creature.dreugh | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.dreugh | dim (0.5) | walk | any (all 1) | quick | quick (1.18 s) | 0.014 ms |
| creature.dreugh | dim (0.5) | run | any (all 1) | quick | quick (1.17 s) | 0.013 ms |
| creature.dreugh | lit (1) | still | any (all 1) | instant | quick (1.05 s) **off** | 0.013 ms |
| creature.dreugh | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.dreugh | lit (1) | walk | any (all 1) | instant | quick (1.04 s) **off** | 0.013 ms |
| creature.dreugh | lit (1) | run | any (all 1) | instant | quick (1.03 s) **off** | 0.013 ms |
| creature.feather-serpent | dark (0) | still | any (all 1) | quick | quick (1.47 s) | 0.016 ms |
| creature.feather-serpent | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.feather-serpent | dark (0) | walk | any (all 1) | quick | quick (1.42 s) | 0.015 ms |
| creature.feather-serpent | dark (0) | run | any (all 1) | quick | quick (1.38 s) | 0.015 ms |
| creature.feather-serpent | dim (0.5) | still | any (all 1) | quick | quick (1.08 s) | 0.013 ms |
| creature.feather-serpent | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.feather-serpent | dim (0.5) | walk | any (all 1) | quick | quick (1.04 s) | 0.014 ms |
| creature.feather-serpent | dim (0.5) | run | any (all 1) | quick | quick (1.02 s) | 0.013 ms |
| creature.feather-serpent | lit (1) | still | any (all 1) | instant | instant (0.95 s) | 0.012 ms |
| creature.feather-serpent | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.feather-serpent | lit (1) | walk | any (all 1) | instant | instant (0.92 s) | 0.012 ms |
| creature.feather-serpent | lit (1) | run | any (all 1) | instant | instant (0.90 s) | 0.012 ms |
| creature.fellrunner | dark (0) | still | any (all 1) | quick | quick (1.91 s) | 0.019 ms |
| creature.fellrunner | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.fellrunner | dark (0) | walk | any (all 1) | quick | quick (1.81 s) | 0.019 ms |
| creature.fellrunner | dark (0) | run | any (all 1) | quick | quick (1.75 s) | 0.018 ms |
| creature.fellrunner | dim (0.5) | still | any (all 1) | quick | quick (1.33 s) | 0.015 ms |
| creature.fellrunner | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.fellrunner | dim (0.5) | walk | any (all 1) | quick | quick (1.28 s) | 0.024 ms |
| creature.fellrunner | dim (0.5) | run | any (all 1) | quick | quick (1.24 s) | 0.015 ms |
| creature.fellrunner | lit (1) | still | any (all 1) | instant | quick (1.15 s) **off** | 0.014 ms |
| creature.fellrunner | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.fellrunner | lit (1) | walk | any (all 1) | instant | quick (1.11 s) **off** | 0.014 ms |
| creature.fellrunner | lit (1) | run | any (all 1) | instant | quick (1.08 s) **off** | 0.014 ms |
| creature.fleshfly | dark (0) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.007 ms |
| creature.fleshfly | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.fleshfly | dark (0) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.fleshfly | dark (0) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.fleshfly | dim (0.5) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.fleshfly | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.006 ms |
| creature.fleshfly | dim (0.5) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.fleshfly | dim (0.5) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.fleshfly | lit (1) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.fleshfly | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.fleshfly | lit (1) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.fleshfly | lit (1) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.giant-leech | dark (0) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.giant-leech | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.giant-leech | dark (0) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.giant-leech | dark (0) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.giant-leech | dim (0.5) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.giant-leech | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.giant-leech | dim (0.5) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.giant-leech | dim (0.5) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.giant-leech | lit (1) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.giant-leech | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.giant-leech | lit (1) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.giant-leech | lit (1) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.giant-wasp | dark (0) | still | any (all 1) | quick | quick (1.58 s) | 0.018 ms |
| creature.giant-wasp | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.giant-wasp | dark (0) | walk | any (all 1) | quick | quick (1.54 s) | 0.017 ms |
| creature.giant-wasp | dark (0) | run | any (all 1) | quick | quick (1.51 s) | 0.014 ms |
| creature.giant-wasp | dim (0.5) | still | any (all 1) | quick | quick (1.15 s) | 0.013 ms |
| creature.giant-wasp | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.006 ms |
| creature.giant-wasp | dim (0.5) | walk | any (all 1) | quick | quick (1.12 s) | 0.014 ms |
| creature.giant-wasp | dim (0.5) | run | any (all 1) | quick | quick (1.10 s) | 0.016 ms |
| creature.giant-wasp | lit (1) | still | any (all 1) | instant | quick (1.01 s) **off** | 0.013 ms |
| creature.giant-wasp | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.giant-wasp | lit (1) | walk | any (all 1) | instant | instant (0.99 s) | 0.014 ms |
| creature.giant-wasp | lit (1) | run | any (all 1) | instant | instant (0.97 s) | 0.013 ms |
| creature.guar | dark (0) | still | any (all 1) | quick | quick (1.58 s) | 0.018 ms |
| creature.guar | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.guar | dark (0) | walk | any (all 1) | quick | quick (1.58 s) | 0.018 ms |
| creature.guar | dark (0) | run | any (all 1) | quick | quick (1.58 s) | 0.018 ms |
| creature.guar | dim (0.5) | still | any (all 1) | quick | quick (1.15 s) | 0.015 ms |
| creature.guar | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.guar | dim (0.5) | walk | any (all 1) | quick | quick (1.15 s) | 0.014 ms |
| creature.guar | dim (0.5) | run | any (all 1) | quick | quick (1.15 s) | 0.014 ms |
| creature.guar | lit (1) | still | any (all 1) | instant | quick (1.01 s) **off** | 0.013 ms |
| creature.guar | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.guar | lit (1) | walk | any (all 1) | instant | quick (1.01 s) **off** | 0.013 ms |
| creature.guar | lit (1) | run | any (all 1) | instant | quick (1.01 s) **off** | 0.013 ms |
| creature.hackwing | dark (0) | still | any (all 1) | quick | quick (1.91 s) | 0.026 ms |
| creature.hackwing | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.hackwing | dark (0) | walk | any (all 1) | quick | quick (1.81 s) | 0.019 ms |
| creature.hackwing | dark (0) | run | any (all 1) | quick | quick (1.75 s) | 0.019 ms |
| creature.hackwing | dim (0.5) | still | any (all 1) | quick | quick (1.33 s) | 0.015 ms |
| creature.hackwing | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.hackwing | dim (0.5) | walk | any (all 1) | quick | quick (1.28 s) | 0.015 ms |
| creature.hackwing | dim (0.5) | run | any (all 1) | quick | quick (1.24 s) | 0.015 ms |
| creature.hackwing | lit (1) | still | any (all 1) | instant | quick (1.15 s) **off** | 0.014 ms |
| creature.hackwing | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.hackwing | lit (1) | walk | any (all 1) | instant | quick (1.11 s) **off** | 0.014 ms |
| creature.hackwing | lit (1) | run | any (all 1) | instant | quick (1.08 s) **off** | 0.014 ms |
| creature.haj-mota | dark (0) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.haj-mota | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.haj-mota | dark (0) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.haj-mota | dark (0) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.haj-mota | dim (0.5) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.haj-mota | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.haj-mota | dim (0.5) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.haj-mota | dim (0.5) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.haj-mota | lit (1) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.haj-mota | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.haj-mota | lit (1) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.haj-mota | lit (1) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.haynekhtnamet | dark (0) | still | any (all 1) | quick | quick (1.54 s) | 0.018 ms |
| creature.haynekhtnamet | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.haynekhtnamet | dark (0) | walk | any (all 1) | quick | quick (1.48 s) | 0.016 ms |
| creature.haynekhtnamet | dark (0) | run | any (all 1) | quick | quick (1.44 s) | 0.016 ms |
| creature.haynekhtnamet | dim (0.5) | still | any (all 1) | quick | quick (1.12 s) | 0.014 ms |
| creature.haynekhtnamet | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.haynekhtnamet | dim (0.5) | walk | any (all 1) | quick | quick (1.09 s) | 0.014 ms |
| creature.haynekhtnamet | dim (0.5) | run | any (all 1) | quick | quick (1.06 s) | 0.014 ms |
| creature.haynekhtnamet | lit (1) | still | any (all 1) | instant | instant (0.99 s) | 0.013 ms |
| creature.haynekhtnamet | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.haynekhtnamet | lit (1) | walk | any (all 1) | instant | instant (0.96 s) | 0.012 ms |
| creature.haynekhtnamet | lit (1) | run | any (all 1) | instant | instant (0.94 s) | 0.013 ms |
| creature.hoarvor | dark (0) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.hoarvor | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.hoarvor | dark (0) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.hoarvor | dark (0) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.hoarvor | dim (0.5) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.hoarvor | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.hoarvor | dim (0.5) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.hoarvor | dim (0.5) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.hoarvor | lit (1) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.hoarvor | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.hoarvor | lit (1) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.hoarvor | lit (1) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.jassa-red-slug | dark (0) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.jassa-red-slug | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.jassa-red-slug | dark (0) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.jassa-red-slug | dark (0) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.jassa-red-slug | dim (0.5) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.jassa-red-slug | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.jassa-red-slug | dim (0.5) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.jassa-red-slug | dim (0.5) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.jassa-red-slug | lit (1) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.jassa-red-slug | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.jassa-red-slug | lit (1) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.jassa-red-slug | lit (1) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.kaj-thux | dark (0) | still | any (all 1) | quick | quick (1.49 s) | 0.016 ms |
| creature.kaj-thux | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.kaj-thux | dark (0) | walk | any (all 1) | quick | quick (1.46 s) | 0.015 ms |
| creature.kaj-thux | dark (0) | run | any (all 1) | quick | quick (1.43 s) | 0.014 ms |
| creature.kaj-thux | dim (0.5) | still | any (all 1) | quick | quick (1.09 s) | 0.013 ms |
| creature.kaj-thux | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.kaj-thux | dim (0.5) | walk | any (all 1) | quick | quick (1.07 s) | 0.014 ms |
| creature.kaj-thux | dim (0.5) | run | any (all 1) | quick | quick (1.05 s) | 0.014 ms |
| creature.kaj-thux | lit (1) | still | any (all 1) | instant | instant (0.96 s) | 0.013 ms |
| creature.kaj-thux | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.kaj-thux | lit (1) | walk | any (all 1) | instant | instant (0.95 s) | 0.029 ms |
| creature.kaj-thux | lit (1) | run | any (all 1) | instant | instant (0.93 s) | 0.012 ms |
| creature.kotu-gava | dark (0) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.kotu-gava | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.kotu-gava | dark (0) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.kotu-gava | dark (0) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.kotu-gava | dim (0.5) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.kotu-gava | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.kotu-gava | dim (0.5) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.kotu-gava | dim (0.5) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.kotu-gava | lit (1) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.kotu-gava | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.kotu-gava | lit (1) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.kotu-gava | lit (1) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.lamia | dark (0) | still | any (all 1) | quick | quick (1.66 s) | 0.017 ms |
| creature.lamia | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.006 ms |
| creature.lamia | dark (0) | walk | any (all 1) | quick | quick (1.60 s) | 0.015 ms |
| creature.lamia | dark (0) | run | any (all 1) | quick | quick (1.56 s) | 0.015 ms |
| creature.lamia | dim (0.5) | still | any (all 1) | quick | quick (1.19 s) | 0.013 ms |
| creature.lamia | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.lamia | dim (0.5) | walk | any (all 1) | quick | quick (1.16 s) | 0.012 ms |
| creature.lamia | dim (0.5) | run | any (all 1) | quick | quick (1.13 s) | 0.012 ms |
| creature.lamia | lit (1) | still | any (all 1) | instant | quick (1.05 s) **off** | 0.012 ms |
| creature.lamia | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.lamia | lit (1) | walk | any (all 1) | instant | quick (1.02 s) **off** | 0.011 ms |
| creature.lamia | lit (1) | run | any (all 1) | instant | quick (1.00 s) **off** | 0.011 ms |
| creature.lizard-steed | dark (0) | still | any (all 1) | quick | quick (1.54 s) | 0.014 ms |
| creature.lizard-steed | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.lizard-steed | dark (0) | walk | any (all 1) | quick | quick (1.52 s) | 0.015 ms |
| creature.lizard-steed | dark (0) | run | any (all 1) | quick | quick (1.51 s) | 0.018 ms |
| creature.lizard-steed | dim (0.5) | still | any (all 1) | quick | quick (1.12 s) | 0.012 ms |
| creature.lizard-steed | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.lizard-steed | dim (0.5) | walk | any (all 1) | quick | quick (1.11 s) | 0.011 ms |
| creature.lizard-steed | dim (0.5) | run | any (all 1) | quick | quick (1.10 s) | 0.012 ms |
| creature.lizard-steed | lit (1) | still | any (all 1) | instant | instant (0.99 s) | 0.012 ms |
| creature.lizard-steed | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.lizard-steed | lit (1) | walk | any (all 1) | instant | instant (0.98 s) | 0.013 ms |
| creature.lizard-steed | lit (1) | run | any (all 1) | instant | instant (0.98 s) | 0.011 ms |
| creature.marsh-giant | dark (0) | still | any (all 1) | quick | quick (1.54 s) | 0.015 ms |
| creature.marsh-giant | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.marsh-giant | dark (0) | walk | any (all 1) | quick | quick (1.48 s) | 0.016 ms |
| creature.marsh-giant | dark (0) | run | any (all 1) | quick | quick (1.44 s) | 0.015 ms |
| creature.marsh-giant | dim (0.5) | still | any (all 1) | quick | quick (1.12 s) | 0.012 ms |
| creature.marsh-giant | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.marsh-giant | dim (0.5) | walk | any (all 1) | quick | quick (1.09 s) | 0.013 ms |
| creature.marsh-giant | dim (0.5) | run | any (all 1) | quick | quick (1.06 s) | 0.013 ms |
| creature.marsh-giant | lit (1) | still | any (all 1) | instant | instant (0.99 s) | 0.013 ms |
| creature.marsh-giant | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.marsh-giant | lit (1) | walk | any (all 1) | instant | instant (0.96 s) | 0.014 ms |
| creature.marsh-giant | lit (1) | run | any (all 1) | instant | instant (0.94 s) | 0.013 ms |
| creature.marsh-rat | dark (0) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.marsh-rat | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.marsh-rat | dark (0) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.marsh-rat | dark (0) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.marsh-rat | dim (0.5) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.marsh-rat | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.marsh-rat | dim (0.5) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.marsh-rat | dim (0.5) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.marsh-rat | lit (1) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.marsh-rat | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.marsh-rat | lit (1) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.marsh-rat | lit (1) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.medusa | dark (0) | still | any (all 1) | quick | quick (1.66 s) | 0.018 ms |
| creature.medusa | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.medusa | dark (0) | walk | any (all 1) | quick | quick (1.61 s) | 0.018 ms |
| creature.medusa | dark (0) | run | any (all 1) | quick | quick (1.58 s) | 0.018 ms |
| creature.medusa | dim (0.5) | still | any (all 1) | quick | quick (1.19 s) | 0.014 ms |
| creature.medusa | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.medusa | dim (0.5) | walk | any (all 1) | quick | quick (1.17 s) | 0.014 ms |
| creature.medusa | dim (0.5) | run | any (all 1) | quick | quick (1.15 s) | 0.014 ms |
| creature.medusa | lit (1) | still | any (all 1) | instant | quick (1.05 s) **off** | 0.013 ms |
| creature.medusa | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.medusa | lit (1) | walk | any (all 1) | instant | quick (1.03 s) **off** | 0.013 ms |
| creature.medusa | lit (1) | run | any (all 1) | instant | quick (1.01 s) **off** | 1.992 ms |
| creature.miregaunt | dark (0) | still | any (all 1) | quick | quick (1.91 s) | 0.036 ms |
| creature.miregaunt | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.007 ms |
| creature.miregaunt | dark (0) | walk | any (all 1) | quick | quick (1.79 s) | 0.020 ms |
| creature.miregaunt | dark (0) | run | any (all 1) | quick | quick (1.71 s) | 0.019 ms |
| creature.miregaunt | dim (0.5) | still | any (all 1) | quick | quick (1.33 s) | 0.017 ms |
| creature.miregaunt | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.miregaunt | dim (0.5) | walk | any (all 1) | quick | quick (1.26 s) | 0.015 ms |
| creature.miregaunt | dim (0.5) | run | any (all 1) | quick | quick (1.22 s) | 0.014 ms |
| creature.miregaunt | lit (1) | still | any (all 1) | instant | quick (1.15 s) **off** | 0.014 ms |
| creature.miregaunt | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.miregaunt | lit (1) | walk | any (all 1) | instant | quick (1.10 s) **off** | 0.033 ms |
| creature.miregaunt | lit (1) | run | any (all 1) | instant | quick (1.07 s) **off** | 0.015 ms |
| creature.moon-adder | dark (0) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.006 ms |
| creature.moon-adder | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.moon-adder | dark (0) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.moon-adder | dark (0) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.moon-adder | dim (0.5) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.moon-adder | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.moon-adder | dim (0.5) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.moon-adder | dim (0.5) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.moon-adder | lit (1) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.moon-adder | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.moon-adder | lit (1) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.moon-adder | lit (1) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.mouth-plover | dark (0) | still | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.mouth-plover | dark (0) | sneak | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.mouth-plover | dark (0) | walk | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.mouth-plover | dark (0) | run | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.mouth-plover | dim (0.5) | still | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.mouth-plover | dim (0.5) | sneak | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.mouth-plover | dim (0.5) | walk | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.mouth-plover | dim (0.5) | run | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.mouth-plover | lit (1) | still | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.mouth-plover | lit (1) | sneak | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.mouth-plover | lit (1) | walk | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.mouth-plover | lit (1) | run | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.osheeja-gar | dark (0) | still | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.osheeja-gar | dark (0) | sneak | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.osheeja-gar | dark (0) | walk | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.osheeja-gar | dark (0) | run | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.osheeja-gar | dim (0.5) | still | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.osheeja-gar | dim (0.5) | sneak | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.osheeja-gar | dim (0.5) | walk | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.osheeja-gar | dim (0.5) | run | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.osheeja-gar | lit (1) | still | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.osheeja-gar | lit (1) | sneak | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.osheeja-gar | lit (1) | walk | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.osheeja-gar | lit (1) | run | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.ripper-eel | dark (0) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.ripper-eel | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.ripper-eel | dark (0) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.ripper-eel | dark (0) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.ripper-eel | dim (0.5) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.ripper-eel | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.ripper-eel | dim (0.5) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.ripper-eel | dim (0.5) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.ripper-eel | lit (1) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.ripper-eel | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.ripper-eel | lit (1) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.ripper-eel | lit (1) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.rootworm | dark (0) | still | any (all 1) | never | never (rate 0) | 0.365 ms |
| creature.rootworm | dark (0) | sneak | any (all 1) | never | never (rate 0) | 0.338 ms |
| creature.rootworm | dark (0) | walk | any (all 1) | never | never (rate 0) | 2.672 ms |
| creature.rootworm | dark (0) | run | any (all 1) | never | never (rate 0) | 0.116 ms |
| creature.rootworm | dim (0.5) | still | any (all 1) | never | never (rate 0) | 0.099 ms |
| creature.rootworm | dim (0.5) | sneak | any (all 1) | never | never (rate 0) | 0.119 ms |
| creature.rootworm | dim (0.5) | walk | any (all 1) | never | never (rate 0) | 0.096 ms |
| creature.rootworm | dim (0.5) | run | any (all 1) | never | never (rate 0) | 0.091 ms |
| creature.rootworm | lit (1) | still | any (all 1) | never | never (rate 0) | 0.096 ms |
| creature.rootworm | lit (1) | sneak | any (all 1) | never | never (rate 0) | 0.096 ms |
| creature.rootworm | lit (1) | walk | any (all 1) | never | never (rate 0) | 0.095 ms |
| creature.rootworm | lit (1) | run | any (all 1) | never | never (rate 0) | 0.092 ms |
| creature.sea-drake | dark (0) | still | any (all 1) | quick | quick (1.91 s) | 0.021 ms |
| creature.sea-drake | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.sea-drake | dark (0) | walk | any (all 1) | quick | quick (1.75 s) | 0.020 ms |
| creature.sea-drake | dark (0) | run | any (all 1) | quick | quick (1.65 s) | 0.018 ms |
| creature.sea-drake | dim (0.5) | still | any (all 1) | quick | quick (1.33 s) | 0.015 ms |
| creature.sea-drake | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.sea-drake | dim (0.5) | walk | any (all 1) | quick | quick (1.24 s) | 0.015 ms |
| creature.sea-drake | dim (0.5) | run | any (all 1) | quick | quick (1.19 s) | 0.015 ms |
| creature.sea-drake | lit (1) | still | any (all 1) | instant | quick (1.15 s) **off** | 0.014 ms |
| creature.sea-drake | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.sea-drake | lit (1) | walk | any (all 1) | instant | quick (1.09 s) **off** | 0.014 ms |
| creature.sea-drake | lit (1) | run | any (all 1) | instant | quick (1.04 s) **off** | 0.013 ms |
| creature.shine | dark (0) | still | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.shine | dark (0) | sneak | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.shine | dark (0) | walk | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.shine | dark (0) | run | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.shine | dim (0.5) | still | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.shine | dim (0.5) | sneak | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.shine | dim (0.5) | walk | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.shine | dim (0.5) | run | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.shine | lit (1) | still | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.shine | lit (1) | sneak | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.shine | lit (1) | walk | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.shine | lit (1) | run | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.slaughterfish | dark (0) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.slaughterfish | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.slaughterfish | dark (0) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.slaughterfish | dark (0) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.slaughterfish | dim (0.5) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.slaughterfish | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.slaughterfish | dim (0.5) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.slaughterfish | dim (0.5) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.slaughterfish | lit (1) | still | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.slaughterfish | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.slaughterfish | lit (1) | walk | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.slaughterfish | lit (1) | run | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.swamp-jelly | dark (0) | still | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.swamp-jelly | dark (0) | sneak | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.swamp-jelly | dark (0) | walk | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.swamp-jelly | dark (0) | run | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.swamp-jelly | dim (0.5) | still | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.swamp-jelly | dim (0.5) | sneak | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.swamp-jelly | dim (0.5) | walk | any (all 1) | never | never (rate 0) | 0.025 ms |
| creature.swamp-jelly | dim (0.5) | run | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.swamp-jelly | lit (1) | still | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.swamp-jelly | lit (1) | sneak | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.swamp-jelly | lit (1) | walk | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.swamp-jelly | lit (1) | run | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.swamp-leviathan | dark (0) | still | any (all 1) | never | quick (2.94 s) **off** | 0.028 ms |
| creature.swamp-leviathan | dark (0) | sneak | any (all 1) | never | slow (4.36 s) **off** | 0.039 ms |
| creature.swamp-leviathan | dark (0) | walk | any (all 1) | never | quick (2.23 s) **off** | 0.023 ms |
| creature.swamp-leviathan | dark (0) | run | any (all 1) | never | quick (1.87 s) **off** | 0.022 ms |
| creature.swamp-leviathan | dim (0.5) | still | any (all 1) | never | quick (2.94 s) **off** | 0.028 ms |
| creature.swamp-leviathan | dim (0.5) | sneak | any (all 1) | never | slow (4.36 s) **off** | 0.040 ms |
| creature.swamp-leviathan | dim (0.5) | walk | any (all 1) | never | quick (2.23 s) **off** | 0.022 ms |
| creature.swamp-leviathan | dim (0.5) | run | any (all 1) | never | quick (1.87 s) **off** | 0.019 ms |
| creature.swamp-leviathan | lit (1) | still | any (all 1) | never | quick (2.94 s) **off** | 0.028 ms |
| creature.swamp-leviathan | lit (1) | sneak | any (all 1) | never | slow (4.36 s) **off** | 0.038 ms |
| creature.swamp-leviathan | lit (1) | walk | any (all 1) | never | quick (2.23 s) **off** | 0.022 ms |
| creature.swamp-leviathan | lit (1) | run | any (all 1) | never | quick (1.87 s) **off** | 0.019 ms |
| creature.torchbug | dark (0) | still | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.torchbug | dark (0) | sneak | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.torchbug | dark (0) | walk | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.torchbug | dark (0) | run | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.torchbug | dim (0.5) | still | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.torchbug | dim (0.5) | sneak | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.torchbug | dim (0.5) | walk | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.torchbug | dim (0.5) | run | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.torchbug | lit (1) | still | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.torchbug | lit (1) | sneak | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.torchbug | lit (1) | walk | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.torchbug | lit (1) | run | any (all 1) | never | never (rate 0) | 0.004 ms |
| creature.voriplasm | dark (0) | still | any (all 1) | never | slow (5.35 s) **off** | 0.047 ms |
| creature.voriplasm | dark (0) | sneak | any (all 1) | never | slow (8.45 s) **off** | 0.071 ms |
| creature.voriplasm | dark (0) | walk | any (all 1) | never | slow (5.35 s) **off** | 0.046 ms |
| creature.voriplasm | dark (0) | run | any (all 1) | never | slow (5.35 s) **off** | 0.046 ms |
| creature.voriplasm | dim (0.5) | still | any (all 1) | never | slow (5.35 s) **off** | 0.046 ms |
| creature.voriplasm | dim (0.5) | sneak | any (all 1) | never | slow (8.45 s) **off** | 0.071 ms |
| creature.voriplasm | dim (0.5) | walk | any (all 1) | never | slow (5.35 s) **off** | 0.046 ms |
| creature.voriplasm | dim (0.5) | run | any (all 1) | never | slow (5.35 s) **off** | 0.047 ms |
| creature.voriplasm | lit (1) | still | any (all 1) | never | slow (5.35 s) **off** | 0.046 ms |
| creature.voriplasm | lit (1) | sneak | any (all 1) | never | slow (8.45 s) **off** | 0.086 ms |
| creature.voriplasm | lit (1) | walk | any (all 1) | never | slow (5.35 s) **off** | 0.039 ms |
| creature.voriplasm | lit (1) | run | any (all 1) | never | slow (5.35 s) **off** | 0.046 ms |
| creature.wamasu | dark (0) | still | any (all 1) | quick | quick (1.54 s) | 0.017 ms |
| creature.wamasu | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.wamasu | dark (0) | walk | any (all 1) | quick | quick (1.49 s) | 0.017 ms |
| creature.wamasu | dark (0) | run | any (all 1) | quick | quick (1.45 s) | 0.017 ms |
| creature.wamasu | dim (0.5) | still | any (all 1) | quick | quick (1.12 s) | 0.014 ms |
| creature.wamasu | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.wamasu | dim (0.5) | walk | any (all 1) | quick | quick (1.09 s) | 0.014 ms |
| creature.wamasu | dim (0.5) | run | any (all 1) | quick | quick (1.07 s) | 0.014 ms |
| creature.wamasu | lit (1) | still | any (all 1) | instant | instant (0.99 s) | 0.013 ms |
| creature.wamasu | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.wamasu | lit (1) | walk | any (all 1) | instant | instant (0.96 s) | 0.012 ms |
| creature.wamasu | lit (1) | run | any (all 1) | instant | instant (0.95 s) | 0.013 ms |
| creature.wisp | dark (0) | still | any (all 1) | quick | quick (1.91 s) | 0.019 ms |
| creature.wisp | dark (0) | sneak | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.wisp | dark (0) | walk | any (all 1) | quick | quick (1.91 s) | 0.021 ms |
| creature.wisp | dark (0) | run | any (all 1) | quick | quick (1.91 s) | 0.019 ms |
| creature.wisp | dim (0.5) | still | any (all 1) | quick | quick (1.33 s) | 0.015 ms |
| creature.wisp | dim (0.5) | sneak | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.wisp | dim (0.5) | walk | any (all 1) | quick | quick (1.33 s) | 0.017 ms |
| creature.wisp | dim (0.5) | run | any (all 1) | quick | quick (1.33 s) | 0.015 ms |
| creature.wisp | lit (1) | still | any (all 1) | instant | quick (1.15 s) **off** | 0.014 ms |
| creature.wisp | lit (1) | sneak | any (all 1) | never | never (rate 0) | 0.005 ms |
| creature.wisp | lit (1) | walk | any (all 1) | instant | quick (1.15 s) **off** | 0.013 ms |
| creature.wisp | lit (1) | run | any (all 1) | instant | quick (1.15 s) **off** | 0.014 ms |
| creature.wispmother | dark (0) | still | any (all 1) | quick | quick (1.91 s) | 0.019 ms |
| creature.wispmother | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| creature.wispmother | dark (0) | walk | any (all 1) | quick | quick (1.81 s) | 0.019 ms |
| creature.wispmother | dark (0) | run | any (all 1) | quick | quick (1.75 s) | 0.018 ms |
| creature.wispmother | dim (0.5) | still | any (all 1) | quick | quick (1.33 s) | 0.015 ms |
| creature.wispmother | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.wispmother | dim (0.5) | walk | any (all 1) | quick | quick (1.28 s) | 0.015 ms |
| creature.wispmother | dim (0.5) | run | any (all 1) | quick | quick (1.24 s) | 0.015 ms |
| creature.wispmother | lit (1) | still | any (all 1) | instant | quick (1.15 s) **off** | 0.014 ms |
| creature.wispmother | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.wispmother | lit (1) | walk | any (all 1) | instant | quick (1.11 s) **off** | 0.014 ms |
| creature.wispmother | lit (1) | run | any (all 1) | instant | quick (1.08 s) **off** | 0.014 ms |
| creature.xal-krona | dark (0) | still | any (all 1) | quick | quick (1.66 s) | 0.018 ms |
| creature.xal-krona | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.xal-krona | dark (0) | walk | any (all 1) | quick | quick (1.61 s) | 0.017 ms |
| creature.xal-krona | dark (0) | run | any (all 1) | quick | quick (1.57 s) | 0.017 ms |
| creature.xal-krona | dim (0.5) | still | any (all 1) | quick | quick (1.19 s) | 0.015 ms |
| creature.xal-krona | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.xal-krona | dim (0.5) | walk | any (all 1) | quick | quick (1.16 s) | 0.014 ms |
| creature.xal-krona | dim (0.5) | run | any (all 1) | quick | quick (1.14 s) | 0.014 ms |
| creature.xal-krona | lit (1) | still | any (all 1) | instant | quick (1.05 s) **off** | 0.013 ms |
| creature.xal-krona | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| creature.xal-krona | lit (1) | walk | any (all 1) | instant | quick (1.02 s) **off** | 0.013 ms |
| creature.xal-krona | lit (1) | run | any (all 1) | instant | quick (1.00 s) **off** | 0.013 ms |
| dagger-warden | dark (0) | still | any (all 1) | quick | quick (1.37 s) | 0.013 ms |
| dagger-warden | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| dagger-warden | dark (0) | walk | any (all 1) | quick | quick (1.29 s) | 0.013 ms |
| dagger-warden | dark (0) | run | any (all 1) | quick | quick (1.25 s) | 0.013 ms |
| dagger-warden | dim (0.5) | still | any (all 1) | quick | instant (0.95 s) **off** | 0.011 ms |
| dagger-warden | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| dagger-warden | dim (0.5) | walk | any (all 1) | quick | instant (0.91 s) **off** | 0.010 ms |
| dagger-warden | dim (0.5) | run | any (all 1) | quick | instant (0.89 s) **off** | 0.011 ms |
| dagger-warden | lit (1) | still | any (all 1) | instant | instant (0.82 s) | 0.010 ms |
| dagger-warden | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| dagger-warden | lit (1) | walk | any (all 1) | instant | instant (0.79 s) | 0.011 ms |
| dagger-warden | lit (1) | run | any (all 1) | instant | instant (0.78 s) | 0.011 ms |
| greatsword-warden | dark (0) | still | any (all 1) | quick | quick (1.37 s) | 0.033 ms |
| greatsword-warden | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| greatsword-warden | dark (0) | walk | any (all 1) | quick | quick (1.29 s) | 0.016 ms |
| greatsword-warden | dark (0) | run | any (all 1) | quick | quick (1.25 s) | 0.015 ms |
| greatsword-warden | dim (0.5) | still | any (all 1) | quick | instant (0.95 s) **off** | 0.013 ms |
| greatsword-warden | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| greatsword-warden | dim (0.5) | walk | any (all 1) | quick | instant (0.91 s) **off** | 0.012 ms |
| greatsword-warden | dim (0.5) | run | any (all 1) | quick | instant (0.89 s) **off** | 0.013 ms |
| greatsword-warden | lit (1) | still | any (all 1) | instant | instant (0.82 s) | 0.012 ms |
| greatsword-warden | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| greatsword-warden | lit (1) | walk | any (all 1) | instant | instant (0.79 s) | 0.012 ms |
| greatsword-warden | lit (1) | run | any (all 1) | instant | instant (0.78 s) | 0.011 ms |
| halberd-warden | dark (0) | still | any (all 1) | quick | quick (1.37 s) | 0.015 ms |
| halberd-warden | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| halberd-warden | dark (0) | walk | any (all 1) | quick | quick (1.29 s) | 0.015 ms |
| halberd-warden | dark (0) | run | any (all 1) | quick | quick (1.25 s) | 0.014 ms |
| halberd-warden | dim (0.5) | still | any (all 1) | quick | instant (0.95 s) **off** | 0.012 ms |
| halberd-warden | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| halberd-warden | dim (0.5) | walk | any (all 1) | quick | instant (0.91 s) **off** | 0.012 ms |
| halberd-warden | dim (0.5) | run | any (all 1) | quick | instant (0.89 s) **off** | 0.011 ms |
| halberd-warden | lit (1) | still | any (all 1) | instant | instant (0.82 s) | 0.012 ms |
| halberd-warden | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| halberd-warden | lit (1) | walk | any (all 1) | instant | instant (0.79 s) | 0.011 ms |
| halberd-warden | lit (1) | run | any (all 1) | instant | instant (0.78 s) | 0.012 ms |
| hollow-warden | dark (0) | still | any (all 1) | quick | quick (1.37 s) | 0.016 ms |
| hollow-warden | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| hollow-warden | dark (0) | walk | any (all 1) | quick | quick (1.29 s) | 0.015 ms |
| hollow-warden | dark (0) | run | any (all 1) | quick | quick (1.25 s) | 0.015 ms |
| hollow-warden | dim (0.5) | still | any (all 1) | quick | instant (0.95 s) **off** | 0.013 ms |
| hollow-warden | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| hollow-warden | dim (0.5) | walk | any (all 1) | quick | instant (0.91 s) **off** | 0.013 ms |
| hollow-warden | dim (0.5) | run | any (all 1) | quick | instant (0.89 s) **off** | 0.012 ms |
| hollow-warden | lit (1) | still | any (all 1) | instant | instant (0.82 s) | 0.012 ms |
| hollow-warden | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| hollow-warden | lit (1) | walk | any (all 1) | instant | instant (0.79 s) | 0.012 ms |
| hollow-warden | lit (1) | run | any (all 1) | instant | instant (0.78 s) | 0.011 ms |
| person | dark (0) | still | any (all 1) | quick | quick (1.37 s) | 0.015 ms |
| person | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| person | dark (0) | walk | any (all 1) | quick | quick (1.29 s) | 0.015 ms |
| person | dark (0) | run | any (all 1) | quick | quick (1.25 s) | 0.015 ms |
| person | dim (0.5) | still | any (all 1) | quick | instant (0.95 s) **off** | 0.012 ms |
| person | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| person | dim (0.5) | walk | any (all 1) | quick | instant (0.91 s) **off** | 0.012 ms |
| person | dim (0.5) | run | any (all 1) | quick | instant (0.89 s) **off** | 0.012 ms |
| person | lit (1) | still | any (all 1) | instant | instant (0.82 s) | 0.012 ms |
| person | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| person | lit (1) | walk | any (all 1) | instant | instant (0.79 s) | 0.012 ms |
| person | lit (1) | run | any (all 1) | instant | instant (0.78 s) | 0.011 ms |
| pike-warden | dark (0) | still | any (all 1) | quick | quick (1.37 s) | 0.015 ms |
| pike-warden | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.004 ms |
| pike-warden | dark (0) | walk | any (all 1) | quick | quick (1.29 s) | 0.016 ms |
| pike-warden | dark (0) | run | any (all 1) | quick | quick (1.25 s) | 0.023 ms |
| pike-warden | dim (0.5) | still | any (all 1) | quick | instant (0.95 s) **off** | 0.014 ms |
| pike-warden | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| pike-warden | dim (0.5) | walk | any (all 1) | quick | instant (0.91 s) **off** | 0.012 ms |
| pike-warden | dim (0.5) | run | any (all 1) | quick | instant (0.89 s) **off** | 0.013 ms |
| pike-warden | lit (1) | still | any (all 1) | instant | instant (0.82 s) | 0.011 ms |
| pike-warden | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| pike-warden | lit (1) | walk | any (all 1) | instant | instant (0.79 s) | 0.010 ms |
| pike-warden | lit (1) | run | any (all 1) | instant | instant (0.78 s) | 0.009 ms |
| rapier-warden | dark (0) | still | any (all 1) | quick | quick (1.37 s) | 0.014 ms |
| rapier-warden | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| rapier-warden | dark (0) | walk | any (all 1) | quick | quick (1.29 s) | 0.014 ms |
| rapier-warden | dark (0) | run | any (all 1) | quick | quick (1.25 s) | 0.014 ms |
| rapier-warden | dim (0.5) | still | any (all 1) | quick | instant (0.95 s) **off** | 0.014 ms |
| rapier-warden | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| rapier-warden | dim (0.5) | walk | any (all 1) | quick | instant (0.91 s) **off** | 0.013 ms |
| rapier-warden | dim (0.5) | run | any (all 1) | quick | instant (0.89 s) **off** | 0.012 ms |
| rapier-warden | lit (1) | still | any (all 1) | instant | instant (0.82 s) | 0.012 ms |
| rapier-warden | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| rapier-warden | lit (1) | walk | any (all 1) | instant | instant (0.79 s) | 0.012 ms |
| rapier-warden | lit (1) | run | any (all 1) | instant | instant (0.78 s) | 0.012 ms |
| shield-warden | dark (0) | still | any (all 1) | quick | quick (1.37 s) | 0.016 ms |
| shield-warden | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| shield-warden | dark (0) | walk | any (all 1) | quick | quick (1.29 s) | 0.015 ms |
| shield-warden | dark (0) | run | any (all 1) | quick | quick (1.25 s) | 0.016 ms |
| shield-warden | dim (0.5) | still | any (all 1) | quick | instant (0.95 s) **off** | 0.013 ms |
| shield-warden | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| shield-warden | dim (0.5) | walk | any (all 1) | quick | instant (0.91 s) **off** | 0.013 ms |
| shield-warden | dim (0.5) | run | any (all 1) | quick | instant (0.89 s) **off** | 0.013 ms |
| shield-warden | lit (1) | still | any (all 1) | instant | instant (0.82 s) | 0.012 ms |
| shield-warden | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| shield-warden | lit (1) | walk | any (all 1) | instant | instant (0.79 s) | 0.012 ms |
| shield-warden | lit (1) | run | any (all 1) | instant | instant (0.78 s) | 0.012 ms |
| warhammer-warden | dark (0) | still | any (all 1) | quick | quick (1.37 s) | 0.016 ms |
| warhammer-warden | dark (0) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| warhammer-warden | dark (0) | walk | any (all 1) | quick | quick (1.29 s) | 0.016 ms |
| warhammer-warden | dark (0) | run | any (all 1) | quick | quick (1.25 s) | 0.015 ms |
| warhammer-warden | dim (0.5) | still | any (all 1) | quick | instant (0.95 s) **off** | 0.014 ms |
| warhammer-warden | dim (0.5) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| warhammer-warden | dim (0.5) | walk | any (all 1) | quick | instant (0.91 s) **off** | 0.013 ms |
| warhammer-warden | dim (0.5) | run | any (all 1) | quick | instant (0.89 s) **off** | 0.013 ms |
| warhammer-warden | lit (1) | still | any (all 1) | instant | instant (0.82 s) | 0.012 ms |
| warhammer-warden | lit (1) | sneak | any (all 1) | never | never (unseen, capped at suspicious) | 0.005 ms |
| warhammer-warden | lit (1) | walk | any (all 1) | instant | instant (0.79 s) | 0.012 ms |
| warhammer-warden | lit (1) | run | any (all 1) | instant | instant (0.78 s) | 0.012 ms |
