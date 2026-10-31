// The pad cursor (1.12 §8): Wind UI's windows (a closed ImGui DLL with no pad navigation; windui.md "In game") are
// driven by the game's own cursor, which the pad moves here. While Wind UI's menu mode is open and no PrismaUI view
// holds focus, the left stick moves the cursor, A and X are the mouse buttons, the right stick and the triggers are the
// wheel, the d-pad nudges, the bumpers cycle the panes (core/pad.h: Wind UI's windows, our journal and map, System
// last), B and Start close and Select waits. Our views keep their own focus navigation (ui/views/core/nav.ts): the
// cursor yields while one is focused. The rules are core/pad.h's (unit-tested); this file only reads and sends events.
//
// The cursor is moved the way a real mouse moves it: a MouseMoveEvent of the difference through the game's input
// event source, and the MenuCursor's position written (Wind UI reads the game's cursor, not the OS's: an OS
// SetCursorPos did not move it). Clicks and wheel notches are mouse ButtonEvents by the same route.
#include "core.h"
#include "prisma_api.h"
#include "argonia/core/pad.h"

#include <atomic>
#include <chrono>
#include <cstring>
#include <deque>
#include <thread>
#include <utility>

namespace argonia::plugin {

namespace {
namespace pad = argonia::core::pad;

constexpr std::string_view kWindUIMenu = "WindUIMenu";
// Keyboard scan codes sent by the engine route (the user event comes from the ControlMap, as for a real key).
constexpr std::uint32_t kTab = 0x0F, kEsc = 0x01, kJ = 0x24, kM = 0x32, kT = 0x14;

prisma::Api1* g_prisma = nullptr;

// Main thread only (the input sink and the tick both run there).
struct State {
  pad::Vec left, right;      // the sticks, as the pad last reported them
  pad::Scroll scroll;
  int pane = -1;             // the last pane the bumpers chose
  bool held_left = false, held_right = false;  // a mouse button the pad holds down (A, X)
  bool release_left = false, release_right = false;  // A or X let go since the last tick
  std::deque<pad::Act> acts;  // button verdicts, acted on at the next tick
  enum class After { none, wait, system } after = After::none;  // once the windows have closed
  int close_ticks = 0;        // ticks since a close was asked (a native close may already have done it)
  std::chrono::steady_clock::time_point last;
  bool was_windows = false;
} g;

std::atomic<bool> g_loop{false};

void Send(RE::InputEvent* ev) {
  auto* mgr = RE::BSInputDeviceManager::GetSingleton();
  if (!mgr || !ev) return;
  RE::InputEvent* head = ev;
  mgr->SendEvent(&head);
}

void Button(RE::INPUT_DEVICE dev, std::uint32_t id, float value, float held) {
  auto* map = RE::ControlMap::GetSingleton();
  if (!map) return;
  auto ctx = RE::UserEvents::INPUT_CONTEXT_ID::kGameplay;
  if (auto& stack = map->GetRuntimeData().contextPriorityStack; !stack.empty()) ctx = stack.back();
  auto name = map->GetUserEventName(id, dev, ctx);
  if (name.empty()) name = map->GetUserEventName(id, dev);
  auto* ev = RE::ButtonEvent::Create(dev, RE::BSFixedString(name), id, value, held);
  if (!ev) return;
  Send(ev);
  ev->SetUserEvent(RE::BSFixedString());
  RE::free(ev);
}

void Tap(RE::INPUT_DEVICE dev, std::uint32_t id) {
  Button(dev, id, 1.0f, 0.0f);
  Button(dev, id, 0.0f, 0.05f);
}

void MouseMove(std::int32_t dx, std::int32_t dy) {
  if (!dx && !dy) return;
  auto* ev = static_cast<RE::MouseMoveEvent*>(RE::malloc(sizeof(RE::MouseMoveEvent)));
  if (!ev) return;
  std::memset(static_cast<void*>(ev), 0, sizeof(RE::MouseMoveEvent));
  REL::Relocation<std::uintptr_t> vt{RE::VTABLE_MouseMoveEvent[0]};
  *reinterpret_cast<std::uintptr_t*>(ev) = vt.address();
  ev->device = RE::INPUT_DEVICE::kMouse;
  ev->eventType = RE::INPUT_EVENT_TYPE::kMouseMove;
  ev->idCode = 0x0A;
  ev->mouseInputX = dx;
  ev->mouseInputY = dy;
  ev->userEvent = RE::BSFixedString(RE::UserEvents::GetSingleton()->look);
  Send(ev);
  ev->userEvent = RE::BSFixedString();
  RE::free(ev);
}

struct Screen {
  double w = 1920, h = 1080;
};
Screen ScreenSize() {
  Screen s;
  if (auto* c = RE::MenuCursor::GetSingleton()) {
    auto& d = c->GetRuntimeData();
    if (d.screenWidthX > 0 && d.screenWidthY > 0) s = {d.screenWidthX, d.screenWidthY};
  }
  return s;
}

void CursorTo(pad::Vec to) {
  auto* c = RE::MenuCursor::GetSingleton();
  if (!c) return;
  auto& d = c->GetRuntimeData();
  const auto dx = static_cast<std::int32_t>(std::lround(to.x - d.cursorPosX));
  const auto dy = static_cast<std::int32_t>(std::lround(to.y - d.cursorPosY));
  MouseMove(dx, dy);
  d.cursorPosX = static_cast<float>(to.x);
  d.cursorPosY = static_cast<float>(to.y);
}

pad::Vec CursorAt() {
  if (auto* c = RE::MenuCursor::GetSingleton()) return {c->GetRuntimeData().cursorPosX, c->GetRuntimeData().cursorPosY};
  return {};
}

bool Open(std::string_view menu) {
  auto* ui = RE::UI::GetSingleton();
  return ui && ui->IsMenuOpen(RE::BSFixedString(menu));
}

pad::Context ContextNow() {
  if (!Open(kWindUIMenu)) return pad::Context::play;  // play or Skyrim's own menus: the controlmap acts
  if (g_prisma && g_prisma->HasAnyActiveFocus()) return pad::Context::view;
  for (auto m : {RE::MessageBoxMenu::MENU_NAME, RE::DialogueMenu::MENU_NAME, RE::BookMenu::MENU_NAME,
                 RE::SleepWaitMenu::MENU_NAME, RE::LockpickingMenu::MENU_NAME, RE::JournalMenu::MENU_NAME})
    if (Open(m)) return pad::Context::other_menu;
  return pad::Context::windows;
}

void MouseButton(bool right, bool down) {
  bool& held = right ? g.held_right : g.held_left;
  if (held == down) return;
  held = down;
  Button(RE::INPUT_DEVICE::kMouse, right ? 1 : 0, down ? 1.0f : 0.0f, down ? 0.0f : 0.1f);
  auto at = CursorAt();
  SKSE::log::info("pad: {} {} at {:.0f},{:.0f}", right ? "right" : "left", down ? "down" : "up", at.x, at.y);
}

void ReleaseButtons() {
  MouseButton(false, false);
  MouseButton(true, false);
}

void AskClose(State::After after) {
  ReleaseButtons();
  g.after = after;
  g.close_ticks = 1;
}

void GoPane(int dir) {
  g.pane = pad::next_pane(g.pane, dir);
  const auto& p = pad::panes()[static_cast<std::size_t>(g.pane)];
  SKSE::log::info("pad: pane {} ({})", p.name, dir > 0 ? "next" : "previous");
  switch (p.kind) {
    case pad::PaneKind::window: {
      auto s = ScreenSize();
      CursorTo({p.fx * s.w, p.fy * s.h});
      break;
    }
    case pad::PaneKind::journal: Tap(RE::INPUT_DEVICE::kKeyboard, kJ); break;  // our journal (the Journal event)
    case pad::PaneKind::map: Tap(RE::INPUT_DEVICE::kKeyboard, kM); break;      // MapMenu, which our chart stands in for
    case pad::PaneKind::system: AskClose(State::After::system); break;         // Skyrim's System page, after the windows
  }
}

void Do(pad::Act a) {
  const auto s = ScreenSize();
  const double step = pad::nudge_px(s.h);
  auto at = CursorAt();
  switch (a) {
    case pad::Act::click_left: MouseButton(false, true); break;
    case pad::Act::click_right: MouseButton(true, true); break;
    case pad::Act::close: AskClose(State::After::none); break;
    case pad::Act::wait_rest: AskClose(State::After::wait); break;
    case pad::Act::next_pane: GoPane(1); break;
    case pad::Act::prev_pane: GoPane(-1); break;
    case pad::Act::wheel_up: Tap(RE::INPUT_DEVICE::kMouse, 8); break;  // BSWin32MouseDevice kWheelUp
    case pad::Act::wheel_down: Tap(RE::INPUT_DEVICE::kMouse, 9); break;
    case pad::Act::nudge_up: CursorTo({at.x, (std::max)(0.0, at.y - step)}); break;
    case pad::Act::nudge_down: CursorTo({at.x, (std::min)(s.h - 1, at.y + step)}); break;
    case pad::Act::nudge_left: CursorTo({(std::max)(0.0, at.x - step), at.y}); break;
    case pad::Act::nudge_right: CursorTo({(std::min)(s.w - 1, at.x + step), at.y}); break;
    case pad::Act::none: break;
  }
}

// One frame's work, on the main thread: the closes in flight, the queued verdicts, the sticks.
void Tick() {
  const auto now = std::chrono::steady_clock::now();
  const double dt = g.last.time_since_epoch().count() ? std::chrono::duration<double>(now - g.last).count() : 0.0;
  g.last = now;
  if (g.close_ticks) {
    // A native close (B is Skyrim's Cancel in a menu) may already have closed the windows: Tab is sent only if they are
    // still open three ticks on, so the toggle never reopens them. Then what was asked after the close.
    if (Open(kWindUIMenu)) {
      if (++g.close_ticks == 4) Tap(RE::INPUT_DEVICE::kKeyboard, kTab);
      if (g.close_ticks > 40) g.close_ticks = 0;  // never closed: give up quietly (the log says so)
      if (!g.close_ticks) SKSE::log::warn("pad: the windows did not close");
      return;
    }
    g.close_ticks = 0;
    SKSE::log::info("pad: windows closed");
    if (g.after == State::After::wait) Tap(RE::INPUT_DEVICE::kKeyboard, kT);
    if (g.after == State::After::system) Tap(RE::INPUT_DEVICE::kKeyboard, kEsc);
    g.after = State::After::none;
    g.acts.clear();
    return;
  }
  const auto ctx = ContextNow();
  if (ctx != pad::Context::windows) {
    if (g.was_windows) ReleaseButtons();
    g.was_windows = false;
    g.acts.clear();
    return;
  }
  if (!g.was_windows) SKSE::log::info("pad: windows open, the pad drives the cursor");
  g.was_windows = true;
  while (!g.acts.empty()) {  // events are sent here, never inside the input sink's own dispatch
    auto a = g.acts.front();
    g.acts.pop_front();
    Do(a);
    if (g.close_ticks) return;
  }
  if (std::exchange(g.release_left, false)) MouseButton(false, false);
  if (std::exchange(g.release_right, false)) MouseButton(true, false);
  const auto s = ScreenSize();
  const auto at = CursorAt();
  const auto to = pad::cursor_step(at, g.left, dt, s.w, s.h);
  if (std::lround(to.x) != std::lround(at.x) || std::lround(to.y) != std::lround(at.y)) CursorTo(to);
  for (int n = pad::scroll_step(g.scroll, g.right.y, dt); n != 0; n += n > 0 ? -1 : 1)
    Tap(RE::INPUT_DEVICE::kMouse, n > 0 ? 8 : 9);
}

class PadSink : public RE::BSTEventSink<RE::InputEvent*> {
 public:
  RE::BSEventNotifyControl ProcessEvent(RE::InputEvent* const* evs, RE::BSTEventSource<RE::InputEvent*>*) override {
    if (!evs) return RE::BSEventNotifyControl::kContinue;
    const auto ctx = ContextNow();
    for (auto* e = *evs; e; e = e->next) {
      if (e->GetDevice() != RE::INPUT_DEVICE::kGamepad) continue;
      if (auto* t = e->AsThumbstickEvent()) {
        pad::Vec v{t->xValue, t->yValue};
        if (t->IsLeft()) g.left = v;
        else g.right = v;
        continue;
      }
      auto* b = e->AsButtonEvent();
      if (!b) continue;
      pad::Button which{};
      if (!pad::button_from_code(b->GetIDCode(), which)) continue;
      if (b->IsUp()) {  // A and X let go: the mouse button too, at the next tick (a held A drags a window)
        if (which == pad::Button::A) g.release_left = true;
        if (which == pad::Button::X) g.release_right = true;
        continue;
      }
      if (!b->IsDown()) continue;
      if (auto a = pad::on_button(ctx, which); a != pad::Act::none) g.acts.push_back(a);
    }
    if (ctx == pad::Context::windows) Run();
    return RE::BSEventNotifyControl::kContinue;
  }

