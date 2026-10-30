// Real input, frame time and the forced crash (0.3 §a; the input path rebuilt by lane input, 2026-10-30).
//   input key <chord> <ms> [os|engine]   a key press held ms (<= 3000). engine: ButtonEvents sent on the
//                            main thread to the game's own input event source, so no window focus or WndProc is on
//                            the path. os: SendInput scan codes after the main window is made foreground; the count
//                            injected and GetLastError come back. With no route named, movement and camera keys go
//                            os (engine events neither move nor turn: game-15) and every other key engine (os E,
//                            ESC, TAB lost: no activation, menus left open). protocol/input.cpp is_movement_key. Calls and schedule: protocol/input.h.
//   focus                    brings the game's main window to the foreground, or says who holds it
//   input-diag               the foreground window, the game's window, the WndProc's module (PrismaUI?), last SendInput
//   frametime [frames]       real frame intervals, measured at the player's per-frame update (a vtable hook by
//                            Address Library id), over the next 10..2000 frames
//   crash yes-really         dereferences null on the main thread: the fail-on-purpose case for crash reporting
#include "bridge.h"
#include "input.h"
#include <cwchar>

namespace argonia::bridge {
namespace {
namespace in = argonia::bridge::input;

std::mutex g_sm;
in::SendResult g_last_send;

// The game's render window: RE::Main's, else the engine's window class (game-14 saw focus on a second window of
// the game's process, which the old pid check passed).
// RE::Main::wnd is not read: on the pinned runtime it gave a code address, not an HWND (game-15), so every focus
// check failed. The window is this process's top-level window of the engine's class.
HWND game_window() {
  struct Find { DWORD pid; HWND found; } f{GetCurrentProcessId(), nullptr};
  EnumWindows(
      [](HWND h, LPARAM p) -> BOOL {
        auto* f = reinterpret_cast<Find*>(p);
        DWORD pid = 0;
        GetWindowThreadProcessId(h, &pid);
        wchar_t cls[64]{};
        if (pid == f->pid && GetClassNameW(h, cls, 64) && std::wcscmp(cls, L"Skyrim Special Edition") == 0) {
          f->found = h;
          return FALSE;
        }
        return TRUE;
      },
      reinterpret_cast<LPARAM>(&f));
  return f.found;
}

in::Window window_info(HWND h) {
  in::Window w;
  w.hwnd = reinterpret_cast<std::uintptr_t>(h);
  if (!h) return w;
  DWORD pid = 0;
  GetWindowThreadProcessId(h, &pid);
  w.pid = pid;
  char buf[256]{};
  GetWindowTextA(h, buf, sizeof buf);
  w.title = buf;
  char cls[256]{};
  GetClassNameA(h, cls, sizeof cls);
  w.cls = cls;
  return w;
}

in::Focus focus_now(in::Window* fg_out = nullptr) {
  HWND fg = GetForegroundWindow();
  auto w = window_info(fg);
  if (fg_out) *fg_out = w;
  return in::classify(w.hwnd, reinterpret_cast<std::uintptr_t>(game_window()), w.pid, GetCurrentProcessId());
}

void alt_tap() {  // a foreground change is allowed to the process that sent the last input event
  INPUT a[2]{};
  a[0].type = a[1].type = INPUT_KEYBOARD;
  a[0].ki.wVk = a[1].ki.wVk = VK_MENU;
  a[1].ki.dwFlags = KEYEVENTF_KEYUP;
  SendInput(2, a, sizeof(INPUT));
}

// AttachThreadInput + BringWindowToTop + SetForegroundWindow, then an ALT tap and again; re-checked after each.
bool bring_to_front() {
  HWND game = game_window();
  if (!game) return false;
  for (int attempt = 0; attempt < 2; ++attempt) {
    if (focus_now() == in::Focus::game) return true;
    if (attempt == 1) alt_tap();
    HWND fg = GetForegroundWindow();
    DWORD fg_thread = fg ? GetWindowThreadProcessId(fg, nullptr) : 0;
    DWORD me = GetCurrentThreadId();
    bool attached = fg_thread && fg_thread != me && AttachThreadInput(me, fg_thread, TRUE);
    if (IsIconic(game)) ShowWindow(game, SW_RESTORE);
    BringWindowToTop(game);
    SetForegroundWindow(game);
    SetFocus(game);
    if (attached) AttachThreadInput(me, fg_thread, FALSE);
    std::this_thread::sleep_for(50ms);
  }
  return focus_now() == in::Focus::game;
}

std::string not_focused(const char* cmd) {
  in::Window fg;
  auto f = focus_now(&fg);
  return reply_error(cmd, "the game's main window is not foreground after activation: " +
                              in::focus_json(f, fg, reinterpret_cast<std::uintptr_t>(game_window())));
}

in::SendResult send_keys(const std::vector<std::uint16_t>& codes, bool up) {
  std::vector<INPUT> v(codes.size());
  for (std::size_t i = 0; i < codes.size(); ++i) {
    v[i].type = INPUT_KEYBOARD;
    v[i].ki.wScan = codes[i];
    v[i].ki.dwFlags = KEYEVENTF_SCANCODE | (up ? KEYEVENTF_KEYUP : 0);
  }
  SetLastError(0);
  in::SendResult r{true, SendInput(static_cast<UINT>(v.size()), v.data(), sizeof(INPUT)), static_cast<std::uint32_t>(v.size()), 0};
  r.last_error = GetLastError();
  std::scoped_lock l(g_sm);
  g_last_send = r;
  return r;
}

// One engine ButtonEvent per key, on the main thread, sent to every sink of the input event source (MenuControls,
// PlayerControls, ...) with the user event the ControlMap maps the key to in the top input context.
void engine_event(std::vector<std::uint16_t> codes, float value, float held) {
  SKSE::GetTaskInterface()->AddTask([codes = std::move(codes), value, held] {
    auto* mgr = RE::BSInputDeviceManager::GetSingleton();
    auto* map = RE::ControlMap::GetSingleton();
    if (!mgr || !map) return;
    auto ctx = RE::UserEvents::INPUT_CONTEXT_ID::kGameplay;
    if (auto& stack = map->GetRuntimeData().contextPriorityStack; !stack.empty()) ctx = stack.back();
    for (auto code : codes) {
      // Codes from 0x100 are mouse buttons (protocol scancode MOUSE1/MOUSE2): the mouse device, button code - 0x100.
      auto dev = code >= 0x100 ? RE::INPUT_DEVICE::kMouse : RE::INPUT_DEVICE::kKeyboard;
      std::uint32_t id = code >= 0x100 ? code - 0x100 : code;
      auto name = map->GetUserEventName(id, dev, ctx);
      if (name.empty()) name = map->GetUserEventName(id, dev);
      auto* ev = RE::ButtonEvent::Create(dev, RE::BSFixedString(name), id, value, held);
      if (!ev) continue;
      RE::InputEvent* head = ev;
      mgr->SendEvent(&head);
      ev->SetUserEvent(RE::BSFixedString());
      RE::free(ev);
    }
  });
}

std::string input_key(const Request& req) {
  auto parsed = in::key_call(req);
  if (auto* e = std::get_if<std::string>(&parsed)) return reply_error("input", *e);
  auto c = std::get<in::KeyCall>(parsed);
  auto t0 = std::chrono::steady_clock::now();
  if (c.route == in::Route::engine) {
    if (save_loading() || !RE::BSInputDeviceManager::GetSingleton())
      return reply_error("input", "the game is loading: the engine input queue is not running");
    for (const auto& tick : in::press_ticks(c.ms)) {
      std::this_thread::sleep_until(t0 + std::chrono::milliseconds(tick.at_ms));
      engine_event(c.codes, tick.value, tick.held_s);
    }
    auto held = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - t0).count();
    return reply_ok("input", JsonObject().str("keys", c.names).str("route", "engine").integer("held_ms", held).done());
  }
  if (!bring_to_front()) return not_focused("input");
  auto down = send_keys(c.codes, false);
  std::this_thread::sleep_for(std::chrono::milliseconds(c.ms));
  auto up = send_keys(c.codes, true);
  auto held = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - t0).count();
  auto body = JsonObject()
                  .str("keys", c.names)
                  .str("route", "os")
                  .integer("held_ms", held)
                  .raw("down", in::send_json(down))
                  .raw("up", in::send_json(up))
                  .done();
  if (down.sent != down.wanted || up.sent != up.wanted)
    return reply_error("input", "SendInput injected fewer events than sent (blocked by UIPI or a desktop switch?): " + body);
  return reply_ok("input", body);
}

