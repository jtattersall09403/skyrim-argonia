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

void prompt_text() {
  CHECK((prompt_from_activate_text("Talk", "Takes-the-Ledger") == PromptText{"Talk", "Takes-the-Ledger"}));
  CHECK((prompt_from_activate_text("Take\nLedger", "x") == PromptText{"Take", "Ledger"}));
  CHECK((prompt_from_activate_text("<font color='#FFFFFF'>Open</font>\r\n <b>Chest</b> ", "") == PromptText{"Open", "Chest"}));
  CHECK(!prompt_from_activate_text("", "Chest") && !prompt_from_activate_text("<font></font>\nChest", "Chest"));
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
  // Our magic pane closes as the journal does, and on P (Quick Magic) again, as the chart on M.
  CloseControl p;
  p.quick_magic = true;
  CHECK(close_intent("magic", esc, false) == R"({"type":"view.close","v":1,"body":{"view":"magic"}})");
  CHECK(close_intent("magic", b, false) && close_intent("magic", tab, false) && close_intent("magic", p, false));
  CHECK(!close_intent("magic", m, false) && !close_intent("chart", p, false) && !close_intent("journal", p, false));
}

void the_table() {
  std::set<std::string_view> ids;
  for (const auto& s : kViews) {
    ids.insert(s.id);
    // each view its own page, but the map pane: the chart's page laid out docked (pane.html, 1.12 look 1)
    CHECK(s.page == (s.id == "chartpane" ? std::string("argonia/chart/pane.html")
                                         : "argonia/" + std::string(s.id) + "/index.html"));
  }
  CHECK(ids.size() == kViews.size());
  CHECK(spec("hud") && !spec("hud")->modal);
  CHECK(spec("dialogue") && spec("dialogue")->modal);
  CHECK(!spec("inventory"));
  CHECK(spec("magic") && spec("magic")->modal);
  CHECK(spec("chartpane") && !spec("chartpane")->modal);  // display only: never takes the focus from Wind UI
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
  CHECK(!s.player && s.places.empty());
}

// 1.12 §5: a marker is a place only once discovered; the player's marker; the minimap carries what is in reach.
void chart_marks() {
  const double cu = 4096;
  CHECK(!chart_place(0x0A000801, "Claywater Station", chart::kMarkerVisible, 3, 0, 0));  // known, not reached
  CHECK(!chart_place(0x0A000801, "", 3, 3, 0, 0));
  CHECK(!chart_place(0x0A000801, "door", 3, 61, 0, 0));
  auto p = chart_place(0x0A000801, "Claywater Station", 3, 3, -58.5 * cu, 10.25 * cu);
  CHECK(p && p->id == "0A000801" && p->kind == "settlement" && p->x == -58.5 && p->y == 10.25);
  const auto me = chart_player(-58 * cu, 10 * cu, 3.14159265358979323846 * 0.75);
  CHECK(me.x == -58 && me.y == 10 && me.heading == 135);
  chart::Discovered d;
  for (int x = -70; x <= -50; ++x) for (int y = 0; y <= 20; ++y) chart::reveal(d, {x, y});
  const auto far = *chart_place(0x0A000802, "Far", 3, 1, -40 * cu, 10 * cu);
  const auto m = minimap(d, {*p, far}, me);
  CHECK(m.map.player == me && m.map.places == std::vector<msg::ChartPlace>{*p});
  CHECK(!m.map.revealed.empty() && m.map.revealed.size() < 140);  // a disc of reach 5: about pi * 6^2 cells
  for (const auto& c : m.map.revealed) CHECK(std::abs(c.x + 58) <= 6 && std::abs(c.y - 10) <= 6);
  CHECK(minimap(d, {*p}, std::nullopt) == msg::HudMinimap{});
  const auto s = chart_state(d, {-58, 10, 4}, {*p}, me);
  auto j = msg::encode(s);
  CHECK(j && j->find(R"("player":{"x":-58,"y":10,"heading":135})") != std::string::npos);
  CHECK(msg::encode(m).has_value());
}

