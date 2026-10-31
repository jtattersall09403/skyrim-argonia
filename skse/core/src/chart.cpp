#include "argonia/core/chart.h"

#include "argonia/core/tables_progression.h"

#include <cmath>
#include <algorithm>
#include <numbers>

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

bool marker_discovered(std::uint8_t flags) {
  return (flags & kMarkerVisible) && (flags & kMarkerCanTravelTo);
}

std::string_view marker_kind(std::uint16_t type) {
  switch (type) {
    case 1: case 2: case 3: case 30: case 32: return "settlement";  // city, town, settlement, shack, dwelling
    case 4: case 12: case 29: return "lair";                       // cave, lair, giant camp
    case 5: return "camp";
    case 6: case 16: case 17: case 22: case 28: case 31: return "martial";  // forts, camps of war, towers
    case 7: case 8: return "ruin";
    case 9: case 21: case 24: case 27: case 33: return "transit";  // wreck, stable, pass, lighthouse, docks
    case 10: case 18: case 25: case 34: case 55: return "sacred";  // grove, stone, altar, shrine
    case 13: return "lone";
    case 14: case 15: case 19: case 20: return "works";
    case 0: case 61: case 62: case 63: case 64: case 65: return "";
    default: return "civic";
  }
}

Point cell_units(double x_units, double y_units) {
  return {x_units / gen::units::cell_units, y_units / gen::units::cell_units};
}

Cell cell_of(Point p) {
  return {std::int32_t(std::floor(p.x)), std::int32_t(std::floor(p.y))};
}

double heading_deg(double angle_z) {
  double d = std::fmod(angle_z * 180.0 / std::numbers::pi, 360.0);
  if (d < 0) d += 360.0;
  return d >= 360.0 ? 0.0 : d;
}

bool within(Point c, Point p, double reach) {
  const double dx = p.x - c.x, dy = p.y - c.y;
  return dx * dx + dy * dy <= reach * reach;
}

std::vector<Cell> near(const Discovered& d, Point c, double reach) {
  // A cell is in reach when its nearest point is: the minimap's disc shows any cell it touches.
  std::vector<Cell> out;
  const auto lo = std::int32_t(std::floor(c.x - reach)), hi = std::int32_t(std::floor(c.x + reach));
  for (auto it = d.columns.lower_bound(lo); it != d.columns.end() && it->first <= hi; ++it)
    for (auto y : it->second) {
      const Point q{std::clamp(c.x, double(it->first), it->first + 1.0), std::clamp(c.y, double(y), y + 1.0)};
      if (within(c, q, reach)) out.push_back({it->first, y});
    }
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
