#include "argonia/core/conditions.h"

#include <algorithm>
#include <cmath>

namespace argonia::core::conditions {

using gen::ArgKind;

std::optional<Term> term_named(std::string_view id) {
  for (std::size_t i = 0; i < gen::kTermCount; ++i)
    if (gen::kTermNames[i] == id) return Term(i);
  return std::nullopt;
}

std::string_view name(Term t) { return gen::kTermNames[std::size_t(t)]; }
const gen::TermRow& row(Term t) { return gen::kTerms[std::size_t(t)]; }

bool is_combinator(Term t) {
  const Shape s = row(t).shape;
  return s == Shape::all || s == Shape::any || s == Shape::not_;
}

std::optional<Op> op_named(std::string_view symbol) {
  for (std::size_t i = 0; i < gen::kOpSymbols.size(); ++i)
    if (gen::kOpSymbols[i] == symbol) return Op(i);
  return std::nullopt;
}

bool compare(double lhs, Op op, double rhs) {
  switch (op) {
    case Op::eq: return lhs == rhs;
    case Op::ne: return lhs != rhs;
    case Op::ge: return lhs >= rhs;
    case Op::le: return lhs <= rhs;
    case Op::lt: return lhs < rhs;
    case Op::gt: return lhs > rhs;
  }
  return false;
}

namespace {

std::span<const gen::ArgSpec> specs(Term t) {
  const auto& r = row(t);
  return std::span<const gen::ArgSpec>(gen::kArgSpecs).subspan(r.first_arg, r.arg_count);
}

std::span<const std::string_view> values(Term t) {
  const auto& r = row(t);
  return std::span<const std::string_view>(gen::kValues).subspan(r.first_value, r.value_count);
}

// The position of a term's first argument of a kind, from its spec rows; none when it has no such argument.
std::optional<std::size_t> pos(Term t, ArgKind k) {
  auto sp = specs(t);
  for (std::size_t i = 0; i < sp.size(); ++i)
    if (sp[i].kind == k) return i;
  return std::nullopt;
}

std::optional<std::size_t> rank(Term t, std::string_view v) {
  auto vs = values(t);
  auto it = std::find(vs.begin(), vs.end(), v);
  if (it == vs.end()) return std::nullopt;
  return std::size_t(it - vs.begin());
}

std::string text(const Arg& a) {
  if (auto s = std::get_if<std::string>(&a)) return *s;
  if (auto d = std::get_if<double>(&a)) {
    std::string s = std::to_string(*d);
    s.erase(s.find_last_not_of('0') + 1);
    if (!s.empty() && s.back() == '.') s.pop_back();
    return s;
  }
  return std::get<bool>(a) ? "true" : "false";
}

bool integral(const Arg& a) {
  auto d = std::get_if<double>(&a);
  return d && std::isfinite(*d) && std::floor(*d) == *d;
}

// An hour-range form of timeOfDay: two integral hours.
bool hour_range(const Pred& p) {
  return p.term == Term::timeOfDay && p.args.size() == std::size_t(gen::conditions::hour_range_args) &&
         std::all_of(p.args.begin(), p.args.end(), integral);
}

std::optional<std::string> check_args(const Pred& p) {
  if (hour_range(p)) return std::nullopt;
  auto sp = specs(p.term);
  std::size_t need = 0;
  for (const auto& s : sp) need += s.optional ? 0 : 1;
  if (p.args.size() < need || p.args.size() > sp.size())
    return "takes " + std::to_string(need) + (need == sp.size() ? "" : "-" + std::to_string(sp.size())) +
           " argument(s), got " + std::to_string(p.args.size());
  for (std::size_t i = 0; i < p.args.size(); ++i) {
    const Arg& a = p.args[i];
    const auto at = "argument " + std::to_string(i + 1) + " ";
    switch (sp[i].kind) {
      case ArgKind::id:
        if (!std::holds_alternative<std::string>(a) || std::get<std::string>(a).empty()) return at + "must be an id";
        break;
      case ArgKind::int_:
        if (!integral(a)) return at + "must be a whole number";
        break;
      case ArgKind::bool_:
        if (!std::holds_alternative<bool>(a) && !(integral(a) && (std::get<double>(a) == 0 || std::get<double>(a) == 1)))
          return at + "must be a flag";
        break;
      case ArgKind::op:
        if (!std::holds_alternative<std::string>(a) || !op_named(std::get<std::string>(a)))
          return at + "must be one of = ≠ ≥ ≤ < >";
        break;
      case ArgKind::enum_:
        if (!std::holds_alternative<std::string>(a)) return at + "must be a value";
        if (!values(p.term).empty() && !rank(p.term, std::get<std::string>(a)))
          return at + "'" + std::get<std::string>(a) + "' is not one of its values";
        break;
    }
  }
  return std::nullopt;
}

std::optional<std::string> check_at(const Pred& p, const std::string& path) {
  if (std::size_t(p.term) >= gen::kTermCount) return (path.empty() ? "" : path + "/") + "?: not a term";
  const std::string here = path.empty() ? std::string(name(p.term)) : path + "/" + std::string(name(p.term));
  if (is_combinator(p.term)) {
    if (!p.args.empty()) return here + ": a combinator takes no arguments";
    if (row(p.term).shape == Shape::not_ && p.children.size() != 1) return here + ": takes exactly one condition";
    for (std::size_t i = 0; i < p.children.size(); ++i)
      if (auto e = check_at(p.children[i], here + "[" + std::to_string(i) + "]")) return e;
    return std::nullopt;
  }
  if (!p.children.empty()) return here + ": a predicate has no children";
  if (auto e = check_args(p)) return here + ": " + *e;
  return std::nullopt;
}

Tri tri(bool b) { return b ? Tri::yes : Tri::no; }

struct Eval {
  const Facts& f;
  std::vector<std::string>& unanswered;

