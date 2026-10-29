<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.10-loops/search.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: search and alarm (2.10 § Loops, lane 2.10-b)

Rule (decisions 0151 item 1, 0092; lore `topics/skyrim-sneak-detection.md`
§1): every observer keeps its own notice state; one that loses the player
walks to the last known position, looks (one look-around at its turn rate),
widens to two further points at its alarm radius, gives up on the
detection row's `searchTimeoutS` and returns to its post. An alarm call puts
every observer within the caller's `alarmRadiusM` into suspicious at the
caller's last known position. A found body (a dead one of the finder's kin
within sight) makes the finder suspicious. Eyes: a people strip of the
search, read by a `reader` (lanes/2.10/b-reader.md).

Measures:

- `cd packages/game-core && npx vitest run src/ai/search.test.ts`

| Measurement | Bar | Result | Elapsed | Capture |
|---|---|---|---|---|
| Lose the player: walks to the last known position on a nav path | reaches it | green: walks there (search.test 1; stealthStep "searches the last known position": walk intent to (0,0,6)) | 5 ms (one test, walk to give-up) | `search.test.ts` |
| Looks there (one look-around) | dwell = 360 / turnDegPerS | green (search.test 1) | 5 ms (same run) | `search.test.ts` |
| Widens to two further points at alarmRadiusM | 2 points, each at alarmRadiusM | green (search.test 1) | 5 ms (same run) | `search.test.ts` |
| Gives up on searchTimeoutS and returns to its post | gives up at the timeout, ends home | green (search.test 1, 2: gives up with points left at 6 s: owner call, the timeout is short for walk + look + widen) | 5 ms + 0 ms | `search.test.ts` |
| Alarm call: observers within alarmRadiusM go suspicious at the caller's last known position | inside: suspicious; outside: unchanged | green: pure (search.test 4, 5) and wired (stealthStep "the alarm call": 15 m suspicious and walking, 25 m unaware) | 0 ms + 0 ms pure, 2 ms wired | `search.test.ts` |
| Found body of the finder's kin in sight: suspicious | kin in sight: suspicious; not kin or unseen: unchanged | green: pure (search.test 6), persons wired (stealthStep "the found body", once per body), creatures wired (creatureEnemy "the found body") | 1 ms pure, 1 ms persons, 5 ms creatures | `search.test.ts` |
| `observersEngaged(state)` returns the engaged ids; `searching(id)` readable | exact ids | green (search.test 7; stealthStep test 1) | 1 ms | `search.test.ts` |
| People strip of a search read by a reader | a player understands it | | | b-reader.md |
