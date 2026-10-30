#include "argonia/core/quest_state.h"

#include <algorithm>

namespace argonia::core::quest_state {

void set_flag(State& s, std::string_view f, bool v) {
  if (v) s.flags[key(f)] = true;
  else s.flags.erase(key(f));  // false is the unset state: one spelling per value
}
bool flag(const State& s, std::string_view f) { return s.flags.count(key(f)) != 0; }

void add_counter(State& s, std::string_view c, std::int32_t by) {
  auto& v = s.counters[key(c)];
  v += by;
  if (v == 0) s.counters.erase(key(c));
}
std::int32_t counter(const State& s, std::string_view c) {
  auto it = s.counters.find(key(c));
  return it == s.counters.end() ? 0 : it->second;
}

void add_deed(State& s, std::string_view faction, std::string_view deed, std::int32_t by) {
  auto& f = s.deeds[key(faction)];
  auto& v = f[key(deed)];
  v = std::max(0, v + by);
  if (v == 0) f.erase(key(deed));
  if (f.empty()) s.deeds.erase(key(faction));
}
std::int32_t deeds(const State& s, std::string_view faction, std::string_view deed) {
  auto f = s.deeds.find(key(faction));
  if (f == s.deeds.end()) return 0;
  auto it = f->second.find(key(deed));
  return it == f->second.end() ? 0 : it->second;
}

cosave::Bytes encode(const State& s) {
  cosave::Writer w;
  w.u32(std::uint32_t(s.flags.size()));
  for (auto [k, v] : s.flags) { w.u32(k); w.u8(v ? 1 : 0); }
  w.u32(std::uint32_t(s.counters.size()));
  for (auto [k, v] : s.counters) { w.u32(k); w.i32(v); }
  w.u32(std::uint32_t(s.deeds.size()));
  for (const auto& [f, classes] : s.deeds) {
    w.u32(f);
    w.u32(std::uint32_t(classes.size()));
    for (auto [k, v] : classes) { w.u32(k); w.i32(v); }
  }
  return w.take();
}

std::optional<State> decode(std::span<const std::uint8_t> b) {
  cosave::Reader r(b);
  State s;
  auto n = r.u32();
  if (!n) return std::nullopt;
  for (std::uint32_t i = 0; i < *n; ++i) {
    auto k = r.u32(); auto v = r.u8();
    if (!k || !v || *v > 1 || s.flags.count(*k)) return std::nullopt;
    s.flags[*k] = *v == 1;
  }
  n = r.u32();
  if (!n) return std::nullopt;
  for (std::uint32_t i = 0; i < *n; ++i) {
    auto k = r.u32(); auto v = r.i32();
    if (!k || !v || s.counters.count(*k)) return std::nullopt;
    s.counters[*k] = *v;
  }
  n = r.u32();
  if (!n) return std::nullopt;
  for (std::uint32_t i = 0; i < *n; ++i) {
    auto f = r.u32(); auto m = r.u32();
    if (!f || !m || s.deeds.count(*f)) return std::nullopt;
    auto& classes = s.deeds[*f];
    for (std::uint32_t j = 0; j < *m; ++j) {
      auto k = r.u32(); auto v = r.i32();
      if (!k || !v || *v < 1 || classes.count(*k)) return std::nullopt;
      classes[*k] = *v;
    }
  }
  if (!r.done()) return std::nullopt;
  return s;
}

}  // namespace argonia::core::quest_state
