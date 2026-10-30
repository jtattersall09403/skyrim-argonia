// L2: respawn on rest (76 §126; owner 2026-10-30): onRest resets, never does not, untilCleared resets until its
// place is cleared; a place is cleared when all its untilCleared actors are dead at once.
#include "check.h"
#include "argonia/core/respawn.h"

#include <vector>

using namespace argonia::core::respawn;

int main() {
  const std::vector<Roster> roster{{1, RespawnClass::onRest}, {2, RespawnClass::never},
                                   {3, RespawnClass::untilCleared, 10}, {4, RespawnClass::untilCleared, 11},
                                   {5, RespawnClass::untilCleared, 10}};
  CHECK((to_reset(roster, {}) == std::vector<ActorId>{1, 3, 4, 5}));
  CHECK((to_reset(roster, {{10}}) == std::vector<ActorId>{1, 4}));
  CHECK((to_reset(roster, {{10, 11}}) == std::vector<ActorId>{1}));
  CHECK(to_reset({}, {}).empty());

  // One of two dead: not cleared, so it comes back; both dead at once: cleared, and neither comes back.
  const std::vector<ActorId> one{3}, both{3, 5}, all{1, 2, 3, 4, 5};
  CHECK(newly_cleared(roster, one, {}).empty());
  CHECK((newly_cleared(roster, both, {}) == std::vector<PlaceId>{10}));
  CHECK((newly_cleared(roster, all, {}) == std::vector<PlaceId>{10, 11}));
  CHECK((newly_cleared(roster, all, {{10}}) == std::vector<PlaceId>{11}));  // already cleared: not again
  // onRest and never actors never clear a place; an untilCleared actor with no place never does either.
  CHECK(newly_cleared(std::vector<Roster>{{1, RespawnClass::onRest, 12}, {2, RespawnClass::never, 12}},
                      all, {}).empty());
  CHECK(newly_cleared(std::vector<Roster>{{7, RespawnClass::untilCleared, 0}}, std::vector<ActorId>{7}, {}).empty());

  CHECK(class_named("onRest") == RespawnClass::onRest);
  CHECK(class_named("never") == RespawnClass::never);
  CHECK(class_named("untilCleared") == RespawnClass::untilCleared);
  CHECK(!class_named("sometimes"));
  return TEST_MAIN_RESULT("core.respawn");
}
