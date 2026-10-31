// L2: the dialogue intercept's conversation over the in-game store (the fixture's written lines): Livia greets, lists
// her topics, answers one, the answer's links are learned from her, an intent decoded by the schema twin drives the
// same path, an off-schema intent is refused, Goodbye closes, and every window encodes as a schema-valid
// dialogue.state. A person with no lines is not an Argonia speaker and is refused (the vanilla path is not taken).
#include "check.h"
#include "argonia/core/fixture_topics.h"
#include "argonia/core/quests.h"
#include "argonia/core/talk.h"

#include <algorithm>
#include <string>

using namespace argonia::core;

namespace {

const std::string kKeeper = "npc.imperial-fringe.claywater-station.well-keeper";

struct Engine : seam::Engine, seam::EngineWrites {
  std::optional<int> item_count(std::string_view) const override { return 0; }
  std::optional<bool> alive(std::string_view) const override { return true; }
  std::optional<int> gold() const override { return 50; }
  std::optional<seam::QuestView> quest(std::string_view) const override { return seam::QuestView{0, {}}; }  // not started
  std::optional<seam::Date> date() const override { return seam::Date{201, 0, 10, 12}; }
  bool give_item(std::string_view, int) override { return true; }
  bool take_item(std::string_view, int) override { return true; }
  bool give_gold(int) override { return true; }
  bool take_gold(int) override { return true; }
  std::vector<std::string> barters;
  bool open_barter(std::string_view n) override { barters.emplace_back(n); return true; }
};

void the_store_holds_written_lines_only() {
  auto store = talk::fixture_store();
  CHECK(store.has_value());
  if (!store) return;
  for (const auto& sp : gen::fixture::kSpeakers) {
    const auto ls = store->lines();
    const bool any = std::any_of(ls.begin(), ls.end(), [&](const topics::Line& l) { return l.speaker == sp.id; });
    CHECK(any == (sp.status == "written"));
  }
}

void runs_split_at_keywords() {
  auto store = talk::fixture_store();
  if (!store) return;
  topics::Known k;
  auto r = talk::runs(*store, "Ask about the clay bend, citizen.", k);
  CHECK(r.size() == 3 && r[1].text == "the clay bend" && r[1].topic == std::optional<std::string>("topic.lf83-clay-bend"));
  CHECK(r[0].text == "Ask about " && !r[0].topic && r[2].text == ", citizen.");
  auto plain = talk::runs(*store, "", k);
  CHECK(plain.size() == 1 && plain[0].text.empty());
}

void livia_talks() {
  auto store = talk::fixture_store();
  if (!store) return;
  seam::State st;
  Engine e;
  const auto graphs = gen::quest_graphs();
  seam::Session ses(st, e, e, graphs);
  auto refused = talk::Conversation::open(*store, ses, "npc.nobody", "Nobody");
  CHECK(!refused && refused.error().find("not an Argonia speaker") != std::string::npos);

  auto c = talk::Conversation::open(*store, ses, kKeeper, "Livia Varinius");
  CHECK(c.has_value());
  if (!c) return;
  auto v = c->view(ses);
  CHECK(v.speaker.id == kKeeper && v.speaker.name == "Livia Varinius" && v.can_leave && !v.persuasion.available);
  CHECK(v.entries.size() == 1 && v.entries[0].kind == msg::DialogueEntryKind::greeting);
  CHECK(msg::encode(v).has_value());
  // The greeting's keywords are learned from her, so her topic list is not empty.
  CHECK(!v.topics.empty() && st.known.size() > 0);
  // and open() hands those notes on for the SKSE log, not into a dropped reply.
  CHECK(!c->greeting_notes().empty() && c->greeting_notes()[0].find("learned ") == 0);
  CHECK(talk::speaks(*store, kKeeper) && !talk::speaks(*store, "npc.nobody"));
  const std::string t = v.topics.front().id;
  auto r = c->ask(t, ses);
  CHECK(r.state && r.state->entries.size() == 2 && r.state->entries[1].kind == msg::DialogueEntryKind::answer);
  CHECK(r.state && r.state->entries[1].heading == std::optional<std::string>(v.topics.front().label));
  CHECK(st.known.heard_from(t, kKeeper));
  CHECK(r.state && msg::encode(*r.state).has_value());
  // The same through the schema: a topic intent as the view sends it.
  auto json = msg::encode(msg::DialogueTopic{t});
  CHECK(json.has_value());
  auto r2 = c->on_intent_text(*json, ses);
  CHECK(r2.state && r2.state->entries.size() == 3);
  // Off-schema and pushed-state intents are refused, and the window stays as it was.
  auto bad = c->on_intent_text(R"({"type":"dialogue.topic","v":1,"body":{"topic":"x","extra":1}})", ses);
  CHECK(bad.state && bad.state->entries.size() == 3 && !bad.notes.empty());
  auto pushed = c->on_intent_text(*msg::encode(*r2.state), ses);
  CHECK(pushed.state && pushed.notes.size() == 1 && pushed.notes[0].find("intents only") != std::string::npos);
  auto none = c->ask("topic.none", ses);
  CHECK(none.state && none.notes.size() == 1);
  // Disposition moves the band the window shows.
  st.disp[seam::key(kKeeper)] = 80;
  CHECK(c->view(ses).disposition.band == msg::DispositionBand::high);
  auto bye = c->on_intent(msg::DialogueGoodbye{}, ses);
  CHECK(bye.closed && !bye.state);
  auto esc = c->on_intent(msg::ViewClose{msg::ViewId::dialogue}, ses);
  CHECK(esc.closed);
}

// Lane trader: her service topic is offered before it is learned, and answering it opens her BarterMenu.
void livia_trades() {
  auto store = talk::fixture_store();
  if (!store) return;
  seam::State st;
  Engine e;
  const auto graphs = gen::quest_graphs();
  seam::Session ses(st, e, e, graphs);
  auto c = talk::Conversation::open(*store, ses, kKeeper, "Livia Varinius");
  CHECK(c.has_value());
  if (!c) return;
  const std::string barter = "topic.service-barter";
  CHECK(!st.known.knows(barter));
  const auto v = c->view(ses);
  CHECK(std::any_of(v.topics.begin(), v.topics.end(), [&](const auto& t) { return t.id == barter; }));
  auto r = c->ask(barter, ses);
  CHECK(r.state && r.state->entries.size() == 2 && !r.closed);
  CHECK(e.barters.size() == 1 && e.barters[0] == kKeeper);
  // Another speaker without a line for it does not offer it.
  auto p = talk::Conversation::open(*store, ses, "npc.imperial-fringe.claywater-station.landing-s-poler", "Poler");
  if (p) {
    const auto pv = p->view(ses);
    CHECK(std::none_of(pv.topics.begin(), pv.topics.end(), [&](const auto& t) { return t.id == barter; }));
  }
}

}  // namespace

int main() {
  the_store_holds_written_lines_only();
  runs_split_at_keywords();
  livia_talks();
  livia_trades();
  return TEST_MAIN_RESULT("core.talk");
}
