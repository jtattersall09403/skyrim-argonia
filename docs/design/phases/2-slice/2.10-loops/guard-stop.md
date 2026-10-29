<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.10-loops/guard-stop.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: the guard stop and custody (2.10 § Loops, lane 2.10-f)

Rule (decision 0151 item 2; world/76 §124; 0142 § 3): where a place has a
watch, a watch person who has the player in `engaged` while the region's Owing
is open starts the `guard-stop` entry: pay (gold, refused when short), serve
(custody: the lamp clock advances by amount × custodyHoursPerNushmeeko, pending
skill progress is lost, the player wakes at the watch's custodyPost, the people's
day runs on), or resist (assault filed, the watch provoked through answered
violence; a later pay or serve makes amends and fires placeCleared). A place with
no watch judges by the crime's weight (0142). Eyes: a strip of the stop and of
waking from custody is lane j's pod (journey step named in the report).

Measures:

- `cd packages/game-core && npx vitest run src/crime`
- `cd packages/scene && npx vitest run src/interact/crime-session.test.ts`

| Measurement | Bar | Result | Elapsed | Capture |
| Measurement | Bar | Result | Elapsed | Capture |
|---|---|---|---|---|
| The stop opens only for a watch person engaged with the player, Owing open in the watch's region, watch non-null | 4 cases | 5 of 5 (plus no watch) | 2.8 s (game-core run) | `crime/crime.test.ts`; `crime-session.test.ts` |
| Pay: gold taken, entries cleared as "paid"; refused when short with its line | 2 of 2 | 2 of 2 (49 gold refused with `text.system.guard-stop.short`; 500 → 450) | 5.5 s (scene run, 10 tests) | `crime-session.test.ts` |
| Serve: clock + amount × custodyHoursPerNushmeeko, pending skill progress 0, player at custodyPost, entries cleared as "served" | 4 of 4 | 4 of 4 (0.5 × 24 = 12 h) | same run | `crime-session.test.ts` |
| Serve moves the people's day (the schedule block after the advance differs) | green | green (catch-up at the wake minute; a Riverwalk person's block changes 14:00 → 02:00) | same run | `crime-session.test.ts` |
| Resist: assault filed, the watch provoked; a later pay or serve calls makeAmends and placeCleared; the place peaceful | green | green (three An-Xileel hostile; served 60 h; one place-cleared event; every record back to its own hostility) | same run | `crime-session.test.ts` |
| No watch: the place judges by the crime's weight through hostileReaction | green | green (theft: ledger only; assault: victim and kin answer via `answer`; no stop) | same runs | `crime/crime.test.ts`; `crime-session.test.ts` |
| Custody credits no skill use | 0 uses logged | 0 | same run | `crime-session.test.ts` |
| Drive: steal seen → ledger → greeting; crime → standing; resist → hostile → clear → peaceful; custody → clock → day → progression | 4 of 4 | 4 of 4 | same run | `crime-session.test.ts` |
| Strip of the stop and of waking from custody | lane j's pod | owed to lane j: journey step `guard-stop` (stop, choose serve, wake at custodyPost) | n/a | lane j |
