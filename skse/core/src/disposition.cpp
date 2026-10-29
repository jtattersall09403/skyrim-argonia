#include "argonia/core/disposition.h"

#include <algorithm>
#include <cmath>

namespace argonia::core::disposition {

namespace c = gen::disposition;

int clamp(double d) { return int(std::lround(std::clamp(d, c::disposition_min, c::disposition_max))); }

int base(const Speaker& s, const Priors& p) {
  return clamp(s.authored_base + c::personality_coefficient * (p.personality - c::personality_reference) +
               p.faction_reaction + p.membership + p.race + p.deeds);
}

DispositionBand band(int d) {
  std::size_t at = 0;
  for (std::size_t i = 0; i < gen::kDispositionBandMin.size(); ++i)
    if (d >= gen::kDispositionBandMin[i]) at = i;
  return DispositionBand(at);
}

int apply(int d, const Change& ch) { return clamp(double(d) + ch.delta); }

cosave::Bytes encode(const Table& t) {
  cosave::Writer w;
  w.u32(std::uint32_t(t.size()));
  for (auto [npc, d] : t) { w.u32(npc); w.i32(d); }
  return w.take();
}

std::optional<Table> decode(std::span<const std::uint8_t> b) {
  cosave::Reader r(b);
  auto n = r.u32();
  if (!n) return std::nullopt;
  Table t;
  for (std::uint32_t i = 0; i < *n; ++i) {
    auto npc = r.u32();
    auto d = r.i32();
    if (!npc || !d || *d < c::disposition_min || *d > c::disposition_max || t.count(*npc)) return std::nullopt;
    t[*npc] = *d;
  }
  if (!r.done()) return std::nullopt;
  return t;
}

}  // namespace argonia::core::disposition
