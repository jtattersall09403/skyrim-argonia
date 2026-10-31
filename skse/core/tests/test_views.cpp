// L2: the web-view host (1.2 §0): a push before the page loads waits for DOM ready; a modal push opens it and closes
// the other modal; close unfocuses and hides; the HUD never closes. The journal key latch; the chart's remembered
// view round-trips and falls back; the journal pages and filters; the 300-topic probe fits the schema.
#include "check.h"
#include "argonia/core/seam.h"
#include "argonia/core/views.h"

#include <set>

using namespace argonia::core;
using namespace argonia::core::views;

namespace {

bool has(const std::vector<Op>& ops, OpKind k, std::string_view v) {
  for (const auto& o : ops)
    if (o.kind == k && o.view == v) return true;
  return false;
}

void close_press_is_consumed() {
  ClosePressGuard g;
  CHECK(!g.swallow(275, true, false, true));    // B goes down in the journal
  CHECK(g.swallow(275, false, false, true));    // its repeat
  CHECK(g.swallow(275, false, true, false));    // released after the view closed: hidden from TK Dodge
  CHECK(!g.swallow(275, false, true, false));   // once only
  CHECK(!g.swallow(275, true, false, false));   // a press with no view open is the game's
  CHECK(!g.swallow(275, false, true, false));
  CHECK(!g.swallow(1, true, false, true) && !g.swallow(2, false, true, false));  // another button's release passes
}

void close_controls() {
  const CloseControl esc{false, false, true, false}, tab{false, true, false, false}, b{true, false, false, false},
      m{false, false, false, true}, none{};
  CHECK(close_intent("dialogue", esc, true) == R"({"type":"dialogue.goodbye","v":1,"body":{}})");
  CHECK(close_intent("dialogue", tab, true) && close_intent("dialogue", b, true));
  CHECK(close_intent("dialogue", esc, false) == R"({"type":"view.close","v":1,"body":{"view":"dialogue"}})");
  CHECK(!close_intent("dialogue", m, true) && !close_intent("dialogue", none, true));
  CHECK(close_intent("journal", esc, false) == R"({"type":"view.close","v":1,"body":{"view":"journal"}})");
  CHECK(!close_intent("journal", m, false) && close_intent("chart", m, false));
  CHECK(!close_intent("sitting", esc, false) && !close_intent("hud", esc, false));
}

void the_table() {
  std::set<std::string_view> ids;
  for (const auto& s : kViews) {
    ids.insert(s.id);
    CHECK(s.page == "argonia/" + std::string(s.id) + "/index.html");
  }
  CHECK(ids.size() == kViews.size());
  CHECK(spec("hud") && !spec("hud")->modal);
  CHECK(spec("dialogue") && spec("dialogue")->modal);
  CHECK(!spec("inventory"));
}

void push_waits_for_ready() {
  Host h;
  auto ops = h.push("dialogue", "A");
  CHECK(h.is_open("dialogue") && !has(ops, OpKind::push, "dialogue") && !has(ops, OpKind::show, "dialogue"));
  ops = h.ready("dialogue");
  CHECK(ops.size() == 3 && ops[0] == (Op{OpKind::push, "dialogue", "A"}));
  CHECK(has(ops, OpKind::show, "dialogue") && has(ops, OpKind::focus, "dialogue"));
  ops = h.push("dialogue", "B");  // already open: only the push
  CHECK(ops.size() == 1 && ops[0] == (Op{OpKind::push, "dialogue", "B"}));
  // a page that loads closed is hidden
  ops = h.ready("journal");
  CHECK(ops.size() == 1 && ops[0].kind == OpKind::hide);
}

void one_modal() {
  Host h;
  h.ready("dialogue");
  h.ready("chart");
  h.push("dialogue", "A");
  auto ops = h.push("chart", "C");
  CHECK(has(ops, OpKind::unfocus, "dialogue") && has(ops, OpKind::hide, "dialogue"));
  CHECK(has(ops, OpKind::show, "chart") && has(ops, OpKind::focus, "chart") && has(ops, OpKind::push, "chart"));
  CHECK(h.modal() == "chart" && !h.is_open("dialogue") && !h.last("dialogue"));
  ops = h.close("chart");
  CHECK(ops.size() == 2 && has(ops, OpKind::unfocus, "chart") && has(ops, OpKind::hide, "chart"));
  CHECK(!h.modal() && h.close("chart").empty());
}

void hud_always_open() {
  Host h;
  auto ops = h.ready("hud");
  CHECK(ops.size() == 1 && ops[0].kind == OpKind::show);
  ops = h.push("hud", "H");
  CHECK(ops.size() == 1 && ops[0].kind == OpKind::push);
  CHECK(h.close("hud").empty() && h.is_open("hud"));
  h.ready("sitting");
  h.push("sitting", "S");
  ops = h.close_all();
  CHECK(has(ops, OpKind::hide, "sitting") && !has(ops, OpKind::hide, "hud") && h.last("hud"));
  CHECK(h.push("nonesuch", "x").empty());
}

void latch() {
  KeyLatch k;
  CHECK(!k.take(10));
  k.press(10);
  CHECK(k.take(10.5));
  CHECK(!k.take(10.6));  // once per press
  k.press(10);
  CHECK(!k.take(12));  // stale: Escape's Journal Menu passes
}

void chart_layout() {
  const msg::ChartView v{-56.85, 11.7, 4};
  CHECK(remembered_chart(chart_layout_text(v)) == v);
  const msg::ChartView whole{1, 1, 1};
  CHECK(remembered_chart(std::nullopt) == whole);
  CHECK(remembered_chart("not json") == whole);
  CHECK(remembered_chart(R"({"type":"chart.pan","v":1,"body":{"view":{"centreX":0,"centreY":0,"zoom":900}}})") == whole);
  CHECK(remembered_chart(R"({"type":"view.close","v":1,"body":{"view":"chart"}})") == whole);
}

// The chart's state carries the CHRT family's cells, x then y, and the remembered view; it fits the schema.
void chart_reveal() {
  chart::Discovered d;
  chart::reveal(d, {-56, 12});
  chart::reveal(d, {-57, 11});
  chart::reveal(d, {-56, 11});
  const msg::ChartView v{-56.85, 11.7, 4};
  const auto s = chart_state(d, v);
  CHECK((s.revealed == std::vector<msg::CellKey>{{-57, 11}, {-56, 11}, {-56, 12}}));
  CHECK(s.view == v && s.sketch == "chart.sketch" && s.worldspace == "argonia");
  auto j = msg::encode(s);
  CHECK(j && j->find(R"("revealed":[{"x":-57,"y":11})") != std::string::npos);
  CHECK(chart_state({}, v).revealed.empty());
}

void the_journal() {
  journal::Log log;
  for (int i = 0; i < 8; ++i) journal::append(log, i < 7 ? 1u : 2u, std::uint32_t(10 * (i + 1)), {201, 8, 16 + i, 9.0});
  auto name = [](journal::QuestId q) { return QuestNames{"quest." + std::to_string(q), "Quest " + std::to_string(q)}; };
  auto text = [](journal::QuestId, journal::EntryId e) { return "entry " + std::to_string(e); };
  const Directions none;
  auto s = journal_state(log, name, text, none, {msg::JournalTab::entries, 0, std::nullopt}, 6);
  CHECK(s.page_count == 2 && s.entries.size() == 6 && s.entries[0].runs[0].text == "entry 10");
  CHECK(s.entries[0].date.text == "16th of the Eighth Month, 201" && s.quests.size() == 2);
  s = journal_state(log, name, text, none, {msg::JournalTab::entries, 9, std::nullopt}, 6);  // clamped to the last page
  CHECK(s.page == 1 && s.entries.size() == 2);
  s = journal_state(log, name, text, none, {msg::JournalTab::entries, 0, std::string("quest.2")}, 6);
  CHECK(s.page_count == 1 && s.entries.size() == 1 && s.entries[0].quest == "quest.2");
  CHECK(msg::encode(s).has_value());
  CHECK(date({201, 1, 1, 0}).text == "1st of the First Month, 201" && date({201, 3, 22, 0}).text.starts_with("22nd"));
  CHECK(date({201, 3, 13, 0}).text.starts_with("13th") && date({201, 3, 23, 0}).text.starts_with("23rd"));
  const journal::Log empty;
  s = journal_state(empty, name, text, none, {msg::JournalTab::quests, 0, std::nullopt});
  CHECK(s.page_count == 1 && s.entries.empty() && msg::encode(s).has_value());
}

// LF83's words from the generated table (quest rows -> journal_text.h): an entry's text, the active quest's
// directions from its latest stage, none once it has ended.
void the_journal_text() {
  const auto lf83 = seam::key("quest.local.lf83");
  const auto* t10 = journal::stage_text(lf83, 10);
  CHECK(t10 && t10->quest_id == "quest.local.lf83" && t10->log.starts_with("I came to Claywater Station"));
  CHECK(t10 && t10->directions.starts_with("From the Blackwood Road"));
  CHECK(t10 && journal::objectives(*t10).size() == 2 && journal::objectives(*t10)[0].index == 10 &&
        journal::objectives(*t10)[0].text == "Hear Livia Varinius's side at the well.");
  CHECK(!journal::stage_text(lf83, 11) && !journal::stage_text(lf83 + 1, 10) && entry_text(lf83, 11).empty());
  CHECK(!entry_directions(lf83, 40));  // an ending gives no directions
  for (std::size_t i = 1; i < gen::kJournalStages.size(); ++i) {  // sorted, so the lookup's binary search holds
    const auto &a = gen::kJournalStages[i - 1], &b = gen::kJournalStages[i];
    CHECK((std::pair{a.quest, a.stage} < std::pair{b.quest, b.stage}));
  }
  for (const auto& r : gen::kJournalStages) {
    CHECK(seam::key(r.quest_id) == r.quest);  // the generator's FNV-1a is quest_state::key
    CHECK(!r.log.empty() && !r.log.starts_with("[not yet written"));
  }

  journal::Log log;
  journal::append(log, lf83, 10, {201, 8, 16, 9.0});
  journal::append(log, lf83, 20, {201, 8, 17, 9.0});
  auto name = [](journal::QuestId) { return QuestNames{"quest.local.lf83", "Two Charges at Claywater"}; };
  auto s = journal_state(log, name, entry_text, entry_directions, {msg::JournalTab::entries, 0, std::nullopt});
  CHECK(s.entries.size() == 2 && s.entries[1].runs[0].text.starts_with("At Claywater Station, Livia Varinius told me"));
  CHECK(s.quests.size() == 1 && s.quests[0].directions && s.quests[0].directions->starts_with("The clay cut is below"));
  CHECK(msg::encode(s).has_value());
  journal::append(log, lf83, 40, {201, 8, 20, 9.0}, journal::Kind::complete);
  s = journal_state(log, name, entry_text, entry_directions, {msg::JournalTab::quests, 0, std::nullopt});
  CHECK(s.quests[0].status == msg::QuestStatus::complete && !s.quests[0].directions);
}

void the_probe() {
  const auto s = probe_dialogue("npc.imperial-fringe.claywater-station.well-keeper", "Livia", 300);
  CHECK(s.topics.size() == 300 && s.topics[299].label == "Topic 300");
  std::set<std::string> ids;
  for (const auto& t : s.topics) ids.insert(t.id);
  CHECK(ids.size() == 300);
  auto j = msg::encode(s);
  CHECK(j.has_value());
  if (j) CHECK(msg::decode_push(*j).has_value());
}

}  // namespace

int main() {
  close_press_is_consumed();
  close_controls();
  the_table();
  push_waits_for_ready();
  one_modal();
  hud_always_open();
  latch();
  chart_layout();
  chart_reveal();
  the_journal();
  the_journal_text();
  the_probe();
  return TEST_MAIN_RESULT("views");
}
