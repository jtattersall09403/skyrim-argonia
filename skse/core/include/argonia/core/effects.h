// The one effect stack (76 §127): races, signs, disease, potions, spells and enchantments are all StatEffect
// entries over the same fields. Entries the engine has a magic effect for are mirrored there by ArgoniaCore; this
// module is the arithmetic and the expiry.
#pragma once
#include "argonia/core/sheet.h"

#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace argonia::core::effects {

using gen::EffectOp;
using SourceId = std::uint32_t;  // the form or row that put the entry on the stack

// An attribute, a skill or a stat field.
struct Field {
  enum class Kind : std::uint8_t { attribute, skill, stat } kind;
  std::uint8_t index;
  static constexpr Field attr(AttrId a) { return {Kind::attribute, std::uint8_t(a)}; }
  static constexpr Field skill(SkillId s) { return {Kind::skill, std::uint8_t(s)}; }
  static constexpr Field stat(StatField f) { return {Kind::stat, std::uint8_t(f)}; }
  bool operator==(const Field&) const = default;
};

// A world id (race_effect.field, birthsign_effects.field) as a field; none when it names nothing.
std::optional<Field> field_named(std::string_view id);
std::optional<EffectOp> op_named(std::string_view id);

struct StatEffect {
  Field field;
  EffectOp op;
  double magnitude;
  std::optional<double> until;  // game time it ends; none: permanent
  SourceId source;
};
using Stack = std::vector<StatEffect>;

// Why an entry cannot apply (an op the field does not take, a negative magnitude where one is meaningless);
// none when it is valid. apply() skips invalid entries.
std::optional<std::string> check(const StatEffect& e);

// The effective sheet at game time `now`: entries with until <= now are ignored.
//   attribute, skill: base + fortify + ability - drain - max(0, damage - restore), never below 0
//   pool: fortify + ability - drain - damage;  resist: summed, at most the resist cap (negative is a weakness)
//   factor: the product of fortify and ability;  per_int: fortify + ability - drain;  flag: on when any entry is
Effective apply(const Sheet& sh, std::span<const StatEffect> stack, double now);

// Drops the entries that have ended by `now`; returns how many.
std::size_t expire(Stack& stack, double now);

}  // namespace argonia::core::effects
