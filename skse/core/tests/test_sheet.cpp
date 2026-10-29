// L2: the sheet's derived values over the five builds (76 §117-§122), the burden thresholds and band lookups.
#include "check.h"
#include "builds.h"

using namespace argonia::core;
using argonia::test::builds;

namespace {

struct Want {
  double health, stamina, magicka, carry, ratio;
  BurdenTier tier;
  double walk, sprint, swim, jump, fall, breath, sreg, mreg, poise, climb;
  double drain;  // < 0: cannot climb
};

const Want want[] = {
    {100, 100, 140, 180, 0.25, BurdenTier::mid, 4.1625, 4.8285, 1.332, 1.43312, 3.2, 51.5, 24, 2.5, 25,
     1.1263379, 7.7442790},
    {44, 92, 140, 150, 0.0666667, BurdenTier::fast, 4.29975, 4.557735, 1.0192, 1.26776, 2.6, 40.25, 21.6, 2.5, 20,
     1.0357476, 7.2389025},
    {85, 88, 260, 120, 0.1666667, BurdenTier::fast, 4.168125, 4.501575, 1.064, 1.21264, 2.4, 40.75, 21.6, 4, 20,
     1.0032588, 7.4742615},
    {113, 140, 110, 240, 1.25, BurdenTier::overloaded, 1.71, 1.71, 0.896, 0, 2.8, 50.5, 20.4, 2, 17.5, 1.0671092, -1},
    {600, 300, 320, 330, 0, BurdenTier::fast, 5.625, 7.875, 2.4, 2.2048, 6, 85, 36, 5.5, 50, 1.375, 4.78125},
};

void five_builds() {
  for (std::size_t i = 0; i < std::size(builds); ++i) {
    const auto& b = builds[i];
    const auto& w = want[i];
    Derived d = derive(b.sheet, Effective::of(b.sheet), b.carried_kg);
    CHECK_NEAR(d.health, w.health, 1e-9);
    CHECK_NEAR(d.stamina, w.stamina, 1e-9);
    CHECK_NEAR(d.magicka, w.magicka, 1e-9);
    CHECK_NEAR(d.carry_kg, w.carry, 1e-9);
    CHECK_NEAR(d.burden_ratio, w.ratio, 1e-6);
    CHECK(d.burden == w.tier);
    CHECK_NEAR(d.walk_mps, w.walk, 1e-9);
    CHECK_NEAR(d.sprint_mps, w.sprint, 1e-9);
    CHECK_NEAR(d.swim_mps, w.swim, 1e-9);
    CHECK_NEAR(d.jump_apex_m, w.jump, 1e-9);
    CHECK_NEAR(d.safe_fall_m, w.fall, 1e-9);
    CHECK_NEAR(d.breath_s, w.breath, 1e-9);
    CHECK_NEAR(d.stamina_regen, w.sreg, 1e-9);
    CHECK_NEAR(d.magicka_regen, w.mreg, 1e-9);
    CHECK_NEAR(d.base_poise, w.poise, 1e-9);
    CHECK_NEAR(d.climb_mps, w.climb, 1e-6);
    CHECK(d.climb_drain_per_s.has_value() == (w.drain >= 0));
    if (d.climb_drain_per_s) CHECK_NEAR(*d.climb_drain_per_s, w.drain, 1e-6);
    CHECK(d.can_run == (w.tier != BurdenTier::overloaded));
    CHECK_NEAR(d.stamina_regen_delay_s, 1.05, 1e-12);
  }
}

void health_is_retroactive() {  // 76 §117.2: level 10, End 50 -> 70 gives 100 -> 130 at once
  Sheet s = argonia::test::marsh_hand();
  s.a[AttrId::endurance] = 70;
  CHECK_NEAR(derive(s, Effective::of(s), 0).health, 130.0, 1e-9);
}

void stamina_above_reference() {  // 296 at End 99, 300 at 100 (76 §121.2)
  Sheet s = argonia::test::marsh_hand();
  s.a[AttrId::endurance] = 99;
  CHECK_NEAR(derive(s, Effective::of(s), 0).stamina, 296.0, 1e-9);
}

void burden_thresholds() {
  CHECK(burden_tier(0) == BurdenTier::fast);
  CHECK(burden_tier(0.1999) == BurdenTier::fast);
  CHECK(burden_tier(0.2) == BurdenTier::mid);
  CHECK(burden_tier(0.35) == BurdenTier::fat);
  CHECK(burden_tier(0.9999) == BurdenTier::fat);
  CHECK(burden_tier(1.0) == BurdenTier::overloaded);
  CHECK(burden_tier(50) == BurdenTier::overloaded);
}

void zero_capacity_is_overloaded_only_when_carrying() {
  Sheet s = argonia::test::make(0, 0, 0, 0, 0, 0, 0, 0, 0, 1);
  Effective e = Effective::of(s);
  e.field[idx(StatField::carryWeight)] = -30;  // a drain to nothing
  CHECK(derive(s, e, 0).burden == BurdenTier::fast);
  CHECK(derive(s, e, 1).burden == BurdenTier::overloaded);
}

void bands_and_scores() {
  Sheet s = argonia::test::marsh_hand();
  Effective e = Effective::of(s);
  CHECK_NEAR(skill_score(SkillId::longBlade, e), 58.3333333, 1e-6);
  CHECK_NEAR(skill_score(SkillId::heavyArmor, e), 45.0, 1e-12);  // no score attribute: the skill itself
  CHECK_NEAR(*skill_band(SkillId::longBlade, Band::damagePosition, e), 0.85215275, 1e-7);
  CHECK(!skill_band(SkillId::heavyArmor, Band::damagePosition, e));  // a band the skill does not have
  s.s[SkillId::alchemy] = 30;
  s.a[AttrId::intelligence] = 40;
  CHECK_NEAR(skill_score(SkillId::alchemy, Effective::of(s)), (30 + 4) / 1.2, 1e-9);
}

}  // namespace

int main() {
  five_builds();
  health_is_retroactive();
  stamina_above_reference();
  burden_thresholds();
  zero_capacity_is_overloaded_only_when_carrying();
  bands_and_scores();
  return TEST_MAIN_RESULT("core.sheet");
}
