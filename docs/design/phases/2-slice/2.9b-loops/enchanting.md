<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9b-loops/enchanting.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: enchanting (2.9b § Loops, lane 2.9b-d)

One row per measurement. The numbers are pure-function tests in
`packages/crafting/src/enchanting.test.ts` and the headless drive in
`packages/scene/src/interact/crafting-session.test.ts`, over the real effect
rows (`packages/magic/src/data/effects.json`), the real soul-gem item rows and
`magic.json` `enchanting`. No capture: enchanting has no world-side visual of
its own (the screen is lane f's survey).

Written before the first measure; results filled after (2026-10-20).

## Rules measured (sources)

- Point budget (world/76 §123): `points = (effEnchant + effInt/5) / 3`.
- Point cost of one effect, Morrowind's enchantment cost rule (UESP
  `Morrowind:Enchant` § Enchantment cost, fetched 2026-10-20 through the UESP API):
  `floor(base × ((min + max) × duration + area) / 40)`, × 1.5 on Target;
  a constant effect puts `100` in place of the duration
  (`magic.json enchanting.constantEffectCostMultiplier`). One magnitude
  (min = max) on our items; at least 1 point.
- Constant effect cap by soul (§123 tiers, owner ruling 2.9b): a soul caps the
  constant effect's magnitude at `floor(share × full range)`, at least 1, where
  share = capacity / 600 (`constantEffectMagnitudeShareBySoul`: petty 0.05,
  lesser 0.1333, common 0.25, greater 0.5, grand 1) and the full range is the
  largest magnitude any catalogue spell gives the effect; the point budget
  applies on top. Canon is one flat gate (soul 400 or more, UESP § Constant
  Effect Requirements). Example: Fortify Health (range 40) at Enchant 100 /
  Int 100: petty caps at 2, grand at 40, and the budget stops it at 8.
- Charged use cost (§123, canon verbatim): `points × (1.1 − effEnchant/100)`,
  at least 1 (UESP: the game enforces a minimum cost of 1 charge).
- Charge: a charged item's `chargeMax` is the filled gem's capacity.
- Recharge from a gem: restores `min(gem capacity, chargeMax − charge)`; the
  2.6 recharge service prices those points by `rechargePrice`.

## Worked budget examples

| Enchant | Intelligence | Budget |
|---|---|---|
| 100 | 100 | (100 + 20) / 3 = 40 |
| 30 | 50 | (30 + 10) / 3 = 13.33 |
| 60 | 40 | (60 + 8) / 3 = 22.67 |

## Rows

| # | Measure (bar) | Elapsed | Result |
|---|---|---|---|
| 1 | budget at the three worked examples (exact) | 0.4 s (file) | green: 40, 13.33, 22.67 |
| 2 | point cost: fire-damage 10 pts 1 s on touch = floor(5 × 20 / 40) style rule, Target × 1.5, constant × 100 (exact) | (in row 1) | green: touch, Target ×1.5, constant ×100, minimum 1 |
| 3 | enchant refusals: not learned, over budget, empty gem, banned effect, constant magnitude over the soul's share (petty vs grand on Fortify Health) (each refused, inventory unchanged) | (in row 1) | green: each refused, nothing consumed; petty 2 ok, 4 refused (cap 2); grand 8 ok, 9 over budget |
| 4 | enchant success: gem consumed, enchantment on the instance, chargeMax = gem capacity, {skill: "enchant", points} | (in row 1) | green: chargeMax 30 from a petty soul; enchant use reported |
| 5 | use cost at Enchant 5, 50, 100, 110 (exact; minimum 1) and refusal under charge | (in row 1) | green: 10.5, 6, 1, 1 at 10 points; under charge refused |
| 6 | disenchant: item destroyed, effect learned | (in row 1) | green: found Steel Dagger of Chills teaches frost-damage |
| 7 | recharge from a gem: restores min(capacity, missing), gem consumed; service price = rechargePrice(points) | 0.4 s (+ economy services.test.ts) | green: 26 restored from a lesser soul; service gold = rechargePrice(30) |
| 8 | crafting save family: learned and instance enchantment round-trip through the registry, wrong shapes refused | 0.3 s | green: version 1, restores after inventory, 7 wrong shapes refused |
| 9 | headless drive: petty gem filled by Soultrap → enchant dagger → equip → use drops charge → recharge from lesser gem → disenchant looted item teaches a new effect | 4.1 s | green: the whole chain in crafting-session.test.ts |
