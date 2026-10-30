// L2: respawn on rest (76 §126; owner 2026-10-30): onRest resets, never does not; untilCleared is retired.
#include "check.h"
#include "argonia/core/respawn.h"

#include <vector>

using namespace argonia::core::respawn;

int main() {
  const std::vector<Roster> roster{{1, RespawnClass::onRest}, {2, RespawnClass::never}, {3, RespawnClass::onRest}};
  CHECK((to_reset(roster) == std::vector<ActorId>{1, 3}));
  CHECK(to_reset({}).empty());
  CHECK((to_reset(std::vector<Roster>{{2, RespawnClass::never}}).empty()));
  CHECK(class_named("onRest") == RespawnClass::onRest);
  CHECK(class_named("never") == RespawnClass::never);
  CHECK(!class_named("untilCleared"));  // retired (owner 2026-10-30): clearable places' actors are `never`
  CHECK(!class_named("sometimes"));
  return TEST_MAIN_RESULT("core.respawn");
}
