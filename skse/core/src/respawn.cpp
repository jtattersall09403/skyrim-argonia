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

std::vector<PlaceId> newly_cleared(std::span<const Roster> roster, std::span<const ActorId> dead,
                                   const ClearedSet& cleared) {
  std::vector<PlaceId> places, alive;
  for (const auto& r : roster) {
    if (!gen::kRespawnClasses[std::size_t(r.cls)].until_cleared || !r.place || cleared.contains(r.place)) continue;
    if (std::find(places.begin(), places.end(), r.place) == places.end()) places.push_back(r.place);
    if (std::find(dead.begin(), dead.end(), r.actor) == dead.end()) alive.push_back(r.place);
  }
  std::erase_if(places, [&](PlaceId p) { return std::find(alive.begin(), alive.end(), p) != alive.end(); });
  return places;
}

}  // namespace argonia::core::respawn
