// L2: the condition tree over the vocabulary (85 §A, §D): validation of every failure shape, each evaluation shape
// against a stub Facts, three-valued unknowns, the 1.3 §b first predicates and P2's mirror list.
#include "check.h"
#include "argonia/core/conditions.h"

#include <map>
#include <string>

using namespace argonia::core::conditions;
namespace gen = argonia::core::gen;

namespace {

std::string key(Term t, std::span<const Arg> keys) {
  return describe(t, keys);
}

struct Stub : Facts {
  std::map<std::string, bool> truths;
  std::map<std::string, double> numbers;
  std::map<std::string, std::string> states;
  std::optional<bool> truth(Term t, std::span<const Arg> k) const override {
    auto it = truths.find(key(t, k));
    return it == truths.end() ? std::nullopt : std::optional<bool>(it->second);
  }
  std::optional<double> number(Term t, std::span<const Arg> k) const override {
    auto it = numbers.find(key(t, k));
    return it == numbers.end() ? std::nullopt : std::optional<double>(it->second);
  }
  std::optional<std::string> state(Term t, std::span<const Arg> k) const override {
    auto it = states.find(key(t, k));
    return it == states.end() ? std::nullopt : std::optional<std::string>(it->second);
  }
};

Pred P(std::string_view term, std::vector<Arg> args) {
  auto p = make(term, std::move(args));
  CHECK(p.has_value());
  return p ? *p : Pred{Term::all, {}, {}};
}

void vocabulary_complete() {
  CHECK(gen::kTermCount == 65);  // 62 predicates + all, any, not (the condition_term rows)
  for (std::size_t i = 0; i < gen::kTermCount; ++i) CHECK(term_named(gen::kTermNames[i]) == Term(i));
  CHECK(!term_named("luckAtLeast"));
  CHECK(name(Term::not_) == "not");
}

void validation_failures() {
  CHECK(!make("knowsTopic", {}).has_value());                                    // arity
  CHECK(!make("knowsTopic", {1.0}).has_value());                                 // kind: an id
  CHECK(!make("knowsTopic", {std::string("")}).has_value());                      // an empty id
  CHECK(!make("dispositionAtLeast", {std::string("npc.a"), 30.5}).has_value());  // a whole number
  CHECK(!make("questStage", {std::string("quest.a"), std::string("=>"), 10.0}).has_value());  // op
  CHECK(!make("questState", {std::string("quest.a"), std::string("begun")}).has_value());     // closed set
  CHECK(!make("frobnicate", {}).has_value());
  CHECK(!make(Term::not_, {}, {}).has_value());                                  // not takes one
  CHECK(!make(Term::all, {1.0}, {}).has_value());                                // a combinator takes no args
  auto e = make(Term::all, {}, {Pred{Term::knowsTopic, {}, {}}});
  CHECK(!e.has_value() && e.error().find("all[0]/knowsTopic") != std::string::npos);  // the path of the bad node
  CHECK(make("hasItem", {std::string("item.a")}).has_value());                  // the count may be left out
  CHECK(make("flag", {std::string("flag.a"), 1.0}).has_value());                // a flag as 0/1, as the rows hold it
  CHECK(!make("flag", {std::string("flag.a"), 2.0}).has_value());
  CHECK(make("timeOfDay", {6.0, 20.0}).has_value());                            // the hour-range form
  CHECK(make("notorietyTier", {std::string("region.a"), std::string("hunted")}).has_value());  // an open set
}

void first_predicates() {  // 1.3 §b: knowsTopic, disposition, quest stage, item count, faction rank
  Stub f;
  f.truths["knowsTopic(topic.eel)"] = true;
  f.numbers["dispositionAtLeast(npc.b)"] = 40;
  f.numbers["questStage(quest.q)"] = 60;
  f.numbers["hasItem(item.rope)"] = 2;
  f.numbers["factionRankAtLeast(faction.f)"] = 1;
  CHECK(eval(P("knowsTopic", {std::string("topic.eel")}), f));
  CHECK(eval(P("dispositionAtLeast", {std::string("npc.b"), 30.0}), f));
  CHECK(!eval(P("dispositionAtLeast", {std::string("npc.b"), 70.0}), f));
  CHECK(eval(P("questStage", {std::string("quest.q"), std::string("≥"), 60.0}), f));
  CHECK(!eval(P("questStage", {std::string("quest.q"), std::string(">"), 60.0}), f));
  CHECK(eval(P("questStage", {std::string("quest.q"), std::string("≠"), 10.0}), f));
  CHECK(eval(P("hasItem", {std::string("item.rope")}), f));
  CHECK(!eval(P("hasItem", {std::string("item.rope"), 3.0}), f));
  CHECK(eval(P("factionRankAtLeast", {std::string("faction.f"), 1.0}), f));
}

void other_shapes() {
  Stub f;
  f.truths["flag(flag.a)"] = false;
  f.states["questState(quest.q)"] = "active";
  f.states["histStepAtLeast()"] = "heard";
  f.numbers["dateAfter()"] = 100;
  f.numbers["dateBefore()"] = 100;
  f.states["timeOfDay()"] = "night";
  f.numbers["timeOfDay()"] = 23;
  f.states["calendarIs(month)"] = "Sun's Dawn";
  f.numbers["calendarIs(day)"] = 3;
  f.states["calendarIs(season)"] = "dry";
  f.truths["stageEverReached(quest.q, 20)"] = true;
  CHECK(eval(P("flag", {std::string("flag.a"), 0.0}), f));
  CHECK(!eval(P("flag", {std::string("flag.a")}), f));
  CHECK(eval(P("questState", {std::string("quest.q"), std::string("active")}), f));
  CHECK(eval(P("histStepAtLeast", {std::string("touched")}), f));
  CHECK(eval(P("histStepAtLeast", {std::string("heard")}), f));
  CHECK(!eval(P("histStepAtLeast", {std::string("sap-speaker")}), f));
  CHECK(eval(P("dateAfter", {99.0}), f) && !eval(P("dateAfter", {100.0}), f));
  CHECK(eval(P("dateBefore", {101.0}), f) && !eval(P("dateBefore", {100.0}), f));
  CHECK(eval(P("timeOfDay", {std::string("night")}), f));
  CHECK(eval(P("timeOfDay", {22.0, 4.0}), f));   // wraps midnight
  CHECK(!eval(P("timeOfDay", {6.0, 20.0}), f));
  CHECK(eval(P("calendarIs", {std::string("Sun's Dawn")}), f));
  CHECK(eval(P("calendarIs", {std::string("Sun's Dawn"), 3.0, std::string("dry")}), f));
  CHECK(!eval(P("calendarIs", {std::string("Sun's Dawn"), 4.0}), f));
  CHECK(eval(P("stageEverReached", {std::string("quest.q"), 20.0}), f));
}

void unknowns_never_hold() {
  Stub f;
  f.truths["npcAlive(npc.a)"] = true;
  Pred unknown = P("witnessed", {std::string("event.e")});
  Pred yes = P("npcAlive", {std::string("npc.a")});
  Verdict v = evaluate(unknown, f);
  CHECK(v.value == Tri::unknown && !v.holds());
  CHECK(v.unanswered.size() == 1 && v.unanswered[0] == "witnessed(event.e)");
  CHECK(evaluate(negate(unknown), f).value == Tri::unknown);  // not(unknown) is not true
  CHECK(evaluate(all({yes, unknown}), f).value == Tri::unknown);
  CHECK(evaluate(all({negate(yes), unknown}), f).value == Tri::no);  // a false child decides
  CHECK(evaluate(any({yes, unknown}), f).value == Tri::yes);
  CHECK(evaluate(any({unknown}), f).value == Tri::unknown);
  CHECK(eval(all({}), f));    // all of nothing holds
  CHECK(!eval(any({}), f));   // any of nothing does not
  CHECK(!eval(Pred{Term::not_, {}, {}}, f));  // an invalid tree never holds
  CHECK(evaluate(Pred{Term::not_, {}, {}}, f).unanswered[0].rfind("invalid", 0) == 0);
  CHECK(check(Pred{Term(200), {}, {}}).value_or("").find("not a term") != std::string::npos);  // no read past the table
  Stub g;
  g.states["histStepAtLeast()"] = "renamed-step";  // a value outside the closed set is not an answer
  Verdict r = evaluate(P("histStepAtLeast", {std::string("touched")}), g);
  CHECK(r.value == Tri::unknown && r.unanswered.size() == 1);
  CHECK(evaluate(negate(P("histStepAtLeast", {std::string("touched")})), g).value == Tri::unknown);
  CHECK(evaluate_valid(all({yes, unknown}), f).value == Tri::unknown);
  CHECK(evaluate_valid(yes, f).holds());
}

void mirrors_for_p2() {
  Pred stage = P("questStage", {std::string("quest.q"), std::string("≥"), 10.0});     // native: GetStage
  Pred topic = P("knowsTopic", {std::string("topic.t")});
  Pred heard = P("topicHeardFrom", {std::string("topic.t"), std::string("npc.b")});
  std::vector<Pred> roots{all({stage, topic, negate(topic)}), any({heard, topic})};
  auto m = mirrors(roots);
  CHECK(m.size() == 2);
  CHECK(m[0].term == Term::knowsTopic && m[1].term == Term::topicHeardFrom);
  CHECK(row(Term::questStage).native == "GetStage");
  CHECK(row(Term::hasItem).native == "GetItemCount");
  CHECK(row(Term::knowsTopic).native.empty());
}


// LF83's terms (the Claywater quest), each true, false and unanswered against the stub.
void lf83_terms() {
  const std::string topic = "topic.t", npc = "npc.n", quest = "quest.q", obj = "obj.o", item = "item.i";
  Stub s;
  auto truth_case = [&](Pred p, const std::string& k) {
    CHECK(evaluate(p, s).value == Tri::unknown);
    s.truths[k] = true;
    CHECK(eval(p, s));
    s.truths[k] = false;
    CHECK(!eval(p, s) && evaluate(p, s).value == Tri::no);
  };
  truth_case(P("topicHeardFrom", {topic, npc}), "topicHeardFrom(topic.t, npc.n)");
  truth_case(P("objectiveComplete", {quest, obj}), "objectiveComplete(quest.q, obj.o)");
  truth_case(P("npcAlive", {npc}), "npcAlive(npc.n)");
  // flag: the wanted value is the optional second argument (true when left out); the key is the flag alone.
  Pred raised = P("flag", {std::string("flag.f"), 1.0}), lowered = P("flag", {std::string("flag.f"), false});
  CHECK(evaluate(raised, s).value == Tri::unknown);
  s.truths["flag(flag.f)"] = true;
  CHECK(eval(raised, s) && !eval(lowered, s) && eval(P("flag", {std::string("flag.f")}), s));
  s.truths["flag(flag.f)"] = false;
  CHECK(!eval(raised, s) && eval(lowered, s));
  // hasItem: the count is the threshold (one when left out), asked by item alone.
  Pred two = P("hasItem", {item, 2.0}), any_ = P("hasItem", {item});
  CHECK(evaluate(two, s).value == Tri::unknown);
  s.numbers["hasItem(item.i)"] = 1;
  CHECK(!eval(two, s) && eval(any_, s));
  s.numbers["hasItem(item.i)"] = 2;
  CHECK(eval(two, s));
  s.numbers["hasItem(item.i)"] = 0;
  CHECK(!eval(any_, s));
  // goldAtLeast and speakerDispositionAtLeast: a number with no key, at or above the threshold.
  for (std::string_view t : {"goldAtLeast", "speakerDispositionAtLeast"}) {
    Pred p = P(t, {70.0});
    const std::string k = std::string(t) + "()";
    CHECK(evaluate(p, s).value == Tri::unknown);
    s.numbers[k] = 69;
    CHECK(!eval(p, s));
    s.numbers[k] = 70;
    CHECK(eval(p, s));
  }
  CHECK(!make("goldAtLeast", {std::string("100")}).has_value());
  // seasonIs: a state, compared as given.
  Pred wet = P("seasonIs", {std::string("wet")});
  // seasonIs has no closed set yet: the rows use dry, dry-peak, wet, wet-peak, weather has dry, hatching, wet.
  CHECK(evaluate(wet, s).value == Tri::unknown);
  s.states["seasonIs()"] = "dry";
  CHECK(!eval(wet, s));
  s.states["seasonIs()"] = "wet";
  CHECK(eval(wet, s));
}

// from_flat: preorder rows with parent indices rebuild the same tree make() would, children in order.
void flat_trees() {
  std::vector<FlatNode> rows{{-1, "all", {}},
                             {0, "questStage", {std::string("quest.q"), std::string("="), 30.0}},
                             {0, "not", {}},
                             {2, "any", {}},
                             {3, "flag", {std::string("flag.a"), 1.0}},
                             {3, "hasItem", {std::string("item.i"), 1.0}},
                             {0, "seasonIs", {std::string("dry")}}};
  auto t = from_flat(rows);
  CHECK(t.has_value());
  if (t) {
    Pred want = all({P("questStage", {std::string("quest.q"), std::string("="), 30.0}),
                     negate(any({P("flag", {std::string("flag.a"), 1.0}), P("hasItem", {std::string("item.i"), 1.0})})),
                     P("seasonIs", {std::string("dry")})});
    CHECK(*t == want);
  }
  CHECK(!from_flat({}).has_value());
  std::vector<FlatNode> late{{-1, "all", {}}, {2, "flag", {std::string("f")}}, {0, "flag", {std::string("g")}}};
  CHECK(!from_flat(late).has_value());  // a parent after its child
  std::vector<FlatNode> bad{{-1, "not", {}}};
  CHECK(!from_flat(bad).has_value());  // validated: not takes one
}

}  // namespace

int main() {
  vocabulary_complete();
  validation_failures();
  first_predicates();
  other_shapes();
  unknowns_never_hold();
  mirrors_for_p2();
  lf83_terms();
  flat_trees();
  CHECK(compare(1, Op::le, 1) && compare(0, Op::lt, 1) && !compare(1, Op::eq, 2));
  CHECK(op_named("≥") == Op::ge && !op_named(">="));
  return TEST_MAIN_RESULT("core.conditions");
}
