#include "argonia/core/respawn.h"

namespace argonia::core::respawn {

std::optional<RespawnClass> class_named(std::string_view id) {
  for (std::size_t i = 0; i < gen::kRespawnClassCount; ++i)
    if (gen::kRespawnClassNames[i] == id) return RespawnClass(i);
  return std::nullopt;
}

std::vector<ActorId> to_reset(std::span<const Roster> roster) {
  std::vector<ActorId> out;
  for (const auto& r : roster) {
    if (gen::kRespawnClasses[std::size_t(r.cls)].on_rest) out.push_back(r.actor);
  }
  return out;
}

}  // namespace argonia::core::respawn
