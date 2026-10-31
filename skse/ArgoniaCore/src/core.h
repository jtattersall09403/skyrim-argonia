// ArgoniaCore's adapter layer (1.1 §a-§d): the only place CommonLibSSE-NG meets skse/core. Every rule is in
// skse/core (seam, talk, quest_runtime, router, families ...) and tested there; these files turn engine events into
// the seam's inputs and write its outputs back (SetStage, SetObjectiveCompleted, actor values, globals, view pushes).
#pragma once
#include "argonia/core/combat.h"
#include "argonia/core/life.h"
#include "argonia/core/quests.h"
#include "argonia/core/router.h"
#include "argonia/core/seam.h"
#include "argonia/core/talk.h"
#include "argonia/core/things.h"
#include "argonia/core/views.h"

#include <map>
#include <mutex>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace argonia::plugin {

namespace ac = argonia::core;

struct Core {
  std::recursive_mutex lock;  // natives, events and the co-save callbacks all take it
  ac::seam::State state;
  ac::families::Registry families;
  ac::router::Router router;
  std::vector<std::string> router_log;
  std::vector<ac::quest_runtime::Graph> graphs;
  std::optional<ac::topics::Store> store;
  std::optional<ac::talk::Conversation> talk;
  std::map<std::string, std::string, std::less<>> views;  // the last push per view, as the view received it
  std::optional<ac::weather::Season> season;              // the season the weather globals hold
  RE::ObjectRefHandle pending_speaker;                    // the person the intercept is opening for
  RE::ObjectRefHandle talk_ref;                           // the person the open conversation is with
  ac::seam::InFlight inflight;                            // quest orders dispatched, not yet run by the VM
  // 1.5 (life.cpp): grow, die, rest, save.
  ac::life::HealthWatch health;                           // each hit actor's health after its last hit
  std::optional<ac::life::Sitting> sitting;               // the open level sitting
  std::vector<ac::respawn::Roster> roster;                // the placed actors that reset at a rest
  struct Home { RE::NiPoint3 pos, rot; RE::TESObjectCELL* cell = nullptr; RE::TESWorldSpace* world = nullptr; };
  std::map<RE::FormID, Home> homes;                       // each roster actor's placement as the data left it
  std::optional<double> last_save_s;                      // the last rest or suspend save, real seconds
  RE::ObjectRefHandle pile_ref;                           // the vastei pile in the world
  RE::ObjectRefHandle rest_spot;                          // the camp spot of the last rest (since the load)
  std::string rest_notice;                                // why the last rest was refused
  bool dying = false;                                     // the death intercept is running
  bool lockpicking = false;                               // the Lockpicking Menu is open
  ac::life::QuitWatch quit_watch;                         // the actual quit, from the menu events (once per quit)
  // 1.2 §0 (views.cpp): the web-view host, the journal key's latch, the HUD's last bars.
  ac::views::Host view_host;
  ac::views::KeyLatch journal_key;
  std::vector<ac::msg::Bar> hud_bars;
  ac::journal::Notices journal_notices;  // the "journal updated" notices (game-10 §2): when, in skse/core journal
};
Core& Get();

// --- engine.cpp: records by world id, the engine reads and writes, the quest orders, the mirrors ------------------
RE::TESForm* Lookup(std::string_view world_id);
template <class T>
T* Lookup(std::string_view world_id) {
  auto* f = Lookup(world_id);
  return f ? f->As<T>() : nullptr;
}
std::optional<std::string> WorldId(const RE::TESForm* form);
// An actor value by its engine (AVIF enum) name; kNone for a name the runtime does not know.
RE::ActorValue AvNamed(std::string_view name);
inline constexpr RE::FormID kGold = 0x0000000F;  // Skyrim.esm's Gold001, the engine's own currency record
class GameEngine final : public ac::seam::Engine, public ac::seam::EngineWrites {
 public:
  std::optional<int> item_count(std::string_view item) const override;
  std::optional<bool> alive(std::string_view npc) const override;
  std::optional<int> gold() const override;
  std::optional<ac::seam::QuestView> quest(std::string_view quest) const override;
  std::optional<ac::seam::Date> date() const override;
  bool give_item(std::string_view item, int count) override;
  bool take_item(std::string_view item, int count) override;
  bool give_gold(int amount) override;
  bool take_gold(int amount) override;
  bool open_barter(std::string_view npc) override;
};
ac::seam::Session Session();
// A fact changed (`why` names it for the log): step the watched quests and apply the orders; check the season.
void FactsChanged(std::string_view why);
void NewCharacter();  // the sheet from race and class, once, at the new game (the studio character's answers)
void MirrorAttributes();
// The player's perks of ours: the dialogue intercept, the rest intercept and the combat carriers.
void EnsurePerks();

