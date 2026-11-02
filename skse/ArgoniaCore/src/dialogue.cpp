// The router's hooks (1.1 §d), the dialogue intercept's handler (1.3 §b, native map P3) and the view host.
// The intercept: the player's ARG_Perk_DialogueIntercept replaces the default activation of any ARG_Speaker with its
// fragment, which calls ArgoniaCore.OpenDialogue(target); the vanilla Dialogue Menu, should it open anyway, is closed
// the frame it opens (the router's backstop) and our conversation opened for the same speaker. The view host keeps
// each view's last push and logs it whole; ViewIntent is the one intent entry for every view (dialogue, journal,
// chart, sitting), routed by type; the web-view binding (PrismaUI) is views.cpp's, behind Push() and ViewIntent.
// Barter (1.12 §6): the window's Barter button hides our view, keeps the conversation and opens Skyrim's BarterMenu
// for the speaker (Wind UI intercepts it and draws its barter window); when that menu closes, our window returns.
#include "core.h"
#include <chrono>

namespace argonia::plugin {

namespace {

// The world id of an actor whose talk is ours (a record of ours with lines in the store); none for anyone else.
std::optional<std::string> SpeakerId(RE::Actor* actor) {
  auto& c = Get();
  if (!actor || !c.store) return std::nullopt;
  auto id = WorldId(actor->GetActorBase());
  if (!id) id = WorldId(actor);
  if (!id || !ac::talk::speaks(*c.store, *id)) return std::nullopt;
  return id;
}

// The open conversation's speaker, while they are still there.
RE::Actor* TalkActor() {
  auto ref = Get().talk_ref.get();
  return ref ? ref->As<RE::Actor>() : nullptr;
}

// The speaker's vendor faction (place_build.py writes one per npc_trade row). CommonLib's GetVendorFaction returns
// the cached field read before it calculates, so the first call after load gives null (batch 20261101T012958:
// Livia had no Barter): read the field again once the calculation has run.
RE::TESFaction* VendorOf(RE::Actor* a) {
  if (!a) return nullptr;
  if (auto* f = a->GetVendorFaction()) return f;
  return a->GetActorRuntimeData().vendorFaction;
}

// The window as the player sees it: the conversation's state and the speaker's service buttons. A merchant (a
// vendor faction, which sets the BarterMenu's chest, hours and buy/sell list) offers Barter.
ac::msg::DialogueState Dressed(ac::msg::DialogueState s) {
  auto* a = TalkActor();
  if (VendorOf(a)) s.services.push_back(ac::msg::ServiceKind::barter);
  return s;
}

constexpr std::string_view kWindUIMenu = "WindUIMenu";  // Wind UI's one menu: its barter window among its panes
// The press that closed Wind UI's barter window (the pad's B, Esc) can reach our window as it comes back, a frame
// later: a close inside this grace after the return is that same press, not the player's (b112d: "back from the
// BarterMenu" then "dialogue: closed" 116 ms later). Goodbye by name still works: only view.close is held.
constexpr auto kReturnGrace = std::chrono::milliseconds(400);
std::chrono::steady_clock::time_point returned_at{};
bool bartering = false;  // our window is hidden behind the BarterMenu it opened; it returns when that menu closes

// Barter chosen: our view hides (the conversation stays open) and the BarterMenu opens on the next frame.
void OpenBarterFromDialogue() {
  auto& c = Get();
  auto* a = TalkActor();
  if (!VendorOf(a)) {
    SKSE::log::warn("dialogue: Barter refused; the speaker is gone or keeps no shop");
    return;
  }
  bartering = true;
  CloseView("dialogue");
  SKSE::GetTaskInterface()->AddTask([h = c.talk_ref] {
    auto r = h.get();
    auto* actor = r ? r->As<RE::Actor>() : nullptr;
    if (!actor) {
      std::lock_guard l(Get().lock);
      bartering = false;
      SKSE::log::warn("dialogue: the speaker is gone before the BarterMenu opened");
      return;
    }
    SKSE::log::info("dialogue: BarterMenu for {:08X} (vendor faction {:08X})", actor->GetFormID(),
                    VendorOf(actor) ? VendorOf(actor)->GetFormID() : 0);
    RE::BarterMenu::OpenMenu(actor);
  });
}

// The BarterMenu closed over a conversation: our window comes back as it was.
void ReturnFromBarter() {
  auto& c = Get();
  bartering = false;
  if (!c.talk) return;
  auto s = Session();
  auto json = ac::msg::encode(Dressed(c.talk->view(s)));
  if (!json) {
    SKSE::log::error("dialogue: the window does not fit the schema: {}", json.error());
    return;
  }
  SKSE::log::info("dialogue: back from the BarterMenu");
  returned_at = std::chrono::steady_clock::now();
  Push("dialogue", std::move(*json));
  FactsChanged("barter closed");
}

// Opens the conversation for the pending speaker: the router's dialogue handler.
void OnDialogueSurface(ac::router::SurfaceId) {
  auto& c = Get();
  std::lock_guard l(c.lock);
  auto ref = c.pending_speaker.get();
  c.pending_speaker = {};
  // A new conversation replaces the last, which may never have been closed; a refusal leaves none open.
  c.talk.reset();
  CloseView("dialogue");
  auto* actor = ref ? ref->As<RE::Actor>() : nullptr;
  auto id = SpeakerId(actor);
  if (!id) {
    SKSE::log::warn("dialogue: {:08X} is not an Argonia speaker; nothing opens", actor ? actor->GetFormID() : 0);
    return;
  }
  auto s = Session();
  auto conv = ac::talk::Conversation::open(*c.store, s, *id, actor->GetDisplayFullName());
  if (!conv) {
    SKSE::log::warn("{}", conv.error());
    return;
  }
  c.talk = std::move(*conv);
  c.talk_ref = ref ? ref->GetHandle() : RE::ObjectRefHandle{};
  for (const auto& n : c.talk->greeting_notes()) SKSE::log::info("{}", n);
  auto json = ac::msg::encode(Dressed(c.talk->view(s)));
  if (!json) {
    SKSE::log::error("dialogue: the window does not fit the schema: {}", json.error());
    return;
  }
  Push("dialogue", std::move(*json));
  FactsChanged("greeting read");
}

}  // namespace

std::expected<std::string, std::string> GreetingFor(std::string_view speaker_id) {
  auto& c = Get();
  std::lock_guard l(c.lock);
  if (!c.store) return std::unexpected("no topic store loaded");
  if (!ac::talk::speaks(*c.store, speaker_id)) return std::unexpected("not an Argonia speaker: " + std::string(speaker_id));
  auto s = Session();
  auto conv = ac::talk::Conversation::open(*c.store, s, std::string(speaker_id), std::string(speaker_id));
  if (!conv) return std::unexpected(conv.error());
  auto json = ac::msg::encode(conv->view(s));
  if (!json) return std::unexpected("the window does not fit the schema: " + json.error());
  return std::move(*json);
}

namespace {

class MenuSink final : public RE::BSTEventSink<RE::MenuOpenCloseEvent> {
 public:
  RE::BSEventNotifyControl ProcessEvent(const RE::MenuOpenCloseEvent* e, RE::BSTEventSource<RE::MenuOpenCloseEvent>*) override {
    if (!e) return RE::BSEventNotifyControl::kContinue;
    const std::string_view menu = e->menuName.c_str();
    // A sheet opening or closing shows or hides our HUD; the task runs after the menu stack has changed.
    if (ac::router::hides_hud_at_once(menu)) HudLoading(menu, e->opening);  // the load blocks the task queue
    if (ac::router::covers_hud(menu)) SKSE::GetTaskInterface()->AddTask([] { HudRefresh(); });
    if (!e->opening) {
      // Wind UI takes the BarterMenu as it opens (it closes within 0.3 s, batch 20261101T020537) and draws its own
      // barter window in WindUIMenu: our window returns only once neither is open.
      if (menu == RE::BarterMenu::MENU_NAME || menu == kWindUIMenu) {
        std::lock_guard l(Get().lock);
        if (bartering)
          SKSE::GetTaskInterface()->AddTask([] {
            auto* ui = RE::UI::GetSingleton();
            if (ui && (ui->IsMenuOpen(RE::BarterMenu::MENU_NAME) || ui->IsMenuOpen(RE::BSFixedString(kWindUIMenu.data())))) return;
            std::lock_guard l2(Get().lock);
            if (bartering) ReturnFromBarter();
          });
      }
      if (menu == RE::SleepWaitMenu::MENU_NAME || menu == RE::LoadingMenu::MENU_NAME) FactsChanged("time passed");
      if (menu == RE::SleepWaitMenu::MENU_NAME || menu == RE::JournalMenu::MENU_NAME) MenusMenuClosed(menu);
      return RE::BSEventNotifyControl::kContinue;
    }
    auto& c = Get();
    std::lock_guard l(c.lock);
    if (menu == RE::BookMenu::MENU_NAME) {  // 1.4: a quest thing's read hook (the ledger), in the world or carried
      MeetThing(RE::BookMenu::GetTargetForm(), ac::things::Hook::read);
      return RE::BSEventNotifyControl::kContinue;
    }
    if (menu == RE::DialogueMenu::MENU_NAME) {
      auto* mtm = RE::MenuTopicManager::GetSingleton();
      auto speaker = mtm ? mtm->speaker.get() : RE::NiPointer<RE::TESObjectREFR>{};
      auto* actor = speaker ? speaker->As<RE::Actor>() : nullptr;
      // Only an Argonia speaker's menu is ours to close; anyone else keeps the vanilla menu (logged: decision 0012
      // quarantines it, and a closed menu with nothing in its place would leave the player unable to talk at all).
      if (!SpeakerId(actor)) {
        SKSE::log::warn("router: vanilla Dialogue Menu left open for {:08X}, not an Argonia speaker",
                        actor ? actor->GetFormID() : 0);
        return RE::BSEventNotifyControl::kContinue;
      }
      c.pending_speaker = mtm->speaker;
    }
    // Escape opens the Journal Menu too (its System tab: save, settings, quit, until 3.1); only the journal key's
    // opening is ours to replace.
    // Since 1.12 look 1 that System page is ours: Dear Diary's movie is hidden and our System pane stands over it.
    if (menu == RE::JournalMenu::MENU_NAME && !JournalKeyTaken()) {
      SystemMenuOpened();
      return RE::BSEventNotifyControl::kContinue;
    }
    if (menu == RE::MessageBoxMenu::MENU_NAME || menu == RE::LockpickingMenu::MENU_NAME) {  // the frame style (look 1)
      FrameMenuOpened(menu);  // and on to the router, as before
    }
    if (menu == RE::SleepWaitMenu::MENU_NAME) {  // T, the pad's Select: our wait window over the hidden menu
      WaitMenuOpened();
      return RE::BSEventNotifyControl::kContinue;
    }
    const auto v = c.router.on_menu(menu);
    if (!v.note.empty()) SKSE::log::info("router: {}", v.note);
    if (v.action == ac::router::Action::block)
      if (auto* q = RE::UIMessageQueue::GetSingleton()) q->AddMessage(e->menuName, RE::UI_MESSAGE_TYPE::kHide, nullptr);
    return RE::BSEventNotifyControl::kContinue;
  }
};

class DeathSink final : public RE::BSTEventSink<RE::TESDeathEvent> {
 public:
  RE::BSEventNotifyControl ProcessEvent(const RE::TESDeathEvent* e, RE::BSTEventSource<RE::TESDeathEvent>*) override {
    if (e && e->dead && e->actorDying) {
      auto* a = e->actorDying->As<RE::Actor>();
      if (auto id = a ? WorldId(a->GetActorBase()) : std::nullopt) FactsChanged("death of " + *id);
    }
    return RE::BSEventNotifyControl::kContinue;
  }
};

class ContainerSink final : public RE::BSTEventSink<RE::TESContainerChangedEvent> {
 public:
  RE::BSEventNotifyControl ProcessEvent(const RE::TESContainerChangedEvent* e,
                                        RE::BSTEventSource<RE::TESContainerChangedEvent>*) override {
    constexpr RE::FormID kPlayerRef = 0x14;
    if (e && (e->newContainer == kPlayerRef || e->oldContainer == kPlayerRef))
    {
      if (e->baseObj == kGold) FactsChanged("gold");  // Skyrim.esm's, so it has no world id; goldAtLeast reads it
      else if (auto id = WorldId(RE::TESForm::LookupByID(e->baseObj))) FactsChanged("carried " + *id);
    }
    return RE::BSEventNotifyControl::kContinue;
  }
};

}  // namespace

bool OpenDialogue(RE::TESObjectREFR* target) {
  auto& c = Get();
  std::lock_guard l(c.lock);
  if (!target) return false;
  if (auto* a = target->As<RE::Actor>(); a && !ac::views::offers_talk(ActorAtOf(a))) {  // a corpse or a fighter
    SKSE::log::info("dialogue: {:08X} is dead or fighting the player; no conversation", a->GetFormID());
    return false;
  }
  c.pending_speaker = target->GetHandle();
  const auto v = c.router.on_surface(ac::router::SurfaceId::dialogueMenu);
  if (!v.note.empty()) SKSE::log::info("router: {}", v.note);
  return v.handled && c.talk.has_value();
}

namespace {

std::string DialogueIntent(std::string_view json) {
  auto& c = Get();
  std::lock_guard l(c.lock);
  if (!c.talk) return R"({"error":"no conversation is open"})";
  if (auto in = ac::msg::decode_intent(json))
    if (const auto* sv = std::get_if<ac::msg::DialogueService>(&*in); sv && sv->service == ac::msg::ServiceKind::barter) {
      OpenBarterFromDialogue();
      return {};
    }
  if (auto in = ac::msg::decode_intent(json); in && std::holds_alternative<ac::msg::ViewClose>(*in) &&
      std::chrono::steady_clock::now() - returned_at < kReturnGrace) {
    SKSE::log::info("dialogue: a close {} ms after the barter's return held (the press that closed the barter)",
                    std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - returned_at).count());
    return {};
  }
  auto s = Session();
  auto r = c.talk->on_intent_text(json, s);
  for (const auto& n : r.notes) SKSE::log::info("{}", n);
  if (r.closed) {
    c.talk.reset();
    CloseView("dialogue");
    SKSE::log::info("dialogue: closed");
    FactsChanged("dialogue closed");
    return {};
  }
  std::string out;
  if (r.state)
    if (auto j = ac::msg::encode(Dressed(*r.state))) out = std::move(*j);
  if (!out.empty()) Push("dialogue", out);
  FactsChanged("topic heard");
  return out;
}

}  // namespace

