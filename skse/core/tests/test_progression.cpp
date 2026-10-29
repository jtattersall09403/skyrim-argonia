// L2: use, worthiness, vastei and the level counter (76 §120), S16a and S16b on the reference, trainers, the
// per-rest Athletics cap and the `stats` family payload.
#include "check.h"
#include "builds.h"
#include "argonia/core/progression.h"

using namespace argonia::core;
using namespace argonia::core::progression;

namespace {

Sheet long_blade_15() {
  Sheet s = argonia::test::marsh_hand();
  s.s[SkillId::longBlade] = 15;
  s.level = 1;
  return s;
}

UseEvent blow(double damage, double target_max = 100) {
  UseEvent ev{SkillId::longBlade, UseKind::weaponConnect};
  ev.damage = damage;
  ev.target_max_health = target_max;
  return ev;
}

void rank_costs() {  // 76 §120.1: 10, 19, 31 and 58 uses per rank (major, specialised)
  Sheet s = long_blade_15();
  CHECK_NEAR(rank_cost(SkillId::longBlade, s), 9.6, 1e-9);
  s.s[SkillId::longBlade] = 30; CHECK_NEAR(rank_cost(SkillId::longBlade, s), 18.6, 1e-9);
  s.s[SkillId::longBlade] = 50; CHECK_NEAR(rank_cost(SkillId::longBlade, s), 30.6, 1e-9);
  s.s[SkillId::longBlade] = 95; CHECK_NEAR(rank_cost(SkillId::longBlade, s), 57.6, 1e-9);
  CHECK_NEAR(rank_cost(SkillId::blunt, s), 6 * 1.0 * 0.8, 1e-9);       // minor, specialised (combat)
  CHECK_NEAR(rank_cost(SkillId::sneak, s), 6 * 1.25, 1e-9);            // misc, other specialisation
}

void s16a_ten_blows_make_a_rank() {
  Sheet s = long_blade_15();
  Effective e = Effective::of(s);
  Progress p;
  Outcome o{p, s};
  for (int i = 0; i < 9; ++i) o = apply(o.progress, o.sheet, e, blow(20));
  CHECK_NEAR(o.sheet.s[SkillId::longBlade], 15, 1e-12);
  o = apply(o.progress, o.sheet, e, blow(15));  // exactly 15 %: a full point
  CHECK_NEAR(o.sheet.s[SkillId::longBlade], 16, 1e-12);
  CHECK(o.ranks == 1);
  CHECK_NEAR(o.progress.vastei, 10 * 4 * (1 + 15.0 / 50), 1e-9);
  CHECK_NEAR(o.progress.xp[idx(SkillId::longBlade)], 0.4, 1e-9);
}

void worthiness_rules() {
  CHECK_NEAR(worthiness(blow(5)), 5.0 / 100 / 0.15, 1e-12);
  CHECK_NEAR(worthiness(blow(5, 1000)), 0.05, 1e-12);  // chip on a giant: the floor
  CHECK_NEAR(worthiness(blow(90)), 1.0, 1e-12);       // capped at 1 a blow
  UseEvent ev = blow(50);
  ev.target_dummy = true; CHECK(worthiness(ev) == 0);
  ev = blow(50); ev.target_summoned = true; CHECK(worthiness(ev) == 0);
  ev = blow(50); ev.target_helpless = true; CHECK(worthiness(ev) == 0);
  ev = blow(50); ev.target_hostile = false; CHECK(worthiness(ev) == 0);
  CHECK(worthiness(blow(0)) == 0);
  CHECK(worthiness(blow(10, 0)) == 0);  // no target health: nothing to scale by
  CHECK_NEAR(use_points(UseKind::weaponConnect, SkillId::axe), 1.2, 1e-12);
  CHECK_NEAR(use_points(UseKind::weaponConnect, SkillId::shortBlade), 0.75, 1e-12);
  CHECK_NEAR(use_points(UseKind::block, SkillId::block), 2.5, 1e-12);
}

void armour_accrual() {
  UseEvent hit{SkillId::heavyArmor, UseKind::hitTaken};
  hit.damage = 30; hit.own_max_health = 100;
  CHECK_NEAR(worthiness(hit), 1.0, 1e-12);
  hit.skill = SkillId::lightArmor; CHECK_NEAR(worthiness(hit), 0.25, 1e-12);
  hit.skill = SkillId::longBlade; CHECK(worthiness(hit) == 0);  // not an armour skill
  UseEvent kill{SkillId::lightArmor, UseKind::armourKill};
  kill.target_max_health = 100; kill.own_max_health = 100;
  CHECK_NEAR(worthiness(kill), 0.5, 1e-12);
  kill.skill = SkillId::heavyArmor; CHECK_NEAR(worthiness(kill), 0.35 * 0.5, 1e-12);
  kill.target_max_health = 5; CHECK_NEAR(worthiness(kill), 0.35 * 0.05, 1e-12);  // vermin: the floor
  kill.target_max_health = 1000; CHECK_NEAR(worthiness(kill), 0.35, 1e-12);
  Sheet s = long_blade_15();
  kill.skill = SkillId::lightArmor; kill.target_max_health = 100;
  Outcome o = apply(Progress{}, s, Effective::of(s), kill);
  CHECK_NEAR(o.points, 3.0 * 0.5, 1e-12);
}

void other_uses() {
  UseEvent spell{SkillId::destruction, UseKind::spellEffect};
  CHECK(worthiness(spell) == 1);
  spell.had_effect = false; CHECK(worthiness(spell) == 0);  // light at noon
  UseEvent jump{SkillId::acrobatics, UseKind::jump};
  CHECK(worthiness(jump) == 0);
  jump.jump_rise_m = 0.35; CHECK(worthiness(jump) == 1);
  jump.jump_rise_m = 0; jump.jump_run_m = 2.5; CHECK(worthiness(jump) == 1);
  UseEvent lock{SkillId::security, UseKind::lock};
  lock.lock_level = 40; lock.lock_ceiling = 55; CHECK(worthiness(lock) == 0);
  lock.lock_level = 45; CHECK(worthiness(lock) == 1);
  UseEvent fall{SkillId::acrobatics, UseKind::fall};
  fall.damage = 10; CHECK(worthiness(fall) == 1);
  fall.first_since_rest = false; CHECK(worthiness(fall) == 0);
  UseEvent brew{SkillId::alchemy, UseKind::brew};
  brew.first_since_rest = false; CHECK(worthiness(brew) == 0);
  UseEvent zero{SkillId::athletics, UseKind::run};
  zero.amount = 0; CHECK(worthiness(zero) == 0);
}

void athletics_cap_per_rest() {
  Sheet s = long_blade_15();
  Effective e = Effective::of(s);
  UseEvent run{SkillId::athletics, UseKind::run};
  run.amount = 1300;
  Outcome o = apply(Progress{}, s, e, run);
  CHECK_NEAR(o.points, 1200 * 0.02, 1e-9);
  run.amount = 100;
  Outcome o2 = apply(o.progress, o.sheet, e, run);
  CHECK_NEAR(o2.points, 0, 1e-12);
  Outcome o3 = apply(on_rest(o2.progress), o2.sheet, e, run);
  CHECK_NEAR(o3.points, 2, 1e-9);
  run.outside_settlement = false;
  CHECK_NEAR(apply(Progress{}, s, e, run).points, 0, 1e-12);
}

void s16b_level_counter() {
  Sheet s = long_blade_15();
  CHECK(ranks_for_level(1) == 1);
  CHECK(ranks_for_level(8) == 8);
  CHECK(ranks_for_level(40) == 8);  // the ceiling of 8
  CHECK(ranks_for_level(0) == 1);
  // One counted rank at level 1 makes one pending level.
  Outcome o = grant_ranks(Progress{}, s, SkillId::longBlade, 1);
  CHECK(o.progress.pending_levels == 1 && o.levels == 1);
  CHECK_NEAR(o.progress.vastei, 0, 1e-12);  // trainers and books grant no vastei
  // Three misc ranks make one counted rank.
  Outcome m = grant_ranks(Progress{}, s, SkillId::sneak, 2);
  CHECK(m.progress.pending_levels == 0);
  m = grant_ranks(m.progress, m.sheet, SkillId::sneak, 1);
  CHECK(m.progress.pending_levels == 1);
  // The next level (2 -> 3, with one pending) asks two ranks.
  Outcome n = grant_ranks(o.progress, o.sheet, SkillId::longBlade, 1);
  CHECK(n.progress.pending_levels == 1);
  n = grant_ranks(n.progress, n.sheet, SkillId::longBlade, 1);
  CHECK(n.progress.pending_levels == 2);
}

void maxed_skill_still_pays() {
  Sheet s = long_blade_15();
  s.s[SkillId::longBlade] = 100;
  Effective e = Effective::of(s);
  Progress p;
  p.xp[idx(SkillId::longBlade)] = rank_cost(SkillId::longBlade, s) - 1;
  Outcome o = apply(p, s, e, blow(50));
  CHECK_NEAR(o.sheet.s[SkillId::longBlade], 100, 1e-12);  // never above the cap
  CHECK(o.ranks == 1);
  CHECK(o.progress.credit == 1);                           // at the 1 : 3 rate
  CHECK_NEAR(o.vastei, 4 * 1 * (1 + 100.0 / 50), 1e-9);
}

void rested_multiplies_experience_only() {
  Sheet s = long_blade_15();
  UseEvent ev = blow(50);
  ev.xp_mult = 1.05;
  Outcome o = apply(Progress{}, s, Effective::of(s), ev);
  CHECK_NEAR(o.progress.xp[idx(SkillId::longBlade)], 1.05, 1e-12);
  CHECK_NEAR(o.vastei, 4 * 1.3, 1e-9);
}

void trainer_cap() {
  Sheet s = long_blade_15();  // Strength 50 governs Long Blade
  CHECK(can_train(s, SkillId::longBlade));
  s.s[SkillId::longBlade] = 50;
  CHECK(!can_train(s, SkillId::longBlade));
}

void stats_family_payload() {
  Sheet s = argonia::test::marsh_hand();
  Progress p;
  p.vastei = 123.5; p.credit = 2; p.pending_levels = 1; p.xp[3] = 4.25; p.athletics_s = 30;
  cosave::Bytes b = encode(s, p);
  Sheet s2; Progress p2;
  CHECK(decode(b, s2, p2));
  CHECK(s2 == s && p2 == p);
  cosave::Bytes short_b(b.begin(), b.end() - 1);
  Sheet s3 = s2; Progress p3 = p2;
  CHECK(!decode(short_b, s3, p3));
  CHECK(s3 == s2 && p3 == p2);  // a refused payload leaves the state alone
  b.push_back(0);
  CHECK(!decode(b, s3, p3));
  cosave::Bytes bad = encode(s, p);
  bad[gen::kAttrIdCount * 8 + gen::kSkillIdCount * 8 + 4] = 99;  // a skill class out of range
  CHECK(!decode(bad, s3, p3));
}

}  // namespace

int main() {
  rank_costs();
  s16a_ten_blows_make_a_rank();
  worthiness_rules();
  armour_accrual();
  other_uses();
  athletics_cap_per_rest();
  s16b_level_counter();
  maxed_skill_still_pays();
  rested_multiplies_experience_only();
  trainer_cap();
  stats_family_payload();
  return TEST_MAIN_RESULT("core.progression");
}
