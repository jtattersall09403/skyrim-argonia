# Lane 1.1-core-rules: the skse/core rule modules (report)

Dated 2026-10-29. This lane built, ahead of Part 0's close, the pure C++ rules that native map §6.1 leaves to
`skse/core`. Route 5, test level L2, no game. Commits: `6236a8a` (rows, generator, headers, co-save field types),
`717ac31` (modules and tests), and the commit with this report. The schema block went in earlier with the db-review
lane's `9217521`, which committed `world/schema.sql` from the live tree while this lane was working. The block is
unchanged.

## What exists

| Module | Covers | Test (ctest) |
|---|---|---|
| `curve` | score, k, band, the out-of-combat fatigue term (76 §116, §117.3) | `core.curve` |
| `sheet` | Attributes, Skills, Class, Sheet, Effective; `derive` gives health, stamina, magicka, carry, both regens, walk, sprint, swim, jump, safe fall, breath, burden tier, climb speed and drain, base poise (76 §117–§122) | `core.sheet` |
| `effects` | StatEffect stack: 7 ops over attributes, skills and 21 stat fields (pool, resist, factor, per-Int, flag); `check`, `apply`, `expire` (76 §127) | `core.effects` |
| `carriers` | P1 per hand: damage position, Strength term (none for bows and hand-to-hand), stamina multiplier (band × burden × soft requirement), wear; armour rating per armour skill, Unarmored, block stability and guard; `mitigation` | `core.carriers` |
| `progression` | rank cost, use values, worthiness for every §120.1 use, vastei, the ranks-per-level counter with 1 : 3 credit, the maxed-skill rule, the per-rest Athletics cap, trainers and books (no vastei), the trainer cap; the `STAT` family payload | `core.progression` |
| `sitting` | cost, open, buy (cap 5 per attribute, purchase cap, too dear), close (vastei carries) | `core.sitting` |
| `rest` | can_rest (combat, hunted, dungeon, not calm, settlement needs a bed); on_rest (bed tier, rested entry, wake point, save, respawn, sitting); xp_multiplier | `core.rest` |
| `death` | one pile, replaced by a second death; take within 2 m ground distance in the same cell; the `DETH` payload | `core.death` |
| `respawn` | to_reset over `onRest`, `never`, `untilCleared` and a cleared set | `core.respawn` |
| `conditions` | typed tree over all 62 predicates plus all/any/not; `check` with the path of the bad node; three-valued `evaluate` (an unanswered fact is unknown, never false); a pure `Facts` interface; `mirrors` for P2 | `core.conditions` |
| `disposition` | base (authored + 0.5 × (Per − 50) + priors), bands < 30, 30–69, ≥ 70, clamped apply; the `DISP` payload | `core.disposition` |
| `journal` | append (idempotent; nothing after an end), index (status, most recent first); the `JRNL` payload | `core.journal` |
| `items` | wear by kind (hit, struck, use, burn), usable, armour effectiveness with its floor, repair stroke and ceiling; the `ITEM` payload | `core.items` |
| `families` | Family {id, version, migrations, save, load, reset}; the sparse migration table; Registry (duplicate refused, as S10a asks); readable refusals with reset; reset_all | `core.families` |

`topics` was skipped, as briefed: its route is 1.3 §b's first step.

## Acceptance, measured

- **Every listed module exists with tests:** 14 modules, 15 core test executables (the co-save contract included)
  plus `bridge.protocol`.
- **`skse/check.sh` passes on Linux:** `100% tests passed out of 16`, 9.1 s wall, peak RSS 209 MB. The no-CMake
  fallback printed `core: 15 test executables passed`.
- **The generated headers are current, and the gate fails on a stale table:** `check.sh` runs `core_tables
  --check` first. Shown once: `k_exponent` was edited 1.6 → 1.7 in `world/db/core_constant.jsonl` without
  regenerating. `check.sh` exited 1 with `skse/core/generated is stale` and the one-line diff. The row was then
  restored and the gate went green again. The pytest `test_a_changed_row_makes_them_stale` holds the same proof.
- **Failing on purpose, once per module group:** one expected value was broken in each of `test_sheet` (the
  sheet-side group), `test_progression` (progression, sitting, rest, death, respawn), `test_conditions`
  (conditions, disposition, journal, items) and `test_families`. ctest reported `75% tests passed, 4 tests failed
  out of 16`, each with its file:line and `want` value. The four files were then restored from copies.
- **No literal formula constant in the module sources:** `test_no_formula_constant_in_rule_sources` scans the 13
  rule modules (src and header) for any numeric literal but 0 and 1. It passes. `test_the_literal_scan_sees_a_constant`
  proves the scan catches a typed `1.6` and ignores comments, strings and type names.
- **`make check`:** every part is green except `plugin-check`, re-proved alone as `ArgoniaWorld.esm: the fixed cell
  sample hashes 653896d87db6, the manifest says a0245b90f930`. That is the terrain and ArgoniaGen lanes' uncommitted
  work (`tools/ArgoniaGen/LandWorld.cs` and others), which no path of this lane reaches. The full gate took 2 min 7 s
  with a peak RSS of 1.35 GB.
- **MSVC:** not compiled, as briefed. The code is C++23 (`std::expected`, `std::bit_cast`, no GNU extension, no
  `<format>`) and builds warning-free under `-Wall -Wextra -Wpedantic -Werror`.

