// L2: the combat wiring's runtime writes (combat-wiring.md): the four wired carriers over the five builds (the
// spec's table: P × S − 1, stamina × − 1, −mitigation at the reference blow, stability − 1), the neutral cases
// (empty hand, unwired rows), armour rating with the Unarmored slots, the pinned vanilla skills, and the roll
// lock by burden tier through TK Dodge's own perk lock.
#include "check.h"
#include "builds.h"
#include "argonia/core/combat.h"
#include "argonia/core/life.h"

#include <set>

using namespace argonia::core;
using namespace argonia::core::combat;
using argonia::test::builds;

namespace {

double value_of(const Pass& p, CarrierId id) {
  for (const auto& w : p.writes)
    if (w.actor_value == gen::kCarriers[std::size_t(id)].actor_value) return w.value;
  return 99;
}

void the_spec_table() {
  // Carrier = P × S − 1 with a long blade (combat-wiring.md's reference builds).
  const double want[] = {-0.148, -0.549, -0.600, -0.408, 0.500};
  const BurdenTier tier[] = {BurdenTier::mid, BurdenTier::fast, BurdenTier::fast, BurdenTier::overloaded, BurdenTier::fast};
  const double power[] = {0.984, 1.175, 1.175, 1.593, 0.800};
  for (std::size_t i = 0; i < std::size(builds); ++i) {
    auto sh = builds[i].sheet;
    if (i == 4) sh.s[SkillId::longBlade] = 100;  // the spec's god: Long Blade 100
    Loadout l{{SkillId::longBlade}, {}, builds[i].carried_kg};
    const auto p = compute(sh, Effective::of(sh), l);
    CHECK_NEAR(value_of(p, CarrierId::right_attack_damage), want[i], 5e-4);
    CHECK(p.burden == tier[i]);
    CHECK_NEAR(value_of(p, CarrierId::right_power_stamina), power[i] - 1, 5e-4);
    CHECK(p.writes.size() == 4);  // only the wired rows
    CHECK(value_of(p, CarrierId::left_attack_damage) == 99);
    CHECK(value_of(p, CarrierId::body_incoming_stagger) == 99);
    CHECK(p.roll_allowed == (tier[i] != BurdenTier::overloaded));
  }
}

void neutral_cases() {
  const auto s = argonia::test::marsh_hand();
  const auto e = Effective::of(s);
  const auto c = carriers::compute(s, e, BurdenTier::mid, {}, {});
  CHECK(carrier_value(CarrierId::right_attack_damage, c, {}, 0) == 0);  // an empty hand never zeroes damage
  CHECK(carrier_value(CarrierId::right_power_stamina, c, {}, 0) == 0);
  CHECK(carrier_value(CarrierId::body_incoming_damage, c, {}, 0) == 0);  // no armour: no mitigation
  CHECK(carrier_value(CarrierId::left_attack_damage, c, {SkillId::axe}, 50) == 0);  // reserved
  // A bow takes no Strength: P − 1.
  auto strong = s;
  strong.a[AttrId::strength] = 100;
  const carriers::HandContext bow{SkillId::marksman, true};
  const auto cb = carriers::compute(strong, Effective::of(strong), BurdenTier::mid, bow, {});
  CHECK_NEAR(carrier_value(CarrierId::right_attack_damage, cb, bow, 0), cb.right.damage_position - 1, 1e-12);
  // Every carrier the table marks wired has a formula here (a new wired row must not be silently neutral).
  for (std::size_t i = 0; i < gen::kCarriers.size(); ++i)
    if (gen::kCarriers[i].wired)
      CHECK(carrier_value(CarrierId(i), c, {SkillId::longBlade}, 50) != 0);
}

void armour_and_mitigation() {
  const auto s = argonia::test::marsh_hand();  // Heavy Armor 45, Unarmored 5
  const auto e = Effective::of(s);
  const auto c = carriers::compute(s, e, BurdenTier::mid, {}, {});
  const Piece cuirass{SkillId::heavyArmor, 50, 0b0010};
  const double bare = 0.0065 * 5 * 5;
  CHECK_NEAR(armour_rating(c, std::span(&cuirass, 1)), 47.5128 + 3 * bare, 1e-3);
  CHECK_NEAR(armour_rating(c, {}), 4 * bare, 1e-12);
  const std::vector<Piece> five(5, cuirass);
  CHECK_NEAR(armour_rating(c, five), 5 * 47.5128 + 3 * bare, 5e-3);  // five on one slot cover one slot
  // Counted by slot: a shield covers none, so shield + cuirass + gauntlets + boots leaves the head bare.
  const std::vector<Piece> kit{{SkillId::heavyArmor, 0, 0}, {SkillId::heavyArmor, 0, 0b0010},
                               {SkillId::heavyArmor, 0, 0b0100}, {SkillId::heavyArmor, 0, 0b1000}};
  CHECK_NEAR(armour_rating(c, kit), bare, 1e-12);
  const std::vector<Piece> full{{SkillId::lightArmor, 0, 0b0001}, {SkillId::lightArmor, 0, 0b1110}};
  CHECK_NEAR(armour_rating(c, full), 0, 1e-12);  // every slot covered: no Unarmored term
  Loadout l{{SkillId::longBlade}, {cuirass}, 45};
  const auto p = compute(s, e, l);
  CHECK_NEAR(value_of(p, CarrierId::body_incoming_damage), -carriers::mitigation(p.armour_rating, 24), 1e-12);
  CHECK_NEAR(value_of(p, CarrierId::body_incoming_damage), -0.2423, 1e-3);
  CHECK_NEAR(value_of(p, CarrierId::body_block), 0.95 - 1, 1e-12);  // Block 50: capped stability
}

void pinned_skills_are_never_mirrored() {
  std::set<std::string_view> pinned(pinned_vanilla_skills().begin(), pinned_vanilla_skills().end());
  CHECK(pinned == (std::set<std::string_view>{"OneHanded", "TwoHanded", "Marksman"}));
  for (const auto& m : life::skill_mirrors()) CHECK(!pinned.count(m.actor_value));
  // The pinned names are engine actor value names, and each is a vanilla skill whose gain is off.
  std::set<std::string_view> vanilla(life::vanilla_skills().begin(), life::vanilla_skills().end());
  for (auto n : pinned) CHECK(vanilla.count(n));
}

void roll_lock() {
  CHECK(roll_allowed(BurdenTier::fast) && roll_allowed(BurdenTier::mid) && roll_allowed(BurdenTier::fat));
  CHECK(!roll_allowed(BurdenTier::overloaded));
  const char* toml = "[Settings]\nbUsePerkLock = true\nfDodgeCost = 15.0\n\n[Forms]\n"
                     "sOnDodgeSpellID = \"OnDodgeDummySpell\"\nsDodgeRequiredPerkID = \"TKDodgeAddon.esp|0x809\"\r\n"
                     "sOnDodgeSpellRequiredPerkID = \"TKDodgeAddon.esp|0x80F\"\n";
  const auto lock = tk_dodge_perk_lock(toml);
  CHECK(lock && lock->on && lock->plugin == "TKDodgeAddon.esp" && lock->local == 0x809);
  CHECK(roll_perk_wanted(lock, BurdenTier::fat) == std::optional<bool>(true));
  CHECK(roll_perk_wanted(lock, BurdenTier::overloaded) == std::optional<bool>(false));
  // The shipped default (bUsePerkLock = false): nothing to do, whatever the tier.
  const auto off = tk_dodge_perk_lock("bUsePerkLock = false\nsDodgeRequiredPerkID = \"TKDodgeAddon.esp|0x809\"\n");
  CHECK(off && !off->on);
  CHECK(!roll_perk_wanted(off, BurdenTier::overloaded));
  // Unreadable perk ids refuse rather than guess.
  CHECK(!tk_dodge_perk_lock("bUsePerkLock = true\n"));
  CHECK(!tk_dodge_perk_lock("sDodgeRequiredPerkID = \"TKDodgeAddon.esp|0xZZ\"\n"));
  CHECK(!tk_dodge_perk_lock("sDodgeRequiredPerkID = \"|0x809\"\n"));
  CHECK(!tk_dodge_perk_lock("# sDodgeRequiredPerkID = \"A.esp|0x809\"\n"));
  CHECK(!roll_perk_wanted(std::nullopt, BurdenTier::overloaded));
}

}  // namespace

int main() {
  the_spec_table();
  neutral_cases();
  armour_and_mitigation();
  pinned_skills_are_never_mirrored();
  roll_lock();
  return TEST_MAIN_RESULT("core.combat");
}
