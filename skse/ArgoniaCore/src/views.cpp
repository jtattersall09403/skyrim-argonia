// The web-view binding (1.2 §0): ArgoniaCore opens, feeds and closes our views through PrismaUI's published API.
// The host's rules (which view is open, what waits for DOM ready) are skse/core's views::Host; this file turns its
// ops into PrismaUI calls, hands intents from JS to ViewIntent on the main thread, and builds the journal's, the
// chart's and the HUD's states. If PrismaUI.dll is absent the views stay off: the dialogue intercept's window has
// nowhere to draw (logged), and the journal and map keys keep the vanilla menus (their handlers are not registered).
// The router's surfaces: journalMenu (the "Journal" user event, J and the pad's Back, never Escape's System tab),
// mapMenu (our chart: decision 0017's 1.2 §0 record says why it replaces FWMF's map), the HUD (always on).
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
  ac::msg::ChartState s;
  s.worldspace = "argonia";
  s.sketch = "chart.sketch";
  // The revealed cells and discovered places are 1.2 §e's co-save family (owed); the sketch shows everywhere.
  s.view = ac::views::remembered_chart(ReadLayout());  // read on every opening: a restart reads the same file
  auto json = ac::msg::encode(s);
  if (!json) {
    SKSE::log::error("views: the chart does not fit the schema: {}", json.error());
    return;
  }
  Push("chart", std::move(*json));
}

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
  // The entry's text is the stage's log line in the record; its table into core is 1.4's (owed): the date and the
  // quest's heading show meanwhile.
  auto text = [](ac::journal::QuestId, ac::journal::EntryId) { return std::string(); };
  auto json = ac::msg::encode(ac::views::journal_state(c.state.log, name, text, at));
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
  c.hud_bars = s.bars;
  if (auto json = ac::msg::encode(s)) Push("hud", std::move(*json));
  else SKSE::log::error("views: the HUD does not fit the schema: {}", json.error());
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
      if (b && b->IsDown() && b->QUserEvent() == ue->journal) {
        std::lock_guard l(Get().lock);
        Get().journal_key.press(Now());
      }
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
  c.router_log.push_back("sinks: InputEvent (the journal key)");
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
  PushHudState();
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
  for (const auto& s : ac::views::kViews)
    out.push_back(std::string(s.id) + (c.view_host.is_ready(s.id) ? " ready" : " loading") +
                  (c.view_host.is_open(s.id) ? " open" : " closed"));
  return out;
}

}  // namespace argonia::plugin
