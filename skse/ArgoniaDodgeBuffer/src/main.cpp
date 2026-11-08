// ArgoniaDodgeBuffer (owner ruling #51): the attack button pressed during a TK Dodge RE dodge is queued and played
// as the dodge ends. Also the Dark Souls backstab (owner walk 3): an attack pressed behind a hostile casts Rim Parry's
// backstab at it (core/backstab.h has the geometry), then plays its execution without a second press. The rules are in core/buffer.h (unit-tested); this file only joins them to the engine: an
// animation-graph event sink on the player, an input sink, and a task that sends the attack event on the next frame.
// Address Library only (CommonLibSSE-NG), so it is version independent; settings in Data/SKSE/Plugins/ArgoniaDodgeBuffer.ini.
#include <spdlog/sinks/basic_file_sink.h>

#include <atomic>
#include <chrono>
#include <cmath>
#include <fstream>
#include <optional>
#include <sstream>

#include "backstab.h"
#include "buffer.h"

namespace db = argonia::dodgebuffer;
namespace bs = argonia::backstab;

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

// Rim Parry and Execution's records (RimExecutionHitSA.esp, the CTD fix's copy; EREP_patchSA.esp overrides 0x822).
constexpr auto kRimPlugin = "RimExecutionHitSA.esp"sv;
constexpr RE::FormID kBackstabSpell = 0x822;     // EldenBlockCounterSA: the spell every player bash clip casts
                                                 // (PIE.$EldenCounterattackSA); EREP's copy is BackStabShoot + ExeBackStab
constexpr RE::FormID kMarkEffect = 0x843;        // NewCastSpellScript_OpenSA: "execution allowed" on the player (3 s);
                                                 // its script casts kExecuteSpell on the next attack press
constexpr RE::FormID kMarkSpell = 0x841;         // EldenMarkSA, which carries kMarkEffect
constexpr RE::FormID kExecuteSpell = 0xA7A;      // ExeCheckExplode: the script's HitSpell, which starts the execution
constexpr RE::FormID kExecutingKeyword = 0x84B;  // EldenBackOverKillSA: the execution clips' OAR condition