## The tables (G11.2)

Rows were written through `db.py`; the schema block sits below the 0030 marker. The constants come from 76 §116–§127
and the shapes from 85. Tables: `core_module`, `core_constant` (80 constants, each with its design section),
`core_burden_tier`, `core_armour_skill`, `core_skill_class`, `core_use`, `core_use_skill_points`, `core_ranks_per_level`,
`core_bed_tier`, `core_disposition_band`, `core_respawn_class`, `core_wear_kind`, `core_effect_op`, `core_stat_field`,
`condition_shape`, `condition_shape_arg`, `condition_shape_value` and `condition_op`. The generator also reads
`attribute`, `skill`, `skill_bands`, `sheet_rules`, `class_rules`, `specialisation`, `skill_family` and
`condition_term`. A pytest checks all 2,643 condition nodes and 1,597 arguments in the world against
`condition_shape_arg`, and finds no mismatch.

## Calls made inside the brief, and what 76 does not state

- **Armour skills have no score attribute,** so their score is the skill itself. This reproduces 76 §116's anchor
  exactly: Heavy Armor 45 gives a steel rating of 47.51 and 24.06 % mitigation against a 24-damage blow (tested).
- **Some constants are not in 76, so they come from elsewhere,** each with its source in `design_ref`:
  - `wear_per_damage` 0.1 and `condition_floor` 0.1 come from the old economy and wear tables (goal data, not code).
  - Overloaded stamina ×1.35 comes from the old curves table, because 76 lists only fast, mid and fat.
  - `wear_per_use_default` 1 and `wear_per_second_burn` 1 are inferred from the `item_condition` rows: a
    25-condition pick and a 240-condition torch.
  - The owner or 2.3 should confirm these.
- **Swim speed's "burden penalty" (76 §122)** is taken as the walk's `(1 − 0.3 × load)`.
- **Worthiness rules 76 gives without a number are left out:** per-spell-per-rest diminishing returns (2.9),
  per-recipe and per-vendor caps (2.10, 2.6) and the merchant-purse cap. The use counts through the flags the
  adapter sets (`had_effect`, `first_since_rest`, `real_outcome`).
- **Pending levels and sittings:** a sitting needs a pending level, raises the level by `levels_per_sitting` (1; O-16
  is open) and prices points at the new level.
- **The level counter is held in integer credit units** (a full rank is 3, a misc or maxed rank 1), so there is no
  float drift.
- **Respawn's `to_reset` lists every resettable actor,** living ones too, because a rest also returns them home.

## Contradictions found in the inputs (not acted on)

- 76 §116 says "75 buys 88 %"; the formula gives 89.1 %. The test follows the formula.
- 76 §118 says Unarmored `0.0065 × skill²` per bare slot is "60 at skill 100 over four slots"; the formula gives 65
  per slot. The code follows the formula and keeps `unarmored_slots` for the caller.
- The `birthsign_effects` rows differ from 76 §127's table (for example, Apprentice in the rows is +Personality
  and +Speechcraft, not magicka ×1.5). The effects module takes either. The rows' owner should reconcile them.

## Owed by others

- `docs/design/world/98-data-model.md` needs the new tables (1.1 §e). That file is outside this lane's paths.
- The adapters in ArgoniaCore (P1, P2, P7) and the L4 stubs named in native map §5 belong to 1.1 and 1.3–1.5.
- `topics` waits on 1.3 §b's route decision.

## Code review (one /code-review pass, medium; 10 findings)

Fixed:
1. `conditions::check` read `kTermNames` before its bounds check. The bounds check is now first, with a test
   for `Term(200)`.
2. `rank_at_least` returned "no" for a state outside the closed set. It now returns unknown and records the fact
   (tested under `not`).
3. `check.sh`'s fallback linked stale objects. It now clears `build/skse/plain/*.o` first.
4. `core_use.scaled` and `unit` were generated but never read. `worthiness` now applies `scaled` (an unscaled use
   counts in full or not at all), and the Athletics cap keys on `unit = second`.
5. Argument positions were named only to get past the literal scan. They now come from the spec rows (`pos(term,
   kind)`), and the hour-range arity is a constant (`hour_range_args`, 85 §A6).
6. `sheet_rules` and `class_rules` were read as `[0]` with no order. They are now ordered, and the generator
   refuses anything but exactly one row.
7. `evaluate` validated on every call. `evaluate_valid` is the hot path for trees `make()` has already checked.

Not changed:
- `families` sits beside `cosave::upgrade`, so there are two lift chains. This is kept so that ArgoniaCore's
  `main.cpp` (not this lane's path) builds unchanged. META should move onto `families::Registry` when 1.1 wires
  the adapters; then `FamilySpec` and `upgrade` can go.
- **For 2.W3 (`skse/core/weather`, commit 95069d6):**
  - 85's `calendarIs` season set is {dry, rain-onset, monsoon, flood-peak, recession}, but `weather`'s Season is
    {dry, hatching, wet}. One vocabulary must win, and the `condition_shape_value` rows for `calendarIs` follow it.
  - `weather::on_day` turns a bad month or day into day 0 (`value_or(0)`) and writes the dry chances instead of
    refusing.

After the fixes: `100% tests passed out of 17` (the 17th is 2.W3's `core.weather`) and `test_core_tables` 6
passed.
