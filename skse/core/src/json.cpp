#include "argonia/core/json.h"

#include <algorithm>
#include <charconv>
#include <cmath>
#include <cstddef>
#include <system_error>

namespace argonia::core::json {

Value Value::boolean(bool b) { Value v; v.v_ = b; return v; }
Value Value::number(double d) { Value v; v.v_ = d; return v; }
Value Value::string(std::string s) { Value v; v.v_ = std::move(s); return v; }
Value Value::array(Array a) { Value v; v.v_ = std::move(a); return v; }
Value Value::object(Object o) { Value v; v.v_ = std::move(o); return v; }

const Value* Value::find(std::string_view key) const {
  const Object* o = as_object();
  if (!o) return nullptr;
  for (const auto& m : *o)
    if (m.key == key) return &m.value;
  return nullptr;
}

bool operator==(const Value& a, const Value& b) {
  if (a.v_.index() != b.v_.index()) return false;
  if (const Object* oa = a.as_object()) {
    const Object* ob = b.as_object();
    if (oa->size() != ob->size()) return false;
    for (const auto& m : *oa) {
      const Value* other = b.find(m.key);
      if (!other || !(m.value == *other)) return false;
    }
    return true;
  }
  if (const Array* aa = a.as_array()) return *aa == *b.as_array();
  if (const std::string* sa = a.as_string()) return *sa == *b.as_string();
  if (const double* da = a.as_number()) return *da == *b.as_number();
  if (const bool* ba = a.as_bool()) return *ba == *b.as_bool();
  return true;  // both null
}

namespace {

class Parser {
 public:
  Parser(std::string_view t, int max_depth) : t_(t), max_depth_(max_depth) {}

  std::expected<Value, std::string> run() {
    Value v;
    if (!value(v, 0)) return std::unexpected(err_);
    ws();
    if (i_ != t_.size()) return std::unexpected(where("text after the value"));
    return v;
  }

 private:
  std::string where(std::string_view why) const { return "JSON error at byte " + std::to_string(i_) + ": " + std::string(why); }
  bool bad(std::string_view why) { err_ = where(why); return false; }
  void ws() {
    while (i_ < t_.size() && (t_[i_] == ' ' || t_[i_] == '\t' || t_[i_] == '\n' || t_[i_] == '\r')) ++i_;
  }
  bool lit(std::string_view word) {
    if (t_.substr(i_, word.size()) != word) return bad("unknown literal");
    i_ += word.size();
    return true;
  }

  bool value(Value& out, int depth) {
    if (depth > max_depth_) return bad("nested too deep");
    ws();
    if (i_ >= t_.size()) return bad("unexpected end");
    const char c = t_[i_];
    if (c == '{') return object(out, depth);
    if (c == '[') return array(out, depth);
    if (c == '"') {
      std::string s;
      if (!string(s)) return false;
      out = Value::string(std::move(s));
      return true;
    }
    if (c == 't') { if (!lit("true")) return false; out = Value::boolean(true); return true; }
    if (c == 'f') { if (!lit("false")) return false; out = Value::boolean(false); return true; }
    if (c == 'n') { if (!lit("null")) return false; out = Value(); return true; }
    return number(out);
  }

  bool object(Value& out, int depth) {
    ++i_;
    Object o;
    ws();
    if (i_ < t_.size() && t_[i_] == '}') { ++i_; out = Value::object(std::move(o)); return true; }
    for (;;) {
      ws();
      if (i_ >= t_.size() || t_[i_] != '"') return bad("want a key");
      std::string key;
      if (!string(key)) return false;
      if (std::any_of(o.begin(), o.end(), [&](const Member& m) { return m.key == key; }))
        return bad("duplicate key \"" + key + "\"");
      ws();
      if (i_ >= t_.size() || t_[i_] != ':') return bad("want ':'");
      ++i_;
      Value v;
      if (!value(v, depth + 1)) return false;
      o.push_back({std::move(key), std::move(v)});
      ws();
      if (i_ < t_.size() && t_[i_] == ',') { ++i_; continue; }
      if (i_ < t_.size() && t_[i_] == '}') { ++i_; break; }
      return bad("want ',' or '}'");
    }
    out = Value::object(std::move(o));
    return true;
  }

  bool array(Value& out, int depth) {
    ++i_;
    Array a;
    ws();
    if (i_ < t_.size() && t_[i_] == ']') { ++i_; out = Value::array(std::move(a)); return true; }
    for (;;) {
      Value v;
      if (!value(v, depth + 1)) return false;
      a.push_back(std::move(v));
      ws();
      if (i_ < t_.size() && t_[i_] == ',') { ++i_; continue; }
      if (i_ < t_.size() && t_[i_] == ']') { ++i_; break; }
      return bad("want ',' or ']'");
    }
    out = Value::array(std::move(a));
    return true;
  }

