# Lane g6: argonia-play moves to a g6.xlarge (owner #16, 2026-10-30)

## Prepared (measured 2026-10-30, before the cut-over)

- **Spot price, Windows, g6.xlarge:** eu-west-2a $0.2866/h, 2b $0.2864/h, 2c $0.4702/h. Nearest EU: eu-west-3
  $0.330, eu-central-1 $0.355-0.375, eu-west-1 none listed. g4dn.xlarge today: $0.2458/h (2a). London 2a: same AZ
  and subnet as the old machine, +$0.041/h. Paris (eu-west-3) is the fallback if 2a has no capacity: a few ms more
  from the UK, +$0.04/h more.
- **Quota:** `L-3819A6DF` (G and VT spot) is now **16 vCPU**: the old 4-vCPU machine and the new one fit side by side.
- **Driver:** the image carries the AWS GRID driver 596.86 (setup.ps1 base stage, `ec2-windows-nvidia-drivers`
  `latest/`, the `_aws_swl` build). The R595 GRID branch supports the L4; no reinstall expected; checked at first boot.
- **What pins identity:** only the EC2 `Name` tag `argonia-play`. run.sh, bridge.py, stack.py, job_guard and alarm.sh
  look the instance up by that tag; so does the play switch worker (`infra/cloudflare/play-switch.js` `state()`),
  which rewrites the stream host's DNS A record to the public IP on each start. No elastic IP exists. The cloudflared
  tunnel token, Sunshine's pairing certificate and the `argonia-idle-stop` task live on the disk, so the image
  carries them. Trap: the worker's DescribeInstances filter has no state filter, so a terminated instance still
  tagged `argonia-play` could be read first; the old machine is renamed `argonia-play-g4dn` before the new one
  launches. Only the `argonia-play-no-stream` alarm is keyed by instance id: re-run `alarm.sh`.

## Cut-over

1. Take the lock (`job_guard.sh run --gpu`), stop the old machine (run.sh stop backs up saves), image it stopped
   (consistent, not `--no-reboot`), tag the image `argonia-image=argonia-play`.
2. Rename the old instance `argonia-play-g4dn`; launch g6.xlarge in eu-west-2a from the image: SG
   `sg-0c73f686853568ced`, profile `argonia-play-ssm`, persistent spot stop-on-interrupt, tags Name=argonia-play,
   project=argonia; `alarm.sh` re-points the no-stream alarm.
3. Prove: nvidia-smi shows the L4, Steam offline, `stack.py menu` MAIN-MENU OK, bridge answers, the stream host
   resolves to it, idle auto-stop fires.
4. Measure frames; retire the old: terminate, cancel `sir-k9bzpisj`, delete `vol-0aad3b3dbba325a86` if left.

## Result (2026-10-30, 17:00-18:00 UTC): no capacity, cut-over not done

- Old machine stopped and imaged 17:01 (ami-097ecf465d213a2cd); dropped at the planner's call for the 16:19 image
  `ami-0e0653a8c139a7441` (available ~18:00), which stays the way back and the g6 source.
- Volume-swap route (option B): g6.xlarge spot in 2a refused, InsufficientInstanceCapacity.
- From the image: 2a, 2b, 2c all InsufficientInstanceCapacity. eu-west-1/-3, eu-central-1 G spot quota 0; the build
  role cannot request quota (servicequotas:RequestServiceQuotaIncrease denied). On-demand G quota 0.
- Old g4dn renamed back to `argonia-play`, started; PrismaUI.dll restored (game-14's .off); `stack.py verify` 1 bad
  (skse\plugins\tk-dodge.toml, tk-dodge-re-addon), left to game-15's deploy.
- London Windows spot $/h: g4dn.xlarge 0.246, g6.xlarge 0.287 (2c 0.470), g5.xlarge 0.312 (2b 0.413), g6.2xlarge
  0.492, g6e not offered. Placement score 1 for all.
- Retry: job `g6-retry` (every 15 min, 2 h) launches `argonia-play-g6` from the image and stops it; the cut-over
  then retags it argonia-play per the steps above. Posted on #16 with a g5.xlarge fallback ask.
