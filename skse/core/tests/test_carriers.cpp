// L2: P1 carriers (76 §118, §121): damage position and Strength per hand, the bow and hand-to-hand exceptions, burden
// and soft requirements on stamina, armour bands per class, mitigation at the reference, over the five builds.
#include "check.h"
#include "builds.h"
#include "argonia/core/carriers.h"

using namespace argonia::core;
using namespace argonia::core::carriers;
using argonia::test::builds;

namespace {

std::size_t armour_index(SkillId s) {
  for (std::size_t i = 0; i < gen::kArmourSkills.size(); ++i)
    if (gen::kArmourSkills[i].skill == s) return i;
  return 0;
}

void marsh_hand_reference() {
  Sheet s = argonia::test::marsh_hand();
  Effective e = Effective::of(s);
  Carriers c = compute(s, e, BurdenTier::mid, {SkillId::longBlade}, {});
  CHECK_NEAR(c.right.damage_position, 0.85215275, 1e-7);
  CHECK_NEAR(c.right.strength_term, 1.0, 1e-12);  // neutral at Strength 50
  CHECK_NEAR(c.right.stamina_mult, 0.91088544 * 1.08, 1e-7);
  CHECK_NEAR(c.right.wear_mult, 0.79712967, 1e-7);
  CHECK_NEAR(c.left.damage_position, 0, 1e-12);  // empty hand
  // Steel rates 50 raw; Heavy Armor 45 makes it 47.51 and 24.06 % against a 24-damage blow (76 §116).
  const double ar = 50 * c.armour_rating_mult[armour_index(SkillId::heavyArmor)];
  CHECK_NEAR(ar, 47.5128, 1e-3);
  CHECK_NEAR(mitigation(ar, 24), 0.2406, 1e-4);
  CHECK_NEAR(mitigation(50, 24), 0.2500, 1e-3);  // the old reference: 25.0 %
  CHECK_NEAR(c.block_stability, 0.95, 1e-12);    // the Block band capped
  CHECK_NEAR(c.guard_stamina_mult, 0.95153603, 1e-7);
}

void strength_exceptions() {
  for (const auto& b : builds) {
    Effective e = Effective::of(b.sheet);
    const double want = (b.sheet.a[AttrId::strength] + 50) / 100;
    Carriers c = compute(b.sheet, e, BurdenTier::fast, {SkillId::axe}, {SkillId::handToHand});
    CHECK_NEAR(c.right.strength_term, want, 1e-12);
    CHECK_NEAR(c.left.strength_term, 1.0, 1e-12);  // hand-to-hand: no Strength
    Carriers bow = compute(b.sheet, e, BurdenTier::fast, {SkillId::marksman, true}, {});
    CHECK_NEAR(bow.right.strength_term, 1.0, 1e-12);
    CHECK(c.right.damage_position >= 0.4 && c.right.damage_position <= 1.0);
  }
  CHECK_NEAR(strength_term(0), 0.5, 1e-12);
  CHECK_NEAR(strength_term(100), 1.5, 1e-12);  // S14a's 0.5 : 1.5
}

void soft_requirements() {
  CHECK_NEAR(soft_requirement_mult(0), 1.0, 1e-12);
  CHECK_NEAR(soft_requirement_mult(10), 1.7, 1e-12);
  CHECK_NEAR(soft_requirement_mult(20), 2.4, 1e-12);
  CHECK_NEAR(soft_requirement_mult(80), 2.4, 1e-12);  // capped at d = 20
  CHECK_NEAR(soft_requirement_mult(-5), 1.0, 1e-12);
  Sheet s = argonia::test::marsh_hand();
  Carriers c = compute(s, Effective::of(s), BurdenTier::fat, {SkillId::longBlade, false, 20}, {});
  CHECK_NEAR(c.right.stamina_mult, 0.91088544 * 1.2 * 2.4, 1e-7);
}

void armour_classes_and_unarmored() {
  Sheet s = argonia::test::make(50, 50, 50, 50, 50, 50, 50, 50, 50, 1);
  for (auto k : {SkillId::lightArmor, SkillId::mediumArmor, SkillId::heavyArmor}) s.s[k] = 100;
  s.s[SkillId::unarmored] = 100;
  Carriers c = compute(s, Effective::of(s), BurdenTier::mid, {}, {});
  CHECK_NEAR(c.armour_rating_mult[armour_index(SkillId::lightArmor)], 0.75 * 1.2, 1e-12);
  CHECK_NEAR(c.armour_rating_mult[armour_index(SkillId::mediumArmor)], 0.9 * 1.2, 1e-12);
  CHECK_NEAR(c.armour_rating_mult[armour_index(SkillId::heavyArmor)], 1.2, 1e-12);
  CHECK_NEAR(c.armour_rating_mult[armour_index(SkillId::unarmored)], 0, 1e-12);
  CHECK_NEAR(c.unarmored_rating_per_slot, 65, 1e-9);  // 0.0065 x skill^2
  CHECK_NEAR(mitigation(-10, 24), 0, 1e-12);
  CHECK(mitigation(1e6, 0) < 1.0);  // never reaches 1
}

}  // namespace

int main() {
  marsh_hand_reference();
  strength_exceptions();
  soft_requirements();
  armour_classes_and_unarmored();
  return TEST_MAIN_RESULT("core.carriers");
}
