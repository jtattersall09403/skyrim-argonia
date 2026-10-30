// The combat wiring's adapter (1.6; docs/research/2026-10-30/combat-wiring.md): on every sheet, effect, equip or
// burden change the player's carriers are written into their reserved actor values (core/combat computes them;
// ARG_Perk_Carriers reads them), the vanilla weapon skills are pinned at 0, and TK Dodge's required perk is given or
// taken by burden tier (its own perk lock: no roll when overloaded). Engine writes run on the main thread.
#include "core.h"
#include "argonia/core/combat.h"

#include <atomic>
#include <chrono>
#include <filesystem>
#include <format>
#include <fstream>
#include <sstream>
#include <thread>

namespace argonia::plugin {

namespace {

namespace cb = ac::combat;

RE::PlayerCharacter* Player() { return RE::PlayerCharacter::GetSingleton(); }

struct RollLock {
  std::optional<cb::PerkLock> lock;
  RE::BGSPerk* perk = nullptr;
};
RollLock& Roll() {
  static RollLock r;
  return r;
}

ac::carriers::HandContext RightHand(RE::Actor* a) {
  ac::carriers::HandContext h;
  auto* weap = a->GetEquippedObject(false) ? a->GetEquippedObject(false)->As<RE::TESObjectWEAP>() : nullptr;
  if (!weap || weap->IsHandToHandMelee()) {
    h.skill = ac::SkillId::handToHand;
    return h;
  }
  h.skill = WeaponSkillOf(weap->GetFormID());  // none: not an Argonia weapon class, so the carrier stays neutral
  h.bow = weap->IsBow() || weap->IsCrossbow();
  return h;  // requirement_shortfall: item soft requirements are 2.7's; 0 until then
}


// Equip changes the hand and the armour; a carried-item change moves the burden tier.
class LoadoutSink final : public RE::BSTEventSink<RE::TESEquipEvent>,
                          public RE::BSTEventSink<RE::TESContainerChangedEvent> {
 public:
  RE::BSEventNotifyControl ProcessEvent(const RE::TESEquipEvent* e, RE::BSTEventSource<RE::TESEquipEvent>*) override {
    if (e && e->actor && e->actor.get() == Player()) WriteCombat("equip");
    return RE::BSEventNotifyControl::kContinue;
  }
  RE::BSEventNotifyControl ProcessEvent(const RE::TESContainerChangedEvent* e,
                                        RE::BSTEventSource<RE::TESContainerChangedEvent>*) override {
    constexpr RE::FormID kPlayerRef = 0x14;
    if (e && (e->newContainer == kPlayerRef || e->oldContainer == kPlayerRef)) {
      WriteCombat("carried");
      // The event comes before the engine moves the item, so the pass it queues reads the old weight: the tier lagged
      // one change behind (game-6: ingots added, roll still unlocked; removed, roll locked and stuck there). A second
      // pass once the burst has settled reads the weight as it is.
      static std::atomic<bool> settling{false};
      if (!settling.exchange(true))
        std::thread([] {
          std::this_thread::sleep_for(std::chrono::milliseconds(500));
          settling = false;
          WriteCombat("carried, settled");
        }).detach();
    }
    return RE::BSEventNotifyControl::kContinue;
  }
};

}  // namespace

std::vector<cb::Piece> WornPieces(RE::Actor* a) {
  using Slot = RE::BGSBipedObjectForm::BipedObjectSlot;
  // The four Unarmored slots (76 §118), one bit each in core/combat's order: head (a hood sits on the hair slot),
  // body, hands, feet.
  constexpr Slot kSlots[][2] = {{Slot::kHead, Slot::kHair}, {Slot::kBody, Slot::kBody}, {Slot::kHands, Slot::kHands},
                                {Slot::kFeet, Slot::kFeet}};
  std::vector<cb::Piece> out;
  for (auto& [obj, data] : a->GetInventory([](RE::TESBoundObject& o) { return o.IsArmor(); })) {
    if (!data.second || !data.second->IsWorn()) continue;
    auto* armo = obj->As<RE::TESObjectARMO>();
    if (!armo) continue;
    cb::Piece p;
    switch (armo->GetArmorType()) {
      case RE::BGSBipedObjectForm::ArmorType::kHeavyArmor: p.skill = ac::SkillId::heavyArmor; break;
      case RE::BGSBipedObjectForm::ArmorType::kLightArmor: p.skill = ac::SkillId::lightArmor; break;
      default: continue;  // clothing covers no armour slot; medium armour's marker is 1.3's (none yet)
    }
    for (std::uint32_t bit = 0; bit < std::size(kSlots); ++bit)
      if (armo->HasPartOf(kSlots[bit][0]) || armo->HasPartOf(kSlots[bit][1])) p.covers |= 1u << bit;
    // The raw rating is 0: our records carry none (w.armour.vanilla) and the item rows hold no rating yet (a stated
    // loss, docs/research/journals/combat.md). A record's own rating is the engine's to apply, never counted twice.
    out.push_back(p);
  }
  return out;
}

void CombatDataLoaded() {
  static LoadoutSink sink;
  if (auto* src = RE::ScriptEventSourceHolder::GetSingleton()) {
    src->AddEventSink<RE::TESEquipEvent>(&sink);
    src->AddEventSink<RE::TESContainerChangedEvent>(&sink);
  }
  auto& r = Roll();
  r = {};
  const std::filesystem::path toml = "Data/SKSE/Plugins/tk-dodge.toml";
  std::ifstream in(toml);
  if (!in) {
    SKSE::log::warn("combat: {} not found; the roll is not locked by burden", toml.string());
    return;
  }
  std::stringstream text;
  text << in.rdbuf();
  r.lock = cb::tk_dodge_perk_lock(text.str());
  if (!r.lock) {
    SKSE::log::error("combat: tk-dodge.toml names no readable sDodgeRequiredPerkID; the roll is not locked by burden");
    return;
  }
  auto* dh = RE::TESDataHandler::GetSingleton();
  r.perk = dh ? dh->LookupForm<RE::BGSPerk>(r.lock->local, r.lock->plugin) : nullptr;
  if (!r.perk) {
    SKSE::log::error("combat: TK Dodge's required perk {}|{:X} is not in this load order", r.lock->plugin, r.lock->local);
    r.lock.reset();
    return;
  }
  SKSE::log::info("combat: TK Dodge perk lock {} (perk {:08X}); the roll follows the burden tier",
                  r.lock->on ? "on" : "off (bUsePerkLock = false: every tier rolls)", r.perk->GetFormID());
}

void WriteCombat(std::string_view why) {
  // One pending pass at a time: a burst of changes (Take All from a chest) queues one task, which reads the state
  // as it is when it runs; the reasons are joined for the log.
  static std::mutex m;
  static std::string pending;
  {
    std::lock_guard g(m);
    const bool queued = !pending.empty();
    if (pending.find(why) == std::string::npos) pending += (queued ? ", " : "") + std::string(why);
    if (queued) return;
  }
  SKSE::GetTaskInterface()->AddTask([] {
    std::string why;
    {
      std::lock_guard g(m);
      why = std::exchange(pending, {});
    }
    auto* p = Player();
    if (!p) return;
    auto& c = Get();
    std::lock_guard l(c.lock);
    auto* avo = p->AsActorValueOwner();
    cb::Loadout lo;
    lo.right = RightHand(p);
    lo.worn = WornPieces(p);
    lo.carried_kg = avo->GetActorValue(RE::ActorValue::kInventoryWeight) / ac::gen::units::weight_per_kg;
    if (c.state.sheet.uninitialised()) {
      SKSE::log::warn("combat: the sheet is uninitialised, no carrier is written ({})", why);
      return;
    }
    const auto pass = cb::compute(c.state.sheet, ac::Effective::of(c.state.sheet), lo);
    std::string line;
    for (const auto& w : pass.writes) {
      const auto av = AvNamed(w.actor_value);
      if (av == RE::ActorValue::kNone) {
        SKSE::log::error("combat: carrier actor value {} unknown to the runtime", w.actor_value);
        continue;
      }
      avo->SetBaseActorValue(av, static_cast<float>(w.value));
      line += std::format(" {}={:.3f}", w.actor_value, w.value);
    }
    for (auto name : cb::pinned_vanilla_skills())
      if (const auto av = AvNamed(name); av != RE::ActorValue::kNone) avo->SetBaseActorValue(av, 0.0f);
      else SKSE::log::error("combat: pinned skill {} unknown to the runtime", name);
    auto& r = Roll();
    if (const auto want = cb::roll_perk_wanted(r.lock, pass.burden); want && r.perk && *want != p->HasPerk(r.perk)) {
      if (*want) p->AddPerk(r.perk);
      else p->RemovePerk(r.perk);
      SKSE::log::info("combat: roll {} (burden {})", *want ? "unlocked" : "locked", ac::gen::kBurdenTierNames[std::size_t(pass.burden)]);
    }
    line = std::format("burden {}, AR {:.1f};", ac::gen::kBurdenTierNames[std::size_t(pass.burden)],
                       pass.armour_rating) + line;
    static std::string last;  // logged when the values change, not at every pick-up
    if (line != last) SKSE::log::info("combat: carriers ({}): {}", why, line);
    last = std::move(line);
  });
}

}  // namespace argonia::plugin
