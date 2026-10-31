# Part 0 check ledger

Every check from the running game (L4 to L6) that a Part 0 brief owes, with what proved it. The format is fixed
(`tools/check_ledger.py` checks it in `make check`; `tools/run_batch.py` rewrites each `journey:<id>` row at the end
of every run). Status: owed, proven or dropped. A proven row carries its run, report line or commit; a dropped row
its owner-brief date. The mapping from each brief's acceptance lines is in
`docs/research/2026-10-31/ledger-audit.md`.

## 0.0 Can it be played?

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| The owner calls a setup playable with the X2s, and touch workable for the whole game | 0.0 Acceptance | L6 | proven | docs/phases/0-foundation/0.0-can-it-be-played.md:197 |
| Latency and stream health logged automatically per setup, device and network | 0.0 Acceptance | L4 | proven | docs/phases/0-foundation/0.0-can-it-be-played.md:206 |
| Frame time at least 60 fps median and 45 fps 1% lows on the chosen instance (vanilla, the g4dn) | 0.0 Acceptance | L4 | proven | docs/phases/0-foundation/0.0-can-it-be-played.md:192 |
| The owner's combat verdict on the stock souls-like mods | 0.0 Acceptance | L6 | proven | docs/phases/0-foundation/0.0-can-it-be-played.md:197 |

## 0.2 The stack

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| `stack.py verify` matches every installed hash | 0.2 §b | L4 | owed | docs/research/2026-10-31/lane-game-21.md:26 (2 bad of 22,574, argonia-theme) |
| The smoke scene passes twice in a row with no crash | 0.2 §c | L4 | proven | docs/research/2026-10-30/lane-game-8.md:40 |
| The smoke journey on the whole stack: place, walk, draw, swing, roll, block, menus | 0.2 §c, 0.3 §d | L4 | proven | journey:smoke pass out/batch/g18b/20261031T011830 |
| Rolls cover distance in all eight directions; a backstep from standstill | 0.2 §c | L4 | proven | docs/research/2026-10-30/lane-game-7.md:34 |
| RT power-attacks through One Click Power Attack's gamepad key | 0.2 §c | L4 | owed | no run on record |
| Climbing (FreeClimb), a ladder, and boarding and sailing the boat: each mod wired and loaded | 0.2 §c, Part 0 exit | L4 | owed | no run on record |
| Swimming and diving | 0.2 §c | L4 | dropped | owner-brief:2026-10-30 (base-Skyrim behaviour is not checked) |
| Frame times on the play machine (the g6) against the revised bar: median 50, 95% 45, 1% lows 25-30 | 0.2 §d, 1.7 packet | L4 | owed | docs/research/2026-10-31/lane-g6-move.md:52 (not measured) |

## 0.3 The agent's hands

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| The bridge answers every call the runner needs; ten scenes apply | 0.3 §a, §d | L4 | proven | docs/research/2026-10-30/lane-game-5.md:56 |
| ArgoniaCore loads on 1.7.104 and a co-save family survives a save and load | 0.3 §b | L4 | proven | docs/research/2026-10-30/lane-game-3.md:25 |
| The Creation Kit compiles our Papyrus on the machine | 0.3 §b | L4 | proven | 19e4e67 |
| A broken journey fails at its step with a readable reason and its still | 0.3 §d | L4 | proven | docs/research/2026-10-30/lane-game-6.md:36 |
| A forced crash reports within 60 s | 0.3 §d | L4 | proven | docs/research/2026-10-30/lane-game-6.md:37 |
| One unattended edit, deploy and verdict cycle, timed | 0.3 §e | L4 | proven | docs/research/2026-10-30/lane-game-8.md:109 |

## 0.4 The pipeline and the first block

| Check | From | Level | Status | Evidence |
|---|---|---|---|---|
| The quarantine: only ours and the allowlist run at days 0, 1, 10 and 50 | 0.4 §b | L4 | proven | journey:quarantine pass out/batch/g17/20261030T225900 |
| The player walks the road into Claywater, into the station house and out; a person at work by day and in bed by night | 0.4 §d | L4 | proven | journey:claywater-walk pass out/batch/g17/20261030T225900 |
| A person sleeps in her own bed at night (Livia, the native sleep) | 0.4 §d | L4 | proven | journey:livia-sleep pass out/batch/g17/20261030T225900 |
| The three people path between two spots | 0.4 §d | L4 | dropped | owner-brief:2026-10-30 (NPC movement is not checked in game) |
| Vantage and full-body stills of the block (the road in, the well, the houses, Livia, the signs) | 0.4 §d | L4 | proven | journey:claywater-look pass out/batch/g17/20261030T225900 |
| A reader passes the block's stills: grass on the paint, trees, no seam, tone mismatch or dark face | 0.4 §d | L4 | owed | no reader report on record |
| The owner walks Claywater (`bat claywater`) and climbs, swims and boards the boat (`bat proving-ground`) | Part 0 exit | L6 | owed | the 1.7 packet carries the walk |
