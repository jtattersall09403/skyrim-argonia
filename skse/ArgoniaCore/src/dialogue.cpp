// The router's hooks (1.1 §d), the dialogue intercept's handler (1.3 §b, native map P3) and the view host.
// The intercept: the player's ARG_Perk_DialogueIntercept replaces the default activation of any ARG_Speaker with its
// fragment, which calls ArgoniaCore.OpenDialogue(target); the vanilla Dialogue Menu, should it open anyway, is closed
// the frame it opens (the router's backstop) and our conversation opened for the same speaker. The view host keeps
// each view's last push and logs it whole; the web-view binding (PrismaUI) is 1.2 §0's, behind Push().
#include "core.h"

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

// Opens the conversation for the pending speaker: the router's dialogue handler.
void OnDialogueSurface(ac::router::SurfaceId) {
  auto& c = Get();
  std::lock_guard l(c.lock);
  auto ref = c.pending_speaker.get();
  c.pending_speaker = {};
  // A new conversation replaces the last, which may never have been closed; a refusal leaves none open.
  c.talk.reset();
  c.views.erase("dialogue");
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
  for (const auto& n : c.talk->greeting_notes()) SKSE::log::info("{}", n);
  auto json = ac::msg::encode(c.talk->view(s));
  if (!json) {
    SKSE::log::error("dialogue: the window does not fit the schema: {}", json.error());
    return;
  }
  Push("dialogue", std::move(*json));
  FactsChanged("greeting read");
}

class MenuSink final : public RE::BSTEventSink<RE::MenuOpenCloseEvent> {
 public:
  RE::BSEventNotifyControl ProcessEvent(const RE::MenuOpenCloseEvent* e, RE::BSTEventSource<RE::MenuOpenCloseEvent>*) override {
    if (!e) return RE::BSEventNotifyControl::kContinue;
    const std::string_view menu = e->menuName.c_str();
    if (!e->opening) {
      if (menu == RE::SleepWaitMenu::MENU_NAME || menu == RE::LoadingMenu::MENU_NAME) FactsChanged("time passed");
      return RE::BSEventNotifyControl::kContinue;
    }
    auto& c = Get();
    std::lock_guard l(c.lock);
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
  c.pending_speaker = target->GetHandle();
  const auto v = c.router.on_surface(ac::router::SurfaceId::dialogueMenu);
  if (!v.note.empty()) SKSE::log::info("router: {}", v.note);
  return v.handled && c.talk.has_value();
}

std::string ViewIntent(std::string_view json) {
  auto& c = Get();
  std::lock_guard l(c.lock);
  if (!c.talk) return R"({"error":"no conversation is open"})";
  auto s = Session();
  auto r = c.talk->on_intent_text(json, s);
  for (const auto& n : r.notes) SKSE::log::info("{}", n);
  if (r.closed) {
    c.talk.reset();
    c.views.erase("dialogue");
    SKSE::log::info("dialogue: closed");
    FactsChanged("dialogue closed");
    return {};
  }
  std::string out;
  if (r.state)
    if (auto j = ac::msg::encode(*r.state)) out = std::move(*j);
  if (!out.empty()) Push("dialogue", out);
  FactsChanged("topic heard");
  return out;
}

void Push(std::string_view view, std::string json) {
  SKSE::log::info("view {} <- {}", view, json);
  Get().views[std::string(view)] = std::move(json);
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
