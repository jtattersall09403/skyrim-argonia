// L2: the journal log (2.12 §b): dated entries in order, no duplicates, nothing after a quest ends, the index's
// status and order, and the `journal` family payload.
#include "check.h"
#include "argonia/core/journal.h"

using namespace argonia::core::journal;

int main() {
  Log log;
  const GameDate d1{201, 8, 17, 9.5}, d2{201, 8, 18, 14}, d3{201, 9, 1, 6};
  CHECK(append(log, 10, 0, d1));
  CHECK(append(log, 20, 0, d2));
  CHECK(!append(log, 10, 0, d2));  // a stage re-entered logs once
  CHECK(append(log, 10, 30, d3, Kind::complete));
  CHECK(!append(log, 10, 40, d3));  // nothing after the end
  CHECK(append(log, 20, 10, d3, Kind::fail));
  CHECK(log.entries.size() == 4);

  auto ix = index(log);
  CHECK(ix.size() == 2);
  CHECK(ix[0].quest == 20 && ix[0].status == Status::failed);  // most recently written first
  CHECK(ix[1].quest == 10 && ix[1].status == Status::complete);
  CHECK(ix[1].started == d1 && ix[1].last == d3);
  CHECK((ix[1].entries == std::vector<std::size_t>{0, 2}));
  CHECK(d1 < d2 && d2 < d3);
  CHECK(index({}).empty());

  auto back = decode(encode(log));
  CHECK(back && *back == log);
  auto bad = encode(log);
  bad[4 + 4 + 4 + 12 + 8] = 7;  // the first entry's kind
  CHECK(!decode(bad));
  bad.pop_back();
  CHECK(!decode(bad));

  // The "journal updated" notice: one per entry or clue, a clue and its stage's entry merged, the stack ages out.
  Notices ns;
  auto a = notify(ns, NoticeCause::clue, "LF83", 1, 100.0);
  CHECK(a && a->seq == 1 && a->cause == NoticeCause::clue);
  CHECK(!notify(ns, NoticeCause::entry, "LF83", 20, 101.5));  // the stage the clue set: merged
  auto b = notify(ns, NoticeCause::entry, "LF84", 10, 101.5);  // another quest is told
  CHECK(b && b->seq == 2 && b->quest == "LF84");
  auto c = notify(ns, NoticeCause::entry, "LF83", 30, 102.0);  // the merge window has passed
  CHECK(c && c->seq == 3 && c->mark == 30);
  CHECK(live(ns, 103.0).size() == 3);
  CHECK((live(ns, 107.0) == std::vector<Notice>{*b, *c}));   // the first aged out after kNoticeLife
  CHECK(live(ns, 200.0).empty());
  // Raised in a conversation (our HUD hidden), the notice waits for the HUD: it is shown its full life after.
  Notices hid;
  hide(hid, 300.0);
  const auto in_talk = notify(hid, NoticeCause::entry, "quest.local.lf83", 10, 301.0);
  CHECK(in_talk && live(hid, 330.0).size() == 1);   // 29 s in the conversation: still held
  show(hid, 330.0);
  CHECK(live(hid, 335.0).size() == 1);               // 5 s on the HUD
  CHECK(live(hid, 336.5).empty());                   // gone after its 6 s
  // One already 4 s old when the HUD hid keeps its 2 s left.
  Notices aged;
  notify(aged, NoticeCause::clue, "quest.local.lf83", 1, 400.0);
  hide(aged, 404.0); show(aged, 500.0);
  CHECK(live(aged, 501.5).size() == 1 && live(aged, 502.5).empty());
  CHECK(kNoticeText == "Journal updated");
  return TEST_MAIN_RESULT("core.journal");
}
