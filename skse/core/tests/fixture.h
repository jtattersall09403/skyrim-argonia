// Helpers turning the generated topic fixture (fixture_topics.h: five Claywater speakers' rows) into the store's
// types, through the same validating constructors a loader uses.
#pragma once
#include "argonia/core/fixture_topics.h"
#include "argonia/core/topics.h"

#include <string>
#include <vector>

namespace fixture_load {

namespace fx = argonia::core::gen::fixture;
using namespace argonia::core;

inline conditions::Arg arg(const fx::FxArg& a) {
  if (a.kind == fx::FxArg::is_text) return std::string(a.text);
  return a.number;
}

inline std::expected<conditions::Pred, std::string> cond(std::size_t c) {
  const auto& fc = fx::kConds[c];
  std::vector<conditions::FlatNode> nodes;
  for (std::size_t i = 0; i < fc.node_count; ++i) {
    const auto& n = fx::kNodes[fc.first_node + i];
    std::vector<conditions::Arg> args;
    for (std::size_t j = 0; j < n.arg_count; ++j) args.push_back(arg(fx::kArgs[n.first_arg + j]));
    nodes.push_back({n.parent, n.term, std::move(args)});
  }
  return conditions::from_flat(nodes);
}

inline std::vector<std::expected<actions::Action, std::string>> action_list(std::size_t l) {
  std::vector<std::expected<actions::Action, std::string>> out;
  const auto& al = fx::kActionLists[l];
  for (std::size_t i = 0; i < al.count; ++i) {
    const auto& a = fx::kActions[al.first + i];
    std::vector<conditions::Arg> args;
    for (std::size_t j = 0; j < a.arg_count; ++j) args.push_back(arg(fx::kActionArgs[a.first_arg + j]));
    out.push_back(actions::make(a.verb, std::move(args)));
  }
  return out;
}

inline std::vector<topics::Topic> fixture_topics() {
  std::vector<topics::Topic> out;
  for (const auto& t : fx::kTopics) {
    topics::Topic x{std::string(t.id), std::string(t.label), {}, t.essential};
    for (std::size_t i = 0; i < t.form_count; ++i) x.forms.emplace_back(fx::kForms[t.first_form + i]);
    out.push_back(std::move(x));
  }
  return out;
}

// Every fixture line; `errors` collects any row a constructor refused (none expected).
inline std::vector<topics::Line> fixture_lines(std::vector<std::string>& errors) {
  std::vector<topics::Line> out;
  for (const auto& l : fx::kLines) {
    topics::Line x;
    x.id = l.id;
    auto t = topics::line_type(l.type);
    if (!t) { errors.push_back(x.id + ": type " + std::string(l.type)); continue; }
    x.type = *t;
    x.speaker = l.speaker;
    x.topic = l.topic;
    x.words = l.words;
    x.low = l.low;
    x.high = l.high;
    if (l.cond >= 0) {
      auto c = cond(std::size_t(l.cond));
      if (c) x.available = *c; else errors.push_back(x.id + ": " + c.error());
    }
    for (std::size_t i = 0; i < l.link_count; ++i) x.links.emplace_back(fx::kLinks[l.first_link + i]);
    if (l.actions >= 0)
      for (auto& a : action_list(std::size_t(l.actions))) {
        if (a) x.on_delivered.push_back(*a); else errors.push_back(x.id + ": " + a.error());
      }
    out.push_back(std::move(x));
  }
  return out;
}

}  // namespace fixture_load
