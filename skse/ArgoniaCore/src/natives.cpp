// The Papyrus natives (papyrus/ArgoniaCore.psc). The quest natives are what 1.4's generated fragments call, one per
// action verb (docs/research/journals/quests.md's native rule); each goes through the seam (actions::run checks and
// applies it) and then steps the watched quests. No condition is evaluated in Papyrus. The read natives are the L4
// journeys' hands (tests/journeys/{cosave,quest-board,dialogue-intercept,attributes}*).
#include "core.h"
#include "argonia/core/version.h"

namespace argonia::plugin {

namespace {

using Arg = ac::conditions::Arg;
using Strings = std::vector<RE::BSFixedString>;

std::string Str(const RE::BSFixedString& s) { return s.c_str() ? std::string(s.c_str()) : std::string(); }

bool Act(std::string_view verb, std::vector<Arg> args) {
  auto& c = Get();
  std::lock_guard l(c.lock);
  auto out = Session().act(verb, std::move(args));
  for (const auto& why : out.refused) SKSE::log::warn("{}: {}", verb, why);
  if (out.done) FactsChanged(verb);
  return out.done;
}

std::optional<std::string> QuestId(RE::TESQuest* q, std::string_view native) {
  auto id = WorldId(q);
  if (!id) SKSE::log::error("{}: {:08X} is not a quest of ours", native, q ? q->GetFormID() : 0u);
  return id;
}

RE::BSFixedString Version(RE::StaticFunctionTag*) { return argonia::core::kVersionString; }

std::int32_t SaveCount(RE::StaticFunctionTag*) {
  std::lock_guard l(Get().lock);
  return static_cast<std::int32_t>(Get().state.meta.save_count);
}

bool WatchQuest(RE::StaticFunctionTag*, RE::TESQuest* q) {
  auto id = QuestId(q, "WatchQuest");
  if (!id) return false;
  std::string why;
  {
    std::lock_guard l(Get().lock);
    if (!Session().watch(*id, &why)) {
      SKSE::log::error("{}", why);
      return false;
    }
  }
  SKSE::log::info("quests: watching {}", *id);
  FactsChanged("watch " + *id);
  return true;
}

bool UnwatchQuest(RE::StaticFunctionTag*, RE::TESQuest* q) {
  auto id = QuestId(q, "UnwatchQuest");
  std::lock_guard l(Get().lock);
  return id && Session().unwatch(*id);
}

bool AddJournalEntry(RE::StaticFunctionTag*, RE::TESQuest* q, std::int32_t stage, std::int32_t kind) {
  auto id = QuestId(q, "AddJournalEntry");
  if (!id) return false;
  std::lock_guard l(Get().lock);
  const auto date = GameEngine{}.date().value_or(ac::seam::Date{});
  std::string why;
  if (!Session().add_journal_entry(*id, stage, kind, date, &why)) {
    SKSE::log::warn("{}", why);
    return false;
  }
  SKSE::log::info("journal: {} stage {} kind {} on {}-{}-{}", *id, stage, kind, date.year, date.month + 1, date.day);
  return true;
}

bool GrantTopic(RE::StaticFunctionTag*, RE::BSFixedString t) { return Act("grantTopic", {Str(t)}); }
bool SetFlag(RE::StaticFunctionTag*, RE::BSFixedString f, bool v) { return Act("setFlag", {Str(f), v}); }
bool ApplyLocalVariant(RE::StaticFunctionTag*, RE::BSFixedString place, RE::BSFixedString variant) {
  return Act("applyLocalVariant", {Str(place), Str(variant)});
}
bool SetPrice(RE::StaticFunctionTag*, RE::BSFixedString service, std::int32_t price) {
  return Act("setPrice", {Str(service), static_cast<double>(price)});
}
bool GiveItem(RE::StaticFunctionTag*, RE::BSFixedString item, std::int32_t n) {
  return Act("giveItem", {Str(item), static_cast<double>(n)});
}
bool TakeItem(RE::StaticFunctionTag*, RE::BSFixedString item, std::int32_t n) {
  return Act("takeItem", {Str(item), static_cast<double>(n)});
}
bool GiveGold(RE::StaticFunctionTag*, std::int32_t n) { return Act("giveGold", {static_cast<double>(n)}); }
bool TakeGold(RE::StaticFunctionTag*, std::int32_t n) { return Act("takeGold", {static_cast<double>(n)}); }
bool ChangeDisposition(RE::StaticFunctionTag*, RE::BSFixedString npc, std::int32_t delta) {
  return Act("changeDisposition", {Str(npc), static_cast<double>(delta)});
}
bool ChangeSettlementStanding(RE::StaticFunctionTag*, RE::BSFixedString place, std::int32_t delta) {
  return Act("changeSettlementStanding", {Str(place), static_cast<double>(delta)});
}

bool OpenDialogueNative(RE::StaticFunctionTag*, RE::TESObjectREFR* target) { return OpenDialogue(target); }
RE::BSFixedString ViewIntentNative(RE::StaticFunctionTag*, RE::BSFixedString json) { return ViewIntent(Str(json)); }
RE::BSFixedString ViewState(RE::StaticFunctionTag*, RE::BSFixedString view) {
  std::lock_guard l(Get().lock);
  auto it = Get().views.find(Str(view));
  return it == Get().views.end() ? RE::BSFixedString() : RE::BSFixedString(it->second);
}

float GetAttribute(RE::StaticFunctionTag*, RE::BSFixedString name) {
  auto a = ac::seam::attribute_named(Str(name));
  std::lock_guard l(Get().lock);
  return a ? static_cast<float>(ac::seam::attribute(Get().state, *a)) : -1.0f;
}

float SetAttribute(RE::StaticFunctionTag*, RE::BSFixedString name, float v) {
  auto a = ac::seam::attribute_named(Str(name));
  if (!a) {
    SKSE::log::warn("SetAttribute: no attribute {}", Str(name));
    return -1.0f;
  }
  double stored = 0;
  {
    std::lock_guard l(Get().lock);
    stored = ac::seam::set_attribute(Get().state, *a, v);
  }
  MirrorAttributes();
  FactsChanged("attribute");
  return static_cast<float>(stored);
}

Strings Families(RE::StaticFunctionTag*) {
  Strings out;
  std::lock_guard l(Get().lock);
  for (auto id : Get().families.ids()) out.emplace_back(ac::families::fourcc_name(id));
  return out;
}

RE::BSFixedString FamilyDigest(RE::StaticFunctionTag*, RE::BSFixedString fourcc) {
  std::lock_guard l(Get().lock);
  return ac::seam::digest(Get().families, ac::cosave::fourcc(Str(fourcc)));
}

Strings RouterLog(RE::StaticFunctionTag*) {
  Strings out;
  std::lock_guard l(Get().lock);
  for (const auto& line : Get().router_log) out.emplace_back(line);
  return out;
}

bool GetFlag(RE::StaticFunctionTag*, RE::BSFixedString flag) {
  std::lock_guard l(Get().lock);
  return ac::quest_state::flag(Get().state.quests, Str(flag));
}

bool KnowsTopic(RE::StaticFunctionTag*, RE::BSFixedString topic) {
  std::lock_guard l(Get().lock);
  return Get().state.known.knows(Str(topic));
}

std::int32_t GetDisposition(RE::StaticFunctionTag*, RE::BSFixedString npc) {
  std::lock_guard l(Get().lock);
  return ac::seam::disposition_of(Get().state, Str(npc));
}

// The journal family as lines "<quest world id> <stage> <kind> <year>-<month>-<day>", oldest first.
Strings JournalEntries(RE::StaticFunctionTag*) {
  Strings out;
  std::lock_guard l(Get().lock);
  for (const auto& e : Get().state.log.entries) {
    std::string quest = std::to_string(e.quest);
    for (const auto& g : Get().graphs)
      if (ac::seam::key(g.id) == e.quest) quest = g.id;
    out.emplace_back(quest + " " + std::to_string(e.entry) + " " + std::to_string(static_cast<int>(e.kind)) + " " +
                     std::to_string(e.date.year) + "-" + std::to_string(e.date.month) + "-" + std::to_string(e.date.day));
  }
  return out;
}

}  // namespace

bool RegisterNatives(RE::BSScript::IVirtualMachine* vm) {
  constexpr auto k = "ArgoniaCore"sv;
  vm->RegisterFunction("Version"sv, k, Version);
  vm->RegisterFunction("SaveCount"sv, k, SaveCount);
  vm->RegisterFunction("WatchQuest"sv, k, WatchQuest);
  vm->RegisterFunction("UnwatchQuest"sv, k, UnwatchQuest);
  vm->RegisterFunction("AddJournalEntry"sv, k, AddJournalEntry);
  vm->RegisterFunction("GrantTopic"sv, k, GrantTopic);
  vm->RegisterFunction("SetFlag"sv, k, SetFlag);
  vm->RegisterFunction("ApplyLocalVariant"sv, k, ApplyLocalVariant);
  vm->RegisterFunction("SetPrice"sv, k, SetPrice);
  vm->RegisterFunction("GiveItem"sv, k, GiveItem);
  vm->RegisterFunction("TakeItem"sv, k, TakeItem);
  vm->RegisterFunction("GiveGold"sv, k, GiveGold);
  vm->RegisterFunction("TakeGold"sv, k, TakeGold);
  vm->RegisterFunction("ChangeDisposition"sv, k, ChangeDisposition);
  vm->RegisterFunction("ChangeSettlementStanding"sv, k, ChangeSettlementStanding);
  vm->RegisterFunction("OpenDialogue"sv, k, OpenDialogueNative);
  vm->RegisterFunction("ViewIntent"sv, k, ViewIntentNative);
  vm->RegisterFunction("ViewState"sv, k, ViewState);
  vm->RegisterFunction("GetAttribute"sv, k, GetAttribute);
  vm->RegisterFunction("SetAttribute"sv, k, SetAttribute);
  vm->RegisterFunction("Families"sv, k, Families);
  vm->RegisterFunction("FamilyDigest"sv, k, FamilyDigest);
  vm->RegisterFunction("RouterLog"sv, k, RouterLog);
  vm->RegisterFunction("GetFlag"sv, k, GetFlag);
  vm->RegisterFunction("KnowsTopic"sv, k, KnowsTopic);
  vm->RegisterFunction("GetDisposition"sv, k, GetDisposition);
  vm->RegisterFunction("JournalEntries"sv, k, JournalEntries);
  return true;
}

}  // namespace argonia::plugin
