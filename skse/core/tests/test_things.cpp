// L2: the thing table (1.4): LF83's well head and mortar tub set their flags when activated, the ledger when read;
// a record met the other way, or not a quest thing, sets nothing; the generated table is sorted for the lookup.
#include "check.h"
#include "argonia/core/things.h"

#include <algorithm>

using namespace argonia::core;
using namespace argonia::core::things;

int main() {
  const auto* well = hook_for("thing.lf83.well-head", Hook::activate);
  CHECK(well && well->flag == "flag.lf83.crack-seen" && well->quest == "quest.local.lf83");
  const auto* tub = hook_for("thing.lf83.mortar-tub", Hook::activate);
  CHECK(tub && tub->flag == "flag.lf83.tub-seen");
  const auto* ledger = hook_for("document.station-water-ledger", Hook::read);
  CHECK(ledger && ledger->flag == "flag.lf83.ledger-read");
  CHECK(!hook_for("document.station-water-ledger", Hook::activate));  // taking the book is not reading it
  CHECK(!hook_for("thing.lf83.well-head", Hook::read));
  CHECK(!hook_for("item.lf83.clay-basket", Hook::activate));
  CHECK(!hook_for("", Hook::read));
  CHECK(std::is_sorted(gen::kThingHooks.begin(), gen::kThingHooks.end(),
                       [](const gen::ThingHookRow& a, const gen::ThingHookRow& b) { return a.record < b.record; }));
  return TEST_MAIN_RESULT("core.things");
}
