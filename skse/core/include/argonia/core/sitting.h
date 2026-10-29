// The level sitting (76 §120.4): a rest banks one pending level and opens the sitting, where vastei buys attribute
// points at the formula cost, at most a cap per attribute per sitting; unspent vastei carries over.
#pragma once
#include "argonia/core/sheet.h"

#include <array>
#include <expected>
#include <string>

namespace argonia::core::sitting {

struct State {
  Sheet sheet;   // the level is already the banked one; attributes rise as points are bought
  double vastei = 0;
  std::array<int, gen::kAttrIdCount> bought{};
};

enum class Refusal { no_pending_level, at_cap_this_sitting, at_purchase_cap, too_dear };
const char* to_string(Refusal r);

// base(level) x (1 + attr/divisor)^exponent x (1 + increment x (nth - 1)); nth counts from 1 this sitting.
double cost(AttrId a, int nth, int level, double attr_value);
double cost(const State& st, AttrId a);  // the next point of `a` in this sitting

// Opens a sitting for one pending level: the level rises by the sitting's levels.
std::expected<State, Refusal> open(const Sheet& sh, double vastei, int pending_levels);
std::expected<State, Refusal> buy(const State& st, AttrId a);

struct Closed { Sheet sheet; double vastei; };
Closed close(const State& st);

}  // namespace argonia::core::sitting
