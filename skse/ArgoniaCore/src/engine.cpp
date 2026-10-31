// The engine side of the seam: world ids to forms (gen::kForms), the reads the conditions need, the item and gold
// writes the actions need, the quest orders applied with the engine's own Quest functions, the attribute mirrors
// (P7: the STAT family is canonical, the actor values only mirror it) and the season's weather globals.
#include "core.h"

namespace argonia::plugin {

namespace {

RE::PlayerCharacter* Player() { return RE::PlayerCharacter::GetSingleton(); }

// Calls a Quest script function on the quest's bound object, through the VM (SetStage runs the stage's fragment).
template <class... Args>
bool CallQuest(RE::TESQuest* q, std::string_view fn, Args... args) {
  auto* vm = RE::BSScript::Internal::VirtualMachine::GetSingleton();
  auto* policy = vm ? vm->GetObjectHandlePolicy() : nullptr;
  if (!policy) return false;
  const auto handle = policy->GetHandleForObject(RE::TESQuest::FORMTYPE, q);
  if (handle == policy->EmptyHandle()) return false;
  RE::BSTSmartPointer<RE::BSScript::IStackCallbackFunctor> none;
  return vm->DispatchMethodCall(handle, RE::BSFixedString("Quest"), RE::BSFixedString(fn),
                                RE::MakeFunctionArguments(std::move(args)...), none);
}

std::optional<RE::Actor*> FindActor(const RE::TESForm* f) {
  if (auto* a = const_cast<RE::TESForm*>(f)->As<RE::Actor>()) return a;  // a placed reference row
  auto* npc = f->As<RE::TESNPC>();
  auto* lists = RE::ProcessLists::GetSingleton();
  if (!npc || !lists) return std::nullopt;
  for (auto* handles : {&lists->highActorHandles, &lists->middleHighActorHandles})
    for (auto& h : *handles)
      if (auto a = h.get(); a && a->GetActorBase() == npc) return a.get();
  return std::nullopt;  // not loaded: unknown, so a condition reading it never holds
}

void SeasonCheck() {
  auto d = GameEngine{}.date();
  if (!d) return;
  auto& c = Get();
  auto change = ac::weather::on_day(d->month, d->day, c.season);
  if (!change) {
    SKSE::log::warn("weather: GameMonth {} day {} is not on the calendar; the globals keep their values", d->month, d->day);
    return;
  }
  const bool turned = c.season && *c.season != change->season;
  for (const auto& w : change->write) {
    auto* g = RE::TESForm::LookupByEditorID<RE::TESGlobal>(w.global);
    if (g) g->value = static_cast<float>(w.value);
    else SKSE::log::warn("weather: global {} not found", w.global);
  }
  if (!change->write.empty()) SKSE::log::info("weather: season {}, {} globals written", static_cast<int>(change->season), change->write.size());
  c.season = change->season;
  if (turned) FactsChanged("season");
}

}  // namespace

Core& Get() {
  static Core c;
  return c;
}

RE::TESForm* Lookup(std::string_view world_id) {
  const auto* row = ac::seam::form(world_id);
  auto* dh = RE::TESDataHandler::GetSingleton();
  return row && dh ? dh->LookupForm(row->local, row->plugin) : nullptr;
}

RE::ActorValue AvNamed(std::string_view name) {
  return RE::ActorValueList::LookupActorValueByName(std::string(name).c_str());
}

std::optional<std::string> WorldId(const RE::TESForm* form) {
  if (!form) return std::nullopt;
  const auto* file = form->GetFile(0);
  if (!file) return std::nullopt;
  const auto* row = ac::seam::form_at(file->GetFilename(), form->GetLocalFormID());
  return row ? std::optional<std::string>(row->id) : std::nullopt;
}

std::optional<int> GameEngine::item_count(std::string_view item) const {
  auto* obj = Lookup<RE::TESBoundObject>(item);
  auto* p = Player();
  if (!obj || !p) return std::nullopt;
  return p->GetItemCount(obj);
}

std::optional<bool> GameEngine::alive(std::string_view npc) const {
  auto* f = Lookup(npc);
  if (!f) return std::nullopt;
  auto a = FindActor(f);
  if (!a) return std::nullopt;
  return !(*a)->IsDead();
}

std::optional<int> GameEngine::gold() const {
  auto* p = Player();
  return p ? std::optional<int>(p->GetGoldAmount()) : std::nullopt;
}

std::optional<ac::seam::QuestView> GameEngine::quest(std::string_view quest) const {
  auto* q = Lookup<RE::TESQuest>(quest);
  if (!q) return std::nullopt;
  ac::seam::QuestView v;
  v.stage = q->GetCurrentStageID();
  for (auto* o : q->objectives) {
    if (!o) continue;
    const auto s = o->state.get();
    if (s == RE::QUEST_OBJECTIVE_STATE::kCompleted || s == RE::QUEST_OBJECTIVE_STATE::kCompletedDisplayed)
      v.done.push_back(o->index);
  }
  return v;
}

std::optional<ac::seam::Date> GameEngine::date() const {
  auto* cal = RE::Calendar::GetSingleton();
  if (!cal) return std::nullopt;
  return ac::seam::Date{static_cast<int>(cal->GetYear()), static_cast<int>(cal->GetMonth()),
                        static_cast<int>(cal->GetDay()), static_cast<double>(cal->GetHour())};
}

bool GameEngine::give_item(std::string_view item, int count) {
  auto* obj = Lookup<RE::TESBoundObject>(item);
  auto* p = Player();
  if (!obj || !p || count <= 0) {
    SKSE::log::warn("giveItem: {} is not a record of ours in this load order", item);
    return false;
  }
  p->AddObjectToContainer(obj, nullptr, count, nullptr);
  return true;
}

bool GameEngine::take_item(std::string_view item, int count) {
  auto* obj = Lookup<RE::TESBoundObject>(item);
  auto* p = Player();
  if (!obj || !p || count <= 0) return false;
  p->RemoveItem(obj, count, RE::ITEM_REMOVE_REASON::kRemove, nullptr, nullptr);
  return true;
}

bool GameEngine::give_gold(int amount) {
  auto* gold = RE::TESForm::LookupByID<RE::TESBoundObject>(kGold);
  auto* p = Player();
  if (!gold || !p || amount <= 0) return false;
  p->AddObjectToContainer(gold, nullptr, amount, nullptr);
  return true;
}

bool GameEngine::take_gold(int amount) {
  auto* gold = RE::TESForm::LookupByID<RE::TESBoundObject>(kGold);
  auto* p = Player();
  if (!gold || !p || amount <= 0) return false;
  p->RemoveItem(gold, amount, RE::ITEM_REMOVE_REASON::kRemove, nullptr, nullptr);
  return true;
}

// The openBarter action (lane trader): the conversation's own speaker, when they are `npc`, gets the engine's BarterMenu
// on the next frame, after our conversation closes; the menu reads their vendor faction (chest, hours, buy/sell list).
bool GameEngine::open_barter(std::string_view npc) {
  auto& c = Get();
  auto ref = c.talk_ref.get();
  auto* actor = ref ? ref->As<RE::Actor>() : nullptr;
  auto id = actor ? WorldId(actor->GetActorBase()) : std::nullopt;
  if (!id && actor) id = WorldId(actor);
  if (!actor || !id || *id != npc) {
    SKSE::log::warn("openBarter: {} is not the person this conversation is with", npc);
    return false;
  }
  SKSE::GetTaskInterface()->AddTask([h = c.talk_ref, who = std::string(npc)] {
    auto& c = Get();
    std::lock_guard l(c.lock);
    c.talk.reset();
    c.talk_ref = {};
    CloseView("dialogue");
    auto r = h.get();
    auto* a = r ? r->As<RE::Actor>() : nullptr;
    if (!a) {
      SKSE::log::warn("openBarter: {} is gone before the menu opened", who);
      return;
    }
    SKSE::log::info("openBarter: BarterMenu for {} (vendor faction {:08X})", who,
                    a->GetVendorFaction() ? a->GetVendorFaction()->GetFormID() : 0);
    RE::BarterMenu::OpenMenu(a);
  });
  return true;
}

ac::seam::Session Session() {
  static GameEngine engine;
  auto& c = Get();
  return ac::seam::Session(c.state, engine, engine, c.graphs);
}

void FactsChanged(std::string_view why) {
  auto& c = Get();
  std::lock_guard l(c.lock);
  for (const auto& o : c.inflight.filter(Session().step())) {
    auto* q = Lookup<RE::TESQuest>(o.quest);
    if (!q) {
      SKSE::log::error("quests: {} is watched but not in this load order", o.quest);
      continue;
    }
    bool refused = false;
    for (auto i : o.completed) {
      const bool ok = CallQuest(q, "SetObjectiveCompleted", static_cast<std::int32_t>(i), true);
      refused |= !ok;
      SKSE::log::info("quests: {} objective {} completed ({}){}", o.quest, i, why, ok ? "" : ", dispatch refused");
      if (ok) JournalNotice(ac::journal::NoticeCause::clue, o.quest, static_cast<std::int32_t>(i));
    }
    if (o.set_stage) {
      const bool ok = CallQuest(q, "SetStage", static_cast<std::int32_t>(*o.set_stage));
      refused |= !ok;
      SKSE::log::info("quests: {} SetStage {} ({}){}", o.quest, *o.set_stage, why, ok ? "" : ", dispatch refused");
    }
    if (refused) c.inflight.forget(o.quest);  // the next step gives them again
  }
  if (why != "season") SeasonCheck();
}

void NewCharacter() {
  auto* p = Player();
  if (!p) return;
  auto& c = Get();
  std::lock_guard l(c.lock);
  const auto* base = p->GetActorBase();
  const bool female = base && base->IsFemale();
  // Once: a sheet that exists is the character's. Also at every game ready (a `coc` start sends no kNewGame).
  if (!ac::ensure_character(c.state.sheet, ac::gen::studio_race, female, ac::gen::studio_class)) return;
  SKSE::log::info("new character: {} {} {} (health {:.0f})", ac::gen::kRaceIdNames[std::size_t(ac::gen::studio_race)],
                  female ? "female" : "male", ac::gen::kClassIdNames[std::size_t(ac::gen::studio_class)],
                  ac::derive(c.state.sheet, ac::Effective::of(c.state.sheet), 0).health);
}

void MirrorAttributes() {
  auto* p = Player();
  if (!p) return;
  auto& c = Get();
  std::lock_guard l(c.lock);
  auto* avo = p->AsActorValueOwner();
  for (const auto& m : ac::seam::attribute_mirrors()) {
    const auto av = RE::ActorValueList::LookupActorValueByName(std::string(m.actor_value).c_str());
    if (av == RE::ActorValue::kNone) {
      SKSE::log::error("attributes: actor value {} unknown to the runtime", m.actor_value);
      continue;
    }
    avo->SetBaseActorValue(av, static_cast<float>(ac::seam::attribute(c.state, m.attribute)));
  }
}

void EnsurePerks() {
  auto* p = Player();
  if (!p) return;
  for (auto id : {"hook.dialogue-intercept"sv, "hook.rest-intercept"sv, "hook.road-closed"sv, "hook.thing-activate"sv,
                  "combat.carriers"sv}) {
    auto* perk = Lookup<RE::BGSPerk>(id);
    if (!perk) {
      SKSE::log::error("perks: {} is not in this load order", id);
      continue;
    }
    if (!p->HasPerk(perk)) {
      p->AddPerk(perk);
      SKSE::log::info("perks: {} ({:08X}) added to the player", id, perk->GetFormID());
    }
  }
}

}  // namespace argonia::plugin
