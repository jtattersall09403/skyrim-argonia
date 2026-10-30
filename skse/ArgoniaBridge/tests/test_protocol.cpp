// L2: the bridge refuses what it must before any handler runs (0.3 §a: each endpoint has a fail-on-purpose test).
#include "bridge_protocol.h"
#include "check.h"

#include <limits>
#include <string>

using namespace argonia::bridge;

namespace {
const std::string kToken = "0123456789abcdef0123456789abcdef";

void ping_parses() {
  auto r = parse(kToken + " ping\r\n", kToken);
  auto* req = std::get_if<Request>(&r);
  CHECK(req && req->command == "ping" && req->args.empty());
}

void args_are_kept() {
  auto r = parse(kToken + " ping a b", kToken);
  auto* req = std::get_if<Request>(&r);
  CHECK(req && req->args.size() == 2 && req->args[1] == "b");
}

void bad_tokens_are_refused() {
  auto wrong = std::string(kToken);
  wrong[31] = '0';
  CHECK(std::holds_alternative<Refusal>(parse(wrong + " ping", kToken)));
  CHECK(std::holds_alternative<Refusal>(parse("ping", kToken)));
  CHECK(std::holds_alternative<Refusal>(parse("", kToken)));
  CHECK(std::holds_alternative<Refusal>(parse(kToken.substr(0, 31) + " ping", kToken.substr(0, 31))));
  CHECK(!token_matches("", ""));
}

void missing_command_and_long_lines_are_refused() {
  CHECK(std::holds_alternative<Refusal>(parse(kToken, kToken)));
  CHECK(std::holds_alternative<Refusal>(parse(kToken + " ", kToken)));
  CHECK(std::holds_alternative<Refusal>(parse(kToken + " ping " + std::string(kMaxLine, 'x'), kToken)));
}

void replies_are_one_json_line() {
  CHECK(reply_ok("ping", "{\"main_thread\":true}") == "{\"ok\":true,\"cmd\":\"ping\",\"result\":{\"main_thread\":true}}\n");
  CHECK(reply_error("x\"y", "a\nb") == "{\"ok\":false,\"cmd\":\"x\\\"y\",\"error\":\"a\\nb\"}\n");
  CHECK(json_escape(std::string(1, '\x01')) == "\\u0001");
}
void rest_keeps_the_line() {
  auto r = std::get<Request>(parse(kToken + " console player.setav  health 50", kToken));
  CHECK(rest(r) == "player.setav  health 50");
  CHECK(rest(r, 1) == " health 50");
  CHECK(rest(Request{"x", {}}).empty());
}

void numbers_and_form_ids() {
  CHECK(to_number("-12.5") == -12.5);
  CHECK(to_number("+3") == 3.0);
  CHECK(!to_number(""));
  CHECK(!to_number("1e999"));  // not finite: refused
  CHECK(!to_number("12abc"));
  CHECK(!to_number("nan"));
  CHECK(to_form_id("0001A26F") == 0x0001A26Fu);
  CHECK(to_form_id("0x14") == 0x14u);
  CHECK(!to_form_id("0x"));
  CHECK(!to_form_id("123456789"));
  CHECK(!to_form_id("xyz"));
}

void json_objects() {
  JsonObject o;
  o.str("a", "q\"").num("b", 1.5).integer("c", -2).boolean("d", false).raw("e", "[1]").hex("f", 0x14);
  CHECK(o.done() == "{\"a\":\"q\\\"\",\"b\":1.5,\"c\":-2,\"d\":false,\"e\":[1],\"f\":\"00000014\"}");
  CHECK(JsonObject().done() == "{}");
  CHECK(json_number(std::numeric_limits<double>::infinity()) == "null");
  CHECK(json_number(-0.25) == "-0.25");
}

void console_text() {
  CHECK(console_delta("a\nb\n", "a\nb\nc\n") == "c\n");
  CHECK(console_delta("", "x\n") == "x\n");
  CHECK(console_delta("old\nlast\n", "last\nnew\n") == "new\n");  // the front was trimmed
  CHECK(console_delta("a\nb\n", "a\nb\n").empty());               // printed nothing
  CHECK(console_refused("Script command \"notacommand\" not found.\n"));
  CHECK(console_refused("Missing parameter Actor Value Name\n"));
  CHECK(!console_refused("GetPos: X >> 1024.00\n"));
  CHECK(!console_refused(""));
}

void save_names() {
  CHECK(valid_save_name("argonia-base"));
  CHECK(valid_save_name("Studio 1_a"));
  CHECK(!valid_save_name(""));
  CHECK(!valid_save_name("..\\x"));
  CHECK(!valid_save_name("a/b"));
  CHECK(!valid_save_name("a.ess"));
  CHECK(!valid_save_name(" lead"));
  CHECK(!valid_save_name(std::string(65, 'a')));
}
void input_keys_and_frames() {
  CHECK(scancode("W") == 0x11);
  CHECK(!scancode("w"));
  CHECK(!scancode(""));
  auto c = chord("W+LSHIFT");
  CHECK(c && c->size() == 2 && (*c)[1] == 0x2A);
  CHECK(!chord("W+"));
  CHECK(!chord("W+NOPE"));
  CHECK(!chord("W+A+S+D+E"));  // five keys: refused
  auto f = frame_stats({16, 17, 15, 100, 16});
  CHECK(f.frames == 5 && f.max == 100 && f.p50 == 16);
  CHECK_NEAR(f.mean, 32.8, 1e-9);
  CHECK(frame_stats({}).frames == 0);
}
}  // namespace

void nav_tests();

void core_calls_and_the_queue() {
  auto parsed = [](std::string line) { return std::get<Request>(parse(kToken + " " + line, kToken)); };
  CHECK(!core_call(parsed("core")));
  auto c = core_call(parsed("core GetVastei"));
  CHECK(c && c->native == "GetVastei" && !c->arg);
  c = core_call(parsed(R"(core ViewIntent {"type":"dialogue.topic","v":1,"body":{"topic":"a b"}})"));
  CHECK(c && c->native == "ViewIntent" && c->arg == R"({"type":"dialogue.topic","v":1,"body":{"topic":"a b"}})");
  CHECK(papyrus_queue_json({3, 2, 1, 0, false}) ==
        R"({"stacks":5,"running":3,"suspended":2,"waiting_latent":1,"waiting_functions":0,"overstressed":false})");
}

int main() {
  core_calls_and_the_queue();
  input_keys_and_frames();
  nav_tests();
  rest_keeps_the_line();
  numbers_and_form_ids();
  json_objects();
  console_text();
  save_names();
  ping_parses();
  args_are_kept();
  bad_tokens_are_refused();
  missing_command_and_long_lines_are_refused();
  replies_are_one_json_line();
  return TEST_MAIN_RESULT("bridge.protocol");
}
