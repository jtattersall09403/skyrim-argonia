// L2: the restated forms of Magic Expanded (1.12): the rename rows, the school table (poison to Destruction; Mysticism
// recorded but shown under the mod's school, no Skyrim actor value), and the guards (no school off an MGEF, no move
// to the school the effect already has).
#include "check.h"
#include "argonia/core/magic.h"

#include <string_view>
#include <variant>
#include <vector>

using namespace argonia::core;
using namespace argonia::core::magic;

namespace {
bool ac_test_encodes(const msg::MagicState& s) { return msg::encode(s).has_value(); }
}  // namespace

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

  // --- our magic pane (lane-1.12-magicpane) ---
  // Schools: the row's (Mark's and Recall's effects are Mysticism, which no Skyrim skill carries), else the skill's.
  using msg::MagicSchool;
  CHECK(school_of(find("Magic.esp", 0x000A8B), "Alteration") == MagicSchool::mysticism);
  CHECK(school_of(find("Magic.esp", 0x000A8D), "Alteration") == MagicSchool::mysticism);
  CHECK(school_of(nullptr, "Destruction") == MagicSchool::destruction);
  CHECK(school_of(nullptr, "restoration") == MagicSchool::restoration);
  CHECK(!school_of(nullptr, "None") && !school_of(nullptr, ""));
  CHECK(school_heading(MagicSchool::mysticism) == "Mysticism");

  std::vector<Known> known = {
      {"FE012A8E", "Recall", 250, false, MagicSchool::mysticism},
      {"FE012A8C", "Mark", 500, false, MagicSchool::mysticism},
      {"00012FCD", "Flames", 14, false, MagicSchool::destruction, true, false},
      {"FE01291F", "Viperbolt", 98, false, MagicSchool::destruction, false, true},
      {"0002F3B8", "healing", 12, false, MagicSchool::restoration},
      {"00012FCD", "Flames", 14, false, MagicSchool::destruction, true, false},  // known twice (race and added)
      {"000E40C9", "Histskin", 0, true, std::nullopt, false, false, true},
      {"FE0129AA", "Oddity", 5, false, std::nullopt},  // no effect on a magic skill
  };
  const auto st = pane_state(known, {{"Fortify Health", active_detail(10, 59.6)}}, std::nullopt);
  CHECK(st.powers.size() == 1 && st.powers[0].name == "Histskin" && st.powers[0].readied);
  CHECK(st.groups.size() == 6);
  const char* order[] = {"Alteration", "Conjuration", "Destruction", "Illusion", "Mysticism", "Restoration"};
  for (int i = 0; i < 6; ++i) CHECK(st.groups[std::size_t(i)].name == order[i]);
  const auto& mys = st.groups[4].spells;
  CHECK(mys.size() == 2 && mys[0].name == "Mark" && mys[1].name == "Recall" && mys[0].cost == 500);
  const auto& des = st.groups[2].spells;
  CHECK(des.size() == 2 && des[0].name == "Flames" && des[0].left && !des[0].right && des[1].right);  // once
  CHECK(st.groups[5].spells.size() == 1 && st.groups[5].spells[0].name == "healing");  // case-insensitive order
  CHECK(st.groups[0].spells.size() == 1 && st.groups[0].spells[0].name == "Oddity");  // kNoSchool
  CHECK(st.groups[1].spells.empty() && st.groups[3].spells.empty());  // empty schools still head the list
  CHECK(st.effects.size() == 1 && st.effects[0].detail == std::optional<std::string>{"10 pts, 60 s"});
  CHECK(!active_detail(1, 0) && !active_detail(0, 0) && active_detail(0, 5) == std::optional<std::string>{"5 s"});
  CHECK(ac_test_encodes(st));

  // Equip: a spell to a hand, a power to the voice.
  CHECK(!equip_refusal(known[0], msg::Hand::right) && !equip_refusal(known[0], msg::Hand::left));
  CHECK(equip_refusal(known[0], msg::Hand::voice));
  CHECK(!equip_refusal(known[6], msg::Hand::voice) && equip_refusal(known[6], msg::Hand::left));
  CHECK(find_known(known, "fe012a8e") == &known[0] && !find_known(known, "00000001"));
  const auto in = msg::decode_intent(R"({"type":"magic.equip","v":1,"body":{"spell":"FE012A8E","hand":"right"}})");
  CHECK(in && std::holds_alternative<msg::MagicEquip>(*in) && std::get<msg::MagicEquip>(*in).hand == msg::Hand::right);
  CHECK(!msg::decode_intent(R"({"type":"magic.equip","v":1,"body":{"spell":"FE012A8E","hand":"both"}})"));

  // Livia's stock: Magic Expanded's tomes, Mark and Recall among them, by Magic.esp's own ids.
  const auto stock = stock_of("npc.imperial-fringe.claywater-station.well-keeper");
  CHECK(stock.size() >= 12);
  bool sold_mark = false, sold_recall = false;
  for (const auto* r : stock) {
    CHECK(r->plugin == "Magic.esp" && r->count > 0);
    sold_mark |= r->local_id == 0x000804;
    sold_recall |= r->local_id == 0x000803;
  }
  CHECK(sold_mark && sold_recall && stock_of("npc.nobody").empty());
  return TEST_MAIN_RESULT("core.magic");
}
