# Infrastructure

What runs where, and how to rebuild it. Decision [0008](../docs/decisions/0008-infrastructure-aws-london-under-100-a-month.md)
holds the why and the budget; this file holds the facts. Update it in place whenever anything here changes.
Prices are 2026-10-27 research values until 0.1 replaces them with measured ones.

## Machines

| Name | Role | Type | Pricing | Disk | Access | Status |
|---|---|---|---|---|---|---|
| `argonia-build` | Claude Code, generators, L1–L3 tests | m7i-flex.xlarge (4 vCPU, 16 GiB, x86), Ubuntu 24.04 (moved from m7i.xlarge 2026-10-28: interruptions) | persistent spot, stop on interruption (spot price: _to record_) | 120 GiB gp3 | VS Code tunnel `argonia-build` (vscode.dev/tunnel/argonia-build, GitHub sign-in); SSM Session Manager as break-glass; no inbound rules | created by the owner 2026-10-27 |
| `argonia-play` | Skyrim (Windows Server 2022), Sunshine + Moonlight-Web, DCV, the gate, L4–L6 | g4dn.xlarge (T4) in eu-west-2a (g6/g5 had no spot capacity on 2026-10-28; type can change while stopped) | persistent spot, stop on interruption; idle-stop 15 min (`infra/gpu-box/idle-stop.ps1`); spot ~$0.25/h on 2026-10-28 | 150 GiB gp3 (~$14/month) | SSH from the build VM only (`infra/gpu-box/run.sh`); owner via `play.`/`dcv.` on the gated domain | created 2026-10-28 by `infra/gpu-box/create.sh` |
| `argonia-play-N` (2, 3, …) | more game-driving lanes (owner, 2026-10-29: as many as parallelism needs) | the source's type, persistent spot | idle-stop as `argonia-play`; the build VM's idle-stop also stops every running clone | 150 GiB gp3 each (~$14/month, stopped or not) | SSH from the build VM only, group `argonia-play-clone` (egress inside the VPC only: no stream, no tunnel, Steam offline) | `infra/gpu-box/clone.sh`; waiting on the owner (IAM for images, spot G quota 8 vCPU = two running at once), issue 13 |
| old elder-souls-argonia box | the old project | m7i.2xlarge | stopped | 250 GiB gp3 (~$23/month) | — | owner call O-1 |

Region: **eu-west-2 (London)**, one VPC: the build VM in eu-west-2c, the game machine in eu-west-2a (where Windows GPU spot
capacity was); traffic between them crosses AZs at about $0.01/GB.

## Several game machines

- Every machine tool takes the target: `ARGONIA_PLAY=argonia-play-2`, or `--machine argonia-play-2` on `run.sh`,
  `stack.py`, `skse_build.sh` and `tools/bridge.py`; the default is `argonia-play`. `run.sh machine` prints which.
- `tooling/job_guard.sh run --gpu=argonia-play-2 …` takes that machine's lock and runs the job with `ARGONIA_PLAY`
  set; bare `--gpu` is `$ARGONIA_PLAY`, else `argonia-play` (its old `gpu.lock`). Locks are per machine.
- Per machine on the build VM: saves go to `saves/<name>/` in the bucket (argonia-play keeps `saves/`), stack.py's
  push record and menu still to `~/.argonia/stack/{push,stills}-<name>`, the bridge's tunnel port to 47615 + N.
- `infra/gpu-box/clone.sh argonia-play-N` makes one: an image of the source with `--no-reboot` (reused for later
  clones), a spot launch, then the tunnel connector off and the Windows name `ARGONIA-PLAY-N`.
- The owner's gate, play switch and alarm serve `argonia-play` only.

**Cost (2026-10-29, London spot):** a running g4dn.xlarge game machine is **$0.251/h** ($0.246 spot + $0.005
IPv4); a g6.xlarge $0.292/h. Each one also costs **$13.92/month** for its 150 GiB disk whether running or not;
the clone image adds about $0.053 per GB stored per month (about $4–5). The build VM is $0.090/h plus
$11.14/month disk. `tools/cost_report.py` prints these live for every machine.

