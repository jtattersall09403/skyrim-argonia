#include "input.h"

#include <algorithm>
#include <cctype>

namespace argonia::bridge::input {

std::variant<KeyCall, std::string> key_call(const Request& r) {
  const auto& a = r.args;
  if ((a.size() != 3 && a.size() != 4) || a[0] != "key")
    return "usage: input key <KEY[+KEY...]> <ms> [engine|os] (the pad goes through tools/bridge.py)";
  KeyCall c;
  auto keys = chord(a[1]);
  if (!keys) return "unknown key in " + a[1];
  c.codes = *keys;
  c.names = a[1];
  auto ms = to_number(a[2]);
  if (!ms || *ms < 1 || *ms > kInputCapMs || *ms != static_cast<int>(*ms))
    return "the hold must be a whole 1..3000 ms (inputs are capped at 3 s)";
  c.ms = static_cast<int>(*ms);
  if (a.size() == 4) {
    if (a[3] == "engine") c.route = Route::engine;
    else if (a[3] == "os") c.route = Route::os;
    else return "the route is engine or os, not " + a[3];
  }
  return c;
}

std::vector<Tick> press_ticks(int ms, int frame_ms) {
  std::vector<Tick> t;
  if (ms < 1 || frame_ms < 1) return t;
  t.push_back({0, 1.0f, 0.0f});
  for (int at = frame_ms; at < ms; at += frame_ms) t.push_back({at, 1.0f, at / 1000.0f});
  t.push_back({ms, 0.0f, ms / 1000.0f});
  return t;
}

Focus classify(std::uintptr_t fg, std::uintptr_t game_wnd, std::uint32_t fg_pid, std::uint32_t game_pid) {
  if (!fg) return Focus::none;
  if (game_wnd && fg == game_wnd) return Focus::game;
  if (fg_pid == game_pid) return Focus::game_other_window;
  return Focus::other_process;
}

const char* focus_name(Focus f) {
  switch (f) {
    case Focus::game: return "game";
    case Focus::game_other_window: return "game_other_window";
    case Focus::other_process: return "other_process";
    default: return "none";
  }
}

std::string focus_json(Focus f, const Window& fg, std::uintptr_t game_wnd) {
  auto w = JsonObject()
               .integer("hwnd", static_cast<long long>(fg.hwnd))
               .integer("pid", fg.pid)
               .str("title", fg.title)
               .str("class", fg.cls)
               .done();
  return JsonObject().str("focus", focus_name(f)).raw("foreground", w).integer("game_hwnd", static_cast<long long>(game_wnd)).done();
}

std::string send_json(const SendResult& s) {
  if (!s.tried) return "null";
  return JsonObject().integer("sent", s.sent).integer("wanted", s.wanted).integer("last_error", s.last_error).done();
}

bool is_prisma(std::string_view path) {
  std::string low(path);
  std::transform(low.begin(), low.end(), low.begin(), [](unsigned char ch) { return static_cast<char>(std::tolower(ch)); });
  return low.find("prismaui") != std::string::npos;
}

}  // namespace argonia::bridge::input
