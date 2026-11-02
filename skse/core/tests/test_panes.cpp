// Our inventory and character sheet's rules (1.12 r4, the custom-UI card).
#include "check.h"
#include "argonia/core/panes.h"

using namespace argonia::core;
using panes::Kind;

namespace {
msg::InventoryItem item(std::string id, std::string name, msg::InventoryCategory c, bool eq) {
  msg::InventoryItem i;
  i.id = std::move(id), i.name = std::move(name), i.category = c, i.equipped = eq, i.count = 1;
  return i;
}

void inventory_rules() {
  CHECK(panes::category(Kind::ammo, false) == msg::InventoryCategory::weapons);
  CHECK(panes::category(Kind::potion, true) == msg::InventoryCategory::food);
  CHECK(panes::category(Kind::potion, false) == msg::InventoryCategory::potions);
  CHECK(panes::category(Kind::soulGem, false) == msg::InventoryCategory::misc);
  CHECK(panes::action(Kind::armor, false, true) == "Unequip" && panes::action(Kind::weapon, false, false) == "Equip");
  CHECK(panes::action(Kind::book, false, false) == "Read" && panes::action(Kind::key, false, false).empty());
  CHECK(panes::key(0x0001397E) == "0001397E");
  CHECK(panes::form_of("0001397E") == 0x0001397Eu && panes::form_of("FE012A8E#2") == 0xFE012A8Eu);
  CHECK(!panes::form_of("xyz") && !panes::form_of("0001397") && !panes::form_of("0001397G"));
  std::vector<msg::InventoryItem> v{item("3", "Bow", msg::InventoryCategory::weapons, false),
                                    item("1", "Ale", msg::InventoryCategory::food, false),
                                    item("2", "Axe", msg::InventoryCategory::weapons, false),
                                    item("4", "Sword", msg::InventoryCategory::weapons, true)};
  panes::order(v);
  CHECK(v[0].name == "Sword" && v[1].name == "Axe" && v[2].name == "Bow" && v[3].name == "Ale");
}

void sheet_rules() {
  CHECK(panes::display_name("handToHand") == "Hand to Hand" && panes::display_name("longBlade") == "Long Blade");
  CHECK(panes::display_name("agility") == "Agility");
  Sheet sh;
  sh.level = 3;
  sh.a[AttrId::agility] = 42.6;
  sh.s[SkillId::sneak] = 17.25;
  sh.cls.of.fill(SkillClass::misc);
  sh.cls.of[idx(SkillId::sneak)] = SkillClass::major;
  sh.cls.of[idx(SkillId::block)] = SkillClass::minor;
  const auto s = panes::charsheet(sh, "Hides-Deep", "Argonian", {50, 60, 40, 40, 70, 80}, 1, {});
  CHECK(s.level == 3 && s.attributes.size() == 7 && s.skills.size() == 27 && s.perk_points == 1);
  CHECK(s.attributes[0].name == "Agility" && s.attributes[0].value == 42);
  CHECK(s.skills[0].id == msg::SkillId::sneak && s.skills[0].group == "Major" && s.skills[0].value == 17);
  CHECK_NEAR(s.skills[0].progress, 0.25, 1e-9);
  CHECK(s.skills[1].id == msg::SkillId::block && s.skills[1].group == "Minor");
  CHECK(s.skills[2].group == "Miscellaneous");
  CHECK(msg::encode(s).has_value());  // fits the schema
}

void perk_rules() {
  msg::CharPerk p;
  p.available = true;
  CHECK(!panes::perk_refusal(&p, 1));
  CHECK(panes::perk_refusal(&p, 0) == "No perk to spend.");
  p.taken = true;
  CHECK(panes::perk_refusal(&p, 1) == "Already taken.");
  p.taken = false, p.available = false, p.need = "Sneak 30";
  CHECK(panes::perk_refusal(&p, 1) == "Sneak 30");
  CHECK(panes::perk_refusal(nullptr, 1).has_value());
}
}  // namespace

int main() {
  inventory_rules();
  sheet_rules();
  perk_rules();
  return TEST_MAIN_RESULT("core.panes");
}