  static void put_utf8(std::string& s, std::uint32_t cp) {
    if (cp < 0x80) {
      s += char(cp);
    } else if (cp < 0x800) {
      s += char(0xC0 | (cp >> 6)); s += char(0x80 | (cp & 0x3F));
    } else if (cp < 0x10000) {
      s += char(0xE0 | (cp >> 12)); s += char(0x80 | ((cp >> 6) & 0x3F)); s += char(0x80 | (cp & 0x3F));
    } else {
      s += char(0xF0 | (cp >> 18)); s += char(0x80 | ((cp >> 12) & 0x3F)); s += char(0x80 | ((cp >> 6) & 0x3F));
      s += char(0x80 | (cp & 0x3F));
    }
  }

  bool hex4(std::uint32_t& cp) {
    if (t_.size() - i_ < 4) return bad("short \\u escape");
    cp = 0;
    for (int k = 0; k < 4; ++k) {
      const char h = t_[i_++];
      cp <<= 4;
      if (h >= '0' && h <= '9') cp |= std::uint32_t(h - '0');
      else if (h >= 'a' && h <= 'f') cp |= std::uint32_t(h - 'a' + 10);
      else if (h >= 'A' && h <= 'F') cp |= std::uint32_t(h - 'A' + 10);
      else return bad("bad \\u escape");
    }
    return true;
  }

  // One UTF-8 sequence starting at i_, copied to s; refuses overlongs, surrogates and anything past U+10FFFF.
  bool utf8(std::string& s) {
    const auto b0 = std::uint8_t(t_[i_]);
    int n = 0;
    std::uint32_t cp = 0, min = 0;
    if (b0 >= 0xC2 && b0 <= 0xDF) { n = 1; cp = b0 & 0x1F; min = 0x80; }
    else if (b0 >= 0xE0 && b0 <= 0xEF) { n = 2; cp = b0 & 0x0F; min = 0x800; }
    else if (b0 >= 0xF0 && b0 <= 0xF4) { n = 3; cp = b0 & 0x07; min = 0x10000; }
    else return bad("invalid UTF-8");
    if (t_.size() - i_ <= std::size_t(n)) return bad("invalid UTF-8");
    for (int k = 1; k <= n; ++k) {
      const auto b = std::uint8_t(t_[i_ + std::size_t(k)]);
      if ((b & 0xC0) != 0x80) return bad("invalid UTF-8");
      cp = (cp << 6) | (b & 0x3F);
    }
    if (cp < min || cp > 0x10FFFF || (cp >= 0xD800 && cp <= 0xDFFF)) return bad("invalid UTF-8");
    s.append(t_.substr(i_, std::size_t(n) + 1));
    i_ += std::size_t(n) + 1;
    return true;
  }

  bool string(std::string& s) {
    ++i_;
    for (;;) {
      if (i_ >= t_.size()) return bad("unterminated string");
      const char c = t_[i_];
      if (c == '"') { ++i_; return true; }
      if (std::uint8_t(c) < 0x20) return bad("control character in a string");
      if (std::uint8_t(c) >= 0x80) { if (!utf8(s)) return false; continue; }
      if (c != '\\') { s += c; ++i_; continue; }
      ++i_;
      if (i_ >= t_.size()) return bad("unterminated escape");
      const char e = t_[i_++];
      switch (e) {
        case '"': s += '"'; break;
        case '\\': s += '\\'; break;
        case '/': s += '/'; break;
        case 'b': s += '\b'; break;
        case 'f': s += '\f'; break;
        case 'n': s += '\n'; break;
        case 'r': s += '\r'; break;
        case 't': s += '\t'; break;
        case 'u': {
          std::uint32_t cp = 0;
          if (!hex4(cp)) return false;
          if (cp >= 0xDC00 && cp <= 0xDFFF) return bad("lone low surrogate");
          if (cp >= 0xD800 && cp <= 0xDBFF) {
            std::uint32_t lo = 0;
            if (t_.substr(i_, 2) != "\\u") return bad("lone high surrogate");
            i_ += 2;
            if (!hex4(lo)) return false;
            if (lo < 0xDC00 || lo > 0xDFFF) return bad("lone high surrogate");
            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
          }
          put_utf8(s, cp);
          break;
        }
        default: return bad("bad escape");
      }
    }
  }

  bool number(Value& out) {
    const std::size_t start = i_;
    auto digits = [&] {
      const std::size_t d = i_;
      while (i_ < t_.size() && t_[i_] >= '0' && t_[i_] <= '9') ++i_;
      return i_ > d;
    };
    if (i_ < t_.size() && t_[i_] == '-') ++i_;
    if (i_ < t_.size() && t_[i_] == '0') ++i_;
    else if (!digits()) return bad("unexpected character");
    if (i_ < t_.size() && t_[i_] == '.') { ++i_; if (!digits()) return bad("want a digit after '.'"); }
    if (i_ < t_.size() && (t_[i_] == 'e' || t_[i_] == 'E')) {
      ++i_;
      if (i_ < t_.size() && (t_[i_] == '+' || t_[i_] == '-')) ++i_;
      if (!digits()) return bad("want a digit in the exponent");
    }
    double d = 0;
    const char* first = t_.data() + start;
    const char* last = t_.data() + i_;
    auto [p, ec] = std::from_chars(first, last, d);
    if (ec != std::errc() || p != last || !std::isfinite(d)) { i_ = start; return bad("number out of range"); }
    out = Value::number(d);
    return true;
  }

