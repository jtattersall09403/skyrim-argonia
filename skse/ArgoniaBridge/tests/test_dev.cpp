// L2: the dev setters refuse every native that is not a scene input; the reads' names are checked; the i-frame
// trace's window is the first and last i-frame sample.
#include "check.h"
#include "dev.h"

using namespace argonia::bridge;
using namespace argonia::bridge::dev;

namespace {
Request req(std::vector<std::string> args) { return Request{"x", std::move(args)}; }

void setters_are_scene_inputs_only() {
  auto a = set_call(req({"SetAttribute", "strength", "10000"}));
  auto* s = std::get_if<SetCall>(&a);
  CHECK(s && s->native == "SetAttribute" && s->text == "strength" && s->value == 10000);
  auto v = set_call(req({"SetVastei", "-5"}));
  CHECK(std::get_if<SetCall>(&v) && std::get<SetCall>(v).value == -5 && !std::get<SetCall>(v).text);
  CHECK(std::holds_alternative<std::string>(set_call(req({"SetFlag", "x", "1"}))));      // sets what quests test
  CHECK(std::holds_alternative<std::string>(set_call(req({"GiveGold", "5"}))));
  CHECK(std::holds_alternative<std::string>(set_call(req({"SetAttribute", "strength"}))));
  CHECK(std::holds_alternative<std::string>(set_call(req({"SetAttribute", "strength", "lots"}))));
  CHECK(std::holds_alternative<std::string>(set_call(req({}))));
  CHECK(setters().size() == 2);
}

void grow_takes_a_ref_and_a_small_count() {
  auto g = grow_call(req({"FF000ABC", "1"}));
  CHECK(std::get_if<GrowCall>(&g) && std::get<GrowCall>(g).pending == 1 && std::get<GrowCall>(g).max_blows == 400);
  auto h = grow_call(req({"0x14", "2", "900"}));
  CHECK(std::get_if<GrowCall>(&h) && std::get<GrowCall>(h).max_blows == 900);
  CHECK(std::holds_alternative<std::string>(grow_call(req({"FF000ABC", "0"}))));
  CHECK(std::holds_alternative<std::string>(grow_call(req({"FF000ABC", "1.5"}))));
  CHECK(std::holds_alternative<std::string>(grow_call(req({"FF000ABC", "1", "5000"}))));
  CHECK(std::holds_alternative<std::string>(grow_call(req({"opp", "1"}))));
}

void names_are_checked() {
  CHECK(valid_ini_name("bShowCompass:Interface"));
  CHECK(valid_ini_name("fTargetLockDistance:TDM"));
  CHECK(!valid_ini_name("bShowCompass"));
  CHECK(!valid_ini_name(":Interface"));
  CHECK(!valid_ini_name("a:b:c"));
  CHECK(!valid_ini_name("a;b:c"));
  CHECK(valid_log_name("CommunityShaders"));
  CHECK(valid_log_name("Fuz Ro D-oh"));
  CHECK(!valid_log_name("..\\x"));
  CHECK(!valid_log_name(""));
}

void log_lines_match() {
  auto m = log_match("[I] Loading Feature: 'InteriorSun'\r\n[I] [Interior Sun] Installed hooks\r\nx\n", "[Interior Sun] Installed hooks");
  CHECK(m.lines == 3 && m.matches == 1 && m.first == "[I] [Interior Sun] Installed hooks");
  CHECK(log_match("", "a").lines == 0);
  CHECK(log_match("abc", "zz").matches == 0);
}

void the_trace_window_is_first_to_last() {
  std::vector<Sample> s;
  for (int f = 0; f < 10; ++f) s.push_back(Sample{f, f * 16.0, 0, 0, 0, f == 6 ? 80.0 : 100.0, f >= 3 && f <= 5, {f == 4}});
  auto j = trace_json(s, {"bIframeActive"}, false);
  CHECK(j.find(R"("iframe_frames":3,"first_frame":3,"last_frame":5,"first_ms":48,"last_ms":80,"window_ms":32)") != std::string::npos);
  CHECK(j.find(R"("health_start":100,"health_min":80)") != std::string::npos);
  CHECK(j.find("samples") == std::string::npos);
  CHECK(trace_json({}, {}, true).find(R"("first_frame":-1)") != std::string::npos);
  CHECK(trace_json(s, {"v"}, true).find(R"({"f":4,"ms":64,"x":0,"y":0,"z":0,"hp":100,"i":true,"v":[true]})") != std::string::npos);
}
}  // namespace

void dev_tests() {
  setters_are_scene_inputs_only();
  grow_takes_a_ref_and_a_small_count();
  names_are_checked();
  log_lines_match();
  the_trace_window_is_first_to_last();
}
