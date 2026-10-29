// ArgoniaBridge's wire protocol (DEV ONLY, 0.3 §a). Pure C++ so its parsing and its refusals are unit-tested on
// the build VM; the plugin only moves bytes over the pipe and runs handlers on the main thread.
//
//   request:  one line, at most kMaxLine bytes:  <token> <command> [arg ...]\n
//   reply:    one line of JSON:  {"ok":true,"cmd":"ping","result":{...}}  or  {"ok":false,"cmd":"..","error":".."}
//
// The token is 32 hex characters written by the plugin at load to ArgoniaBridge.token beside its SKSE log; a
// request without it is refused before any handler runs.
#pragma once
#include <cstddef>
#include <string>
#include <string_view>
#include <variant>
#include <vector>

namespace argonia::bridge {

inline constexpr std::size_t kMaxLine = 4096;
inline constexpr std::size_t kTokenHexChars = 32;

struct Request {
  std::string command;
  std::vector<std::string> args;
};

struct Refusal {
  std::string error;
};

// Constant-time in the token's length, so the comparison leaks nothing by timing.
bool token_matches(std::string_view expected, std::string_view given);

// Splits on single spaces after trimming a trailing \r\n; checks the token. Never throws.
std::variant<Request, Refusal> parse(std::string_view line, std::string_view expected_token);

std::string json_escape(std::string_view s);
// result_json must already be a JSON value (object, number, string literal).
std::string reply_ok(std::string_view cmd, std::string_view result_json);
std::string reply_error(std::string_view cmd, std::string_view error);

}  // namespace argonia::bridge
