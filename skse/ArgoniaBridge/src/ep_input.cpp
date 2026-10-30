// Real input, frame time and the forced crash (0.3 §a).
//   input key <chord> <ms>   a real keyboard press: SendInput scan codes from inside the game's own process (the
//                            desktop session), held ms (<= 3000) and released; refused when the game window does not
//                            have focus, since the press would land elsewhere. The gamepad is pad.ps1's virtual pad
//                            (ViGEm, the real XInput path), driven by tools/bridge.py.
//   frametime [frames]       real frame intervals, measured at the player's per-frame update (a vtable hook by
//                            Address Library id), over the next 10..2000 frames
//   crash yes-really         dereferences null on the main thread: the fail-on-purpose case for crash reporting
#include "bridge.h"

namespace argonia::bridge {
namespace {

bool game_has_focus() {
  HWND fg = GetForegroundWindow();
  DWORD pid = 0;
  if (fg) GetWindowThreadProcessId(fg, &pid);
  return pid == GetCurrentProcessId();
}

void send_keys(const std::vector<std::uint16_t>& codes, bool up) {
  std::vector<INPUT> in(codes.size());
  for (std::size_t i = 0; i < codes.size(); ++i) {
    in[i].type = INPUT_KEYBOARD;
    in[i].ki.wScan = codes[i];
    in[i].ki.dwFlags = KEYEVENTF_SCANCODE | (up ? KEYEVENTF_KEYUP : 0);
  }
  SendInput(static_cast<UINT>(in.size()), in.data(), sizeof(INPUT));
}

std::string input(const Request& req) {
  if (req.args.size() != 3 || req.args[0] != "key")
    return reply_error("input", "usage: input key <KEY[+KEY...]> <ms> (the pad goes through tools/bridge.py)");
  auto keys = chord(req.args[1]);
  if (!keys) return reply_error("input", "unknown key in " + req.args[1]);
  auto ms = to_number(req.args[2]);
  if (!ms || *ms < 1 || *ms > kInputCapMs) return reply_error("input", "the hold must be 1..3000 ms (inputs are capped at 3 s)");
  if (!game_has_focus()) return reply_error("input", "the game window does not have focus; a real press would go elsewhere");
  auto t0 = std::chrono::steady_clock::now();
  send_keys(*keys, false);
  std::this_thread::sleep_for(std::chrono::milliseconds(static_cast<long long>(*ms)));
  send_keys(*keys, true);
  auto held = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - t0).count();
  return reply_ok("input", JsonObject().str("keys", req.args[1]).integer("held_ms", held).done());
}

// --- frame time: the player's Update(float delta), vfunc 0xAD, runs once per frame in a world ---------------
std::mutex g_fm;
std::condition_variable g_fcv;
std::vector<double> g_frames;
std::size_t g_want = 0;
std::chrono::steady_clock::time_point g_last;

struct PlayerUpdate {
  static void thunk(RE::PlayerCharacter* p, float delta) {
    func(p, delta);
    trace_frame(p);
    std::scoped_lock l(g_fm);
    if (g_want == 0) return;
    auto now = std::chrono::steady_clock::now();
    if (g_last.time_since_epoch().count() != 0)
      g_frames.push_back(std::chrono::duration<double, std::milli>(now - g_last).count());
    g_last = now;
    if (g_frames.size() >= g_want) {
      g_want = 0;
      g_fcv.notify_all();
    }
  }
  static inline REL::Relocation<decltype(thunk)> func;
};

std::string frametime(const Request& req) {
  double n = 120;
  if (!req.args.empty()) {
    auto v = to_number(req.args[0]);
    if (!v || *v < 10 || *v > 2000) return reply_error("frametime", "frames must be 10..2000");
    n = *v;
  }
  auto in_world = on_main_thread("frametime", [] { return player_in_world() ? "yes"s : "no"s; });
  if (in_world != "yes") return reply_error("frametime", "no player in a world: frames are measured in game");
  std::unique_lock l(g_fm);
  g_frames.clear();
  g_last = {};
  g_want = static_cast<std::size_t>(n);
  if (!g_fcv.wait_for(l, std::chrono::milliseconds(static_cast<long long>(n * 250 + 2000)), [] { return g_want == 0; })) {
    g_want = 0;
    return reply_error("frametime", "only " + std::to_string(g_frames.size()) + " frames arrived (paused or in a menu?)");
  }
  auto s = frame_stats(g_frames);
  return reply_ok("frametime", JsonObject()
                                   .integer("frames", static_cast<long long>(s.frames))
                                   .num("mean_ms", s.mean)
                                   .num("p50_ms", s.p50)
                                   .num("p95_ms", s.p95)
                                   .num("p99_ms", s.p99)
                                   .num("max_ms", s.max)
                                   .num("fps", s.fps)
                                   .done());
}

std::string crash(const Request& req) {
  if (rest(req) != "yes-really") return reply_error("crash", "usage: crash yes-really (kills the game on purpose)");
  SKSE::GetTaskInterface()->AddTask([] {
    volatile int* p = nullptr;
    *p = 1;  // the forced crash: Crash Logger writes its log, bridge.py reports it
  });
  return reply_ok("crash", "{\"queued\":true}");
}

const Register r_input{"input", &input};
const Register r_frametime{"frametime", &frametime};
const Register r_crash{"crash", &crash};

}  // namespace

void input_install() {
  REL::Relocation<std::uintptr_t> vtbl{RE::VTABLE_PlayerCharacter[0]};
  PlayerUpdate::func = vtbl.write_vfunc(0xAD, PlayerUpdate::thunk);
}

}  // namespace argonia::bridge
