# Machine moves lose nothing

The owner, 2026-10-31: the xLODGen distant terrain made on the g4dn existed only in that machine's MO2 folder,
and went when the machine was terminated in the move to the g6. "We may have to move machines again in future.
We must lose nothing in such moves."

## The rule

Nothing lives only on a machine. Anything a machine makes that the repo cannot rebuild in minutes is written to the
private bucket by the job that makes it, when it is made. For the play machine that is: the saves (`saves-sync.ps1`
to the saves bucket every 5 minutes and on a spot notice) and the mod archives (`stack.py` caches every archive it
fetches in the bucket's `mods/`). Everything else on it (Steam's install, MO2's layout, Pandora's output, our
plugin) is remade by `create.sh`, `setup.ps1`, `stack.py install` and `deploy.sh`. On 2026-11-05 the play machine
was terminated with its disk and nothing the new goal needs was lost, for that reason.

## The build VM's disk

The owner pays for the build VM's disk by its size (120 GB gp3, about $11 a month), so it must never need to grow.
`tooling/disk.sh report` shows what fills it, by kind; `tooling/disk.sh tidy` frees what the bucket can give back:

- **Mod archives** (`~/.argonia/mods`, 16 GB): `stack.py evict` deletes each local archive once the bucket's
  `mods/` holds it with the manifest's hash; `stack.py fetch` takes it back from the bucket in minutes.

Kept on purpose: the staged mods (`~/.argonia/stack/MO2`, what stack push sends) and the owner's Skyrim SE install
(`~/games/skyrimse`, read for vanilla records).

## Interrupts: the job queue survives a reboot

The build VM is a spot instance (reclaimed twelve times on 2026-11-02) and comes back within minutes. Every
`job_guard.sh run` spools what a relaunch needs under `~/.argonia/jobs` (on the root EBS volume, so it survives the
reboot): `<name>.cmd` (argv, NUL-separated), `.cwd`, `.env` (ARGONIA_* and PATH), `.seq` (launch order), `.gpu`
(the game machine whose lock it takes) and `.state` (queued, running, done, stopped). At boot the systemd --user unit
`argonia-job-resume.service` (lingering is on for ubuntu, so it starts without a login; laid once by
`tooling/job_resume.sh --install`) runs `tooling/job_resume.sh`, which relaunches in `.seq` order, through the
normal `job_guard.sh run` path (same locks and queue, same cwd, env and argv, same seq), every job whose state is
queued or running, whose `.rc` is absent or a signal's (>= 128; `stop` marks a job stopped, so it stays stopped) and
whose unit is not alive. It writes `RESUMED-<boot-id>` with what it relaunched; the planner reads that instead of
re-queueing. A job finished before the interrupt is not rerun; the interrupted run's log is kept as `<name>.log.interrupted`.
Jobs on one machine take its lock in `.seq` order, so the queue's order holds.

**What a job must be.** A relaunched job starts again from its first line, so every job must be idempotent: a rerun
skips the steps that finished (step markers, checkpoints) and only waits where the wait is already satisfied.
Already so: `tooling/lod.sh run` (per-step markers per ArgoniaWorld sha), the terrain build (resumes from an
interrupted `land.tmp-*` with equal inputs, 3a36981), `~/.argonia/scripts/up_until.sh` (bringing a machine up twice
is harmless), the chains in `~/.argonia/scripts/` built on it. A job that is not (one that appends, pushes or sends
on every run) must check for its own output first, or not be run under job_guard.
