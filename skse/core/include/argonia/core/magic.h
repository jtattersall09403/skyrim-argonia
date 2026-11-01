// Dependency mods' forms restated at data load (1.12; lane-1.12-magic.md): the rename and school rules over
// gen::kModForms. Pure: ArgoniaCore resolves each row's form and applies what these return.
#pragma once
#include "argonia/core/messages.h"
#include "argonia/core/tables_magic.h"

#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace argonia::core::magic {

using gen::ModFormRow;

// Every row of a plugin (exact, case-insensitive file name), in table order.
std::vector<const ModFormRow*> rows_of(std::string_view plugin);
// The row of a form, if any.
const ModFormRow* find(std::string_view plugin, std::uint32_t local_id);

// The name to set: the row's name, or none to keep the mod's.
std::optional<std::string_view> rename(const ModFormRow& r);
// The description to set (MGEF, MESG): the row's, or none.
std::optional<std::string_view> redescribe(const ModFormRow& r);
// The magic skill actor value to give an effect whose current one is `current`: the row school's Skyrim actor value
// when it has one and differs; none keeps the mod's (no school, not an MGEF, or a school with no Skyrim actor value).
std::optional<std::string_view> school_av(const ModFormRow& r, std::string_view current);

// The rows whose school no Skyrim actor value carries (Mysticism): they stay under the mod's school.
std::vector<const ModFormRow*> unshown_schools();

// --- our magic pane (1.12, lane-1.12-magicpane): Morrowind's spell list --------------------------------------------
// An effect's Morrowind school: its mod_form row's school when the row gives one (Mysticism's 21 effects), else the
// school of the Skyrim magic skill it carries ("Alteration" ... "Restoration", after the data-load moves); none for an
// effect with no magic skill.
std::optional<msg::MagicSchool> school_of(const ModFormRow* effect_row, std::string_view effect_av);
// The heading the player reads.
std::string_view school_heading(msg::MagicSchool s);

// One spell or power the player knows, as ArgoniaCore reads it from the engine.
struct Known {
  std::string id, name;          // 8 hex digits; the engine's name (our restated one where mod_form gives it)
  std::int64_t cost = 0;         // the engine's magicka cost for the player
  bool power = false;            // a power or lesser power (the voice slot)
  std::optional<msg::MagicSchool> school;  // from school_of over its effects, costliest first
  bool left = false, right = false, voice = false;  // where it is readied now
};
// The school a spell with none of its effects on a magic skill is listed under (logged by ArgoniaCore).
inline constexpr msg::MagicSchool kNoSchool = msg::MagicSchool::alteration;

// The pane: powers by name; then all six schools in Morrowind's order (alteration, conjuration, destruction,
// illusion, mysticism, restoration), each school's spells by name (case-insensitive, then by id); a spell known twice
// (race and added) once; the active effects as given.
msg::MagicState pane_state(std::vector<Known> known, std::vector<msg::MagicActive> effects,
                           std::optional<std::string> notice = std::nullopt);

// An active effect's detail line: "12 pts, 30 s" (pts left out at 1 or less, a flag effect; s when none left).
std::optional<std::string> active_detail(double magnitude, double seconds_left);

// What a magic.equip asks, checked: a power goes only to the voice slot and a spell only to a hand. The refusal's
// words for the pane's notice, or none when the equip may go ahead.
std::optional<std::string> equip_refusal(const Known& k, msg::Hand hand);
// The intent's spell among the known ones, by its id (case-insensitive hex).
const Known* find_known(const std::vector<Known>& known, std::string_view id);

// A trader's dependency-mod stock rows (trade_class_mod_stock), in table order.
std::vector<const gen::ModStockRow*> stock_of(std::string_view npc);

}  // namespace argonia::core::magic
