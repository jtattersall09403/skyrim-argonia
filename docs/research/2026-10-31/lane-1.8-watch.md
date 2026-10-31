# lane-1.8-watch: the interruption notice (1.8 Work item 2)

## Built
- `infra/gpu-box/spot-watch.ps1`: polls IMDSv2 `latest/meta-data/spot/instance-action` every 5 s (token PUT, then
  the read); base URL from `-Metadata`, else `$env:ARGONIA_IMDS`, else `http://169.254.169.254`. Does nothing while
  SkyrimSE is not running. On a notice it writes `C:\argonia\state\interrupted.json` ({utc, action, time}) and sends
  `<token> core-suspend spot_reclaim` to ArgoniaBridge's socket (127.0.0.1:47615), the line tools/bridge.py sends.
  One save per notice (AWS repeats it; same action+time is skipped). `-Drill` starts a mock IMDS on 127.0.0.1:47620
  (HttpListener job) answering a stop notice, polls it, and prints one JSON line: ok when ArgoniaSuspend.ess is
  newer than the mock's start within 30 s.
- `setup.ps1`: scheduled task `argonia-spot-watch`, at startup as SYSTEM, no time limit, restarted on failure.
- Native reason: `SuspendWhy::spot_reclaim` (skse/core life.h/.cpp; to_string "spot_reclaim" so the log line reads
  `saves: ArgoniaSuspend written (spot_reclaim)`); suspend_due treats every caller's reason as always due when the
  game can save. Unit-tested in skse/core/tests/test_life.cpp (skse/check.sh: 33/33 pass). Bridge usage strings,
  `tools/bridge.py` SUSPEND_WHYS, and a machine-side `spot-drill` call (runs the drill; journey `read`).
- `tests/journeys/spot-watch.yaml` (scene first-place): `read [spot-drill] ok == true`, then the ArgoniaCore log line.
- Play page (`infra/cloudflare/play-switch.js`): state() reads the spot request's status code
  (DescribeSpotInstanceRequests) and `reclaimed` (marked-for-stop, instance-stopped-* other than by-user); the start
  page says "AWS took the machine back; your game was saved." Start retry (owner #29): a Start refused with
  IncorrectSpotRequestState / IncorrectInstanceState / InsufficientInstanceCapacity shows "Starting…" and retries at
  each 4 s reload for 2 min from the first refusal (cookie argoniaStartRetry), then shows AWS's error.
  Tests: `node infra/cloudflare/test/spot.mjs` (12 spot-message + 5 retry + 3 stubbed-page checks pass).
  **The Worker is not deployed** (coordinator deploys at the London g6.2xlarge cut-over). The switch's IAM user needs
  `ec2:DescribeSpotInstanceRequests`, else the message is silently absent (caught).

## Gate
make unit 469 passed; skse/check.sh 33/33; run_journey --dry ok. The cloudflare .mjs tests are not in make check.

## Owed
- The L4 journey: London (argonia-play-london) had no spot capacity all afternoon (InsufficientInstanceCapacity),
  so the check moved to argonia-play-new (g6.2xlarge, fresh from image). There deploy failed at launch and the
  journey failed at its scene (out/runs/spot-watch/20261031T135035): bridge `ping`/`player` "main thread did not
  run the task within 3000 ms", before any watcher step ran, likely EBS lazy-loading on the fresh disk. The
  coordinator took the batch over (pre-warm, redeploy, spot-watch). Runner: the scratchpad watch-new.sh.
- The watcher reaches the save through ArgoniaBridge (dev-only plugin). A player build without the bridge needs a
  non-dev seam (e.g. a named pipe in ArgoniaCore); the drill does not test the scheduled task itself, only the script.
