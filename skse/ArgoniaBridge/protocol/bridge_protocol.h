// ArgoniaBridge's wire protocol (DEV ONLY, 0.3 §a). Pure C++ so its parsing, its refusals and the text rules its
// handlers lean on are unit-tested on the build VM; the plugin only moves bytes and runs handlers on the main thread.
//
//   request:  one line, at most kMaxLine bytes:  <token> <command> [arg ...]\n
//   reply:    one line of JSON:  {"ok":true,"cmd":"ping","result":{...}}  or  {"ok":false,"cmd":"..","error":".."}
//
// The token is 32 hex characters written by the plugin at load to ArgoniaBridge.token beside its SKSE log; a
// request without it is refused before any handler runs. The same lines go over the named pipe
// \\.\pipe\argonia-bridge and over TCP 127.0.0.1:kTcpPort (the build VM reaches the port through an SSH tunnel).
#pragma once
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <variant>
#include <vector>

namespace argonia::bridge {

inline constexpr std::size_t kMaxLine = 4096;
inline constexpr std::size_t kTokenHexChars = 32;
inline constexpr std::uint16_t kTcpPort = 47615;

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

// The arguments as the client sent them (single spaces kept), for commands that take a free line (`console`).
std::string rest(const Request& r, std::size_t from = 0);

// A decimal number, all of the text or nothing (no locale, no trailing junk, finite only).
std::optional<double> to_number(std::string_view s);
// A form id as hex, with or without 0x: "0001A26F", "0x14".
std::optional<std::uint32_t> to_form_id(std::string_view s);

std::string json_escape(std::string_view s);
// result_json must already be a JSON value (object, number, string literal).
std::string reply_ok(std::string_view cmd, std::string_view result_json);
std::string reply_error(std::string_view cmd, std::string_view error);

// Builds one JSON object in insertion order; a non-finite number is written as null.
class JsonObject {
 public:
  JsonObject& str(std::string_view key, std::string_view value);
  JsonObject& num(std::string_view key, double value);
  JsonObject& integer(std::string_view key, long long value);
  JsonObject& boolean(std::string_view key, bool value);
  JsonObject& raw(std::string_view key, std::string_view json);
  JsonObject& hex(std::string_view key, std::uint32_t form_id);  // "0001A26F"
  std::string done() const { return body_ + "}"; }

 private:
  void key(std::string_view k);
  std::string body_ = "{";
};
std::string json_number(double v);
std::string json_string(std::string_view s);  // with the quotes

// What the console printed between two snapshots of its log buffer. The game trims the front of a long buffer, so
// when `after` no longer starts with `before`, the new text is what follows `before`'s last line in `after`.
std::string console_delta(std::string_view before, std::string_view after);
// The compiler's own words for a line it would not run (the console prints these and runs nothing).
bool console_refused(std::string_view output);

// Real inputs are short (0.3 §d: an input of at most 3 s); a longer hold is refused.
inline constexpr int kInputCapMs = 3000;
// DirectInput scan codes by name (W, LSHIFT, SPACE, 1, ...); a chord is names joined by '+', all held together.
std::optional<std::uint16_t> scancode(std::string_view name);
std::optional<std::vector<std::uint16_t>> chord(std::string_view names);

// Frame-time statistics over a sample of frame intervals in milliseconds.
struct FrameStats {
  std::size_t frames = 0;
  double mean = 0, p50 = 0, p95 = 0, p99 = 0, max = 0, fps = 0;
};
FrameStats frame_stats(std::vector<double> ms);

// A save name the bridge will pass to the game: 1..64 of [A-Za-z0-9 _-], no path, no extension.
bool valid_save_name(std::string_view name);

}  // namespace argonia::bridge
