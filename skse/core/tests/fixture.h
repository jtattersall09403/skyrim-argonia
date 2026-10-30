// The generated topic fixture (fixture_topics.h: five Claywater speakers' rows) as the store's types, for the L2
// tests: talk::fixture_rows, the same conversion the in-game store uses, over every line.
#pragma once
#include "argonia/core/fixture_topics.h"
#include "argonia/core/talk.h"

#include <string>
#include <vector>

namespace fixture_load {

using namespace argonia::core;

inline std::vector<std::expected<actions::Action, std::string>> action_list(std::size_t l) {
  return talk::fixture_rows::action_list(l);
}
inline std::vector<topics::Topic> fixture_topics() { return talk::fixture_rows::topics(); }
// Every fixture line; `errors` collects any row a constructor refused (none expected).
inline std::vector<topics::Line> fixture_lines(std::vector<std::string>& errors) {
  return talk::fixture_rows::lines(false, errors);
}

}  // namespace fixture_load
