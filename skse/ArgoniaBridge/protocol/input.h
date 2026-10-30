// The bridge's real input (lane input, 2026-10-30): the parts that are pure C++, unit-tested on the build VM. The
// handlers live in src/ep_input.cpp (DEV ONLY).
//   input key <chord> <ms> [engine|os]
//     engine (default): ButtonEvents dispatched on the main thread straight to the game's input event source
//            (BSInputDeviceManager), with the user event the ControlMap gives the key in the current context: no window,
//            focus or WndProc on the path, so a dead window-message path (PrismaUI's subclass, a lost focus) cannot eat it.
//     os:    SendInput scan codes, after the game's main window is brought to the foreground; SendInput's count and
//            GetLastError come back in the reply.
//   focus       brings the game's main window to the foreground (bridge.py runs it before every pad sequence)
//   input-diag  the foreground window, the game's window, the WndProc's owning module, the last SendInput
#pragma once
#include "bridge_protocol.h"

#include <cstdint>
#include <string>
#include <variant>
#include <vector>

namespace argonia::bridge::input {

enum class Route { engine, os };

struct KeyCall {
  std::vector<std::uint16_t> codes;
  std::string names;
  int ms = 0;
  Route route = Route::os;  // the default is per key: is_movement_key (input.cpp)
};
std::variant<KeyCall, std::string> key_call(const Request& r);  // the call, or the refusal in words

// One engine ButtonEvent of a press: at `at_ms` after the press began, value 1 (down or held) or 0 (up), and the
// seconds held so far (0 on the down event, as the engine's own devices send it; > 0 on held and up events).
struct Tick {
  int at_ms = 0;
  float value = 0;
  float held_s = 0;
};
// A press held `ms`: the down at 0, a held event every `frame_ms` (the engine re-sends held keys each frame, and
// movement reads them), the up at `ms`.
// The keys the player moves or looks with (W A S D, F, SPACE, LALT, LSHIFT, LCTRL, C): os by default.
bool is_movement_key(std::uint16_t code);

std::vector<Tick> press_ticks(int ms, int frame_ms = 16);

// Who holds the foreground, from the window handles and process ids.
enum class Focus { game, game_other_window, other_process, none };
Focus classify(std::uintptr_t fg, std::uintptr_t game_wnd, std::uint32_t fg_pid, std::uint32_t game_pid);
const char* focus_name(Focus f);

struct Window {
  std::uintptr_t hwnd = 0;
  std::uint32_t pid = 0;
  std::string title, cls;
};
struct SendResult {
  bool tried = false;
  std::uint32_t sent = 0, wanted = 0, last_error = 0;
};
// {"focus":"other_process","foreground":{"hwnd":..,"pid":..,"title":..,"class":..},"game_hwnd":..}
std::string focus_json(Focus f, const Window& fg, std::uintptr_t game_wnd);
std::string send_json(const SendResult& s);  // {"sent":n,"wanted":n,"last_error":n} or null when never tried
// The WndProc's module tells whether something subclassed the game's window (PrismaUI says it does at launch).
bool is_prisma(std::string_view module_path);

}  // namespace argonia::bridge::input
