// The dev bridge's `core <Native> [arg]` (1.7's first-place journey and soak): which ArgoniaCore natives a journey
// may call through ArgoniaBridge, and how their values travel. The reads of papyrus/ArgoniaCore.psc plus the two view
// intents (ViewIntent, SittingIntent: the view's own hand, until a click sends it); every setter and every native
// that takes a form is refused, so a journey can never set what it tests (loops rule 4).
// The call is an SKSE message from "ArgoniaBridge" to ArgoniaCore whose data is BridgeCore; ArgoniaCore's listener
// answers in it before the dispatch returns, as BridgeSuspend and BridgeGreeting do.
#pragma once
#include "argonia/core/cosave.h"
#include "argonia/core/json.h"

#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace argonia::core::bridge_call {

// What a native returns on the wire: Json is a JSON document held as text (a view's state); empty is null.
enum class Returns { Text, Int, Float, Bool, TextList, Json };

struct Native {
  std::string_view name;
  bool takes_text;  // one string argument (the rest of the request line, spaces kept)
  Returns returns;
};

// Every callable native, in papyrus/ArgoniaCore.psc's order.
std::span<const Native> natives();
const Native* find(std::string_view name);

// Nothing when the call may go; else the refusal in words (an unknown or refused native, a missing or extra arg).
std::optional<std::string> refuse(std::string_view name, bool has_arg);

// The value as the bridge's reply carries it: {"native":..,"value":..}. A Json value that does not parse travels as
// a string, so the reply is always valid JSON.
std::string encode_text(std::string_view native, std::string_view s);
std::string encode_number(std::string_view native, double v);
std::string encode_bool(std::string_view native, bool b);
std::string encode_list(std::string_view native, const std::vector<std::string>& items);
std::string encode_json(std::string_view native, std::string_view json_text);

inline constexpr std::uint32_t kBridgeCoreMessage = cosave::fourcc("CORE");
struct BridgeCore {
  char native[48] = {};
  char arg[4096] = {};
  bool has_arg = false;
  char json[65536] = {};
  char error[256] = {};
  bool ok = false;
};

}  // namespace argonia::core::bridge_call