// --- dialogue.cpp: the router's handler, the view host, the sinks ---------------------------------------------
bool OpenDialogue(RE::TESObjectREFR* target);
std::string ViewIntent(std::string_view json);
// The dev bridge's greeting read: the window a conversation with this speaker opens on, as JSON; the refusal else.
std::expected<std::string, std::string> GreetingFor(std::string_view speaker_id);
void InstallHooks();
// natives.cpp: the dev bridge's `core <Native> [arg]` (1.7's journeys): a whitelisted native's value as the reply's
// JSON; HandleBridgeCore answers the "CORE" SKSE message in place and returns false for any other message.
std::expected<std::string, std::string> BridgeCall(std::string_view native, const std::optional<std::string>& arg);
bool HandleBridgeCore(SKSE::MessagingInterface::Message* m);

// --- life.cpp: grow, die, rest, save (1.5) ---------------------------------------------------------------------
void LifeDataLoaded();
void LifeGameReady();
void MirrorSkills();
void MirrorPools();
// True when a suspend save is due and written (now, on the main thread) or queued (a task).
bool SuspendCheck(ac::life::SuspendWhy why, bool now = false);
bool RestAt(RE::TESObjectREFR* spot);
std::string SittingIntent(std::string_view json);
std::optional<double> TakeVastei(RE::TESObjectREFR* pile);
// The skill an equipped weapon trains, from its Argonia weapon-class keyword; none for any other weapon.
std::optional<ac::SkillId> WeaponSkillOf(RE::FormID weapon);
// The suspend save on a caller's reason ("quit", "stream_drop"); false when refused or not due (the log says why).
bool SuspendSaveFor(std::string_view why);

// --- combat.cpp: the carriers, the pinned weapon skills, the roll lock (1.6) -------------------------------------
void CombatDataLoaded();
// Recompute and write on the main thread; `why` names the change for the log.
void WriteCombat(std::string_view why);
// The armour pieces an actor wears (heavy and light; clothing and medium's missing marker skipped), with the
// Unarmored slots each covers: one walk serves the hit's armour skill and the carriers' rating.
std::vector<ac::combat::Piece> WornPieces(RE::Actor* a);

// --- views.cpp: the PrismaUI binding (1.2 §0) -----------------------------------------------------------------
bool ViewsBound();
void ViewsPostLoad();    // kPostLoad: PrismaUI's API, or the views stay off
void ViewsDataLoaded();  // after InstallHooks: the views created, the journal and map handlers, the HUD loop
void ViewsGameReady();   // the HUD's whole state
bool JournalKeyTaken();  // the Journal Menu opening now follows the journal key (J, the pad's Back), not Escape
// A push keeps the view's last state (ViewState reads it) and sends it; a modal view opens on its first push.
void Push(std::string_view view, std::string json);
void CloseView(std::string_view view);
void CloseAllViews();
std::string JournalIntent(const ac::msg::JournalPage& at);
std::string ChartIntent(const ac::msg::ChartPan& pan);
std::string ViewProbe(std::string_view topics);  // dev: the probe's 300-topic window (bridge only)
std::vector<std::string> ViewsReport();          // dev: bound, and each view's ready/open
// An entry logged or a clue found: "Journal updated" through the engine's HUD notification and our HUD's notices,
// and the ArgoniaJournalNotice mod event (the bridge's `mod` events, so a journey can wait on it). Any thread.
void JournalNotice(ac::journal::NoticeCause cause, std::string_view quest, std::int32_t mark);

// --- natives.cpp ------------------------------------------------------------------------------------------------
bool RegisterNatives(RE::BSScript::IVirtualMachine* vm);
// A quest thing met (1.4): the record's row in the thing table sets its flag (the setFlag action); false when the
// record is no quest thing met this way. The activate hook's native and the Book Menu's opening call it.
bool MeetThing(const RE::TESForm* record, ac::things::Hook how);

}  // namespace argonia::plugin
