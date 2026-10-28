# 0008: Infrastructure: AWS London, an x86 build VM and an on-demand GPU box, under $100 a month

**Status:** decided 2026-10-27 (owner: AWS, max $100/month for infrastructure, not Hetzner, "as cheaply as
possible", London). Prices re-measured in 0.1 and recorded in [infra/README.md](../../infra/README.md).

## Decision

1. **Build VM `argonia-build`**: `m7i.xlarge` (4 vCPU, 16 GiB, x86), Ubuntu 24.04, 120 GiB gp3, **persistent
   spot, stop on interruption**, no inbound rules. The owner works in **VS Code in the browser**
   (vscode.dev through a `code tunnel` service named `argonia-build`, GitHub sign-in); **SSM Session Manager**
   in the AWS console is the break-glass shell. Nothing is installed on the Mac. Claude Code runs in the
   tunnel's terminal inside `tmux`. x86 is required: Wine (xEdit,
   PapyrusCompiler, msvc-wine, BSArch, xLODGen, DSAnimStudio) does not run on Graviton.
2. **GPU box `argonia-play`**: created in 0.2 from a script in `infra/`; g6.xlarge (L4) spot by default, g4dn
   (T4) for light agent runs if the benchmark allows, in the same VPC/AZ as the build VM. Stopped when idle
   (15 min). It holds Skyrim, the pinned dependency mods, Proton, the agent bridge, Selkies and saves.
3. **Control from Claude Code**: AWS CLI under an IAM role scoped to start/stop/describe instances tagged
   `project=argonia` and read/write one S3 bucket; optionally the AWS MCP server with the same role. The GPU
   box is reached from the build VM over the private VPC address (security group: build VM → GPU box on SSH
   and the bridge port only).
4. **RunPod is not used for play** (no inbound UDP: WebRTC fails). Vast.ai is the documented fallback GPU host.
   Hetzner is excluded.
5. **Budget guard**: an AWS Budget at $100 with alerts at 50/80/100% actual and 100% forecast (the owner's setup step 1).
   The planner reads month-to-date cost weekly (Cost Explorer via CLI) and reports it in the owner check-in.

## Monthly estimate (London, 2026-10-27 prices, re-measure in 0.1)

| Item | Assumption | $/month |
|---|---|---|
| Build VM m7i.xlarge spot | ~$0.08/h, idle-stopped when no agent runs (5x plan ≈ 120 h/week ≈ 520 h/month) | ~42 (58 if always on) |
| Build VM disk | 120 GiB gp3 | ~11 |
| GPU box, agent test runs | g4dn ~$0.19/h or g6 ~$0.36/h × ~43 h | ~8–16 |
| GPU box, owner play | g6 ~$0.36/h × ~43 h (10 h/week) | ~16 |
| GPU box disk | ~150 GiB (Skyrim + dependency mods + Proton) | ~14 |
| Egress (streaming) | ~150 GB, first 100 GB free | ~5 |
| Public IPv4 | while attached | ~4 |
| S3 (saves, small backups) | <10 GB | <1 |
| **Total** | | **~$95–110** |

This is at the limit. **The $100 is a hard cap for AWS infrastructure only** (owner rule). The Claude
subscription is separate (decision 0013); Fal usage is separate and small (the old project's UI art cost about
$0.15 per generated image) and is reported in check-ins. **Levers, in order:** idle-stop the build VM when no agent session runs (biggest);
shrink the GPU disk by keeping only the pinned files; use g4dn for agent runs; release the old
elder-souls-argonia machine's 250 GiB disk (~$23/month while stopped, outside this table: owner call O-1);
move to `m7i.large` for the build VM during low-parallelism parts.

## Per-part cost budget (AWS, on top of the steady state above)

| Part | Extra items | Budget |
|---|---|---|
| 0 | GPU benchmark hours on three instance types (~15 h); a temporary Windows spot instance only if G1/G4/G6 need it (~10 h); the owner's streaming test; installer from-scratch runs (~10 GPU hours) | ≤ $35 |
| 1 | the core-loop soak (~3 GPU hours); L4 batches otherwise inside the steady state | ≤ $5 |
| 2 | a 64 GiB spot instance for LOD generation (~6 h per full build; e.g. r7i.2xlarge/m7i.4xlarge spot) and navmesh/vegetation L4 sweeps (world track); systems-track L4 batches inside the steady state; the owner's playthrough counted as play | ≤ $20 |
| 3 | a temporary Windows spot instance for install and release tests (~10 h) | ≤ $10 |
| 4 | immersion booth batches at 4.1 (~20 GPU hours on g4dn, ≤ $10); per region: L4 sweeps (~10 GPU hours) and one LOD rebuild at region close (~6 h big instance), ≤ $10 per region | as listed |

**Stop-and-ask rule (T-COST):** the planner projects the month's AWS total weekly (month-to-date plus planned
hours at current spot prices). If the projection exceeds $100, it stops starting new paid work, applies the
levers above, and if that is not enough asks the owner (raise the cap for the month, or slow down). A part's
extra budget overrunning by 50% also triggers a check-in.

## Consequences

- No local GPU for the build VM: every in-game test is a GPU-box job (testing level L4+), batched.
- The Claude subscription is separate from this budget (decision 0013).
