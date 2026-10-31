// L2: the restated forms of Magic Expanded (1.12): the rename rows, the school table (poison to Destruction; Mysticism
// recorded but shown under the mod's school, no Skyrim actor value), and the guards (no school off an MGEF, no move
// to the school the effect already has).
#include "check.h"
#include "argonia/core/magic.h"

#include <string_view>

using namespace argonia::core;
using namespace argonia::core::magic;

int main() {
  const auto all = rows_of("Magic.esp");
  CHECK(all.size() == gen::kModForms.size());
  CHECK(rows_of("magic.ESP").size() == all.size());  // file names compare case-insensitively
  CHECK(rows_of("Skyrim.esm").empty());

  // The Nordic shout's name on the force effects becomes the spells' own.
  const auto* force = find("Magic.esp", 0x000AC2);
  CHECK(force && rename(*force) == std::string_view{"Force"});
  // The snowstorm spell is a hailstorm: its spell, its effect's name and description, and its tome.
  const auto* storm = find("Magic.esp", 0x000973);
  CHECK(storm && rename(*storm) == std::string_view{"Marsh Squall"});
  CHECK(storm && redescribe(*storm) && redescribe(*storm)->find("squall") != std::string_view::npos);
  const auto* tome = find("Magic.esp", 0x00089D);
  CHECK(tome && rename(*tome) == std::string_view{"Spell Tome: Marsh Squall"} && !redescribe(*tome));
  // A description-only row keeps the mod's name.
  const auto* raise = find("Magic.esp", 0x0009A3);
  CHECK(raise && !rename(*raise) && redescribe(*raise));

  // Poison: Restoration in the mod, Destruction in Morrowind.
  const auto* viper = find("Magic.esp", 0x00091E);
  CHECK(viper && viper->school == gen::SkillId::destruction);
  CHECK(viper && school_av(*viper, "Restoration") == std::string_view{"Destruction"});
  CHECK(viper && !school_av(*viper, "destruction"));  // already there: no move
  // Mysticism: recorded, no Skyrim actor value, so the effect stays under the mod's school.
  const auto* recall = find("Magic.esp", 0x000A8D);
  CHECK(recall && recall->school == gen::SkillId::mysticism && recall->school_av.empty());
  CHECK(recall && !school_av(*recall, "Alteration"));
  const auto unshown = unshown_schools();
  CHECK(unshown.size() == 21);
  for (const auto* r : unshown) CHECK(r->school == gen::SkillId::mysticism);

  // Every row: a school only on an MGEF, a school's actor value one of the five, and something to do.
  for (const auto& r : gen::kModForms) {
    CHECK(!r.school || r.form_type == "MGEF");
    CHECK(r.school_av.empty() || r.school_av == "Alteration" || r.school_av == "Conjuration" ||
          r.school_av == "Destruction" || r.school_av == "Illusion" || r.school_av == "Restoration");
    CHECK(rename(r) || redescribe(r) || r.school);
    CHECK(find(r.plugin, r.local_id) == &r);  // ids unique
  }
  CHECK(!find("Magic.esp", 0x000001));
  return TEST_MAIN_RESULT("core.magic");
}
