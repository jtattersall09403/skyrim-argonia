// ArgoniaDodgeBuffer (owner ruling #51): the attack button pressed during a TK Dodge RE dodge is queued and played
// as the dodge ends. The rules are in core/buffer.h (unit-tested); this file only joins them to the engine: an
// animation-graph event sink on the player, an input sink, and a task that sends the attack event on the next frame.
// Address Library only (CommonLibSSE-NG), so it is version independent; settings in Data/SKSE/Plugins/ArgoniaDodgeBuffer.ini.
#include <spdlog/sinks/basic_file_sink.h>

#include <chrono>
#include <fstream>
#include <optional>
#include <sstream>

#include "buffer.h"

namespace db = argonia::dodgebuffer;

namespace {

constexpr auto kIni = "Data/SKSE/Plugins/ArgoniaDodgeBuffer.ini";

double Now() {
  using namespace std::chrono;
  return duration<double>(steady_clock::now().time_since_epoch()).count();
}

db::Settings LoadSettings() {
  db::Settings s;
  std::ifstream f(kIni);
  if (!f) {
    SKSE::log::warn("{} not found: defaults", kIni);
    return s;
  }
  std::stringstream ss;
  ss << f.rdbuf();
  for (const auto& k : db::parse_ini(ss.str(), s)) SKSE::log::warn("ini: unknown key {}", k);
  return s;
}

void SetupLog() {
  auto path = SKSE::log::log_directory();
  if (!path) return;
  *path /= "ArgoniaDodgeBuffer.log";
  auto log = std::make_shared<spdlog::logger>("global log",
                                              std::make_shared<spdlog::sinks::basic_file_sink_mt>(path->string(), true));
  log->set_level(spdlog::level::info);
  log->flush_on(spdlog::level::info);
  spdlog::set_default_logger(std::move(log));
  spdlog::set_pattern("[%H:%M:%S] [%l] %v");
}

db::Context EngineContext() {
  db::Context c;
  auto* ui = RE::UI::GetSingleton();
  c.in_menu = !ui || ui->GameIsPaused() || ui->IsMenuOpen(RE::DialogueMenu::MENU_NAME);
  auto* player = RE::PlayerCharacter::GetSingleton();
  c.weapon_drawn = player && player->AsActorState()->IsWeaponDrawn();
  return c;
}

class Plugin : public RE::BSTEventSink<RE::BSAnimationGraphEvent>, public RE::BSTEventSink<RE::InputEvent*> {
 public:
  static Plugin& Get() {
    static Plugin p;
    return p;
  }

  void Init() {
    std::lock_guard l(lock_);
    buffer_.emplace(LoadSettings());
    const auto& s = buffer_->settings();
    SKSE::log::info("enabled {}, buffer {} s, power hold {} s, user event '{}', attack '{}', power '{}'", s.enabled,
                    s.buffer_seconds, s.power_hold_seconds, s.user_event, s.attack_event, s.power_event);
  }

  bool Enabled() {
    std::lock_guard l(lock_);
    return buffer_ && buffer_->settings().enabled;
  }

  // The player's graph is rebuilt on a load: take the sink off and on again so it is on exactly once.
  void AttachGraph() {
    auto* player = RE::PlayerCharacter::GetSingleton();
    if (!player) return;
    player->RemoveAnimationGraphEventSink(this);
    const bool ok = player->AddAnimationGraphEventSink(this);
    SKSE::log::info("animation graph sink on the player: {}", ok ? "added" : "REFUSED");
  }

  void AttachInput() {
    if (inputAttached_) return;
    if (auto* dm = RE::BSInputDeviceManager::GetSingleton()) {
      dm->AddEventSink<RE::InputEvent*>(this);
      inputAttached_ = true;
      SKSE::log::info("input sink added");
    }
  }

