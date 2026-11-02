# Machine moves lose nothing

The owner, 2026-10-31: the xLODGen distant terrain made on the g4dn existed only in that machine's MO2 folder,
and went when the machine was terminated in the move to the g6. "We may have to move machines again in future.
We must lose nothing in such moves."

## The rule (CLAUDE.md)

Nothing lives only on a machine. Anything a game machine makes that the repo can't rebuild in minutes is archived
to the private bucket when it is made, by the job that makes it. No machine is stopped for good, terminated,
re-imaged or replaced until `infra/gpu-box/machine_inventory.sh --machine <name>` reports nothing unarchived.

## What the inventory checks

`infra/gpu-box/machine_inventory.sh --machine <name>` is read-only: one `Get-ChildItem` listing over `run.sh ps`,
then S3 listings on the build VM. The raw listing is kept in `out/inventory/<name>.tsv` (`--replay` classifies it
again). It prints each thing only that machine has, with `archived` or `UNARCHIVED`, and exits 1 while anything is
UNARCHIVED.

| Kind | What is listed | Archived when |
|---|---|---|
| mod | an MO2 mod folder named in neither `data/dependencies.json` nor `combat-test-mods.json` (their archives are in the private bucket's `mods/`) and not built by deploy (Argonia SKSE, SkyLink (dev, rebuilt)) | for "Argonia LOD (generated)": the private bucket's `lod/` holds a tar of its size (`lod.sh archive`, run by the job that makes it); any other mod: add it to the manifest |
| save | a save that isn't ours (not argoniabase\*, ArgoniaRest, ArgoniaSuspend, quick- or autosave) | the machine's `saves.sh backup` latest.zip (or the legacy `saves/latest.zip`) has it at the same size; `run.sh stop` runs the backup |
| ck | a Creation Kit or records-job output in `C:\argonia\records\out` other than the Papyrus compile (deploy rebuilds that) | the build VM's `out/gpu` holds a file of that name and size (fetched back) |
| state | a `C:\argonia` folder that deploy, setup.ps1 or our tools don't make | never by itself: archive it, make it a `setup.ps1` step, or record why it isn't needed |
| scratch | a loose `C:\argonia` file (an agent's one-off script) | not counted; deleted or kept with the image |

Hand-made machine setup (a driver bind, firewall rules, a scheduled task) can't be seen by a listing: it is a step in
`setup.ps1`, never only a manual fix. Things the repo rebuilds in minutes (the plugin, the SKSE DLLs, Papyrus,
scenes, the base save, the manifest's mods) are not listed; `deploy.sh` and `stack.py push` make them again.

## A move, in order

1. Run `machine_inventory.sh` on the old machine. Archive anything it lists as UNARCHIVED, or record why it isn't
   needed in the move's lane report.
2. Make the new machine from the newest image, deploy, and restore the archives (`lod.sh restore`, saves).
3. Prove the owner's path on the new machine (the card, our ESMs loaded, a still).
4. Run the inventory on the old machine once more, then retire it. Its image goes only after the new machine has
   run for a day.

## The build VM's disk

The owner pays for the build VM's disk by its size (120 GB gp3, about $11 a month), so it must never need to grow.
`tooling/disk.sh report` shows what fills it, by kind; `tooling/disk.sh tidy` frees what the bucket can give back:

- **Lane worktrees** (`~/wt-*`, one per agent lane, about 0.6 GB each): one idle for 3 hours (no process inside,
  nothing changed) is archived to `s3://argonia-private-…/worktrees/<name>/` and removed. The archive holds its
  `out/` (run dirs, batches, stills; built plugins excepted), its untracked files, any uncommitted edits and a bundle
  of any commits not on origin/main. Evidence a doc cites as `wt-<name>/out/…` is at that prefix, same path.
  `tooling/worktree.sh` runs the tidy before it makes each new lane (`NO_TIDY=1` skips it).
- **Mod archives** (`~/.argonia/mods`, 16 GB): `stack.py evict` deletes each local archive once the bucket's
  `mods/` holds it with the manifest's hash; `stack.py fetch` takes it back from the bucket in minutes.

Kept on purpose: the staged mods (`~/.argonia/stack/MO2`; stack push and the UI theme build read them), the owned
games (`~/games`: Skyrim SE data for ArgoniaGen, DSR for measuring), the main tree's `out/`.

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
