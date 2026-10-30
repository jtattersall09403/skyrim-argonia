// L2: the seam ArgoniaCore's adapters stand on: the forms table, the QWCH family, every family bound and round-
// tripped through one registry, the world facts over the state and a fake engine, the action natives, LF83 stepped
// from its start to an ending as the quest adapter does, the router's hooks installed once, the attribute mirrors.
#include "check.h"
#include "argonia/core/quests.h"
#include "argonia/core/seam.h"

#include <algorithm>
#include <map>
#include <set>
#include <string>

using namespace argonia::core;
using conditions::Arg;
using conditions::Term;

namespace {

const std::string kLf83 = "quest.local.lf83";
const std::string kKeeper = "npc.imperial-fringe.claywater-station.well-keeper";
const std::string kPoler = "npc.imperial-fringe.claywater-station.landing-s-poler";

struct FakeEngine : seam::Engine, seam::EngineWrites {
  std::map<std::string, int> items;
  std::map<std::string, bool> living;
  std::optional<int> purse = 100;
  std::map<std::string, seam::QuestView> quests;
  std::optional<seam::Date> today = seam::Date{201, 0, 10, 12};  // GameMonth 0: the dry season
  std::vector<std::string> writes;

  std::optional<int> item_count(std::string_view i) const override {
    auto it = items.find(std::string(i));
    return it == items.end() ? std::optional<int>(0) : it->second;
  }
  std::optional<bool> alive(std::string_view n) const override {
    auto it = living.find(std::string(n));
    return it == living.end() ? std::nullopt : std::optional<bool>(it->second);
  }
  std::optional<int> gold() const override { return purse; }
  std::optional<seam::QuestView> quest(std::string_view q) const override {
    auto it = quests.find(std::string(q));
    return it == quests.end() ? std::nullopt : std::optional<seam::QuestView>(it->second);
  }
  std::optional<seam::Date> date() const override { return today; }
  bool give_item(std::string_view i, int n) override { items[std::string(i)] += n; writes.push_back("give " + std::string(i)); return true; }
  bool take_item(std::string_view i, int n) override { items[std::string(i)] -= n; return true; }
  bool give_gold(int n) override { *purse += n; return true; }
  bool take_gold(int n) override { *purse -= n; return true; }
};

void forms_both_ways() {
  const auto* q = seam::form(kLf83);
  CHECK(q && q->type == "QUST" && q->plugin == "Argonia.esm" && q->local == 0x852);
  const auto* back = seam::form_at("ARGONIA.ESM", 0x852);  // file names compare without case
  CHECK(back && back->id == kLf83);
  CHECK(!seam::form("quest.none") && !seam::form_at("Argonia.esm", 0xFFFFFF));
  CHECK(!seam::form_at("Argonia\x0Esm", 0x852));  // only letters fold: '.' (0x2E) is not 0x0E
  for (std::size_t i = 1; i < gen::kForms.size(); ++i) CHECK(gen::kForms[i - 1].id < gen::kForms[i].id);  // sorted
}

void watch_family() {
  seam::Watch w;
  w.quests = {seam::key(kLf83), 7, 3};
  CHECK(seam::decode(seam::encode(w)) == w);
  cosave::Writer bad;
  bad.u32(2); bad.u32(5); bad.u32(5);  // a repeat
  CHECK(!seam::decode(bad.take()));
  cosave::Writer pad;
  pad.u32(0); pad.u8(1);
  CHECK(!seam::decode(pad.take()));
}

void every_family_through_one_registry() {
  seam::State a, b;
  families::Registry ra, rb;
  CHECK(seam::bind(ra, a).empty());
  CHECK(seam::bind(rb, b).empty());
  CHECK(ra.ids().size() == 10);
  CHECK(seam::bind(ra, a).size() == 10);  // a second bind is refused family by family
  // A marker in every family.
  seam::on_save(a);
  a.sheet.a[AttrId::strength] = 61;
  a.disp[seam::key(kKeeper)] = 42;
  journal::append(a.log, seam::key(kLf83), 10, {201, 1, 10, 12});
  a.items[9] = items::ItemState{20, 100, std::nullopt};
  a.death.pile = death::Pile{{1, 2, 3, 4}, 120};
  quest_state::set_flag(a.quests, "flag.lf83.ford-tasted", true);
  a.known.learn("topic.claywater-two-charges", kKeeper);
  a.watch.quests.insert(seam::key(kLf83));
  chart::reveal(a.chart, {-56, 11});
  std::map<std::uint32_t, std::string> before;
  for (auto id : ra.ids()) before[id] = seam::digest(ra, id);
  for (auto& rec : ra.save_all()) CHECK(rb.load(rec.id, rec.version, rec.payload).ok());
  for (auto id : rb.ids()) CHECK(seam::digest(rb, id) == before[id]);
  CHECK(b.meta.save_count == 1 && b.sheet.a[AttrId::strength] == 61 && b.watch == a.watch && b.known == a.known &&
        b.chart == a.chart);
  // The scene reset leaves nothing behind: every family reads as a fresh state's.
  seam::State fresh;
  families::Registry rf;
  seam::bind(rf, fresh);
  rb.reset_all();
  for (auto id : rb.ids()) CHECK(seam::digest(rb, id) == seam::digest(rf, id));
  CHECK(seam::digest(rb, cosave::fourcc("NONE")).empty());
  // A newer save is refused and the family reset, never half-loaded.
  auto r = rb.load(seam::kWatchType, 2, seam::encode(a.watch));
  CHECK(r.status == families::Status::refused_newer && b.watch.quests.empty());
}

void world_facts() {
  seam::State s;
  FakeEngine e;
  const auto graphs = gen::quest_graphs();
  const seam::WorldFacts f(s, e, graphs);
  const std::vector<Arg> flag{std::string("flag.x")}, topic{std::string("topic.t")},
      heard{std::string("topic.t"), std::string(kKeeper)}, item{std::string("item.lf83.clay-basket")},
      keeper{std::string(kKeeper)}, lf83{std::string(kLf83)},
      obj{std::string(kLf83), std::string("hear-station")};
  CHECK(f.truth(Term::flag, flag) == false);
  quest_state::set_flag(s.quests, "flag.x", true);
  CHECK(f.truth(Term::flag, flag) == true);
  CHECK(f.truth(Term::knowsTopic, topic) == false);
  s.known.learn("topic.t", kKeeper);
  CHECK(f.truth(Term::knowsTopic, topic) == true && f.truth(Term::topicHeardFrom, heard) == true);
  CHECK(f.number(Term::hasItem, item) == 0.0);
  e.items["item.lf83.clay-basket"] = 1;
  CHECK(f.number(Term::hasItem, item) == 1.0);
  CHECK(f.number(Term::goldAtLeast, {}) == 100.0);
  CHECK(!f.truth(Term::npcAlive, keeper));  // not loaded: unknown, never false
  e.living[kKeeper] = true;
  CHECK(f.truth(Term::npcAlive, keeper) == true);
  CHECK(f.state(Term::seasonIs, {}) == std::optional<std::string>("dry"));
  e.today->month = 8;  // GameMonth 8: day 243, the wet season
  CHECK(f.state(Term::seasonIs, {}) == std::optional<std::string>("wet"));
  e.today->month = 12;  // no such month: unknown
  CHECK(!f.state(Term::seasonIs, {}));
  CHECK(!f.number(Term::questStage, lf83));
  e.quests[kLf83] = {10, {10}};
  CHECK(f.number(Term::questStage, lf83) == 10.0 && f.truth(Term::objectiveComplete, obj) == true);
  CHECK(f.number(Term::levelAtLeast, {}) == 1.0);
  s.sheet.a[AttrId::willpower] = 33;
  CHECK(f.number(Term::attributeAtLeast, std::vector<Arg>{std::string("willpower")}) == 33.0);
  CHECK(!f.truth(Term::detectedBy, keeper));  // a term the seam does not answer yet
}

void the_action_natives() {
  seam::State s;
  FakeEngine e;
  const auto graphs = gen::quest_graphs();
  seam::Session ses(s, e, e, graphs);
  CHECK(ses.act("setFlag", {std::string("flag.lf83.terms-settled"), true}).done);
  CHECK(quest_state::flag(s.quests, "flag.lf83.terms-settled"));
  CHECK(ses.act("grantTopic", {std::string("topic.lf83-one-charge")}).done && s.known.knows("topic.lf83-one-charge"));
  CHECK(ses.act("giveItem", {std::string("item.potion-of-regeneration"), 1.0}).done && e.writes.size() == 1);
  s.disp[seam::key(kKeeper)] = 95;
  CHECK(ses.act("changeDisposition", {std::string(kKeeper), 15.0}).done && s.disp[seam::key(kKeeper)] == 100);
  CHECK(ses.act("changeDisposition", {std::string(kPoler), -15.0}).done && s.disp[seam::key(kPoler)] == 0);
  CHECK(ses.act("applyLocalVariant", {std::string("place.p"), std::string("v")}).done);
  CHECK(ses.facts().truth(Term::localVariantActive, std::vector<Arg>{std::string("place.p"), std::string("v")}) == true);
  CHECK(ses.act("setPrice", {std::string("ferry.f"), 7.0}).done && ses.act("setPrice", {std::string("ferry.f"), 0.0}).done);
  CHECK(quest_state::counter(s.quests, seam::price_counter("ferry.f")) == 0);
  CHECK(ses.act("changeSettlementStanding", {std::string("place.p"), 10.0}).done &&
        ses.facts().number(Term::settlementStandingAtLeast, std::vector<Arg>{std::string("place.p")}) == 10.0);
  // Refusals: an unknown verb, a wrong argument kind, a need the player cannot meet.
  CHECK(!ses.act("flyAway", {}).done);
  CHECK(!ses.act("setFlag", {1.0, true}).done);
  CHECK(!ses.act("takeGold", {500.0}).done && *e.purse == 100);
  // The journal: dated, once per stage, nothing after the ending.
  std::string why;
  CHECK(ses.add_journal_entry(kLf83, 10, 0, {201, 0, 10, 12}));
  CHECK(s.log.entries.size() == 1 && s.log.entries[0].date.month == 1 && s.log.entries[0].quest == seam::key(kLf83));
  CHECK(!ses.add_journal_entry(kLf83, 10, 0, {201, 0, 10, 12}, &why) && !why.empty());
  CHECK(!ses.add_journal_entry(kLf83, 20, 3, {201, 0, 10, 12}));
  CHECK(ses.add_journal_entry(kLf83, 41, 1, {201, 0, 11, 9}));
  CHECK(!ses.add_journal_entry(kLf83, 42, 1, {201, 0, 11, 9}));
  CHECK(!ses.watch("quest.none", &why) && why.find("no stage graph") != std::string::npos);
}

// The quest adapter's loop with the engine faked: each order is applied as SetObjectiveCompleted and SetStage would.
void lf83_start_to_end() {
  seam::State s;
  FakeEngine e;
  const auto graphs = gen::quest_graphs();
  seam::Session ses(s, e, e, graphs);
  e.quests[kLf83] = {0, {}};
  auto apply = [&] {
    auto orders = ses.step();
    for (const auto& o : orders) {
      auto& v = e.quests[o.quest];
      for (auto i : o.completed) v.done.push_back(i);
      if (o.set_stage) v.stage = *o.set_stage;
    }
    return orders;
  };
  CHECK(apply().empty());  // not watched yet: stage 0's fragment calls WatchQuest
  CHECK(ses.watch(kLf83));
  CHECK(apply().empty());  // started by hearing of the two charges in the dry season
  s.known.learn("topic.claywater-two-charges", kKeeper);
  auto o = apply();
  CHECK(o.size() == 1 && o[0].set_stage == 10);
  e.living[kKeeper] = e.living[kPoler] = true;
  o = apply();
  CHECK(o.size() == 1 && o[0].completed == std::vector<std::uint16_t>{10} && !o[0].set_stage);
  s.known.learn("topic.claywater-two-charges", kPoler);
  s.known.learn("topic.lf83-clay-bend", kPoler);
  o = apply();
  CHECK(o.size() == 1 && o[0].completed == std::vector<std::uint16_t>{11} && o[0].set_stage == 20);
  CHECK(ses.act("setFlag", {std::string("flag.lf83.ford-charge-bought"), true}).done);
  o = apply();
  CHECK(o.size() == 1 && o[0].set_stage == 41 && e.quests[kLf83].stage == 41);
  CHECK(apply().empty());  // an ending rests
  // A death overrides progress: the keeper dies at stage 20.
  e.quests[kLf83] = {20, {}};
  e.living[kKeeper] = false;
  o = apply();
  CHECK(o.size() == 1 && o[0].set_stage == 92);
  CHECK(ses.unwatch(kLf83) && apply().empty() && !ses.unwatch(kLf83));
}

void hooks_once() {
  router::Router r;
  int opened = 0;
  auto log = seam::install(r, [&](router::SurfaceId) { ++opened; });
  CHECK(r.installed(router::HookId::menuOpenClose) && r.installed(router::HookId::dialogueIntercept));
  CHECK(r.has_handler(router::SurfaceId::dialogueMenu));
  CHECK(!log.empty() && log.back().rfind("second registration refused: hook dialogueIntercept: already installed", 0) == 0);
  auto v = r.on_menu("Dialogue Menu");
  CHECK(v.action == router::Action::block && v.handled && opened == 1);
  // A second install of the whole set is refused hook by hook.
  auto again = seam::install(r, [](router::SurfaceId) {});
  CHECK(std::count_if(again.begin(), again.end(), [](const std::string& l) { return l.rfind("refused: ", 0) == 0; }) == 3);
}

void attributes() {
  std::set<AttrId> covered;
  std::set<std::string_view> avs;
  for (const auto& m : seam::attribute_mirrors()) { covered.insert(m.attribute); avs.insert(m.actor_value); }
  CHECK(covered.size() == gen::kAttrIdCount && avs.size() == gen::kAttrIdCount);
  CHECK(seam::attribute_named("strength") == AttrId::strength && !seam::attribute_named("luck"));
  seam::State s;
  CHECK(seam::set_attribute(s, AttrId::endurance, 70) == 70 && seam::attribute(s, AttrId::endurance) == 70);
  CHECK(seam::set_attribute(s, AttrId::endurance, 900) == 255 && seam::set_attribute(s, AttrId::endurance, -1) == 0);
  CHECK(seam::disposition_of(s, kKeeper) == 0);  // unmet, authored base 0, Personality 0
}

}  // namespace

// Orders the engine has not run yet are not given twice; a refused dispatch, a load or a revert lets them again.
void in_flight_once() {
  seam::InFlight f;
  const seam::Order o{kLf83, {10, 11}, 20};
  CHECK(f.filter({o}) == std::vector<seam::Order>{o});
  CHECK(f.filter({o}).empty());                                    // the VM has not run the first yet
  CHECK((f.filter({{kLf83, {10, 12}, 20}}) == std::vector<seam::Order>{{kLf83, {12}, std::nullopt}}));
  CHECK((f.filter({{kLf83, {}, 30}}) == std::vector<seam::Order>{{kLf83, {}, 30}}));  // the next stage passes
  f.forget(kLf83);
  CHECK(f.filter({o}) == std::vector<seam::Order>{o});
  f.clear();
  CHECK(f.filter({o}) == std::vector<seam::Order>{o});
}

int main() {
  forms_both_ways();
  watch_family();
  every_family_through_one_registry();
  world_facts();
  the_action_natives();
  lf83_start_to_end();
  hooks_once();
  attributes();
  in_flight_once();
  return TEST_MAIN_RESULT("core.seam");
}
