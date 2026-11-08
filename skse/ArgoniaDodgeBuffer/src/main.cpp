// ArgoniaDodgeBuffer (owner ruling #51): the attack button pressed during a TK Dodge RE dodge is queued and played
// as the dodge ends. Also the Dark Souls backstab (owner walks 3 and 4): an attack pressed behind a hostile casts Rim
// Parry's backstab at it (core/backstab.h has the geometry); once its stagger lands and the swing ends, the player plays
// Rim Parry's execution on it (EldenSkillSA), with no second press and no mark to wait for. The rules are in core/buffer.h (unit-tested); this file only joins them to the engine: an
// animation-graph event sink on the player, an input sink, and a task that sends the attack event on the next frame.
// Address Library only (CommonLibSSE-NG), so it is version independent; settings in Data/SKSE/Plugins/ArgoniaDodgeBuffer.ini.
#include <spdlog/sinks/basic_file_sink.h>

#include <atomic>
#include <chrono>
#include <cmath>
#include <fstream>
#include <optional>
#include <sstream>
#include <thread>

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
constexpr RE::FormID kMarkEffect = 0x843;        // NewCastSpellScript_OpenSA: Rim Parry's "execution allowed" mark on
                                                 // the player, sent seconds after the stagger (CastSpellOnRefWhenActive);
                                                 // ours has already played the execution, so the mark is dispelled
constexpr RE::FormID kMarkSpell = 0x841;         // EldenMarkSA, which carries kMarkEffect
constexpr RE::FormID kStaggerKeyword = 0xA35;    // ExeBackStabStagger: ExeBackStab (0xA34) landed, the big stagger
constexpr RE::FormID kConfirmKeyword = 0xA21;    // ExecutionConfirmRP: the victim may be executed (AllowExecutionMarkerRP,
                                                 // its red light); the execution clip's locate explosion needs it
constexpr RE::FormID kAllowSpell = 0xA23;        // ExeStaggerAllowExe: gives kConfirmKeyword (the stagger clip casts it)
constexpr RE::FormID kSkillSpell = 0x849;        // EldenSkillSA: on the player, kExecutingKeyword plus IdleCombatStart,
                                                 // which OAR plays as the execution clip for the weapon held
