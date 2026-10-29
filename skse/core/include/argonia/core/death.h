// Death (76 §120.3, §126): wake at the last rest with the world and the character kept; carried vastei stays as
// one pile at the death spot, a second death replaces it, and the whole pile is taken back within the radius.
#pragma once
#include "argonia/core/cosave.h"
#include "argonia/core/rest.h"

#include <optional>
#include <span>

namespace argonia::core::death {

using rest::Pos;

struct Pile { Pos at; double vastei = 0; bool operator==(const Pile&) const = default; };

struct Outcome {
  std::optional<Pile> pile;  // replaces any earlier pile; none when nothing was carried
  double carried = 0;        // after death
  Pos wake;                  // the last rest's wake point
  bool counts_as_rest = true;
};

Outcome on_death(double carried, Pos at, Pos last_wake_point);

// Ground distance (x, y) in metres, same cell only.
double ground_distance(Pos a, Pos b);
// The whole pile when the player stands within the recovery radius, else none.
std::optional<double> take(const Pile& pile, Pos player);
std::optional<double> take(const Pile& pile, Pos player, double radius_m);

// The `death` family payload: the pile, if any, and the wake point (version 1).
inline constexpr std::uint32_t kDeathType = cosave::fourcc("DETH");
struct State { std::optional<Pile> pile; std::optional<Pos> wake; bool operator==(const State&) const = default; };
cosave::Bytes encode(const State& s);
std::optional<State> decode(std::span<const std::uint8_t> b);

}  // namespace argonia::core::death
