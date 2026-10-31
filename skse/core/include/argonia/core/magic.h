// Dependency mods' forms restated at data load (1.12; lane-1.12-magic.md): the rename and school rules over
// gen::kModForms. Pure: ArgoniaCore resolves each row's form and applies what these return.
#pragma once
#include "argonia/core/tables_magic.h"

#include <optional>
#include <span>
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

}  // namespace argonia::core::magic
