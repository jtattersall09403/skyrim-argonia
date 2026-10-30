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

msg::JournalState journal_state(const journal::Log& log, const std::function<QuestNames(journal::QuestId)>& name,
                                const std::function<std::string(journal::QuestId, journal::EntryId)>& text,
                                const msg::JournalPage& at, std::size_t per_page) {
  msg::JournalState s;
  s.tab = at.tab;
  s.quest_filter = at.quest_filter;
  for (const auto& q : journal::index(log)) {
    const auto n = name(q.quest);
    s.quests.push_back({n.id, n.name, status(q.status), date(q.started), std::nullopt});
  }
  std::vector<const journal::Entry*> shown;
  for (const auto& e : log.entries)
    if (!at.quest_filter || name(e.quest).id == *at.quest_filter) shown.push_back(&e);
  per_page = std::max<std::size_t>(per_page, 1);
  const auto pages = std::max<std::size_t>(1, (shown.size() + per_page - 1) / per_page);
  s.page_count = std::int64_t(pages);
  s.page = std::clamp<std::int64_t>(at.page, 0, s.page_count - 1);
  if (s.tab == msg::JournalTab::entries) {
    const auto from = std::size_t(s.page) * per_page;
    for (std::size_t i = from; i < shown.size() && i < from + per_page; ++i) {
      const auto& e = *shown[i];
      const auto n = name(e.quest);
      s.entries.push_back({n.id, n.name, date(e.date), entry_kind(e.kind), {{text(e.quest, e.entry), std::nullopt}}});
    }
  }
  return s;
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

}  // namespace argonia::core::views
