#include "argonia/core/chart.h"

namespace argonia::core::chart {

namespace {
bool in_range(std::int32_t v) { return v >= kCellMin && v <= kCellMax; }
}  // namespace

bool reveal(Discovered& d, Cell c) {
  if (!in_range(c.x) || !in_range(c.y)) return false;
  return d.columns[c.x].insert(c.y).second;
}

bool revealed(const Discovered& d, Cell c) {
  auto it = d.columns.find(c.x);
  return it != d.columns.end() && it->second.contains(c.y);
}

std::size_t count(const Discovered& d) {
  std::size_t n = 0;
  for (const auto& [x, ys] : d.columns) n += ys.size();
  return n;
}

std::vector<Cell> cells(const Discovered& d) {
  std::vector<Cell> out;
  for (const auto& [x, ys] : d.columns)
    for (auto y : ys) out.push_back({x, y});
  return out;
}

std::vector<families::Step> migrations() { return {}; }

cosave::Bytes encode(const Discovered& d) {
  cosave::Writer w;
  w.u32(std::uint32_t(d.columns.size()));
  for (const auto& [x, ys] : d.columns) {
    w.i32(x);
    w.u32(std::uint32_t(ys.size()));
    for (auto y : ys) w.i32(y);
  }
  return w.take();
}

std::optional<Discovered> decode(std::span<const std::uint8_t> b) {
  cosave::Reader r(b);
  auto n = r.u32();
  if (!n) return std::nullopt;
  Discovered d;
  std::optional<std::int32_t> px;
  for (std::uint32_t i = 0; i < *n; ++i) {
    auto x = r.i32();
    auto m = r.u32();
    if (!x || !m || !in_range(*x) || (px && *x <= *px)) return std::nullopt;  // columns rise: a map
    px = x;
    auto& ys = d.columns[*x];
    std::optional<std::int32_t> py;
    for (std::uint32_t j = 0; j < *m; ++j) {
      auto y = r.i32();
      if (!y || !in_range(*y) || (py && *y <= *py)) return std::nullopt;  // rows rise: a set
      py = y;
      ys.insert(*y);
    }
  }
  if (!r.done()) return std::nullopt;
  return d;
}

}  // namespace argonia::core::chart
