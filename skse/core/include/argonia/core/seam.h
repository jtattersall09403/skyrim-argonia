// The game-state seam as pure logic (1.1 §a-§d): everything ArgoniaCore's adapters do that is not an engine call.
// One State holds every co-save family (P7); `bind` registers them all with the families registry; WorldFacts
// answers the condition vocabulary over that state and what the engine reports (items, the living, gold, quests,
// the date); Session runs the action natives through `actions` and steps the watched quests through
// `quest_runtime`; `install` puts the hooks and the dialogue handler into the menu router. ArgoniaCore implements
// Engine and EngineWrites with CommonLibSSE-NG and applies what comes back (SetStage, SetObjectiveCompleted, the
// actor-value mirrors); no rule lives there, so all of it is tested here at L2.
#pragma once
#include "argonia/core/actions.h"
#include "argonia/core/conditions.h"
#include "argonia/core/cosave.h"
#include "argonia/core/death.h"
#include "argonia/core/disposition.h"
#include "argonia/core/families.h"
#include "argonia/core/forms.h"
#include "argonia/core/items.h"
#include "argonia/core/journal.h"
#include "argonia/core/progression.h"
#include "argonia/core/quest_runtime.h"
#include "argonia/core/quest_state.h"
#include "argonia/core/router.h"
#include "argonia/core/sheet.h"
#include "argonia/core/topics.h"
#include "argonia/core/weather.h"

#include <cstdint>
#include <optional>
#include <set>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace argonia::core::seam {

using Key = std::uint32_t;
// A world id's co-save key: FNV-1a 32, the same function as quest_state::key and topics::key.
constexpr Key key(std::string_view id) { return quest_state::key(id); }

// --- Records by world id (gen::kForms, from the formid table) ---------------------------------------------------
const gen::FormRow* form(std::string_view id);
const gen::FormRow* form_at(std::string_view plugin, std::uint32_t local);  // the reverse, for an engine form

// --- The watched quests (the QWCH family, version 1): quests whose stage graph ArgoniaCore steps ---------------
struct Watch {
  std::set<Key> quests;
  bool operator==(const Watch&) const = default;
};
inline constexpr std::uint32_t kWatchType = cosave::fourcc("QWCH");
cosave::Bytes encode(const Watch& w);
std::optional<Watch> decode(std::span<const std::uint8_t> b);

// --- Every family's state -----------------------------------------------------------------------------------
struct State {
  cosave::Meta meta;
  Sheet sheet;
  progression::Progress prog;
  disposition::Table disp;  // keyed by key(npc world id)
  journal::Log log;         // quest ids are key(quest world id)
  items::Table items;
  death::State death;
  quest_state::State quests;
  topics::Known known;
  Watch watch;
};

// Registers every family over `s`: META, STAT, DISP, JRNL, ITEM, DETH, QSTA, TOPC, QWCH. Returns the refusals
// (none expected; a second bind of the same registry is refused family by family).
std::vector<std::string> bind(families::Registry& reg, State& s);
// The META step a save takes: one more save, written by this build.
void on_save(State& s);
// A family's current payload digest (FNV-1a 64 of save(), as 16 hex digits): S10b's marker read. Empty: no such family.
std::string digest(const families::Registry& reg, std::uint32_t id);

// --- What the engine reports ----------------------------------------------------------------------------------
struct Date {
  int year = 0, month = 0, day = 1;  // month 0..11 (Skyrim's GameMonth), day 1..31
  double hour = 0;
};
struct QuestView {
  std::int32_t stage = 0;             // the engine's current stage
  std::vector<std::uint16_t> done;    // objectives completed
};
class Engine {
 public:
  virtual ~Engine() = default;
  virtual std::optional<int> item_count(std::string_view item) const = 0;  // none: not a record the engine has
  virtual std::optional<bool> alive(std::string_view npc) const = 0;       // none: no such actor loaded or placed
  virtual std::optional<int> gold() const = 0;
  virtual std::optional<QuestView> quest(std::string_view quest) const = 0;
  virtual std::optional<Date> date() const = 0;
};