  template <class T>
  std::optional<T> ask(std::optional<T> v, const Pred& p) {
    if (!v) unanswered.push_back(describe(p.term, p.args));
    return v;
  }

  Tri leaf(const Pred& p) {
    std::span<const Arg> args(p.args);
    const auto all_keys = args;
    const auto keys_but_last = args.empty() ? args : args.first(args.size() - 1);
    switch (row(p.term).shape) {
      case Shape::truth: {
        auto v = ask(f.truth(p.term, all_keys), p);
        return v ? tri(*v) : Tri::unknown;
      }
      case Shape::flag: {
        auto keys = args.first(1);
        const std::size_t at = *pos(p.term, ArgKind::bool_);
        bool want = args.size() <= at ? true
                                      : (std::holds_alternative<bool>(args[at]) ? std::get<bool>(args[at])
                                                                                : std::get<double>(args[at]) != 0);
        auto v = ask(f.truth(p.term, keys), p);
        return v ? tri(*v == want) : Tri::unknown;
      }
      case Shape::at_least: {
        // The threshold is the last whole-number argument; hasItem's count may be left out (one).
        const auto spec = specs(p.term);
        const bool threshold_given = args.size() == spec.size();
        const double need = threshold_given ? std::get<double>(args.back()) : 1.0;
        auto v = ask(f.number(p.term, threshold_given ? keys_but_last : all_keys), p);
        return v ? tri(*v >= need) : Tri::unknown;
      }
      case Shape::compare: {
        auto v = ask(f.number(p.term, args.first(1)), p);
        if (!v) return Tri::unknown;
        const Arg& op = args[*pos(p.term, ArgKind::op)];
        const Arg& rhs = args[*pos(p.term, ArgKind::int_)];
        return tri(compare(*v, *op_named(std::get<std::string>(op)), std::get<double>(rhs)));
      }
      case Shape::is: {
        auto v = ask(f.state(p.term, keys_but_last), p);
        return v ? tri(*v == std::get<std::string>(args.back())) : Tri::unknown;
      }
      case Shape::rank_at_least: {
        auto v = ask(f.state(p.term, keys_but_last), p);
        if (!v) return Tri::unknown;
        auto have = rank(p.term, *v);
        auto want = rank(p.term, std::get<std::string>(args.back()));
        if (!have || !want) {  // a value outside the closed set is not an answer
          unanswered.push_back(describe(p.term, p.args) + " = " + *v);
          return Tri::unknown;
        }
        return tri(*have >= *want);
      }
      case Shape::after:
      case Shape::before: {
        auto v = ask(f.number(p.term, {}), p);
        if (!v) return Tri::unknown;
        const double day = std::get<double>(args[0]);
        return tri(row(p.term).shape == Shape::after ? *v > day : *v < day);
      }
      case Shape::calendar: {
        // Keys name the part asked for: "month", "day", "season".
        const std::vector<Arg> month{std::string("month")}, day{std::string("day")}, season{std::string("season")};
        auto m = ask(f.state(p.term, month), p);
        if (!m) return Tri::unknown;
        if (*m != std::get<std::string>(args[0])) return Tri::no;
        const std::size_t day_at = *pos(p.term, ArgKind::int_), season_at = *pos(p.term, ArgKind::enum_);
        if (args.size() > day_at) {
          auto d = ask(f.number(p.term, day), p);
          if (!d) return Tri::unknown;
          if (*d != std::get<double>(args[day_at])) return Tri::no;
        }
        if (args.size() > season_at) {
          auto s = ask(f.state(p.term, season), p);
          if (!s) return Tri::unknown;
          if (*s != std::get<std::string>(args[season_at])) return Tri::no;
        }
        return Tri::yes;
      }
      case Shape::time_of_day: {
        if (hour_range(p)) {
          auto h = ask(f.number(p.term, {}), p);
          if (!h) return Tri::unknown;
          const double from = std::get<double>(args.front()), to = std::get<double>(args.back());
          return tri(from <= to ? (*h >= from && *h < to) : (*h >= from || *h < to));  // a range may wrap midnight
        }
        auto v = ask(f.state(p.term, {}), p);
        return v ? tri(*v == std::get<std::string>(args[0])) : Tri::unknown;
      }
      case Shape::all:
      case Shape::any:
      case Shape::not_: break;
    }
    return Tri::unknown;
  }

