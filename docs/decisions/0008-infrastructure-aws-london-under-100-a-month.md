# 0008: Infrastructure: AWS, an on-demand build VM run a few hours a day, a spot GPU play machine, under $100 a month

**Status:** decided 2026-10-27 (owner: AWS, max $100/month for infrastructure, "as cheaply as possible");
corrected by the owner on 2026-11-05: the build VM is **on demand**, the play machine stays **spot**.
The $100 cap binds from November 2026 (October was the old project's spend).

## Decision

1. **Build VM `argonia-build`** (London, eu-west-2): `m7i-flex.xlarge` (4 vCPU, 16 GiB, x86), Ubuntu 24.04,
   120 GiB gp3, **on demand** (the owner recreated it so on 2026-11-05 after spot reclaims cost whole builds).
   Because it is on demand it **runs only while an agent is working, about 8 to 10 hours a day**: the idle-stop
   timer (`infra/build-vm/idle-stop.sh`, 20 minutes with no Claude session, no job and no tunnel client) stops
   it, `tooling/agent_stop.sh` stops it when the agent is done, and an owner comment starts it again
   (`.github/workflows/wake.yml`). An agent never leaves it running idle overnight. The owner works in VS Code in
   the browser (a `code tunnel` named `argonia-build`); SSM Session Manager is the break-glass shell.
2. **Play machine `argonia-play`**: a **g6.xlarge** (L4, comfortably strong enough) **persistent spot** instance,
   Windows Server 2022, stopped when idle (15 minutes) and started by the play page. It has run in Paris
   (eu-west-3) since 2026-10-31. **The region is whichever European region is expected to interrupt a g6.xlarge
   least at a similar price** (the spot placement score and the interruption band on the Spot Instance Advisor,
   measured when the machine is created or moved; London and Paris are the usual two). The machine was terminated
   with its disk on 2026-11-05 and is recreated in PLAN Phase 0; the region is chosen then by that measure.
3. **Control from Claude Code**: the AWS CLI under the build VM's IAM role (start/stop/describe instances tagged
   `project=argonia`, the two S3 buckets); the play machine is reached over SSH on its public address, open only to
   the build VM.
4. **Nothing lives only on a machine** ([machine-moves.md](../machine-moves.md)): saves and mod archives are in
   S3; everything else is rebuilt from the scripts.

## Monthly estimate (2026-11-05)

| Item | Assumption | $/month |
|---|---|---|
| Build VM m7i-flex.xlarge on demand | ~$0.19/h × 9 h/day × 30 | ~51 |
| Build VM disk | 120 GiB gp3 | ~11 |
| Play machine g6.xlarge spot | ~$0.35–0.45/h × ~50 h (owner play and the odd agent check) | ~20 |
| Play machine disk | ~150 GiB gp3 | ~14 |
| Egress (streaming), public IPv4, S3 | | ~8 |
| **Total** | | **~$100** |

At the limit. **Levers, in order:** keep the build VM's running hours down (stop when idle, batch agent work
into sessions); keep the play machine stopped between sessions; shrink its disk to the pinned mods; a smaller
build VM for light phases.

**Stop-and-ask rule:** each check-in reports month-to-date; if the projection passes $100 the agent stops starting
paid work, applies the levers, and only then asks the owner (raise the cap for the month, or slow down).

## Consequences

- The build VM's hours are a budget: agents work in sessions and stop the machine; long jobs are scheduled inside
  those hours, and a job that can run on the play machine while the owner is not playing may run there.
- Spot reclaims still hit the play machine, so every job on it, and every agent's work, stays interrupt-proof
  ([0037](0037-work-is-interrupt-proof.md)).