void the_journal() {
  journal::Log log;
  for (int i = 0; i < 8; ++i) journal::append(log, i < 7 ? 1u : 2u, std::uint32_t(10 * (i + 1)), {201, 8, 16 + i, 9.0});
  auto name = [](journal::QuestId q) { return QuestNames{"quest." + std::to_string(q), "Quest " + std::to_string(q)}; };
  auto text = [](journal::QuestId, journal::EntryId e) { return "entry " + std::to_string(e); };
  const Directions none;
  const GroupOf by_line = [](journal::QuestId q) { return journal::Group{q == 1 ? "Line A" : "Line B", false}; };
  using P = msg::JournalPage;
  // All entries: the diary, oldest first, paged; clamped to the last page.
  auto s = journal_state(log, name, text, none, by_line, P{msg::JournalTab::all, 0, {}, {}}, 6);
  CHECK(s.page_count == 2 && s.entries.size() == 6 && s.entries[0].runs[0].text == "entry 10" && s.groups.empty());
  CHECK(s.entries[0].date.text == "16th of the Eighth Month, 201" && s.matches == 8);
  s = journal_state(log, name, text, none, by_line, P{msg::JournalTab::all, 9, {}, {}}, 6);
  CHECK(s.page == 1 && s.entries.size() == 2);
  // The search: every word, any case; it narrows the diary and the count.
  s = journal_state(log, name, text, none, by_line, P{msg::JournalTab::all, 0, {}, std::string("ENTRY 8")}, 6);
  CHECK(s.matches == 1 && s.entries.size() == 1 && s.entries[0].runs[0].text == "entry 80" && s.search == "ENTRY 8");
  s = journal_state(log, name, text, none, by_line, P{msg::JournalTab::all, 0, {}, std::string("")}, 6);
  CHECK(!s.search && s.matches == 8);
  CHECK(msg::encode(s).has_value());
  CHECK(date({201, 1, 1, 0}).text == "1st of the First Month, 201" && date({201, 3, 22, 0}).text.starts_with("22nd"));
  CHECK(date({201, 3, 13, 0}).text.starts_with("13th") && date({201, 3, 23, 0}).text.starts_with("23rd"));
  const journal::Log empty;
  s = journal_state(empty, name, text, none, by_line, P{msg::JournalTab::current, 0, {}, {}});
  CHECK(s.page_count == 1 && s.groups.empty() && !s.quest && msg::encode(s).has_value());
  s = journal_state(log, name, text, none, by_line, P{msg::JournalTab::current, 0, {}, {}});
  CHECK(s.groups.size() == 2 && s.groups[0].label == "Line B" && s.quest && s.quest->id == "quest.2" && !s.quest->directions);
  s = journal_state(log, name, text, none, by_line, P{msg::JournalTab::topics, 0, {}, {}});
  CHECK(s.groups.empty() && s.entries.empty() && !s.quest);  // 2.12 fills it
}