  std::string_view t_;
  int max_depth_;
  std::size_t i_ = 0;
  std::string err_;
};

void dump_string(std::string& out, const std::string& s) {
  static constexpr char kHex[] = "0123456789abcdef";
  out += '"';
  for (const char c : s) {
    switch (c) {
      case '"': out += "\\\""; break;
      case '\\': out += "\\\\"; break;
      case '\n': out += "\\n"; break;
      case '\r': out += "\\r"; break;
      case '\t': out += "\\t"; break;
      case '\b': out += "\\b"; break;
      case '\f': out += "\\f"; break;
      default:
        if (std::uint8_t(c) < 0x20) {
          out += "\\u00";
          out += kHex[std::uint8_t(c) >> 4];
          out += kHex[std::uint8_t(c) & 0xF];
        } else {
          out += c;
        }
    }
  }
  out += '"';
}

void dump_number(std::string& out, double d) {
  if (!std::isfinite(d)) { out += "null"; return; }
  char buf[32];
  std::to_chars_result r;
  if (d == std::trunc(d) && std::fabs(d) <= kMaxSafeInt) r = std::to_chars(buf, buf + sizeof buf, std::int64_t(d));
  else r = std::to_chars(buf, buf + sizeof buf, d);
  out.append(buf, r.ptr);
}

void dump_into(std::string& out, const Value& v) {
  if (v.is_null()) out += "null";
  else if (const bool* b = v.as_bool()) out += *b ? "true" : "false";
  else if (const double* d = v.as_number()) dump_number(out, *d);
  else if (const std::string* s = v.as_string()) dump_string(out, *s);
  else if (const Array* a = v.as_array()) {
    out += '[';
    for (std::size_t i = 0; i < a->size(); ++i) {
      if (i) out += ',';
      dump_into(out, (*a)[i]);
    }
    out += ']';
  } else if (const Object* o = v.as_object()) {
    out += '{';
    for (std::size_t i = 0; i < o->size(); ++i) {
      if (i) out += ',';
      dump_string(out, (*o)[i].key);
      out += ':';
      dump_into(out, (*o)[i].value);
    }
    out += '}';
  }
}

}  // namespace

std::expected<Value, std::string> parse(std::string_view text, int max_depth) { return Parser(text, max_depth).run(); }

std::string dump(const Value& v) {
  std::string out;
  dump_into(out, v);
  return out;
}

bool fail(std::string& err, const std::string& path, std::string_view why) {
  err = path + ": " + std::string(why);
  return false;
}

bool read(const Value& v, std::string& out, const std::string& path, std::string& err) {
  const std::string* s = v.as_string();
  if (!s) return fail(err, path, "want a string");
  out = *s;
  return true;
}

bool read(const Value& v, bool& out, const std::string& path, std::string& err) {
  const bool* b = v.as_bool();
  if (!b) return fail(err, path, "want true or false");
  out = *b;
  return true;
}

namespace {
std::string show(double d) { std::string s; dump_number(s, d); return s; }
}  // namespace

bool read_num(const Value& v, double& out, double lo, double hi, const std::string& path, std::string& err) {
  const double* d = v.as_number();
  if (!d || !std::isfinite(*d)) return fail(err, path, "want a number");
  if (*d < lo || *d > hi) return fail(err, path, show(*d) + " is outside " + show(lo) + ".." + show(hi));
  out = *d;
  return true;
}

bool read_int(const Value& v, std::int64_t& out, double lo, double hi, const std::string& path, std::string& err) {
  const double* d = v.as_number();
  if (!d || *d != std::trunc(*d) || std::fabs(*d) > kMaxSafeInt) return fail(err, path, "want a whole number");
  if (*d < lo || *d > hi) return fail(err, path, show(*d) + " is outside " + show(lo) + ".." + show(hi));
  out = std::int64_t(*d);
  return true;
}

Fields::Fields(const Value& v, std::string path, std::string& err) : obj_(v.as_object()), path_(std::move(path)), err_(err) {
  if (!obj_) fail(err_, path_, "want an object");
  else used_.assign(obj_->size(), false);
}

const Value* Fields::opt(std::string_view key) {
  for (std::size_t i = 0; i < obj_->size(); ++i)
    if ((*obj_)[i].key == key) { used_[i] = true; return &(*obj_)[i].value; }
  return nullptr;
}

const Value* Fields::req(std::string_view key) {
  const Value* v = opt(key);
  if (!v) fail(err_, path_ + "." + std::string(key), "missing");
  return v;
}

bool Fields::done() {
  for (std::size_t i = 0; i < obj_->size(); ++i)
    if (!used_[i]) return fail(err_, path_ + "." + (*obj_)[i].key, "not in the schema");
  return true;
}

std::string envelope(std::string_view type, std::uint32_t version, Value body) {
  Object o;
  o.push_back({"type", Value::string(std::string(type))});
  o.push_back({"v", Value::number(double(version))});
  o.push_back({"body", std::move(body)});
  return dump(Value::object(std::move(o)));
}

}  // namespace argonia::core::json
