// The Papyrus natives (papyrus/ArgoniaCore.psc). The quest natives are what 1.4's generated fragments call, one per
// action verb (docs/research/journals/quests.md's native rule); each goes through the seam (actions::run checks and
// applies it) and then steps the watched quests. No condition is evaluated in Papyrus. The read natives are the L4
// journeys' hands (tests/journeys/{cosave,quest-board,dialogue-intercept,attributes}*).
#include "core.h"
#include "argonia/core/bridge_call.h"
#include "argonia/core/version.h"

#include <algorithm>
#include <cctype>
#include <format>

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

}  // namespace

bool MeetThing(const RE::TESForm* record, ac::things::Hook how) {
  const char* way = how == ac::things::Hook::activate ? "activated" : "read";
  auto id = WorldId(record);
  const auto* row = id ? ac::things::hook_for(*id, how) : nullptr;
  if (!row) return false;  // not a quest thing met this way: nothing to set, nothing logged (every book opens here)
  const bool ok = Act("setFlag", {std::string(row->flag), true});
  SKSE::log::info("things: {} {} sets {} ({}){}", *id, way, row->flag, row->quest, ok ? "" : ", refused");
  return ok;
}

namespace {

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
  JournalNotice(ac::journal::NoticeCause::entry, *id, stage);
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
  // BSFixedString pools strings case-insensitively: "dialogue" can come back as an older "Dialogue" (game-9: the
  // pushed dialogue state read null), and every view name is lower case.
  auto name = Str(view);
  std::ranges::transform(name, name.begin(), [](unsigned char ch) { return static_cast<char>(std::tolower(ch)); });
  std::lock_guard l(Get().lock);
  auto it = Get().views.find(name);
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
  WriteCombat("attribute");
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

// --- 1.5: grow, die, rest, save --------------------------------------------------------------------------------
bool RestAtNative(RE::StaticFunctionTag*, RE::TESObjectREFR* spot) { return RestAt(spot); }
// ARG_PRKF_ThingHook's one call: the activated reference's base, met as a quest thing (1.4).
bool ThingActivated(RE::StaticFunctionTag*, RE::TESObjectREFR* ref) {
  return MeetThing(ref ? ref->GetBaseObject() : nullptr, ac::things::Hook::activate);
}
RE::BSFixedString RestNotice(RE::StaticFunctionTag*) {
  std::lock_guard l(Get().lock);
  return Get().rest_notice;
}
float TakeVasteiNative(RE::StaticFunctionTag*, RE::TESObjectREFR* pile) {
  auto got = TakeVastei(pile);
  return got ? static_cast<float>(*got) : -1.0f;
}
RE::BSFixedString SittingIntentNative(RE::StaticFunctionTag*, RE::BSFixedString json) { return SittingIntent(Str(json)); }
bool SuspendSave(RE::StaticFunctionTag*, RE::BSFixedString why) { return SuspendSaveFor(Str(why)); }
float GetVastei(RE::StaticFunctionTag*) {
  std::lock_guard l(Get().lock);
  return static_cast<float>(Get().state.prog.vastei);
}
float SetVastei(RE::StaticFunctionTag*, float v) {
  std::lock_guard l(Get().lock);
  Get().state.prog.vastei = (std::max)(0.0, static_cast<double>(v));
  return static_cast<float>(Get().state.prog.vastei);
}
std::int32_t GetPendingLevels(RE::StaticFunctionTag*) {
  std::lock_guard l(Get().lock);
  return Get().state.prog.pending_levels;
}
std::int32_t GetLevel(RE::StaticFunctionTag*) {
  std::lock_guard l(Get().lock);
  return Get().state.sheet.level;
}
float GetSkill(RE::StaticFunctionTag*, RE::BSFixedString name) {
  auto s = ac::life::skill_named(Str(name));
  std::lock_guard l(Get().lock);
  return s ? static_cast<float>(Get().state.sheet.s[*s]) : -1.0f;
}
std::string PosText(const ac::rest::Pos& p) {
  return std::format("{:.2f} {:.2f} {:.2f} {:08X}", p.x, p.y, p.z, p.cell);
}
RE::BSFixedString PileState(RE::StaticFunctionTag*) {
  std::lock_guard l(Get().lock);
  const auto& pile = Get().state.death.pile;
  return pile ? PosText(pile->at) + std::format(" {:.0f}", pile->vastei) : std::string();
}
RE::BSFixedString WakePoint(RE::StaticFunctionTag*) {
  std::lock_guard l(Get().lock);
  const auto& w = Get().state.death.wake;
  return w ? PosText(*w) : std::string();
}
bool SittingOpen(RE::StaticFunctionTag*) {
  std::lock_guard l(Get().lock);
  return Get().sitting.has_value();
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
  vm->RegisterFunction("RestAt"sv, k, RestAtNative);
  vm->RegisterFunction("ThingActivated"sv, k, ThingActivated);
  vm->RegisterFunction("RestNotice"sv, k, RestNotice);
  vm->RegisterFunction("TakeVastei"sv, k, TakeVasteiNative);
  vm->RegisterFunction("SittingIntent"sv, k, SittingIntentNative);
  vm->RegisterFunction("SuspendSave"sv, k, SuspendSave);
  vm->RegisterFunction("GetVastei"sv, k, GetVastei);
  vm->RegisterFunction("SetVastei"sv, k, SetVastei);
  vm->RegisterFunction("GetPendingLevels"sv, k, GetPendingLevels);
  vm->RegisterFunction("GetLevel"sv, k, GetLevel);
  vm->RegisterFunction("GetSkill"sv, k, GetSkill);
  vm->RegisterFunction("PileState"sv, k, PileState);
  vm->RegisterFunction("WakePoint"sv, k, WakePoint);
  vm->RegisterFunction("SittingOpen"sv, k, SittingOpen);
  return true;
}

// The dev bridge's `core <Native> [arg]` (argonia/core/bridge_call.h): the same natives a script calls, on the main
// thread, their value encoded for the reply. The whitelist is checked first, so no setter is reachable from here.
std::expected<std::string, std::string> BridgeCall(std::string_view native, const std::optional<std::string>& arg) {
  namespace bc = ac::bridge_call;
  if (auto why = bc::refuse(native, arg.has_value())) return std::unexpected(*why);
  const RE::BSFixedString a(arg ? arg->c_str() : "");
  auto list = [&](const Strings& s) {
    std::vector<std::string> out;
    for (const auto& x : s) out.push_back(Str(x));
    return bc::encode_list(native, out);
  };
  const auto n = native;
  if (n == "Version") return bc::encode_text(n, Str(Version(nullptr)));
  if (n == "SaveCount") return bc::encode_number(n, SaveCount(nullptr));
  if (n == "ViewIntent") return bc::encode_json(n, Str(ViewIntentNative(nullptr, a)));
  if (n == "ViewState") return bc::encode_json(n, Str(ViewState(nullptr, a)));
  if (n == "GetAttribute") return bc::encode_number(n, GetAttribute(nullptr, a));
  if (n == "Families") return list(Families(nullptr));
  if (n == "FamilyDigest") return bc::encode_text(n, Str(FamilyDigest(nullptr, a)));
  if (n == "RouterLog") return list(RouterLog(nullptr));
  if (n == "GetFlag") return bc::encode_bool(n, GetFlag(nullptr, a));
  if (n == "KnowsTopic") return bc::encode_bool(n, KnowsTopic(nullptr, a));
  if (n == "GetDisposition") return bc::encode_number(n, GetDisposition(nullptr, a));
  if (n == "JournalEntries") return list(JournalEntries(nullptr));
  if (n == "RestNotice") return bc::encode_text(n, Str(RestNotice(nullptr)));
  if (n == "SittingIntent") return bc::encode_json(n, Str(SittingIntentNative(nullptr, a)));
  if (n == "GetVastei") return bc::encode_number(n, GetVastei(nullptr));
  if (n == "GetPendingLevels") return bc::encode_number(n, GetPendingLevels(nullptr));
  if (n == "GetLevel") return bc::encode_number(n, GetLevel(nullptr));
  if (n == "GetSkill") return bc::encode_number(n, GetSkill(nullptr, a));
  if (n == "PileState") return bc::encode_text(n, Str(PileState(nullptr)));
  if (n == "WakePoint") return bc::encode_text(n, Str(WakePoint(nullptr)));
  if (n == "SittingOpen") return bc::encode_bool(n, SittingOpen(nullptr));
  if (n == "ViewProbe") return bc::encode_json(n, ViewProbe(*arg));
  if (n == "Views") return bc::encode_list(n, ViewsReport());
  return std::unexpected("whitelisted but not wired: " + std::string(native));  // a new whitelist row needs a line here
}

bool HandleBridgeCore(SKSE::MessagingInterface::Message* m) {
  namespace bc = ac::bridge_call;
  if (!m || m->type != bc::kBridgeCoreMessage || !m->data || m->dataLen != sizeof(bc::BridgeCore)) return false;
  auto* req = static_cast<bc::BridgeCore*>(m->data);
  req->native[sizeof(req->native) - 1] = '\0';
  req->arg[sizeof(req->arg) - 1] = '\0';
  auto r = BridgeCall(req->native, req->has_arg ? std::optional<std::string>(req->arg) : std::nullopt);
  const std::string& text = r ? *r : r.error();
  char* into = r ? req->json : req->error;
  const std::size_t cap = r ? sizeof(req->json) : sizeof(req->error);
  req->ok = r.has_value() && text.size() < cap;
  if (r && !req->ok) {
    std::string why = "the value is " + std::to_string(text.size()) + " bytes, over the reply's room";
    why.copy(req->error, (std::min)(why.size(), sizeof(req->error) - 1));
    return true;
  }
  text.copy(into, (std::min)(text.size(), cap - 1));  // (std::min): windows.h defines min
  return true;
}

}  // namespace argonia::plugin
