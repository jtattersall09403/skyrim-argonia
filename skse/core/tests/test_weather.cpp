// L2: the season of a day and the weather-chance globals it sets (2.W3; regions/season.py writes the tables).
#include "check.h"
#include "argonia/core/weather.h"

using namespace argonia::core::weather;
namespace gen = argonia::core::gen;

int main() {
  CHECK(day_of_year(0, 1) == 0);
  CHECK(day_of_year(11, 31) == 364);
  CHECK(!day_of_year(1, 29) && !day_of_year(12, 1) && !day_of_year(0, 0));
  // the windows tile the year once, in order
  int at = 0;
  for (const auto& w : gen::kSeasonWindows) { CHECK(w.first_day == at && w.end_day > w.first_day); at = w.end_day; }
  CHECK(at == 365);
  CHECK(season_of(0) == gen::kSeasonWindows.front().season && season_of(364) == gen::kSeasonWindows.back().season);
  // every global is set every time; dry haze is ruled out of the wet season, storms grow in it
  const auto wet = settings(Season::wet), dry = settings(Season::dry);
  CHECK(wet.size() == gen::kWeatherChances.size() && !wet.empty());
  for (std::size_t i = 0; i < wet.size(); ++i) {
    if (wet[i].global.ends_with("tannin_haze")) CHECK(wet[i].value == 0 && dry[i].value > 0);
    if (wet[i].global == "ARG_WChance_coastal_rain") CHECK(wet[i].value > dry[i].value);
  }
  // a day in the same season writes nothing; the turn of a season writes the full set
  const DayChange first = on_day(0, 1, std::nullopt);
  CHECK(first.season == Season::dry && first.write.size() == gen::kWeatherChances.size());
  CHECK(on_day(0, 2, Season::dry).write.empty());
  CHECK(on_day(11, 31, Season::dry).season == Season::wet && !on_day(11, 31, Season::dry).write.empty());
  return argonia::test::failures;
}
