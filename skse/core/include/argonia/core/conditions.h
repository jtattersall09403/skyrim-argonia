// The condition vocabulary as a typed predicate tree (85 §A, §D; native map P2). Each term's evaluation shape and
// argument kinds come from the condition_shape tables; the facts come from ArgoniaCore through `Facts`. Evaluation
// is three-valued: a fact the host cannot answer makes the predicate unknown, never silently false, and an unknown
// root does not hold.
#pragma once
#include "argonia/core/tables_conditions.h"

#include <expected>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <variant>
#include <vector>

namespace argonia::core::conditions {

using gen::Op;
using gen::Shape;
using gen::Term;

// An argument: an id or enum value (text), a number, or a flag.
using Arg = std::variant<std::string, double, bool>;

struct Pred {
  Term term;
  std::vector<Arg> args;       // a predicate's arguments
  std::vector<Pred> children;  // a combinator's children
  bool operator==(const Pred&) const = default;
};

std::optional<Term> term_named(std::string_view id);
std::string_view name(Term t);
const gen::TermRow& row(Term t);
bool is_combinator(Term t);

// Why a tree breaks the vocabulary (wrong child count, arity, argument kind, an enum value outside the closed set,
// an unknown op), with the path of the first bad node; none when valid.
std::optional<std::string> check(const Pred& p);
// A validated node, or why not.
std::expected<Pred, std::string> make(Term t, std::vector<Arg> args, std::vector<Pred> children = {});
std::expected<Pred, std::string> make(std::string_view term, std::vector<Arg> args, std::vector<Pred> children = {});
Pred all(std::vector<Pred> c);
Pred any(std::vector<Pred> c);
Pred negate(Pred c);

// What ArgoniaCore knows. `keys` are the predicate's identifying arguments (every argument but the one compared).
// Each answer is optional: none means the host cannot answer, and the predicate is unknown.
class Facts {
 public:
  virtual ~Facts() = default;
  virtual std::optional<bool> truth(Term t, std::span<const Arg> keys) const = 0;
  virtual std::optional<double> number(Term t, std::span<const Arg> keys) const = 0;
  virtual std::optional<std::string> state(Term t, std::span<const Arg> keys) const = 0;
};

enum class Tri { no, yes, unknown };
struct Verdict {
  Tri value;
  std::vector<std::string> unanswered;  // "term(args)" for each fact the host could not answer
  bool holds() const { return value == Tri::yes; }
};

Verdict evaluate(const Pred& p, const Facts& f);
bool eval(const Pred& p, const Facts& f);  // evaluate(...).holds(); an invalid tree never holds

// P2: one key per predicate instance that Skyrim cannot test natively, so ArgoniaCore publishes it as a global.
struct MirrorKey {
  Term term;
  std::vector<Arg> args;
  bool operator==(const MirrorKey&) const = default;
};
std::vector<MirrorKey> mirrors(std::span<const Pred> roots);  // distinct, in first-seen order
std::string describe(Term t, std::span<const Arg> args);     // "questStage(quest.x, ≥, 60)"

std::optional<Op> op_named(std::string_view symbol);
bool compare(double lhs, Op op, double rhs);

}  // namespace argonia::core::conditions
