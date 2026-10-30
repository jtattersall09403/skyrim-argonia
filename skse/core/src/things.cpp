#include "argonia/core/things.h"

#include <algorithm>

namespace argonia::core::things {

const gen::ThingHookRow* hook_for(std::string_view record, Hook how) {
  const std::string_view want = how == Hook::activate ? "activate" : "read";
  auto it = std::lower_bound(gen::kThingHooks.begin(), gen::kThingHooks.end(), record,
                             [](const gen::ThingHookRow& r, std::string_view k) { return r.record < k; });
  return it != gen::kThingHooks.end() && it->record == record && it->hook == want ? &*it : nullptr;
}

}  // namespace argonia::core::things