  Tri node(const Pred& p) {
    switch (row(p.term).shape) {
      case Shape::all: {
        Tri out = Tri::yes;
        for (const auto& c : p.children) {
          Tri v = node(c);
          if (v == Tri::no) return Tri::no;
          if (v == Tri::unknown) out = Tri::unknown;
        }
        return out;
      }
      case Shape::any: {
        Tri out = Tri::no;
        for (const auto& c : p.children) {
          Tri v = node(c);
          if (v == Tri::yes) return Tri::yes;
          if (v == Tri::unknown) out = Tri::unknown;
        }
        return out;
      }
      case Shape::not_: {
        Tri v = node(p.children.front());
        return v == Tri::unknown ? v : tri(v == Tri::no);
      }
      default: return leaf(p);
    }
  }
};

void collect(const Pred& p, std::vector<MirrorKey>& out) {
  if (is_combinator(p.term)) {
    for (const auto& c : p.children) collect(c, out);
    return;
  }
  if (!row(p.term).native.empty()) return;
  MirrorKey k{p.term, p.args};
  if (std::find(out.begin(), out.end(), k) == out.end()) out.push_back(std::move(k));
}

}  // namespace

std::optional<std::string> check(const Pred& p) { return check_at(p, ""); }

std::expected<Pred, std::string> make(Term t, std::vector<Arg> args, std::vector<Pred> children) {
  Pred p{t, std::move(args), std::move(children)};
  if (auto e = check(p)) return std::unexpected(*e);
  return p;
}

std::expected<Pred, std::string> make(std::string_view term, std::vector<Arg> args, std::vector<Pred> children) {
  auto t = term_named(term);
  if (!t) return std::unexpected("'" + std::string(term) + "' is not in the vocabulary");
  return make(*t, std::move(args), std::move(children));
}

std::expected<Pred, std::string> from_flat(std::span<const FlatNode> nodes) {
  if (nodes.empty() || nodes[0].parent != -1) return std::unexpected("a tree starts with its root (parent -1)");
  std::vector<Pred> built(nodes.size());
  for (std::size_t i = 0; i < nodes.size(); ++i) {
    auto t = term_named(nodes[i].term);
    if (!t) return std::unexpected("'" + std::string(nodes[i].term) + "' is not in the vocabulary");
    if (i > 0 && (nodes[i].parent < 0 || std::size_t(nodes[i].parent) >= i))
      return std::unexpected("node " + std::to_string(i) + ": its parent must come before it");
    built[i] = Pred{*t, nodes[i].args, {}};
  }
  // Attach from the last node back, so each child is whole (its own children gathered, last first, then put back in
  // order) before it moves into its parent.
  for (std::size_t i = nodes.size(); i-- > 1;) {
    std::reverse(built[i].children.begin(), built[i].children.end());
    built[std::size_t(nodes[i].parent)].children.push_back(std::move(built[i]));
  }
  std::reverse(built[0].children.begin(), built[0].children.end());
  if (auto e = check(built[0])) return std::unexpected(*e);
  return std::move(built[0]);
}

Pred all(std::vector<Pred> c) { return Pred{Term::all, {}, std::move(c)}; }
Pred any(std::vector<Pred> c) { return Pred{Term::any, {}, std::move(c)}; }
Pred negate(Pred c) { return Pred{Term::not_, {}, {std::move(c)}}; }

Verdict evaluate(const Pred& p, const Facts& f) {
  Verdict v{Tri::unknown, {}};
  if (auto e = check(p)) {
    v.unanswered.push_back("invalid: " + *e);
    return v;
  }
  Eval ev{f, v.unanswered};
  v.value = ev.node(p);
  return v;
}

Verdict evaluate_valid(const Pred& p, const Facts& f) {
  Verdict v{Tri::unknown, {}};
  Eval ev{f, v.unanswered};
  v.value = ev.node(p);
  return v;
}

bool eval(const Pred& p, const Facts& f) { return evaluate(p, f).holds(); }

std::vector<MirrorKey> mirrors(std::span<const Pred> roots) {
  std::vector<MirrorKey> out;
  for (const auto& r : roots) collect(r, out);
  return out;
}

std::string describe(Term t, std::span<const Arg> args) {
  std::string s(name(t));
  s += "(";
  for (std::size_t i = 0; i < args.size(); ++i) s += (i ? ", " : "") + text(args[i]);
  return s + ")";
}

}  // namespace argonia::core::conditions
