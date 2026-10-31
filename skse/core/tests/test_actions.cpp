// L2: the action vocabulary (85 §B): validation against the action_shape_arg rows, each verb LF83 needs through a
// recording Effects, the all-or-nothing need check before anything changes, disposition kept inside 0-100, and every
// action list of the Claywater fixture rows valid and run.
#include "check.h"
#include "fixture.h"
#include "argonia/core/actions.h"

#include <map>
#include <string>

using namespace argonia::core;
using namespace argonia::core::actions;
using conditions::Term;

namespace {

struct Facts : conditions::Facts {
  std::map<std::string, double> numbers;
  std::optional<bool> truth(Term, std::span<const Arg>) const override { return std::nullopt; }
  std::optional<double> number(Term t, std::span<const Arg> k) const override {
    auto it = numbers.find(conditions::describe(t, k));
    return it == numbers.end() ? std::nullopt : std::optional<double>(it->second);
  }
  std::optional<std::string> state(Term, std::span<const Arg>) const override { return std::nullopt; }
};

struct Log : Effects {
  std::vector<std::string> done;
  bool refuse_all = false;
  bool note(std::string s) { done.push_back(std::move(s)); return !refuse_all; }
  static std::string n(int v) { return std::to_string(v); }
  bool takeGold(int a) override { return note("takeGold " + n(a)); }
  bool giveGold(int a) override { return note("giveGold " + n(a)); }
  bool takeItem(std::string_view i, int c) override { return note("takeItem " + std::string(i) + " " + n(c)); }
  bool giveItem(std::string_view i, int c) override { return note("giveItem " + std::string(i) + " " + n(c)); }
  bool setFlag(std::string_view f, bool v) override { return note("setFlag " + std::string(f) + (v ? " 1" : " 0")); }
  bool grantTopic(std::string_view t) override { return note("grantTopic " + std::string(t)); }
  bool applyLocalVariant(std::string_view p, std::string_view v) override {
    return note("applyLocalVariant " + std::string(p) + " " + std::string(v));
  }
  bool setPrice(std::string_view s, int p) override { return note("setPrice " + std::string(s) + " " + n(p)); }
  bool changeDisposition(std::string_view x, int d) override { return note("changeDisposition " + std::string(x) + " " + n(d)); }
  bool changeSettlementStanding(std::string_view x, int d) override {
    return note("changeSettlementStanding " + std::string(x) + " " + n(d));
  }
  bool openBarter(std::string_view x) override { return note("openBarter " + std::string(x)); }
  bool other(const Action& a) override { return note("other " + describe(a)); }
};

Action A(std::string_view verb, std::vector<Arg> args) {
  auto a = make(verb, std::move(args));
  CHECK(a.has_value());
  return a ? *a : Action{Verb::setFlag, {std::string("bad")}};
}

const std::string kItem = "item.lf83.clay-basket", kNpc = "npc.w", kPlace = "place.p";

void vocabulary() {
  CHECK(gen::kVerbCount == 44);  // the condition_term rows of kind action
  for (std::size_t i = 0; i < gen::kVerbCount; ++i) CHECK(verb_named(gen::kVerbNames[i]) == Verb(i));
  CHECK(!verb_named("questStage"));
  CHECK(!make("giveItem", {}).has_value());                                       // arity
  CHECK(!make("giveItem", {kItem, 1.5}).has_value());                              // a whole count
  CHECK(!make("takeGold", {std::string("ten")}).has_value());                      // kind
  CHECK(!make("setFlag", {std::string("flag.f"), 2.0}).has_value());               // a flag
  CHECK(!make("grantTopic", {std::string("")}).has_value());                       // an empty id
  CHECK(!make("frob", {}).has_value());
  CHECK(make("giveItem", {kItem}).has_value() && make("setFlag", {std::string("flag.f")}).has_value());  // optionals
  CHECK(describe(A("giveItem", {kItem, 2.0})) == "giveItem(item.lf83.clay-basket, 2)");
}

void each_verb() {
  Facts f;
  f.numbers["goldAtLeast()"] = 150;
  f.numbers["hasItem(" + kItem + ")"] = 1;
  f.numbers["dispositionAtLeast(" + kNpc + ")"] = 50;
  Log fx;
  std::vector<Action> list{A("takeGold", {100.0}), A("takeItem", {kItem}), A("giveItem", {std::string("item.x"), 2.0}),
                           A("setFlag", {std::string("flag.a"), 1.0}), A("setFlag", {std::string("flag.b"), false}),
                           A("grantTopic", {std::string("topic.t")}), A("applyLocalVariant", {kPlace, std::string("v")}),
                           A("setPrice", {std::string("ferry.f"), 0.0}), A("changeDisposition", {kNpc, 5.0}),
                           A("changeSettlementStanding", {kPlace, 10.0}), A("giveGold", {150.0}),
                           A("openBarter", {kNpc}), A("setStage", {std::string("quest.q"), 10.0})};
  auto o = run(list, f, fx);
  CHECK(o.done && o.applied == list.size() && o.refused.empty());
  const std::vector<std::string> want{"takeGold 100", "takeItem item.lf83.clay-basket 1", "giveItem item.x 2",
                                      "setFlag flag.a 1", "setFlag flag.b 0", "grantTopic topic.t",
                                      "applyLocalVariant place.p v", "setPrice ferry.f 0", "changeDisposition npc.w 5",
                                      "changeSettlementStanding place.p 10", "giveGold 150", "openBarter npc.w",
                                      "other setStage(quest.q, 10)"};
  CHECK(fx.done == want);
}

void needs_before_changes() {
  Facts f;
  f.numbers["goldAtLeast()"] = 99;
  f.numbers["hasItem(" + kItem + ")"] = 1;
  Log fx;
  // Two takes of 50 sum to 100: more than the 99 carried, so nothing happens, not even the setFlag before them.
  std::vector<Action> list{A("setFlag", {std::string("flag.a")}), A("takeGold", {50.0}), A("takeGold", {50.0})};
  auto o = run(list, f, fx);
  CHECK(!o.done && o.applied == 0 && fx.done.empty() && o.refused.size() == 1);
  // Two baskets asked, one carried.
  std::vector<Action> items{A("takeItem", {kItem}), A("takeItem", {kItem, 1.0})};
  CHECK(!run(items, f, fx).done && fx.done.empty());
  // An unanswered count refuses too: the host must be able to say what the player has.
  std::vector<Action> unknown{A("takeItem", {std::string("item.unknown")})};
  CHECK(!run(unknown, f, fx).done && fx.done.empty());
  // An invalid action anywhere refuses the list.
  std::vector<Action> broken{A("grantTopic", {std::string("topic.t")}), Action{Verb::giveItem, {}}};
  auto b = run(broken, f, fx);
  CHECK(!b.done && fx.done.empty() && b.refused.front().find("invalid") == 0);
  // The game refusing stops the list where it refused.
  fx.refuse_all = true;
  std::vector<Action> two{A("grantTopic", {std::string("topic.t")}), A("grantTopic", {std::string("topic.u")})};
  auto r = run(two, f, fx);
  CHECK(!r.done && r.applied == 0 && fx.done.size() == 1);
}

void disposition_stays_in_range() {
  Facts f;
  f.numbers["dispositionAtLeast(" + kNpc + ")"] = 97;
  Log fx;
  std::vector<Action> up{A("changeDisposition", {kNpc, 10.0})};
  CHECK(run(up, f, fx).done && fx.done.back() == "changeDisposition npc.w 3");
  f.numbers["dispositionAtLeast(" + kNpc + ")"] = 4;
  std::vector<Action> down{A("changeDisposition", {kNpc, -10.0})};
  CHECK(run(down, f, fx).done && fx.done.back() == "changeDisposition npc.w -4");
  f.numbers.clear();  // unknown: the host clamps
  CHECK(run(down, f, fx).done && fx.done.back() == "changeDisposition npc.w -10");
}

void fixture_lists() {
  namespace fx_ = argonia::core::gen::fixture;
  std::size_t n = 0;
  for (std::size_t l = 0; l < fx_::kActionLists.size(); ++l)
    for (auto& a : fixture_load::action_list(l)) {
      CHECK(a.has_value());
      ++n;
    }
  CHECK(n == fx_::kActions.size());
}

}  // namespace

int main() {
  vocabulary();
  each_verb();
  needs_before_changes();
  disposition_stays_in_range();
  fixture_lists();
  return TEST_MAIN_RESULT("core.actions");
}
