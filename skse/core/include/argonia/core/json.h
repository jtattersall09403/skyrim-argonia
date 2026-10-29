// JSON for the view messages (1.1 §c): a strict parser and writer plus the field readers the generated twin
// (generated/argonia/core/messages.h) is built from. Pure C++, no dependency. Strict on purpose: duplicate keys,
// trailing text, invalid UTF-8, lone surrogates, numbers out of double range and nesting past `max_depth` are
// refused, so both ends agree on what a message is.
#pragma once
#include <cstdint>
#include <expected>
#include <string>
#include <string_view>
#include <variant>
#include <vector>

namespace argonia::core::json {

class Value;
struct Member;
using Array = std::vector<Value>;
using Object = std::vector<Member>;  // in document order; keys unique

class Value {
 public:
  Value() = default;  // null
  static Value boolean(bool b);
  static Value number(double d);
  static Value string(std::string s);
  static Value array(Array a);
  static Value object(Object o);

  bool is_null() const { return std::holds_alternative<std::monostate>(v_); }
  const bool* as_bool() const { return std::get_if<bool>(&v_); }
  const double* as_number() const { return std::get_if<double>(&v_); }
  const std::string* as_string() const { return std::get_if<std::string>(&v_); }
  const Array* as_array() const { return std::get_if<Array>(&v_); }
  const Object* as_object() const { return std::get_if<Object>(&v_); }
  const Value* find(std::string_view key) const;  // an object's member, else nullptr

  // Structural equality; object members compare regardless of order.
  friend bool operator==(const Value& a, const Value& b);

 private:
  std::variant<std::monostate, bool, double, std::string, Array, Object> v_;
};

struct Member {
  std::string key;
  Value value;
};

inline constexpr int kMaxDepth = 64;
inline constexpr double kMaxSafeInt = 9007199254740991.0;  // 2^53 - 1: an integer both ends hold exactly

std::expected<Value, std::string> parse(std::string_view text, int max_depth = kMaxDepth);
// Compact, members in order. Integral numbers within the safe range print without a fraction; others print the
// shortest text that reads back to the same double. A non-finite number prints null (and the schema refuses it).
std::string dump(const Value& v);

// ---- field readers for the generated decoders: each returns false and sets `err` to "<path>: <why>" ----

bool fail(std::string& err, const std::string& path, std::string_view why);
bool read(const Value& v, std::string& out, const std::string& path, std::string& err);
bool read(const Value& v, bool& out, const std::string& path, std::string& err);
bool read_int(const Value& v, std::int64_t& out, double lo, double hi, const std::string& path, std::string& err);
bool read_num(const Value& v, double& out, double lo, double hi, const std::string& path, std::string& err);

// The members of one object: each schema field is taken once; `done` refuses any member not taken.
class Fields {
 public:
  Fields(const Value& v, std::string path, std::string& err);
  bool ok() const { return obj_ != nullptr; }
  const Value* req(std::string_view key);  // nullptr and err "<path>.<key>: missing" when absent
  const Value* opt(std::string_view key);  // nullptr when absent
  bool done();
  const std::string& path() const { return path_; }

 private:
  const Object* obj_ = nullptr;
  std::string path_;
  std::string& err_;
  std::vector<bool> used_;
};

// {"type": ..., "v": ..., "body": ...} as text.
std::string envelope(std::string_view type, std::uint32_t version, Value body);

}  // namespace argonia::core::json
