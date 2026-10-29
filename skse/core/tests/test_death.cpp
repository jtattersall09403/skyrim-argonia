// L2: death and the pile (76 §120.3, §126; S17a's reads): one pile, replaced by a second death, taken whole within
// 2 m ground distance in the same cell, and the `death` family payload.
#include "check.h"
#include "argonia/core/death.h"

using namespace argonia::core::death;

int main() {
  const Pos camp{0, 0, 0, 1}, spot{100, 50, 4, 1};
  Outcome o = on_death(120, spot, camp);
  CHECK(o.pile && o.pile->vastei == 120 && o.pile->at == spot);
  CHECK(o.carried == 0 && o.wake == camp && o.counts_as_rest);
  CHECK(!on_death(0, spot, camp).pile);  // nothing carried: no pile, and the old one is gone

  const Pile p = *o.pile;
  CHECK(take(p, {101.5, 50, 4, 1}) == 120.0);   // 1.5 m
  CHECK(take(p, {101.2, 51.2, 4, 1}) == 120.0); // 1.70 m
  CHECK(!take(p, {102.5, 50, 4, 1}));           // 2.5 m
  CHECK(take(p, {100, 50, 30, 1}) == 120.0);    // ground distance: height does not count
  CHECK(!take(p, {100, 50, 4, 2}));             // another cell
  CHECK(take(p, {103, 50, 4, 1}, 5) == 120.0);
  CHECK_NEAR(ground_distance({0, 0, 0, 0}, {3, 4, 9, 0}), 5, 1e-12);

  Outcome second = on_death(30, {5, 5, 0, 1}, camp);  // a second death replaces the pile
  CHECK(second.pile->vastei == 30);

  State s{p, camp};
  auto back = decode(encode(s));
  CHECK(back && *back == s);
  State empty{};
  CHECK(decode(encode(empty)) == empty);
  auto b = encode(s);
  b[0] = 2;  // a flag that is not 0 or 1
  CHECK(!decode(b));
  auto t = encode(s);
  t.pop_back();
  CHECK(!decode(t));
  return TEST_MAIN_RESULT("core.death");
}
