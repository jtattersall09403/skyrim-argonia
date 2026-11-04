# Lane 1.15-r6-scan-retake: a scan of headings at every look stop, and a done marker per journey

Owner ruling 19:05 #41 (0036 amended): every look stop takes a scan of headings; a wrongly framed capture is judged and retaken inside the run. Route 0010 route 5 (our harness); 0037 (a scan is inside one step, so a resume loses at most one stop). No game was run.

## What changed
- `tools/run_journey.py`: a step with `scan: N` (after its still, when it passed) reads the stand's heading (`player` `heading_deg`), keeps the step's still under its old name and copies it to `<n>-<name>-s0.png`, then for k = 1..N-1 sets `player.setangle z h0 + k·360/N` (pitch untouched), waits `SCAN_SETTLE_S` = 2 s and captures `<n>-<name>-s<k>.png`; the stand's heading is put back after. report.json's step carries `scan: [{k, heading, still}]`. A step without `scan` is unchanged.
- `tools/journeys/look.py`: `with_scan` adds `scan: 6` (`SCAN`) to each stop it builds: `ground_materials` directly, `reaim` on every re-stood step with a `# subject:`, `booth_standard` on every booth step; idempotent (booth_standard twice gives the same text).
- `tools/journey_lint.py` `look`: a `look: world` stop without `scan` (an int ≥ 2) fails as `step <name>: look: world: a scan of headings at each stop (scan: 6; owner 19:05 #41)`.
- `tools/run_batch.py`: `<journey run dir>/done.json` (journey, run, verdict, failed_at, reason, report, stills, scans) as each journey finishes; `--on-done <cmd>` runs `<cmd> <done.json>` detached (new session, no stdio); a failed write or hook is printed and never fails the batch.
- `docs/research/2026-11-04/briefs/round-6-readers.md`: readers judge the scan, name the heading that shows the subject, PASS or FAIL on it, and name the heading the stand should take.

## Proof (L1, L2)
- `pytest tools/tests/test_run_journey.py test_run_batch.py test_journey_lint.py test_journeys.py`: 96 passed. New: a scan test (fake bridge at heading 30: headings 30, 90, ..., 330, 7 captures, setangle z turns then back to 30, no pitch line, s0..s5 files, report.json lists them, plain step unchanged); a lint test (the error names the step; `scan: 1` refused); a done-marker test (PASS and FAIL markers, hook args, detached, a hook that raises does not stop the batch). ruff clean.
- `run_journey.py --dry` ok on rock-booth and ground-materials after `booth_standard` / `with_scan` (6 and 2 stops with `scan: 6`), copies in the scratchpad, not committed.
- `test_the_five_look_journeys_meet_the_standard` ignores the scan error until the planner's `refresh` regenerates tests/journeys (after lane 1.15-r6-road-stop lands); drop that filter then.

## Cost per stop (estimated, not measured in game)
Five extra captures per stop at about 3 s each (2 s settle + about 1 s screenshot, the brief's figure) = about 15 s per stop. The look journeys hold 30 stops (claywater-look 10, tree-seat 12, rock-booth 6, ground-materials 2; road-look's 4 steps are not teleport stops), so about 450 s (7.5 min) on the round's 355-step batch. Measure it from report.json `seconds` on the first batch.

## What else should take a scan
The stills judged for framing that are not `look: world` yet: water-types (7), river-steps (8), world-panel stops, sky-ab vantages, creature-spots (7) and creatures-kinds (4) (a framing finding is exactly what a scan settles), claywater-walk (8). Their generators should mark them `look: world` or add `scan: 6` directly.
