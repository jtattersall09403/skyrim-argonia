#pragma once
// The Dark Souls backstab's geometry, with no engine types (unit-tested on Linux by skse/check.sh).
// Skyrim's frame: x east, y north, z up; an actor's heading is angle.z in radians, clockwise from north, so its
// forward vector is (sin z, cos z). A light attack starts a backstab on a target when all hold:
//   the player stands within `reach` units of the target (flat distance) and within `height` units up or down;
//   the player stands behind the target: the target-to-player direction is within `behind_deg` of the target's
//     straight-back direction (its back hemisphere's middle cone);
//   the player faces the way the target faces: the two headings differ by at most `facing_deg`
//     (Rim Parry's ExeBackStab checks the same, GetRelativeAngle on Z, widened 30 -> 45 by our plugin's override).
#include <cmath>

namespace argonia::backstab {

struct Pose {
  double x = 0, y = 0, z = 0;  // position
  double heading = 0;          // angle.z, radians
};

struct Rule {
  double reach = 200.0;      // units (BackStabProjectile's range is 250: the feeler must still reach the back)
  double height = 100.0;     // units
  double behind_deg = 60.0;  // each side of straight behind
  double facing_deg = 45.0;  // each side of the target's heading
};

constexpr double kPi = 3.14159265358979323846;

inline double deg(double rad) { return rad * 180.0 / kPi; }

// Smallest absolute difference between two headings, degrees in [0, 180].
inline double heading_diff_deg(double a, double b) {
  double d = std::fmod(std::fabs(a - b), 2.0 * kPi);
  if (d > kPi) d = 2.0 * kPi - d;
  return deg(d);
}

// Angle between the target's straight-back direction and the direction from the target to the player, degrees.
inline double off_behind_deg(const Pose& target, const Pose& player) {
  const double dx = player.x - target.x, dy = player.y - target.y;
  const double len = std::hypot(dx, dy);
  if (len < 1e-6) return 0.0;
  const double bx = -std::sin(target.heading), by = -std::cos(target.heading);
  double c = (dx * bx + dy * by) / len;
  c = c > 1.0 ? 1.0 : (c < -1.0 ? -1.0 : c);
  return deg(std::acos(c));
}

enum class Why { Ok, TooFar, TooHighOrLow, NotBehind, NotFacing };

inline Why check(const Pose& player, const Pose& target, const Rule& r) {
  if (std::hypot(player.x - target.x, player.y - target.y) > r.reach) return Why::TooFar;
  if (std::fabs(player.z - target.z) > r.height) return Why::TooHighOrLow;
  if (off_behind_deg(target, player) > r.behind_deg) return Why::NotBehind;
  if (heading_diff_deg(player.heading, target.heading) > r.facing_deg) return Why::NotFacing;
  return Why::Ok;
}

inline const char* name(Why w) {
  switch (w) {
    case Why::Ok: return "ok";
    case Why::TooFar: return "too far";
    case Why::TooHighOrLow: return "too high or low";
    case Why::NotBehind: return "not behind";
    case Why::NotFacing: return "not facing its way";
  }
  return "?";
}

}  // namespace argonia::backstab
