# 0037 — Work is interrupt-proof: every long job resumes from exactly where it got to

**Date:** 2026-11-03 · **Status:** accepted (owner rulings on #38, 16:02, 16:04 and 16:14; a binding CLAUDE.md line; binds every job, tool and method)

## Decision

1. **The machines are spot and stay spot.** The build VM and the game machines are reclaimed without warning (thirteen
   times on 2026-11-03) and come back within minutes. No on-demand instance is bought to avoid it (owner: "I cannot
   afford on demand").
2. **An interruption may cost only the gap itself.** Every long job is a sequence of steps whose verdicts are
   checkpointed as they pass, keyed by the step's inputs (never by the repository commit), and a rerun skips every
   step already done for the same inputs: the pre-batch (`infra/gpu-box/jobs/r5_prebatch.sh`), the round
   (`infra/gpu-box/round.sh`: one deploy per build, the batch continuing from the first journey not reached), the LOD
   (`infra/gpu-box/lod.sh`: a marker per step on the play machine; a tool still running when the driver comes back
   is attached and waited for, never restarted). Jobs relaunch at boot from their spool (`tooling/job_resume.sh`);
   lanes resume from their transcripts, their worktrees keep uncommitted files, and they commit each proven step.
3. **Every agent plans its own work this way** (owner, 16:14): it expects frequent interruptions, and any pre-existing tool or
   method it finds that is not interrupt-proof it makes so before using it again.
4. **A step that cannot checkpoint is split until it can**, or it runs on the machine that survives (the LOD tools run
   on the play machine; the build VM only drives them).

## Why

Round 5 (2026-11-03): each reboot of the build VM restarted the round's pre-batch from the top (fifteen minutes) and
lost a running DynDOLOD (thirty-five minutes); the close of the round slipped three hours. The owner's bar: nothing is
lost but the interrupt gap, and the work is picked up from exactly where it was.

## Consequences

- A job's resume key names its inputs; any key that includes `git rev-parse HEAD` is a defect (the round's, 2026-11-03,
  to be narrowed to the built world and the stack).
- `job_guard.sh status` and the lane log say for every job where it will resume from.
- Owner-facing: the hand-over's "machine time" is the sum of the steps, not of the restarts.

## Amendment, 2026-11-03 (owner, 22:20, #37): a chain's verdict is its output, and its end wakes the agent

Round 5's close-8 lost 90 minutes: xLODGen had written the whole terrain LOD, the driver's one read of the tool's
window came back unreadable, the step was called failed, the machine stopped, and nothing woke the agent until the
owner asked. The owner: prevent anything of that shape. So, for every long chain:

- A step's verdict comes from its output on disk (files written, stable, helpers gone), never from a single read of a
  window or a log line; the window text is a progress signal and is re-read until it is there.
- Finished work is never discarded by a driver's doubt: the step marker is written when the output is proven, and a rerun
  accepts proven output instead of remaking it.
- Every end of a chain, good or bad, calls `infra/build-vm/agent-wake.sh`; the build VM's two-minute wake timer treats
  that line as it treats an owner comment, and the session that launched the chain also watches its log. A chain that
  can stop silently is a defect in the chain.
