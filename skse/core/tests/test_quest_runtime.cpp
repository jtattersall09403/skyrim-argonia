// L2: LF83's generated stage graph (quests.h) run by quest_runtime, with stage_walk's expectations
// (tools/argonia_world/tests/test_stage_walk.py): the start, every stage's fail-forwards (each keeper's death, the
// wet season) and the bribe from 10, 20 and 30, the main path to each ending, a death overriding progress,
// objectives completed first and kept, an unanswered fact never holding, and endings doing nothing.
#include "check.h"
#include "argonia/core/quests.h"

#include <map>
#include <set>
#include <string>

using namespace argonia::core;
using namespace argonia::core::quest_runtime;
using conditions::Arg;
using conditions::Term;

namespace {

const std::string kQuest = "quest.local.lf83";
const std::string kNpc = "npc.imperial-fringe.claywater-station.";
const std::string kKeeper = kNpc + "well-keeper", kPoler = kNpc + "landing-s-poler";
const std::string kCroc = "creature-at.imperial-fringe.claywater-station.eco-crocodile";

std::string s0(std::span<const Arg> k, std::size_t i = 0) { return std::get<std::string>(k[i]); }

// stage_walk's State as the host's facts.
struct World : conditions::Facts {
  std::set<std::pair<std::string, std::string>> heard;
  std::map<std::string, bool> flags;
  std::map<std::string, double> items;
  std::set<std::string> dead;
  std::string season = "dry";
  bool blind = false;  // answers nothing

  std::optional<bool> truth(Term t, std::span<const Arg> k) const override {
    if (blind) return std::nullopt;
    switch (t) {
      case Term::topicHeardFrom: return heard.count({s0(k), s0(k, 1)}) == 1;
      case Term::flag: { auto it = flags.find(s0(k)); return it != flags.end() && it->second; }
      case Term::npcAlive: return dead.count(s0(k)) == 0;
      default: return std::nullopt;
    }
  }
  std::optional<double> number(Term t, std::span<const Arg> k) const override {
    if (blind || t != Term::hasItem) return std::nullopt;
    auto it = items.find(s0(k));
    return it == items.end() ? 0.0 : it->second;
  }
  std::optional<std::string> state(Term t, std::span<const Arg>) const override {
    if (blind || t != Term::seasonIs) return std::nullopt;
    return season;
  }
};

const Graph& lf83() {
  static const auto all = gen::quest_graphs();
  for (const auto& g : all)
    if (g.id == kQuest) return g;
  std::fprintf(stderr, "LF83 not generated\n");
  std::abort();
}

std::optional<std::int32_t> next(std::int32_t stage, const World& w, std::vector<std::uint16_t> done = {}) {
  return step(lf83(), State{stage, std::move(done)}, w).set_stage;
}

void every_generated_graph_runs() {
  for (const auto& g : gen::quest_graphs()) {
    for (const auto& line : check(g)) std::fprintf(stderr, "  %s\n", line.c_str());
    CHECK(check(g).empty());
  }
  Graph broken = lf83();
  broken.stages.front().edges.push_back(Edge{77, false, broken.stages.front().edges.front().when});
  CHECK(check(broken).size() == 1);
}

void the_start() {
  World w;
  CHECK(!next(0, w));
  w.heard.insert({"topic.claywater-two-charges", kKeeper});
  CHECK(next(0, w) == 10);
  w.season = "wet";
  CHECK(!next(0, w));
}

void fail_forwards_and_the_bribe_from_every_working_stage() {
  for (std::int32_t at : {10, 20, 30}) {
    World keeper; keeper.dead.insert(kKeeper);
    CHECK(next(at, keeper) == 92);
    World poler; poler.dead.insert(kPoler);
    CHECK(next(at, poler) == 93);
    World wet; wet.season = "wet";
    CHECK(next(at, wet) == 90);
    World bribe; bribe.flags["flag.lf83.ford-charge-bought"] = true;
    CHECK(next(at, bribe) == 41);
    World both; both.dead = {kKeeper, kPoler};
    CHECK(next(at, both) == 92);  // the first fail-forward in record order
    World idle;
    CHECK(!next(at, idle));
  }
}

void the_main_path_and_the_other_settlement() {
  World w;
  w.heard = {{"topic.claywater-two-charges", kKeeper}, {"topic.claywater-two-charges", kPoler},
             {"topic.lf83-clay-bend", kPoler}};
  Step s = step(lf83(), State{10, {}}, w);
  CHECK(s.set_stage == 20 && s.completed == std::vector<std::uint16_t>({10, 11}));
  World croc; croc.dead.insert(kCroc);
  CHECK(!next(20, croc));
  croc.items["item.lf83.clay-basket"] = 1;
  Step s20 = step(lf83(), State{20, {}}, croc);
  CHECK(s20.set_stage == 30 && s20.completed == std::vector<std::uint16_t>({21, 22}));
  World none;
  CHECK(next(20, none, {21, 22}) == 30);  // completed objectives are kept
  World terms; terms.flags = {{"flag.lf83.one-charge-station", true}, {"flag.lf83.one-charge-landing", true}};
  CHECK(next(30, terms) == 40);
  World landing; landing.flags["flag.lf83.stop-charge-dropped"] = true;
  CHECK(next(30, landing) == 42);
  World half; half.flags["flag.lf83.one-charge-station"] = true;
  CHECK(!next(30, half));
}

void death_overrides_progress() {
  World w;
  w.heard = {{"topic.claywater-two-charges", kKeeper}, {"topic.claywater-two-charges", kPoler},
             {"topic.lf83-clay-bend", kPoler}};
  w.dead.insert(kPoler);
  CHECK(next(10, w) == 93);
}

void unknown_never_holds_and_endings_rest() {
  World blind; blind.blind = true;
  for (std::int32_t at : {0, 10, 20, 30}) CHECK(!next(at, blind));
  World dead; dead.dead = {kKeeper};
  for (std::int32_t at : {40, 41, 42, 90, 92, 93}) CHECK(step(lf83(), State{at, {}}, dead) == Step{});
}

}  // namespace

int main() {
  every_generated_graph_runs();
  the_start();
  fail_forwards_and_the_bribe_from_every_working_stage();
  the_main_path_and_the_other_settlement();
  death_overrides_progress();
  unknown_never_holds_and_endings_rest();
  return TEST_MAIN_RESULT("core.quest_runtime");
}
