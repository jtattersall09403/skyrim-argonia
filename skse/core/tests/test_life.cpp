// L2: the 1.5 adapters' logic (life): engine facts to use events, a gain into the STAT family, the rest and its
// sitting with the view's intents, death and the pile, respawn on rest and on waking, the suspend policy, the
// router's 1.5 hooks, and the STAT and DETH families' round trip after the whole loop (1.5's L2 journey).
#include "check.h"
#include "builds.h"
#include "argonia/core/life.h"

#include <set>

using namespace argonia::core;
using namespace argonia::core::life;

namespace {

rest::Pos at(double x, double y, std::uint32_t cell = 7) { return {x, y, 0, cell}; }

rest::Context camp_at(rest::Pos p) {
  rest::Context c;
  c.bed = rest::BedTier::camp;
  c.at = p;
  return c;
}

}  // namespace

int main() {
  // Skills: weapon classes are skills; the mirrors follow SkillId's order; the vanilla gains switched off.
  CHECK(weapon_skill("weapon_class.longBlade") == SkillId::longBlade);
  CHECK(weapon_skill("weapon_class.spear") == SkillId::spear);
  CHECK(!weapon_skill("weapon_class.nothing"));
  CHECK(!weapon_skill("item.steel-sword"));
  CHECK(skill_mirrors().size() == gen::kSkillIdCount);
  int vanilla = 0;
  for (std::size_t i = 0; i < skill_mirrors().size(); ++i) {
    CHECK(skill_mirrors()[i].skill == SkillId(i));
    vanilla += !skill_mirrors()[i].actor_value.empty();
  }
  CHECK(vanilla == 14);  // 1.3 §a's fifteen less Marksman, which stays pinned at 0 (combat-wiring.md)
  // The engine's actor value names (AVIF enum names), not the menu's: Marksman, not Archery; Speechcraft, not Speech.
  CHECK(skill_mirrors()[idx(SkillId::speechcraft)].actor_value == "Speechcraft");
  CHECK(skill_mirrors()[idx(SkillId::marksman)].actor_value.empty());
  CHECK(skill_mirrors()[idx(SkillId::security)].actor_value == "Lockpicking");
  CHECK(vanilla_skills().size() == 18);
  for (auto menu_name : {"Archery", "Speech"})
    CHECK(std::set<std::string_view>(vanilla_skills().begin(), vanilla_skills().end()).count(menu_name) == 0);
  CHECK(std::set<std::string_view>(vanilla_skills().begin(), vanilla_skills().end()).count("OneHanded") == 1);

  // Armour class by the most pieces worn; ties go to the heavier; nothing worn is Unarmored.
  CHECK(armour_skill({}) == SkillId::unarmored);
  CHECK(armour_skill({3, 0, 2}) == SkillId::lightArmor);
  CHECK(armour_skill({2, 2, 0}) == SkillId::mediumArmor);
  CHECK(armour_skill({1, 2, 2}) == SkillId::heavyArmor);

  // The damage of a hit from health seen: the maximum the first time, the last reading after; never negative.
  HealthWatch hw;
  CHECK_NEAR(hw.damage(1, 80, 100), 20, 1e-12);
  CHECK_NEAR(hw.damage(1, 70, 100), 10, 1e-12);
  CHECK_NEAR(hw.damage(1, 72, 100), 0, 1e-12);  // regenerated between hits: reads low, never below 0
  CHECK_NEAR(hw.damage(2, 50, 50), 0, 1e-12);
  hw.forget(1);
  CHECK_NEAR(hw.damage(1, 90, 100), 10, 1e-12);
  CHECK(hw.size() == 2);

  // A blow on a hostile trains its weapon's skill and earns vastei = 4 x points x (1 + effSkill/50); a dummy nothing.
  seam::State s;
  s.sheet = argonia::test::marsh_hand();
  s.sheet.level = 1;
  const double long_blade = s.sheet.s[SkillId::longBlade];
  Target hostile{100};
  auto g = use(s, hit_dealt(SkillId::longBlade, 20, hostile));
  CHECK(g.counted() && g.skill == SkillId::longBlade);
  CHECK_NEAR(g.vastei, gen::progression::vastei_per_use * g.points * (1 + long_blade / gen::progression::vastei_skill_divisor), 1e-9);
  CHECK_NEAR(s.prog.vastei, g.vastei, 1e-12);
  Target dummy{100};
  dummy.dummy = true;
  CHECK(!use(s, hit_dealt(SkillId::longBlade, 20, dummy)).counted());
  CHECK(!use(s, hit_dealt(std::nullopt, 0, hostile)).counted());  // no damage, no use
  // Only weapons train weapon skills: a spell or an unclassed weapon trains nothing; fists train Hand-to-hand.
  CHECK(!blow_skill(false, false, std::nullopt));
  CHECK(!blow_skill(false, false, SkillId::longBlade));
  CHECK(!blow_skill(true, false, std::nullopt));
  CHECK(blow_skill(true, true, std::nullopt) == SkillId::handToHand);
  CHECK(blow_skill(true, false, SkillId::axe) == SkillId::axe);
  const combat::Piece pieces[] = {{SkillId::heavyArmor, 50, 0}, {SkillId::heavyArmor, 0, 0}, {SkillId::lightArmor, 0, 0},
                                  {SkillId::mediumArmor, 0, 0}};
  const auto w = worn_of(pieces);
  CHECK(w.heavy == 2 && w.light == 1 && w.medium == 1);
  CHECK(armour_skill(w) == SkillId::heavyArmor);
  CHECK(hit_dealt(std::nullopt, 5, hostile).skill == SkillId::handToHand);

  // Struck while blocking: the armour class's hitTaken, then Block; a kill trains the armour class.
  auto struck = hit_taken(10, 100, {0, 0, 3}, true, true);
  CHECK(struck.size() == 2 && struck[0].skill == SkillId::heavyArmor && struck[1].skill == SkillId::block);
  CHECK(struck[1].kind == gen::UseKind::block);
  CHECK(hit_taken(10, 100, {}, false, true).size() == 1);
  CHECK(kill(hostile, 100, {2, 0, 0}).skill == SkillId::lightArmor);
  CHECK(use(s, cast(SkillId::destruction, true)).counted());
  CHECK(!use(s, cast(SkillId::destruction, false)).counted());
  CHECK(unlock(50, 60).skill == SkillId::security);

  // Scripted skill uses to a pending level (S16b's join: combat use -> skill -> vastei -> level).
  int guard = 0;
  while (s.prog.pending_levels == 0 && guard++ < 10000) use(s, hit_dealt(SkillId::longBlade, 20, hostile));
  CHECK(s.prog.pending_levels == 1);
  CHECK(s.sheet.s[SkillId::longBlade] > long_blade);
  CHECK(s.sheet.level == 1);  // levels are taken only at rest

  // A rest in combat is refused and changes nothing; in a settlement on the ground it is wait only.
  auto busy = camp_at(at(10, 10));
  busy.in_combat = true;
  auto refused = rest_at(s, busy, {});
  CHECK(refused.outcome.ruling.verdict == rest::Verdict::refused && !refused.notice.empty());
  CHECK(!s.death.wake && !refused.sitting && !refused.save_now);
  auto town = camp_at(at(10, 10));
  town.in_settlement = true;
  CHECK(rest_at(s, town, {}).outcome.ruling.verdict == rest::Verdict::wait_only);

  // Rest at the camp: the wake point, the roster reset (onRest yes, never no, untilCleared in a cleared place no),
  // and the sitting opens because a level is pending; the save waits for the sitting's close.
  Roster roster;
  roster.actors = {{0x100, *respawn::class_named("onRest"), 1}, {0x101, *respawn::class_named("never"), 1},
                   {0x102, *respawn::class_named("untilCleared"), 2}, {0x103, *respawn::class_named("untilCleared"), 3}};
  roster.cleared.places = {2};
  const auto camp = at(100, 200);
  auto rested = rest_at(s, camp_at(camp), roster);
  CHECK(rested.outcome.ruling.verdict == rest::Verdict::rest);
  CHECK(s.death.wake == camp);
  CHECK((rested.reset == std::vector<respawn::ActorId>{0x100, 0x103}));
  CHECK(rested.sitting.has_value() && !rested.save_now);
  CHECK(rested.sitting->sheet.level == 2);

  // The sitting view: seven rows priced by the core; a buy spends; too dear names the refusal; done applies.
  s.prog.vastei += 1000;  // enough for a few points
  rested.sitting->vastei = s.prog.vastei;
  auto sit = open_sitting(*rested.sitting, s);
  auto v = view(sit);
  CHECK(v.level == 2 && v.attributes.size() == gen::kAttrIdCount && v.pending_after == 0);
  CHECK(v.attributes[idx(AttrId::endurance)].name == "Endurance");
  CHECK_NEAR(v.attributes[idx(AttrId::endurance)].cost, sitting::cost(AttrId::endurance, 1, 2, 50), 1e-9);
  CHECK(!v.attributes[idx(AttrId::endurance)].refusal);
  const double before = sit.st.vastei;
  auto r = on_intent_text(sit, R"({"type":"sitting.buy","v":1,"body":{"attribute":"endurance"}})", s);
  CHECK(r.state && !r.closed);
  CHECK_NEAR(r.state->vastei, before - sitting::cost(AttrId::endurance, 1, 2, 50), 1e-9);
  CHECK(r.state->attributes[idx(AttrId::endurance)].value == 51 && r.state->attributes[idx(AttrId::endurance)].bought == 1);
  CHECK(r.state->health.after > r.state->health.before);  // health recomputes with Endurance
  CHECK(s.sheet.a[AttrId::endurance] == 50);               // not applied before the close
  auto bad = on_intent_text(sit, R"({"type":"sitting.buy","v":1,"body":{"attribute":"luck"}})", s);
  CHECK(bad.state && !bad.notes.empty());
  for (int i = 0; i < 20; ++i) on_intent_text(sit, R"({"type":"sitting.buy","v":1,"body":{"attribute":"strength"}})", s);
  auto vs = view(sit);
  CHECK(vs.attributes[idx(AttrId::strength)].bought <= 5);
  CHECK(vs.attributes[idx(AttrId::strength)].refusal.has_value());
  const auto left = sit.st.vastei;
  const auto end_after = sit.st.sheet.a[AttrId::endurance];
  auto done = on_intent_text(sit, R"({"type":"sitting.done","v":1,"body":{}})", s);
  CHECK(done.closed && done.save_now && !done.state);
  CHECK(s.sheet.level == 2 && s.prog.pending_levels == 0);
  CHECK_NEAR(s.prog.vastei, left, 1e-12);  // unspent vastei carries over
  CHECK(s.sheet.a[AttrId::endurance] == end_after);

  // A rest with nothing pending saves at once and opens no sitting.
  auto plain = rest_at(s, camp_at(camp), roster);
  CHECK(!plain.sitting && plain.save_now);

  // Death: carried vastei becomes one pile at the death spot; wake at the camp; reset as a rest; a second death
  // replaces the pile; within 2 m the whole pile comes back, beyond it nothing.
  s.prog.vastei = 120;
  const auto fell = at(500, 500);
  auto d1 = die(s, fell, roster);
  CHECK(d1.outcome.pile && d1.outcome.pile->vastei == 120 && d1.outcome.pile->at == fell);
  CHECK(d1.outcome.wake == camp && d1.had_wake_point && !d1.replaced_pile);
  CHECK(s.prog.vastei == 0 && s.sheet.level == 2);  // the character is kept
  CHECK((d1.reset == std::vector<respawn::ActorId>{0x100, 0x103}));
  CHECK(pile_name(120) == "Vastei (120)" && pile_name(99.7) == "Vastei (99)");
  CHECK(!take_pile(s, at(503, 500)));       // 3 m: too far
  CHECK(!take_pile(s, at(500, 500, 8)));    // another cell
  s.prog.vastei = 40;
  auto d2 = die(s, at(600, 600), roster);
  CHECK(d2.replaced_pile && s.death.pile && s.death.pile->vastei == 40);
  CHECK(!take_pile(s, at(500, 500)));       // the first pile is gone
  auto got = take_pile(s, at(601.5, 600));
  CHECK(got && *got == 40 && s.prog.vastei == 40 && !s.death.pile);
  CHECK(!take_pile(s, at(601.5, 600)));     // taken once
  s.prog.vastei = 0;
  die(s, at(1, 1), roster);
  CHECK(!s.death.pile);                     // dying with nothing carried leaves no pile and loses the old one

  // Units: the recovery radius in Skyrim units is 2 m x units_per_metre, and back.
  const auto u = at_units(2 * gen::units::units_per_metre, 0, 0, 7);
  CHECK_NEAR(u.x, 2, 1e-12);
  CHECK_NEAR(to_units(u)[0], 2 * gen::units::units_per_metre, 1e-9);

  // Death before any rest wakes where the player fell.
  seam::State fresh;
  fresh.prog.vastei = 5;
  auto d0 = die(fresh, at(9, 9), {});
  CHECK(!d0.had_wake_point && d0.outcome.wake == at(9, 9));

  // The suspend save: quit and stream drop always (if the game can save); else once the interval has passed, never
  // in combat and never with a menu open. Opening a menu (the Journal, the Tween hub) is never a reason (game-8).
  const double iv = gen::rest::suspend_save_interval_s;
  CHECK(suspend_why("quit") == SuspendWhy::quit);
  CHECK(suspend_why("stream_drop") == SuspendWhy::stream_drop);
  for (auto w : {"", "pause_hub", "pause hub", "interval", "stream drop", "QUIT"}) CHECK(!suspend_why(w));
  CHECK(suspend_due(SuspendWhy::quit, 10, 9, true, true, true));
  CHECK(suspend_due(SuspendWhy::stream_drop, 10, 9, false, true, true));
  CHECK(!suspend_due(SuspendWhy::quit, 10, 9, false, false, false));
  CHECK(suspend_due(SuspendWhy::interval, 9 + iv, 9, false, true, false));
  CHECK(suspend_due(SuspendWhy::interval, 10, std::nullopt, false, true, false));
  CHECK(!suspend_due(SuspendWhy::interval, 9 + iv, 9, true, true, false));
  CHECK(!suspend_due(SuspendWhy::interval, 9 + iv, 9, false, true, true));     // a menu is open: never
  CHECK(!suspend_due(SuspendWhy::interval, 10, std::nullopt, false, true, true));
  {
    QuitWatch q;
    CHECK(!q.on_menu(true, false));   // the Journal opens: nothing
    CHECK(!q.on_menu(true, false));   // the Tween hub opens: nothing
    CHECK(!q.on_menu(false, false));  // a menu closes with no quit asked: nothing
    CHECK(!q.on_menu(true, false));   // the quit confirmation opens: nothing yet
    CHECK(!q.on_menu(true, true));    // a menu opening never saves, even mid-quit
    CHECK(q.on_menu(false, true) == SuspendWhy::quit);  // Yes: the confirmation closes with the flag set
    CHECK(!q.on_menu(false, true));   // the Journal closes next: once per quit
    CHECK(!q.on_menu(true, false));   // a load clears the flag and the latch
    CHECK(q.on_menu(false, true) == SuspendWhy::quit);  // the next quit saves again
  }
  CHECK(kRestSave != kSuspendSave);

  // The router: the two 1.5 hooks once, the LevelUp Menu blocked with its handler run, playerDeath handled.
  router::Router rt;
  int level_ups = 0, deaths = 0;
  auto log = install(rt, [&](router::SurfaceId) { ++level_ups; }, [&](router::SurfaceId) { ++deaths; });
  CHECK((log == std::vector<std::string>{"hook progressionOff", "hook deathIntercept", "handler levelUpMenu",
                                          "handler playerDeath"}));
  auto lv = rt.on_menu("LevelUp Menu");
  CHECK(lv.action == router::Action::block && lv.handled && level_ups == 1);
  auto pd = rt.on_surface(router::SurfaceId::playerDeath);
  CHECK(pd.action == router::Action::block && pd.handled && deaths == 1);
  auto again = install(rt, [](router::SurfaceId) {}, [](router::SurfaceId) {});
  CHECK(again.size() == 4 && again[0].starts_with("refused: "));
  CHECK(seam::install(rt, [](router::SurfaceId) {}).size() >= 3);  // 1.1's hooks sit beside 1.5's

  // Every family round-trips after the loop (1.5 acceptance: a save round trip keeps every family).
  s.prog.vastei = 77;
  s.death.pile = death::Pile{at(3, 4), 55};
  families::Registry reg;
  CHECK(seam::bind(reg, s).empty());
  auto saved = reg.save_all();
  const auto want_sheet = s.sheet;
  const auto want_prog = s.prog;
  const auto want_death = s.death;
  reg.reset_all();
  CHECK(s.prog.vastei == 0 && !s.death.pile);
  for (auto& rec : saved) CHECK(reg.load(rec.id, rec.version, rec.payload).ok());
  CHECK(s.sheet == want_sheet && s.prog == want_prog && s.death == want_death);

  return TEST_MAIN_RESULT("life");
}
