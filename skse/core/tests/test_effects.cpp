// L2: the effect stack (76 §127): each op on each field kind, expiry, restore against damage, the resist cap,
// invalid entries refused, and S15b's Fortify Long Blade 10 for 60 s.
#include "check.h"
#include "builds.h"
#include "argonia/core/effects.h"

using namespace argonia::core;
using namespace argonia::core::effects;

namespace {

StatEffect fx(Field f, EffectOp op, double m, std::optional<double> until = std::nullopt) { return {f, op, m, until, 7}; }

void potion_for_sixty_seconds() {
  Sheet s = argonia::test::marsh_hand();
  Stack st{fx(Field::skill(SkillId::longBlade), EffectOp::fortify, 10, 60.0)};
  CHECK_NEAR(apply(s, st, 0).s[SkillId::longBlade], 70, 1e-12);
  CHECK_NEAR(apply(s, st, 59.9).s[SkillId::longBlade], 70, 1e-12);
  CHECK_NEAR(apply(s, st, 60).s[SkillId::longBlade], 60, 1e-12);  // ended at 60: base again
  CHECK(expire(st, 59) == 0);
  CHECK(expire(st, 60) == 1);
  CHECK(st.empty());
}

void attribute_ops() {
  Sheet s = argonia::test::marsh_hand();
  const Field end = Field::attr(AttrId::endurance);
  Stack st{fx(end, EffectOp::fortify, 20), fx(end, EffectOp::drain, 5), fx(end, EffectOp::damage, 30),
           fx(end, EffectOp::restore, 10), fx(end, EffectOp::ability, 1)};
  CHECK_NEAR(apply(s, st, 0).a[AttrId::endurance], 50 + 20 - 5 - 20 + 1, 1e-12);
  st.push_back(fx(end, EffectOp::restore, 50));  // restore heals damage only, never above
  CHECK_NEAR(apply(s, st, 0).a[AttrId::endurance], 66, 1e-12);
  Stack floor{fx(end, EffectOp::drain, 500)};
  CHECK_NEAR(apply(s, floor, 0).a[AttrId::endurance], 0, 1e-12);
  // Effective Endurance moves health through derive.
  Stack up{fx(end, EffectOp::fortify, 20)};
  CHECK_NEAR(derive(s, apply(s, up, 0), 0).health, 130, 1e-9);
}

void stat_fields() {
  Sheet s = argonia::test::marsh_hand();
  Stack st{fx(Field::stat(StatField::resistPoison), EffectOp::resist, 100),
           fx(Field::stat(StatField::resistPoison), EffectOp::resist, 50),
           fx(Field::stat(StatField::resistFire), EffectOp::resist, -100),
           fx(Field::stat(StatField::magickaMultiplier), EffectOp::fortify, 1.5),
           fx(Field::stat(StatField::staminaRegenMultiplier), EffectOp::ability, 1.25),
           fx(Field::stat(StatField::staminaRegenMultiplier), EffectOp::ability, 2),
           fx(Field::stat(StatField::poise), EffectOp::fortify, 25),
           fx(Field::stat(StatField::waterBreathing), EffectOp::ability, 1)};
  Effective e = apply(s, st, 0);
  CHECK_NEAR(e[StatField::resistPoison], 100, 1e-12);  // capped: immune
  CHECK_NEAR(e[StatField::resistFire], -100, 1e-12);   // a weakness stays negative
  CHECK_NEAR(e[StatField::staminaRegenMultiplier], 2.5, 1e-12);
  Derived d = derive(s, e, 0);
  CHECK_NEAR(d.magicka, 20 + (3 + 1.5) * 40, 1e-9);
  CHECK_NEAR(d.stamina_regen, 24 * 2.5, 1e-9);
  CHECK_NEAR(d.base_poise, 50, 1e-9);
  CHECK(d.unlimited_breath);
}

void invalid_entries_refused_and_skipped() {
  Sheet s = argonia::test::marsh_hand();
  StatEffect bad_resist = fx(Field::attr(AttrId::strength), EffectOp::resist, 10);
  StatEffect bad_restore = fx(Field::stat(StatField::health), EffectOp::restore, 60);
  StatEffect bad_factor = fx(Field::stat(StatField::magickaRegenMultiplier), EffectOp::drain, 1);
  StatEffect neg = fx(Field::skill(SkillId::sneak), EffectOp::fortify, -5);
  CHECK(check(bad_resist).has_value());
  CHECK(check(bad_restore).has_value());
  CHECK(check(bad_factor).has_value());
  CHECK(check(neg).has_value());
  CHECK(!check(fx(Field::stat(StatField::health), EffectOp::fortify, 10)));
  Stack st{bad_resist, bad_restore, bad_factor, neg};
  Effective e = apply(s, st, 0);
  CHECK(e.a == s.a && e.s == s.s);
  CHECK_NEAR(e[StatField::magickaRegenMultiplier], 1, 1e-12);
}

void names_from_the_world() {
  CHECK(field_named("resistPoison") == Field::stat(StatField::resistPoison));
  CHECK(field_named("endurance") == Field::attr(AttrId::endurance));
  CHECK(field_named("shortBlade") == Field::skill(SkillId::shortBlade));
  CHECK(!field_named("luck"));  // no Luck (76 §117)
  CHECK(op_named("ability") == EffectOp::ability);
  CHECK(!op_named("curse"));
}

}  // namespace

int main() {
  potion_for_sixty_seconds();
  attribute_ops();
  stat_fields();
  invalid_entries_refused_and_skipped();
  names_from_the_world();
  return TEST_MAIN_RESULT("core.effects");
}
