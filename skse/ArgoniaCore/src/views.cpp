// The web-view binding (1.2 §0): ArgoniaCore opens, feeds and closes our views through PrismaUI's published API.
// The host's rules (which view is open, what waits for DOM ready) are skse/core's views::Host; this file turns its
// ops into PrismaUI calls, hands intents from JS to ViewIntent on the main thread, and builds the journal's, the
// chart's and the HUD's states. If PrismaUI.dll is absent the views stay off: the dialogue intercept's window has
// nowhere to draw (logged), and the journal and map keys keep the vanilla menus (their handlers are not registered).
// The router's surfaces: journalMenu (the "Journal" user event, J and the pad's Back, never Escape's System tab),
// mapMenu (our chart: decision 0017's 1.2 §0 record says why it replaces FWMF's map), the HUD (always on; the
// vanilla HUD's bars and compass hidden through the hudElements hook, router::kHudClips). The chart's revealed
// cells: the player's exterior cell in ARG_Province is marked on every cell change (BGSActorCellEvent) and at load.
#include "core.h"
#include "prisma_api.h"

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <Windows.h>

#include <algorithm>

#include <atomic>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <thread>

namespace argonia::plugin {

namespace {

prisma::Api1* g_api = nullptr;
prisma::Api2* g_api2 = nullptr;
std::map<std::string, prisma::View, std::less<>> g_ids;  // our view id -> PrismaUI's handle (set once, at data loaded)
std::atomic<bool> g_hud_loop{false};
ac::views::ClosePressGuard g_close_guard;  // under Get().lock
std::string g_vanilla_hud = "vanilla-hud not yet hidden";  // ViewsReport's line: what the last hide found

double Now() {
  return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();
}

std::optional<std::string> ViewOf(prisma::View h) {
  for (const auto& [id, v] : g_ids)
    if (v == h) return id;
  return std::nullopt;
}

void Apply(const std::vector<ac::views::Op>& ops) {
  if (!g_api) return;
  for (const auto& op : ops) {
    auto it = g_ids.find(op.view);
    if (it == g_ids.end()) continue;
    const auto v = it->second;
    switch (op.kind) {
      case ac::views::OpKind::push:
        g_api->InteropCall(v, std::string(ac::views::kPushFunction).c_str(), op.arg.c_str());
        break;
      case ac::views::OpKind::show: g_api->Show(v); break;
      case ac::views::OpKind::hide: g_api->Hide(v); break;
      case ac::views::OpKind::focus: g_api->Focus(v, true, false); break;  // pauses the game, as Morrowind's windows
      case ac::views::OpKind::unfocus: g_api->Unfocus(v); break;
    }
  }
}

void OnDomReady(prisma::View h) {
  SKSE::GetTaskInterface()->AddTask([h] {
    auto& c = Get();
    std::lock_guard l(c.lock);
    auto id = ViewOf(h);
    if (!id) return;
    SKSE::log::info("views: {} ready", *id);
    Apply(c.view_host.ready(*id));
  });
}

void OnJsIntent(const char* text) {
  if (!text) return;
  SKSE::GetTaskInterface()->AddTask([s = std::string(text)] { ViewIntent(s); });
}

void OnJsConsole(prisma::View h, prisma::ConsoleLevel level, const char* message) {
  if (level != prisma::ConsoleLevel::error && level != prisma::ConsoleLevel::warning) return;
  const auto id = ViewOf(h);
  SKSE::log::warn("views: {} console: {}", id ? *id : "?", message ? message : "");
}

// --- the chart's remembered view: a settings file beside the SKSE logs (per install, as Morrowind's layout) -------
std::optional<std::filesystem::path> LayoutPath() {
  auto dir = SKSE::log::log_directory();
  if (!dir) return std::nullopt;
  return *dir / "ArgoniaUI-chart.json";
}

std::optional<std::string> ReadLayout() {
  auto p = LayoutPath();
  if (!p) return std::nullopt;
  std::ifstream f(*p, std::ios::binary);
  if (!f) return std::nullopt;
  std::stringstream ss;
  ss << f.rdbuf();
  return ss.str();
}

void WriteLayout(const ac::msg::ChartView& v) {
  auto p = LayoutPath();
  if (!p) return;
  std::ofstream f(*p, std::ios::binary | std::ios::trunc);
  f << ac::views::chart_layout_text(v);
  if (!f) SKSE::log::warn("views: the chart layout was not written to {}", p->string());
}

// --- the chart ---------------------------------------------------------------------------------------------------
void OpenChart() {
  // The revealed cells from the CHRT family; the view read on every opening (a restart reads the same file).
  auto json = ac::msg::encode(ac::views::chart_state(Get().state.chart, ac::views::remembered_chart(ReadLayout())));
  if (!json) {
    SKSE::log::error("views: the chart does not fit the schema: {}", json.error());
    return;
  }
  Push("chart", std::move(*json));
}

// The player's cell, if it is an exterior cell of ARG_Province, joins the revealed set (logged when new).
void MarkPlayerCell(std::string_view why) {
  auto* p = RE::PlayerCharacter::GetSingleton();
  auto* cell = p ? p->GetParentCell() : nullptr;
  auto* ws = p ? p->GetWorldspace() : nullptr;
  if (!cell || !ws || !cell->IsExteriorCell()) return;
  const char* edid = ws->GetFormEditorID();
  if (!edid || std::string_view(edid) != ac::chart::kWorldspace) return;
  const auto* xy = cell->GetCoordinates();
  if (!xy) return;
  auto& c = Get();
  std::lock_guard l(c.lock);
  if (ac::chart::reveal(c.state.chart, {xy->cellX, xy->cellY}))
    SKSE::log::info("chart: cell {},{} revealed ({}), {} in all", xy->cellX, xy->cellY, why,
                    ac::chart::count(c.state.chart));
}

class CellSink final : public RE::BSTEventSink<RE::BGSActorCellEvent> {
 public:
  // Enter or leave: the player's parent cell is read, so a leave re-marks the cell already marked (a no-op).
  RE::BSEventNotifyControl ProcessEvent(const RE::BGSActorCellEvent* e, RE::BSTEventSource<RE::BGSActorCellEvent>*) override {
    if (e) SKSE::GetTaskInterface()->AddTask([] { MarkPlayerCell("cell change"); });
    return RE::BSEventNotifyControl::kContinue;
  }
};

// --- the vanilla HUD (1.2 §d) ------------------------------------------------------------------------------------
// Each clip of router::hidden_hud_clips() is held hidden by three locks (router.h, kHudModes: game-10 read "0 out of
// HudElements" and the clips back with the next mode): _visible false now; its mode members deleted, so
// HUDMovieBase.SetMode's hasOwnProperty(mode) is false in every mode; _alpha 0, which no mode change touches; and its
// entry taken out of HudElements (router::hud_list_removals: by identity, our mark or _name). The movie stays: the
// crosshair and subtitles are restyled rows. Run at every HUD Menu opening and every load; only while our views are
// bound, so a missing PrismaUI leaves the vanilla bars (the player is never without health).
void HideVanillaHud() {
  if (!g_api) return;
  auto* ui = RE::UI::GetSingleton();
  auto menu = ui ? ui->GetMenu<RE::HUDMenu>() : RE::GPtr<RE::HUDMenu>{};
  auto* movie = menu ? menu->uiMovie.get() : nullptr;
  if (!movie) {
    g_vanilla_hud = "vanilla-hud no movie";
    return;
  }
  const std::string root(ac::router::kHudRoot);
  RE::GFxValue list;
  std::string list_name;
  for (const char* n : {"HudElements", "HUDElements"})
    if (movie->GetVariable(&list, (root + "." + n).c_str()) && list.IsArray()) {
      list_name = n;
      break;
    }
  const auto clips = ac::router::hidden_hud_clips();
  std::vector<RE::GFxValue> found;
  std::size_t hidden = 0, modes = 0, faded = 0;
  std::string missing, seen;  // seen: the first clip's members, for the Views line when a lock does not take
  for (auto clip : clips) {
    const std::string path = root + "." + std::string(clip);
    RE::GFxValue v;
    if (!movie->GetVariable(&v, path.c_str()) || !v.IsDisplayObject()) {
      missing += " " + std::string(clip);
      continue;
    }
    movie->SetVariable((path + "._visible").c_str(), RE::GFxValue(false));
    if (movie->SetVariable((path + "._alpha").c_str(), RE::GFxValue(0.0))) ++faded;
    std::vector<std::string> members;
    v.VisitMembers([&](const char* name, const RE::GFxValue&) { if (name) members.emplace_back(name); });
    if (seen.empty() && !members.empty()) {
      for (std::size_t i = 0; i < members.size() && i < 12; ++i) seen += (i ? "," : "") + members[i];
      seen = std::string(clip) + "{" + seen + "}";
    }
    for (auto m : ac::router::kHudModes) members.emplace_back(m);  // deleted by name too: a visit may skip them
    for (const auto& m : members)
      if (ac::router::is_hud_mode(m) && v.HasMember(m.c_str())) v.DeleteMember(m.c_str());
    v.SetMember("argoniaHidden", RE::GFxValue(true));
    found.push_back(v);
    ++hidden;
  }
  std::uint32_t size = 0;
  std::size_t listed = 0;
  if (!list_name.empty()) {
    size = list.GetArraySize();
    std::vector<ac::router::HudListEntry> entries(size);
    for (std::uint32_t i = 0; i < size; ++i) {
      RE::GFxValue el, mark, name;
      if (!list.GetElement(i, &el) || !(el.IsObject() || el.IsDisplayObject())) continue;
      for (const auto& f : found) entries[i].same_object |= el == f;
      entries[i].marked = el.GetMember("argoniaHidden", &mark) && mark.IsBool() && mark.GetBool();
      if (el.GetMember("_name", &name) && name.IsString()) entries[i].name = name.GetString();
    }
    for (auto i : ac::router::hud_list_removals(entries, clips)) list.RemoveElement(i);
    // the end state, not this call's delta (later calls find nothing left to remove): hidden clips no longer listed
    size = list.GetArraySize();
    for (auto f : found) {
      bool in = false;
      for (std::uint32_t i = 0; i < size && !in; ++i) {
        RE::GFxValue el;
        in = list.GetElement(i, &el) && el == f;
      }
      listed += !in;
    }
  }
  // likewise modes: clips with no mode member left (the first call deleted them, later calls find none)
  for (auto f : found) {
    bool any = false;
    for (auto m : ac::router::kHudModes) any |= f.HasMember(std::string(m).c_str());
    modes += !any;
  }
  g_vanilla_hud = "vanilla-hud hidden " + std::to_string(hidden) + "/" + std::to_string(clips.size()) +
                  (list_name.empty() ? ", no HudElements list"
                                     : ", " + std::to_string(listed) + " out of " + list_name + " (" +
                                           std::to_string(size) + " listed)") +
                  ", modes absent " + std::to_string(modes) + ", alpha 0 " + std::to_string(faded) + (missing.empty() ? "" : ", missing:" + missing) + (seen.empty() ? "" : ", members " + seen);
  SKSE::log::info("views: {}", g_vanilla_hud);
}

class HudMenuSink final : public RE::BSTEventSink<RE::MenuOpenCloseEvent> {
 public:
  RE::BSEventNotifyControl ProcessEvent(const RE::MenuOpenCloseEvent* e, RE::BSTEventSource<RE::MenuOpenCloseEvent>*) override {
    if (e && e->opening && e->menuName == RE::HUDMenu::MENU_NAME)
      SKSE::GetTaskInterface()->AddTask([] {
        std::lock_guard l(Get().lock);
        HideVanillaHud();
      });
    return RE::BSEventNotifyControl::kContinue;
  }
};

// --- the journal -------------------------------------------------------------------------------------------------
void OpenJournal(const ac::msg::JournalPage& at) {
  auto& c = Get();
  auto name = [&c](ac::journal::QuestId q) {
    ac::views::QuestNames n{std::to_string(q), std::to_string(q)};
    for (const auto& g : c.graphs)
      if (ac::seam::key(g.id) == q) {
        n.id = g.id;
        auto* quest = Lookup<RE::TESQuest>(g.id);
        const char* full = quest ? quest->GetFullName() : nullptr;
        n.name = full && *full ? full : g.id;
      }
    return n;
  };
  // The entry's words are the stage's log entry and directions from the quest rows (generated/journal_text.h).
  auto json = ac::msg::encode(
      ac::views::journal_state(c.state.log, name, ac::views::entry_text, ac::views::entry_directions, at));
  if (!json) {
    SKSE::log::error("views: the journal does not fit the schema: {}", json.error());
    return;
  }
  Push("journal", std::move(*json));
}

// --- the HUD -----------------------------------------------------------------------------------------------------
std::vector<ac::msg::Bar> Bars() {
  std::vector<ac::msg::Bar> out;
  auto* p = RE::PlayerCharacter::GetSingleton();
  if (!p) return out;
  auto* avo = p->AsActorValueOwner();
  auto bar = [&](ac::msg::BarKind k, RE::ActorValue av) {
    const double now = (std::max)(0.0f, avo->GetActorValue(av));
    const double max = (std::max)(0.0f, avo->GetPermanentActorValue(av));
    out.push_back({k, now, (std::max)(max, now), true});
  };
  bar(ac::msg::BarKind::health, RE::ActorValue::kHealth);
  bar(ac::msg::BarKind::stamina, RE::ActorValue::kStamina);
  bar(ac::msg::BarKind::magicka, RE::ActorValue::kMagicka);
  out.push_back({ac::msg::BarKind::breath, 0, 0, false});  // breath and climb join with 2.13 and 2.14
  out.push_back({ac::msg::BarKind::climb, 0, 0, false});
  return out;
}

void PushHudState() {
  auto& c = Get();
  ac::msg::HudState s;
  s.visible = !c.view_host.modal().has_value();
  s.bars = Bars();
  auto* p = RE::PlayerCharacter::GetSingleton();
  s.sneak = {p && p->IsSneaking(), 0.0};
  s.vastei = {std::int64_t(c.state.prog.vastei), std::nullopt};
  for (const auto& n : ac::journal::live(c.journal_notices, Now()))
    s.notices.push_back({"journal-" + std::to_string(n.seq), ac::msg::NoticeKind::journal,
                         std::string(ac::journal::kNoticeText)});
  c.hud_bars = s.bars;
  if (auto json = ac::msg::encode(s)) Push("hud", std::move(*json));
  else SKSE::log::error("views: the HUD does not fit the schema: {}", json.error());
}

void JournalNoticeNow(ac::journal::NoticeCause cause, std::string quest, std::int32_t mark) {
  auto& c = Get();
  std::lock_guard l(c.lock);
  const auto n = ac::journal::notify(c.journal_notices, cause, quest, mark, Now());
  const char* what = cause == ac::journal::NoticeCause::entry ? "entry" : "clue";
  if (!n) {
    SKSE::log::info("journal notice: {} {} {} merged into the last", quest, what, mark);
    return;
  }
  // The engine's own notification (the HUD's message block, never among the hidden clips) and our HUD's stack.
  RE::SendHUDMessage::ShowHUDMessage(std::string(ac::journal::kNoticeText).c_str());
  if (g_api) PushHudState();
  // Sent on the main thread: from the view's thread (game-16) no sink ever saw it.
  SKSE::GetTaskInterface()->AddTask([str = quest + " " + what, mark] {
    SKSE::ModCallbackEvent ev{"ArgoniaJournalNotice", RE::BSFixedString(str), static_cast<float>(mark), nullptr};
    if (auto* src = SKSE::GetModCallbackEventSource()) src->SendEvent(&ev);
    else SKSE::log::warn("journal notice: no mod callback event source; ArgoniaJournalNotice not sent");
  });
  SKSE::log::info("journal notice {}: {} {} {}", n->seq, quest, what, mark);
}

void PushHudBars() {
  auto& c = Get();
  std::lock_guard l(c.lock);
  if (!g_api || c.view_host.modal()) return;
  auto bars = Bars();
  if (bars == c.hud_bars) return;
  c.hud_bars = bars;
  if (auto json = ac::msg::encode(ac::msg::HudBars{std::move(bars)})) {
    c.views["hud"] = *json;  // ViewState reads it; the host keeps the full state for a page reload
    Apply({{ac::views::OpKind::push, "hud", std::move(*json)}});
  }
}

// --- the journal key ---------------------------------------------------------------------------------------------
class InputSink final : public RE::BSTEventSink<RE::InputEvent*> {
 public:
  RE::BSEventNotifyControl ProcessEvent(RE::InputEvent* const* events, RE::BSTEventSource<RE::InputEvent*>*) override {
    const auto* ue = RE::UserEvents::GetSingleton();
    for (auto* e = events ? *events : nullptr; e && ue; e = e->next) {
      if (e->GetEventType() != RE::INPUT_EVENT_TYPE::kButton) continue;
      const auto* b = e->AsButtonEvent();
      if (!b) continue;
      if (b->IsDown() && b->QUserEvent() == ue->journal) {
        std::lock_guard l(Get().lock);
        Get().journal_key.press(Now());
      }
      // A press that began in one of our views ends there: its repeats and release lose their user event, so the
      // game (TK Dodge on the sprint key) never reads the B that closed the view as gameplay input.
      const auto key = (std::uint32_t(b->GetDevice()) << 16) | std::uint32_t(b->GetIDCode());
      bool swallow;
      {
        std::lock_guard l(Get().lock);
        swallow = g_close_guard.swallow(key, b->IsDown(), b->IsUp(), Get().view_host.modal().has_value());
      }
      if (swallow) const_cast<RE::ButtonEvent*>(b)->strUserEvent = "";
    }
    return RE::BSEventNotifyControl::kContinue;
  }
};

void OnJournalSurface(ac::router::SurfaceId) { OpenJournal({ac::msg::JournalTab::entries, 0, std::nullopt}); }
void OnMapSurface(ac::router::SurfaceId) { OpenChart(); }

}  // namespace

bool ViewsBound() { return g_api != nullptr; }

void ViewsPostLoad() {
  auto* dll = GetModuleHandleA(prisma::kDll);
  auto request = dll ? reinterpret_cast<prisma::RequestApi>(GetProcAddress(dll, prisma::kEntry)) : nullptr;
  if (!request) {
    SKSE::log::warn("views: {} is not loaded; our views are off and the vanilla menus pass", prisma::kDll);
    return;
  }
  g_api2 = static_cast<prisma::Api2*>(request(prisma::Version::v2));
  g_api = g_api2 ? g_api2 : static_cast<prisma::Api1*>(request(prisma::Version::v1));
  SKSE::log::info("views: PrismaUI API {}", g_api2 ? "v2" : g_api ? "v1" : "refused");
}

void ViewsDataLoaded() {
  auto& c = Get();
  std::lock_guard l(c.lock);
  if (!g_api) return;
  for (const auto& s : ac::views::kViews) {
    const auto v = g_api->CreateView(std::string(s.page).c_str(), OnDomReady);
    g_ids[std::string(s.id)] = v;
    g_api->SetOrder(v, s.order);
    g_api->RegisterJSListener(v, std::string(ac::views::kIntentFunction).c_str(), OnJsIntent);
    if (g_api2) g_api2->RegisterConsoleCallback(v, OnJsConsole);
    SKSE::log::info("views: {} created from PrismaUI/views/{}", s.id, s.page);
  }
  std::string why;
  for (auto [s, h] : {std::pair{ac::router::SurfaceId::journalMenu, &OnJournalSurface},
                      std::pair{ac::router::SurfaceId::mapMenu, &OnMapSurface}}) {
    if (c.router.handle(s, h, &why)) c.router_log.push_back("handler " + std::string(ac::router::name(s)));
    else c.router_log.push_back("refused: " + why);
  }
  static InputSink input;
  if (auto* idm = RE::BSInputDeviceManager::GetSingleton()) idm->AddEventSink<RE::InputEvent*>(&input);
  static CellSink cells;
  if (auto* p = RE::PlayerCharacter::GetSingleton()) p->AsBGSActorCellEventSource()->AddEventSink(&cells);
  if (c.router.install(ac::router::HookId::hudElements, &why)) {
    static HudMenuSink hud;
    if (auto* ui = RE::UI::GetSingleton()) ui->AddEventSink<RE::MenuOpenCloseEvent>(&hud);
    c.router_log.push_back("hook hudElements: the HUD movie's clips hidden at each HUD Menu opening and load");
  } else {
    c.router_log.push_back("refused: " + why);
  }
  c.router_log.push_back("sinks: InputEvent (the journal key), BGSActorCellEvent (the chart's cells)");
  if (!g_hud_loop.exchange(true))
    std::thread([] {
      for (;;) {
        std::this_thread::sleep_for(std::chrono::milliseconds(200));  // 5 bar updates a second, only on change
        SKSE::GetTaskInterface()->AddTask([] { PushHudBars(); });
      }
    }).detach();
}

void ViewsGameReady() {
  auto& c = Get();
  std::lock_guard l(c.lock);
  MarkPlayerCell("load");
  HideVanillaHud();
  PushHudState();
}

void JournalNotice(ac::journal::NoticeCause cause, std::string_view quest, std::int32_t mark) {
  // On the main thread: a native runs on a Papyrus thread, and the HUD and the event sinks expect the main one.
  SKSE::GetTaskInterface()->AddTask([cause, q = std::string(quest), mark] { JournalNoticeNow(cause, q, mark); });
}

bool JournalKeyTaken() { return Get().journal_key.take(Now()); }

void Push(std::string_view view, std::string json) {
  auto& c = Get();
  SKSE::log::info("view {} <- {}", view, json);
  c.views[std::string(view)] = json;
  const bool was_modal = c.view_host.modal().has_value();
  Apply(c.view_host.push(view, std::move(json)));
  if (view != "hud" && was_modal != c.view_host.modal().has_value()) PushHudState();
}

void CloseView(std::string_view view) {
  auto& c = Get();
  c.views.erase(std::string(view));
  const bool was_modal = c.view_host.modal().has_value();
  Apply(c.view_host.close(view));
  if (was_modal != c.view_host.modal().has_value()) PushHudState();
}

void CloseAllViews() {
  auto& c = Get();
  for (const auto& s : ac::views::kViews)
    if (s.modal) c.views.erase(std::string(s.id));
  Apply(c.view_host.close_all());
}

std::string JournalIntent(const ac::msg::JournalPage& at) {
  auto& c = Get();
  std::lock_guard l(c.lock);
  OpenJournal(at);
  return c.views.contains("journal") ? c.views["journal"] : std::string();
}

std::string ChartIntent(const ac::msg::ChartPan& pan) {
  std::lock_guard l(Get().lock);
  WriteLayout(pan.view);  // the view has already moved; ArgoniaCore remembers where
  return {};
}

std::string ViewProbe(std::string_view topics) {
  auto& c = Get();
  std::lock_guard l(c.lock);
  std::size_t n = 300;
  try {
    n = std::clamp<std::size_t>(std::stoul(std::string(topics)), 1, 1000);
  } catch (...) {
  }
  c.talk.reset();
  auto json = ac::msg::encode(ac::views::probe_dialogue("npc.imperial-fringe.claywater-station.well-keeper",
                                                       "Livia (probe)", n));
  if (!json) return R"({"error":"the probe window does not fit the schema"})";
  Push("dialogue", *json);
  return *json;
}

std::vector<std::string> ViewsReport() {
  auto& c = Get();
  std::lock_guard l(c.lock);
  std::vector<std::string> out;
  out.push_back(std::string("bound ") + (g_api2 ? "v2" : g_api ? "v1" : "no"));
  out.push_back(g_vanilla_hud);
  out.push_back("chart revealed " + std::to_string(ac::chart::count(c.state.chart)));
  for (const auto& s : ac::views::kViews)
    out.push_back(std::string(s.id) + (c.view_host.is_ready(s.id) ? " ready" : " loading") +
                  (c.view_host.is_open(s.id) ? " open" : " closed"));
  return out;
}

}  // namespace argonia::plugin
