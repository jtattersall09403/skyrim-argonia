# Lane infra-play2: N game machines (2026-10-29)

## The way (decision note)

Clone `argonia-play` and run more machines; don't run several Skyrim instances on one machine. One machine has
one Steam sign-in, a single GPU (a T4 on g4dn), and the game's frame times are what L4 measures. Two games on
one machine would share all three and skew every measurement. A clone needs no new Steam sign-in and no
reinstall, and costs the same per hour as the original. N machines are named `argonia-play`, `argonia-play-2`,
`argonia-play-3`, and so on.

## Measured blockers (owner, issue 13)

- **IAM:** the build role `argonia-build-ssm` may not run `ec2:CreateImage`. The `argonia-agent` policy only
  grants it on resources tagged `project=argonia`, and a new image has no tag yet. `ec2:CreateSnapshot` and
  `ec2:RegisterImage` are denied too (`--dry-run`, 2026-10-29). Because there's no image, there's no clone.
  Issue 13 holds the policy block to add (`CloneMachines`, `TidyClones`).
- **Quota:** `L-3819A6DF` (All G and VT Spot Instance Requests) is **8 vCPU**, and `L-DB2E81BA` (On-Demand G and
  VT) is **0**. `argonia-play` is a g4dn.xlarge (4 vCPU), so only **two** game machines can run at once. Three
  need 12 vCPU. The request asks for 16. The text, ready to paste: "Game test automation for a hobby mod project:
  up to four g4dn.xlarge or g6.xlarge Windows spot instances at once in eu-west-2, each stopped when idle."
- **Cost:** each machine past the first breaks the $100 cap on its disk alone ($13.92/month each). The owner
  rules "go 3", "go 2" or "cap" on issue 13.

Until the owner grants the IAM change: play-2 and play-3 don't exist, nothing reached the main menu on a clone,
and `argonia-play` was never touched. There was no image, so I took no snapshot.

## What was built (commit 03143eb, plus the bridge commit after it)

- `tools/bridge.py [--machine NAME]` and `Machine(name=)`: the local tunnel port is 47615 + N, the token cache `~/.argonia/bridge-NAME`; argonia-play keeps 47615 and `~/.argonia/bridge`.
- `run.sh [--machine NAME]`, or `ARGONIA_PLAY=NAME`. The default is `argonia-play`. Names other than
  `argonia-play` and `argonia-play-<n>` are refused (exit 2). `run.sh machine` is the dry run:
  `argonia-play i-0a3a…` by default and `argonia-play-2 None` with the flag.
- `stack.py --machine NAME …`. Per machine: push record `~/.argonia/stack/push-NAME`, stills `stills-NAME`.
- `skse_build.sh --machine NAME …`. `saves.sh` writes to `saves/NAME/` in the bucket (argonia-play keeps `saves/`).
- `job_guard.sh run --gpu[=NAME]` takes a lock per machine and sets `ARGONIA_PLAY` for the job.
  `argonia-play` keeps `gpu.lock`. `tooling/tests/test_job_guard.py`: 2 passed. Same machine: the second job is
  refused. Play, play-2 and play-3 run side by side. Bare `--gpu` follows `ARGONIA_PLAY`.
- `clone.sh [--from SRC] [--new-image] argonia-play-N [type] [az]` is repeatable:
  - it reuses the newest image tagged `argonia-image=SRC`, or takes one with `--no-reboot`;
  - it launches a persistent spot clone in group `argonia-play-clone`, with SSH from the build VM only and egress
    inside the VPC only, so there's no stream, no tunnel connector and no Steam online;
  - it disables cloudflared (the clone carries the gate's token), names Windows `ARGONIA-PLAY-N`, reboots, and
    seeds the push record.
  - The source group `argonia-play` opens the stream ports to 0.0.0.0/0, so clones don't use it.
- `idle-stop.sh` (build VM): before it stops the build VM, it stops every running `argonia-play-*`.
  `argonia-play` stays with its own idle-stop and the play switch.
- `cost_report.py` prints each machine's state, its live spot price per hour and its disk per month.
- `infra/README.md`: the multi-machine section, cost per hour, the November forecast.

## Costs (live 2026-10-29)

- g4dn.xlarge: $0.251/h ($0.246 spot + IPv4). g6.xlarge: $0.292/h. Disk: $13.92/month per game machine.
- Build VM: $0.090/h, plus $11.14/month for its disk.
- November forecast: about $92 with 1 machine and 60 h, about $121 with 2 machines and 100 h, about $135 with 3
  machines and 100 h.
- October month to date: $360.50 (excused).

## When the owner says done

```
tooling/job_guard.sh run --gpu=argonia-play-2 clone-2 -- infra/gpu-box/clone.sh argonia-play-2
infra/gpu-box/run.sh --machine argonia-play-2 ip; infra/gpu-box/run.sh --machine argonia-play-2 ps hostname
python3 infra/gpu-box/stack.py --machine argonia-play-2 menu        # MAIN-MENU OK; Steam offline, no login prompt
infra/gpu-box/run.sh --machine argonia-play-2 stop
```

For play-3, run the same with `argonia-play-3` while play-2 is stopped (quota 8 = two running).

Not yet proved, and to check at that step:
- whether Steam starts offline on a clone with no internet egress;
- whether the Windows rename leaves Steam's saved sign-in intact.

If either fails, it's an owner moment.

## Docs for the planner

ways-of-working §3 and `phases/README.md` say "one lane drives the game at a time". They need to change to "one
lane per game machine". The `job_guard --gpu` mentions in the 0 README, 4.2 and `records_jobs.sh` still hold:
bare `--gpu` is unchanged.
