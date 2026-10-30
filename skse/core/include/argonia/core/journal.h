// The journal log (2.12 §b, native map G22.3): dated entries in the order they were written, and the quest index
// the journal view lists. Text lives in the records; the log holds ids and dates only.
#pragma once
#include "argonia/core/cosave.h"

#include <compare>
#include <cstdint>
#include <optional>
#include <span>
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

inline constexpr std::uint32_t kJournalType = cosave::fourcc("JRNL");
cosave::Bytes encode(const Log& log);
std::optional<Log> decode(std::span<const std::uint8_t> b);

}  // namespace argonia::core::journal