// Current and Finished: grouped by questline or place, most recent first; a failed quest is Finished and marked;
// a quest opens on its latest direction, then its entries newest first; the search keeps a quest by any entry.
void the_journal_ribbons() {
  journal::Log log;
  journal::append(log, 1, 10, {201, 8, 16, 9});
  journal::append(log, 2, 10, {201, 8, 17, 9});
  journal::append(log, 3, 10, {201, 8, 18, 9});
  journal::append(log, 1, 20, {201, 8, 19, 9});
  journal::append(log, 4, 10, {201, 8, 20, 9});
  journal::append(log, 4, 90, {201, 8, 21, 9}, journal::Kind::fail);
  journal::append(log, 3, 40, {201, 8, 22, 9}, journal::Kind::complete);
  auto name = [](journal::QuestId q) { return QuestNames{"quest." + std::to_string(q), "Quest " + std::to_string(q)}; };
  auto text = [](journal::QuestId q, journal::EntryId e) { return "q" + std::to_string(q) + " entry " + std::to_string(e); };
  const Directions dir = [](journal::QuestId q, journal::EntryId e) -> std::optional<std::string> {
    return "go on from " + std::to_string(q) + "/" + std::to_string(e);
  };
  const GroupOf g = [](journal::QuestId q) {
    return q == 2 ? journal::Group{"Marsh Charter", false} : journal::Group{"Claywater Station", true};
  };
  using P = msg::JournalPage;
  auto s = journal_state(log, name, text, dir, g, P{msg::JournalTab::current, 0, {}, {}});
  CHECK(s.groups.size() == 2 && s.matches == 2 && s.quest && s.quest->id == "quest.1");  // the most recent opens
  CHECK(s.groups[0].label == "Claywater Station" && s.groups[0].kind == msg::QuestGroupKind::place);
  CHECK(s.groups[0].quests.size() == 1 && s.groups[0].quests[0].id == "quest.1");  // written last: first
  CHECK(s.groups[1].label == "Marsh Charter" && s.groups[1].kind == msg::QuestGroupKind::questline);
  CHECK(s.groups[0].quests[0].last.day == 19 && s.groups[0].quests[0].started.day == 16);
  s = journal_state(log, name, text, dir, g, P{msg::JournalTab::current, 0, std::string("quest.1"), {}});
  CHECK(s.quest && s.quest->directions == "go on from 1/20" && s.quest->group == "Claywater Station");
  CHECK(s.quest && s.quest->entries.size() == 2 && s.quest->entries[0].runs[0].text == "q1 entry 20");  // newest first
  s = journal_state(log, name, text, dir, g, P{msg::JournalTab::finished, 0, {}, {}});
  CHECK(s.groups.size() == 1 && s.groups[0].quests.size() == 2);
  CHECK(s.groups[0].quests[0].id == "quest.3" && s.groups[0].quests[0].status == msg::QuestStatus::complete);
  CHECK(s.groups[0].quests[1].id == "quest.4" && s.groups[0].quests[1].status == msg::QuestStatus::failed);
  s = journal_state(log, name, text, dir, g, P{msg::JournalTab::finished, 0, std::string("quest.4"), {}});
  CHECK(s.quest && !s.quest->directions && s.quest->status == msg::QuestStatus::failed);  // an ended quest: none
  s = journal_state(log, name, text, dir, g, P{msg::JournalTab::finished, 0, std::string("quest.1"), {}});
  CHECK(s.quest && s.quest->id == "quest.3");  // not on this ribbon: the most recent opens instead
  s = journal_state(log, name, text, dir, g, P{msg::JournalTab::current, 0, {}, std::string("Entry 20")});
  CHECK(s.matches == 1 && s.groups.size() == 1 && s.groups[0].quests[0].id == "quest.1");
  s = journal_state(log, name, text, dir, g, P{msg::JournalTab::current, 0, {}, std::string("no such words")});
  CHECK(s.matches == 0 && s.groups.empty() && msg::encode(s).has_value());
}

// LF83's words and group from the generated table (quest rows -> journal_text.h): an entry's text, the active
// quest's directions from its latest stage, none once it has ended; listed under its place, Claywater Station.
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
  for (const auto& r : gen::kJournalQuests) CHECK(seam::key(r.quest_id) == r.quest && !r.title.empty());
  CHECK((entry_group(lf83) == journal::Group{"Claywater Station", true}));
  CHECK((entry_group(lf83 + 1) == journal::Group{"Other quests", false}));

  journal::Log log;
  journal::append(log, lf83, 10, {201, 8, 16, 9.0});
  journal::append(log, lf83, 20, {201, 8, 17, 9.0});
  auto name = [](journal::QuestId) { return QuestNames{"quest.local.lf83", "The Well and the Landing"}; };
  using P = msg::JournalPage;
  auto s = journal_state(log, name, entry_text, entry_directions, entry_group, P{msg::JournalTab::all, 0, {}, {}});
  CHECK(s.entries.size() == 2 && s.entries[1].runs[0].text.starts_with("At Claywater Station, Livia Varinius told me"));
  s = journal_state(log, name, entry_text, entry_directions, entry_group,
                    P{msg::JournalTab::current, 0, std::string("quest.local.lf83"), {}});
  CHECK(s.groups.size() == 1 && s.groups[0].label == "Claywater Station");
  CHECK(s.quest && s.quest->directions && s.quest->directions->starts_with("The clay cut is below"));
  CHECK(msg::encode(s).has_value());
  journal::append(log, lf83, 40, {201, 8, 20, 9.0}, journal::Kind::complete);
  s = journal_state(log, name, entry_text, entry_directions, entry_group, P{msg::JournalTab::current, 0, {}, {}});
  CHECK(s.groups.empty());
  s = journal_state(log, name, entry_text, entry_directions, entry_group,
                    P{msg::JournalTab::finished, 0, std::string("quest.local.lf83"), {}});
  CHECK(s.groups.size() == 1 && s.groups[0].quests[0].status == msg::QuestStatus::complete && s.quest && !s.quest->directions);
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
  prompt_text();
  the_table();
  push_waits_for_ready();
  one_modal();
  hud_always_open();
  latch();
  chart_layout();
  chart_reveal();
  chart_marks();
  the_journal();
  the_journal_ribbons();
  the_journal_text();
  the_probe();
  return TEST_MAIN_RESULT("views");
}
