// L2: item condition (76 §121.6, S25b's reads): wear by kind, broken at 0 and whole above, armour effectiveness
// and its floor, repair strokes and the ceiling, and the `items` family payload.
#include "check.h"
#include "argonia/core/items.h"

using namespace argonia::core::items;

int main() {
  const ItemState sword{100, 100, std::nullopt}, hammer{100, 100, 4.0}, pick{25, 25, std::nullopt}, torch{240, 240, std::nullopt};
  CHECK_NEAR(wear(sword, WearKind::hit, 30, 0.8), 2.4, 1e-12);
  CHECK_NEAR(wear(sword, WearKind::struck, 30), 3.0, 1e-12);
  CHECK_NEAR(wear(hammer, WearKind::use, 1), 4.0, 1e-12);  // 25 strokes of a 100 hammer
  ItemState h = hammer;
  for (int i = 0; i < 25; ++i) h = worn(h, WearKind::use, 1);
  CHECK_NEAR(h.condition, 0, 1e-12);
  CHECK(!usable(h));
  CHECK_NEAR(wear(pick, WearKind::use, 1), 1.0, 1e-12);    // the default: 25 uses
  CHECK_NEAR(wear(torch, WearKind::burn, 60), 60.0, 1e-12);
  CHECK_NEAR(wear(sword, WearKind::hit, -5), 0, 1e-12);
  CHECK_NEAR(worn(sword, WearKind::struck, 5000).condition, 0, 1e-12);  // never below 0

  ItemState chipped{0.01, 100, std::nullopt};
  CHECK(usable(chipped) && !usable({0, 100, std::nullopt}));
  CHECK_NEAR(armour_effectiveness({50, 100, std::nullopt}), 0.5, 1e-12);
  CHECK_NEAR(armour_effectiveness({5, 100, std::nullopt}), 0.1, 1e-12);  // the floor
  CHECK_NEAR(armour_effectiveness({0, 0, std::nullopt}), 0.1, 1e-12);

  CHECK_NEAR(repair_stroke(0), 6, 1e-12);
  CHECK_NEAR(repair_stroke(100), 22, 1e-12);
  CHECK_NEAR(repaired({50, 100, std::nullopt}, 0).condition, 56, 1e-12);
  CHECK_NEAR(repaired({95, 100, std::nullopt}, 100).condition, 100, 1e-12);  // up to the ceiling

  Table t{{1, sword}, {0xFFFFFFFF01ull, hammer}};
  auto back = decode(encode(t));
  CHECK(back && *back == t);
  auto bad = encode({{1, {150, 100, std::nullopt}}});  // condition above max
  CHECK(!decode(bad));
  auto trunc = encode(t);
  trunc.pop_back();
  CHECK(!decode(trunc));
  return TEST_MAIN_RESULT("core.items");
}
