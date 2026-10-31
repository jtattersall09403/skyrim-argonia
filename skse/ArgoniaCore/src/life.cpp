// The 1.5 adapters (grow, die, rest, save; native map G16.1-G17.2): engine facts into skse/core's `life` and its
// orders back into the engine. Every rule is in core/life and tested there (core.life); this file reads the engine
// (hits, kills, casts, unlocks, the player's place and danger, the worn armour), applies the outcomes (skill and
// pool mirrors, the vastei pile reference, the wake move, the respawn resets, the rest and suspend saves) and hosts
// the sitting view. Engine writes from a Papyrus native or a sink run on the main thread through SKSE's task queue.
#include "core.h"

#include <algorithm>
#include <chrono>

namespace argonia::plugin {

namespace {

RE::PlayerCharacter* Player() { return RE::PlayerCharacter::GetSingleton(); }

double Seconds() {
  using namespace std::chrono;
  return duration<double>(steady_clock::now().time_since_epoch()).count();
}

// The cell for an interior, the worldspace for an exterior: the space a position is measured in.
std::uint32_t SpaceOf(const RE::TESObjectREFR* r) {
  if (auto* ws = r->GetWorldspace()) return ws->GetFormID();
  auto* cell = r->GetParentCell();
  return cell ? cell->GetFormID() : 0;
}

ac::rest::Pos PosOf(const RE::TESObjectREFR* r) {
  const auto p = r->GetPosition();
  return ac::life::at_units(p.x, p.y, p.z, SpaceOf(r));
}

double Health(RE::Actor* a, bool max) {
  auto* avo = a->AsActorValueOwner();
  return max ? avo->GetPermanentActorValue(RE::ActorValue::kHealth) : avo->GetActorValue(RE::ActorValue::kHealth);
}

bool HasOurKeyword(const RE::BGSKeywordForm* form, std::string_view world_id) {
  auto* kw = Lookup<RE::BGSKeyword>(world_id);
  return form && kw && form->HasKeyword(kw);
}

bool LocationHas(RE::BGSLocation* loc, std::string_view world_id) {
  for (int depth = 0; loc && depth < 16; loc = loc->parentLoc, ++depth)
    if (HasOurKeyword(loc, world_id)) return true;
  return false;
}

ac::life::Worn WornArmour(RE::Actor* a) { return ac::life::worn_of(WornPieces(a)); }

ac::life::Target TargetOf(RE::Actor* a) {
  ac::life::Target t;
  t.max_health = Health(a, true);
  auto* p = Player();
  t.hostile = p && a->IsHostileToActor(p);
  t.summoned = a->IsCommandedActor() && a->GetCommandingActor().get() == p;
  // trainingDummy and helpless are 2.7's flags (a keyword on the target); none yet.
  return t;
}

// The weapon-class skill of a weapon (none: not a weapon, or no Argonia class keyword).
std::optional<ac::SkillId> ClassSkill(const RE::TESObjectWEAP* weap) {
  if (!weap) return std::nullopt;
  std::optional<ac::SkillId> out;
  weap->ForEachKeyword([&](RE::BGSKeyword* kw) {
    if (auto id = WorldId(kw))
      if (auto s = ac::life::weapon_skill(*id)) {
        out = s;
        return RE::BSContainer::ForEachResult::kStop;
      }
    return RE::BSContainer::ForEachResult::kContinue;
  });
  return out;
}

// The skill a landed blow trains (core life::blow_skill): none for a spell, enchantment, poison or explosion and
// for a weapon with no class (logged), Hand-to-hand for fists.
std::optional<ac::SkillId> BlowSkill(RE::FormID source) {
  auto* weap = RE::TESForm::LookupByID<RE::TESObjectWEAP>(source);
  const bool fists = weap && weap->IsHandToHandMelee();
  const auto cls = fists ? std::nullopt : ClassSkill(weap);
  if (weap && !fists && !cls)
    SKSE::log::warn("grow: weapon {:08X} carries no Argonia weapon class; the blow trains nothing", source);
  return ac::life::blow_skill(weap != nullptr, fists, cls);
}

std::optional<ac::SkillId> SchoolSkill(RE::FormID spell) {
  auto* item = RE::TESForm::LookupByID<RE::MagicItem>(spell);
  auto* mgef = item ? item->GetAVEffect() : nullptr;
  if (!mgef) return std::nullopt;
  const std::string_view av = RE::ActorValueList::GetActorValueName(mgef->GetMagickSkill());
  for (const auto& m : ac::life::skill_mirrors())
    if (!m.actor_value.empty() && m.actor_value == av) return m.skill;
  return std::nullopt;
}

// A gain into STAT, then its mirrors and the log line; S16a reads the line and the natives.
void Use(const ac::progression::UseEvent& ev, std::string_view what) {
  auto& c = Get();
  std::lock_guard l(c.lock);
  const auto g = ac::life::use(c.state, ev);
  if (!g.counted()) return;
  SKSE::log::info("grow: {} {}: {:.3f} points, {:.3f} vastei (carried {:.1f}), ranks {}, levels {} (pending {})",
                  what, ac::gen::kSkillIdNames[ac::idx(g.skill)], g.points, g.vastei, c.state.prog.vastei, g.ranks,
                  g.levels, c.state.prog.pending_levels);
  if (g.ranks > 0) {
    MirrorSkills();
    WriteCombat("skill rank");
  }
  SuspendCheck(ac::life::SuspendWhy::interval);
}

// --- the respawn roster (G13.1, G17.1) -------------------------------------------------------------------------
// The clearable places cleared now. A place's cleared state is the engine's own: the LCTN's `cleared` flag, which the
// save keeps (BGSLocation::ChangeFlags::kCleared), so no co-save family. When every `untilCleared` actor of a place is
// dead at once (the core rule), set it as Papyrus Location.SetCleared does. Caller holds the lock.
ac::respawn::ClearedSet ClearedNow() {
  auto& c = Get();
  ac::respawn::ClearedSet cleared;
  std::vector<ac::respawn::ActorId> dead;
  for (const auto& r : c.roster) {
    if (r.place && !cleared.contains(r.place))
      if (auto* loc = RE::TESForm::LookupByID<RE::BGSLocation>(r.place); loc && loc->IsCleared())
        cleared.places.push_back(r.place);
    if (auto* a = RE::TESForm::LookupByID<RE::Actor>(r.actor); a && a->IsDead()) dead.push_back(r.actor);
  }
  for (auto place : ac::respawn::newly_cleared(c.roster, dead, cleared)) {
    if (auto* loc = RE::TESForm::LookupByID<RE::BGSLocation>(place)) {
      loc->cleared = true;
      loc->everCleared = true;
      loc->AddChange(RE::BGSLocation::ChangeFlags::kCleared);
      SKSE::log::info("respawn: {} ({:08X}) cleared; its untilCleared actors stay dead", loc->GetName(), place);
    }
    cleared.places.push_back(place);
  }
  return cleared;
}

ac::life::Roster RosterNow() {
  auto& c = Get();
  ac::life::Roster r;
  r.actors = c.roster;
  r.cleared = ClearedNow();
  return r;
}

// The engine's own cell-reset step for a respawning actor: Resurrect with its inventory reset to the base record
// (template drops only, 76 §126), then back to its placement. Only roster actors are touched: never containers, so
// placed treasure never refills, and never a `never` actor (the core rule leaves them out of `ids`).
void ResetActors(const std::vector<ac::respawn::ActorId>& ids) {
  std::size_t reset = 0;
  for (auto id : ids) {
    auto* a = RE::TESForm::LookupByID<RE::Actor>(id);
    if (!a) continue;
    if (a->IsDisabled()) {  // a disabled actor has no 3D or process to reset (diag4: the disabled deserter)
      SKSE::log::info("respawn: {:08X} is disabled; not reset", id);
      continue;
    }
    ++reset;
    if (a->IsDead()) a->Resurrect(true, true);  // (resetInventory, attach3D)
    else {  // a living roster actor is reset too: whole again, wherever the fight left it
      auto* avo = a->AsActorValueOwner();
      for (auto av : {RE::ActorValue::kHealth, RE::ActorValue::kStamina, RE::ActorValue::kMagicka})
        avo->RestoreActorValue(av, avo->GetPermanentActorValue(av));
    }
    if (a->MoveToEditorLocation()) continue;  // across cells, unlike SetPosition
    // An actor never moved by the engine has no starting-position extra, so MoveToEditorLocation refuses (game-16:
    // the ambush deserter stayed 2888 units off); its placement as the data left it is the same spot.
    auto& homes = Get().homes;
    auto h = homes.find(id);
    const bool same = h != homes.end() && (h->second.world ? a->GetWorldspace() == h->second.world
                                                           : a->GetParentCell() == h->second.cell);
    if (same) {  // an exterior actor changes cell as it is placed, as one that walks does
      a->SetPosition(h->second.pos, true);
      a->SetAngle(h->second.rot);
    } else
      SKSE::log::warn("respawn: {:08X} has no editor location; left where it stands", id);
  }
  if (!ids.empty()) SKSE::log::info("respawn: {} of {} actors reset", reset, ids.size());
}

// --- saving ---------------------------------------------------------------------------------------------------
void SavingBlocked(bool blocked) {
  auto* p = Player();
  if (!p) return;
  if (blocked) p->GetGameStatsData().byCharGenFlag.set(RE::PlayerCharacter::ByCharGenFlag::kDisableSaving);
  else p->GetGameStatsData().byCharGenFlag.reset(RE::PlayerCharacter::ByCharGenFlag::kDisableSaving);
}

// Our own save: saving is opened for the one call and closed again (whether the chargen flag also blocks
// BGSSaveLoadManager::Save is S17a's question; this works either way).
// Writes a save: `now` on the main thread (a menu event: the quit, before the engine resets), else as a task.
void WriteSave(std::string_view slot, std::string_view why, bool now = false) {
  auto write = [slot = std::string(slot), why = std::string(why)] {
    auto* mgr = RE::BGSSaveLoadManager::GetSingleton();
    if (!mgr || !Player()) return;
    SavingBlocked(false);
    mgr->Save(slot.c_str());
    SavingBlocked(true);
    auto& c = Get();
    std::lock_guard l(c.lock);
    c.last_save_s = Seconds();
    SKSE::log::info("saves: {} written ({})", slot, why);
  };
  if (now) write();
  else SKSE::GetTaskInterface()->AddTask(std::move(write));
}

// A menu that pauses the game is open (the Journal, the Tween hub, a crafting or lock menu): no interval save then,
// because a save's spinner closes the player's menu (game-8).
bool MenuOpen() {
  auto* ui = RE::UI::GetSingleton();
  return ui && ui->GameIsPaused();
}

// The engine's quit (to the desktop) or reset (to the main menu) flag: set when the player confirms Quit.
bool QuitRequested() {
  auto* m = RE::Main::GetSingleton();
  return m && (m->GetRuntimeData().quitGame || m->GetRuntimeData().resetGame);
}

bool CanSaveNow() {
  auto* ui = RE::UI::GetSingleton();
  auto* p = Player();
  return p && ui && !ui->IsMenuOpen(RE::LoadingMenu::MENU_NAME) && !Get().sitting && !Get().dying;
}

// --- the pile --------------------------------------------------------------------------------------------------
RE::TESObjectACTI* PileBase() { return Lookup<RE::TESObjectACTI>("death.vastei-pile"); }

RE::TESObjectREFR* PileRef() {
  auto ref = Get().pile_ref.get();
  return ref && !ref->IsDisabled() ? ref.get() : nullptr;
}

void RemovePileRef() {
  if (auto* ref = PileRef()) {
    ref->Disable();
    ref->SetDelete(true);
  }
  Get().pile_ref = {};
}

// The pile reference the game save holds, found again after a load (persistent references stay in the form map).
void FindPileRef() {
  auto& c = Get();
  c.pile_ref = {};
  auto* base = PileBase();
  if (!base) return;
  std::vector<RE::TESObjectREFR*> found;
  {
    const auto& [map, lock] = RE::TESForm::GetAllForms();
    RE::BSReadLockGuard g(lock);
    for (auto& [id, form] : *map)
      if (auto* ref = form ? form->AsReference() : nullptr; ref && ref->GetBaseObject() == base && !ref->IsDeleted())
        found.push_back(ref);
  }
  for (auto* ref : found) {
    if (!c.pile_ref && c.state.death.pile) c.pile_ref = ref->GetHandle();
    else { ref->Disable(); ref->SetDelete(true); }  // a stray pile: the family says there is none, or one already
  }
  if (c.state.death.pile && !c.pile_ref)
    SKSE::log::error("death: the co-save holds a pile of {:.0f} but the save has no pile reference",
                     c.state.death.pile->vastei);
}

// --- the sitting view ------------------------------------------------------------------------------------------
void PushSitting() {
  auto& c = Get();
  if (!c.sitting) return;
  auto json = ac::msg::encode(ac::life::view(*c.sitting));
  if (!json) {
    SKSE::log::error("sitting: the view does not fit the schema: {}", json.error());
    return;
  }
  Push("sitting", std::move(*json));
}

// --- the router's handlers --------------------------------------------------------------------------------------
void OnLevelUpSurface(ac::router::SurfaceId) {
  SKSE::log::error("grow: the vanilla LevelUp Menu opened and was closed (a sighting is a failure, S16c)");
}

void OnDeathSurface(ac::router::SurfaceId) {
  auto* p = Player();
  if (!p) return;
  auto& c = Get();
  std::lock_guard l(c.lock);
  if (c.dying) return;
  c.dying = true;
  const auto at = PosOf(p);
  const auto d = ac::life::die(c.state, at, RosterNow());
  SKSE::log::info("death: fell at ({:.1f}, {:.1f}) in {:08X}; pile {:.0f}{}; wake {}", at.x, at.y, at.cell,
                  d.outcome.pile ? d.outcome.pile->vastei : 0.0, d.replaced_pile ? ", the earlier pile removed" : "",
                  d.had_wake_point ? "at the last rest" : "where the player fell (no rest yet)");
  SKSE::GetTaskInterface()->AddTask([d] {
    auto* p = Player();
    auto& c = Get();
    std::lock_guard l(c.lock);
    RemovePileRef();
    if (d.outcome.pile)
      if (auto* base = PileBase()) {
        base->SetFullName(ac::life::pile_name(d.outcome.pile->vastei).c_str());
        if (auto ref = p->PlaceObjectAtMe(base, true)) c.pile_ref = ref->GetHandle();
      }
    if (d.outcome.pile && !c.pile_ref) SKSE::log::error("death: the pile could not be placed (death.vastei-pile missing?)");
    // Wake at the last rest: the same space moves in place; another space needs the rest spot's reference.
    const auto here = SpaceOf(p);
    if (d.outcome.wake.cell == here) {
      const auto u = ac::life::to_units(d.outcome.wake);
      p->SetPosition(RE::NiPoint3(float(u[0]), float(u[1]), float(u[2])), true);
    } else if (auto spot = c.rest_spot.get()) {
      p->MoveTo(spot.get());
    } else {
      SKSE::log::error("death: the wake point is in {:08X}, the player in {:08X}, and the rest spot is not known since "
                       "the load; the player wakes here", d.outcome.wake.cell, here);
    }
    auto* avo = p->AsActorValueOwner();
    for (auto av : {RE::ActorValue::kHealth, RE::ActorValue::kStamina, RE::ActorValue::kMagicka})
      avo->RestoreActorValue(av, avo->GetPermanentActorValue(av));
    // The graph event alone left the life state at bleedout (diag6 4: the player woke unable to act); the engine's
    // own way is the life state back to alive, then the graph out of its bleedout idle. The log line is the check.
    if (auto* st = p->AsActorState(); st && st->IsBleedingOut()) {
      p->SetLifeState(RE::ACTOR_LIFE_STATE::kAlive);
      p->NotifyAnimationGraph("BleedOutStop");
      avo->RestoreActorValue(RE::ActorValue::kHealth, avo->GetPermanentActorValue(RE::ActorValue::kHealth));
      SKSE::log::info("death: bleedout {}", p->AsActorState()->IsBleedingOut() ? "STILL ON" : "ended");
    } else
      SKSE::log::info("death: bleedout ended (not bleeding out at the wake)");
    ResetActors(d.reset);
    c.health.clear();
    c.dying = false;
    SKSE::log::info("death: woke; carried vastei {:.0f}", c.state.prog.vastei);
  });
}

// --- the sinks --------------------------------------------------------------------------------------------------
class HitSink final : public RE::BSTEventSink<RE::TESHitEvent> {
 public:
  RE::BSEventNotifyControl ProcessEvent(const RE::TESHitEvent* e, RE::BSTEventSource<RE::TESHitEvent>*) override {
    auto* p = Player();
    if (!e || !p || !e->target || !e->cause) return RE::BSEventNotifyControl::kContinue;
    auto* target = e->target->As<RE::Actor>();
    auto* cause = e->cause->As<RE::Actor>();
    if (!target || !cause) return RE::BSEventNotifyControl::kContinue;
    if (cause == p && target != p) {
      double dmg;
      {
        std::lock_guard l(Get().lock);
        dmg = Get().health.damage(target->GetFormID(), Health(target, false), Health(target, true));
      }
      if (const auto skill = BlowSkill(e->source)) Use(ac::life::hit_dealt(*skill, dmg, TargetOf(target)), "hit");
    } else if (target == p) {
      double dmg;
      {
        std::lock_guard l(Get().lock);
        dmg = Get().health.damage(p->GetFormID(), Health(p, false), Health(p, true));
      }
      const bool blocked = e->flags.any(RE::TESHitEvent::Flag::kHitBlocked);
      for (const auto& ev : ac::life::hit_taken(dmg, Health(p, true), WornArmour(p), blocked, cause->IsHostileToActor(p)))
        Use(ev, "struck");
    }
    return RE::BSEventNotifyControl::kContinue;
  }
};

class KillSink final : public RE::BSTEventSink<RE::TESDeathEvent> {
 public:
  RE::BSEventNotifyControl ProcessEvent(const RE::TESDeathEvent* e, RE::BSTEventSource<RE::TESDeathEvent>*) override {
    if (e && e->dead && e->actorDying) {  // any death of a roster actor may clear its place, whoever killed it
      std::lock_guard l(Get().lock);
      ClearedNow();
    }
    auto* p = Player();
    if (!e || !e->dead || !p || !e->actorDying || !e->actorKiller || e->actorKiller.get() != p)
      return RE::BSEventNotifyControl::kContinue;
    if (auto* victim = e->actorDying->As<RE::Actor>()) {
      Use(ac::life::kill(TargetOf(victim), Health(p, true), WornArmour(p)), "kill");
      std::lock_guard l(Get().lock);
      Get().health.forget(victim->GetFormID());
    }
    return RE::BSEventNotifyControl::kContinue;
  }
};

class CastSink final : public RE::BSTEventSink<RE::TESSpellCastEvent> {
 public:
  RE::BSEventNotifyControl ProcessEvent(const RE::TESSpellCastEvent* e, RE::BSTEventSource<RE::TESSpellCastEvent>*) override {
    if (!e || !e->object || e->object.get() != Player()) return RE::BSEventNotifyControl::kContinue;
    // had_effect: whether the spell changed something is CheckCast's (2.9); a cast counts until then.
    if (auto s = SchoolSkill(e->spell)) Use(ac::life::cast(*s, true), "cast");
    return RE::BSEventNotifyControl::kContinue;
  }
};

class LockSink final : public RE::BSTEventSink<RE::TESLockChangedEvent> {
 public:
  RE::BSEventNotifyControl ProcessEvent(const RE::TESLockChangedEvent* e, RE::BSTEventSource<RE::TESLockChangedEvent>*) override {
    if (!e || !e->lockedObject || e->lockedObject->IsLocked() || !Get().lockpicking)
      return RE::BSEventNotifyControl::kContinue;
    // The player's opening ceiling is 2.11's (locks); until then every picked lock is at the ceiling.
    Use(ac::life::unlock(0, 0), "unlock");
    return RE::BSEventNotifyControl::kContinue;
  }
};

class BleedoutSink final : public RE::BSTEventSink<RE::TESEnterBleedoutEvent> {
 public:
  RE::BSEventNotifyControl ProcessEvent(const RE::TESEnterBleedoutEvent* e, RE::BSTEventSource<RE::TESEnterBleedoutEvent>*) override {
    if (!e || !e->actor || e->actor.get() != Player()) return RE::BSEventNotifyControl::kContinue;
    auto& c = Get();
    ac::router::Verdict v;
    {
      std::lock_guard l(c.lock);
      v = c.router.on_surface(ac::router::SurfaceId::playerDeath);
    }
    if (!v.handled) SKSE::log::error("death: the player bled out and no death handler ran: {}", v.note);
    return RE::BSEventNotifyControl::kContinue;
  }
};

// The menus 1.5 watches: the quit (the suspend save, on the first menu close once the player confirmed Quit; never
// on a menu opening), the Lockpicking Menu (an unlock is the player's).
class LifeMenuSink final : public RE::BSTEventSink<RE::MenuOpenCloseEvent> {
 public:
  RE::BSEventNotifyControl ProcessEvent(const RE::MenuOpenCloseEvent* e, RE::BSTEventSource<RE::MenuOpenCloseEvent>*) override {
    if (!e) return RE::BSEventNotifyControl::kContinue;
    const std::string_view menu = e->menuName.c_str();
    if (menu == RE::LockpickingMenu::MENU_NAME) Get().lockpicking = e->opening;
    std::optional<ac::life::SuspendWhy> why;
    {
      auto& c = Get();
      std::lock_guard l(c.lock);
      why = c.quit_watch.on_menu(e->opening, QuitRequested());
    }
    if (why) SuspendCheck(*why, true);
    return RE::BSEventNotifyControl::kContinue;
  }
};

}  // namespace

void MirrorSkills() {
  auto* p = Player();
  if (!p) return;
  auto& c = Get();
  std::lock_guard l(c.lock);
  auto* avo = p->AsActorValueOwner();
  for (const auto& m : ac::life::skill_mirrors()) {
    if (m.actor_value.empty()) continue;  // a Custom Skills Framework skill: its globals are 1.3's, owed
    if (const auto av = AvNamed(m.actor_value); av != RE::ActorValue::kNone)
      avo->SetBaseActorValue(av, static_cast<float>(c.state.sheet.s[m.skill]));
    else
      SKSE::log::error("grow: skill mirror {} is not an engine actor value name", m.actor_value);
  }
}

void MirrorPools() {
  auto* p = Player();
  if (!p) return;
  auto& c = Get();
  std::lock_guard l(c.lock);
  const auto d = ac::derive_set(c.state.sheet, ac::Effective::of(c.state.sheet), 0);
  if (!d) {  // no sheet yet: the engine's own pools stay (a derived 0 would leave the player dead)
    SKSE::log::warn("pools: the sheet is uninitialised, the engine's pools are left alone");
    return;
  }
  auto* avo = p->AsActorValueOwner();
  avo->SetBaseActorValue(RE::ActorValue::kHealth, static_cast<float>(d->health));
  avo->SetBaseActorValue(RE::ActorValue::kStamina, static_cast<float>(d->stamina));
  avo->SetBaseActorValue(RE::ActorValue::kMagicka, static_cast<float>(d->magicka));
}

bool SuspendCheck(ac::life::SuspendWhy why, bool now) {
  auto& c = Get();
  bool due;
  {
    std::lock_guard l(c.lock);
    auto* p = Player();
    due = ac::life::suspend_due(why, Seconds(), c.last_save_s, p && p->IsInCombat(), CanSaveNow(),
                                    MenuOpen());
    if (due) c.last_save_s = Seconds();  // one at a time: the task sets it again when written
  }
  if (due) WriteSave(ac::life::kSuspendSave, ac::life::to_string(why), now);
  return due;
}

bool SuspendSaveFor(std::string_view wire) {
  const auto why = ac::life::suspend_why(wire);
  if (!why) {
    SKSE::log::warn("saves: SuspendSave(\"{}\") refused: the callers' reasons are quit, stream_drop and spot_reclaim", wire);
    return false;
  }
  const bool due = SuspendCheck(*why);
  if (!due) SKSE::log::info("saves: SuspendSave({}) not due (a menu or load is open, or the player is dying)", wire);
  return due;
}

std::optional<ac::SkillId> WeaponSkillOf(RE::FormID weapon) {
  return ClassSkill(RE::TESForm::LookupByID<RE::TESObjectWEAP>(weapon));
}

bool RestAt(RE::TESObjectREFR* spot) {
  auto* p = Player();
  if (!p || !spot) return false;
  auto& c = Get();
  std::lock_guard l(c.lock);
  if (c.sitting) return false;
  ac::rest::Context ctx;
  ctx.in_combat = p->IsInCombat();
  auto* lists = RE::ProcessLists::GetSingleton();
  ctx.hostiles_near = lists && lists->AreHostileActorsNear(nullptr);
  ctx.hunted = false;  // per-observer search is 2.11's (stealth); in combat and hostiles near cover Part 1
  auto* loc = p->GetCurrentLocation();
  ctx.in_settlement = LocationHas(loc, "hook.loc-settlement");
  ctx.in_dungeon = LocationHas(loc, "hook.loc-dungeon");
  ctx.bed = ac::rest::BedTier::camp;  // camp spots only in 1.5; beds by tier are 2.8's
  ctx.at = PosOf(spot);
  if (auto* cal = RE::Calendar::GetSingleton()) ctx.now = cal->GetHoursPassed();
  auto r = ac::life::rest_at(c.state, ctx, RosterNow());
  if (r.outcome.ruling.verdict != ac::rest::Verdict::rest) {
    SKSE::log::info("rest: refused: {}", r.notice);
    c.rest_notice = r.notice;  // the fragment shows it (Debug.Notification; the router's engineMessage row)
    return false;
  }
  c.rest_spot = spot->GetHandle();
  c.rest_notice.clear();
  SKSE::log::info("rest: at ({:.1f}, {:.1f}) in {:08X}; {} reset; sitting {}", ctx.at.x, ctx.at.y, ctx.at.cell,
                  r.reset.size(), r.sitting ? "opens" : "not due");
  auto reset = r.reset;
  SKSE::GetTaskInterface()->AddTask([reset] {
    auto* p = Player();
    auto* avo = p->AsActorValueOwner();
    for (auto av : {RE::ActorValue::kHealth, RE::ActorValue::kStamina, RE::ActorValue::kMagicka})
      avo->RestoreActorValue(av, avo->GetPermanentActorValue(av));
    ResetActors(reset);
    std::lock_guard l(Get().lock);
    Get().health.clear();  // healed and reset actors: a hit after the rest is measured from their new health
  });
  if (r.sitting) {
    c.sitting = ac::life::open_sitting(*r.sitting, c.state);
    PushSitting();
  }
  if (r.save_now) WriteSave(ac::life::kRestSave, "rest");
  FactsChanged("rest");
  return true;
}

std::string SittingIntent(std::string_view json) {
  auto& c = Get();
  std::lock_guard l(c.lock);
  if (!c.sitting) return R"({"error":"no sitting is open"})";
  auto r = ac::life::on_intent_text(*c.sitting, json, c.state);
  for (const auto& n : r.notes) SKSE::log::info("{}", n);
  if (r.closed) {
    c.sitting.reset();
    CloseView("sitting");
    MirrorAttributes();
    MirrorPools();
    WriteCombat("sitting closed");
    if (r.save_now) WriteSave(ac::life::kRestSave, "rest, after the sitting");
    FactsChanged("sitting closed");
    return {};
  }
  PushSitting();
  auto it = c.views.find("sitting");
  return it == c.views.end() ? std::string() : it->second;
}

std::optional<double> TakeVastei(RE::TESObjectREFR* pile) {
  auto* p = Player();
  if (!p || !pile) return std::nullopt;
  auto& c = Get();
  std::lock_guard l(c.lock);
  auto got = ac::life::take_pile(c.state, PosOf(p));
  if (!got) {
    SKSE::log::info("death: the pile is out of reach or gone");
    return std::nullopt;
  }
  SKSE::log::info("death: took the pile back, {:.0f} vastei (carried {:.0f})", *got, c.state.prog.vastei);
  SKSE::GetTaskInterface()->AddTask([] {
    std::lock_guard l(Get().lock);
    RemovePileRef();
  });
  return got;
}

void LifeDataLoaded() {
  auto& c = Get();
  std::lock_guard l(c.lock);
  // P4 at runtime: no vanilla skill gains (an AVIF override would ship vanilla records, decision 0003).
  int zeroed = 0;
  for (auto name : ac::life::vanilla_skills()) {
    auto* info = RE::ActorValueList::GetActorValueInfo(AvNamed(name));
    if (!info || !info->skill) SKSE::log::error("grow: vanilla skill {} is not an engine actor value name", name);
    if (info && info->skill) {
      info->skill->useMult = 0;
      info->skill->offsetMult = 0;
      ++zeroed;
    }
  }
  // Rest is the only save: the engine's own save points off (autosaves on rest, wait, travel, the menus).
  int off = 0;
  // They are SkyrimPrefs.ini settings (the Gameplay menu's "Save on ..."), so the prefs collection holds them.
  for (auto name : {"bSaveOnRest:SaveGame", "bSaveOnWait:SaveGame", "bSaveOnTravel:SaveGame", "bSaveOnCharacterMenu:SaveGame"}) {
    RE::Setting* s = nullptr;
    if (auto* prefs = RE::INIPrefSettingCollection::GetSingleton()) s = prefs->GetSetting(name);
    if (!s)
      if (auto* ini = RE::INISettingCollection::GetSingleton()) s = ini->GetSetting(name);
    if (s) {
      s->data.b = false;
      ++off;
    } else {
      SKSE::log::error("saves: {} is in neither ini collection; that engine save point stays on", name);
    }
  }
  // The roster: every persistent placed actor whose base carries the NPC_ Respawn flag (records make our people
  // persistent; the flag is the compiled `onRest` or `untilCleared` class, place_build.respawns). An actor whose
  // editor location (ACHR XLCN, place_build) is a clearable place's LCTN is `untilCleared` for that place.
  c.roster.clear();
  c.homes.clear();
  const auto on_rest = ac::respawn::class_named("onRest");
  const auto until_cleared = ac::respawn::class_named("untilCleared");
  auto* clearable = Lookup<RE::BGSKeyword>("hook.loc-clearable");
  if (on_rest && until_cleared) {
    const auto& [map, lock] = RE::TESForm::GetAllForms();
    RE::BSReadLockGuard g(lock);
    for (auto& [id, form] : *map) {
      auto* a = form ? form->As<RE::Actor>() : nullptr;
      auto* base = a ? a->GetActorBase() : nullptr;
      if (!base || a->IsPlayerRef()) continue;
      if (!base->actorData.actorBaseFlags.all(RE::ACTOR_BASE_DATA::Flag::kRespawn)) continue;
      // Our people only (game-16: 2930 vanilla and dependency actors carried the flag and were reset each rest,
      // unreviewed vanilla behaviour, 0012); ours are placed by Argonia.esm or ArgoniaWorld.esm.
      auto* file = a->GetFile(0);
      if (!file || !std::string_view(file->GetFilename()).starts_with("Argonia")) continue;
      c.homes[a->GetFormID()] = {a->GetPosition(), a->GetAngle(), a->GetParentCell(), a->GetWorldspace()};
      auto* loc = a->GetEditorLocation();
      if (clearable && loc && loc->HasKeyword(clearable))
        c.roster.push_back({a->GetFormID(), *until_cleared, loc->GetFormID()});
      else
        c.roster.push_back({a->GetFormID(), *on_rest});
    }
  }
  SKSE::log::info("respawn: roster of {} flagged actors ({} in clearable places)", c.roster.size(),
                  std::ranges::count_if(c.roster, [](const auto& r) { return r.place != 0; }));
  static HitSink hits;
  static KillSink kills;
  static CastSink casts;
  static LockSink locks;
  static BleedoutSink bleedouts;
  static LifeMenuSink menus;
  if (auto* src = RE::ScriptEventSourceHolder::GetSingleton()) {
    src->AddEventSink<RE::TESHitEvent>(&hits);
    src->AddEventSink<RE::TESDeathEvent>(&kills);
    src->AddEventSink<RE::TESSpellCastEvent>(&casts);
    src->AddEventSink<RE::TESLockChangedEvent>(&locks);
    src->AddEventSink<RE::TESEnterBleedoutEvent>(&bleedouts);
  }
  if (auto* ui = RE::UI::GetSingleton()) ui->AddEventSink<RE::MenuOpenCloseEvent>(&menus);
  for (const auto& line : ac::life::install(c.router, OnLevelUpSurface, OnDeathSurface)) c.router_log.push_back(line);
  c.router_log.push_back("sinks: TESHitEvent, TESDeathEvent (kills), TESSpellCastEvent, TESLockChangedEvent, "
                         "TESEnterBleedoutEvent, MenuOpenCloseEvent (quit, lockpicking)");
  SKSE::log::info("grow: {} vanilla skills' gain off, {} engine save points off, roster {} actors", zeroed, off,
                  c.roster.size());
}

void LifeGameReady() {
  auto* p = Player();
  if (!p) return;
  auto& c = Get();
  std::lock_guard l(c.lock);
  // The death intercept (the Respawn - Soulslike pattern): the player is essential, so a lethal blow is a bleedout.
  if (auto* base = p->GetActorBase()) base->actorData.actorBaseFlags.set(RE::ACTOR_BASE_DATA::Flag::kEssential);
  SavingBlocked(true);
  c.sitting.reset();
  c.dying = false;
  c.health.clear();
  c.rest_spot = {};
  FindPileRef();
  if (auto* base = PileBase(); base && c.state.death.pile)
    base->SetFullName(ac::life::pile_name(c.state.death.pile->vastei).c_str());
  MirrorSkills();
  MirrorPools();
}

}  // namespace argonia::plugin
