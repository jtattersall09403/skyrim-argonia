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
  const auto first = on_day(0, 1, std::nullopt);
  CHECK(first && first->season == Season::dry && first->write.size() == gen::kWeatherChances.size());
  CHECK(on_day(0, 2, Season::dry)->write.empty());
  CHECK(on_day(11, 31, Season::dry)->season == Season::wet && !on_day(11, 31, Season::dry)->write.empty());
  // a date the calendar lacks is refused, never read as the first day (which would write the dry chances)
  CHECK(on_day(12, 1, Season::wet).error() == DateError::bad_month);
  CHECK(on_day(-1, 1, std::nullopt).error() == DateError::bad_month);
  CHECK(on_day(1, 29, Season::wet).error() == DateError::bad_day);
  CHECK(on_day(0, 0, std::nullopt).error() == DateError::bad_day);
  // mist regimes: their chance inside their hours, 0 outside; radiation mist is a dawn weather and peaks in the dry
  CHECK(!gen::kMistRegimes.empty());
  for (const auto& m : gen::kMistRegimes) {
    for (auto s : {Season::dry, Season::hatching, Season::wet}) {
      const auto in = mist_settings(s, m.first_hour + 0.5), out = mist_settings(s, m.end_hour + 0.01);
      for (std::size_t i = 0; i < in.size(); ++i)
        if (in[i].global == m.global) {
          CHECK(in[i].value == m.chance[static_cast<std::size_t>(s)]);
          CHECK(out[i].value == 0);
        }
    }
    if (m.global == "ARG_WMist_radiation") {
      CHECK(m.first_hour <= 6 && m.end_hour <= 10);
      CHECK(m.chance[static_cast<std::size_t>(Season::dry)] > m.chance[static_cast<std::size_t>(Season::wet)]);
    }
  }
  CHECK(mist_settings(Season::dry, 12.0).size() == gen::kMistRegimes.size());
  return argonia::test::failures;
}