class Plugin : public RE::BSTEventSink<RE::BSAnimationGraphEvent>,
               public RE::BSTEventSink<RE::InputEvent*>,
               public RE::BSTEventSink<RE::TESMagicEffectApplyEvent> {
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

  // The player's graph is rebuilt on a load, and again when the race menu or a 3D reload replaces it: take the sink
  // off and on again so it is on exactly once. At kNewGame the graph does not exist yet and the add is refused (owner
  // walk 2026-11-07: refused at the new game, so no dodge was ever seen and no attack was queued), so the input sink
  // re-attaches on a button press at most once a second (Reattach), and the next dodge is seen whatever rebuilt the graph.
  void AttachGraph(bool quiet = false) {
    auto* player = RE::PlayerCharacter::GetSingleton();
    if (!player) return;
    player->RemoveAnimationGraphEventSink(this);
    const bool ok = player->AddAnimationGraphEventSink(this);
    lastAttach_ = Now();
    if (!quiet || ok != graphAttached_) SKSE::log::info("animation graph sink on the player: {}", ok ? "added" : "REFUSED");
    graphAttached_ = ok;
  }

  void Reattach() {
    if (Now() - lastAttach_ < 1.0 || !Enabled()) return;
    auto* ui = RE::UI::GetSingleton();
    if (!ui || ui->GameIsPaused()) return;
    AttachGraph(true);
  }

  void AttachInput() {
    if (inputAttached_) return;
    if (auto* dm = RE::BSInputDeviceManager::GetSingleton()) {
      dm->AddEventSink<RE::InputEvent*>(this);
      inputAttached_ = true;
      SKSE::log::info("input sink added");
    }
  }

  void AttachMagic() {
    if (magicAttached_) return;
    if (auto* h = RE::ScriptEventSourceHolder::GetSingleton()) {
      h->AddEventSink<RE::TESMagicEffectApplyEvent>(this);
      magicAttached_ = true;
    }
    auto* dh = RE::TESDataHandler::GetSingleton();
    if (!dh) return;
    backstabSpell_ = dh->LookupForm<RE::SpellItem>(kBackstabSpell, kRimPlugin);
    executeSpell_ = dh->LookupForm<RE::SpellItem>(kExecuteSpell, kRimPlugin);
    markSpell_ = dh->LookupForm<RE::SpellItem>(kMarkSpell, kRimPlugin);
    markEffect_ = dh->LookupForm<RE::EffectSetting>(kMarkEffect, kRimPlugin);
    executingKeyword_ = dh->LookupForm<RE::BGSKeyword>(kExecutingKeyword, kRimPlugin);
    SKSE::log::info("backstab: spell {}, mark {}, execute {} ({})", backstabSpell_ ? "found" : "MISSING",
                    markEffect_ ? "found" : "MISSING", executeSpell_ ? "found" : "MISSING", kRimPlugin);
  }

  // A press of the attack button: the Dark Souls backstab (owner walk 3). Main thread (input events).
  void TryBackstab() {
    db::Settings s;
    {
      std::lock_guard l(lock_);
      if (!buffer_ || buffer_->dodging()) return;
      s = buffer_->settings();
    }
    if (!s.backstab || !backstabSpell_) return;
    const auto ctx = EngineContext();
    auto* player = RE::PlayerCharacter::GetSingleton();
    if (ctx.in_menu || !ctx.weapon_drawn || !player || player->IsDead() || player->IsInKillMove() ||
        player->IsBlocking() || player->IsOnMount())
      return;  // block + attack is the bash, which Rim Parry answers itself
    if (Now() - lastBackstab_ < 1.0) return;
    const bs::Rule rule{s.backstab_reach, s.backstab_height, s.backstab_behind_deg, s.backstab_facing_deg};
    const auto pp = player->GetPosition();
    const bs::Pose me{pp.x, pp.y, pp.z, player->GetAngleZ()};
    RE::Actor* best = nullptr;
    double bestDist = 1e9;
    auto* pl = RE::ProcessLists::GetSingleton();
    if (!pl) return;
    for (auto& h : pl->highActorHandles) {
      auto a = h.get();
      if (!a || a.get() == player || a->IsDead() || a->IsInKillMove() || a->IsPlayerTeammate() ||
          a->IsCommandedActor() || a->IsDisabled() || !a->Is3DLoaded() || !a->IsHostileToActor(player))
        continue;
      const auto tp = a->GetPosition();
      const bs::Pose them{tp.x, tp.y, tp.z, a->GetAngleZ()};
      if (bs::check(me, them, rule) != bs::Why::Ok) continue;
      const double d = std::hypot(tp.x - pp.x, tp.y - pp.y);
      if (d < bestDist) {
        bestDist = d;
        best = a.get();
      }
    }
    if (!best) return;
    lastBackstab_ = Now();
    pendingExecute_ = s.backstab_execute ? lastBackstab_ : 0.0;
    auto* caster = player->GetMagicCaster(RE::MagicSystem::CastingSource::kInstant);
    if (!caster) return;
    caster->CastSpellImmediate(backstabSpell_, false, best, 1.0f, false, 0.0f, player);
    SKSE::log::info("backstab: cast at {:08X} '{}' ({:.0f} units)", best->GetFormID(), best->GetName(), bestDist);
  }

  // Rim Parry marks the player for the execution (kMarkEffect) once the backstab stagger lands; its script then waits
  // for another press. After an attack that started a backstab, the execution plays at once, as in Dark Souls.
  RE::BSEventNotifyControl ProcessEvent(const RE::TESMagicEffectApplyEvent* e,
                                        RE::BSTEventSource<RE::TESMagicEffectApplyEvent>*) override {
    if (!e || !e->target || !e->target->IsPlayerRef() || !markEffect_ || e->magicEffect != markEffect_->GetFormID())
      return RE::BSEventNotifyControl::kContinue;
    const double t = pendingExecute_.load();
    if (t <= 0.0 || Now() - t > 3.0) return RE::BSEventNotifyControl::kContinue;
    pendingExecute_ = 0.0;
    SKSE::GetTaskInterface()->AddTask([this] {
      auto* player = RE::PlayerCharacter::GetSingleton();
      if (!player || !executeSpell_ || player->IsDead()) return;
      if (executingKeyword_ && player->HasMagicEffectWithKeyword(executingKeyword_)) return;  // already executing
      if (auto* caster = player->GetMagicCaster(RE::MagicSystem::CastingSource::kInstant))
        caster->CastSpellImmediate(executeSpell_, false, player, 1.0f, false, 0.0f, player);
      // as the mark's script does after its cast: the mark goes, so a later press does not cast it twice
      if (auto* list = player->AsMagicTarget()->GetActiveEffectList())
        for (auto* ae : *list)
          if (ae && ae->spell == markSpell_) ae->Dispel(true);
      SKSE::log::info("backstab: execution cast");
    });
    return RE::BSEventNotifyControl::kContinue;
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
      if (b && b->IsDown()) Reattach();
      if (b && b->IsDown() && IsAttackButton(b)) TryBackstab();
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
  bool magicAttached_ = false;
  RE::SpellItem* backstabSpell_ = nullptr;
  RE::SpellItem* executeSpell_ = nullptr;
  RE::SpellItem* markSpell_ = nullptr;
  RE::EffectSetting* markEffect_ = nullptr;
  RE::BGSKeyword* executingKeyword_ = nullptr;
  double lastBackstab_ = 0.0;
  std::atomic<double> pendingExecute_{0.0};
  bool graphAttached_ = false;  // main thread only (load messages and input events)
  double lastAttach_ = 0.0;
};

void OnMessage(SKSE::MessagingInterface::Message* m) {
  switch (m->type) {
    case SKSE::MessagingInterface::kInputLoaded:
    case SKSE::MessagingInterface::kDataLoaded:
      Plugin::Get().AttachInput();
      if (m->type == SKSE::MessagingInterface::kDataLoaded) Plugin::Get().AttachMagic();
      break;
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
