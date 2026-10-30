// L2: the topic store (1.3 §b, route b) over the generated Claywater fixture (five speakers' rows from the world
// database) and a 300-topic synthetic speaker: the store builds from real rows; a topic learned from one person is
// offered by and asked of another; low, mid and high variants by disposition band; essential topics answer at 0 with
// the line they give at 50; conditioned lines come before the plain fallback; keywords hyperlink whole words; the
// learned set survives its co-save round trip. Prints measured cycle times (no budget is asserted).
#include "check.h"
#include "fixture.h"
#include "argonia/core/topics.h"

#include <chrono>
#include <cstdio>
#include <map>
#include <set>
#include <string>

using namespace argonia::core;
using namespace argonia::core::topics;
using conditions::Arg;
using conditions::Term;
namespace fx = argonia::core::gen::fixture;

namespace {

// A world that answers every fact: the quest stage and season are set, flags and counts default to none.
struct World : Facts {
  double stage = 0;
  std::string season = "dry";
  std::map<std::string, bool> truths;
  std::map<std::string, double> numbers;
  mutable int asked = 0;
  std::optional<bool> truth(Term t, std::span<const Arg> k) const override {
    ++asked;
    auto it = truths.find(conditions::describe(t, k));
    if (it != truths.end()) return it->second;
    return t == Term::npcAlive;  // everyone lives unless a test says otherwise
  }
  std::optional<double> number(Term t, std::span<const Arg> k) const override {
    ++asked;
    if (t == Term::questStage) return stage;
    auto it = numbers.find(conditions::describe(t, k));
    return it == numbers.end() ? 0.0 : it->second;
  }
  std::optional<std::string> state(Term t, std::span<const Arg>) const override {
    ++asked;
    if (t == Term::seasonIs) return season;
    if (t == Term::timeOfDay) return std::string("day");
    if (t == Term::questState) return std::string(stage > 0 ? "active" : "unstarted");
    return std::string();
  }
};

double us_since(std::chrono::steady_clock::time_point t0) {
  return std::chrono::duration<double, std::micro>(std::chrono::steady_clock::now() - t0).count();
}

Store fixture_store() {
  std::vector<std::string> errors;
  auto lines = fixture_load::fixture_lines(errors);
  for (const auto& e : errors) std::fprintf(stderr, "fixture row: %s\n", e.c_str());
  CHECK(errors.empty());
  auto s = Store::build(fixture_load::fixture_topics(), std::move(lines));
  if (!s) {
    for (const auto& e : s.error()) std::fprintf(stderr, "store: %s\n", e.c_str());
    CHECK(false);
    return *Store::build({}, {});
  }
  return std::move(*s);
}

void builds_from_rows(const Store& s) {
  // The real rows' 0145 findings, printed for the writers (lint is the gate's to enforce, not the store's).
  const auto findings = s.lint();
  for (const auto& f : findings) std::printf("lint: %s\n", f.c_str());
  std::printf("lint: %zu line(s) on essential topics read disposition\n", findings.size());
  CHECK(fx::kSpeakers.size() == 5);
  CHECK(s.lines().size() == fx::kLines.size() && s.all().size() == fx::kTopics.size());
  // Every fixture speaker greets at the quest's start in the dry season, at every band.
  World w;
  for (const auto& sp : fx::kSpeakers)
    for (int d : {0, 50, 100}) {
      Known k;
      auto g = greeting(s, Speaker{std::string(sp.id), d}, k, w);
      CHECK(g && !g->text.empty());
    }
}

void refusals() {
  Topic t{"topic.e", "the essential", {}, true}, u{"topic.u", "other", {}, false};
  Line ok{"l.ok", LineType::dialogue, "npc.a", "topic.e", std::nullopt, "words", "", "", {}, {}};
  auto gated = ok;
  gated.id = "l.gated";
  gated.available = conditions::all({*conditions::make("questStage", {std::string("q"), std::string("≥"), 10.0}),
                                     *conditions::make("speakerDispositionAtLeast", {30.0})});
  auto r = Store::build({t, u}, {ok, gated});
  CHECK(r && r->lint().size() == 1 && r->lint()[0].find("l.gated") == 0);
  Line stray{"l.stray", LineType::dialogue, "npc.a", "topic.none", std::nullopt, "w", "", "", {"topic.nolink"}, {}};
  Line greet{"l.greet", LineType::greeting, "npc.a", "topic.u", std::nullopt, "w", "", "", {}, {}};
  auto r2 = Store::build({t, u}, {stray, greet});
  CHECK(!r2 && r2.error().size() == 3);
  auto r3 = Store::build({t, t}, {});
  CHECK(!r3);  // a duplicate id
}

// The speakers that answer a topic at the current facts.
std::vector<std::string_view> answerers(const Store& s, std::string_view topic, const World& w) {
  std::vector<std::string_view> out;
  Known all_known;
  all_known.learn(topic);
  for (const auto& sp : fx::kSpeakers)
    if (answer(s, topic, Speaker{std::string(sp.id), 50}, all_known, w)) out.push_back(sp.id);
  return out;
}

void learned_from_a_asked_of_b(const Store& s) {
  World w;
  w.stage = 10;
  // A topic two people answer, which person A's greeting or an answer of A's teaches.
  bool tried = false;
  for (const auto& t : s.all()) {
    auto who = answerers(s, t.id, w);
    if (who.size() < 2) continue;
    const Speaker a{std::string(who[0]), 50}, b{std::string(who[1]), 50};
    Known k;
    CHECK(offered(s, b, k, w).empty());  // nothing learned yet, so nothing to ask
    // A teaches it: a line of A's whose words or links name it (else A is told it outright, as grantTopic does).
    Known all;
    for (const auto& x : s.all()) all.learn(x.id);
    bool taught = false;
    for (auto tid : offered(s, a, all, w)) {
      auto ans = answer(s, tid, a, all, w);
      if (!ans) continue;
      Known probe;
      probe.learn(tid, a.id);
      deliver(s, *ans, a, probe);
      if (probe.knows(t.id) && tid != t.id) {
        k = probe;
        taught = true;
        break;
      }
    }
    if (!taught) continue;
    tried = true;
    CHECK(k.heard_from(t.id, a.id) && !k.heard_from(t.id, b.id));
    auto list = offered(s, b, k, w);
    CHECK(std::find(list.begin(), list.end(), t.id) != list.end());
    auto ans = answer(s, t.id, b, k, w);
    CHECK(ans && ans->line->speaker == b.id);
    deliver(s, *ans, b, k);
    CHECK(k.heard_from(t.id, b.id));
    // topicHeardFrom reads the learned set through TalkFacts.
    TalkFacts tf(b, k, w);
    const std::vector<Arg> keys{t.id, a.id};
    CHECK(tf.truth(Term::topicHeardFrom, keys) == std::optional<bool>(true));
    break;
  }
  CHECK(tried);
}

void bands_pick_variants(const Store& s) {
  const Line* l = nullptr;
  for (const auto& x : s.lines())
    if (!x.low.empty() && !x.high.empty() && x.low != x.words && x.high != x.words) { l = &x; break; }
  CHECK(l != nullptr);
  if (!l) return;
  CHECK(words_at(*l, 0).text == l->low && words_at(*l, 29).text == l->low);
  CHECK(words_at(*l, 30).text == l->words && words_at(*l, 69).text == l->words);
  CHECK(words_at(*l, 70).text == l->high && words_at(*l, 100).text == l->high);
  CHECK(words_at(*l, 29).band == DispositionBand::low && words_at(*l, 70).band == DispositionBand::high);
}

void essential_at_zero(const Store& s) {
  // The mechanism: an essential topic whose lines read no disposition gives the same line at 0 as at 50, in its
  // low words, and is offered at 0.
  Topic t{"topic.e", "the essential", {}, true};
  Line staged{"l.staged", LineType::dialogue, "npc.a", "topic.e",
              *conditions::make("questStage", {std::string("q"), std::string("≥"), 10.0}), "mid", "cold", "warm", {}, {}};
  Line plain{"l.plain", LineType::dialogue, "npc.a", "topic.e", std::nullopt, "before", "", "", {}, {}};
  auto st = Store::build({t}, {staged, plain});
  CHECK(st && st->lint().empty());
  World w;
  w.stage = 10;
  Known k;
  k.learn("topic.e");
  auto at0 = answer(*st, "topic.e", Speaker{"npc.a", 0}, k, w), at50 = answer(*st, "topic.e", Speaker{"npc.a", 50}, k, w);
  CHECK(at0 && at50 && at0->line == at50->line && at0->text == "cold" && at50->text == "mid");
  CHECK(offered(*st, Speaker{"npc.a", 0}, k, w).size() == 1);

  // The walk over the real rows (0145 item 4): every essential topic each fixture speaker answers, at 0 and at 50,
  // across the quest's stages. A difference is a content finding for the writers, and lint must already name the
  // line that made it (so the L1 gate catches what the walk catches).
  std::set<std::string> linted;
  for (const auto& f : s.lint()) linted.insert(f.substr(0, f.find(':')));
  int asked = 0, differ = 0;
  for (double stage : {0.0, 10.0, 20.0, 30.0, 40.0, 90.0}) {
    w.stage = stage;
    for (const auto& topic : s.all()) {
      if (!topic.essential) continue;
      Known kk;
      kk.learn(topic.id);
      for (const auto& sp : fx::kSpeakers) {
        auto mid = answer(s, topic.id, Speaker{std::string(sp.id), 50}, kk, w);
        auto zero = answer(s, topic.id, Speaker{std::string(sp.id), 0}, kk, w);
        if (!mid && !zero) continue;
        ++asked;
        CHECK(zero && !zero->text.empty());  // never a dead end at the floor
        if (mid && zero && mid->line != zero->line) {
          ++differ;
          std::printf("walk: %s at stage %g gives %s at 50, %s at 0\n", topic.id.c_str(), stage,
                      mid->line->id.c_str(), zero->line->id.c_str());
          CHECK(linted.count(mid->line->id) || linted.count(zero->line->id));
        }
      }
    }
  }
  CHECK(asked > 0);
  std::printf("walk: %d essential asks, %d differ between 0 and 50\n", asked, differ);
}

void conditioned_before_plain(const Store& s) {
  // In every slot, no plain line precedes a conditioned one.
  for (const auto& sp : fx::kSpeakers)
    for (const auto& t : s.all()) {
      bool plain_seen = false;
      for (const Line* l : s.candidates(sp.id, t.id, LineType::dialogue)) {
        if (l->speaker.empty()) break;
        if (!l->available) plain_seen = true;
        else CHECK(!plain_seen);
      }
    }
  // And the plain fallback answers when no condition holds: a synthetic slot.
  Topic t{"topic.x", "x", {}, false};
  Line plain{"a.plain", LineType::dialogue, "npc.a", "topic.x", std::nullopt, "plain", "", "", {}, {}};
  Line late{"b.late", LineType::dialogue, "npc.a", "topic.x",
            *conditions::make("questStage", {std::string("q"), std::string("≥"), 40.0}), "late", "", "", {}, {}};
  auto st = Store::build({t}, {plain, late});
  CHECK(st.has_value());
  World w;
  Known k;
  k.learn("topic.x");
  w.stage = 50;
  CHECK(answer(*st, "topic.x", Speaker{"npc.a", 50}, k, w)->text == "late");
  w.stage = 10;
  CHECK(answer(*st, "topic.x", Speaker{"npc.a", 50}, k, w)->text == "plain");
  CHECK(!answer(*st, "topic.x", Speaker{"npc.b", 50}, k, w));  // another person has no line on it
}

void keyword_spans() {
  Topic t{"topic.cw", "Claywater Station", {"Claywater", "clay-bend"}, false}, u{"topic.well", "well", {}, false};
  auto s = Store::build({t, u}, {});
  CHECK(s.has_value());
  Known k;
  k.learn("topic.well");
  const std::string text = "At claywater station the well is dry; Claywater's wells, the clay-bend.";
  auto spans = s->keywords(text, k);
  CHECK(spans.size() == 4);
  if (spans.size() == 4) {
    CHECK(text.substr(spans[0].begin, spans[0].size) == "claywater station" && spans[0].topic == "topic.cw");
    CHECK(text.substr(spans[1].begin, spans[1].size) == "well" && spans[1].known);
    CHECK(text.substr(spans[2].begin, spans[2].size) == "Claywater" && !spans[2].known);  // the possessive links
    CHECK(text.substr(spans[3].begin, spans[3].size) == "clay-bend");
  }
  // "wells" is not "well": whole words only.
  CHECK(s->keywords("wells", k).empty());
}

void learned_set_round_trip() {
  Known k;
  k.learn("topic.a", "npc.x");
  k.learn("topic.a", "npc.y");
  k.learn("topic.b");
  auto b = encode(k);
  auto back = decode(b);
  CHECK(back && *back == k && back->heard_from("topic.a", "npc.y") && back->knows("topic.b"));
  b.pop_back();
  CHECK(!decode(b));
  CHECK(decode(encode(Known{})) == std::optional<Known>(Known{}));
}

void claywater_measured(const Store& s) {
  World w;
  w.stage = 30;
  Known all;
  for (const auto& t : s.all()) all.learn(t.id);
  const int reps = 200;
  std::size_t n = 0;
  auto t0 = std::chrono::steady_clock::now();
  for (int r = 0; r < reps; ++r)
    for (const auto& sp : fx::kSpeakers) n += offered(s, Speaker{std::string(sp.id), 50}, all, w).size();
  const double per = us_since(t0) / (reps * double(fx::kSpeakers.size()));
  std::printf("claywater: %zu lines, %zu topics; offered() %.1f us per speaker (%zu topics offered per pass), "
              "%d facts asked\n", s.lines().size(), s.all().size(), per, n / reps, w.asked / reps);
  auto t1 = std::chrono::steady_clock::now();
  for (int r = 0; r < 20; ++r) fixture_store();
  std::printf("claywater: Store::build from the fixture rows %.0f us\n", us_since(t1) / 20);
}

void synthetic_300() {
  const int topics_n = 300;
  std::vector<Topic> ts;
  std::vector<Line> ls;
  const std::string npc = "npc.synthetic", other = "npc.other";
  for (int i = 0; i < topics_n; ++i) {
    const std::string id = "topic.s" + std::to_string(i);
    ts.push_back({id, "subject " + std::to_string(i), {"form" + std::to_string(i)}, false});
    auto c = [&](std::string_view term, std::vector<Arg> a) { return *conditions::make(term, std::move(a)); };
    // Four lines per topic, the first three conditioned (stage, a flag and a teller, disposition), then a plain one.
    ls.push_back({id + ".stage", LineType::dialogue, npc, id,
                  conditions::all({c("questStage", {std::string("quest.s"), std::string("≥"), double(i % 5 * 10)}),
                                   c("flag", {"flag.s" + std::to_string(i % 7), 1.0})}), "stage", "", "", {}, {}});
    ls.push_back({id + ".told", LineType::dialogue, npc, id, c("topicHeardFrom", {id, other}), "told", "", "", {}, {}});
    ls.push_back({id + ".warm", LineType::dialogue, npc, id, c("speakerDispositionAtLeast", {70.0}), "warm", "", "", {}, {}});
    ls.push_back({id + ".plain", LineType::dialogue, npc, id, std::nullopt, "plain words about form" +
                  std::to_string((i + 1) % topics_n), "low", "high", {}, {}});
  }
  auto s = Store::build(std::move(ts), std::move(ls));
  CHECK(s.has_value());
  if (!s) return;
  World w;
  w.stage = 20;
  w.truths["flag(flag.s3)"] = true;
  Known k;
  for (int i = 0; i < topics_n; ++i) k.learn("topic.s" + std::to_string(i), i % 2 ? other : "");
  const Speaker sp{npc, 50};
  CHECK(offered(*s, sp, k, w).size() == std::size_t(topics_n));
  // First match by the rule: stage and flag, else told by the other, else plain (disposition 50 is not warm).
  for (int i = 0; i < topics_n; ++i) {
    auto a = answer(*s, "topic.s" + std::to_string(i), sp, k, w);
    const char* want = (i % 5 * 10 <= 20 && i % 7 == 3) ? "stage" : (i % 2 ? "told" : "plain");
    CHECK(a && a->line->words.rfind(want, 0) == 0);
  }
  CHECK(answer(*s, "topic.s0", Speaker{npc, 80}, k, w)->text == "warm");
  CHECK(answer(*s, "topic.s0", Speaker{npc, 10}, k, w)->text == "low");
  const int reps = 200;
  auto t0 = std::chrono::steady_clock::now();
  std::size_t n = 0;
  for (int r = 0; r < reps; ++r) n += offered(*s, sp, k, w).size();
  const double offer_us = us_since(t0) / reps;
  auto t1 = std::chrono::steady_clock::now();
  for (int r = 0; r < reps; ++r) n += answer(*s, "topic.s" + std::to_string(r % topics_n), sp, k, w).has_value();
  const double answer_us = us_since(t1) / reps;
  std::string text;
  for (int i = 0; i < 60; ++i) text += "the subject " + std::to_string(i * 5) + " and form" + std::to_string(i) + ", ";
  auto t2 = std::chrono::steady_clock::now();
  for (int r = 0; r < reps; ++r) n += s->keywords(text, k).size();
  const double kw_us = us_since(t2) / reps;
  CHECK(n > 0);
  std::printf("synthetic: 300 topics x 4 lines; offered() %.1f us, answer() %.2f us, keywords() over %zu chars "
              "%.1f us\n", offer_us, answer_us, text.size(), kw_us);
}

}  // namespace

int main() {
  const Store s = fixture_store();
  builds_from_rows(s);
  refusals();
  learned_from_a_asked_of_b(s);
  bands_pick_variants(s);
  essential_at_zero(s);
  conditioned_before_plain(s);
  keyword_spans();
  learned_set_round_trip();
  claywater_measured(s);
  synthetic_300();
  return TEST_MAIN_RESULT("core.topics");
}
