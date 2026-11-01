// The pad on every menu (1.12 §8, owner's "Input on every device"): Wind UI (an ImGui DLL with no pad navigation)
// is driven by a cursor the pad moves, and our PrismaUI views keep their own focus navigation (ui/views/core/nav.ts).
// These are the rules: which button does what in which context, the stick-to-cursor curve, the right stick's scroll,
// the d-pad's nudge and the pane cycle. ArgoniaCore's padcursor.cpp reads the pad and acts on the verdicts.
#pragma once

#include <cstdint>
#include <string_view>
#include <vector>

namespace argonia::core::pad {

// Where the player is, as the pad sees it.
enum class Context {
  play,       // no menu: Skyrim's controlmap acts (controlmap.py's DS1 layout)
  windows,    // Wind UI's menu mode (WindUIMenu open), no PrismaUI view focused: the pad cursor acts
  view,       // a PrismaUI view (journal, chart, dialogue) holds focus: nav.ts acts, the cursor yields
  other_menu  // any other menu (message box, book, lockpicking, sleep/wait): Skyrim acts
};

enum class Button { A, B, X, Y, LB, RB, LS, RS, Start, Back, Up, Down, Left, Right, LT, RT };

enum class Act {
  none,          // the pad cursor does nothing: the event is someone else's
  close,         // close Wind UI's menu mode, back to play
  click_left,    // a left mouse click at the cursor
  click_right,   // a right mouse click at the cursor
  next_pane,     // the cursor to the next pane (bumper right)
  prev_pane,     // the cursor to the previous pane (bumper left)
  wheel_up,      // one wheel notch up (the left trigger: zoom out / scroll up)
  wheel_down,    // one wheel notch down (the right trigger: zoom in / scroll down)
  nudge_up,      // the d-pad: the cursor one step
  nudge_down,
  nudge_left,
  nudge_right,
  wait_rest      // Select: close the windows, then Skyrim's wait (T)
};

// The verdict for one button going down. Only `windows` gives anything but none: in play Start already opens Wind UI
// (Tween Menu -> its menu mode) and Select is bound to Wait by controlmap.py; a view and other menus keep their own.
Act on_button(Context c, Button b);

// Wind UI takes InventoryMenu reliably but not TweenMenu early in a session: a frame after TweenMenu opens, if it is
// still open and Wind UI's menu mode is not, the tween is closed and InventoryMenu opened (its full menu mode).
bool tween_to_windows(bool tween_open, bool windui_open);

// The Start that opened the windows (through the tween swap) can reach them once they are open, a frame later, as a
// close (pad112g: opened and shut in 0.6 s). A close this soon after the windows opened is that press: ignored.
inline constexpr double kCloseGuardS = 0.5;
bool close_allowed(double seconds_since_open);

// Button name from the Xbox name used by the bridge's pad (A B X Y LB RB LS RS START BACK UP DOWN LEFT RIGHT LT RT).
bool button_from_name(std::string_view name, Button& out);
// Skyrim's gamepad id code (BSWin32GamepadDevice::Key) to a button; false for an unknown code.
bool button_from_code(std::uint32_t code, Button& out);

struct Tuning {
  double deadzone = 0.18;        // stick radius under which nothing moves (the X2s rests near 0.05)
  double max_speed = 1500.0;     // cursor px/s at full deflection on a 1080-line screen (scaled by the screen height)
  double exponent = 2.2;         // the response curve: fine near the centre, fast at the rim
  double scroll_rate = 12.0;     // wheel notches/s at full right-stick deflection
  double nudge_px = 24.0;        // a d-pad step on a 1080-line screen
  double trigger_on = 0.5;       // a trigger past this is pressed
};

struct Vec {
  double x = 0, y = 0;
};

// Cursor velocity in px/s for a stick reading (each axis -1..1, y up as the pad reports it; screen y grows down).
// Radial deadzone, then the power curve over the rest of the throw, scaled to the screen height.
Vec cursor_velocity(Vec stick, double screen_h, const Tuning& t = {});

// The cursor after dt seconds of a stick reading, kept on the screen.
Vec cursor_step(Vec at, Vec stick, double dt, double screen_w, double screen_h, const Tuning& t = {});

// The right stick's scroll: notches accrue at scroll_rate * curve(y); whole notches come out (+ up, - down), the
// remainder is kept. A stick in the deadzone clears the remainder.
struct Scroll {
  double acc = 0;
};
int scroll_step(Scroll& s, double stick_y, double dt, const Tuning& t = {});

// The d-pad's step in px on this screen.
double nudge_px(double screen_h, const Tuning& t = {});

// The panes the bumpers cycle, in order (owner: System last). Wind UI's windows are cursor anchors (fractions of the
// screen at its default layout); journal and map open our views; system opens Skyrim's System page.
enum class PaneKind { window, journal, map, system };
struct Pane {
  std::string_view name;
  PaneKind kind = PaneKind::window;
  double fx = 0.5, fy = 0.5;  // where the cursor lands, as a fraction of the screen (windows only)
};
const std::vector<Pane>& panes();

// The next pane index from `at` in direction +1 / -1, wrapping. An `at` of -1 (none yet) gives the first (or last).
int next_pane(int at, int dir);

}  // namespace argonia::core::pad
