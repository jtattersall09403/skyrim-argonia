#include "argonia/core/carriers.h"

#include <algorithm>

namespace argonia::core::carriers {

namespace c = gen::carriers;

double soft_requirement_mult(double shortfall) {
  return 1.0 + c::soft_requirement_stamina_per_point * std::clamp(shortfall, 0.0, c::soft_requirement_max_shortfall);
}

double mitigation(double armour_rating, double incoming_damage) {
  const double ar = std::max(0.0, armour_rating);
  return ar / (ar + c::mitigation_constant + c::mitigation_damage_coefficient * std::max(0.0, incoming_damage));
}

double strength_term(double strength) { return (strength + c::strength_damage_base) / c::strength_damage_divisor; }

namespace {

Hand hand(const Effective& e, BurdenTier burden, const HandContext& h) {
  Hand out;
  if (!h.skill) return out;
  const SkillId s = *h.skill;
  const bool no_strength = h.bow || s == SkillId::handToHand;
  out.damage_position = skill_band(s, Band::damagePosition, e).value_or(0.0);
  out.strength_term = no_strength ? 1.0 : strength_term(e.a[AttrId::strength]);
  const double stamina_band = skill_band(s, h.bow ? Band::drawStamina : Band::staminaCost, e).value_or(1.0);
  out.stamina_mult = stamina_band * gen::kBurdenTiers[std::size_t(burden)].stamina_mult *
                     soft_requirement_mult(h.requirement_shortfall);
  out.wear_mult = skill_band(s, Band::wear, e).value_or(1.0);
  return out;
}

}  // namespace

Carriers compute(const Sheet&, const Effective& e, BurdenTier burden, HandContext right, HandContext left) {
  Carriers out;
  out.right = hand(e, burden, right);
  out.left = hand(e, burden, left);
  for (std::size_t i = 0; i < gen::kArmourSkills.size(); ++i) {
    const auto& row = gen::kArmourSkills[i];
    out.armour_rating_mult[i] =
        row.rating_mult ? *row.rating_mult * skill_band(row.skill, Band::rating, e).value_or(1.0) : 0.0;
  }
  const double bare = e.s[SkillId::unarmored];
  out.unarmored_rating_per_slot = c::unarmored_coefficient * bare * bare;
  out.block_stability = std::min(skill_band(SkillId::block, Band::stability, e).value_or(1.0), c::block_stability_cap) +
                        e[StatField::blockStability];
  out.guard_stamina_mult = skill_band(SkillId::block, Band::guardStamina, e).value_or(1.0);
  return out;
}

}  // namespace argonia::core::carriers