  RE::BSEventNotifyControl ProcessEvent(const RE::BSAnimationGraphEvent* e,
                                        RE::BSTEventSource<RE::BSAnimationGraphEvent>*) override {
    if (!e || !e->holder || !e->holder->IsPlayerRef()) return RE::BSEventNotifyControl::kContinue;
    const std::string_view tag = e->tag.c_str();
    db::Fire fire = db::Fire::None;
    {
      std::lock_guard l(lock_);
      if (!buffer_) return RE::BSEventNotifyControl::kContinue;
      const bool was = buffer_->dodging();
      fire = buffer_->on_graph_event(tag, Now(), EngineContext());
      if (!was && buffer_->dodging()) SKSE::log::info("dodge started ({})", tag);
    }
    if (fire != db::Fire::None) Queue(fire, tag);
    return RE::BSEventNotifyControl::kContinue;
  }

  RE::BSEventNotifyControl ProcessEvent(RE::InputEvent* const* events, RE::BSTEventSource<RE::InputEvent*>*) override {
    if (!events) return RE::BSEventNotifyControl::kContinue;
    for (auto* e = *events; e; e = e->next) {
      if (e->GetEventType() != RE::INPUT_EVENT_TYPE::kButton) continue;
      auto* b = e->AsButtonEvent();
      if (!b || !(b->IsDown() || b->IsUp()) || !IsAttackButton(b)) continue;
      std::lock_guard l(lock_);
      if (!buffer_) continue;
      const bool was = buffer_->buffered();
      buffer_->on_button(b->IsDown(), Now());
      if (!was && buffer_->buffered()) SKSE::log::info("attack press buffered");
    }
    return RE::BSEventNotifyControl::kContinue;
  }

 private:
  // Not a hardcoded key: the control map says which key or button (per device) is the configured user event.
  bool IsAttackButton(const RE::ButtonEvent* b) {
    std::string userEvent;
    {
      std::lock_guard l(lock_);
      if (!buffer_) return false;
      userEvent = buffer_->settings().user_event;
    }
    if (b->QUserEvent() == userEvent.c_str()) return true;
    auto* cm = RE::ControlMap::GetSingleton();
    if (!cm) return false;
    const auto key = cm->GetMappedKey(userEvent, b->GetDevice(), RE::UserEvents::INPUT_CONTEXT_ID::kGameplay);
    return key != RE::ControlMap::kInvalid && key == b->GetIDCode();
  }

  void Queue(db::Fire fire, std::string_view why) {
    SKSE::log::info("dodge ended on '{}': sending a {} attack next frame", why, fire == db::Fire::Power ? "power" : "light");
    SKSE::GetTaskInterface()->AddTask([this, fire] {
      std::string ev;
      {
        std::lock_guard l(lock_);
        if (!buffer_) return;
        ev = fire == db::Fire::Power ? buffer_->settings().power_event : buffer_->settings().attack_event;
      }
      auto* player = RE::PlayerCharacter::GetSingleton();
      if (!player) return;
      const bool ok = player->NotifyAnimationGraph(ev.c_str());
      SKSE::log::info("NotifyAnimationGraph('{}') -> {}", ev, ok);
      if (!ok) {
        std::lock_guard l(lock_);
        buffer_->rejected();  // one more try, at the next end event
      }
    });
  }

  std::mutex lock_;
  std::optional<db::Buffer> buffer_;
  bool inputAttached_ = false;
};

void OnMessage(SKSE::MessagingInterface::Message* m) {
  switch (m->type) {
    case SKSE::MessagingInterface::kInputLoaded:
    case SKSE::MessagingInterface::kDataLoaded: Plugin::Get().AttachInput(); break;
    case SKSE::MessagingInterface::kPostLoadGame:
    case SKSE::MessagingInterface::kNewGame:
      if (Plugin::Get().Enabled()) Plugin::Get().AttachGraph();
      break;
    default: break;
  }
}

}  // namespace

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* skse) {
  SKSE::Init(skse);
  SetupLog();
  SKSE::log::info("ArgoniaDodgeBuffer loading on runtime {}", skse->RuntimeVersion().string("."));
  Plugin::Get().Init();
  if (!SKSE::GetMessagingInterface()->RegisterListener(OnMessage)) {
    SKSE::log::critical("SKSE messaging listener not registered");
    return false;
  }
  return true;
}
