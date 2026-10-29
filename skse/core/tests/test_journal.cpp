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
  return TEST_MAIN_RESULT("core.journal");
}
