// A quest thing's native hook (1.4): activating the thing's activator, or reading its book, sets one flag of its
// quest. The table (generated/things.h, tools/argonia_world/thing_hooks.py from the thing_hook rows) is keyed by the
// world id of the record the thing is placed as; ArgoniaCore reads the activated or read form's world id and asks
// here, then sets the flag through the setFlag action.
#pragma once
#include "argonia/core/things_table.h"

#include <cstdint>
#include <string_view>

namespace argonia::core::things {

enum class Hook : std::uint8_t { activate, read };

// The thing table's row for this record met this way, or null (not a thing of a quest, or met the other way).
const gen::ThingHookRow* hook_for(std::string_view record, Hook how);

}  // namespace argonia::core::things
