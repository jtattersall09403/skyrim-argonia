// L2: the loading screen's drift (1.12 lane loading): about 8 degrees a second, wrapping at 360; the scale breathes
// within +-4 % over 20 s; a hitch steps at most 0.25 s; a zero, negative or NaN step changes nothing; the first drag
// freezes it for the rest of the screen.
#include "check.h"
#include "argonia/core/loadscreen.h"

#include <cmath>
#include <limits>

using namespace argonia::core::loadscreen;

static bool near(float a, float b, float eps = 1e-3f) { return std::fabs(a - b) < eps; }

int main() {
  Drift d;
  for (int i = 0; i < 60; ++i) d = step(d, 1.0f / 60.0f, false);
  CHECK(near(d.seconds, 1.0f));
  CHECK(near(d.yaw_deg, 8.0f, 1e-2f));
  CHECK(d.scale > 1.0f && d.scale < 1.0f + kZoomAmplitude);
  Drift w;
  for (int i = 0; i < 46 * 4; ++i) w = step(w, 0.25f, false);  // 46 s: one full turn and 8 degrees
  CHECK(w.yaw_deg >= 0.0f && w.yaw_deg < 360.0f && near(w.yaw_deg, 8.0f, 1e-1f));
  float lo = 2, hi = 0;
  Drift z;
  for (int i = 0; i < 2000; ++i) { z = step(z, 0.01f, false); lo = std::fmin(lo, z.scale); hi = std::fmax(hi, z.scale); }
  CHECK(near(hi, 1.0f + kZoomAmplitude, 1e-3f) && near(lo, 1.0f - kZoomAmplitude, 1e-3f));
  Drift h = step(Drift{}, 5.0f, false);  // a hitch
  CHECK(near(h.seconds, kMaxStepSec) && near(h.yaw_deg, kTurnDegPerSec * kMaxStepSec));
  CHECK(step(Drift{}, 0.0f, false).seconds == 0.0f);
  CHECK(step(Drift{}, -1.0f, false).seconds == 0.0f);
  CHECK(step(Drift{}, std::numeric_limits<float>::quiet_NaN(), false).seconds == 0.0f);
  Drift g = step(d, 0.1f, true);  // dragged: holds
  CHECK(g.dragged && g.yaw_deg == d.yaw_deg && g.scale == d.scale);
  g = step(g, 0.5f, false);       // and stays held after the drag ends
  CHECK(g.yaw_deg == d.yaw_deg && g.seconds == d.seconds);
  return TEST_MAIN_RESULT("core.loadscreen");
}
