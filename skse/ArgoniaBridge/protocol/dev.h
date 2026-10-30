// The dev-only setters and the reads 1.7's journeys owed (lane bridge-gaps), the parts that are pure C++ so they are
// unit-tested on the build VM: which ArgoniaCore natives `dev-set` may call, the INI and log names the reads take,
// and the i-frame trace's summary. The handlers live in src/ep_dev.cpp (DEV ONLY; never in ArgoniaCore).
#pragma once
#include "bridge_protocol.h"

#include <optional>
#include <string>
#include <string_view>
#include <variant>
#include <vector>

namespace argonia::bridge::dev {

// `dev-set <Native> [text] <number>`: an ArgoniaCore Papyrus native called through the Papyrus VM, the same entry a
// script uses, so its own clamps and refusals apply. Only the scene-input setters are allowed (a scene sets inputs
// at step 0, never the thing tested): SetAttribute <attribute> <value> and SetVastei <value>.
struct SetCall {
  std::string native;
  std::optional<std::string> text;
  double value = 0;
};
std::variant<SetCall, std::string> set_call(const Request& r);  // the call, or the refusal in words
std::vector<std::string_view> setters();

// `dev-grow <target ref> <pending levels> [max blows]`: landed blows sent as hit events into ArgoniaCore's own sink
// until GetPendingLevels reaches the target (a measured blow count; the pending level is the rest's input).
struct GrowCall {
  std::string target;
  int pending = 1;
  int max_blows = 400;
};
std::variant<GrowCall, std::string> grow_call(const Request& r);

// `ini <name:Section>`: an INI setting as the game holds it ("bShowCompass:Interface"); the name only.
bool valid_ini_name(std::string_view s);
// `logfile <name> <text>`: an SKSE log beside ours ("CommunityShaders"); letters, digits, _ and spaces.
bool valid_log_name(std::string_view s);
// The lines of `text` that contain `needle`, and how many lines there are.
struct LogMatch {
  long long lines = 0, matches = 0;
  std::string first;  // the first matching line, "" when none
};
LogMatch log_match(std::string_view text, std::string_view needle);

// The i-frame trace: one sample per frame of the player's update, armed by `trace start <frames> [graph var...]`.
struct Sample {
  long long frame = 0;
  double ms = 0;  // since the trace was armed
  double x = 0, y = 0, z = 0;
  double health = 0;
  bool ghost = false;  // Actor::IsGhost (TK Dodge's i-frames), or any named graph bool true
  std::vector<bool> vars;
};
inline constexpr int kTraceMaxFrames = 1200;
// The window: the first and last i-frame sample, their count and the span in ms (first_frame -1 when none).
std::string trace_json(const std::vector<Sample>& s, const std::vector<std::string>& var_names, bool with_samples);

}  // namespace argonia::bridge::dev
