# Lane 1.15-r5-creatures-journey

The round-5 run of `creatures-kinds` passed with three stills framing no creature and no check on the kinds. It is now a
check that can fail, generated from the build.

- Generator `tools/journeys/gen.py creatures_kinds`, run by `python3 -m tools.journeys refresh` (`creatures-kinds` is in
  DERIVED, so `tools.journeys check` covers its stands).
- Each of three classes (coastal-lagoon, northern-transition, western-frontier) takes a planned land or shore spawn of the
  whole-province creature plan: the class on the most cells two out (13+ of 25 first), then the most spawn points within 90 m,
  3+ cells from a place. The first candidate with a dry stand 15-25 m off and a clear eye line wins
  (`frame(..., band=(15, 25))`, new). First person, HUD off, facing the spawn.
- `read [actors, 8192]` kept as the class's list, and a new expectation `kinds: {ge: 4, among: [list names]}`
  (`tools/run_journey.py check_kinds`) fails unless 4 distinct kinds of the class's list are live within two cells; kinds
  found are kept in report.json (`<class>_kinds`). A kind matches an actor whose name ends it or that it ends.
- Fourth stop `guar-pen`: stand 8 m from the pen, dry and clear, facing the two guar; per guar `dead` false, `disabled`
  false, `dist` < 1500; the actors list kept as `guar_pen`. It teleports by cell and setpos: the vocab cache on this
  machine predates the guar refs, so a `moveto ARG_Ref_...` fails the lint; the actors read with the ref id is fine.
- Not run on a machine. The earlier run found 2 kinds at the lagoon, 0 in the north and 1 in the west within two cells, so
  expect the `kinds` expectation to fail on the round-5 build: that is the finding it was built to make.
- Tests: `test_kinds_found_counts_distinct_live_kinds`; test_run_journey, test_journeys, test_journey_lint 54 passed;
  `run_journey --dry` ok; `tools.journeys check` 0 stale.
