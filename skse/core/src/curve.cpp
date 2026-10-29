#include "argonia/core/curve.h"

#include "argonia/core/tables_sheet.h"

#include <algorithm>
#include <cmath>

namespace argonia::core::curve {

namespace c = gen::curve;

double score(double skill, double attr) { return score(skill, attr, c::score_attr_divisor); }

double score(double skill, double attr, double attr_divisor) {
  return (skill + attr / attr_divisor) / c::score_normaliser;
}

double k(double s) {
  const double x = std::clamp(s / c::score_scale, 0.0, 1.0);
  return 1.0 - std::pow(1.0 - x, c::k_exponent);
}

double band(double lo, double hi, double s) { return lo + (hi - lo) * k(s); }

double fatigue(double stamina, double max_stamina) {
  if (max_stamina <= 0) return 1.0;
  return c::fatigue_floor + c::fatigue_span * std::clamp(stamina / max_stamina, 0.0, 1.0);
}

}  // namespace argonia::core::curve
