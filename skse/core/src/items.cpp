#include "argonia/core/items.h"

#include "argonia/core/curve.h"

#include <algorithm>

namespace argonia::core::items {

namespace c = gen::items;

double wear(const ItemState& it, WearKind kind, double amount, double skill_wear_band) {
  const double a = std::max(0.0, amount);
  switch (gen::kWearPer[std::size_t(kind)]) {
    case gen::WearPer::damage: return a * c::wear_per_damage * skill_wear_band;
    case gen::WearPer::use: return a * it.wear_per_use.value_or(c::wear_per_use_default);
    case gen::WearPer::second: return a * c::wear_per_second_burn;
  }
  return 0;
}

ItemState worn(const ItemState& it, WearKind kind, double amount, double skill_wear_band) {
  ItemState out = it;
  out.condition = std::max(0.0, it.condition - wear(it, kind, amount, skill_wear_band));
  return out;
}

bool usable(const ItemState& it) { return it.condition > 0; }

double armour_effectiveness(const ItemState& it) {
  if (it.max <= 0) return c::condition_floor;
  return std::clamp(it.condition / it.max, c::condition_floor, 1.0);
}

double repair_stroke(double smithing_score) {
  for (const auto& r : gen::kSkillBands)
    if (r.skill == gen::SkillId::smithing && r.band == gen::Band::repairPerStroke)
      return curve::band(r.lo, r.hi, smithing_score);
  return 0;
}

ItemState repaired(const ItemState& it, double smithing_score) {
  ItemState out = it;
  out.condition = std::min(it.max * c::repair_ceiling, std::max(it.condition, it.condition + repair_stroke(smithing_score)));
  return out;
}

cosave::Bytes encode(const Table& t) {
  cosave::Writer w;
  w.u32(std::uint32_t(t.size()));
  for (const auto& [id, s] : t) {
    w.u64(id); w.f64(s.condition); w.f64(s.max);
    w.u8(s.wear_per_use ? 1 : 0);
    if (s.wear_per_use) w.f64(*s.wear_per_use);
  }
  return w.take();
}

std::optional<Table> decode(std::span<const std::uint8_t> b) {
  cosave::Reader r(b);
  auto n = r.u32();
  if (!n) return std::nullopt;
  Table t;
  for (std::uint32_t i = 0; i < *n; ++i) {
    auto id = r.u64(); auto cond = r.f64(); auto max = r.f64(); auto has = r.u8();
    if (!id || !cond || !max || !has || *has > 1 || t.count(*id)) return std::nullopt;
    ItemState s{*cond, *max, std::nullopt};
    if (*has) {
      auto wpu = r.f64();
      if (!wpu) return std::nullopt;
      s.wear_per_use = *wpu;
    }
    if (s.condition < 0 || s.condition > s.max) return std::nullopt;
    t[*id] = s;
  }
  if (!r.done()) return std::nullopt;
  return t;
}

}  // namespace argonia::core::items
