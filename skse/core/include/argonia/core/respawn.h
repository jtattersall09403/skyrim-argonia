// Respawn on rest (76 §126, decision 0031): generic enemies reset at each rest and at each wake from death; named
// people, bosses and quest actors never do; a cleared place stops its `untilCleared` population.
#pragma once
#include "argonia/core/tables_progression.h"

#include <cstdint>
#include <optional>
#include <span>
#include <string_view>
#include <vector>

namespace argonia::core::respawn {

using gen::RespawnClass;
using ActorId = std::uint32_t;  // the placed reference's FormID
using PlaceId = std::uint32_t;  // the location's FormID

struct Roster { ActorId actor; RespawnClass cls; PlaceId place; };

struct ClearedSet {
  std::vector<PlaceId> places;
  bool contains(PlaceId p) const;
};

std::optional<RespawnClass> class_named(std::string_view id);  // npc_statblock.respawn's values

// The actors a rest resurrects and returns to their editor location, in roster order.
std::vector<ActorId> to_reset(std::span<const Roster> roster, const ClearedSet& cleared);

}  // namespace argonia::core::respawn
