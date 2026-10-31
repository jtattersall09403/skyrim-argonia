#include "argonia/core/journal.h"

#include <algorithm>
#include <utility>

namespace argonia::core::journal {

bool append(Log& log, QuestId q, EntryId e, GameDate date, Kind kind) {
  for (const auto& x : log.entries)
    if (x.quest == q && (x.entry == e || x.kind != Kind::progress)) return false;
  log.entries.push_back({q, e, date, kind});
  return true;
}

std::vector<QuestLine> index(const Log& log) {
  std::vector<QuestLine> out;
  std::vector<std::size_t> last_write;
  for (std::size_t i = 0; i < log.entries.size(); ++i) {
    const auto& e = log.entries[i];
    auto it = std::find_if(out.begin(), out.end(), [&](const QuestLine& l) { return l.quest == e.quest; });
    if (it == out.end()) {
      out.push_back({e.quest, Status::active, e.date, e.date, {}});
      last_write.push_back(i);
      it = out.end() - 1;
    }
    it->entries.push_back(i);
    it->last = e.date;
    last_write[std::size_t(it - out.begin())] = i;
    if (e.kind == Kind::complete) it->status = Status::complete;
    if (e.kind == Kind::fail) it->status = Status::failed;
  }
  std::vector<std::size_t> order(out.size());
  for (std::size_t i = 0; i < order.size(); ++i) order[i] = i;
  std::stable_sort(order.begin(), order.end(), [&](std::size_t a, std::size_t b) { return last_write[a] > last_write[b]; });
  std::vector<QuestLine> sorted;
  for (auto i : order) sorted.push_back(std::move(out[i]));
  return sorted;
}

const gen::JournalStageText* stage_text(QuestId q, EntryId stage) {
  auto it = std::lower_bound(gen::kJournalStages.begin(), gen::kJournalStages.end(), std::pair{q, stage},
                             [](const gen::JournalStageText& t, std::pair<QuestId, EntryId> k) {
                               return std::pair{t.quest, t.stage} < k;
                             });
  return it != gen::kJournalStages.end() && it->quest == q && it->stage == stage ? &*it : nullptr;
}

std::span<const gen::JournalObjectiveText> objectives(const gen::JournalStageText& t) {
  return std::span(gen::kJournalObjectives).subspan(t.first_objective, t.objective_count);
}

std::optional<Notice> notify(Notices& n, NoticeCause cause, std::string_view quest, std::int32_t mark, double now) {
  for (const auto& x : n.recent)
    if (x.quest == quest && now - x.at >= 0 && now - x.at < kNoticeMerge) return std::nullopt;
  Notice out{++n.seq, now, cause, std::string(quest), mark};
  n.recent.push_back(out);
  live(n, now);
  return out;
}

void hide(Notices& n, double now) {
  if (!n.hidden_at) n.hidden_at = now;
}

void show(Notices& n, double now) {
  if (!n.hidden_at) return;
  for (auto& x : n.recent) x.at = now - (std::max)(0.0, *n.hidden_at - x.at);
  n.hidden_at.reset();
}

std::vector<Notice> live(Notices& n, double now) {
  if (n.hidden_at) return n.recent;  // frozen while our HUD is hidden
  std::erase_if(n.recent, [&](const Notice& x) { return now - x.at >= kNoticeLife || now < x.at; });
  return n.recent;
}

cosave::Bytes encode(const Log& log) {
  cosave::Writer w;
  w.u32(std::uint32_t(log.entries.size()));
  for (const auto& e : log.entries) {
    w.u32(e.quest); w.u32(e.entry);
    w.i32(e.date.year); w.i32(e.date.month); w.i32(e.date.day); w.f64(e.date.hour);
    w.u8(std::uint8_t(e.kind));
  }
  return w.take();
}

std::optional<Log> decode(std::span<const std::uint8_t> b) {
  cosave::Reader r(b);
  auto n = r.u32();
  if (!n) return std::nullopt;
  Log log;
  for (std::uint32_t i = 0; i < *n; ++i) {
    auto q = r.u32(); auto e = r.u32();
    auto y = r.i32(); auto m = r.i32(); auto d = r.i32(); auto h = r.f64();
    auto k = r.u8();
    if (!q || !e || !y || !m || !d || !h || !k || *k > std::uint8_t(Kind::fail)) return std::nullopt;
    log.entries.push_back({*q, *e, {*y, *m, *d, *h}, Kind(*k)});
  }
  if (!r.done()) return std::nullopt;
  return log;
}

}  // namespace argonia::core::journal
