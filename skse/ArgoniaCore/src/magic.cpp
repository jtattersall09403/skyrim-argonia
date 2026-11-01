// Dependency mods' forms restated at data load (1.12; docs/research/2026-10-31/lane-1.12-magic.md): each mod_form
// row (core/magic over tables_magic.h) is looked up in its plugin and given our name, our description, or for a magic
// effect the magic skill of its Morrowind school. The mod's plugin is never edited or mastered (0003, 0012); a row
// whose plugin is not loaded is skipped with one log line. Each trader's mod stock (trade_class_mod_stock) is added to
// their merchant chest's base container, found through their vendor faction.
// Our magic pane (lane-1.12-magicpane): the router's magicMenu surface (P, MagicMenu) pushes magic.state built from the
// player's spells (core magic::pane_state groups them under Morrowind's six schools), and magic.equip readies a spell
// in a hand or a power in the voice slot through the engine's own ActorEquipManager.
#include "core.h"
#include "argonia/core/magic.h"

#include <algorithm>
#include <cmath>
#include <format>

#ifdef GetObject  // windows.h maps it to GetObjectA, hiding BGSDefaultObjectManager::GetObject
#undef GetObject
#endif

namespace argonia::plugin {

namespace {

namespace mg = ac::magic;

// Merchant stock from dependency mods. Each row's chest is found through the trader's vendor faction.
struct StockAt {
  const ac::gen::ModStockRow* row;
  RE::TESBoundObject* item;
  RE::TESObjectREFR* chest;
};
std::vector<StockAt> Stock(bool log) {
  std::vector<StockAt> out;
  auto* dh = RE::TESDataHandler::GetSingleton();
  for (const auto& r : ac::gen::kModStock) {
    auto* npc = Lookup<RE::TESNPC>(r.npc);
    auto* form = (dh->LookupLoadedModByName(r.plugin) || dh->LookupLoadedLightModByName(r.plugin))
                     ? dh->LookupForm(r.local_id, r.plugin) : nullptr;  // untyped: the typed lookup refused a BOOK (mp10)
    auto* item = form ? form->As<RE::TESBoundObject>() : nullptr;
    RE::TESObjectREFR* chest = nullptr;
    if (npc)
      for (const auto& fr : npc->factions)
        if (fr.faction && fr.faction->vendorData.merchantContainer) chest = fr.faction->vendorData.merchantContainer;
    if (item && chest) out.push_back({&r, item, chest});
    else if (log)
      SKSE::log::warn("magic: stock {:06X}:{} for {} skipped ({})", r.local_id, r.plugin, r.npc,
                      !item ? "form not loaded" : "no merchant chest");
  }
  return out;
}

// At data load, into the chest's base container (a chest the save has never filled lists it from there).
void AddModStock() {
  int added = 0;
  for (const auto& s : Stock(true))
    if (auto* base = s.chest->GetBaseObject() ? s.chest->GetBaseObject()->As<RE::TESObjectCONT>() : nullptr) {
      base->AddObjectToContainer(s.item, s.row->count, nullptr);
      ++added;
    }
  SKSE::log::info("magic: {} of {} mod stock rows added to merchant chests", added, ac::gen::kModStock.size());
}

}  // namespace

// At each load: a chest whose inventory the save already holds (mp7: Livia's barter showed no tome) is topped up to
// each row's count on the reference itself.
void MagicGameReady() {
  int topped = 0;
  for (const auto& s : Stock(false)) {
    const auto counts = s.chest->GetInventoryCounts();
    const auto it = counts.find(s.item);
    const int have = it == counts.end() ? 0 : it->second;
    if (have < s.row->count) {
      s.chest->AddObjectToContainer(s.item, nullptr, s.row->count - have, nullptr);
      ++topped;
    }
  }
  SKSE::log::info("magic: {} mod stock rows topped up in merchant chests at load", topped);
}

namespace {

std::string Hex(RE::FormID id) { return std::format("{:08X}", id); }

// An effect's school: its mod_form row (by plugin and local id), else its magic skill's name.
std::optional<ac::msg::MagicSchool> EffectSchool(RE::EffectSetting* e) {
  if (!e) return std::nullopt;
  const ac::magic::ModFormRow* row = nullptr;
  if (auto* file = e->GetFile(0)) row = mg::find(file->GetFilename(), e->GetLocalFormID());
  const char* av = e->GetMagickSkill() == RE::ActorValue::kNone ? nullptr : RE::ActorValueList::GetActorValueName(e->GetMagickSkill());
  return mg::school_of(row, av ? av : "");  // no magic skill: no name (a null name crashed the first run, mp3)
}

std::vector<mg::Known> KnownSpells() {
  std::vector<mg::Known> out;
  auto* p = RE::PlayerCharacter::GetSingleton();
  if (!p) return out;
  auto& rd = p->GetActorRuntimeData();
  auto add = [&](RE::SpellItem* sp) {
    if (!sp) return;
    const auto t = sp->GetSpellType();
    const bool power = t == RE::MagicSystem::SpellType::kPower || t == RE::MagicSystem::SpellType::kLesserPower;
    if (!power && t != RE::MagicSystem::SpellType::kSpell) return;  // abilities, diseases, shouts: not the pane's
    mg::Known k;
    k.id = Hex(sp->GetFormID());
    k.name = sp->GetFullName() ? sp->GetFullName() : k.id;
    k.cost = std::lround(sp->CalculateMagickaCost(p));
    k.power = power;
    if (auto* top = sp->GetCostliestEffectItem()) k.school = EffectSchool(top->baseEffect);
    for (auto* e : sp->effects)
      if (!k.school && e) k.school = EffectSchool(e->baseEffect);
    if (!power && !k.school) SKSE::log::info("magic: {} ({}) has no school; listed under Alteration", k.name, k.id);
    k.left = rd.selectedSpells[RE::Actor::SlotTypes::kLeftHand] == sp;
    k.right = rd.selectedSpells[RE::Actor::SlotTypes::kRightHand] == sp;
    k.voice = rd.selectedPower == sp;
    out.push_back(std::move(k));
  };
  for (auto* sp : rd.addedSpells) add(sp);
  if (auto* base = p->GetActorBase(); base && base->actorEffects)
    for (std::uint32_t i = 0; base->actorEffects->spells && i < base->actorEffects->numSpells; ++i)
      add(base->actorEffects->spells[i]);
  if (auto* race = p->GetRace())
    if (race->actorEffects)
      for (std::uint32_t i = 0; race->actorEffects->spells && i < race->actorEffects->numSpells; ++i)
        add(race->actorEffects->spells[i]);
  return out;
}

std::vector<ac::msg::MagicActive> ActiveEffects() {
  std::vector<ac::msg::MagicActive> out;
  auto* p = RE::PlayerCharacter::GetSingleton();
  auto* list = p ? p->AsMagicTarget()->GetActiveEffectList() : nullptr;
  if (!list) return out;
  for (auto* ae : *list) {
    auto* e = ae ? ae->GetBaseObject() : nullptr;
    if (!e || ae->flags.any(RE::ActiveEffect::Flag::kInactive) ||
        e->data.flags.any(RE::EffectSetting::EffectSettingData::Flag::kHideInUI))
      continue;
    const char* n = e->GetFullName();
    if (!n || !*n) continue;
    const double left = ae->duration > 0 ? ae->duration - ae->elapsedSeconds : 0;
    out.push_back({n, mg::active_detail(ae->magnitude, left)});
  }
  std::sort(out.begin(), out.end(), [](const auto& a, const auto& b) { return a.name < b.name; });
  return out;
}

}  // namespace

// Under Get().lock (the router's handler and ViewIntent hold it).
void OpenMagic(std::optional<std::string> notice) {
  auto json = ac::msg::encode(mg::pane_state(KnownSpells(), ActiveEffects(), std::move(notice)));
  if (!json) {
    SKSE::log::error("views: the magic pane does not fit the schema: {}", json.error());
    return;
  }
  Push("magic", std::move(*json));
}

std::string MagicIntent(const ac::msg::MagicEquip& m) {
  const auto known = KnownSpells();
  const auto* k = mg::find_known(known, m.spell);
  auto* p = RE::PlayerCharacter::GetSingleton();
  std::optional<std::string> notice;
  if (!k || !p) notice = "That spell is not known.";
  else notice = mg::equip_refusal(*k, m.hand);
  if (!notice) {
    auto* sp = RE::TESForm::LookupByID<RE::SpellItem>(std::stoul(m.spell, nullptr, 16));
    auto* dom = RE::BGSDefaultObjectManager::GetSingleton();
    const auto which = m.hand == ac::msg::Hand::left ? RE::DEFAULT_OBJECT::kLeftHandEquip
                     : m.hand == ac::msg::Hand::right ? RE::DEFAULT_OBJECT::kRightHandEquip
                                                     : RE::DEFAULT_OBJECT::kVoiceEquip;
    auto* slot = dom ? dom->GetObject<RE::BGSEquipSlot>(which) : nullptr;
    if (sp && slot) {
      RE::ActorEquipManager::GetSingleton()->EquipSpell(p, sp, slot);
      SKSE::log::info("magic: {} ({}) readied {}", k->name, m.spell, ac::msg::kHandNames[std::size_t(m.hand)]);
    } else {
      notice = "That spell cannot be readied.";
    }
  }
  if (notice) SKSE::log::info("magic: equip {} refused: {}", m.spell, *notice);
  OpenMagic(notice);
  return {};
}

// The pane's reads for the journey (the bridge's views report): what each hand holds now.
std::vector<std::string> MagicReport() {
  std::vector<std::string> out;
  for (const auto& k : KnownSpells()) {
    if (k.left) out.push_back("magic left " + k.name);
    if (k.right) out.push_back("magic right " + k.name);
    if (k.voice) out.push_back("magic power " + k.name);
  }
  // The mod stock on the traders' chests: rows whose item the chest holds now, of all rows.
  int held = 0;
  for (const auto& s : Stock(false)) {
    const auto counts = s.chest->GetInventoryCounts();
    const auto it = counts.find(s.item);
    held += it != counts.end() && it->second > 0;
  }
  out.push_back(std::format("magic stock {}/{}", held, ac::gen::kModStock.size()));
  return out;
}

void MagicDataLoaded() {
  auto* dh = RE::TESDataHandler::GetSingleton();
  if (!dh) return;
  int named = 0, described = 0, moved = 0, missing = 0;
  for (const auto& r : ac::gen::kModForms) {
    if (!dh->LookupLoadedModByName(r.plugin) && !dh->LookupLoadedLightModByName(r.plugin)) {
      ++missing;
      continue;
    }
    auto* form = dh->LookupForm(r.local_id, r.plugin);
    if (!form) {
      SKSE::log::warn("magic: {:06X}:{} not found", r.local_id, r.plugin);
      ++missing;
      continue;
    }
    if (auto n = ac::magic::rename(r)) {
      if (auto* full = form->As<RE::TESFullName>()) {
        full->fullName = std::string(*n);
        ++named;
      }
    }
    if (auto* mgef = form->As<RE::EffectSetting>()) {
      if (auto d = ac::magic::redescribe(r)) {
        mgef->magicItemDescription = std::string(*d);
        ++described;
      }
      const std::string_view current = RE::ActorValueList::GetActorValueName(mgef->GetMagickSkill());
      if (auto av = ac::magic::school_av(r, current)) {
        const auto value = RE::ActorValueList::LookupActorValueByName(std::string(*av).c_str());
        if (value != RE::ActorValue::kNone) {
          mgef->data.associatedSkill = value;
          ++moved;
        }
      }
    }
  }
  SKSE::log::info("magic: {} renamed, {} described, {} moved school, {} missing; {} effects of a school with no "
                  "Skyrim actor value stay under their mod's",
                  named, described, moved, missing, ac::magic::unshown_schools().size());
  AddModStock();
}

}  // namespace argonia::plugin
