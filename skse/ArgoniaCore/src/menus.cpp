// Our System pane and our wait window over the engine's own menus (1.12, lane 1.12-menus; owner look 1).
//
// Esc opens the Journal Menu, whose System page is Dear Diary's (parchment, with a Quests tab): its movie is hidden the
// frame it opens and our System pane (PrismaUI, the frame style) opens instead. The Journal Menu stays open underneath
// so the game's own handlers do the work: the two quits call its FxDelegate's QuitToMainMenu (wrapped by life.cpp for
// the suspend save) and QuitToDesktop; Settings and Load show its movie again and start that page by the page's own
// category press; when the player backs out to the page's main list, the movie hides again and our pane returns.
// T opens the Sleep/Wait Menu: its movie is hidden and our wait window opens; the hours picked are set on the movie's
// own slider and its own OK press runs the engine's wait. Nothing of the game's behaviour is rebuilt here.
#include "core.h"

#include <atomic>
#include <chrono>
#include <thread>
#include <utility>

namespace argonia::plugin {

namespace {

// Main thread (menu events, the view host's intents run under Get().lock on it).
struct MenusState {
  bool system_open = false;   // our pane stands over a hidden Journal Menu
  bool delegated = false;     // a page of the Journal Menu (Settings, Load) is shown; our pane returns at its main list
  bool wait_open = false;     // our wait window stands over a hidden Sleep/Wait Menu
  bool waiting = false;       // the engine's wait was started from our window: its menu closes itself
} g;

RE::GPtr<RE::IMenu> MenuOf(std::string_view name) {
  auto* ui = RE::UI::GetSingleton();
  return ui ? ui->GetMenu(RE::BSFixedString(name)) : RE::GPtr<RE::IMenu>{};
}

bool IsOpen(std::string_view name) {
  auto* ui = RE::UI::GetSingleton();
  return ui && ui->IsMenuOpen(RE::BSFixedString(name));
}

bool SetMovieVisible(std::string_view name, bool visible) {
  auto m = MenuOf(name);
  if (!m || !m->uiMovie) return false;
  m->uiMovie->SetVisible(visible);
  return true;
}

void HideMenu(std::string_view name) {
  if (auto* q = RE::UIMessageQueue::GetSingleton()) q->AddMessage(RE::BSFixedString(name), RE::UI_MESSAGE_TYPE::kHide, nullptr);
}

// The Journal Menu's System page (PageArray[2]: Quests, General stats, System).
bool SystemPage(RE::GFxValue& page) {
  auto m = MenuOf(RE::JournalMenu::MENU_NAME);
  RE::GFxValue pages;
  return m && m->uiMovie && m->uiMovie->GetVariable(&pages, "_root.QuestJournalFader.Menu_mc.PageArray") &&
         pages.IsArray() && pages.GetArraySize() > 2 && pages.GetElement(2, &page) && page.IsObject();
}

double PageState(RE::GFxValue& page) {
  RE::GFxValue s;
  return page.GetMember("iCurrentState", &s) && s.IsNumber() ? s.GetNumber() : -1;
}

void PushSystem() {
  auto json = ac::msg::encode(ac::msg::SystemState{true});
  if (!json) {
    SKSE::log::error("views: the System pane does not fit the schema: {}", json.error());
    return;
  }
  Push("system", std::move(*json));
}

// While a page of the Journal Menu is shown: back at the page's main list (the state it had when we handed over), the
// movie hides and our pane returns; the Journal Menu closed (the page's own quit or load), nothing more is ours.
void WatchDelegated(double main_state) {
  // Load leaves the main list a few frames after its press (the save list is read first: state 0 -> 0 at the press,
  // menus-look 20261101T143721), so the page counts as back only once it has left the main list, or after 3 s.
  std::thread([main_state] {
    bool left = false;
    for (int i = 0; i < 20 * 60 * 30; ++i) {  // at most half an hour on a page
      std::this_thread::sleep_for(std::chrono::milliseconds(50));
      std::atomic<int> verdict{0};  // 0 waiting, 1 stop
      std::atomic<bool> done{false};
      SKSE::GetTaskInterface()->AddTask([main_state, i, &left, &verdict, &done] {
        RE::GFxValue page;
        const bool at_main = SystemPage(page) && PageState(page) == main_state;
        if (!at_main) left = true;
        if (!g.delegated || !IsOpen(RE::JournalMenu::MENU_NAME)) {
          g.delegated = g.system_open = false;
          verdict = 1;
        } else if (at_main && (left || i >= 60)) {
          SetMovieVisible(RE::JournalMenu::MENU_NAME, false);
          g.delegated = false;
          SKSE::log::info("menus: back at the System page's main list; our System pane again ({})", left ? "left and back" : "never left it");
          std::lock_guard l(Get().lock);
          PushSystem();
          verdict = 1;
        }
        done = true;
        done.notify_one();
      });
      done.wait(false);
      if (verdict) return;
    }
  }).detach();
}

// Settings and Load are Dear Diary's System page, with the Quests and stats tabs over it (owner look 1: quests live
// only in the journal). Handed over, the tab bar is hidden; the page's colours, like the Mod configuration pages,
// message boxes and lockpicking, come from the install-time recolour (tools/ui_theme/retheme.py FRAME, decision 0014).
bool FrameMovie(std::string_view menu_name, const char* path, bool tabs) {
  auto m = MenuOf(menu_name);
  if (!m || !m->uiMovie) return false;
  RE::GFxValue menu;
  if (!m->uiMovie->GetVariable(&menu, path) || !menu.IsDisplayObject()) {
    SKSE::log::warn("menus: no {} on {}; left as it is", path, menu_name);
    return false;
  }
  std::string members, hidden;
  menu.VisitMembers([&members](const char* name, const RE::GFxValue&) { members += (members.empty() ? "" : ",") + std::string(name); });
  if (tabs)
    for (const char* tab : {"QuestsTab", "StatsTab", "SystemTab", "previousTabButton", "nextTabButton"}) {  // the tab bar
      RE::GFxValue clip;
      if (menu.GetMember(tab, &clip) && clip.IsDisplayObject()) {
        RE::GFxValue::DisplayInfo info;
        info.SetVisible(false);
        clip.SetDisplayInfo(info);
        hidden += (hidden.empty() ? "" : ",") + std::string(tab);
      }
    }
  SKSE::log::info("menus: {} handed over (tabs hidden: {}; {} has {})", menu_name, hidden.empty() ? "none" : hidden,
                  path, members);
  const bool ok = true;
  return ok;
}

// Settings or Load: the page's own category press for the entry whose label names it, with the movie shown again.
void Delegate(std::string_view want) {
  RE::GFxValue page, list, entries;
  if (!SystemPage(page) || !page.GetMember("CategoryList", &list) || !list.IsObject() ||
      !list.GetMember("entryList", &entries) || !entries.IsArray()) {
    SKSE::log::warn("menus: the System page has no CategoryList.entryList; {} not opened", want);
    return;
  }
  std::string seen;
  for (std::uint32_t i = 0; i < entries.GetArraySize(); ++i) {
    RE::GFxValue entry, text, index;
    if (!entries.GetElement(i, &entry) || !entry.IsObject() || !entry.GetMember("text", &text) || !text.IsString()) continue;
    std::string t = text.GetString();
    seen += (seen.empty() ? "" : ", ") + t;
    std::string up = t;
    for (auto& ch : up) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    if (up.find(want) == std::string::npos) continue;
    auto m = MenuOf(RE::JournalMenu::MENU_NAME);
    RE::GFxValue ev;
    m->uiMovie->CreateObject(&ev);
    ev.SetMember("entry", entry);
    const double idx = entry.GetMember("index", &index) && index.IsNumber() ? index.GetNumber() : i;
    ev.SetMember("index", RE::GFxValue(idx));
    const double main_state = PageState(page);
    g.delegated = true;
    FrameMovie(RE::JournalMenu::MENU_NAME, "_root.QuestJournalFader.Menu_mc", true);
    m->uiMovie->SetVisible(true);
    const bool ok = page.Invoke("onCategoryButtonPress", nullptr, &ev, 1);
    SKSE::log::info("menus: the System page's {} pressed (entry {} '{}', index {}, state {} -> {}){}", want, i, t, idx,
                    main_state, PageState(page), ok ? "" : "; the movie refused");
    WatchDelegated(main_state);
    return;
  }
  SKSE::log::warn("menus: no {} entry on the System page (entries: {})", want, seen);
}

bool JournalCallback(const char* name) {
  auto m = MenuOf(RE::JournalMenu::MENU_NAME);
  if (!m || !m->fxDelegate || !m->uiMovie) return false;
  // GameDelegate.call sends the response id first (0: no response), as quit_via_journal in the bridge does (b112e).
  RE::GFxValue args[1];
  args[0].SetNumber(0.0);
  m->fxDelegate->Callback(m->uiMovie.get(), name, args, 1);
  return true;
}

void LogCallbacks(std::string_view menu) {
  auto m = MenuOf(menu);
  if (!m || !m->fxDelegate) return;
  std::string names;
  for (auto it = m->fxDelegate->callbacks.begin(); it != m->fxDelegate->callbacks.end(); ++it)
    names += (names.empty() ? "" : ", ") + std::string(it->first.c_str());
  SKSE::log::info("menus: {} registers {}", menu, names);
}

// The wait window: the time now as the player reads it (core views::wait_now, the journal's calendar words).
std::string NowText() {
  auto* cal = RE::Calendar::GetSingleton();
  if (!cal) return {};
  return ac::views::wait_now({static_cast<std::int32_t>(cal->GetYear()), static_cast<std::int32_t>(cal->GetMonth()) + 1,
                              static_cast<std::int32_t>(cal->GetDay()), static_cast<double>(cal->GetHour())});
}

constexpr const char* kWaitRoots[] = {"_root.SleepWaitMenu_mc", "_root.SleepWaitMenuObj", "_root"};

}  // namespace

// --- Esc ---------------------------------------------------------------------------------------------------------

// The Journal Menu opened by Esc (not J): its movie hidden now, before it draws, and our System pane over it.
void SystemMenuOpened() {
  if (!ViewsBound()) return;
  SetMovieVisible(RE::JournalMenu::MENU_NAME, false);
  g.system_open = true;
  g.delegated = false;
  SKSE::log::info("menus: Esc's Journal Menu hidden; our System pane opens");
  PushSystem();
}

std::string SystemIntent(const ac::msg::SystemPick& p) {
  switch (p.action) {
    case ac::msg::SystemAction::settings:
    case ac::msg::SystemAction::load: {
      const bool settings = p.action == ac::msg::SystemAction::settings;
      g.delegated = true;  // closing our pane must not close the Journal Menu
      CloseView("system");
      SKSE::GetTaskInterface()->AddTask([settings] { Delegate(settings ? "SETTINGS" : "LOAD"); });
      return {};
    }
    case ac::msg::SystemAction::quitToMainMenu:
      SKSE::log::info("menus: quit to the main menu from our System pane");
      LogCallbacks(RE::JournalMenu::MENU_NAME);
      if (!JournalCallback("QuitToMainMenu")) return R"({"error":"the Journal Menu is not open"})";
      return {};
    case ac::msg::SystemAction::quitToDesktop:
      SKSE::log::info("menus: quit to the desktop from our System pane");
      SuspendSaveFor("quit");
      if (!JournalCallback("QuitToDesktop")) return R"({"error":"the Journal Menu is not open"})";
      return {};
  }
  return {};
}

// --- message boxes and lockpicking ------------------------------------------------------------------------------

// Dear Diary's message box and lockpicking are in the frame style from the install-time recolour (retheme.py FRAME);
// at opening only their root's members are logged, a frame later (the movie has loaded by then).
void FrameMenuOpened(std::string_view menu) {
  std::string name(menu);
  SKSE::GetTaskInterface()->AddTask([name] { FrameMovie(name, "_root", false); });
}

// --- T -----------------------------------------------------------------------------------------------------------

void WaitMenuOpened() {
  if (!ViewsBound()) return;
  SetMovieVisible(RE::SleepWaitMenu::MENU_NAME, false);
  g.wait_open = true;
  g.waiting = false;
  LogCallbacks(RE::SleepWaitMenu::MENU_NAME);
  // The engine sets sleep or wait on the movie a frame after its opening (SetSleeping): read then.
  SKSE::GetTaskInterface()->AddTask([] {
    SKSE::GetTaskInterface()->AddTask([] {
      auto m = MenuOf(RE::SleepWaitMenu::MENU_NAME);
      bool sleep = false;
      if (m && m->uiMovie)
        for (const auto* root : kWaitRoots) {
          RE::GFxValue q;
          const std::string path = std::string(root) + ".QuestionInstance.text";
          if (m->uiMovie->GetVariable(&q, path.c_str()) && q.IsString()) {
            const std::string t = q.GetString();
            sleep = t.find("Rest") != std::string::npos || t.find("Sleep") != std::string::npos;
            SKSE::log::info("menus: the Sleep/Wait Menu asks '{}' ({})", t, path);
            break;
          }
        }
      ac::msg::WaitState s{sleep ? ac::msg::WaitMode::sleep : ac::msg::WaitMode::wait, NowText(), 1, 24};
      auto json = ac::msg::encode(s);
      if (!json) {
        SKSE::log::error("views: the wait window does not fit the schema: {}", json.error());
        return;
      }
      std::lock_guard l(Get().lock);
      if (IsOpen(RE::SleepWaitMenu::MENU_NAME)) Push("wait", std::move(*json));
    });
  });
  SKSE::log::info("menus: the Sleep/Wait Menu hidden; our wait window opens");
}

std::string WaitIntent(const ac::msg::WaitPick& p) {
  const auto hours = std::clamp<std::int64_t>(p.hours, 1, 24);
  g.waiting = true;  // closing our window must not cancel the wait
  CloseView("wait");
  SKSE::GetTaskInterface()->AddTask([hours] {
    auto m = MenuOf(RE::SleepWaitMenu::MENU_NAME);
    if (!m || !m->uiMovie) {
      SKSE::log::warn("menus: the Sleep/Wait Menu closed before the wait");
      return;
    }
    for (const auto* root : kWaitRoots) {
      RE::GFxValue slider;
      const std::string base(root);
      if (!m->uiMovie->GetVariable(&slider, (base + ".HoursSlider").c_str()) || !slider.IsObject()) continue;
      slider.SetMember("value", RE::GFxValue(static_cast<double>(hours)));
      RE::GFxValue back;
      slider.GetMember("value", &back);
      const bool ok = m->uiMovie->Invoke((base + ".onOKPress").c_str(), nullptr, nullptr, 0);
      SKSE::log::info("menus: wait {} h through {}.onOKPress (slider reads {}){}", hours, base,
                      back.IsNumber() ? back.GetNumber() : -1.0, ok ? "" : "; the movie refused");
      return;
    }
    SKSE::log::warn("menus: no HoursSlider on the Sleep/Wait Menu; no wait");
    HideMenu(RE::SleepWaitMenu::MENU_NAME);
  });
  return {};
}

// A view of ours closed: the engine menu under it closes too, unless it is handed over (a page, the wait running).
void MenusViewClosed(std::string_view view) {
  if (view == "system" && g.system_open && !g.delegated) {
    g.system_open = false;
    if (IsOpen(RE::JournalMenu::MENU_NAME)) HideMenu(RE::JournalMenu::MENU_NAME);
  }
  if (view == "wait" && g.wait_open) {
    g.wait_open = false;
    if (!g.waiting && IsOpen(RE::SleepWaitMenu::MENU_NAME)) HideMenu(RE::SleepWaitMenu::MENU_NAME);
  }
}

// An engine menu closed under a view of ours (a load, a quit, the wait's end): the view goes too.
void MenusMenuClosed(std::string_view menu) {
  auto& c = Get();
  std::lock_guard l(c.lock);
  if (menu == RE::JournalMenu::MENU_NAME) {
    const bool ours = std::exchange(g.system_open, false);
    g.delegated = false;
    if (ours && c.view_host.is_open("system")) CloseView("system");
  }
  if (menu == RE::SleepWaitMenu::MENU_NAME) {
    const bool ours = std::exchange(g.wait_open, false);
    g.waiting = false;
    if (ours && c.view_host.is_open("wait")) CloseView("wait");
  }
}

}  // namespace argonia::plugin
