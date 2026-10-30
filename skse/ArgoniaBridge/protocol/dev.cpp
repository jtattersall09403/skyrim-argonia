#include "dev.h"

#include <array>
#include <cctype>

namespace argonia::bridge::dev {

namespace {
constexpr std::array<std::string_view, 2> kSetters{"SetAttribute", "SetVastei"};
}

std::vector<std::string_view> setters() { return {kSetters.begin(), kSetters.end()}; }

std::variant<SetCall, std::string> set_call(const Request& r) {
  const std::string usage = "usage: dev-set SetAttribute <attribute> <value> | dev-set SetVastei <value>";
  if (r.args.empty()) return usage;
  const auto& n = r.args[0];
  if (n == "SetAttribute") {
    if (r.args.size() != 3) return usage;
    auto v = to_number(r.args[2]);
    if (!v) return "the value must be a number";
    return SetCall{n, r.args[1], *v};
  }
  if (n == "SetVastei") {
    if (r.args.size() != 2) return usage;
    auto v = to_number(r.args[1]);
    if (!v) return "the value must be a number";
    return SetCall{n, std::nullopt, *v};
  }
  return "not a scene-input setter: " + n + " (dev-set takes SetAttribute or SetVastei)";
}

std::variant<GrowCall, std::string> grow_call(const Request& r) {
  const std::string usage = "usage: dev-grow <target ref id> <pending levels 1..5> [max blows 1..2000]";
  if (r.args.size() < 2 || r.args.size() > 3) return usage;
  GrowCall g{r.args[0]};
  auto p = to_number(r.args[1]);
  if (!p || *p < 1 || *p > 5 || *p != static_cast<int>(*p)) return usage;
  g.pending = static_cast<int>(*p);
  if (r.args.size() == 3) {
    auto m = to_number(r.args[2]);
    if (!m || *m < 1 || *m > 2000 || *m != static_cast<int>(*m)) return usage;
    g.max_blows = static_cast<int>(*m);
  }
  if (!to_form_id(g.target)) return "the target is a reference's form id";
  return g;
}

bool valid_ini_name(std::string_view s) {
  auto colon = s.find(':');
  if (colon == std::string_view::npos || colon == 0 || colon + 1 >= s.size() || s.size() > 96) return false;
  for (std::size_t i = 0; i < s.size(); ++i) {
    const auto c = static_cast<unsigned char>(s[i]);
    if (i == colon) continue;
    if (!std::isalnum(c) && c != '_' && c != ' ') return false;
  }
  return s.find(':', colon + 1) == std::string_view::npos;
}

bool valid_log_name(std::string_view s) {
  if (s.empty() || s.size() > 64 || s.front() == ' ') return false;
  for (auto ch : s) {
    const auto c = static_cast<unsigned char>(ch);
    if (!std::isalnum(c) && c != '_' && c != ' ' && c != '-') return false;
  }
  return true;
}

LogMatch log_match(std::string_view text, std::string_view needle) {
  LogMatch m;
  while (!text.empty()) {
    auto nl = text.find('\n');
    auto line = text.substr(0, nl);
    if (!line.empty() && line.back() == '\r') line.remove_suffix(1);
    ++m.lines;
    if (!needle.empty() && line.find(needle) != std::string_view::npos) {
      if (m.matches++ == 0) m.first = std::string(line);
    }
    if (nl == std::string_view::npos) break;
    text.remove_prefix(nl + 1);
  }
  return m;
}

std::string trace_json(const std::vector<Sample>& s, const std::vector<std::string>& var_names, bool with_samples) {
  long long first = -1, last = -1, count = 0;
  double first_ms = 0, last_ms = 0;
  double h0 = s.empty() ? 0 : s.front().health, hmin = h0;
  for (const auto& x : s) {
    if (x.health < hmin) hmin = x.health;
    if (!x.ghost) continue;
    ++count;
    if (first < 0) first = x.frame, first_ms = x.ms;
    last = x.frame, last_ms = x.ms;
  }
  std::string names = "[";
  for (const auto& n : var_names) names += (names.size() > 1 ? "," : "") + json_string(n);
  JsonObject o;
  o.integer("frames", static_cast<long long>(s.size()))
      .raw("vars", names + "]")
      .integer("iframe_frames", count)
      .integer("first_frame", first)
      .integer("last_frame", last)
      .num("first_ms", first < 0 ? 0 : first_ms)
      .num("last_ms", last < 0 ? 0 : last_ms)
      .num("window_ms", first < 0 ? 0 : last_ms - first_ms)
      .num("health_start", h0)
      .num("health_min", hmin);
  if (with_samples) {
    std::string rows = "[";
    for (const auto& x : s) {
      std::string vars = "[";
      for (bool b : x.vars) vars += std::string(vars.size() > 1 ? "," : "") + (b ? "true" : "false");
      if (rows.size() > 1) rows += ',';
      rows += JsonObject().integer("f", x.frame).num("ms", x.ms).num("x", x.x).num("y", x.y).num("z", x.z)
                  .num("hp", x.health).boolean("i", x.ghost).raw("v", vars + "]").done();
    }
    o.raw("samples", rows + "]");
  }
  return o.done();
}

}  // namespace argonia::bridge::dev
