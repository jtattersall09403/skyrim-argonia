// L2: respawn on rest (76 §126): onRest resets, never does not, untilCleared stops once its place is cleared.
#include "check.h"
#include "argonia/core/respawn.h"

#include <vector>

using namespace argonia::core::respawn;

int main() {
  const std::vector<Roster> roster{{1, RespawnClass::onRest, 10}, {2, RespawnClass::never, 10},
                                   {3, RespawnClass::untilCleared, 10}, {4, RespawnClass::untilCleared, 11}};
  CHECK((to_reset(roster, {}) == std::vector<ActorId>{1, 3, 4}));
  CHECK((to_reset(roster, {{10}}) == std::vector<ActorId>{1, 4}));
  CHECK((to_reset(roster, {{10, 11}}) == std::vector<ActorId>{1}));
  CHECK(to_reset({}, {}).empty());
  CHECK(class_named("onRest") == RespawnClass::onRest);
  CHECK(class_named("untilCleared") == RespawnClass::untilCleared);
  CHECK(!class_named("sometimes"));
  return TEST_MAIN_RESULT("core.respawn");
}
