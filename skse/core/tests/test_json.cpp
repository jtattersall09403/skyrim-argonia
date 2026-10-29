// L2: the strict JSON under the view messages (1.1 §c): what parses, what is refused, and that dump reads back.
#include "check.h"
#include "argonia/core/json.h"

#include <limits>
#include <string>

using namespace argonia::core;

namespace {

bool refused(std::string_view text, const char* why) {
  auto r = json::parse(text);
  return !r && r.error().find(why) != std::string::npos;
}

void parses_and_reads_back() {
  auto v = json::parse(R"( {"a": [1, -2.5, 1e3, true, false, null], "s": "x\"y\\z\n\u00e9\ud83d\ude00", "o": {}} )");
  CHECK(v.has_value());
  const json::Array* a = v->find("a")->as_array();
  CHECK(a && a->size() == 6 && *(*a)[1].as_number() == -2.5 && *(*a)[2].as_number() == 1000 && (*a)[5].is_null());
  CHECK(*v->find("s")->as_string() == "x\"y\\z\n\xc3\xa9\xf0\x9f\x98\x80");
  auto again = json::parse(json::dump(*v));
  CHECK(again && *again == *v);
  CHECK(json::dump(json::Value::number(3)) == "3" && json::dump(json::Value::number(0.1)) == "0.1");
  CHECK(json::dump(json::Value::string("\x01")) == "\"\\u0001\"");
  // Object equality ignores member order.
  CHECK(*json::parse(R"({"a":1,"b":2})") == *json::parse(R"({"b":2,"a":1})"));
  CHECK(!(*json::parse(R"({"a":1})") == *json::parse(R"({"a":1.5})")));
}

void refuses() {
  CHECK(refused(R"({"a":1,"a":2})", "duplicate key"));
  CHECK(refused("[1] x", "text after the value"));
  CHECK(refused("[1,]", "unexpected character"));
  CHECK(refused("01", "text after the value"));
  CHECK(refused("1e999", "out of range"));
  CHECK(refused("\"\xff\"", "invalid UTF-8"));
  CHECK(refused("\"\xc0\xaf\"", "invalid UTF-8"));  // overlong
  CHECK(refused(R"("\ud800")", "lone high surrogate"));
  CHECK(refused(R"("\udc00")", "lone low surrogate"));
  CHECK(refused("\"a\nb\"", "control character"));
  CHECK(refused("nul", "unknown literal"));
  CHECK(refused("", "unexpected end"));
  std::string deep(json::kMaxDepth + 2, '[');
  deep += std::string(json::kMaxDepth + 2, ']');
  CHECK(refused(deep, "nested too deep"));
}

void field_readers() {
  std::string err;
  std::int64_t i = 0;
  double d = 0;
  CHECK(!json::read_int(json::Value::number(1.5), i, -10, 10, "p", err) && err == "p: want a whole number");
  CHECK(!json::read_int(json::Value::number(11), i, -10, 10, "p", err) && err == "p: 11 is outside -10..10");
  CHECK(json::read_int(json::Value::number(-10), i, -10, 10, "p", err) && i == -10);
  CHECK(!json::read_num(json::Value::number(std::numeric_limits<double>::quiet_NaN()), d, 0, 1, "p", err));
  auto obj = json::parse(R"({"a":1,"b":2})");
  json::Fields f(*obj, "m", err);
  CHECK(f.ok() && f.req("a") && !f.req("c") && err == "m.c: missing");
  CHECK(!f.done() && err == "m.b: not in the schema");
}

}  // namespace

int main() {
  parses_and_reads_back();
  refuses();
  field_readers();
  return TEST_MAIN_RESULT("core.json");
}
