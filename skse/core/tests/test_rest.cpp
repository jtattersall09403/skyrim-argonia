// L2: where a rest is allowed (76 §126, 0039 S3) and what it does: the rested entry by bed tier and its expiry.
#include "check.h"
#include "argonia/core/rest.h"

#include <string>

using namespace argonia::core::rest;

int main() {
  Context wild;
  wild.at = {10, 20, 3, 7};
  CHECK(can_rest(wild).verdict == Verdict::rest);
  Outcome o = on_rest(wild, 1);
  CHECK(o.tier == BedTier::camp && !o.rested);  // a camp grants nothing beyond the sitting
  CHECK(o.wake_point == wild.at && o.save && o.restore_pools && o.respawn && o.open_sitting);
  CHECK(!on_rest(wild, 0).open_sitting);

  Context c = wild; c.in_combat = true;
  CHECK(can_rest(c).verdict == Verdict::refused && can_rest(c).why == Why::in_combat);
  c = wild; c.hunted = true; CHECK(can_rest(c).why == Why::hunted);
  c = wild; c.in_dungeon = true; CHECK(can_rest(c).why == Why::in_dungeon);
  c = wild; c.hostiles_near = true; CHECK(can_rest(c).why == Why::not_calm);
  c = wild; c.in_settlement = true;
  CHECK(can_rest(c).verdict == Verdict::wait_only);
  Outcome w = on_rest(c, 1);
  CHECK(!w.save && !w.wake_point && !w.open_sitting && !w.respawn);  // waiting passes time only
  c.bed = BedTier::camp; CHECK(can_rest(c).verdict == Verdict::wait_only);  // S16c: a bed spot in town is refused
  c.bed = BedTier::rented; c.now = 100;
  Outcome inn = on_rest(c, 0);
  CHECK(inn.ruling.verdict == Verdict::rest && inn.tier == BedTier::rented);
  CHECK(inn.rested && inn.rested->xp_mult == 1.05 && inn.rested->until == 108);
  CHECK(xp_multiplier(inn.rested, 107.9) == 1.05);
  CHECK(xp_multiplier(inn.rested, 108) == 1.0);
  CHECK(xp_multiplier(std::nullopt, 0) == 1.0);
  c.bed = BedTier::owned; CHECK(on_rest(c, 0).rested->xp_mult == 1.08);
  c.hunted = true; c.bed = BedTier::owned;  // hunted beats an owned bed
  CHECK(can_rest(c).why == Why::hunted);
  CHECK(std::string(to_string(Why::hunted)).find("hunted") != std::string::npos);
  return TEST_MAIN_RESULT("core.rest");
}
