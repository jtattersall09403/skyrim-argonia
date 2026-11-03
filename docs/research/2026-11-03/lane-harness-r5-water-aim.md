# Lane harness-r5-water-aim: water stops must hold water

Cause: the water-types stops stood 15 m back from a cell-level shore. A water cell's ground can be dry across most of it
(the sea stop stood 210 m from the real shoreline, facing a hillside), and the foliage clearance (stand_near/stand_bad)
then moved the stand without re-aiming at the water.

Fix (tools/journeys):
- `water_share` (__init__): share by area of the near field (0-60 m along the aim, +-30 deg) that is water at or below the
  eye and in sight (ground between does not rise over the line). `water_stop_bad` fails a stop whose heading is >3 deg off
  its subject, whose aim point is not water, or whose share is under `min_share(step)` (40%; stream 8%).
- `tools.journeys check` runs it on every water-types stop (red on a violation); unit tests on a synthetic cell grid in
  tools/tests/test_journeys.py.
- gen `_fit`: the stand is searched within 30 m of the authored one (dry, clear), aimed at the body's centre, and must
  pass the invariant; the best shore first, up to 40 shores, else the refresh raises (no silent off-aim stop). The real
  shore is the first wet sample out from a dry-middled water cell. Each refresh prints the share per stop.
- Sea: aim 400 m out over water, pitch 0, horizon in frame.

Shares (refresh of 2026-11-03): sea 100%, green-marsh 45%, black-swamp 95%, river 95%, stream 18%, tarn 97%, brackish-rim 61%.

Ruling needed (my choice, flag it): a creek is a few metres wide, so no stand can reach 40% of a 60 m x 60 deg field
(about 20% at the very most); the stream stop's floor is 8% (`WATER_MIN_SHARE_BY_STEP`), with its aim point still water.
Stream is the only exception; the 18% stand has the channel in frame.
