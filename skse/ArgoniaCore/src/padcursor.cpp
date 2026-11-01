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
constexpr std::uint32_t kTab = 0x0F, kEsc = 0x01, kJ = 0x24, kM = 0x32, kT = 0x14, kP = 0x19;

prisma::Api1* g_prisma = nullptr;

// Main thread only (the input sink and the tick both run there).
struct State {
  pad::Vec left, right;      // the sticks, as the pad last reported them
  pad::Scroll scroll;
  int pane = -1;             // the last pane the bumpers chose
  bool held_left = false, held_right = false;  // a mouse button the pad holds down (A, X)
  bool release_left = false, release_right = false;  // A or X let go since the last tick
  std::deque<pad::Act> acts;  // button verdicts, acted on at the next tick
  enum class After { none, wait, system, journal, map, magic } after = After::none;  // once the windows have closed
  // A pane of ours (journal, map, System) is opened with Wind UI's windows closed, so nothing is drawn over it; once it
  // has opened and then closed again (B, Esc, its Close), the windows come back. 0 none, 1 waiting for it, 2 it is open.
  int away = 0;
  std::chrono::steady_clock::time_point away_since, away_closed;
  int close_ticks = 0;        // ticks since a close was asked (a native close may already have done it)
  std::chrono::steady_clock::time_point last;
  bool was_windows = false;
  bool taskbar_journal = false;  // a click on Wind UI's taskbar Journal: our paper book instead of its window
  bool esc_close = false;  // the queued close is the keyboard's Esc: no opening guard (that is for the pad's Start)
  std::chrono::steady_clock::time_point opened;  // when the windows last opened
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

// One of our modal views (journal, chart) is open: the view host's own record, not PrismaUI's focus (pad112k: the
// journal opened without focus read as closed, and the windows came back over it).
bool OurViewOpen() {
  auto& c = Get();
  std::lock_guard l(c.lock);
  return c.view_host.modal().has_value();
}

bool MagicPaneOpen() {
  auto& c = Get();
  std::lock_guard l(c.lock);
  return c.view_host.modal() == std::optional<std::string>("magic");
}

pad::Context ContextNow() {
  if (!Open(kWindUIMenu)) return pad::Context::play;  // play or Skyrim's own menus: the controlmap acts
  if ((g_prisma && g_prisma->HasAnyActiveFocus()) || OurViewOpen()) return pad::Context::view;
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
    // ours open only once Wind UI's windows are closed, so they are never drawn over (reader, 2026-11-01)
    case pad::PaneKind::journal: AskClose(State::After::journal); break;  // our journal (the Journal event, J)
    case pad::PaneKind::map: AskClose(State::After::map); break;          // MapMenu, which our chart stands in for (M)
    case pad::PaneKind::magic: AskClose(State::After::magic); break;      // MagicMenu, our magic pane (P)
    case pad::PaneKind::system: AskClose(State::After::system); break;    // Skyrim's System page (Esc)
  }
}

