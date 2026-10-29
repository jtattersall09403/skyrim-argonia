#include "argonia/core/respawn.h"

#include <algorithm>

namespace argonia::core::respawn {

bool ClearedSet::contains(PlaceId p) const { return std::find(places.begin(), places.end(), p) != places.end(); }

std::optional<RespawnClass> class_named(std::string_view id) {
  for (std::size_t i = 0; i < gen::kRespawnClassCount; ++i)
    if (gen::kRespawnClassNames[i] == id) return RespawnClass(i);
  return std::nullopt;
}

std::vector<ActorId> to_reset(std::span<const Roster> roster, const ClearedSet& cleared) {
  std::vector<ActorId> out;
  for (const auto& r : roster) {
    const auto& row = gen::kRespawnClasses[std::size_t(r.cls)];
    if (!row.on_rest || (row.until_cleared && cleared.contains(r.place))) continue;
    out.push_back(r.actor);
  }
  return out;
}

}  // namespace argonia::core::respawn
