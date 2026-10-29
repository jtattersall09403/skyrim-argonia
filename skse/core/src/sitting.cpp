#include "argonia/core/sitting.h"

#include <cmath>

namespace argonia::core::sitting {

namespace c = gen::sitting;

const char* to_string(Refusal r) {
  switch (r) {
    case Refusal::no_pending_level: return "no level is ready to bank";
    case Refusal::at_cap_this_sitting: return "no more points in that attribute this sitting";
    case Refusal::at_purchase_cap: return "that attribute is at the purchase cap";
    case Refusal::too_dear: return "not enough vastei";
  }
  return "?";
}

double cost(AttrId, int nth, int level, double attr_value) {
  const double base = c::cost_base * std::pow(1.0 + level / c::cost_level_divisor, c::cost_level_exponent);
  return base * std::pow(1.0 + attr_value / c::cost_attr_divisor, c::cost_attr_exponent) *
         (1.0 + c::cost_nth_increment * (nth - 1));
}

double cost(const State& st, AttrId a) { return cost(a, st.bought[idx(a)] + 1, st.sheet.level, st.sheet.a[a]); }

std::expected<State, Refusal> open(const Sheet& sh, double vastei, int pending_levels) {
  if (pending_levels <= 0) return std::unexpected(Refusal::no_pending_level);
  State st{sh, vastei, {}};
  st.sheet.level += int(c::levels_per_sitting);
  return st;
}

std::expected<State, Refusal> buy(const State& st, AttrId a) {
  if (st.bought[idx(a)] >= int(c::points_per_attribute_cap)) return std::unexpected(Refusal::at_cap_this_sitting);
  if (st.sheet.a[a] >= gen::sheet_rules::purchase_cap) return std::unexpected(Refusal::at_purchase_cap);
  const double price = cost(st, a);
  if (st.vastei < price) return std::unexpected(Refusal::too_dear);
  State out = st;
  out.vastei -= price;
  out.sheet.a[a] += 1.0;
  ++out.bought[idx(a)];
  return out;
}

Closed close(const State& st) { return {st.sheet, st.vastei}; }

}  // namespace argonia::core::sitting
