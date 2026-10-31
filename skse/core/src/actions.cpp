#include "argonia/core/actions.h"

#include "argonia/core/disposition.h"

#include <cmath>
#include <map>

namespace argonia::core::actions {

using gen::ActionArgKind;
using conditions::Term;

std::optional<Verb> verb_named(std::string_view id) {
  for (std::size_t i = 0; i < gen::kVerbCount; ++i)
    if (gen::kVerbNames[i] == id) return Verb(i);
  return std::nullopt;
}

std::string_view name(Verb v) { return gen::kVerbNames[std::size_t(v)]; }

namespace {

std::span<const gen::ActionArgSpec> specs(Verb v) {
  const auto& r = gen::kVerbs[std::size_t(v)];
  return std::span<const gen::ActionArgSpec>(gen::kActionArgSpecs).subspan(r.first_arg, r.arg_count);
}

bool integral(const Arg& a) {
  auto d = std::get_if<double>(&a);
  return d && std::isfinite(*d) && std::floor(*d) == *d;
}

std::string_view id(const Action& a, std::size_t i) { return std::get<std::string>(a.args[i]); }
// A whole-number argument, or `dflt` when an optional one is left out.
int whole(const Action& a, std::size_t i, int dflt) {
  return i < a.args.size() ? int(std::get<double>(a.args[i])) : dflt;
}
bool flag(const Action& a, std::size_t i, bool dflt) {
  if (i >= a.args.size()) return dflt;
  if (auto b = std::get_if<bool>(&a.args[i])) return *b;
  return std::get<double>(a.args[i]) != 0;
}

}  // namespace

std::optional<std::string> check(const Action& a) {
  if (std::size_t(a.verb) >= gen::kVerbCount) return "?: not a verb";
  const std::string here(name(a.verb));
  auto sp = specs(a.verb);
  std::size_t need = 0;
  for (const auto& s : sp) need += s.optional ? 0 : 1;
  if (a.args.size() < need || a.args.size() > sp.size())
    return here + ": takes " + std::to_string(need) + (need == sp.size() ? "" : "-" + std::to_string(sp.size())) +
           " argument(s), got " + std::to_string(a.args.size());
  for (std::size_t i = 0; i < a.args.size(); ++i) {
    const Arg& x = a.args[i];
    const auto at = here + ": argument " + std::to_string(i + 1) + " ";
    switch (sp[i].kind) {
      case ActionArgKind::id:
        if (!std::holds_alternative<std::string>(x) || std::get<std::string>(x).empty()) return at + "must be an id";
        break;
      case ActionArgKind::int_:
        if (!integral(x)) return at + "must be a whole number";
        break;
      case ActionArgKind::bool_:
        if (!std::holds_alternative<bool>(x) && !(integral(x) && (std::get<double>(x) == 0 || std::get<double>(x) == 1)))
          return at + "must be a flag";
        break;
    }
  }
  return std::nullopt;
}

std::expected<Action, std::string> make(Verb v, std::vector<Arg> args) {
  Action a{v, std::move(args)};
  if (auto e = check(a)) return std::unexpected(*e);
  return a;
}

std::expected<Action, std::string> make(std::string_view verb, std::vector<Arg> args) {
  auto v = verb_named(verb);
  if (!v) return std::unexpected("'" + std::string(verb) + "' is not an action verb");
  return make(*v, std::move(args));
}

std::string describe(const Action& a) {
  // The condition side's rendering of arguments, under the verb's name.
  auto s = conditions::describe(Term::all, a.args);
  return std::string(name(a.verb)) + s.substr(conditions::name(Term::all).size());
}

Outcome run(std::span<const Action> list, const conditions::Facts& facts, Effects& fx) {
  Outcome out;
  for (const auto& a : list)
    if (auto e = check(a)) out.refused.push_back("invalid: " + *e);
  if (!out.refused.empty()) return out;

  // What the list takes from the player, summed, against what the player has: nothing changes when it falls short.
  int gold = 0;
  std::map<std::string, int, std::less<>> items;
  for (const auto& a : list) {
    if (a.verb == Verb::takeGold) gold += whole(a, 0, 0);
    if (a.verb == Verb::takeItem) items[std::string(id(a, 0))] += whole(a, 1, 1);
  }
  if (gold > 0) {
    auto have = facts.number(Term::goldAtLeast, {});
    if (!have) out.refused.push_back("goldAtLeast(): unanswered");
    else if (*have < gold) out.refused.push_back("takeGold: has " + std::to_string(int(*have)) + ", needs " + std::to_string(gold));
  }
  for (const auto& [item, n] : items) {
    const std::vector<Arg> key{item};
    auto have = facts.number(Term::hasItem, key);
    if (!have) out.refused.push_back("hasItem(" + item + "): unanswered");
    else if (*have < n) out.refused.push_back("takeItem(" + item + "): has " + std::to_string(int(*have)) + ", needs " + std::to_string(n));
  }
  if (!out.refused.empty()) return out;

  for (const auto& a : list) {
    bool ok = false;
    switch (a.verb) {
      case Verb::takeGold: ok = fx.takeGold(whole(a, 0, 0)); break;
      case Verb::giveGold: ok = fx.giveGold(whole(a, 0, 0)); break;
      case Verb::takeItem: ok = fx.takeItem(id(a, 0), whole(a, 1, 1)); break;
      case Verb::giveItem: ok = fx.giveItem(id(a, 0), whole(a, 1, 1)); break;
      case Verb::setFlag: ok = fx.setFlag(id(a, 0), flag(a, 1, true)); break;
      case Verb::grantTopic: ok = fx.grantTopic(id(a, 0)); break;
      case Verb::applyLocalVariant: ok = fx.applyLocalVariant(id(a, 0), id(a, 1)); break;
      case Verb::setPrice: ok = fx.setPrice(id(a, 0), whole(a, 1, 0)); break;
      case Verb::changeDisposition: {
        int delta = whole(a, 1, 0);
        const std::vector<Arg> key{std::string(id(a, 0))};
        if (auto d = facts.number(Term::dispositionAtLeast, key)) {
          const int now = disposition::clamp(*d);
          delta = disposition::apply(now, {delta}) - now;
        }
        ok = fx.changeDisposition(id(a, 0), delta);
        break;
      }
      case Verb::openBarter: ok = fx.openBarter(id(a, 0)); break;
      case Verb::changeSettlementStanding: ok = fx.changeSettlementStanding(id(a, 0), whole(a, 1, 0)); break;
      default: ok = fx.other(a); break;
    }
    if (!ok) {
      out.refused.push_back(describe(a) + ": refused by the game");
      return out;
    }
    ++out.applied;
  }
  out.done = true;
  return out;
}

}  // namespace argonia::core::actions
