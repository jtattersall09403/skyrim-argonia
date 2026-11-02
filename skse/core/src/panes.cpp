#include "argonia/core/panes.h"

#include <algorithm>
#include <cctype>
#include <charconv>
#include <cmath>
#include <cstdio>

namespace argonia::core::panes {

using msg::InventoryCategory;

InventoryCategory category(Kind k, bool food) {
  switch (k) {
    case Kind::weapon:
    case Kind::ammo: return InventoryCategory::weapons;
    case Kind::armor: return InventoryCategory::apparel;
    case Kind::potion: return food ? InventoryCategory::food : InventoryCategory::potions;
    case Kind::ingredient: return InventoryCategory::ingredients;
    case Kind::scroll: return InventoryCategory::scrolls;
    case Kind::book: return InventoryCategory::books;
    case Kind::key: return InventoryCategory::keys;
    case Kind::light:
    case Kind::misc:
    case Kind::soulGem: return InventoryCategory::misc;
  }
  return InventoryCategory::misc;
}

std::string action(Kind k, bool food, bool equipped) {
  switch (k) {
    case Kind::weapon:
    case Kind::ammo:
    case Kind::armor:
    case Kind::light: return equipped ? "Unequip" : "Equip";
    case Kind::potion: return food ? "Eat" : "Drink";
    case Kind::ingredient: return "Eat";
    case Kind::scroll: return equipped ? "Unequip" : "Ready";
    case Kind::book: return "Read";
    case Kind::key:
    case Kind::misc:
    case Kind::soulGem: return "";
  }
  return "";
}

std::string key(std::uint32_t form_id) {
  char b[9];
  std::snprintf(b, sizeof b, "%08X", form_id);
  return b;
}

std::optional<std::uint32_t> form_of(std::string_view k) {
  k = k.substr(0, k.find('#'));
  if (k.size() != 8) return std::nullopt;
  std::uint32_t v = 0;
  const auto r = std::from_chars(k.data(), k.data() + k.size(), v, 16);
  if (r.ec != std::errc{} || r.ptr != k.data() + k.size()) return std::nullopt;
  return v;
}

void order(std::vector<msg::InventoryItem>& items) {
  std::stable_sort(items.begin(), items.end(), [](const auto& a, const auto& b) {
    if (a.category != b.category) return a.category < b.category;
    if (a.equipped != b.equipped) return a.equipped;
    if (a.name != b.name) return a.name < b.name;
    return a.id < b.id;
  });
}

std::string display_name(std::string_view id) {
  std::string out;
  for (std::size_t i = 0; i < id.size(); ++i) {
    const char c = id[i];
    if (i == 0) out += char(std::toupper(static_cast<unsigned char>(c)));
    else if (std::isupper(static_cast<unsigned char>(c))) {
      out += ' ';
      const std::string_view rest = id.substr(i);
      const bool small = rest.starts_with("To") && (rest.size() == 2 || std::isupper(static_cast<unsigned char>(rest[2])));
      out += small ? char(std::tolower(static_cast<unsigned char>(c))) : c;
    } else out += c;
  }
  return out;
}

namespace {
std::string group_of(SkillClass c) {
  switch (c) {
    case SkillClass::major: return "Major";
    case SkillClass::minor: return "Minor";
    default: return "Miscellaneous";
  }
}
int rank(SkillClass c) { return c == SkillClass::major ? 0 : c == SkillClass::minor ? 1 : 2; }
}  // namespace

msg::CharsheetState charsheet(const Sheet& sh, std::string name, std::string race, const Pools& p, int perk_points,
                              std::vector<msg::CharPerk> perks) {
  msg::CharsheetState s;
  s.name = std::move(name);
  s.race = std::move(race);
  s.level = std::max(1, sh.level);
  s.progress = 0;  // the level's progress is 1.3's meter (skill-ups since the last level); owed with it
  s.health = p.health, s.health_max = p.health_max, s.magicka = p.magicka, s.magicka_max = p.magicka_max;
  s.stamina = p.stamina, s.stamina_max = p.stamina_max;
  s.perk_points = std::max(0, perk_points);
  for (std::size_t i = 0; i < gen::kAttrIdCount; ++i) {
    msg::CharAttribute a;
    a.id = msg::AttributeId(i);
    a.name = display_name(gen::kAttrIdNames[i]);
    a.value = std::int64_t(std::floor(sh.a.v[i]));
    s.attributes.push_back(std::move(a));
  }
  std::vector<std::size_t> idx(gen::kSkillIdCount);
  for (std::size_t i = 0; i < idx.size(); ++i) idx[i] = i;
  std::stable_sort(idx.begin(), idx.end(), [&](std::size_t x, std::size_t y) {
    const int rx = rank(sh.cls.of[x]), ry = rank(sh.cls.of[y]);
    return rx != ry ? rx < ry : gen::kSkillIdNames[x] < gen::kSkillIdNames[y];
  });
  for (std::size_t i : idx) {
    msg::CharSkill k;
    k.id = msg::SkillId(i);
    k.name = display_name(gen::kSkillIdNames[i]);
    k.group = group_of(sh.cls.of[i]);
    const double v = std::max(0.0, sh.s.v[i]);
    k.value = std::int64_t(std::floor(v));
    k.progress = std::clamp(v - std::floor(v), 0.0, 1.0);
    s.skills.push_back(std::move(k));
  }
  s.perks = std::move(perks);
  return s;
}

std::optional<std::string> perk_refusal(const msg::CharPerk* p, int perk_points) {
  if (!p) return "That perk is not on the sheet.";
  if (p->taken) return "Already taken.";
  if (!p->available) return p->need ? *p->need : std::string("Not yet.");
  if (perk_points <= 0) return "No perk to spend.";
  return std::nullopt;
}

}  // namespace argonia::core::panes
