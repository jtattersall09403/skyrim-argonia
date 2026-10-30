// L2: the QSTA family's state (flags, counters, deeds): set and read by world id, the unset spellings, deeds never
// below zero, and encode/decode back to the same state (the schema round trip is test_roundtrip's).
#include "check.h"
#include "argonia/core/quest_state.h"

using namespace argonia::core::quest_state;

int main() {
  State s;
  CHECK(!flag(s, "flag.lf83.terms-settled"));
  set_flag(s, "flag.lf83.terms-settled", true);
  CHECK(flag(s, "flag.lf83.terms-settled") && !flag(s, "flag.lf83.ford-tasted"));
  set_flag(s, "flag.lf83.terms-settled", false);
  CHECK(s.flags.empty());
  add_counter(s, "counter.x", 3);
  add_counter(s, "counter.x", -1);
  CHECK(counter(s, "counter.x") == 2 && counter(s, "counter.y") == 0);
  add_deed(s, "faction.a", "deed.helped");
  add_deed(s, "faction.a", "deed.helped", 2);
  add_deed(s, "faction.a", "deed.robbed", -5);
  CHECK(deeds(s, "faction.a", "deed.helped") == 3 && deeds(s, "faction.a", "deed.robbed") == 0);
  set_flag(s, "flag.lf83.crack-seen", true);
  auto back = decode(encode(s));
  CHECK(back && *back == s);
  auto bytes = encode(s);
  bytes.pop_back();
  CHECK(!decode(bytes));
  CHECK(key("flag.lf83.terms-settled") != key("flag.lf83.ford-tasted"));
  static_assert(key("") == 2166136261u);
  return TEST_MAIN_RESULT("core.quest_state");
}
