// L2: the level sitting (76 §120.4): the cost formula, the per-sitting cap, the purchase cap, too dear, carried
// vastei, S16c's Endurance point and the no-deferral-advantage shape.
#include "check.h"
#include "builds.h"
#include "argonia/core/sitting.h"

using namespace argonia::core;
using namespace argonia::core::sitting;

int main() {
  CHECK_NEAR(cost(AttrId::endurance, 1, 2, 50), 202.79423394, 1e-6);
  CHECK_NEAR(cost(AttrId::endurance, 2, 2, 51), 310.30559706, 1e-6);
  CHECK(cost(AttrId::endurance, 1, 20, 50) > cost(AttrId::endurance, 1, 2, 50));  // deferral never pays
  CHECK(cost(AttrId::endurance, 1, 2, 80) > cost(AttrId::endurance, 1, 2, 50));   // dearer as it rises

  Sheet s = argonia::test::marsh_hand();
  s.level = 1;
  CHECK(open(s, 1000, 0).error() == Refusal::no_pending_level);
  auto st = open(s, 5000, 1);
  CHECK(st.has_value() && st->sheet.level == 2);

  // S16c: one Endurance point costs cost(End, 1, level) and health recomputes from the formula.
  const double price = cost(*st, AttrId::endurance);
  auto one = buy(*st, AttrId::endurance);
  CHECK(one.has_value());
  CHECK_NEAR(one->vastei, 5000 - price, 1e-9);
  CHECK_NEAR(one->sheet.a[AttrId::endurance], 51, 1e-12);
  CHECK_NEAR(derive(one->sheet, Effective::of(one->sheet), 0).health, (50 + 51) * 0.5 + 2 * 5.1, 1e-9);

  // At most five points in one attribute per sitting.
  auto cur = *one;
  for (int i = 0; i < 4; ++i) {
    auto next = buy(cur, AttrId::endurance);
    CHECK(next.has_value());
    if (next) cur = *next;
  }
  CHECK(cur.bought[idx(AttrId::endurance)] == 5);
  CHECK(buy(cur, AttrId::endurance).error() == Refusal::at_cap_this_sitting);
  CHECK(buy(cur, AttrId::strength).has_value());  // another attribute still sells

  auto poor = open(s, 10, 1);
  CHECK(buy(*poor, AttrId::agility).error() == Refusal::too_dear);
  Sheet top = s;
  top.a[AttrId::agility] = 100;
  CHECK(buy(*open(top, 1e9, 1), AttrId::agility).error() == Refusal::at_purchase_cap);

  Closed c = close(cur);
  CHECK_NEAR(c.vastei, cur.vastei, 1e-12);  // unspent vastei carries over
  CHECK(c.sheet.level == 2);
  CHECK(std::string(to_string(Refusal::too_dear)) == "not enough vastei");
  return TEST_MAIN_RESULT("core.sitting");
}
