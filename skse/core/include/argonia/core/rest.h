// Rest (76 §126, decision 0039 S3): camp anywhere calm in the wild; only wait in a settlement without a bed you own
// or rent; never in a dungeon, in combat or while hunted. A rest saves, banks a pending level, opens the sitting,
// restores the pools, respawns and becomes the wake point; a bed grants a rested entry.
#pragma once
#include "argonia/core/tables_progression.h"

#include <optional>

namespace argonia::core::rest {

using gen::BedTier;

struct Pos { double x = 0, y = 0, z = 0; std::uint32_t cell = 0; bool operator==(const Pos&) const = default; };

struct Context {
  bool in_combat = false;
  bool hunted = false;           // any observer searching for the player, whatever its notice has decayed to
  bool in_settlement = false;
  bool in_dungeon = false;
  bool hostiles_near = false;    // not calm
  std::optional<BedTier> bed;    // the bed or camp spot activated; none: resting on the ground
  Pos at;
  double now = 0;                // game hours
};

enum class Verdict { rest, wait_only, refused };
enum class Why { ok, in_combat, hunted, in_dungeon, not_calm, settlement_needs_bed };
struct Ruling { Verdict verdict; Why why; };
const char* to_string(Why w);

Ruling can_rest(const Context& ctx);

struct Rested { double xp_mult; double until; };  // the stack's rested entry
struct Outcome {
  Ruling ruling{Verdict::refused, Why::ok};
  BedTier tier = BedTier::camp;
  std::optional<Rested> rested;  // a bed of a tier with hours
  std::optional<Pos> wake_point; // only a rest taken becomes the wake point
  bool save = false, restore_pools = false, respawn = false, open_sitting = false;
};
// What a rest does; a refused or wait-only rest changes nothing but time.
Outcome on_rest(const Context& ctx, int pending_levels);

// The rested multiplier at game hour `now`, 1 once it ends.
double xp_multiplier(const std::optional<Rested>& r, double now);

}  // namespace argonia::core::rest
