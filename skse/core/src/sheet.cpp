#include "argonia/core/sheet.h"

#include "argonia/core/curve.h"

#include <algorithm>

namespace argonia::core {

namespace c = gen::sheet;

Effective Effective::of(const Sheet& sh) {
  Effective e;
  e.a = sh.a;
  e.s = sh.s;
  for (std::size_t i = 0; i < gen::kStatFieldCount; ++i)
    e.field[i] = gen::kStatFieldKind[i] == gen::FieldKind::factor ? 1.0 : 0.0;
  return e;
}

BurdenTier burden_tier(double ratio) {
  for (std::size_t i = 0; i < gen::kBurdenTiers.size(); ++i) {
    const auto& t = gen::kBurdenTiers[i];
    if (!t.below_ratio || ratio < *t.below_ratio) return BurdenTier(i);
  }
  return BurdenTier(gen::kBurdenTiers.size() - 1);
}

std::optional<gen::BandRow> band_row(SkillId s, Band b) {
  for (const auto& r : gen::kSkillBands)
    if (r.skill == s && r.band == b) return r;
  return std::nullopt;
}

double skill_score(SkillId s, const Effective& e) {
  const auto& row = gen::kSkills[idx(s)];
  if (!row.score) return e.s[s];
  return row.score_divisor ? curve::score(e.s[s], e.a[*row.score], *row.score_divisor)
                           : curve::score(e.s[s], e.a[*row.score]);
}

std::optional<double> skill_band(SkillId s, Band b, const Effective& e) {
  auto r = band_row(s, b);
  if (!r) return std::nullopt;
  return curve::band(r->lo, r->hi, skill_score(s, e));
}

Derived derive(const Sheet& sh, const Effective& e, double carried_kg) {
  const double str = e.a[AttrId::strength], end = e.a[AttrId::endurance], agi = e.a[AttrId::agility];
  const double spd = e.a[AttrId::speed], intel = e.a[AttrId::intelligence], wil = e.a[AttrId::willpower];
  const double ath = e.s[SkillId::athletics], acro = e.s[SkillId::acrobatics];
  Derived d{};
  d.health = (str + end) * c::health_attr_coefficient + sh.level * end / c::health_level_end_divisor +
             e[StatField::health];
  d.stamina = c::stamina_base + c::stamina_end_coefficient * std::min(end, c::stamina_reference_end) +
              c::stamina_above_coefficient * std::max(0.0, end - c::stamina_reference_end) + e[StatField::stamina];
  d.magicka = c::magicka_base + (c::magicka_int_coefficient + e[StatField::magickaMultiplier]) * intel +
              e[StatField::magicka];
  d.stamina_regen = (c::stamina_regen_base + c::stamina_regen_agi_coefficient * agi) *
                    e[StatField::staminaRegenMultiplier];
  d.stamina_regen_delay_s = c::stamina_regen_delay_s;
  d.magicka_regen = (c::magicka_regen_base + c::magicka_regen_wil_coefficient * wil) *
                    e[StatField::magickaRegenMultiplier];
  d.carry_kg = c::carry_base_kg + c::carry_str_coefficient_kg * str + e[StatField::carryWeight];
  d.burden_ratio = d.carry_kg > 0 ? std::max(0.0, carried_kg) / d.carry_kg : (carried_kg > 0 ? 1.0 : 0.0);
  d.burden = burden_tier(d.burden_ratio);
  const auto& tier = gen::kBurdenTiers[std::size_t(d.burden)];
  d.can_run = d.can_jump = d.can_swim_up = tier.can_run;
  const double load = std::min(d.burden_ratio, 1.0);
  const double speed_factor = c::walk_speed_factor_base + spd / c::walk_speed_divisor;
  d.walk_mps = c::walk_base_mps * speed_factor *
               (tier.can_run ? 1.0 - c::load_speed_penalty * load : c::overloaded_walk_fraction);
  d.sprint_mps = tier.can_run ? d.walk_mps * (1.0 + ath / c::sprint_athletics_divisor) : d.walk_mps;
  d.swim_mps = c::swim_base_mps * (c::swim_athletics_base + ath / c::swim_athletics_divisor) *
               (1.0 - c::load_speed_penalty * load);
  d.jump_apex_m = tier.can_run ? c::jump_apex_base_m * (c::jump_acrobatics_base + acro / c::jump_acrobatics_divisor)
                               : 0.0;
  d.safe_fall_m = c::safe_fall_base_m + acro / c::safe_fall_acrobatics_divisor;
  d.breath_s = c::breath_base_s + c::breath_athletics_coefficient * ath + c::breath_endurance_coefficient * end;
  d.unlimited_breath = e[StatField::waterBreathing] > 0;
  d.climb_mps = c::climb_base_mps * skill_band(SkillId::acrobatics, Band::climbSpeed, e).value_or(1.0);
  if (tier.climb_drain_mult)
    d.climb_drain_per_s = c::climb_drain_base_per_s *
                          skill_band(SkillId::acrobatics, Band::climbStamina, e).value_or(1.0) *
                          *tier.climb_drain_mult;
  d.base_poise = agi * c::poise_agility_coefficient + e[StatField::poise];
  return d;
}

std::optional<Derived> derive_set(const Sheet& sh, const Effective& e, double carried_kg) {
  if (sh.uninitialised()) return std::nullopt;
  return derive(sh, e, carried_kg);
}

Sheet new_character(gen::RaceId race, bool female, gen::ClassId cls) {
  const auto& r = gen::kRaces[std::size_t(race)];
  const auto& k = gen::kClasses[std::size_t(cls)];
  Sheet sh;
  sh.a.v = female ? r.female : r.male;
  for (auto f : k.favoured) sh.a[f] += gen::class_rules::favoured_attribute_bonus;
  sh.level = 1;
  sh.cls.spec = k.spec;
  sh.cls.favoured.assign(k.favoured.begin(), k.favoured.end());
  for (std::size_t i = 0; i < gen::kSkillIdCount; ++i) {
    sh.cls.of[i] = SkillClass::misc;
    sh.s.v[i] = gen::class_rules::starting_skill + r.skill_bonus[i] +
                (gen::kSkills[i].spec == k.spec ? gen::class_rules::specialization_bonus : 0.0);
  }
  for (auto s : k.major) {
    sh.cls.of[idx(s)] = SkillClass::major;
    sh.s[s] += gen::class_rules::major_bonus;
  }
  for (auto s : k.minor) {
    sh.cls.of[idx(s)] = SkillClass::minor;
    sh.s[s] += gen::class_rules::minor_bonus;
  }
  return sh;
}

}  // namespace argonia::core
