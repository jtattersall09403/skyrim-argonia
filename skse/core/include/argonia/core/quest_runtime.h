// The quest stage graph at run time (1.4; 2.12 §a; native map G19.1, G19.2): each quest's stages, their edges in
// the rule's order (fail-forwards first, so a death or the deadline overrides progress, then successors, each in
// record order) and the objectives' completion conditions, generated from the quest records into quests.h by
// tools/argonia_world/quest_gen.py. On every fact change ArgoniaCore asks `step` what to do for each watched quest
// and applies it with the engine's own quest functions (SetObjectiveCompleted, SetStage); the stage's begin
// fragment then does the rest. No condition is evaluated in Papyrus.
#pragma once
#include "argonia/core/conditions.h"

#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <vector>

namespace argonia::core::quest_runtime {

using conditions::Pred;

enum class Ending : std::uint8_t { none, complete, failed };

struct Objective {
  std::uint16_t index;  // the QUST objective index
  std::string id;       // the record's objective id (objectiveComplete's second argument)
  Pred complete_when;
};

struct Edge {
  std::int32_t to;
  bool fail_forward;
  Pred when;
};

struct Stage {
  std::int32_t id;
  Ending ending;
  std::vector<Objective> objectives;
  std::vector<Edge> edges;  // fail-forwards first, then successors
};

struct Graph {
  std::string id;                   // the quest's world id
  std::int32_t start;               // the first stage
  std::optional<Pred> start_when;   // none: started by an action
  std::vector<Stage> stages;
  const Stage* stage(std::int32_t id) const;
};

// The quest as the engine holds it: its stage (0: running, not yet started; the generator's start-up stage) and
// the objectives already completed.
struct State {
  std::int32_t stage = 0;
  std::vector<std::uint16_t> done;
};

struct Step {
  std::vector<std::uint16_t> completed;   // objectives to mark completed, in record order
  std::optional<std::int32_t> set_stage;  // the stage to set, if an edge holds
  bool operator==(const Step&) const = default;
};

// What the quest does now. Objectives are completed first, so an edge that reads objectiveComplete of its own
// quest sees them; a fact the host cannot answer leaves its condition unknown, which never holds.
Step step(const Graph& g, const State& s, const conditions::Facts& f);

// Why a graph cannot run (an invalid tree, a dangling edge, an ending with edges); empty when it can.
std::vector<std::string> check(const Graph& g);

}  // namespace argonia::core::quest_runtime
