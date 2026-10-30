// Respawn on rest (76 §126, decision 0031; owner 2026-10-30): `onRest` actors reset at each rest and at each wake
// from death; `untilCleared` actors (homed in a clearable place) do too until their place is cleared, then never;
// `never` actors (named people, bosses, quest actors, unique creatures) never do. A place is cleared when every
// `untilCleared` actor of it is dead at the same moment; the adapter then sets the LCTN's native cleared flag.
// Containers and placed treasure are not actors, so a rest never touches them.
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
using PlaceId = std::uint32_t;  // the clearable place's LCTN FormID (0: none)

struct Roster { ActorId actor; RespawnClass cls; PlaceId place = 0; };

struct ClearedSet {
  std::vector<PlaceId> places;
  bool contains(PlaceId p) const;
};

std::optional<RespawnClass> class_named(std::string_view id);  // npc_statblock.respawn's values

// The actors a rest resurrects and returns to their editor location, in roster order.
std::vector<ActorId> to_reset(std::span<const Roster> roster, const ClearedSet& cleared);

// The places not yet cleared whose `untilCleared` actors are all dead now (a place with none is never cleared).
std::vector<PlaceId> newly_cleared(std::span<const Roster> roster, std::span<const ActorId> dead,
                                   const ClearedSet& cleared);

}  // namespace argonia::core::respawn
