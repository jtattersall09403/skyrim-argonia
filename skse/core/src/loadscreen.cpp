#include "argonia/core/loadscreen.h"

#include <cmath>

namespace argonia::core::loadscreen {

Drift step(Drift d, float dt, bool dragging) {
  if (dragging) d.dragged = true;
  if (d.dragged) return d;
  if (!(dt > 0.0f)) return d;  // also NaN
  if (dt > kMaxStepSec) dt = kMaxStepSec;
  d.seconds += dt;
  d.yaw_deg = std::fmod(d.yaw_deg + kTurnDegPerSec * dt, 360.0f);
  constexpr float kTau = 6.28318530718f;
  d.scale = 1.0f + kZoomAmplitude * std::sin(kTau * d.seconds / kZoomPeriodSec);
  return d;
}

}  // namespace argonia::core::loadscreen
