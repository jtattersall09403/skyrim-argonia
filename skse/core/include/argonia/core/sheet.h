// The character sheet (76 §116-§122): seven attributes, 27 skills, a level and a class, and every value derived
// from them. Attributes and skills are canonical in the `stats` family (P7); this module only computes.
#pragma once
#include "argonia/core/tables_progression.h"
#include "argonia/core/tables_sheet.h"

#include <array>
#include <cstddef>
#include <optional>
#include <vector>

namespace argonia::core {

using gen::AttrId;
using gen::Band;
using gen::BurdenTier;
using gen::SkillClass;
using gen::SkillId;
using gen::Specialisation;
using gen::StatField;

constexpr std::size_t idx(AttrId a) { return std::size_t(a); }
constexpr std::size_t idx(SkillId s) { return std::size_t(s); }
constexpr std::size_t idx(StatField f) { return std::size_t(f); }

struct Attributes {
  std::array<double, gen::kAttrIdCount> v{};
  double& operator[](AttrId a) { return v[idx(a)]; }
  double operator[](AttrId a) const { return v[idx(a)]; }
  bool operator==(const Attributes&) const = default;
};

struct Skills {
  std::array<double, gen::kSkillIdCount> v{};
  double& operator[](SkillId s) { return v[idx(s)]; }
  double operator[](SkillId s) const { return v[idx(s)]; }
  bool operator==(const Skills&) const = default;
};

// Morrowind's class (76 §119): each skill major, minor or miscellaneous, a specialisation, favoured attributes.
struct Class {
  std::array<SkillClass, gen::kSkillIdCount> of{};
  Specialisation spec = Specialisation::combat;
  std::vector<AttrId> favoured;
  bool operator==(const Class&) const = default;
};

struct Sheet {
  Attributes a;  // base values (bought at sittings, set at creation)
  Skills s;      // base values (raised by use, trainers and books)
  int level = 1;
  Class cls;
  bool operator==(const Sheet&) const = default;
};

// The sheet after the effect stack (effects.h): effective attributes and skills, and one combined value per stat
// field (pool and resist: summed; factor: multiplied; per_int: summed; flag: 1 when on).
struct Effective {
  Attributes a;
  Skills s;
  std::array<double, gen::kStatFieldCount> field{};
  double operator[](StatField f) const { return field[idx(f)]; }
  static Effective of(const Sheet& sh);  // no effects: base values, every field at its identity
};

struct Derived {
  double health, stamina, magicka, carry_kg;
  double stamina_regen, stamina_regen_delay_s, magicka_regen;
  double walk_mps, sprint_mps, swim_mps, jump_apex_m, safe_fall_m, breath_s;
  bool unlimited_breath;
  double burden_ratio;
  BurdenTier burden;
  bool can_run, can_jump, can_swim_up;
  double climb_mps;
  std::optional<double> climb_drain_per_s;  // none: cannot climb (overloaded)
  double base_poise;
};

// Every derived value of 76 §117-§122 over the effective sheet and what is carried.
Derived derive(const Sheet& sh, const Effective& e, double carried_kg);

// The burden tier for carried / capacity (76 §122).
BurdenTier burden_tier(double ratio);

// A skill's §118 score over the effective sheet: its score attribute (and divisor) where it has one, else the skill.
double skill_score(SkillId s, const Effective& e);
// Where the effective sheet sits in one of a skill's bands; none when the skill has no such band.
std::optional<double> skill_band(SkillId s, Band b, const Effective& e);
std::optional<gen::BandRow> band_row(SkillId s, Band b);

}  // namespace argonia::core
