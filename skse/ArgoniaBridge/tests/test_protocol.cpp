// L2: the bridge refuses what it must before any handler runs (0.3 §a: each endpoint has a fail-on-purpose test).
#include "bridge_protocol.h"
#include "check.h"

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
}  // namespace

int main() {
  ping_parses();
  args_are_kept();
  bad_tokens_are_refused();
  missing_command_and_long_lines_are_refused();
  replies_are_one_json_line();
  return TEST_MAIN_RESULT("bridge.protocol");
}