// The season on a date (weather's calendar); none for a date the calendar does not have.
std::optional<weather::Season> season(const Date& d);
// A person's disposition now: the co-save's value once met, else their base (authored base 0 until the person
// rows carry one, 2.W5) from the player's effective Personality.
int disposition_of(const State& s, std::string_view npc);
// Quest state the actions keep in QSTA until their chunk gives them a family (2.6 prices, 2.12 variants and
// standing): a settlement's standing is the counter named by its id, a local variant the flag "<place>#<variant>",
// a service's price the counter "price#<service>".
std::string variant_flag(std::string_view place, std::string_view variant);
std::string price_counter(std::string_view service);

// The condition vocabulary over the state and the engine. Answered: knowsTopic, topicHeardFrom, flag,
// counterAtLeast, deedCountAtLeast, dispositionAtLeast, settlementStandingAtLeast, localVariantActive, levelAtLeast,
// attributeAtLeast, skillAtLeast (the co-save); hasItem, goldAtLeast, npcAlive, questStage, objectiveComplete,
// seasonIs (the engine). Every other term is unknown, so a condition reading it never holds.
class WorldFacts : public conditions::Facts {
 public:
  WorldFacts(const State& s, const Engine& e, std::span<const quest_runtime::Graph> graphs)
      : s_(s), e_(e), graphs_(graphs) {}
  std::optional<bool> truth(conditions::Term t, std::span<const conditions::Arg> keys) const override;
  std::optional<double> number(conditions::Term t, std::span<const conditions::Arg> keys) const override;
  std::optional<std::string> state(conditions::Term t, std::span<const conditions::Arg> keys) const override;

 private:
  const State& s_;
  const Engine& e_;
  std::span<const quest_runtime::Graph> graphs_;
};

// What ArgoniaCore does in the engine for an action: items and gold. False when the game refused it.
class EngineWrites {
 public:
  virtual ~EngineWrites() = default;
  virtual bool give_item(std::string_view item, int count) = 0;
  virtual bool take_item(std::string_view item, int count) = 0;
  virtual bool give_gold(int amount) = 0;
  virtual bool take_gold(int amount) = 0;
};

// The orders a step gives one watched quest, for the engine's own quest functions.
struct Order {
  std::string quest;                     // world id
  std::vector<std::uint16_t> completed;  // SetObjectiveCompleted, in order
  std::optional<std::int32_t> set_stage; // then SetStage
  bool operator==(const Order&) const = default;
};

class Session {
 public:
  Session(State& s, const Engine& e, EngineWrites& w, std::span<const quest_runtime::Graph> graphs)
      : s_(s), e_(e), w_(w), graphs_(graphs) {}

  // The quest natives (1.4's fragments). Each returns false, with `why`, when refused.
  bool watch(std::string_view quest, std::string* why = nullptr);
  bool unwatch(std::string_view quest);
  bool add_journal_entry(std::string_view quest, std::int32_t stage, int kind, const Date& at, std::string* why = nullptr);
  // One action verb with its arguments, through actions::run (validated, needs checked, disposition clamped).
  actions::Outcome act(std::string_view verb, std::vector<conditions::Arg> args);
  // A list (a line's onDelivered).
  actions::Outcome act(std::span<const actions::Action> list);

  // A fact changed: what each watched quest does now (quests the engine cannot report are skipped).
  std::vector<Order> step() const;

  WorldFacts facts() const { return WorldFacts(s_, e_, graphs_); }
  State& state() { return s_; }
  const State& state() const { return s_; }
  const quest_runtime::Graph* graph(std::string_view quest) const;

 private:
  State& s_;
  const Engine& e_;
  EngineWrites& w_;
  std::span<const quest_runtime::Graph> graphs_;
};

// --- The router's hooks, installed once (1.1 §d) ---------------------------------------------------------------
// Installs menuOpenClose and dialogueIntercept, registers `on_dialogue` as the dialogue menu's handler, then tries
// the dialogue intercept a second time to prove the refusal (S10a). Returns the load log lines, the refusal last.
std::vector<std::string> install(router::Router& r, router::Handler on_dialogue);

// --- The seven attributes and their actor-value mirrors (av-audit.md; P7: the sheet is canonical) --------------
struct Mirror { AttrId attribute; std::string_view actor_value; };  // the CommonLib ActorValue name
std::span<const Mirror> attribute_mirrors();
std::optional<AttrId> attribute_named(std::string_view name);  // "strength" ...
double attribute(const State& s, AttrId a);
// Sets the base attribute, clamped to the STAT family's range; returns the value stored.
double set_attribute(State& s, AttrId a, double v);

}  // namespace argonia::core::seam
