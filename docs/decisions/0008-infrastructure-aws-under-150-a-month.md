# 0008: Infrastructure: AWS, an on-demand build VM run 8 to 10 hours a day, an on-demand GPU play machine, under $150 a month

**Status:** decided 2026-10-27 (owner: AWS, "as cheaply as possible"). The limit is $150 a month (owner, 2026-11-10)
and $200 for November 2026 alone (owner, 2026-11-18).

## Decision

1. **Build VM `argonia-build`** (London, eu-west-2): `m7i-flex.xlarge` (4 vCPU, 16 GiB, x86), Ubuntu 24.04,
   120 GiB gp3, **on demand** (spot reclaims cost whole builds). Because it is on demand it **runs only while an
   agent is working, about 8 to 10 hours a day**: the idle-stop timer (`infra/build-vm/idle-stop.sh`, 20 minutes
   with no Claude session, no job and no tunnel client) stops it, `tooling/agent_stop.sh` stops it when the agent
   is done, and an owner comment or a studio visit starts it again. An agent never leaves it running idle. The
   owner works in VS Code in the browser (a `code tunnel` named `argonia-build`); SSM Session Manager is the
   break-glass shell.
2. **Play machine `argonia-play`**: a g4dn.xlarge on demand in Paris, Windows Server 2022, stopping itself when
   idle ([0039](0039-the-play-machine-is-a-g4dn-on-demand.md)).
3. **Control from Claude Code**: the AWS CLI under the build VM's IAM role (start, stop and describe instances
   tagged `project=argonia`, the two S3 buckets); the play machine is reached over SSH on its public address, open
   only to the build VM.
4. **Nothing lives only on a machine** ([machine-moves.md](../machine-moves.md)): saves and mod archives are in
   S3; everything else is rebuilt from the scripts.

## Monthly estimate

| Item | Assumption | $/month |
|---|---|---|
| Build VM m7i-flex.xlarge on demand | about $0.19/h x 9 h/day x 30 | about 51 |
| Build VM disk | 120 GiB gp3 | about 11 |
| Play machine g4dn.xlarge on demand | about $0.80/h x about 50 h (owner play and the odd agent check) | about 40 |
| Play machine disk | about 150 GiB gp3 | about 14 |
| Egress (streaming), public IPv4, S3 | | about 8 |
| **Total** | | **about $120 at 50 play hours** |

**Levers, in order:** keep the build VM's running hours down (stop when idle, batch agent work into sessions); keep
the play machine stopped between sessions; shrink its disk to the pinned mods; a smaller build VM for light work.

**Stop-and-ask rule:** each check-in reports month-to-date; if the projection passes the limit the agent stops
starting paid work, applies the levers, and only then asks the owner (raise the limit for the month, or slow down).

## Consequences

- The build VM's hours are a budget: agents work in sessions and stop the machine; long jobs are scheduled inside
  those hours, and a job that can run on the play machine while the owner is not playing may run there.
- Every job on either machine, and every agent's work, stays interrupt-proof
  ([0037](0037-work-is-interrupt-proof.md)).
