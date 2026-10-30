#include "bridge_protocol.h"

#include <algorithm>
#include <charconv>
#include <cmath>
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

std::string rest(const Request& r, std::size_t from) {
  std::string out;
  for (std::size_t i = from; i < r.args.size(); ++i) {
    if (i > from) out += ' ';
    out += r.args[i];
  }
  return out;
}

std::optional<double> to_number(std::string_view s) {
  if (s.empty()) return std::nullopt;
  if (s.front() == '+') s.remove_prefix(1);
  double v = 0;
  auto [p, ec] = std::from_chars(s.data(), s.data() + s.size(), v);
  if (ec != std::errc{} || p != s.data() + s.size() || !std::isfinite(v)) return std::nullopt;
  return v;
}

std::optional<std::uint32_t> to_form_id(std::string_view s) {
  if (s.size() > 2 && s[0] == '0' && (s[1] == 'x' || s[1] == 'X')) s.remove_prefix(2);
  if (s.empty() || s.size() > 8) return std::nullopt;
  std::uint32_t v = 0;
  auto [p, ec] = std::from_chars(s.data(), s.data() + s.size(), v, 16);
  if (ec != std::errc{} || p != s.data() + s.size()) return std::nullopt;
  return v;
}

std::string json_number(double v) {
  if (!std::isfinite(v)) return "null";
  char buf[32];
  std::snprintf(buf, sizeof buf, "%.9g", v);
  return buf;
}

std::string json_string(std::string_view s) { return "\"" + json_escape(s) + "\""; }

void JsonObject::key(std::string_view k) {
  if (body_.size() > 1) body_ += ',';
  body_ += json_string(k);
  body_ += ':';
}
JsonObject& JsonObject::str(std::string_view k, std::string_view v) {
  key(k);
  body_ += json_string(v);
  return *this;
}
JsonObject& JsonObject::num(std::string_view k, double v) {
  key(k);
  body_ += json_number(v);
  return *this;
}
JsonObject& JsonObject::integer(std::string_view k, long long v) {
  key(k);
  body_ += std::to_string(v);
  return *this;
}
JsonObject& JsonObject::boolean(std::string_view k, bool v) {
  key(k);
  body_ += v ? "true" : "false";
  return *this;
}
JsonObject& JsonObject::raw(std::string_view k, std::string_view json) {
  key(k);
  body_ += json;
  return *this;
}
JsonObject& JsonObject::hex(std::string_view k, std::uint32_t id) {
  char buf[16];
  std::snprintf(buf, sizeof buf, "%08X", static_cast<unsigned>(id));
  return str(k, buf);
}

std::string console_delta(std::string_view before, std::string_view after) {
  if (after.substr(0, before.size()) == before) return std::string(after.substr(before.size()));
  // Trimmed at the front: anchor on the last line of `before` (it ends in \n when the console printed it).
  auto b = before;
  while (!b.empty() && b.back() == '\n') b.remove_suffix(1);
  auto nl = b.rfind('\n');
  auto last = nl == std::string_view::npos ? b : b.substr(nl + 1);
  if (!last.empty()) {
    auto at = after.rfind(last);
    if (at != std::string_view::npos) {
      auto tail = after.substr(at + last.size());
      if (!tail.empty() && tail.front() == '\n') tail.remove_prefix(1);
      return std::string(tail);
    }
  }
  return std::string(after);
}

bool console_refused(std::string_view out) {
  for (std::string_view w : {"Script command \"", "Missing parameter", "Compiled script not saved", "not found for parameter",
                             "Invalid ", "Unknown command"})
    if (out.find(w) != std::string_view::npos && (w != "Script command \"" || out.find("not found") != std::string_view::npos))
      return true;
  return false;
}

std::optional<std::uint16_t> scancode(std::string_view n) {
  struct Key {
    std::string_view name;
    std::uint16_t code;
  };
  static constexpr Key keys[] = {
      {"ESC", 0x01}, {"1", 0x02}, {"2", 0x03}, {"3", 0x04}, {"4", 0x05}, {"5", 0x06}, {"6", 0x07}, {"7", 0x08},
      {"8", 0x09}, {"9", 0x0A}, {"0", 0x0B}, {"TAB", 0x0F}, {"Q", 0x10}, {"W", 0x11}, {"E", 0x12}, {"R", 0x13},
      {"T", 0x14}, {"Y", 0x15}, {"U", 0x16}, {"I", 0x17}, {"O", 0x18}, {"P", 0x19}, {"ENTER", 0x1C},
      {"LCTRL", 0x1D}, {"A", 0x1E}, {"S", 0x1F}, {"D", 0x20}, {"F", 0x21}, {"G", 0x22}, {"H", 0x23}, {"J", 0x24},
      {"K", 0x25}, {"L", 0x26}, {"TILDE", 0x29}, {"LSHIFT", 0x2A}, {"Z", 0x2C}, {"X", 0x2D}, {"C", 0x2E},
      {"V", 0x2F}, {"B", 0x30}, {"N", 0x31}, {"M", 0x32}, {"SLASH", 0x35}, {"LALT", 0x38}, {"SPACE", 0x39}, {"CAPS", 0x3A},
      {"F1", 0x3B}, {"F2", 0x3C}, {"F3", 0x3D}, {"F4", 0x3E}, {"F5", 0x3F}, {"F6", 0x40}, {"F12", 0x58},
  };
  for (const auto& k : keys)
    if (k.name == n) return k.code;
  return std::nullopt;
}

std::optional<std::vector<std::uint16_t>> chord(std::string_view names) {
  std::vector<std::uint16_t> out;
  for (std::size_t start = 0; start <= names.size();) {
    auto end = names.find('+', start);
    if (end == std::string_view::npos) end = names.size();
    auto code = scancode(names.substr(start, end - start));
    if (!code) return std::nullopt;
    out.push_back(*code);
    start = end + 1;
  }
  if (out.empty() || out.size() > 4) return std::nullopt;
  return out;
}

FrameStats frame_stats(std::vector<double> ms) {
  FrameStats s;
  s.frames = ms.size();
  if (ms.empty()) return s;
  std::sort(ms.begin(), ms.end());
  double sum = 0;
  for (double v : ms) sum += v;
  s.mean = sum / double(ms.size());
  auto pick = [&](double q) { return ms[std::min(ms.size() - 1, static_cast<std::size_t>(q * double(ms.size())))]; };
  s.p50 = pick(0.50);
  s.p95 = pick(0.95);
  s.p99 = pick(0.99);
  s.max = ms.back();
  s.fps = s.mean > 0 ? 1000.0 / s.mean : 0;
  return s;
}

bool valid_save_name(std::string_view n) {
  if (n.empty() || n.size() > 64) return false;
  for (char c : n) {
    bool ok = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_' || c == '-' || c == ' ';
    if (!ok) return false;
  }
  return n.front() != ' ' && n.back() != ' ';
}

std::optional<CoreCall> core_call(const Request& r) {
  if (r.args.empty() || r.args[0].empty()) return std::nullopt;
  CoreCall c{r.args[0], std::nullopt};
  if (r.args.size() > 1) c.arg = rest(r, 1);
  return c;
}

std::string papyrus_queue_json(const PapyrusQueue& q) {
  return JsonObject()
      .integer("stacks", q.running + q.suspended)
      .integer("running", q.running)
      .integer("suspended", q.suspended)
      .integer("waiting_latent", q.waiting_latent)
      .integer("waiting_functions", q.waiting_functions)
      .boolean("overstressed", q.overstressed)
      .done();
}

}  // namespace argonia::bridge
