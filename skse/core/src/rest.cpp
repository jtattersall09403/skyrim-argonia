#include "argonia/core/rest.h"

namespace argonia::core::rest {

const char* to_string(Why w) {
  switch (w) {
    case Why::ok: return "ok";
    case Why::in_combat: return "You cannot rest in combat.";
    case Why::hunted: return "You cannot rest while you are hunted.";
    case Why::in_dungeon: return "You cannot rest here.";
    case Why::not_calm: return "You cannot rest with enemies nearby.";
    case Why::settlement_needs_bed: return "You can only wait here; a bed you own or rent lets you rest.";
  }
  return "?";
}

Ruling can_rest(const Context& ctx) {
  if (ctx.in_combat) return {Verdict::refused, Why::in_combat};
  if (ctx.hunted) return {Verdict::refused, Why::hunted};
  if (ctx.in_dungeon) return {Verdict::refused, Why::in_dungeon};
  if (ctx.hostiles_near) return {Verdict::refused, Why::not_calm};
  if (ctx.in_settlement && (!ctx.bed || *ctx.bed == BedTier::camp)) return {Verdict::wait_only, Why::settlement_needs_bed};
  return {Verdict::rest, Why::ok};
}

Outcome on_rest(const Context& ctx, int pending_levels) {
  Outcome o;
  o.ruling = can_rest(ctx);
  if (o.ruling.verdict != Verdict::rest) return o;
  o.tier = ctx.bed.value_or(BedTier::camp);
  const auto& row = gen::kBedTiers[std::size_t(o.tier)];
  if (row.hours > 0) o.rested = Rested{row.xp_mult, ctx.now + row.hours};
  o.wake_point = ctx.at;
  o.save = o.restore_pools = o.respawn = true;
  o.open_sitting = pending_levels > 0;
  return o;
}

double xp_multiplier(const std::optional<Rested>& r, double now) {
  return r && now < r->until ? r->xp_mult : 1.0;
}

}  // namespace argonia::core::rest
