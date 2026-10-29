#include "bridge_protocol.h"

#include <cstdio>

namespace argonia::bridge {

bool token_matches(std::string_view expected, std::string_view given) {
  if (expected.size() != kTokenHexChars || given.size() != expected.size()) return false;
  unsigned diff = 0;
  for (std::size_t i = 0; i < expected.size(); ++i) diff |= unsigned(expected[i] ^ given[i]);
  return diff == 0;
}

std::variant<Request, Refusal> parse(std::string_view line, std::string_view expected_token) {
  if (line.size() > kMaxLine) return Refusal{"request longer than 4096 bytes"};
  while (!line.empty() && (line.back() == '\n' || line.back() == '\r')) line.remove_suffix(1);
  std::vector<std::string_view> parts;
  std::size_t start = 0;
  while (start <= line.size()) {
    std::size_t end = line.find(' ', start);
    if (end == std::string_view::npos) end = line.size();
    parts.push_back(line.substr(start, end - start));
    start = end + 1;
  }
  if (parts.empty() || !token_matches(expected_token, parts[0])) return Refusal{"bad token"};
  if (parts.size() < 2 || parts[1].empty()) return Refusal{"no command"};
  Request r{std::string(parts[1]), {}};
  for (std::size_t i = 2; i < parts.size(); ++i) r.args.emplace_back(parts[i]);
  return r;
}

std::string json_escape(std::string_view s) {
  std::string out;
  out.reserve(s.size() + 2);
  for (char c : s) {
    switch (c) {
      case '"': out += "\\\""; break;
      case '\\': out += "\\\\"; break;
      case '\n': out += "\\n"; break;
      case '\r': out += "\\r"; break;
      case '\t': out += "\\t"; break;
      default:
        if (static_cast<unsigned char>(c) < 0x20) {
          char buf[8];
          std::snprintf(buf, sizeof buf, "\\u%04x", unsigned(static_cast<unsigned char>(c)));
          out += buf;
        } else {
          out += c;
        }
    }
  }
  return out;
}

std::string reply_ok(std::string_view cmd, std::string_view result_json) {
  return "{\"ok\":true,\"cmd\":\"" + json_escape(cmd) + "\",\"result\":" + std::string(result_json) + "}\n";
}

std::string reply_error(std::string_view cmd, std::string_view error) {
  return "{\"ok\":false,\"cmd\":\"" + json_escape(cmd) + "\",\"error\":\"" + json_escape(error) + "\"}\n";
}

}  // namespace argonia::bridge