  // The tick loop runs while the windows are open: a thread asks for a main-thread tick each ~16 ms and stops itself
  // once a tick finds the windows closed and nothing in flight.
  static void Run() {
    if (g_loop.exchange(true)) return;
    std::thread([] {
      for (;;) {
        std::this_thread::sleep_for(std::chrono::milliseconds(16));
        std::atomic<bool> done{false}, keep{true};
        SKSE::GetTaskInterface()->AddTask([&done, &keep] {
          Tick();
          keep = g.was_windows || g.close_ticks != 0;
          done = true;
          done.notify_one();
        });
        done.wait(false);
        if (!keep) {
          g.last = {};
          g_loop = false;
          return;
        }
      }
    }).detach();
  }
};

}  // namespace

void PadCursorInstall() {
  if (auto* dll = GetModuleHandleA(prisma::kDll))
    if (auto request = reinterpret_cast<prisma::RequestApi>(GetProcAddress(dll, prisma::kEntry)))
      g_prisma = static_cast<prisma::Api1*>(request(prisma::Version::v1));
  auto* mgr = RE::BSInputDeviceManager::GetSingleton();
  if (!mgr) {
    SKSE::log::error("pad: no input device manager; the pad cursor is off");
    return;
  }
  static PadSink sink;
  mgr->AddEventSink(&sink);
  SKSE::log::info("pad: cursor ready (Wind UI's menu mode; PrismaUI {})", g_prisma ? "bound" : "absent");
}

}  // namespace argonia::plugin
