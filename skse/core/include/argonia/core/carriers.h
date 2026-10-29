// P1 carrier values (native map §2): the numbers Skyrim's perk entry points cannot compute from conditions,
// written by ArgoniaCore into reserved actor values. One set per hand, one armour multiplier per armour skill.
#pragma once
#include "argonia/core/sheet.h"

#include <array>
#include <optional>

namespace argonia::core::carriers {

struct HandContext {
  std::optional<SkillId> skill;      // the weapon class's skill (76 §118); none: the hand is empty
  bool bow = false;                  // a bow or crossbow: no Strength term (76 §117 point 1)
  double requirement_shortfall = 0;  // the largest attribute shortfall under the item's soft requirements
};

struct Hand {
  double damage_position = 0;  // where in the listed range the blow lands (the skill's damagePosition band)
  double strength_term = 0;    // (Str + base) / divisor; 1 for bows and hand-to-hand
  double stamina_mult = 0;     // skill band x burden tier x soft requirement
  double wear_mult = 0;        // the skill's wear band; 1 when the class has none
};

struct Carriers {
  Hand right, left;
  std::array<double, gen::kArmourSkills.size()> armour_rating_mult{};  // per kArmourSkills row; 0 for Unarmored
  double unarmored_rating_per_slot = 0;
  double block_stability = 0;  // the Block band, at most the stability cap, plus the stack's blockStability
  double guard_stamina_mult = 0;
};

Carriers compute(const Sheet& sh, const Effective& e, BurdenTier burden, HandContext right, HandContext left);

// The stamina multiplier of a soft requirement shortfall (76 §121.1), the shortfall capped.
double soft_requirement_mult(double shortfall);
// Defence (76 §121.4): AR / (AR + constant + coefficient x incoming damage).
double mitigation(double armour_rating, double incoming_damage);
// Morrowind's Strength damage term (76 §121.1).
double strength_term(double strength);

}  // namespace argonia::core::carriers
