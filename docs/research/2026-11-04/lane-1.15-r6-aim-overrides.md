# Lane 1.15-r6-aim-overrides: a reader-named heading reaches the stand (0036 amendment, owner 19:05 #41)

- `python3 -m tools.journeys ledger aim <journey> <step> <heading> [--pitch P]` records the override and the stand's x, y in tests/journeys/aims.yaml (tracked).
- `tools/journeys/aims.py` `apply_text` puts it on that step's `player.setangle` lines; sky_ab and the panel's journey_text apply it inside the generator (so the stale check agrees), refresh applies it to every other journey and prints "aim override: <journey> <step> <heading>".
- A stand more than 5 m from the recorded x, y drops the override on refresh (printed, removed from the file); the stand is never moved.
- First use: sky-ab coastal-lagoon-shore-noon 154 (the scan's lagoon heading; the stand's own aim 94 showed a frond tree).
- Tests: tools/tests/test_journeys_aims.py (write, apply, drop, panel vantages).
