# Infrastructure

What runs where, and how to rebuild it. Decision [0008](../docs/decisions/0008-infrastructure-aws-london-under-100-a-month.md)
holds the why and the budget; this file holds the facts. Update it in place whenever anything here changes.
Prices are 2026-10-27 research values until 0.1 replaces them with measured ones.

## Machines

| Name | Role | Type | Pricing | Disk | Access | Status |
|---|---|---|---|---|---|---|
| `argonia-build` | Claude Code, generators, compilers, L1–L3 tests | m7i.xlarge (4 vCPU, 16 GiB, x86), Ubuntu 24.04 | persistent spot, stop on interruption (spot price: _to record_) | 120 GiB gp3 | VS Code tunnel `argonia-build` (vscode.dev/tunnel/argonia-build, GitHub sign-in); SSM Session Manager as break-glass; no inbound rules | created by the owner 2026-10-27 |
| `argonia-play` | Skyrim under Proton, bridge, Selkies, L4–L6 | g6.xlarge (L4) default; g4dn.xlarge / g5.xlarge fallbacks | persistent spot, stop on interruption; idle-stop 15 min | ~150 GiB gp3 | from the build VM over the VPC; owner via Selkies | created in 0.2 G0 |
| old elder-souls-argonia box | the old project | m7i.2xlarge | stopped | 250 GiB gp3 (~$23/month) | — | owner call O-1 |

Region: **eu-west-2 (London)**, same AZ for both project machines.

## Accounts, roles, budget

- AWS Budget `argonia-monthly`: $100, alerts at 50/80/100% actual and 100% forecast (owner set up, step 1).
- IAM role `argonia-build-ssm` on the build VM: `AmazonSSMManagedInstanceCore` (+ optional
  `CloudWatchAgentServerPolicy`); 0.1 adds the `argonia-agent` policy (EC2 start/stop/describe on
  `project=argonia`, S3 on the saves bucket, Cost Explorer read).
- Secrets: `~/.argonia/secrets.env` on the build VM (mode 600; never in the repo): R2 credentials (old vault),
  Nexus API key (if Premium), Fal key (1.2 onward), Selkies password.
- Steam: the owner's account, logged in once on each machine with Steam Guard; offline mode on the GPU box;
  updates disabled for the pinned Skyrim (decision 0002). Record the depot manifest ids here: _to record in P1_.

## Setup scripts (to be written)

- `infra/build-vm/setup.sh`, `smoke.sh`, `idle-stop.sh` (0.1).
- `infra/gpu-box/create.sh`, `setup.sh`, `idle-stop.sh` (0.2 S0); golden AMI in 3.4.
- `installer/install.py` (0.3).

## What the owner did by hand (2026-10-27)

1. Budget alert (step 1).
2. Launched `argonia-build` (step 2): Ubuntu 24.04 x86, m7i.xlarge, no key pair, no inbound rules, 120 GiB gp3,
   role `argonia-build-ssm`, persistent spot with stop on interruption.
3. VS Code tunnel service `argonia-build` (step 3): `code tunnel service install`, lingering enabled for `ubuntu`.
4. Claude Code installed and logged in; `gh` authenticated; repo cloned to `~/skyrim-argonia`; tmux session
   `argonia` (step 4).