std::string focus(const Request&) {
  if (!bring_to_front()) return not_focused("focus");
  in::Window fg;
  auto f = focus_now(&fg);
  return reply_ok("focus", in::focus_json(f, fg, reinterpret_cast<std::uintptr_t>(game_window())));
}

std::string input_diag(const Request&) {
  in::Window fg;
  auto f = focus_now(&fg);
  HWND game = game_window();
  std::string module;
  if (game) {
    auto proc = GetWindowLongPtrW(game, GWLP_WNDPROC);
    HMODULE mod = nullptr;
    if (proc && GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                                   reinterpret_cast<LPCWSTR>(proc), &mod)) {
      char path[MAX_PATH]{};
      GetModuleFileNameA(mod, path, MAX_PATH);
      module = path;
    }
  }
  in::SendResult last;
  {
    std::scoped_lock l(g_sm);
    last = g_last_send;
  }
  auto gw = window_info(game);
  return reply_ok("input-diag", JsonObject()
                                    .raw("focus", in::focus_json(f, fg, gw.hwnd))
                                    .str("game_title", gw.title)
                                    .str("game_class", gw.cls)
                                    .str("wndproc_module", module)
                                    .boolean("prisma_wndproc", in::is_prisma(module))
                                    .boolean("prisma_loaded", GetModuleHandleW(L"PrismaUI.dll") != nullptr)
                                    .boolean("loading", save_loading())
                                    .raw("last_sendinput", in::send_json(last))
                                    .done());
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

const Register r_input{"input", &input_key};
const Register r_focus{"focus", &focus};
const Register r_input_diag{"input-diag", &input_diag};
const Register r_frametime{"frametime", &frametime};
const Register r_crash{"crash", &crash};

}  // namespace

void input_install() {
  REL::Relocation<std::uintptr_t> vtbl{RE::VTABLE_PlayerCharacter[0]};
  PlayerUpdate::func = vtbl.write_vfunc(0xAD, PlayerUpdate::thunk);
}

}  // namespace argonia::bridge
