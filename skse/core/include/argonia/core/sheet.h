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
  // No attribute set: the new-character step has not run (or the save predates it). Its derived values would be
  // degenerate (health 0), so nothing is written from it; the engine keeps its own.
  bool uninitialised() const {
    for (double x : a.v)
      if (x > 0) return false;
    return true;
  }
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

// derive(), or none while the sheet is uninitialised: the caller leaves the engine's own values alone.
std::optional<Derived> derive_set(const Sheet& sh, const Effective& e, double carried_kg);

// The new character (76 §119): the race's attribute baselines for the sex, the class's favoured attributes +10;
// skills start at 5, plus the race's bonus, +25 a major, +10 a minor and +5 for the class's specialisation.
// Level 1, no growth. ArgoniaCore runs it once, at the new game, for the studio character.
Sheet new_character(gen::RaceId race, bool female, gen::ClassId cls);
// At game ready: a sheet still uninitialised becomes the new character (game-11: a `coc` from the main menu starts a
// game with no kNewGame, so the sheet stayed empty, no carrier was written and TK Dodge's perk lock refused every
// roll). True when it made one; a sheet that exists is the character's and is never replaced.
bool ensure_character(Sheet& sh, gen::RaceId race, bool female, gen::ClassId cls);

// The burden tier for carried / capacity (76 §122).
BurdenTier burden_tier(double ratio);

// A skill's §118 score over the effective sheet: its score attribute (and divisor) where it has one, else the skill.
double skill_score(SkillId s, const Effective& e);
// Where the effective sheet sits in one of a skill's bands; none when the skill has no such band.
std::optional<double> skill_band(SkillId s, Band b, const Effective& e);
std::optional<gen::BandRow> band_row(SkillId s, Band b);

}  // namespace argonia::core
