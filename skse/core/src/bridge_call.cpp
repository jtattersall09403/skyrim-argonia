#include "argonia/core/bridge_call.h"

#include <array>

namespace argonia::core::bridge_call {

namespace {
using R = Returns;
constexpr std::array kNatives{
    Native{"Version", false, R::Text},          Native{"SaveCount", false, R::Int},
    Native{"ViewIntent", true, R::Json},        Native{"ViewState", true, R::Json},
    Native{"GetAttribute", true, R::Float},     Native{"Families", false, R::TextList},
    Native{"FamilyDigest", true, R::Text},      Native{"RouterLog", false, R::TextList},
    Native{"GetFlag", true, R::Bool},           Native{"KnowsTopic", true, R::Bool},
    Native{"GetDisposition", true, R::Int},     Native{"JournalEntries", false, R::TextList},
    Native{"RestNotice", false, R::Text},       Native{"SittingIntent", true, R::Json},
    Native{"GetVastei", false, R::Float},       Native{"GetPendingLevels", false, R::Int},
    Native{"GetLevel", false, R::Int},          Native{"GetSkill", true, R::Float},
    Native{"PileState", false, R::Text},        Native{"WakePoint", false, R::Text},
    Native{"SittingOpen", false, R::Bool},
    // Bridge only, no Papyrus twin: the 1.2 §0 probe's window (its fixture, never what the probe measures) and the
    // views' binding state.
    Native{"ViewProbe", true, R::Json},         Native{"Views", false, R::TextList},
};

std::string wrap(std::string_view native, json::Value v) {
  return json::dump(json::Value::object({{"native", json::Value::string(std::string(native))}, {"value", std::move(v)}}));
}
}  // namespace

std::span<const Native> natives() { return kNatives; }

const Native* find(std::string_view name) {
  for (const auto& n : kNatives)
    if (n.name == name) return &n;
  return nullptr;
}

std::optional<std::string> refuse(std::string_view name, bool has_arg) {
  const auto* n = find(name);
  if (!n) return "not a callable native: " + std::string(name) + " (the reads of ArgoniaCore.psc and the view intents only)";
  if (n->takes_text && !has_arg) return std::string(name) + " takes one argument";
  if (!n->takes_text && has_arg) return std::string(name) + " takes no argument";
  return std::nullopt;
}

std::string encode_text(std::string_view native, std::string_view s) { return wrap(native, json::Value::string(std::string(s))); }
std::string encode_number(std::string_view native, double v) { return wrap(native, json::Value::number(v)); }
std::string encode_bool(std::string_view native, bool b) { return wrap(native, json::Value::boolean(b)); }

std::string encode_list(std::string_view native, const std::vector<std::string>& items) {
  json::Array a;
  for (const auto& s : items) a.push_back(json::Value::string(s));
  return wrap(native, json::Value::array(std::move(a)));
}

std::string encode_json(std::string_view native, std::string_view json_text) {
  if (json_text.empty()) return wrap(native, json::Value());
  auto v = json::parse(json_text);
  return wrap(native, v ? std::move(*v) : json::Value::string(std::string(json_text)));
}

}  // namespace argonia::core::bridge_call
