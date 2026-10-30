// L2: the bridge's input calls, press schedule and focus report (lane input, 2026-10-30).
#include "check.h"
#include "input.h"

using namespace argonia::bridge;
using namespace argonia::bridge::input;

namespace {
const std::string kTok = "0123456789abcdef0123456789abcdef";
Request req(const std::string& line) { return std::get<Request>(parse(kTok + " " + line, kTok)); }

void key_calls() {
  auto v = key_call(req("input key F 150"));
  auto* k = std::get_if<KeyCall>(&v);
  CHECK(k && k->route == Route::os && k->ms == 150 && k->codes.size() == 1 && k->codes[0] == 0x21);
  v = key_call(req("input key E 120"));  // activation and menu keys default to the engine route
  k = std::get_if<KeyCall>(&v);
  CHECK(k && k->route == Route::engine);
  v = key_call(req("input key TAB+W 120"));  // any movement key in the chord: os
  k = std::get_if<KeyCall>(&v);
  CHECK(k && k->route == Route::os);
  v = key_call(req("input key MOUSE1 120"));  // a mouse button: engine only
  k = std::get_if<KeyCall>(&v);
  CHECK(k && k->route == Route::engine && k->codes[0] == 0x100);
  CHECK(std::holds_alternative<std::string>(key_call(req("input key MOUSE1 120 os"))));
  v = key_call(req("input key E 120 os"));
  k = std::get_if<KeyCall>(&v);
  CHECK(k && k->route == Route::os);
  v = key_call(req("input key LSHIFT+W 800 os"));
  k = std::get_if<KeyCall>(&v);
  CHECK(k && k->route == Route::os && k->codes.size() == 2);
  CHECK(std::holds_alternative<std::string>(key_call(req("input key F 150 window"))));
  CHECK(std::holds_alternative<std::string>(key_call(req("input key F 3001"))));
  CHECK(std::holds_alternative<std::string>(key_call(req("input key F 0"))));
  CHECK(std::holds_alternative<std::string>(key_call(req("input key F 1.5"))));
  CHECK(std::holds_alternative<std::string>(key_call(req("input key NOPE 100"))));
  CHECK(std::holds_alternative<std::string>(key_call(req("input pad A 100"))));
  CHECK(std::holds_alternative<std::string>(key_call(req("input key F"))));
}

void ticks() {
  auto t = press_ticks(50, 16);
  CHECK(t.size() == 5);  // down 0, held 16 32 48, up 50
  CHECK(t.front().at_ms == 0 && t.front().value == 1.0f && t.front().held_s == 0.0f);
  CHECK(t[1].held_s > 0.0f && t[1].value == 1.0f);
  CHECK(t.back().at_ms == 50 && t.back().value == 0.0f && t.back().held_s == 0.05f);
  CHECK(press_ticks(1).size() == 2);  // a tap: down then up
  CHECK(press_ticks(0).empty());
}

void focus() {
  CHECK(classify(0, 5, 0, 7) == Focus::none);
  CHECK(classify(5, 5, 7, 7) == Focus::game);
  CHECK(classify(9, 5, 7, 7) == Focus::game_other_window);  // game-14: a second window of the game's process
  CHECK(classify(9, 5, 3, 7) == Focus::other_process);
  CHECK(classify(9, 0, 7, 7) == Focus::game_other_window);  // no main window known: never "game"
  Window w{3015804, 7, "a \"b\"", "Notepad"};
  CHECK(focus_json(Focus::other_process, w, 328054) ==
        R"({"focus":"other_process","foreground":{"hwnd":3015804,"pid":7,"title":"a \"b\"","class":"Notepad"},"game_hwnd":328054})");
  CHECK(send_json({}) == "null");
  CHECK(send_json({true, 0, 2, 5}) == R"({"sent":0,"wanted":2,"last_error":5})");
  CHECK(is_prisma("C:\\Skyrim\\Data\\SKSE\\Plugins\\PrismaUI.dll"));
  CHECK(!is_prisma("C:\\Skyrim\\SkyrimSE.exe"));
}
}  // namespace

void input_tests() {
  key_calls();
  ticks();
  focus();
}
