// The action vocabulary (85 §B) as typed actions over a pure effects interface: a line's onDelivered, a stage's
// onEnter, an ending's rewards. Each verb's argument kinds come from the action_shape_arg rows (tables_actions.h).
// `run` validates a whole list, checks what can be checked before anything changes (the player has the gold and the
// items a list takes), then applies the actions in order through `Effects`, which ArgoniaCore implements with one
// native per verb named as the verb (GrantTopic, SetFlag, ...). World state such as flags lives behind Effects
// (1.4's quest_state), not here.
#pragma once
#include "argonia/core/conditions.h"
#include "argonia/core/tables_actions.h"

#include <cstddef>
#include <expected>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace argonia::core::actions {

using conditions::Arg;
using gen::Verb;

struct Action {
  Verb verb;
  std::vector<Arg> args;
  bool operator==(const Action&) const = default;
};

std::optional<Verb> verb_named(std::string_view id);
std::string_view name(Verb v);
// Why an action breaks the vocabulary (arity, argument kind), or none.
std::optional<std::string> check(const Action& a);
std::expected<Action, std::string> make(Verb v, std::vector<Arg> args);
std::expected<Action, std::string> make(std::string_view verb, std::vector<Arg> args);
std::string describe(const Action& a);  // "giveItem(item.x, 1)"

// What ArgoniaCore does. Each returns false when the game refused it. Every verb 1.3 covers has its own entry; the
// rest reach `other` until their chunk (2.5, 2.12) gives them one.
class Effects {
 public:
  virtual ~Effects() = default;
  virtual bool takeGold(int amount) = 0;
  virtual bool giveGold(int amount) = 0;
  virtual bool takeItem(std::string_view item, int count) = 0;
  virtual bool giveItem(std::string_view item, int count) = 0;
  virtual bool setFlag(std::string_view flag, bool value) = 0;
  virtual bool grantTopic(std::string_view topic) = 0;
  virtual bool applyLocalVariant(std::string_view place, std::string_view variant) = 0;
  virtual bool setPrice(std::string_view service, int price) = 0;
  virtual bool changeDisposition(std::string_view npc, int delta) = 0;  // delta already clamped to 0-100 by run
  virtual bool changeSettlementStanding(std::string_view settlement, int delta) = 0;
  virtual bool other(const Action& a) = 0;
};

struct Outcome {
  bool done = false;                 // every action applied
  std::size_t applied = 0;           // how many, in order
  std::vector<std::string> refused;  // why not: an invalid action, an unmet need, a refusal by the game
};

// Facts read: goldAtLeast (the player's gold), hasItem(item) (the count carried), dispositionAtLeast(npc) (the
// person's current disposition, to keep a change inside 0-100; unknown passes the delta through).
Outcome run(std::span<const Action> list, const conditions::Facts& facts, Effects& fx);

}  // namespace argonia::core::actions
