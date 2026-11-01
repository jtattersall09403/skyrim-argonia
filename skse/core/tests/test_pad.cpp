// L2: the pad rules (1.12 §8): which button does what where, the stick-to-cursor curve, the scroll, the panes.
#include "check.h"
#include "argonia/core/pad.h"

#include <cmath>

using namespace argonia::core::pad;

int main() {
  // Contexts: only Wind UI's menu mode is the cursor's; play, a focused view and other menus are left alone.
  CHECK(on_button(Context::windows, Button::A) == Act::click_left);
  CHECK(on_button(Context::windows, Button::X) == Act::click_right);
  CHECK(on_button(Context::windows, Button::B) == Act::close);
  CHECK(on_button(Context::windows, Button::Start) == Act::close);  // owner: B or Start closes
  CHECK(on_button(Context::windows, Button::RB) == Act::next_pane);
  CHECK(on_button(Context::windows, Button::LB) == Act::prev_pane);
  CHECK(on_button(Context::windows, Button::LT) == Act::wheel_up);
  CHECK(on_button(Context::windows, Button::RT) == Act::wheel_down);
  CHECK(on_button(Context::windows, Button::Down) == Act::nudge_down);
  CHECK(on_button(Context::windows, Button::Back) == Act::wait_rest);  // owner: Select is wait/rest
  CHECK(on_button(Context::windows, Button::Y) == Act::none);
  for (auto c : {Context::play, Context::view, Context::other_menu})
    for (auto b : {Button::A, Button::B, Button::Start, Button::RB, Button::LT, Button::Back, Button::Up})
      CHECK(on_button(c, b) == Act::none);

  CHECK(tween_to_windows(true, false));   // Skyrim's tween alone: Wind UI's windows instead
  CHECK(!tween_to_windows(true, true));   // Wind UI took it
  CHECK(!tween_to_windows(false, false)); // closed already
  CHECK(!tween_to_windows(false, true));

  CHECK(!close_allowed(0.1));  // the opening Start's echo
  CHECK(close_allowed(0.5));
  CHECK(close_allowed(30));

  Button b{};
  CHECK(button_from_name("START", b) && b == Button::Start);
  CHECK(button_from_name("RT", b) && b == Button::RT);
  CHECK(!button_from_name("Z", b));
  CHECK(button_from_code(0x1000, b) && b == Button::A);
  CHECK(button_from_code(0x0200, b) && b == Button::RB);
  CHECK(button_from_code(0x000A, b) && b == Button::RT);
  CHECK(!button_from_code(0x0003, b));

  // The curve: dead inside the deadzone, full speed at the rim, slower than linear between; stick up is screen up.
  Tuning t;
  auto v = cursor_velocity({0.1, 0.1}, 1080, t);
  CHECK(v.x == 0 && v.y == 0);
  v = cursor_velocity({1, 0}, 1080, t);
  CHECK_NEAR(v.x, 1500, 1e-9);
  CHECK_NEAR(v.y, 0, 1e-9);
  v = cursor_velocity({0, 1}, 1080, t);
  CHECK(v.y < -1499);
  v = cursor_velocity({0, 1}, 2160, t);  // a 4K screen moves twice the pixels in the same time
  CHECK_NEAR(v.y, -3000, 1e-6);
  auto half = cursor_velocity({0.59, 0}, 1080, t);  // half the throw past the deadzone
  CHECK(half.x > 0 && half.x < 0.3 * 1500);
  auto diag = cursor_velocity({0.7071, 0.7071}, 1080, t);  // radial: a diagonal is as fast as a straight push
  CHECK_NEAR(std::hypot(diag.x, diag.y), 1500, 1.0);
  auto over = cursor_velocity({1, 1}, 1080, t);  // the square gate's corner is held at full speed
  CHECK_NEAR(std::hypot(over.x, over.y), 1500, 1e-6);

  // The step: integrated, clamped to the screen, a hitch capped at 0.1 s.
  auto p = cursor_step({960, 540}, {1, 0}, 0.016, 1920, 1080, t);
  CHECK_NEAR(p.x, 960 + 24, 1e-9);
  p = cursor_step({1900, 10}, {1, 1}, 0.1, 1920, 1080, t);
  CHECK(p.x == 1919 && p.y == 0);
  p = cursor_step({960, 540}, {1, 0}, 5.0, 1920, 1080, t);
  CHECK_NEAR(p.x, 960 + 150, 1e-9);
  p = cursor_step({960, 540}, {1, 0}, -1, 1920, 1080, t);
  CHECK(p.x == 960);

  // Scroll: 12 notches/s at full, the remainder kept, cleared in the deadzone; sign follows the stick.
  Scroll s;
  int total = 0;
  for (int i = 0; i < 60; ++i) total += scroll_step(s, 1.0, 1.0 / 60, t);
  CHECK(total == 12 || total == 11);  // floating sum of 60 sixtieths
  s = {};
  total = 0;
  for (int i = 0; i < 30; ++i) total += scroll_step(s, -1.0, 1.0 / 60, t);
  CHECK(total == -6 || total == -5);
  scroll_step(s, 0.05, 0.016, t);
  CHECK(s.acc == 0);

  CHECK_NEAR(nudge_px(1080, t), 24, 1e-12);
  CHECK_NEAR(nudge_px(2160, t), 48, 1e-12);

  // Panes: System last (owner), journal and map ours, wrapping both ways.
  const auto& ps = panes();
  CHECK(ps.size() >= 4);
  CHECK(ps.back().kind == PaneKind::system);
  int journal = -1, map = -1;
  for (int i = 0; i < static_cast<int>(ps.size()); ++i) {
    if (ps[i].kind == PaneKind::journal) journal = i;
    if (ps[i].kind == PaneKind::map) map = i;
    if (ps[i].kind == PaneKind::window) CHECK(ps[i].fx > 0 && ps[i].fx < 1 && ps[i].fy > 0 && ps[i].fy < 1);
  }
  CHECK(journal >= 0 && map >= 0);
  const int n = static_cast<int>(ps.size());
  CHECK(next_pane(-1, 1) == 0);
  CHECK(next_pane(-1, -1) == n - 1);
  CHECK(next_pane(n - 1, 1) == 0);
  CHECK(next_pane(0, -1) == n - 1);
  CHECK(next_pane(1, 1) == 2);
  return TEST_MAIN_RESULT("core.pad");
}
