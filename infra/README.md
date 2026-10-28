# Infrastructure

What runs where, and how to rebuild it. Decision [0008](../docs/decisions/0008-infrastructure-aws-london-under-100-a-month.md)
holds the why and the budget; this file holds the facts. Update it in place whenever anything here changes.
Prices are 2026-10-27 research values until 0.1 replaces them with measured ones.

## Machines

| Name | Role | Type | Pricing | Disk | Access | Status |
|---|---|---|---|---|---|---|
| `argonia-build` | Claude Code, generators, L1–L3 tests | m7i-flex.xlarge (4 vCPU, 16 GiB, x86), Ubuntu 24.04 (moved from m7i.xlarge 2026-10-28: interruptions) | persistent spot, stop on interruption (spot price: _to record_) | 120 GiB gp3 | VS Code tunnel `argonia-build` (vscode.dev/tunnel/argonia-build, GitHub sign-in); SSM Session Manager as break-glass; no inbound rules | created by the owner 2026-10-27 |
| `argonia-play` | Skyrim (Windows Server 2022), Sunshine + Moonlight-Web, DCV, the gate, L4–L6 | g4dn.xlarge (T4) in eu-west-2a (g6/g5 had no spot capacity on 2026-10-28; type can change while stopped) | persistent spot, stop on interruption; idle-stop 15 min (`infra/gpu-box/idle-stop.ps1`); spot ~$0.25/h on 2026-10-28 | 150 GiB gp3 (~$14/month) | SSH from the build VM only (`infra/gpu-box/run.sh`); owner via `play.`/`dcv.` on the gated domain | created 2026-10-28 by `infra/gpu-box/create.sh` |
| old elder-souls-argonia box | the old project | m7i.2xlarge | stopped | 250 GiB gp3 (~$23/month) | — | owner call O-1 |

Region: **eu-west-2 (London)**, one VPC: the build VM in eu-west-2c, the game machine in eu-west-2a (where Windows GPU spot
capacity was); traffic between them crosses AZs at about $0.01/GB.

## Accounts, roles, budget

- AWS Budget `argonia-monthly`: $100, alerts at 50/80/100% actual and 100% forecast (owner set up, step 1).
- IAM role `argonia-build-ssm` on the build VM: `AmazonSSMManagedInstanceCore` (+ optional
  `CloudWatchAgentServerPolicy`); 0.1 adds the `argonia-agent` policy (EC2 start/stop/describe on
  `project=argonia`, S3 on the saves bucket, Cost Explorer read).
- Secrets: `~/.argonia/secrets.env` on the build VM (mode 600; never in the repo): R2 credentials (old vault),
  Nexus API key (if Premium), Fal key (1.2 onward), Selkies password.
- Steam: the owner's account, logged in once on each machine with Steam Guard; offline mode on the game machine;
  updates disabled for the pinned Skyrim (decision 0002): app manifest read-only, build **24914197** (runtime
  1.7.104.0), depots 489831 manifest 4940892828028256588, 489832 manifest 5728778377666085157, 489833 manifest
  4886117324142477814.
- The sign-in gate: Cloudflare (owner's account), domain bought 2026-10-28 (~$10/year, outside the AWS budget);
  a named tunnel `argonia-play` behind Access, owner's email only. Token and tunnel token in `secrets.env`.
- The play switch: Cloudflare Worker `argonia-play-switch` on `play.`/`dcv.` (behind Access; workers.dev off),
  schedules every 30 min and 03:00 UTC; IAM user `argonia-play-switch` (describe, start and stop `argonia-play`
  only; key in `secrets.env`). AWS alarm `argonia-play-no-stream` stops the machine with no stream for 30 minutes.
- The machine role `argonia-play-ssm`: SSM core plus S3 read of `nvidia-gaming` and `dcv-license.eu-west-2`.

## Setup scripts

- Build VM: `infra/build-vm/install.sh` installs `idle-stop.sh` (a timer, 20 minutes idle) and `resume.sh` (at
  boot); `setup.sh` and `smoke.sh` come in 0.1.
- Game machine: `infra/gpu-box/create.sh` (launch), `run.sh` (SSH, desktop-session jobs, start and stop),
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
