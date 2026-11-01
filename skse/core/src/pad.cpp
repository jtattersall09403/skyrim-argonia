#include "argonia/core/pad.h"

#include <algorithm>
#include <cmath>

namespace argonia::core::pad {

Act on_button(Context c, Button b) {
  if (c != Context::windows) return Act::none;
  switch (b) {
    case Button::A: return Act::click_left;
    case Button::X: return Act::click_right;
    case Button::B:
    case Button::Start: return Act::close;
    case Button::RB: return Act::next_pane;
    case Button::LB: return Act::prev_pane;
    case Button::LT: return Act::wheel_up;
    case Button::RT: return Act::wheel_down;
    case Button::Up: return Act::nudge_up;
    case Button::Down: return Act::nudge_down;
    case Button::Left: return Act::nudge_left;
    case Button::Right: return Act::nudge_right;
    case Button::Back: return Act::wait_rest;
    default: return Act::none;  // Y, LS, RS: free in the windows
  }
}

bool button_from_name(std::string_view n, Button& out) {
  struct Row {
    std::string_view name;
    Button b;
  };
  static constexpr Row rows[] = {{"A", Button::A},         {"B", Button::B},       {"X", Button::X},
                                 {"Y", Button::Y},         {"LB", Button::LB},     {"RB", Button::RB},
                                 {"LS", Button::LS},       {"RS", Button::RS},     {"START", Button::Start},
                                 {"BACK", Button::Back},   {"UP", Button::Up},     {"DOWN", Button::Down},
                                 {"LEFT", Button::Left},   {"RIGHT", Button::Right}, {"LT", Button::LT},
                                 {"RT", Button::RT}};
  for (const auto& r : rows)
    if (r.name == n) {
      out = r.b;
      return true;
    }
  return false;
}

bool button_from_code(std::uint32_t code, Button& out) {
  switch (code) {  // BSWin32GamepadDevice::Key (the codes controlmap.py binds)
    case 0x0001: out = Button::Up; return true;
    case 0x0002: out = Button::Down; return true;
    case 0x0004: out = Button::Left; return true;
    case 0x0008: out = Button::Right; return true;
    case 0x0010: out = Button::Start; return true;
    case 0x0020: out = Button::Back; return true;
    case 0x0040: out = Button::LS; return true;
    case 0x0080: out = Button::RS; return true;
    case 0x0100: out = Button::LB; return true;
    case 0x0200: out = Button::RB; return true;
    case 0x1000: out = Button::A; return true;
    case 0x2000: out = Button::B; return true;
    case 0x4000: out = Button::X; return true;
    case 0x8000: out = Button::Y; return true;
    case 0x0009: out = Button::LT; return true;
    case 0x000A: out = Button::RT; return true;
    default: return false;
  }
}

namespace {
// 0 inside the deadzone, then 0..1 over the rest of the throw, raised to the exponent.
double curve(double mag, const Tuning& t) {
  if (!(mag > t.deadzone)) return 0;
  double u = std::min(1.0, (mag - t.deadzone) / (1.0 - t.deadzone));
  return std::pow(u, t.exponent);
}
double scale(double screen_h) { return screen_h > 0 ? screen_h / 1080.0 : 1.0; }
}  // namespace

Vec cursor_velocity(Vec s, double screen_h, const Tuning& t) {
  double mag = std::hypot(s.x, s.y);
  double k = curve(mag, t);
  if (k == 0) return {};
  double speed = t.max_speed * scale(screen_h) * k;
  return {speed * s.x / mag, -speed * s.y / mag};  // stick up is screen up
}

Vec cursor_step(Vec at, Vec stick, double dt, double w, double h, const Tuning& t) {
  if (!(dt > 0)) dt = 0;
  dt = std::min(dt, 0.1);  // a long frame (a hitch, a load) never flings the cursor
  auto v = cursor_velocity(stick, h, t);
  return {std::clamp(at.x + v.x * dt, 0.0, std::max(0.0, w - 1)), std::clamp(at.y + v.y * dt, 0.0, std::max(0.0, h - 1))};
}

int scroll_step(Scroll& s, double y, double dt, const Tuning& t) {
  double k = curve(std::abs(y), t);
  if (k == 0) {
    s.acc = 0;
    return 0;
  }
  dt = std::clamp(dt, 0.0, 0.1);
  s.acc += (y > 0 ? 1 : -1) * k * t.scroll_rate * dt;
  int whole = static_cast<int>(s.acc);  // toward zero
  s.acc -= whole;
  return whole;
}

double nudge_px(double screen_h, const Tuning& t) { return t.nudge_px * scale(screen_h); }

const std::vector<Pane>& panes() {
  // Wind UI's windows at its default layout, measured on 1080p stills (out/pad112/p1080/08-a.png: Character
  // 40-1030 x 35-500, Inventory 40-1030 x 535-990, Magic 1078-1878 x 35-675), then ours, System last (owner).
  static const std::vector<Pane> p = {
      {"stats", PaneKind::window, 0.28, 0.25},
      {"inventory", PaneKind::window, 0.28, 0.70},
      {"magic", PaneKind::window, 0.77, 0.33},
      {"journal", PaneKind::journal},
      {"map", PaneKind::map},
      {"system", PaneKind::system},
  };
  return p;
}

int next_pane(int at, int dir) {
  const int n = static_cast<int>(panes().size());
  if (at < 0 || at >= n) return dir >= 0 ? 0 : n - 1;
  return ((at + (dir >= 0 ? 1 : -1)) % n + n) % n;
}

}  // namespace argonia::core::pad
