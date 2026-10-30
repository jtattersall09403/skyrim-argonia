// Grow, die, rest, save (1.5; 2.8 §a, §c; native map G16.1-G17.2) as pure logic over the seam's state: what
// ArgoniaCore's 1.5 adapters do that is not an engine call. The engine's sinks (a hit dealt or taken, a kill, a
// cast, an unlock) become progression's UseEvents here; a gain banks vastei and pending levels in the STAT family;
// a rest is ruled by `rest`, becomes the wake point, resets the respawn roster and opens the level sitting; the
// sitting spends vastei through `sitting` and answers the sitting view's intents; a death leaves one pile and wakes
// the player at the last rest; the save policy says when the rest save and the hidden suspend save are written.
// ArgoniaCore implements the engine side (actor values, the pile reference, the fade, BGSSaveLoadManager::Save).
#pragma once
#include "argonia/core/combat.h"
#include "argonia/core/death.h"
#include "argonia/core/messages.h"
#include "argonia/core/progression.h"
#include "argonia/core/respawn.h"
#include "argonia/core/rest.h"
#include "argonia/core/router.h"
#include "argonia/core/seam.h"
#include "argonia/core/sitting.h"

#include <array>
#include <cstdint>
#include <map>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace argonia::core::life {

// --- Skills and their engine mirrors (1.3 §a's table) -------------------------------------------------------
std::optional<SkillId> skill_named(std::string_view id);  // "longBlade" ...
// The skill a weapon trains, from the world id of its weapon-class keyword ("weapon_class.longBlade"); none for
// any other world id. The class ids are the skill ids (world db weapon_class.skill).
std::optional<SkillId> weapon_skill(std::string_view class_world_id);
// Where a skill's value is mirrored in the engine (P7: STAT is canonical): a vanilla skill actor value (CommonLib
// ActorValue name), or a Custom Skills Framework skill, whose globals 1.3 has not generated yet (empty name).
struct SkillMirror { SkillId skill; std::string_view actor_value; };
std::span<const SkillMirror> skill_mirrors();
// Every vanilla skill actor value whose use gain is switched off (P4: useMult and offsetMult 0), the hidden three
// included (One-handed, Two-handed, Pickpocket).
std::span<const std::string_view> vanilla_skills();

// --- Use events from the engine (G16.1) ----------------------------------------------------------------------
// The armour pieces worn, by the armour skill they train.
struct Worn { int light = 0, medium = 0, heavy = 0; };
// The armour skill a hit or a kill trains: the class worn on the most pieces (a tie goes to the heavier), Unarmored
// with none.
SkillId armour_skill(const Worn& w);
// The worn armour classes from the pieces the engine reports (one walk serves both the hit and the carriers).
Worn worn_of(std::span<const combat::Piece> pieces);
// The skill a landed blow trains, from what the hit's source is: a weapon with an Argonia class trains that class's
// skill, a hand-to-hand weapon (fists) Hand-to-hand; a spell, enchantment, poison or explosion (not a weapon) and a
// weapon with no class train nothing (none). 2.9 owns spell hits through CheckCast.
std::optional<SkillId> blow_skill(bool is_weapon, bool hand_to_hand, std::optional<SkillId> weapon_class);

// The damage of a hit, which TESHitEvent does not carry: the target's health before (last seen after its previous
// hit, its maximum the first time) less its health now, never below 0. Regeneration between hits makes it read low
// (a stated loss; S16a measures it against HandleHealthDamage before that hook is chosen).
class HealthWatch {
 public:
  double damage(std::uint32_t actor, double health_now, double health_max);
  void forget(std::uint32_t actor) { last_.erase(actor); }
  void clear() { last_.clear(); }
  std::size_t size() const { return last_.size(); }

 private:
  std::map<std::uint32_t, double> last_;
};

struct Target {
  double max_health = 0;
  bool hostile = true, dummy = false, summoned = false, helpless = false;
};
// The player's blow landed: the weapon class's skill (none: hand-to-hand).
progression::UseEvent hit_dealt(std::optional<SkillId> weapon, double damage, const Target& t);
// The player was struck: the worn armour class's hitTaken, then Block when the blow was blocked by a hostile.
std::vector<progression::UseEvent> hit_taken(double damage, double own_max_health, const Worn& w, bool blocked,
                                             bool attacker_hostile);
// The player killed a target: the worn armour class's armourKill.
progression::UseEvent kill(const Target& victim, double own_max_health, const Worn& w);
// A spell of the school's skill was cast; it counts only when it changed something.
progression::UseEvent cast(SkillId school, bool had_effect);
// A lock opened at `lock_level` with the player's opening ceiling.
progression::UseEvent unlock(double lock_level, double ceiling);

// One gain, for the SKSE log, the HUD's vastei plaque and the skill mirrors.
struct Gain {
  SkillId skill{};
  double points = 0, vastei = 0;
  int ranks = 0, levels = 0;
  bool counted() const { return points > 0; }
};
// Applies one use to the STAT family (no effect stack yet: the effective sheet is the base, owed to 2.1).
Gain use(seam::State& s, const progression::UseEvent& ev);

