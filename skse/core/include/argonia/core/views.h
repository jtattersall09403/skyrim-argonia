// The web-view host (1.2 §0, decision 0017 §3) as pure logic: which of our views exist, which is open, which has
// its page loaded, and what the binding must do next. ArgoniaCore's views.cpp turns each Op into one PrismaUI call
// (InteropCall, Show, Hide, Focus, Unfocus); nothing here knows PrismaUI, so the Scaleform fallback (0017, 1.2 §0)
// would replace only that adapter. Also: the journal key's latch, the chart's remembered view (a settings file,
// as Morrowind keeps its window layout per install, not per save), the journal's state from the log, and the
// 300-topic probe window (dev only: the probe journey's speaker).
#pragma once
#include "argonia/core/chart.h"
#include "argonia/core/journal.h"
#include "argonia/core/messages.h"

#include <array>
#include <cstdint>
#include <functional>
#include <map>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace argonia::core::views {

// One view of ours: its page under Data/PrismaUI/views/ (the installer lays the bundle there), whether opening it
// takes the input focus and pauses the game, and its draw order (the HUD lowest).
struct Spec {
  std::string_view id, page;
  bool modal;  // takes focus and pauses; one modal at a time
  int order;
};
inline constexpr std::array<Spec, 11> kViews{{
    {"hud", "argonia/hud/index.html", false, 0},
    {"dialogue", "argonia/dialogue/index.html", true, 10},
    {"journal", "argonia/journal/index.html", true, 10},
    {"chart", "argonia/chart/index.html", true, 10},
    {"sitting", "argonia/sitting/index.html", true, 10},
    {"magic", "argonia/magic/index.html", true, 10},  // our magic pane, for Wind UI's magic window (1.12)
    // the map pane among Wind UI's windows (1.12 look 1): the chart docked and display-only, shown while they are open
    {"chartpane", "argonia/chart/pane.html", false, 5},
    {"system", "argonia/system/index.html", true, 10},  // our System pane, for Dear Diary's System page (Esc)
    {"wait", "argonia/wait/index.html", true, 10},      // our wait window, over the hidden Sleep/Wait Menu (T)
    // the custom-UI card only (router set_custom_ui): ours for InventoryMenu and StatsMenu (1.12 r4)
    {"inventory", "argonia/inventory/index.html", true, 10},
    {"charsheet", "argonia/charsheet/index.html", true, 10},
}};
const Spec* spec(std::string_view id);
// The map pane's rule (owner play test 3 #26: "Map UI pane appears over dialogue UI pane"): the docked chart shows
// only while Wind UI's pause windows are open with none of its trade, container or crafting windows, no
// conversation (the engine's DialogueMenu, which outlives our dialogue view across a barter round trip) and no modal
// view of ours. Opening any modal view hides it (Host::open).
bool pane_wanted(bool windui_open, bool trade_window_open, bool dialogue_menu_open, bool modal_open);
// Every engine menu that takes the screen from Wind UI's windows and so hides the pane (the owner's finding 26, barter:
// the pane stood over Livia's stock). The menu events and the rule both read this one list.
bool is_trade_menu(std::string_view menu_name);
// The menu of an open/close event counts as it will be (open when opening), whatever the UI's stack says at the
// event: the engine sends the event before the menu is in (or out of) its stack.
bool menu_open_after_event(bool listed_open, bool event_menu_is_this, bool event_opening);
inline constexpr std::string_view kPushFunction = "argoniaPush";      // bridge.ts: window.argoniaPush(text)
inline constexpr std::string_view kIntentFunction = "argoniaIntent";  // bridge.ts calls window.argoniaIntent(text)

enum class OpKind : std::uint8_t { push, show, hide, focus, unfocus };
struct Op {
  OpKind kind;
  std::string view;
  std::string arg;  // the push's text
  bool operator==(const Op&) const = default;
};

class Host {
 public:
  // A push keeps the text as the view's last; it is sent now if the page is loaded, else when it loads. A push to a
  // closed modal view opens it (closing any other modal first); the HUD is always open.
  std::vector<Op> push(std::string_view view, std::string text);
  // The page reported DOM ready: its last push is sent and, if it is open, it is shown (and focused if modal).
  std::vector<Op> ready(std::string_view view);
  std::vector<Op> close(std::string_view view);
  std::vector<Op> close_all();  // a load: every modal closes, the HUD stays
  bool is_open(std::string_view view) const;
  bool is_ready(std::string_view view) const;
  std::optional<std::string> modal() const { return modal_; }
  const std::string* last(std::string_view view) const;

 private:
  std::vector<Op> open(std::string_view view);
  std::map<std::string, std::string, std::less<>> last_;
  std::map<std::string, bool, std::less<>> ready_;
  std::optional<std::string> modal_;
};

// The journal key (J, the pad's Back: the "Journal" user event in our control map) opens our journal; Escape also
// opens the vanilla Journal Menu (its System tab: save, settings, quit), which must keep working until 3.1. The
// latch holds a press for `window` seconds, so the Journal Menu that opens right after it is ours to replace.
class KeyLatch {
 public:
  void press(double now) { at_ = now; }
  bool take(double now, double window = 1.0);  // true once per press within the window

 private:
  std::optional<double> at_;
};