**November forecast** (build VM ~520 h ≈ $47 + $11 disk; egress and IPv4 ~$5):

| Game machines | Game hours | Forecast |
|---|---|---|
| 1 (`argonia-play`) | 60 | ~$92 |
| 2 | 100 | ~$121 (image kept) |
| 3 | 100 | ~$135 |
| 3 | 150 | ~$147 |

So every machine past the first breaks the $100 cap (0008) on its disk alone. The owner's call is on issue 13: keep
the clones, or make them per batch and delete them after (then a clone costs only its hours plus the image).

## Accounts, roles, budget

- AWS Budget `argonia-monthly`: $100, alerts at 50/80/100% actual and 100% forecast (owner set up, step 1).
- IAM role `argonia-build-ssm` on the build VM: `AmazonSSMManagedInstanceCore` (+ optional
  `CloudWatchAgentServerPolicy`); 0.1 adds the `argonia-agent` policy (EC2 start/stop/describe on
  `project=argonia`, S3 on the saves bucket, Cost Explorer read).
- Passwords the owner types are four random words from the EFF large list, hyphenated (`chunk-table-scissors-otter`,
  about 51 bits); the Windows one is Capitalised, which Windows' complexity policy needs.
- **Never reset the game machine's Windows password** (`net user`): Windows then drops everything it encrypted
  under the old one, including Steam's saved sign-in, and the owner has to sign in to Steam again (2026-10-28).
  Change it only as the signed-in user, with the old password.
- Secrets: `~/.argonia/secrets.env` on the build VM (mode 600; never in the repo): R2 credentials (old vault),
  Nexus API key (if Premium), Fal key (1.2 onward), Selkies password.
- Steam: the owner's account, logged in once on each machine with Steam Guard; offline mode on the game machine;
  updates disabled for the pinned Skyrim (decision 0002): app manifest read-only, build **24914197** (runtime
  1.7.104.0), depots 489831 manifest 4940892828028256588, 489832 manifest 5728778377666085157, 489833 manifest
  4886117324142477814.
- The sign-in gate: Cloudflare (owner's account), domain bought 2026-10-28 (~$10/year, outside the AWS budget);
  a named tunnel `argonia-play` behind Access, owner's email only. Token and tunnel token in `secrets.env`.
- The play switch: Cloudflare Worker `argonia-play-switch` on `play.`/`dcv.` (behind Access; workers.dev off),
  schedules every 10 min and 03:00 UTC; IAM user `argonia-play-switch` (describe, start and stop `argonia-play`
  only; key in `secrets.env`). It stops the machine when its heartbeat (`/argonia-metrics/activity`, read with
  the Access service token `argonia-heartbeat`) is missing for 30 minutes after a start. The AWS alarm
  `argonia-play-no-stream` is kept with its actions off; the build role may manage that one alarm.
- The machine role `argonia-play-ssm`: SSM core plus S3 read of `nvidia-gaming` and `dcv-license.eu-west-2`.

## Setup scripts

- Build VM: `infra/build-vm/install.sh` installs `idle-stop.sh` (a timer, 20 minutes idle) and `resume.sh` (at
  boot); `setup.sh` and `smoke.sh` come in 0.1.
- Game machine: `infra/gpu-box/create.sh` (launch), `clone.sh` (another game machine from its image), `run.sh` (SSH, desktop-session jobs, start and stop),
  `setup.ps1` (stages), `cloudflare_gate.py` (the gate), `pair_moonlight_web.py`, `combat-mode.ps1`,
  `idle-stop.ps1`; golden AMI in 3.4.
- `installer/install.py` (0.3).

## What the owner did by hand (2026-10-27)

1. Budget alert (step 1).
2. Launched `argonia-build` (step 2): Ubuntu 24.04 x86, m7i.xlarge, no key pair, no inbound rules, 120 GiB gp3,
   role `argonia-build-ssm`, persistent spot with stop on interruption.
3. VS Code tunnel service `argonia-build` (step 3): `code tunnel service install`, lingering enabled for `ubuntu`.
4. Claude Code installed and logged in; `gh` authenticated; repo cloned to `~/skyrim-argonia`; tmux session
   `argonia` (step 4).
