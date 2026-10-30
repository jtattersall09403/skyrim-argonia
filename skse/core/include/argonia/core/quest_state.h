// The quest-side state the condition evaluator reads (1.4; native map P7, G19.2): named world flags (`flag`,
// `setFlag`), authored counters (`counterAtLeast`, `addCounter`) and deed counts per faction and deed class
// (`deedCountAtLeast`, old 0039). Canonical in the QSTA co-save family; globals and records only mirror it.
// Keys are the world ids hashed (FNV-1a, 32 bits), so a key never depends on load order or a table's row order;
// tools/argonia_world/quest_gen.py refuses two ids in use that share a hash.
#pragma once
#include "argonia/core/cosave.h"

#include <cstdint>
#include <map>
#include <optional>
#include <span>
#include <string_view>

namespace argonia::core::quest_state {

using Key = std::uint32_t;

constexpr Key key(std::string_view id) {
  std::uint32_t h = 2166136261u;
  for (char c : id) h = (h ^ std::uint8_t(c)) * 16777619u;
  return h;
}

struct State {
  std::map<Key, bool> flags;                 // unset: false
  std::map<Key, std::int32_t> counters;      // unset: 0
  std::map<Key, std::map<Key, std::int32_t>> deeds;  // faction -> deed class -> count; unset: 0, never below
  bool operator==(const State&) const = default;
};

void set_flag(State& s, std::string_view flag, bool v);
bool flag(const State& s, std::string_view flag);
void add_counter(State& s, std::string_view counter, std::int32_t by);
std::int32_t counter(const State& s, std::string_view counter);
void add_deed(State& s, std::string_view faction, std::string_view deed, std::int32_t by = 1);
std::int32_t deeds(const State& s, std::string_view faction, std::string_view deed);

inline constexpr std::uint32_t kQuestStateType = cosave::fourcc("QSTA");
cosave::Bytes encode(const State& s);
std::optional<State> decode(std::span<const std::uint8_t> b);

}  // namespace argonia::core::quest_state
