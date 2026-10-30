#include "argonia/core/quest_runtime.h"

#include <algorithm>

namespace argonia::core::quest_runtime {

const Stage* Graph::stage(std::int32_t id_) const {
  auto it = std::find_if(stages.begin(), stages.end(), [&](const Stage& s) { return s.id == id_; });
  return it == stages.end() ? nullptr : &*it;
}

namespace {

// The host's facts, with this quest's own objectives answered from what is done.
struct Own : conditions::Facts {
  const Graph& g;
  const std::vector<std::uint16_t>& done;
  const conditions::Facts& host;
  Own(const Graph& g_, const std::vector<std::uint16_t>& d, const conditions::Facts& h) : g(g_), done(d), host(h) {}

  std::optional<bool> truth(conditions::Term t, std::span<const conditions::Arg> keys) const override {
    if (t == conditions::Term::objectiveComplete && keys.size() == 2 && std::get_if<std::string>(&keys[0]) &&
        std::get<std::string>(keys[0]) == g.id) {
      const auto* obj = std::get_if<std::string>(&keys[1]);
      for (const auto& s : g.stages)
        for (const auto& o : s.objectives)
          if (obj && o.id == *obj) return std::find(done.begin(), done.end(), o.index) != done.end();
      return std::nullopt;
    }
    return host.truth(t, keys);
  }
  std::optional<double> number(conditions::Term t, std::span<const conditions::Arg> keys) const override {
    return host.number(t, keys);
  }
  std::optional<std::string> state(conditions::Term t, std::span<const conditions::Arg> keys) const override {
    return host.state(t, keys);
  }
};

}  // namespace

Step step(const Graph& g, const State& s, const conditions::Facts& f) {
  Step out;
  if (s.stage == 0) {
    if (g.start_when && conditions::evaluate_valid(*g.start_when, f).holds()) out.set_stage = g.start;
    return out;
  }
  const Stage* st = g.stage(s.stage);
  if (!st || st->ending != Ending::none) return out;
  std::vector<std::uint16_t> done = s.done;
  for (const auto& o : st->objectives) {
    if (std::find(done.begin(), done.end(), o.index) != done.end()) continue;
    if (conditions::evaluate_valid(o.complete_when, Own(g, done, f)).holds()) {
      done.push_back(o.index);
      out.completed.push_back(o.index);
    }
  }
  const Own facts(g, done, f);
  for (const auto& e : st->edges)
    if (conditions::evaluate_valid(e.when, facts).holds()) {
      out.set_stage = e.to;
      break;
    }
  return out;
}

std::vector<std::string> check(const Graph& g) {
  std::vector<std::string> out;
  const std::string q = g.id + " ";
  if (g.start_when)
    if (auto why = conditions::check(*g.start_when)) out.push_back(q + "startWhen: " + *why);
  if (!g.stage(g.start)) out.push_back(q + "start " + std::to_string(g.start) + ": no such stage");
  for (const auto& s : g.stages) {
    const std::string at = q + "stage " + std::to_string(s.id);
    if (s.id == 0) out.push_back(at + ": stage 0 is the start-up stage");
    if (s.ending != Ending::none && !s.edges.empty()) out.push_back(at + ": an ending has edges");
    if (s.ending == Ending::none && s.edges.empty()) out.push_back(at + ": not an ending and no way out");
    for (const auto& o : s.objectives)
      if (auto why = conditions::check(o.complete_when)) out.push_back(at + " objective " + o.id + ": " + *why);
    bool successors = false;
    for (const auto& e : s.edges) {
      if (!g.stage(e.to)) out.push_back(at + " -> " + std::to_string(e.to) + ": no such stage");
      if (auto why = conditions::check(e.when)) out.push_back(at + " -> " + std::to_string(e.to) + ": " + *why);
      if (!e.fail_forward) successors = true;
      else if (successors) out.push_back(at + ": a fail-forward after a successor (fail-forwards come first)");
    }
  }
  return out;
}

}  // namespace argonia::core::quest_runtime
