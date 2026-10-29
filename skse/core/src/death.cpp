#include "argonia/core/death.h"

#include "argonia/core/tables_progression.h"

#include <cmath>

namespace argonia::core::death {

Outcome on_death(double carried, Pos at, Pos last_wake_point) {
  Outcome o;
  if (carried > 0) o.pile = Pile{at, carried};
  o.carried = 0;
  o.wake = last_wake_point;
  return o;
}

double ground_distance(Pos a, Pos b) { return std::hypot(a.x - b.x, a.y - b.y); }

std::optional<double> take(const Pile& pile, Pos player) {
  return take(pile, player, gen::death::pile_recovery_radius_m);
}

std::optional<double> take(const Pile& pile, Pos player, double radius_m) {
  if (pile.at.cell != player.cell || ground_distance(pile.at, player) > radius_m) return std::nullopt;
  return pile.vastei;
}

namespace {
void put(cosave::Writer& w, const Pos& p) { w.f64(p.x); w.f64(p.y); w.f64(p.z); w.u32(p.cell); }
std::optional<Pos> get(cosave::Reader& r) {
  auto x = r.f64(); auto y = r.f64(); auto z = r.f64(); auto c = r.u32();
  if (!x || !y || !z || !c) return std::nullopt;
  return Pos{*x, *y, *z, *c};
}
}  // namespace

cosave::Bytes encode(const State& s) {
  cosave::Writer w;
  w.u8(s.pile ? 1 : 0);
  if (s.pile) { put(w, s.pile->at); w.f64(s.pile->vastei); }
  w.u8(s.wake ? 1 : 0);
  if (s.wake) put(w, *s.wake);
  return w.take();
}

std::optional<State> decode(std::span<const std::uint8_t> b) {
  cosave::Reader r(b);
  State s;
  auto has_pile = r.u8();
  if (!has_pile || *has_pile > 1) return std::nullopt;
  if (*has_pile) {
    auto at = get(r); auto v = r.f64();
    if (!at || !v) return std::nullopt;
    s.pile = Pile{*at, *v};
  }
  auto has_wake = r.u8();
  if (!has_wake || *has_wake > 1) return std::nullopt;
  if (*has_wake) {
    auto at = get(r);
    if (!at) return std::nullopt;
    s.wake = *at;
  }
  if (!r.done()) return std::nullopt;
  return s;
}

}  // namespace argonia::core::death
