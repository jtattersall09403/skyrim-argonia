// Our inventory and character sheet (1.12 r4) on the "Argonia custom UI" card: with Wind UI's DLL absent the router
// takes InventoryMenu and StatsMenu (core router::set_custom_ui), closes the engine's menu and opens ours. This file
// only reads the player into core panes' rows and does what the views' intents ask through the engine's own calls
// (ActorEquipManager, DropObject, AddPerk); every rule is in core/panes and tested there.
#include "core.h"
#include "argonia/core/life.h"
#include "argonia/core/panes.h"

#include <algorithm>
#include <set>
#include <string>
#include <vector>

namespace argonia::plugin {

namespace {
namespace pn = ac::panes;

std::optional<pn::Kind> KindOf(RE::TESBoundObject* o, bool& food) {
  food = false;
  switch (o->GetFormType()) {
    case RE::FormType::Weapon: return pn::Kind::weapon;
    case RE::FormType::Ammo: return pn::Kind::ammo;
    case RE::FormType::Armor: return pn::Kind::armor;
    case RE::FormType::AlchemyItem: food = o->As<RE::AlchemyItem>()->IsFood(); return pn::Kind::potion;
    case RE::FormType::Ingredient: return pn::Kind::ingredient;
    case RE::FormType::Scroll: return pn::Kind::scroll;
    case RE::FormType::Book: return pn::Kind::book;
    case RE::FormType::KeyMaster: return pn::Kind::key;
    case RE::FormType::Light: return pn::Kind::light;
    case RE::FormType::SoulGem: return pn::Kind::soulGem;
    case RE::FormType::Misc: return pn::Kind::misc;
    default: return std::nullopt;
  }
}

ac::msg::InventoryState InventoryState(std::optional<std::string> notice) {
  ac::msg::InventoryState s;
  auto* p = RE::PlayerCharacter::GetSingleton();
  if (!p) return s;
  for (auto& [obj, data] : p->GetInventory()) {
    if (!obj || data.first <= 0) continue;
    if (obj->GetFormID() == 0xF) {  // gold
      s.gold += data.first;
      continue;
    }
    bool food = false;
    const auto kind = KindOf(obj, food);
    const char* name = obj->GetName();
    if (!kind || !obj->GetPlayable() || !name || !*name) continue;
    const bool worn = data.second && data.second->IsWorn();
    ac::msg::InventoryItem it;
    it.id = pn::key(obj->GetFormID());
    it.name = name;
    it.category = pn::category(*kind, food);
    it.count = data.first;
    it.weight = (std::max)(0.0, double(obj->GetWeight()) * data.first);
    it.value = std::max<std::int64_t>(0, std::int64_t(obj->GetGoldValue()) * data.first);
    it.equipped = worn;
    it.action = pn::action(*kind, food, worn);
    s.items.push_back(std::move(it));
  }
  pn::order(s.items);
  auto* avo = p->AsActorValueOwner();
  s.carried = (std::max)(0.0, double(avo->GetActorValue(RE::ActorValue::kInventoryWeight)));
  s.capacity = (std::max)(0.0, double(avo->GetActorValue(RE::ActorValue::kCarryWeight)));
  s.notice = std::move(notice);
  return s;
}

// Each engine skill's perk tree, walked from its root in tree order (the skills a Custom Skills Framework tree
// carries are 1.3's, owed with it).
std::vector<std::pair<ac::msg::CharPerk, RE::BGSPerk*>> Perks(RE::PlayerCharacter* p) {
  std::vector<std::pair<ac::msg::CharPerk, RE::BGSPerk*>> out;
  for (const auto& m : ac::life::skill_mirrors()) {
    if (m.actor_value.empty()) continue;
    auto* info = RE::ActorValueList::GetActorValueInfo(AvNamed(m.actor_value));
    if (!info || !info->perkTree) continue;
    std::vector<RE::BGSSkillPerkTreeNode*> todo{info->perkTree};
    std::set<RE::BGSPerk*> seen;
    for (std::size_t i = 0; i < todo.size(); ++i) {
      for (auto* ch : todo[i]->children)
        if (ch) todo.push_back(ch);
      auto* perk = todo[i]->perk;
      if (!perk || !seen.insert(perk).second) continue;
      const char* n = perk->GetName();
      if (!n || !*n) continue;
      ac::msg::CharPerk c;
      c.id = pn::key(perk->GetFormID());
      c.skill = ac::msg::SkillId(std::size_t(m.skill));
      c.name = n;
      RE::BSString d;
      perk->GetDescription(d, perk);
      c.description = d.c_str() ? d.c_str() : "";
      c.taken = p->HasPerk(perk);
      c.available = !c.taken && perk->perkConditions.IsTrue(p, p);
      if (!c.taken && !c.available) c.need = "Not yet: its skill or an earlier perk first.";
      out.emplace_back(std::move(c), perk);
    }
  }
  return out;
}

ac::msg::CharsheetState SheetState(std::optional<std::string> notice) {
  auto* p = RE::PlayerCharacter::GetSingleton();
  if (!p) return {};
  auto* avo = p->AsActorValueOwner();
  const auto av = [&](RE::ActorValue a) { return (std::max)(0.0, double(avo->GetActorValue(a))); };
  const auto mx = [&](RE::ActorValue a) { return (std::max)(0.0, double(avo->GetPermanentActorValue(a))); };
  const pn::Pools pools{av(RE::ActorValue::kHealth), mx(RE::ActorValue::kHealth), av(RE::ActorValue::kMagicka),
                        mx(RE::ActorValue::kMagicka), av(RE::ActorValue::kStamina), mx(RE::ActorValue::kStamina)};
  std::vector<ac::msg::CharPerk> perks;
  for (auto& [c, perk] : Perks(p)) perks.push_back(std::move(c));
  const char* name = p->GetName();
  auto* race = p->GetRace();
  auto s = pn::charsheet(Get().state.sheet, name ? name : "", race && race->GetName() ? race->GetName() : "",
                         pools, p->GetGameStatsData().perkCount, std::move(perks));
  s.notice = std::move(notice);
  return s;
}

RE::TESBoundObject* Carried(std::string_view key, std::int32_t& count) {
  const auto id = pn::form_of(key);
  auto* p = RE::PlayerCharacter::GetSingleton();
  if (!id || !p) return nullptr;
  for (auto& [obj, data] : p->GetInventory())
    if (obj && obj->GetFormID() == *id && data.first > 0) {
      count = data.first;
      return obj;
    }
  return nullptr;
}

}  // namespace

// Under Get().lock (the router's handler and ViewIntent hold it).
void OpenInventory(std::optional<std::string> notice) {
  auto json = ac::msg::encode(InventoryState(std::move(notice)));
  if (!json) {
    SKSE::log::error("views: the inventory does not fit the schema: {}", json.error());
    return;
  }
  Push("inventory", std::move(*json));
}

void OpenCharsheet(std::optional<std::string> notice) {
  auto json = ac::msg::encode(SheetState(std::move(notice)));
  if (!json) {
    SKSE::log::error("views: the character sheet does not fit the schema: {}", json.error());
    return;
  }
  Push("charsheet", std::move(*json));
}

std::string InventoryUse(const ac::msg::InventoryUse& m) {
  std::int32_t count = 0;
  auto* o = Carried(m.item, count);
  auto* p = RE::PlayerCharacter::GetSingleton();
  bool food = false;
  const auto kind = o ? KindOf(o, food) : std::nullopt;
  if (!o || !p || !kind) {
    OpenInventory("That is no longer carried.");
    return {};
  }
  auto* eq = RE::ActorEquipManager::GetSingleton();
  bool worn = false;
  for (auto& [obj, data] : p->GetInventory())
    if (obj == o) worn = data.second && data.second->IsWorn();
  if (pn::action(*kind, food, worn).empty() || *kind == pn::Kind::book) {
    OpenInventory(*kind == pn::Kind::book ? "Read it where it lies: books open from the world for now." : "That has no use here.");
    return {};
  }
  if (worn) eq->UnequipObject(p, o);
  else eq->EquipObject(p, o);  // a potion or ingredient is drunk or eaten by equipping it, as the engine's menu does
  OpenInventory(std::nullopt);
  return {};
}

std::string InventoryDrop(const ac::msg::InventoryDrop& m) {
  std::int32_t count = 0;
  auto* o = Carried(m.item, count);
  auto* p = RE::PlayerCharacter::GetSingleton();
  if (!o || !p) {
    OpenInventory("That is no longer carried.");
    return {};
  }
  p->DropObject(o, nullptr, count);
  OpenInventory(std::nullopt);
  return {};
}

std::string CharsheetPerk(const ac::msg::CharsheetPerk& m) {
  auto* p = RE::PlayerCharacter::GetSingleton();
  if (!p) return {};
  auto perks = Perks(p);
  const auto it = std::find_if(perks.begin(), perks.end(), [&](const auto& x) { return x.first.id == m.perk; });
  const int points = p->GetGameStatsData().perkCount;
  if (auto no = pn::perk_refusal(it == perks.end() ? nullptr : &it->first, points)) {
    OpenCharsheet(std::move(*no));
    return {};
  }
  p->AddPerk(it->second);
  p->GetGameStatsData().perkCount = std::uint8_t(points - 1);
  SKSE::log::info("views: perk {} taken from our sheet", m.perk);
  OpenCharsheet(std::nullopt);
  return {};
}

}  // namespace argonia::plugin
