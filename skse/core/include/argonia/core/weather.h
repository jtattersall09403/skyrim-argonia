// Weather by season (2.W3; native map G05.3): the REGN weather lists draw their chances from the ARG_WChance_*
// globals, and this rule says what each one holds on a given day. ArgoniaCore's adapter calls `on_day` when the game
// day changes and writes the globals it returns. The tables are generated (regions/season.py) from the world database.
#pragma once
#include "argonia/core/tables_weather.h"

#include <optional>
#include <string_view>
#include <vector>

namespace argonia::core::weather {

using gen::Season;

// The 0-based day of the year from Skyrim's GameMonth (0..11) and GameDay (1..31); nullopt when out of range.
std::optional<int> day_of_year(int month, int day);

Season season_of(int day_of_year);

struct Setting { std::string_view global; std::uint8_t value; };
// Every global's value in a season (the full set, so a load or a skipped week converges in one call).
std::vector<Setting> settings(Season s);

// The day changed: the season it is now, and the settings to write when the season differs from `last`
// (none when it is the same season: the globals already hold it).
struct DayChange { Season season; std::vector<Setting> write; };
DayChange on_day(int month, int day, std::optional<Season> last);

}  // namespace argonia::core::weather