void Do(pad::Act a) {
  const auto s = ScreenSize();
  const double step = pad::nudge_px(s.h);
  auto at = CursorAt();
  switch (a) {
    case pad::Act::click_left: MouseButton(false, true); break;
    case pad::Act::click_right: MouseButton(true, true); break;
    case pad::Act::close:
      if (std::exchange(g.esc_close, false) || pad::close_allowed(std::chrono::duration<double>(std::chrono::steady_clock::now() - g.opened).count()))
        AskClose(State::After::none);
      break;
    case pad::Act::wait_rest: AskClose(State::After::wait); break;
    case pad::Act::next_pane: GoPane(1); break;
    case pad::Act::prev_pane: GoPane(-1); break;
    case pad::Act::wheel_up:  // BSWin32MouseDevice kWheelUp
      Tap(RE::INPUT_DEVICE::kMouse, 8);
      SKSE::log::info("pad: wheel up (trigger)");
      break;
    case pad::Act::wheel_down:
      Tap(RE::INPUT_DEVICE::kMouse, 9);
      SKSE::log::info("pad: wheel down (trigger)");
      break;
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
    // still open three ticks on (Esc is the menus' Cancel, as B; Tab left them open, pad112f). Then what was asked after the close.
    if (Open(kWindUIMenu)) {
      // Wind UI's menu hidden by the UI queue: Tab left it open (pad112f), and Esc there also opened the System page
      // (pad112m), which then hid our journal's opening.
      if (++g.close_ticks == 4)
        if (auto* q = RE::UIMessageQueue::GetSingleton())
          q->AddMessage(RE::BSFixedString(kWindUIMenu), RE::UI_MESSAGE_TYPE::kHide, nullptr);
      if (g.close_ticks > 40) g.close_ticks = 0;  // never closed: give up quietly (the log says so)
      if (!g.close_ticks) SKSE::log::warn("pad: the windows did not close");
      return;
    }
    g.close_ticks = 0;
    SKSE::log::info("pad: windows closed");
    switch (g.after) {
      case State::After::wait: Tap(RE::INPUT_DEVICE::kKeyboard, kT); break;
      case State::After::system: Tap(RE::INPUT_DEVICE::kKeyboard, kEsc); break;
      case State::After::journal: Tap(RE::INPUT_DEVICE::kKeyboard, kJ); break;
      case State::After::map: Tap(RE::INPUT_DEVICE::kKeyboard, kM); break;
      case State::After::magic: Tap(RE::INPUT_DEVICE::kKeyboard, kP); break;
      case State::After::none: break;
    }
    if (g.after == State::After::system || g.after == State::After::journal || g.after == State::After::map ||
        g.after == State::After::magic) {
      g.away = 1;
      g.away_since = now;
    }
    g.after = State::After::none;
    g.acts.clear();
    return;
  }
  if (g.away) {
    const bool ours_open = Open(RE::MapMenu::MENU_NAME) || Open(RE::JournalMenu::MENU_NAME) || OurViewOpen();
    const double s_away = std::chrono::duration<double>(now - g.away_since).count();
    if (g.away == 1 && ours_open) g.away = 2;
    // The Journal Menu hands over to our journal a few frames later (pad112l: the gap read as "closed"): a pane counts
    // as left only once nothing of ours has been open for half a second.
    if (ours_open) g.away_closed = {};
    else if (g.away == 2 && !g.away_closed.time_since_epoch().count()) g.away_closed = now;
    const bool left = g.away == 2 && g.away_closed.time_since_epoch().count() &&
                      std::chrono::duration<double>(now - g.away_closed).count() > 0.5;
    // The player opened them some other way; not the windows Wind UI pops as P's MagicMenu opens under our magic pane
    // (hidden by the MagicMenu watcher below; pad-panes mp7 lost the way back to the windows to them).
    if (Open(kWindUIMenu) && !MagicPaneOpen() && s_away > 1.5) g.away = 0;
    else if (left || (g.away == 1 && s_away > 5.0)) {
      g.away_closed = {};
      g.away = 0;
      if (auto* q = RE::UIMessageQueue::GetSingleton()) q->AddMessage(RE::InventoryMenu::MENU_NAME, RE::UI_MESSAGE_TYPE::kShow, nullptr);
      SKSE::log::info("pad: back to Wind UI's windows");
      return;
    }
  }
  const auto ctx = ContextNow();
  if (ctx != pad::Context::windows) {
    if (g.was_windows) {
      ReleaseButtons();
      SKSE::log::info("pad: windows closed");
    }
    g.was_windows = false;
    g.acts.clear();
    return;
  }
  if (!g.was_windows) {
    g.opened = now;
    SKSE::log::info("pad: windows open, the pad drives the cursor");
  }
  g.was_windows = true;
  if (std::exchange(g.taskbar_journal, false)) {
    AskClose(State::After::journal);
    return;
  }
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
  const int notches = pad::scroll_step(g.scroll, g.right.y, dt);
  for (int n = notches; n != 0; n += n > 0 ? -1 : 1) Tap(RE::INPUT_DEVICE::kMouse, n > 0 ? 8 : 9);
  if (notches) SKSE::log::info("pad: wheel {} {} by the right stick", notches > 0 ? "up" : "down", notches > 0 ? notches : -notches);
}

