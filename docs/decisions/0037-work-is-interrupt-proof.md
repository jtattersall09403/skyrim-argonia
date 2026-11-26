# 0037: Work is interrupt-proof: every long job resumes from exactly where it got to

**Status:** decided 2026-11-03 (owner rulings on #37, #38 and #39); a binding CLAUDE.md line; binds every job, tool
and method.

## Decision

1. **An interruption may cost only the gap itself.** Machines stop when idle, sessions end, a job is killed, a
   machine is rebooted; none of that may lose work. Every long job is a sequence of steps whose verdicts are
   checkpointed as they pass, keyed by the step's inputs (never by the repository commit), and a rerun skips every
   step already done for the same inputs. The LOD build (`infra/gpu-box/lod.sh`) keeps a marker per step on the
   play machine, and a tool still running when the driver comes back is attached and waited for, never restarted.
   Jobs run under `tooling/job_guard.sh` and relaunch at boot from their spool (`tooling/job_resume.sh`); lanes
   resume from their transcripts, their worktrees keep uncommitted files, and they commit each proven step.
2. **Every agent plans its own work this way**: it expects frequent interruptions, and any tool or method it finds
   that is not interrupt-proof it makes so before using it again. No agent asks whether to pay for a machine to
   avoid interruptions; the rule is to lose nothing.
3. **A step that cannot checkpoint is split until it can**, or it runs on the machine that survives (the LOD
   tools run on the play machine; the build VM only drives them).
4. **A chain's verdict is its output, and its end wakes the agent.**
   - A step's verdict comes from its output on disk (files written, stable, helpers gone), never from a single
     read of a window or a log line; the window text is a progress signal and is re-read until it is there.
   - Finished work is never discarded by a driver's doubt: the step marker is written when the output is proven,
     and a rerun accepts proven output instead of remaking it.
   - Every end of a chain, good or bad, calls `infra/build-vm/agent-wake.sh`, and the session that launched the
     chain also watches its log. A chain that can stop silently is a defect in the chain.
5. **A resumed chain never repeats finished work**: a pre-batch is keyed by its inputs and skipped whole when they
   hold, a deploy is keyed by the build the machine already holds and skipped whole when it matches, and a batch
   resumes at its next open step.

## Why

On 2026-11-03 each reboot of the build VM restarted a pre-batch from the top (fifteen minutes) and lost a running
DynDOLOD (thirty-five minutes); a later chain wrote the whole terrain LOD, one unreadable window read called the
step failed, and nothing woke the agent for ninety minutes. The owner's bar: nothing is lost but the interrupt
gap, and the work is picked up from exactly where it was.

## Consequences

- A job's resume key names its inputs; any key that includes `git rev-parse HEAD` is a defect.
- `job_guard.sh status` and the lane log say for every job where it will resume from.
- Owner-facing: the hand-over's "machine time" is the sum of the steps, not of the restarts.
