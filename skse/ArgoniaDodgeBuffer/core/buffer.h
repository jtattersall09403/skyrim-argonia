#pragma once
// The dodge buffer's rules, with no engine types (unit-tested on Linux by skse/check.sh):
//   a graph event named in `start_events` begins a dodge, one in `end_events` ends it;
//   a press of the attack button while dodging is buffered with its time;
//   at the end of the dodge, a press no older than buffer_seconds fires the light attack, or the power attack when
//   the button is still held past power_hold_seconds; a refused fire is retried once at the next end event.
#include <algorithm>
#include <string>
#include <string_view>
#include <vector>

#include "ini.h"

namespace argonia::dodgebuffer {

// A dodge whose end event never came (death, a load, a cancelled graph) stops counting after this long.
constexpr double kMaxDodgeSeconds = 3.0;

enum class Fire { None, Light, Power };

struct Context {
  bool in_menu = false;
  bool weapon_drawn = true;
};

inline bool matches(const std::vector<std::string>& names, std::string_view event) {
  const std::string e = lower(event);
  return std::any_of(names.begin(), names.end(), [&](const std::string& n) { return lower(n) == e; });
}

class Buffer {
 public:
  explicit Buffer(Settings s) : s_(std::move(s)) {}
  const Settings& settings() const { return s_; }
  bool dodging() const { return dodging_; }
  bool buffered() const { return buffered_; }

  // A graph event reached the player. Returns what to fire now (None unless this is an end event that fires).
  Fire on_graph_event(std::string_view event, double now, const Context& ctx) {
    if (!s_.enabled) return Fire::None;
    if (matches(s_.start_events, event)) {
      dodging_ = true;
      dodge_at_ = now;
      buffered_ = retry_ = held_ = false;
      return Fire::None;
    }
    if (!matches(s_.end_events, event)) return Fire::None;
    if (retry_) return decide(now, ctx);  // the graph refused the first try: this is the one more
    if (!dodging_) return Fire::None;  // a fallback end event (tailCombatIdle) with no dodge behind it
    dodging_ = false;
    return decide(now, ctx);
  }

  // The attack button went down (true) or up (false) at `now`.
  void on_button(bool down, double now) {
    if (!s_.enabled) return;
    if (down) {
      if (!dodging_ || now - dodge_at_ > kMaxDodgeSeconds) return;
      buffered_ = true;
      held_ = true;
      press_at_ = now;
    } else {
      held_ = false;
    }
  }

  // The graph refused the event just fired: keep the press for the next end event.
  void rejected() { retry_ = buffered_ = true; }

 private:
  Fire decide(double now, const Context& ctx) {
    const bool had = buffered_;
    const bool fresh = now - press_at_ <= s_.buffer_seconds;
    const bool power = held_ && now - press_at_ > s_.power_hold_seconds;
    buffered_ = retry_ = false;
    if (!had || !fresh || ctx.in_menu || !ctx.weapon_drawn) return Fire::None;
    return power ? Fire::Power : Fire::Light;
  }

  Settings s_;
  bool dodging_ = false;
  bool buffered_ = false;
  bool retry_ = false;
  bool held_ = false;
  double dodge_at_ = 0.0;
  double press_at_ = 0.0;
};

}  // namespace argonia::dodgebuffer
