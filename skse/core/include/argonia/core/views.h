// The web-view host (1.2 §0, decision 0017 §3) as pure logic: which of our views exist, which is open, which has
// its page loaded, and what the binding must do next. ArgoniaCore's views.cpp turns each Op into one PrismaUI call
// (InteropCall, Show, Hide, Focus, Unfocus); nothing here knows PrismaUI, so the Scaleform fallback (0017, 1.2 §0)
// would replace only that adapter. Also: the journal key's latch, the chart's remembered view (a settings file,
// as Morrowind keeps its window layout per install, not per save), the journal's state from the log, and the
// 300-topic probe window (dev only: the probe journey's speaker).
#pragma once
#include "argonia/core/journal.h"
#include "argonia/core/messages.h"

#include <array>
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
inline constexpr std::array<Spec, 5> kViews{{
    {"hud", "argonia/hud/index.html", false, 0},
    {"dialogue", "argonia/dialogue/index.html", true, 10},
    {"journal", "argonia/journal/index.html", true, 10},
    {"chart", "argonia/chart/index.html", true, 10},
    {"sitting", "argonia/sitting/index.html", true, 10},
}};
const Spec* spec(std::string_view id);
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

// The chart's view as remembered between sessions: the settings file holds the last chart.pan intent's text. A
// missing, unreadable or out-of-range file gives the whole province (centre 1,1, zoom 1).
msg::ChartView remembered_chart(std::optional<std::string_view> text);
std::string chart_layout_text(const msg::ChartView& v);

// The game date as the journal prints it ("16th of the Eighth Month, 201"); views never format dates.
msg::GameDate date(const journal::GameDate& d);

// The journal at one page of a tab. `name(quest)` is the quest's display name and its world id, `text(quest,
// entry)` the log entry's text; entries are paged `per_page` at a time, oldest first, optionally filtered to one
// quest (by world id).
struct QuestNames {
  std::string id, name;
};
msg::JournalState journal_state(const journal::Log& log, const std::function<QuestNames(journal::QuestId)>& name,
                                const std::function<std::string(journal::QuestId, journal::EntryId)>& text,
                                const msg::JournalPage& at, std::size_t per_page = 6);

// The 1.2 §0 probe's window: a speaker with `topics` topics (labels "Topic 001" ...), one greeting, Goodbye on.
msg::DialogueState probe_dialogue(std::string speaker_id, std::string speaker_name, std::size_t topics);

}  // namespace argonia::core::views
