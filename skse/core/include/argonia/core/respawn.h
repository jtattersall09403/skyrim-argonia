// Respawn on rest (76 §126, decision 0031; owner 2026-10-30): `onRest` actors reset at each rest and at each wake
// from death; `never` actors (named people, bosses, quest actors, everyone homed in a clearable place) never do.
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

struct Roster { ActorId actor; RespawnClass cls; };

std::optional<RespawnClass> class_named(std::string_view id);  // npc_statblock.respawn's values

// The actors a rest resurrects and returns to their editor location, in roster order.
std::vector<ActorId> to_reset(std::span<const Roster> roster);

}  // namespace argonia::core::respawn
