# Lane paris: the play machine moves to Paris (#27)

## What was done
- AMI ami-0b28d03211e7d92d2 copied to eu-west-3 as ami-0f9b0854f7125d6a3 (150 GB, ~25 min, tagged project=argonia).
- Blocked at first by IAM: `argonia-agent`'s CreateInLondon statement was eu-west-2 only. Owner call #28 (one line,
  region list adds eu-west-3), applied by the owner 10:18; infra/OWNER-SETUP.md should show the two-region list.
- Paris SG sg-0617ac75f5e8c5e92 = London's rules (stream ports open; SSH from the build VM only). The build VM has no
  Elastic IP, so run.sh opens 22 for its current address on each call to a public-address machine.
- No key pair: the image carries the SSH key. Subnet euw3-az2 (spot placement score 9; London 4-6).
- i-06e8da597eb5fceab g6.xlarge spot (persistent, stop on interruption) in eu-west-3b, spot $0.33/h.
- L4 unbound on first boot as on London: `pnputil /add-driver C:\Windows\INF\oem81.inf /install` + reboot ->
  `NVIDIA L4, 596.86, 23034 MiB`. Needed once per new instance from this image; the image baked after handover keeps it.
- Windows' "Networks" discovery flyout (explorer, new network) stole focus from the game and failed base_save:
  profile set Private, HKLM\...\Network\NewNetworkWindowOff created.
- Deploy: DEPLOY OK 556 s (stack push re-sent tropical-skyrim-sse, the image's stack was older); SKSE OK at 6a14cb8;
  base save 1.88 MB.

## Code (pushed)
- infra/gpu-box/machines.conf: machine -> region, address. Read by run.sh, build-VM idle-stop, cloudflare_gate.py
  (the worker's REGION binding).
- infra/cloudflare/test/switch.mjs refuses unless ARGONIA_SWITCH_E2E=1. Incident: run as a check at 10:10:26 it
  stopped game-21's London g6 mid-checks.
- job_guard.sh and tools/bridge.py accept named machines (argonia-play-paris).

## Heartbeat check (10:18)
Tunnel connected, /argonia-metrics/activity HTTP 200 with the service token; idle-stop task every ~15 min, stale
threshold 30 min from start. Not a cause of the London stops. Two machines on one tunnel split traffic, so only
one runs cloudflared (Automatic) at a time.

## Cut-over (11:10 UTC)
- Tags: London i-082ad5630dee91959 -> argonia-play-london (stays up for game-22); Paris -> argonia-play.
  machines.conf swapped; ~/.argonia/cache/ip-*, sg-* cleared. cloudflared: London Manual+stopped, Paris Automatic.
- Worker redeployed with REGION=eu-west-3: play.<domain>/argonia/status -> i-06e8da597eb5fceab running; heartbeat
  through the tunnel fresh.
- Owner's path: "Argonia (shaders on)" through moonlight-web, WebRTC decoding, still = Argonia main menu. Without the
  bridge: Plugins.txt *ArgoniaWorld.esm, *Argonia.esm (11:24:48); ArgoniaCore.log "0.3.0 loading on runtime
  1.7.104.0" at the card's launch 11:24:18.
- Start through the switch code with its own IAM user: EC2 running 7 s, tunnel healthy 24 s. The first attempt
  right after a stop got IncorrectSpotRequestState (spot request not yet `disabled`): the start page has no retry.
- After a start the first stream try can fail ("Tried all configured transport options"), the upstream stale-socket
  case after a failed session; the next try streamed. Not fixed here.
- wake.yml reads argonia-play's region from machines.conf. AWS_WAKE_ROLE's policy (OWNER-SETUP step 6) has no region
  condition; its play-machine start is unproved until the owner's next "play" comment.
- Cost: Paris spot $0.33/h (London g6 spot $0.286/h now). Build VM -> Paris TCP connect 7.9 ms (London ~1 ms).
- Not done: Loading Menu still (console at the main menu opened the save panel); London termination (kept for game-22);
  baked image from Paris (after the owner's first session); delete ami-0b28d03211e7d92d2 after a day.
