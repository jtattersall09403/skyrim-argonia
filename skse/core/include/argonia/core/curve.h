// The one skill curve over Morrowind's score (76 §116): score, k and band. Every number is a generated table value.
#pragma once

namespace argonia::core::curve {

// Morrowind's term normalised to 0-100: (skill + attr / divisor) / normaliser; the divisor defaults to 5.
double score(double skill, double attr);
double score(double skill, double attr, double attr_divisor);
// 1 - (1 - s/100)^exponent: 0 at score 0, 1 at score 100; a score outside 0-100 is held at the nearer end.
double k(double s);
// lo + (hi - lo) * k(s): where in a band a score sits.
double band(double lo, double hi, double s);
// The out-of-combat fatigue term (76 §117.3): floor + span * stamina/max; 1 when max is not positive.
double fatigue(double stamina, double max_stamina);

}  // namespace argonia::core::curve
