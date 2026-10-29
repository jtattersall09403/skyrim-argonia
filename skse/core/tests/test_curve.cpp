// L2: the skill curve (76 §116): score, k, band and the fatigue term, with their ends and out-of-range scores.
#include "check.h"
#include "argonia/core/curve.h"

#include <cmath>

using namespace argonia::core;

int main() {
  CHECK_NEAR(curve::score(100, 100), 100.0, 1e-12);       // 100/100 reads 100
  CHECK_NEAR(curve::score(60, 50), 58.333333333, 1e-6);    // Marsh Hand's Long Blade
  CHECK_NEAR(curve::score(30, 40, 10), 28.333333333, 1e-6);  // Alchemy's Int/10
  CHECK_NEAR(curve::k(0), 0.0, 1e-12);
  CHECK_NEAR(curve::k(100), 1.0, 1e-12);
  CHECK_NEAR(curve::k(25), 0.369, 1e-3);                   // "25 buys 36 %"
  CHECK_NEAR(curve::k(50), 0.670, 1e-3);                   // "50 buys 67 %"
  CHECK_NEAR(curve::k(75), 0.891, 1e-3);                   // "75 buys 88 %" (89.1 by the formula)
  CHECK_NEAR(curve::k(150), 1.0, 1e-12);                   // a god build is held at the end, never NaN
  CHECK_NEAR(curve::k(-20), 0.0, 1e-12);
  CHECK(std::isfinite(curve::k(1e9)));
  CHECK_NEAR(curve::band(0.4, 1.0, 0), 0.4, 1e-12);
  CHECK_NEAR(curve::band(0.4, 1.0, 100), 1.0, 1e-12);
  CHECK_NEAR(curve::band(1.25, 0.8, 100), 0.8, 1e-12);     // a falling band
  CHECK_NEAR(curve::fatigue(100, 100), 1.0, 1e-12);
  CHECK_NEAR(curve::fatigue(0, 100), 0.85, 1e-12);
  CHECK_NEAR(curve::fatigue(10, 0), 1.0, 1e-12);           // no pool: no penalty
  CHECK_NEAR(curve::fatigue(200, 100), 1.0, 1e-12);
  return TEST_MAIN_RESULT("core.curve");
}
