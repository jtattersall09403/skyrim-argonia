// L2: the chart's revealed cells (1.2 §e): a cell reveals once, the set only grows, out-of-range cells are refused,
// the CHRT payload round-trips and a broken one (falling keys, a short or padded payload) is refused.
#include "check.h"
#include "argonia/core/chart.h"

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
  return TEST_MAIN_RESULT("core.chart");
}