constexpr RE::FormID kExecutingKeyword = 0x84B;  // EldenBackOverKillSA: the execution clips' OAR condition
constexpr double kStaggerWait = 0.6;             // seconds for the stagger to land before the backstab counts as refused
constexpr double kSwingWait = 1.5;               // seconds, at most, for the player's own swing to end

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
    markSpell_ = dh->LookupForm<RE::SpellItem>(kMarkSpell, kRimPlugin);
    markEffect_ = dh->LookupForm<RE::EffectSetting>(kMarkEffect, kRimPlugin);
    staggerKeyword_ = dh->LookupForm<RE::BGSKeyword>(kStaggerKeyword, kRimPlugin);
    confirmKeyword_ = dh->LookupForm<RE::BGSKeyword>(kConfirmKeyword, kRimPlugin);
    allowSpell_ = dh->LookupForm<RE::SpellItem>(kAllowSpell, kRimPlugin);
    skillSpell_ = dh->LookupForm<RE::SpellItem>(kSkillSpell, kRimPlugin);
    executingKeyword_ = dh->LookupForm<RE::BGSKeyword>(kExecutingKeyword, kRimPlugin);
    auto f = [](const void* p) { return p ? "found" : "MISSING"; };
    SKSE::log::info("backstab ({}): spell {}, stagger {}, confirm {}, allow {}, execution {}, executing {}, mark {}",
                    kRimPlugin, f(backstabSpell_), f(staggerKeyword_), f(confirmKeyword_), f(allowSpell_),
                    f(skillSpell_), f(executingKeyword_), f(markEffect_));
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
    if (Now() - lastBackstab_ < 1.0 || executing_.load() > 0.0) return;  // one at a time: a press during it is a swing
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
    auto* caster = player->GetMagicCaster(RE::MagicSystem::CastingSource::kInstant);
    if (!caster) return;
    caster->CastSpellImmediate(backstabSpell_, false, best, 1.0f, false, 0.0f, player);
    SKSE::log::info("backstab: cast at {:08X} '{}' ({:.0f} units)", best->GetFormID(), best->GetName(), bestDist);
    if (s.backstab_execute && skillSpell_ && staggerKeyword_) Watch(best->GetHandle(), lastBackstab_);
  }

  // After the backstab's cast: a background clock asks the main thread every 50 ms how it stands. The stagger must land
  // (kStaggerKeyword on the victim) within kStaggerWait, else Rim Parry refused it (its cooldown, or the angle) and the
  // swing stays a normal swing. Then the victim gets kConfirmKeyword if its stagger clip has not given it yet, and when
  // the player's own swing has ended (an idle is not taken mid-attack) the player is given EldenSkillSA, which plays
  // the execution clip; its annotations place the victim and deal the execution's damage.
  void Watch(RE::ActorHandle victim, double started) {
    executing_ = started;
    staggered_ = false;
    std::thread([this, victim, started] {
      for (int i = 0; i < 60 && executing_.load() == started; ++i) {
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        SKSE::GetTaskInterface()->AddTask([this, victim, started] { Step(victim, started); });
      }
    }).detach();
  }

  void Step(RE::ActorHandle victim, double started) {
    if (executing_.load() != started) return;
    auto* player = RE::PlayerCharacter::GetSingleton();
    auto v = victim.get();
    const double t = Now() - started;
    auto stop = [&](std::string_view why) {
      executing_ = 0.0;
      SKSE::log::info("backstab: {} ({:.2f} s)", why, t);
    };
    if (!player || player->IsDead() || !v || v->IsDead() || !v->Is3DLoaded()) return stop("victim or player gone");
    if (!staggered_) {
      if (!v->HasMagicEffectWithKeyword(staggerKeyword_)) {
        if (t > kStaggerWait) stop("no stagger: Rim Parry refused it (its cooldown or the angle), a normal swing");
        return;
      }
      staggered_ = true;
      SKSE::log::info("backstab: stagger landed on {:08X} ({:.2f} s)", v->GetFormID(), t);
    }
    if (confirmKeyword_ && allowSpell_ && !v->HasMagicEffectWithKeyword(confirmKeyword_)) {
      if (auto* c = player->GetMagicCaster(RE::MagicSystem::CastingSource::kInstant))
        c->CastSpellImmediate(allowSpell_, false, v.get(), 1.0f, false, 0.0f, player);
    }
    const bool swinging = player->AsActorState()->GetAttackState() != RE::ATTACK_STATE_ENUM::kNone;
    if (swinging && t < kSwingWait) return;
    if (auto* c = player->GetMagicCaster(RE::MagicSystem::CastingSource::kInstant))
      c->CastSpellImmediate(skillSpell_, false, player, 1.0f, false, 0.0f, player);
    const bool keyword = executingKeyword_ && player->HasMagicEffectWithKeyword(executingKeyword_);
    // EldenSkillSA's script sends the same event from Papyrus a frame or more later; sent here too, so the log says
    // whether the graph took it
    const bool ok = player->NotifyAnimationGraph("IdleCombatStart");
    lastExecution_ = Now();
    stop(fmt::format("execution on {:08X}: executing keyword {}, IdleCombatStart -> {}{}", v->GetFormID(), keyword, ok,
                     swinging ? " (swing still going)" : ""));
  }

  // Rim Parry's own mark (kMarkEffect) arrives seconds after a stagger and would start a second execution on the next
  // press: after ours it is dispelled.
  RE::BSEventNotifyControl ProcessEvent(const RE::TESMagicEffectApplyEvent* e,
                                        RE::BSTEventSource<RE::TESMagicEffectApplyEvent>*) override {
    if (!e || !e->target || !e->target->IsPlayerRef() || !markEffect_ || e->magicEffect != markEffect_->GetFormID())
      return RE::BSEventNotifyControl::kContinue;
    if (Now() - lastExecution_.load() > 8.0) return RE::BSEventNotifyControl::kContinue;
    SKSE::GetTaskInterface()->AddTask([this] {
      auto* player = RE::PlayerCharacter::GetSingleton();
      if (!player) return;
      if (auto* list = player->AsMagicTarget()->GetActiveEffectList())
        for (auto* ae : *list)
          if (ae && ae->spell == markSpell_) ae->Dispel(true);
      SKSE::log::info("backstab: Rim Parry's mark dispelled (ours played the execution)");
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
  RE::SpellItem* markSpell_ = nullptr;
  RE::EffectSetting* markEffect_ = nullptr;
  RE::BGSKeyword* staggerKeyword_ = nullptr;
  RE::BGSKeyword* confirmKeyword_ = nullptr;
  RE::SpellItem* allowSpell_ = nullptr;
  RE::SpellItem* skillSpell_ = nullptr;
  RE::BGSKeyword* executingKeyword_ = nullptr;
  double lastBackstab_ = 0.0;
  std::atomic<double> executing_{0.0};      // the backstab being watched (its start time), 0 when none
  std::atomic<double> lastExecution_{0.0};
  bool staggered_ = false;                  // main thread only
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