// --- Rest (G16.3, G17.1) --------------------------------------------------------------------------------------
struct Roster {
  std::vector<respawn::Roster> actors;  // the placed actors with a respawn class that resets
  respawn::ClearedSet cleared;          // the places cleared now
};
struct Rested {
  rest::Outcome outcome;                         // the ruling and what the rest does
  std::optional<sitting::State> sitting;         // opened when a level is pending
  std::vector<respawn::ActorId> reset;           // resurrect and return to their editor places
  bool save_now = false;                         // no sitting: the rest save is written now; else at its close
  std::string notice;                            // the refusal or the wait-only line, empty when rested
};
// Rules the rest; a rest taken becomes the wake point, clears the per-rest counters and resets the roster.
Rested rest_at(seam::State& s, const rest::Context& ctx, const Roster& roster);

// --- The sitting and its view (G16.3) -------------------------------------------------------------------------
std::string attribute_label(AttrId a);  // "Endurance"
struct Sitting {
  sitting::State st;
  double health_before = 0;
  int pending_after = 0;
  std::string notice;
};
Sitting open_sitting(const sitting::State& st, const seam::State& s);
msg::SittingState view(const Sitting& sit);
struct SittingReply {
  std::optional<msg::SittingState> state;  // the sitting to show; empty when it closed
  bool closed = false, save_now = false;   // closed: the level is taken and the rest save is due
  std::vector<std::string> notes;          // for the SKSE log
};
// sitting.buy or sitting.done as JSON, decoded by the schema twin; done (or any other closing) applies the sitting
// to the STAT family: the sheet with its points and the new level, the vastei left, one pending level taken.
SittingReply on_intent_text(Sitting& sit, std::string_view json, seam::State& s);
void close(const Sitting& sit, seam::State& s);

// A position in Skyrim units (a reference's GetPosition) as the core's metres; `cell` the cell or worldspace FormID.
rest::Pos at_units(double x, double y, double z, std::uint32_t cell);
// And back, for the engine's MoveTo.
std::array<double, 3> to_units(const rest::Pos& p);

// --- Death and the pile (G17.1) -------------------------------------------------------------------------------
struct Died {
  death::Outcome outcome;             // the pile (replacing any earlier) and the wake point
  bool had_wake_point = false;        // false: no rest yet, so the player wakes where they fell
  bool replaced_pile = false;         // an earlier pile was there and is removed
  std::vector<respawn::ActorId> reset;  // waking counts as a rest for respawn
};
// Carried vastei becomes the one pile at `at`; the player keeps skills, levels, items and gold.
Died die(seam::State& s, rest::Pos at, const Roster& roster);
// Takes the whole pile back when the player is within the recovery radius; the pile is gone after.
std::optional<double> take_pile(seam::State& s, rest::Pos player);
// The pile's display name: "Vastei (N)", N the whole vastei it holds.
std::string pile_name(double vastei);

// --- Saving: rest is the only save (2.8 §c) -------------------------------------------------------------------
inline constexpr std::string_view kRestSave = "ArgoniaRest";        // one slot, overwritten at each rest
inline constexpr std::string_view kSuspendSave = "ArgoniaSuspend";  // the hidden suspend save
enum class SuspendWhy { quit, stream_drop, interval };
const char* to_string(SuspendWhy w);
// A caller's reason by its wire name ("quit", "stream_drop"): only the two outside callers' reasons are accepted
// (the interval is ArgoniaCore's own), so an unknown word never forces a save in combat.
std::optional<SuspendWhy> suspend_why(std::string_view wire);
// The dev bridge's call (ArgoniaBridge `core-suspend <why>`): an SKSE message to ArgoniaCore whose data is this
// struct; ArgoniaCore's listener answers in `written` before the dispatch returns.
inline constexpr std::uint32_t kBridgeSuspendMessage = cosave::fourcc("SUSP");
struct BridgeSuspend {
  char why[32] = {};
  bool written = false;
};
// When the suspend save is written: on a quit or a stream drop always; at any other event once the interval has
// passed since the last save of either kind, never in combat and never while a menu is open (a save's spinner
// closes the player's menu: game-8's Journal lag); never when the game cannot save now (a load). Opening a menu is
// never a reason. `now_s` and `last_save_s` are real seconds.
bool suspend_due(SuspendWhy why, double now_s, std::optional<double> last_save_s, bool in_combat, bool can_save_now,
                 bool menu_open);
// The actual quit, from the menu events: the player confirmed Quit (to the main menu or the desktop) in the pause
// menu, so the engine's quit or reset flag is set, and a menu (the confirmation, then the Journal) closes. Returns
// `quit` once per quit, on the first close with the flag set; a menu opening never returns a reason; the latch
// clears when the flag does (a load or a new game).
class QuitWatch {
 public:
  std::optional<SuspendWhy> on_menu(bool opening, bool quit_requested);

 private:
  bool saved_ = false;
};

// --- The router's 1.5 hooks (1.1 §d) --------------------------------------------------------------------------
// Installs progressionOff and deathIntercept, registers `on_level_up` for the LevelUp Menu (blocked; a sighting is
// a failure, S16c) and `on_death` for playerDeath. Returns the load log lines for these two hooks.
std::vector<std::string> install(router::Router& r, router::Handler on_level_up, router::Handler on_death);

}  // namespace argonia::core::life