class PadSink : public RE::BSTEventSink<RE::InputEvent*> {
 public:
  RE::BSEventNotifyControl ProcessEvent(RE::InputEvent* const* evs, RE::BSTEventSource<RE::InputEvent*>*) override {
    if (!evs) return RE::BSEventNotifyControl::kContinue;
    const auto ctx = ContextNow();
    for (auto* e = *evs; e; e = e->next) {
      // Esc in Wind UI's windows closes them back to play (the input map): ImGui does not consume it, so its Pause
      // event would also open the System page (system-perks, 04:57:20). The press is swallowed and we close them.
      if (e->GetDevice() == RE::INPUT_DEVICE::kKeyboard && ctx == pad::Context::windows) {
        auto* kb = e->AsButtonEvent();
        if (kb && (kb->GetIDCode() == kEsc || kb->GetIDCode() == kTab)) {  // Tab left them open (pad112t)
          const_cast<RE::BSFixedString&>(kb->QUserEvent()) = "";
          if (kb->IsDown()) {
            SKSE::log::info("pad: {} in the windows: closed to play", kb->GetIDCode() == kEsc ? "Esc" : "Tab");
            g.acts.push_back(pad::Act::close);
            g.esc_close = true;
          }
        }
        continue;
      }
      // Wind UI's taskbar Journal toggles its own journal window (owner look 1: "not the paper book"; no setting hides
      // it). A left click there (the mouse, the pad's A, a tap) is taken from Wind UI and opens our book, as J does.
      if (e->GetDevice() == RE::INPUT_DEVICE::kMouse && ctx == pad::Context::windows) {
        auto* mb = e->AsButtonEvent();
        if (mb && mb->GetIDCode() == 0 && (mb->IsDown() || mb->IsUp() || mb->IsHeld())) {
          const auto s = ScreenSize();
          const auto at = CursorAt();
          if (pad::on_taskbar_journal(at, s.w, s.h)) {
            if (mb->IsDown()) {
              SKSE::log::info("pad: Wind UI's taskbar Journal at {:.0f},{:.0f}: our journal instead", at.x, at.y);
              g.taskbar_journal = true;
            }
            const_cast<RE::BSFixedString&>(mb->QUserEvent()) = "";
            auto& rd = const_cast<RE::ButtonEvent*>(mb)->GetRuntimeData();
            rd.value = 0.0f;  // neither down nor up: Wind UI never sees the press
            rd.heldDownSecs = 0.0f;
          }
        }
        continue;
      }
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
      if (auto a = pad::on_button(ctx, which); a != pad::Act::none) {
        if (a == pad::Act::close)
          SKSE::log::info("pad: close asked by pad code 0x{:04x} (value {:.2f}, held {:.2f})", b->GetIDCode(), b->Value(), b->HeldDuration());
        g.acts.push_back(a);
      }
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
          keep = g.was_windows || g.close_ticks != 0 || g.away != 0;
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

// The Journal Menu's System page (index 2 of its PageArray: Quests, General stats, System).
void SystemTab() {
  auto* ui = RE::UI::GetSingleton();
  if (!ui || !Open(RE::JournalMenu::MENU_NAME)) return;
  auto menu = ui->GetMenu(RE::JournalMenu::MENU_NAME);
  if (!menu || !menu->uiMovie) return;
  RE::GFxValue args[2];
  args[0].SetNumber(2);
  args[1].SetBoolean(false);  // RestoreSavedSettings(aiSavedTab, abTabsDisabled)
  // RestoreSavedSettings is what the engine calls at the opening with its saved tab (Quests); called again with the
  // System page it selects the tab button and the page together. SwitchPageToFront alone left Quests showing (pad112o).
  RE::GFxValue before;
  menu->uiMovie->GetVariable(&before, "_root.QuestJournalFader.Menu_mc.iCurrentTab");
  const bool r = menu->uiMovie->Invoke("_root.QuestJournalFader.Menu_mc.RestoreSavedSettings", nullptr, args, 2);
  args[1].SetBoolean(true);  // SwitchPageToFront(aiTab, abForceFade): the page faded in, not left at the Quests fade
  menu->uiMovie->Invoke("_root.QuestJournalFader.Menu_mc.SwitchPageToFront", nullptr, args, 2);
  // The bottom bar's hints belong to the page in front: a real tab change ends the old page and starts the new one
  // (quest_journal.swf: each page's startPage fills buttonPanel, Quests' with "Toggle Active" and "Show on Map"), so
  // the Quests page is ended and the System page started, as the movie's own tab change does.
  RE::GFxValue pages, quests, system;
  bool refreshed = false;
  if (menu->uiMovie->GetVariable(&pages, "_root.QuestJournalFader.Menu_mc.PageArray") && pages.IsArray() &&
      pages.GetArraySize() > 2 && pages.GetElement(0, &quests) && pages.GetElement(2, &system)) {
    if (quests.IsObject()) quests.Invoke("endPage");
    refreshed = system.IsObject() && system.Invoke("startPage");
  }
  SKSE::log::info("pad: the System page's own button hints {}", refreshed ? "started" : "not started (no PageArray)");
  RE::GFxValue after;
  const bool read = menu->uiMovie->GetVariable(&after, "_root.QuestJournalFader.Menu_mc.iCurrentTab");
  const double tab = read && after.IsNumber() ? after.GetNumber() : -1;
  const double was = before.IsNumber() ? before.GetNumber() : -1;
  SKSE::log::info("pad: the Journal Menu to its System page ({}; tab {} -> {})", tab == 2 ? "switched" : r ? "not switched" : "the movie refused", was, tab);
}

// Tab, the pad's Start and the HUD's Menu button all open TweenMenu; Wind UI does not always take it, so the next
// frame swaps an untaken tween for InventoryMenu, which Wind UI takes into its full menu mode (coordinator, 1.12 §8).
class TweenSink : public RE::BSTEventSink<RE::MenuOpenCloseEvent> {
 public:
  RE::BSEventNotifyControl ProcessEvent(const RE::MenuOpenCloseEvent* e, RE::BSTEventSource<RE::MenuOpenCloseEvent>*) override {
    if (e && e->opening && e->menuName == RE::JournalMenu::MENU_NAME) {
      // Esc's System page: Wind UI pops its windows over it; they are closed the next frame (reader, 2026-11-01).
      // J's opening too: the router swaps the Journal Menu for our journal, and the windows Wind UI popped for it were
      // left under it, open after the journal closed (pad112r step 20). Windows already up before (the taskbar's
      // Journal, a pane of ours) are left alone.
      const bool popped = !g.was_windows;
      // Wind UI's windows can come up a few frames late (pad112s: open under our journal, seen when it closed), so the
      // check runs each 50 ms for 1.5 s and hides them once.
      std::thread([popped] {
        for (int i = 0; i < 30; ++i) {
          std::this_thread::sleep_for(std::chrono::milliseconds(50));
          std::atomic<bool> done{false}, hid{false};
          SKSE::GetTaskInterface()->AddTask([popped, &done, &hid] {
            if (Open(kWindUIMenu) && (Open(RE::JournalMenu::MENU_NAME) || popped)) {
              if (auto* q = RE::UIMessageQueue::GetSingleton())
                q->AddMessage(RE::BSFixedString(kWindUIMenu), RE::UI_MESSAGE_TYPE::kHide, nullptr);
              SKSE::log::info("pad: Wind UI's windows closed over the Journal Menu or our journal");
              hid = true;
            }
            done = true;
            done.notify_one();
          });
          done.wait(false);
          if (hid) return;
        }
      }).detach();
      // It opens on its Quests tab (Skyrim's old quest log); the System pane and Esc want settings, load and quit: the
      // movie's own tab switch once it has loaded (J's opening is our journal's, closed by the router before this runs).
      std::thread([] {
        std::this_thread::sleep_for(std::chrono::milliseconds(400));
        SKSE::GetTaskInterface()->AddTask([] { SystemTab(); });
      }).detach();
      return RE::BSEventNotifyControl::kContinue;
    }
    if (e && e->opening && e->menuName == RE::MagicMenu::MENU_NAME) {
      // P: Wind UI takes MagicMenu into its windows, and the router has swapped it for our magic pane; the windows are
      // hidden while our pane is open (they can come up a few frames late, so each 50 ms for 1.5 s, as for J).
      std::thread([] {
        int hidden = 0;
        for (int i = 0; i < 30; ++i) {
          std::this_thread::sleep_for(std::chrono::milliseconds(50));
          std::atomic<bool> done{false};
          SKSE::GetTaskInterface()->AddTask([&done, &hidden] {
            if (Open(kWindUIMenu) && MagicPaneOpen())
              if (auto* q = RE::UIMessageQueue::GetSingleton()) {
                q->AddMessage(RE::BSFixedString(kWindUIMenu), RE::UI_MESSAGE_TYPE::kHide, nullptr);
                if (!hidden++) SKSE::log::info("pad: Wind UI's windows hidden under our magic pane");
              }
            done = true;
            done.notify_one();
          });
          done.wait(false);
        }
      }).detach();
      return RE::BSEventNotifyControl::kContinue;
    }
    if (!e || !e->opening || e->menuName != RE::TweenMenu::MENU_NAME) return RE::BSEventNotifyControl::kContinue;
    // Dear Diary's tween (its centre picker) drew for the frames until the swap below took (owner look 1: "starts to
    // bring up the dear diary UI before cutting to Wind UI"). Its movie is hidden now, in the opening event, before it
    // first draws; the menu itself still opens, so Wind UI's takeover and the swap run as before.
    if (auto* ui = RE::UI::GetSingleton())
      if (auto m = ui->GetMenu(RE::TweenMenu::MENU_NAME); m && m->uiMovie) {
        m->uiMovie->SetVisible(false);
        SKSE::log::info("pad: Dear Diary's tween hidden at its opening");
      }
    SKSE::GetTaskInterface()->AddTask([] {
      if (!pad::tween_to_windows(Open(RE::TweenMenu::MENU_NAME), Open(kWindUIMenu))) return;
      auto* q = RE::UIMessageQueue::GetSingleton();
      if (!q) return;
      q->AddMessage(RE::TweenMenu::MENU_NAME, RE::UI_MESSAGE_TYPE::kHide, nullptr);
      q->AddMessage(RE::InventoryMenu::MENU_NAME, RE::UI_MESSAGE_TYPE::kShow, nullptr);
      SKSE::log::info("pad: tween -> Wind UI's windows");
    });
    return RE::BSEventNotifyControl::kContinue;
  }
};

}  // namespace

void PadCursorInstall() {
  if (auto* ui = RE::UI::GetSingleton()) {
    static TweenSink tween;
    ui->AddEventSink<RE::MenuOpenCloseEvent>(&tween);
  }
  if (auto* dll = GetModuleHandleA(prisma::kDll))
    if (auto request = reinterpret_cast<prisma::RequestApi>(GetProcAddress(dll, prisma::kEntry)))
      g_prisma = static_cast<prisma::Api1*>(request(prisma::Version::v1));
  auto* mgr = RE::BSInputDeviceManager::GetSingleton();
  if (!mgr) {
    SKSE::log::error("pad: no input device manager; the pad cursor is off");
    return;
  }
  static PadSink sink;
  mgr->PrependEventSink(&sink);  // before the game's own sinks: a swallowed Esc never reaches the Journal Menu
  SKSE::log::info("pad: cursor ready (Wind UI's menu mode; PrismaUI {})", g_prisma ? "bound" : "absent");
}

}  // namespace argonia::plugin