// The one intent entry every view's listener calls: routed by the intent's type to the view's host.
std::string ViewIntent(std::string_view json) {
  std::lock_guard l(Get().lock);  // the JS listener's task, the bridge and Papyrus all come here
  const auto view = ac::router::intent_view(json);
  if (!view) {
    SKSE::log::warn("views: intent refused: {}", view.error());
    return R"({"error":"the intent does not fit the schema"})";
  }
  const auto m = ac::msg::decode_intent(json);
  const bool closing = m && std::holds_alternative<ac::msg::ViewClose>(*m);
  if (*view == "dialogue" && closing && !Get().talk) {  // the probe's window, or one left after a load
    CloseView("dialogue");
    return {};
  }
  if (*view == "dialogue") return DialogueIntent(json);
  if ((*view == "journal" || *view == "chart" || *view == "magic" || *view == "system" || *view == "wait") && closing) {
    CloseView(*view);
    return {};
  }
  if (m)
    if (const auto* p = std::get_if<ac::msg::JournalPage>(&*m)) return JournalIntent(*p);
  if (m)
    if (const auto* p = std::get_if<ac::msg::ChartPan>(&*m)) return ChartIntent(*p);
  if (m)
    if (const auto* p = std::get_if<ac::msg::MagicEquip>(&*m)) return MagicIntent(*p);
  if (m)
    if (const auto* p = std::get_if<ac::msg::SystemPick>(&*m)) return SystemIntent(*p);
  if (m)
    if (const auto* p = std::get_if<ac::msg::WaitPick>(&*m)) return WaitIntent(*p);
  if (*view == "sitting") return SittingIntent(json);
  if (*view == "hud") return OpenTweenMenu() ? std::string{} : R"({"error":"the Tween Menu could not open"})";
  SKSE::log::warn("views: no host for the {} view's intents yet", *view);
  return R"({"error":"that view has no host yet"})";
}

void InstallHooks() {
  auto& c = Get();
  std::lock_guard l(c.lock);
  c.router_log = ac::seam::install(c.router, OnDialogueSurface);
  static MenuSink menus;
  static DeathSink deaths;
  static ContainerSink containers;
  if (auto* ui = RE::UI::GetSingleton()) ui->AddEventSink<RE::MenuOpenCloseEvent>(&menus);
  if (auto* src = RE::ScriptEventSourceHolder::GetSingleton()) {
    src->AddEventSink<RE::TESDeathEvent>(&deaths);
    src->AddEventSink<RE::TESContainerChangedEvent>(&containers);
  }
  c.router_log.push_back("sinks: MenuOpenCloseEvent, TESDeathEvent, TESContainerChangedEvent");
  for (const auto& line : c.router_log) SKSE::log::info("router: {}", line);
}

}  // namespace argonia::plugin
