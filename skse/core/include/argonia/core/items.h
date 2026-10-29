// Item condition (76 §121.6, native map G25.2): 0 to max per instance, worn by hits, blows taken, use and burning;
// a weapon at 0 refuses the attack and does full damage above 0; worn armour guards in proportion, never below
// the floor; a repair stroke restores the Smithing band, up to the ceiling.
#pragma once
#include "argonia/core/cosave.h"
#include "argonia/core/tables_sheet.h"

#include <cstdint>
#include <map>
#include <optional>
#include <span>

namespace argonia::core::items {

using gen::WearKind;
using InstanceId = std::uint64_t;  // the instance's unique id (how instances are told apart: S25b)

struct ItemState {
  double condition = 0;
  double max = 0;                   // item_condition.max
  std::optional<double> wear_per_use;  // item_condition.wear_per_use
  bool operator==(const ItemState&) const = default;
};

// Condition lost: damage kinds lose amount x wear-per-damage x the wielder's wear band; use loses the item's own
// wear per use (or the default) per use; burn loses per second. `amount` is damage, uses or seconds.
double wear(const ItemState& it, WearKind kind, double amount, double skill_wear_band = 1);
ItemState worn(const ItemState& it, WearKind kind, double amount, double skill_wear_band = 1);
bool usable(const ItemState& it);
double armour_effectiveness(const ItemState& it);
// One stroke's condition (the Smithing repairPerStroke band at the score), and the item after it.
double repair_stroke(double smithing_score);
ItemState repaired(const ItemState& it, double smithing_score);

inline constexpr std::uint32_t kItemsType = cosave::fourcc("ITEM");
using Table = std::map<InstanceId, ItemState>;
cosave::Bytes encode(const Table& t);
std::optional<Table> decode(std::span<const std::uint8_t> b);

}  // namespace argonia::core::items
