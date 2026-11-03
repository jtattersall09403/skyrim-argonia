#include "argonia/core/views.h"

#include <algorithm>
#include <cmath>
#include <cstdio>

namespace argonia::core::views {

const Spec* spec(std::string_view id) {
  for (const auto& s : kViews)
    if (s.id == id) return &s;
  return nullptr;
}

bool pane_wanted(bool windui_open, bool trade_window_open, bool dialogue_menu_open, bool modal_open) {
  return windui_open && !trade_window_open && !dialogue_menu_open && !modal_open;
}

bool is_trade_menu(std::string_view n) {
  for (std::string_view m : {"BarterMenu", "ContainerMenu", "GiftMenu", "Crafting Menu", "Lockpicking Menu", "Book Menu",
                             "Training Menu"})
    if (n == m) return true;
  return false;
}

bool menu_open_after_event(bool listed_open, bool event_menu_is_this, bool event_opening) {
  return event_menu_is_this ? event_opening : listed_open;
}

// --- Host --------------------------------------------------------------------------------------------------------

bool Host::is_ready(std::string_view view) const {
  auto it = ready_.find(view);
  return it != ready_.end() && it->second;
}

bool Host::is_open(std::string_view view) const {
  const auto* s = spec(view);
  if (!s) return false;
  return s->modal ? modal_ == view : true;
}

const std::string* Host::last(std::string_view view) const {
  auto it = last_.find(view);
  return it == last_.end() ? nullptr : &it->second;
}

std::vector<Op> Host::open(std::string_view view) {
  std::vector<Op> ops;
  const auto* s = spec(view);
  if (!s || !s->modal || modal_ == view) return ops;
  if (modal_) {
    const std::string prev = *modal_;  // a copy: close() resets modal_, which a view of it would dangle on
    auto shut = close(prev);
    ops.insert(ops.end(), shut.begin(), shut.end());
  }
  modal_ = std::string(view);
  // A docked display-only view (the map pane) never stands over a modal one: hidden as any modal opens.
  for (const auto& d : kViews)
    if (!d.modal && d.order > 0 && is_ready(d.id)) ops.push_back({OpKind::hide, std::string(d.id), {}});
  if (is_ready(view)) {
    ops.push_back({OpKind::show, std::string(view), {}});
    ops.push_back({OpKind::focus, std::string(view), {}});
  }
  return ops;
}

std::vector<Op> Host::push(std::string_view view, std::string text) {
  std::vector<Op> ops;
  const auto* s = spec(view);
  if (!s) return ops;
  last_[std::string(view)] = text;
  if (s->modal) ops = open(view);
  if (is_ready(view)) ops.push_back({OpKind::push, std::string(view), std::move(text)});
  return ops;
}

std::vector<Op> Host::ready(std::string_view view) {
  std::vector<Op> ops;
  const auto* s = spec(view);
  if (!s) return ops;
  ready_[std::string(view)] = true;
  if (const auto* t = last(view)) ops.push_back({OpKind::push, std::string(view), *t});
  if (is_open(view)) {
    ops.push_back({OpKind::show, std::string(view), {}});
    if (s->modal) ops.push_back({OpKind::focus, std::string(view), {}});
  } else {
    ops.push_back({OpKind::hide, std::string(view), {}});
  }
  return ops;
}

std::vector<Op> Host::close(std::string_view view) {
  std::vector<Op> ops;
  const auto* s = spec(view);
  if (!s || !s->modal) return ops;  // the HUD never closes
  last_.erase(std::string(view));
  if (modal_ != view) return ops;
  modal_.reset();
  if (is_ready(view)) {
    ops.push_back({OpKind::unfocus, std::string(view), {}});
    ops.push_back({OpKind::hide, std::string(view), {}});
  }
  return ops;
}

std::vector<Op> Host::close_all() {
  std::vector<Op> ops;
  if (modal_) {
    const std::string prev = *modal_;
    ops = close(prev);
  }
  for (const auto& s : kViews)
    if (s.modal) last_.erase(std::string(s.id));
  return ops;
}

// --- KeyLatch ----------------------------------------------------------------------------------------------------

bool KeyLatch::take(double now, double window) {
  if (!at_) return false;
  const bool fresh = now >= *at_ && now - *at_ <= window;
  at_.reset();
  return fresh;
}

// --- the chart's remembered view ---------------------------------------------------------------------------------

msg::ChartView remembered_chart(std::optional<std::string_view> text) {
  const msg::ChartView whole{1.0, 1.0, 1.0};
  if (!text) return whole;
  auto m = msg::decode_intent(*text);  // the schema twin checks the zoom's range
  if (!m) return whole;
  const auto* pan = std::get_if<msg::ChartPan>(&*m);
  if (!pan || !std::isfinite(pan->view.centre_x) || !std::isfinite(pan->view.centre_y)) return whole;
  return pan->view;
}

std::string chart_layout_text(const msg::ChartView& v) {
  auto t = msg::encode(msg::ChartPan{v});
  return t ? *t : std::string();
}

msg::ChartState chart_state(const chart::Discovered& d, const msg::ChartView& v, std::vector<msg::ChartPlace> places,
                            std::optional<msg::ChartPlayer> player) {
  msg::ChartState s;
  s.worldspace = "argonia";
  s.sketch = "chart.sketch";
  for (const auto& c : chart::cells(d)) s.revealed.push_back({c.x, c.y});
  s.places = std::move(places);
  s.player = player;
  s.view = v;
  return s;
}

std::optional<msg::ChartPlace> chart_place(std::uint32_t form_id, std::string_view name, std::uint8_t flags,
                                           std::uint16_t type, double x_units, double y_units) {
  const auto kind = chart::marker_kind(type);
  if (!chart::marker_discovered(flags) || kind.empty() || name.empty()) return std::nullopt;
  char id[9];
  std::snprintf(id, sizeof id, "%08X", form_id);
  const auto p = chart::cell_units(x_units, y_units);
  const auto r = [](double n) { return std::round(n * 1000) / 1000; };
  return msg::ChartPlace{id, std::string(name), std::string(kind), r(p.x), r(p.y)};
}

msg::ChartPlayer chart_player(double x_units, double y_units, double angle_z) {
  const auto p = chart::cell_units(x_units, y_units);
  const auto r = [](double n) { return std::round(n * 1000) / 1000; };
  const double h = std::round(chart::heading_deg(angle_z) * 10) / 10;
  return {r(p.x), r(p.y), h >= 360 ? 0 : h};
}

msg::HudMinimap minimap(const chart::Discovered& d, const std::vector<msg::ChartPlace>& places,
                        std::optional<msg::ChartPlayer> player) {
  msg::HudMinimap m;
  if (!player) return m;
  m.map.player = player;
  const chart::Point at{player->x, player->y};
  for (const auto& c : chart::cells_near(d, at)) m.map.revealed.push_back({c.x, c.y});
  for (const auto& p : places)
    if (chart::within(at, {p.x, p.y})) m.map.places.push_back(p);
  return m;
}

// --- the journal -------------------------------------------------------------------------------------------------

namespace {

std::string ordinal(std::int64_t n) {
  const auto m100 = n % 100, m10 = n % 10;
  const char* suf = (m100 >= 11 && m100 <= 13) ? "th" : m10 == 1 ? "st" : m10 == 2 ? "nd" : m10 == 3 ? "rd" : "th";
  return std::to_string(n) + suf;
}

constexpr std::array<std::string_view, 12> kMonthWords{"First", "Second", "Third", "Fourth", "Fifth", "Sixth",
                                                       "Seventh", "Eighth", "Ninth", "Tenth", "Eleventh", "Twelfth"};

msg::JournalEntryKind entry_kind(journal::Kind k) {
  switch (k) {
    case journal::Kind::complete: return msg::JournalEntryKind::complete;
    case journal::Kind::fail: return msg::JournalEntryKind::fail;
    default: return msg::JournalEntryKind::progress;
  }
}

msg::QuestStatus status(journal::Status s) {
  switch (s) {
    case journal::Status::complete: return msg::QuestStatus::complete;
    case journal::Status::failed: return msg::QuestStatus::failed;
    default: return msg::QuestStatus::active;
  }
}

}  // namespace

msg::GameDate date(const journal::GameDate& d) {
  msg::GameDate out{d.year, d.month, d.day, d.hour, {}};
  const auto month = (d.month >= 1 && d.month <= 12) ? std::string(kMonthWords[std::size_t(d.month - 1)])
                                                     : std::to_string(d.month);
  out.text = ordinal(d.day) + " of the " + month + " Month, " + std::to_string(d.year);
  return out;
}

std::string wait_now(const journal::GameDate& d) {
  const int minutes = static_cast<int>(d.hour * 60.0 + 0.5) % (24 * 60);
  const int h24 = minutes / 60, m = minutes % 60;
  const int h12 = h24 % 12 == 0 ? 12 : h24 % 12;
  const char* part = h24 < 5 ? "at night" : h24 < 12 ? "in the morning" : h24 < 18 ? "in the afternoon" : h24 < 21 ? "in the evening" : "at night";
  char clock[16];
  std::snprintf(clock, sizeof clock, "%d:%02d", h12, m);
  const auto t = date(d).text;  // "17th of the Second Seed Month, 201"
  return std::string(clock) + " " + part + ", the " + t.substr(0, t.rfind(','));
}

msg::JournalState journal_state(const journal::Log& log, const std::function<QuestNames(journal::QuestId)>& name,
                                const EntryText& text, const Directions& directions, const GroupOf& group,
                                const msg::JournalPage& at, std::size_t per_page) {
  msg::JournalState s;
  s.tab = at.tab;
  if (at.search && !at.search->empty()) s.search = at.search;
  const std::string_view query = s.search ? std::string_view(*s.search) : std::string_view();
  auto entry_of = [&](const journal::Entry& e, const QuestNames& n) {
    return msg::JournalEntry{n.id, n.name, date(e.date), entry_kind(e.kind), {{text(e.quest, e.entry), std::nullopt}}};
  };
  s.page_count = 1;
  if (s.tab == msg::JournalTab::current || s.tab == msg::JournalTab::finished) {
    const bool current = s.tab == msg::JournalTab::current;
    for (const auto& q : journal::index(log)) {  // most recently written first
      if ((q.status == journal::Status::active) != current) continue;
      const auto n = name(q.quest);
      bool hit = journal::matches(n.name, query);
      for (auto i : q.entries) hit = hit || journal::matches(text(log.entries[i].quest, log.entries[i].entry), query);
      if (!hit) continue;
      const auto g = group ? group(q.quest) : journal::Group{"Other quests", false};
      auto it = std::find_if(s.groups.begin(), s.groups.end(), [&](const msg::QuestGroup& x) { return x.label == g.label; });
      if (it == s.groups.end()) {
        s.groups.push_back({g.label, g.place ? msg::QuestGroupKind::place : msg::QuestGroupKind::questline, {}});
        it = s.groups.end() - 1;
      }
      it->quests.push_back({n.id, n.name, status(q.status), date(q.started), date(q.last)});
      ++s.matches;
      if (at.quest ? *at.quest == n.id : !s.quest) {  // the quest asked for, else the most recent listed
        msg::OpenQuest o{n.id, n.name, status(q.status), g.label, std::nullopt, {}};
        if (q.status == journal::Status::active && !q.entries.empty() && directions) {
          const auto& last = log.entries[q.entries.back()];
          o.directions = directions(last.quest, last.entry);
        }
        for (auto i = q.entries.rbegin(); i != q.entries.rend(); ++i) o.entries.push_back(entry_of(log.entries[*i], n));
        s.quest = std::move(o);
      }
    }
    if (at.quest && !s.quest && !s.groups.empty())  // asked for one not on this ribbon: open the most recent
      return journal_state(log, name, text, directions, group, {at.tab, at.page, std::nullopt, at.search}, per_page);
  } else if (s.tab == msg::JournalTab::all) {
    std::vector<const journal::Entry*> shown;
    for (const auto& e : log.entries)
      if (journal::matches(text(e.quest, e.entry), query) || journal::matches(name(e.quest).name, query))
        shown.push_back(&e);
    s.matches = std::int64_t(shown.size());
    per_page = std::max<std::size_t>(per_page, 1);
    s.page_count = std::int64_t(std::max<std::size_t>(1, (shown.size() + per_page - 1) / per_page));
    s.page = std::clamp<std::int64_t>(at.page, 0, s.page_count - 1);
    const auto from = std::size_t(s.page) * per_page;
    for (std::size_t i = from; i < shown.size() && i < from + per_page; ++i)
      s.entries.push_back(entry_of(*shown[i], name(shown[i]->quest)));
  }
  return s;
}

journal::Group entry_group(journal::QuestId q) {
  const auto* t = journal::quest_text(q);
  return t ? journal::group_of(*t) : journal::Group{"Other quests", false};
}

std::string entry_text(journal::QuestId q, journal::EntryId e) {
  const auto* t = journal::stage_text(q, e);
  return t ? std::string(t->log) : std::string();
}

std::optional<std::string> entry_directions(journal::QuestId q, journal::EntryId e) {
  const auto* t = journal::stage_text(q, e);
  if (!t || t->directions.empty()) return std::nullopt;
  return std::string(t->directions);
}

// --- the probe ---------------------------------------------------------------------------------------------------

msg::DialogueState probe_dialogue(std::string speaker_id, std::string speaker_name, std::size_t topics) {
  msg::DialogueState s;
  s.speaker = {std::move(speaker_id), std::move(speaker_name)};
  s.entries.push_back({msg::DialogueEntryKind::greeting, std::nullopt,
                       {{"The 1.2 probe window: " + std::to_string(topics) + " topics to scroll and filter.", {}}}});
  for (std::size_t i = 1; i <= topics; ++i) {
    char label[16];
    std::snprintf(label, sizeof label, "Topic %03zu", i);
    s.topics.push_back({"topic.probe-" + std::to_string(i), label});
  }
  s.disposition = {50, msg::DispositionBand::mid};
  s.can_leave = true;
  return s;
}

std::optional<std::string> close_intent(std::string_view v, const CloseControl& c, bool conversation_open) {
  const bool any = c.cancel || c.tween || c.journal;
  if ((v == "journal" && any) || (v == "chart" && (any || c.quick_map)) || (v == "magic" && (any || c.quick_magic)) ||
      ((v == "system" || v == "wait" || v == "inventory" || v == "charsheet") && any))
    return R"({"type":"view.close","v":1,"body":{"view":")" + std::string(v) + R"("}})";
  if (v == "dialogue" && any)
    return conversation_open ? std::string(R"({"type":"dialogue.goodbye","v":1,"body":{}})")
                             : std::string(R"({"type":"view.close","v":1,"body":{"view":"dialogue"}})");
  return std::nullopt;
}

namespace {
std::string untagged_trimmed(std::string_view s) {
  std::string out;
  bool tag = false;
  for (char ch : s) {
    if (ch == '<') tag = true;
    else if (ch == '>') tag = false;
    else if (!tag && ch != '\r') out += ch;
  }
  const auto a = out.find_first_not_of(" \t"), b = out.find_last_not_of(" \t");
  return a == std::string::npos ? std::string{} : out.substr(a, b - a + 1);
}
}  // namespace

std::optional<PromptText> prompt_from_activate_text(std::string_view text, std::string_view name) {
  const auto nl = text.find('\n');
  PromptText p{untagged_trimmed(text.substr(0, nl)),
               nl == std::string_view::npos ? std::string{} : untagged_trimmed(text.substr(nl + 1))};
  if (p.verb.empty()) return std::nullopt;
  if (p.target.empty()) p.target = untagged_trimmed(name);
  return p;
}

bool offers_talk(const ActorAt& a) { return !a.dead && !a.fighting_player; }

std::optional<PromptText> actor_prompt(std::optional<PromptText> engine, const ActorAt& a) {
  if (a.fighting_player && !a.dead) return std::nullopt;
  if (a.dead && engine) engine->verb = "Search";
  return engine;
}

bool ClosePressGuard::swallow(std::uint32_t key, bool down, bool up, bool modal_open) {
  const auto it = std::find(held_.begin(), held_.end(), key);
  if (down) {
    if (it == held_.end() && modal_open) held_.push_back(key);  // pressed inside a view: the game never gets its end
    return false;  // the view's own input path handles the press itself
  }
  if (it == held_.end()) return false;
  if (up) held_.erase(it);
  return true;  // a repeat or the release of a press that began in a view
}

}  // namespace argonia::core::views
