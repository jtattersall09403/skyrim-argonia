#include "argonia/core/weather.h"

namespace argonia::core::weather {

std::optional<int> day_of_year(int month, int day) {
  if (month < 0 || month >= static_cast<int>(gen::kMonthDays.size())) return std::nullopt;
  if (day < 1 || day > gen::kMonthDays[static_cast<std::size_t>(month)]) return std::nullopt;
  int n = 0;
  for (int m = 0; m < month; ++m) n += gen::kMonthDays[static_cast<std::size_t>(m)];
  return n + day - 1;
}

Season season_of(int d) {
  for (const auto& w : gen::kSeasonWindows)
    if (d >= w.first_day && d < w.end_day) return w.season;
  return gen::kSeasonWindows.back().season;  // past the year's end: its last season
}

std::vector<Setting> settings(Season s) {
  std::vector<Setting> out;
  out.reserve(gen::kWeatherChances.size());
  for (const auto& c : gen::kWeatherChances) out.push_back({c.global, c.chance[static_cast<std::size_t>(s)]});
  return out;
}

std::expected<DayChange, DateError> on_day(int month, int day, std::optional<Season> last) {
  if (month < 0 || month >= static_cast<int>(gen::kMonthDays.size())) return std::unexpected(DateError::bad_month);
  const auto d = day_of_year(month, day);
  if (!d) return std::unexpected(DateError::bad_day);
  const Season s = season_of(*d);
  if (last && *last == s) return DayChange{s, {}};
  return DayChange{s, settings(s)};
}

}  // namespace argonia::core::weather