// The press that closes a modal view must not reach the game: B (or Esc) goes down while the view is open, the view
// closes, and the release then reaches TK Dodge, which rolls on a sprint-key tap. The guard remembers each button
// that went down while a modal was open and swallows that button's repeats and release, once; a press that began
// with no modal open is never touched. `key` is the device and button id packed by the adapter.
// The intent a close control (Cancel, the Tween Menu key Tab, the Journal key Esc or the pad's Back, the Quick Map key
// on the chart) sends to the open modal view, or nothing when that view does not close by it. The dialogue view says
// goodbye when a conversation is open (the probe's window, with none, just closes); sitting stands by its own intent.
struct CloseControl {
  bool cancel = false, tween = false, journal = false, quick_map = false, quick_magic = false;
};
std::optional<std::string> close_intent(std::string_view open_view, const CloseControl& c, bool conversation_open);

// The activation prompt (1.2 §d, the hudPrompt row is our view): the engine's activate text for the crosshair's
// reference ("Talk", "Take\nLedger", "<font color='#FFFFFF'>Open</font>\nChest") read into a verb and a target; the
// target falls back to the reference's display name. Tags are dropped. Nothing when there is no verb.
struct PromptText {
  std::string verb, target;
  bool operator==(const PromptText&) const = default;
};
std::optional<PromptText> prompt_from_activate_text(std::string_view activate_text, std::string_view display_name);

// The activated actor as the intercept sees it (owner play test 3, findings 27, 28). A corpse is searched and a fighter
// in combat with the player is fought: neither is ever spoken to, whatever the engine's text or a perk's label says.
struct ActorAt {
  bool dead = false;
  bool fighting_player = false;  // in combat and hostile to the player
};
bool offers_talk(const ActorAt& a);
// The prompt over an actor: a corpse's verb is Search, a fighter has none, anyone else keeps the engine's text.
std::optional<PromptText> actor_prompt(std::optional<PromptText> engine, const ActorAt& a);

class ClosePressGuard {
 public:
  // True when the adapter must hide this event from the game.
  bool swallow(std::uint32_t key, bool down, bool up, bool modal_open);

 private:
  std::vector<std::uint32_t> held_;
};

// The chart's view as remembered between sessions: the settings file holds the last chart.pan intent's text. A
// missing, unreadable or out-of-range file gives the whole province (centre 1,1, zoom 1).
msg::ChartView remembered_chart(std::optional<std::string_view> text);
std::string chart_layout_text(const msg::ChartView& v);
// The open chart: the sketch everywhere, the revealed layer through the cells of the CHRT family (x then y), the
// view as remembered. Discovered places join with 2.W4.
msg::ChartState chart_state(const chart::Discovered& d, const msg::ChartView& v,
                            std::vector<msg::ChartPlace> places = {},
                            std::optional<msg::ChartPlayer> player = std::nullopt);
// One discovered map marker as the chart's place, or nothing: a marker not yet discovered (chart::marker_discovered),
// of no place kind, or unnamed. `x_units, y_units` are the marker reference's position in Skyrim units.
std::optional<msg::ChartPlace> chart_place(std::uint32_t form_id, std::string_view name, std::uint8_t flags,
                                           std::uint16_t type, double x_units, double y_units);
// The player in Skyrim units and radians as the chart's marker.
msg::ChartPlayer chart_player(double x_units, double y_units, double angle_z);
// The HUD's minimap: the revealed cells and discovered places within chart::kMinimapReach of the player, each in
// the order given (cells x then y). Outside the province (no player) it carries nothing.
msg::HudMinimap minimap(const chart::Discovered& d, const std::vector<msg::ChartPlace>& places,
                        std::optional<msg::ChartPlayer> player);

// The game date as the journal prints it ("16th of the Eighth Month, 201"); views never format dates.
msg::GameDate date(const journal::GameDate& d);
// The wait window's "now" (lane 1.12-menus): the hour in words and the journal's date, e.g. "10:09 in the morning,
// the 17th of the Second Seed Month" (never the engine's "4E 201" string: views never format game dates).
std::string wait_now(const journal::GameDate& d);

// The journal at one ribbon (1.12 §6). `name(quest)` is the quest's display name and world id, `text(quest, entry)`
// the log entry's text, `directions(quest, entry)` where to go next after that entry, `group(quest)` the questline
// or place it is listed under. Current lists the active quests, Finished the complete and failed, each by group in
// the order its most recent quest was written, most recent first; the quest picked (else the most recent listed)
// opens on its latest direction (active only), then its entries newest first. All entries is the diary, oldest first, `per_page` a page.
// The search keeps the quests whose name or any entry matches it, and the diary's entries that match (journal::
// matches); Topics is 2.12's and empty.
struct QuestNames {
  std::string id, name;
};
using EntryText = std::function<std::string(journal::QuestId, journal::EntryId)>;
using Directions = std::function<std::optional<std::string>(journal::QuestId, journal::EntryId)>;
using GroupOf = std::function<journal::Group(journal::QuestId)>;
msg::JournalState journal_state(const journal::Log& log, const std::function<QuestNames(journal::QuestId)>& name,
                                const EntryText& text, const Directions& directions, const GroupOf& group,
                                const msg::JournalPage& at, std::size_t per_page = 6);
// The records' group (journal::quest_text, group_of); a quest the table lacks is listed under "Other quests".
journal::Group entry_group(journal::QuestId q);
// The records' words (journal::stage_text): the stage's log entry ("" when the table lacks the stage) and its
// directions (none when it gives none). What ArgoniaCore passes to journal_state.
std::string entry_text(journal::QuestId q, journal::EntryId e);
std::optional<std::string> entry_directions(journal::QuestId q, journal::EntryId e);

// The 1.2 §0 probe's window: a speaker with `topics` topics (labels "Topic 001" ...), one greeting, Goodbye on.
msg::DialogueState probe_dialogue(std::string speaker_id, std::string speaker_name, std::size_t topics);

}  // namespace argonia::core::views
