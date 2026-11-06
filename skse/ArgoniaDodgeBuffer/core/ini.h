#pragma once
// A tiny ini reader (key=value, ';' and '#' comments, [sections] ignored) and the plugin's settings. No engine types.
#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <string>
#include <string_view>
#include <vector>

namespace argonia::dodgebuffer {

inline std::string trim(std::string_view s) {
  while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.remove_prefix(1);
  while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.remove_suffix(1);
  return std::string(s);
}

inline std::string lower(std::string_view s) {
  std::string o(s);
  std::transform(o.begin(), o.end(), o.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
  return o;
}

inline std::vector<std::string> split_list(std::string_view s) {
  std::vector<std::string> out;
  std::size_t at = 0;
  while (at <= s.size()) {
    auto comma = s.find(',', at);
    if (comma == std::string_view::npos) comma = s.size();
    auto item = trim(s.substr(at, comma - at));
    if (!item.empty()) out.push_back(item);
    at = comma + 1;
  }
  return out;
}

struct Settings {
  bool enabled = true;
  double buffer_seconds = 0.6;
  double power_hold_seconds = 0.4;
  std::string user_event = "Right Attack/Block";
  std::vector<std::string> start_events{"TKDR_DodgeStart"};
  std::vector<std::string> end_events{"TKDR_DodgeEnd", "TKDodgeStop", "tailCombatIdle"};
  std::string attack_event = "attackStart";
  std::string power_event = "attackPowerStartInPlace";
};

// Reads `text` over `s`: an absent or unreadable key keeps the value already in `s`; a negative or non-numeric
// number is refused (kept). Returns the keys it did not recognise, for the log.
inline std::vector<std::string> parse_ini(std::string_view text, Settings& s) {
  std::vector<std::string> unknown;
  auto number = [](const std::string& v, double& into) {
    char* end = nullptr;
    const double d = std::strtod(v.c_str(), &end);
    if (end != v.c_str() && *end == '\0' && d >= 0.0) into = d;
  };
  std::size_t at = 0;
  while (at < text.size()) {
    auto nl = text.find('\n', at);
    if (nl == std::string_view::npos) nl = text.size();
    const std::string line = trim(text.substr(at, nl - at));
    at = nl + 1;
    if (line.empty() || line[0] == ';' || line[0] == '#' || line[0] == '[') continue;
    const auto eq = line.find('=');
    if (eq == std::string::npos) continue;
    const std::string key = lower(trim(std::string_view(line).substr(0, eq)));
    const std::string val = trim(std::string_view(line).substr(eq + 1));
    if (key == "benabled") s.enabled = val != "0" && lower(val) != "false" && !val.empty();
    else if (key == "fbufferseconds") number(val, s.buffer_seconds);
    else if (key == "fpowerholdseconds") number(val, s.power_hold_seconds);
    else if (key == "suserevent") { if (!val.empty()) s.user_event = val; }
    else if (key == "sdodgestartevents") { auto l = split_list(val); if (!l.empty()) s.start_events = l; }
    else if (key == "sdodgeendevents") { auto l = split_list(val); if (!l.empty()) s.end_events = l; }
    else if (key == "sattackevent") { if (!val.empty()) s.attack_event = val; }
    else if (key == "spowerevent") { if (!val.empty()) s.power_event = val; }
    else unknown.push_back(key);
  }
  return unknown;
}

}  // namespace argonia::dodgebuffer
