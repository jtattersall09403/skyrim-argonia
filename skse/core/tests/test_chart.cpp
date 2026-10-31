// L2: the chart's revealed cells (1.2 §e): a cell reveals once, the set only grows, out-of-range cells are refused,
// the CHRT payload round-trips and a broken one (falling keys, a short or padded payload) is refused.
#include "check.h"
#include "argonia/core/chart.h"

#include <algorithm>
#include <cmath>

using namespace argonia::core::chart;

int main() {
  Discovered d;
  CHECK(count(d) == 0 && cells(d).empty());
  CHECK(reveal(d, {-56, 11}));
  CHECK(!reveal(d, {-56, 11}));  // once
  CHECK(reveal(d, {-56, 12}));
  CHECK(reveal(d, {3, -4}));
  CHECK(!reveal(d, {kCellMax + 1, 0}));
  CHECK(!reveal(d, {0, kCellMin - 1}));
  CHECK(count(d) == 3);
  CHECK(revealed(d, {-56, 12}) && !revealed(d, {-55, 12}));
  CHECK((cells(d) == std::vector<Cell>{{-56, 11}, {-56, 12}, {3, -4}}));
  CHECK(migrations().empty());  // version 1: nothing to lift yet

  auto back = decode(encode(d));
  CHECK(back && *back == d);
  CHECK(decode(encode(Discovered{})) == Discovered{});

  auto bad = encode(d);
  CHECK(!decode({bad.data(), bad.size() - 1}));  // short
  bad.push_back(0);
  CHECK(!decode(bad));  // padded
  // The second column's x written below the first: columns must rise.
  argonia::core::cosave::Writer w;
  w.u32(2); w.i32(5); w.u32(0); w.i32(4); w.u32(0);
  CHECK(!decode(w.take()));
  argonia::core::cosave::Writer v;  // rows must rise
  v.u32(1); v.i32(5); v.u32(2); v.i32(1); v.i32(1);
  CHECK(!decode(v.take()));

  // 1.12 §5: a marker shows only once discovered (Visible alone is known, not reached).
  CHECK(!marker_discovered(0) && !marker_discovered(kMarkerVisible) && !marker_discovered(kMarkerCanTravelTo));
  CHECK(marker_discovered(kMarkerVisible | kMarkerCanTravelTo) && marker_discovered(0xFF));
  CHECK(marker_kind(1) == "settlement" && marker_kind(8) == "ruin" && marker_kind(4) == "lair");
  CHECK(marker_kind(33) == "transit" && marker_kind(34) == "sacred" && marker_kind(11) == "civic");
  CHECK(marker_kind(0).empty() && marker_kind(62).empty() && marker_kind(65).empty());
  CHECK(marker_kind(999) == "civic");
  // Skyrim units -> cell units (4096 a cell), the cell a point is in (floor, so -0.5 is cell -1).
  CHECK((cell_units(4096 * 3 + 2048, -4096 * 2) == Point{3.5, -2}));
  CHECK((cell_of({-0.5, 2.999}) == Cell{-1, 2}));
  // The heading: 0 north, clockwise, any number of turns, never 360.
  const double pi = 3.14159265358979323846;
  CHECK(heading_deg(0) == 0);
  CHECK(std::abs(heading_deg(pi * 0.75) - 135) < 1e-9);
  CHECK(std::abs(heading_deg(-pi / 2) - 270) < 1e-9);
  CHECK(std::abs(heading_deg(5 * pi) - 180) < 1e-9);
  CHECK(heading_deg(2 * pi) < 1e-9);
  // The minimap's reach: a circle; a cell counts when its nearest point is inside.
  Discovered m;
  for (int x = -10; x <= 10; ++x) for (int y = -10; y <= 10; ++y) reveal(m, {x, y});
  auto in = near(m, {0.5, 0.5}, 2);
  CHECK(!in.empty());
  for (auto c : in) CHECK(within({0.5, 0.5}, {std::clamp(0.5, double(c.x), c.x + 1.0), std::clamp(0.5, double(c.y), c.y + 1.0)}, 2));
  CHECK(std::find(in.begin(), in.end(), Cell{2, 0}) != in.end());   // 1.5 away
  CHECK(std::find(in.begin(), in.end(), Cell{3, 0}) == in.end());   // 2.5 away
  CHECK(std::find(in.begin(), in.end(), Cell{2, 2}) == in.end());   // the corner: 1.5 * sqrt 2 > 2
  CHECK(near(Discovered{}, {0, 0}).empty());
  CHECK(within({0, 0}, {3, 4}, 5) && !within({0, 0}, {3, 4.01}, 5));
  return TEST_MAIN_RESULT("core.chart");
}
