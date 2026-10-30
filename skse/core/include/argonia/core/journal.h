// The journal log (2.12 §b, native map G22.3): dated entries in the order they were written, and the quest index
// the journal view lists. Text lives in the records (generated/journal_text.h, from the quest rows); the log holds
// ids and dates only.
#pragma once
#include "argonia/core/cosave.h"
#include "argonia/core/journal_text.h"
#include "argonia/core/tables_conditions.h"

#include <compare>
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace argonia::core::journal {

using QuestId = std::uint32_t;  // the quest's world id key (FNV-1a 32, seam::key): stable across load orders
using EntryId = std::uint32_t;  // the stage whose log entry it is

struct GameDate {
  std::int32_t year = 0, month = 0, day = 0;
  double hour = 0;
  auto operator<=>(const GameDate&) const = default;
};

enum class Kind : std::uint8_t { progress, complete, fail };

struct Entry { QuestId quest; EntryId entry; GameDate date; Kind kind; bool operator==(const Entry&) const = default; };
struct Log { std::vector<Entry> entries; bool operator==(const Log&) const = default; };

// Adds the entry; false (and nothing added) when this quest's entry is already logged or the quest has ended.
bool append(Log& log, QuestId q, EntryId e, GameDate date, Kind kind = Kind::progress);

enum class Status : std::uint8_t { active, complete, failed };
struct QuestLine {
  QuestId quest;
  Status status;
  GameDate started, last;
  std::vector<std::size_t> entries;  // indices into Log::entries, oldest first
};
// One line per quest, most recently written first.
std::vector<QuestLine> index(const Log& log);

// The records' words for a quest's stage: its log entry, directions and objectives (gen::kJournalStages); null when
// the table has no such stage.
const gen::JournalStageText* stage_text(QuestId q, EntryId stage);
std::span<const gen::JournalObjectiveText> objectives(const gen::JournalStageText& t);

// The "journal updated" notice (game-10 §2): an entry logged at a stage, or a clue found (an objective completed),
// tells the player once, through the engine's own HUD notification and our HUD view's notice stack. A clue that
// sets a stage and that stage's entry land within moments of each other: one notice for both (kNoticeMerge).
inline constexpr std::string_view kNoticeText = "Journal updated";
inline constexpr double kNoticeMerge = gen::journal::notice_merge_seconds;  // real seconds: the same quest's merged
inline constexpr double kNoticeLife = gen::journal::notice_life_seconds;    // real seconds in the HUD's stack
enum class NoticeCause : std::uint8_t { entry, clue };
struct Notice {
  std::uint32_t seq;  // the notice's number this session: the HUD's notice id, so the view fades it once
  double at;          // real seconds when raised
  NoticeCause cause;
  std::string quest;  // the quest's world id
  std::int32_t mark;  // the stage (entry) or the objective index (clue)
  bool operator==(const Notice&) const = default;
};
struct Notices {
  std::vector<Notice> recent;  // oldest first
  std::uint32_t seq = 0;
};
// The notice to raise now, or nothing when the same quest raised one less than kNoticeMerge seconds ago.
std::optional<Notice> notify(Notices& n, NoticeCause cause, std::string_view quest, std::int32_t mark, double now);
// The notices still shown at `now` (younger than kNoticeLife), oldest first; older ones are dropped.
std::vector<Notice> live(Notices& n, double now);

inline constexpr std::uint32_t kJournalType = cosave::fourcc("JRNL");
cosave::Bytes encode(const Log& log);
std::optional<Log> decode(std::span<const std::uint8_t> b);

}  // namespace argonia::core::journal
