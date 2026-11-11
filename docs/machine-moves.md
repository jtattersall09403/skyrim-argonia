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
`tooling/disk.sh report` shows what fills it, by kind. Kept on purpose: the staged mods (`~/.argonia/stack`, what
stack push sends), the owner's Skyrim SE install (`~/games/skyrimse`, read for vanilla records) and the main tree's
`out/` (the current build).

## Tidying is automatic

`tooling/disk.sh tidy` is the one tidy of the disk, the lane worktrees and the bucket (the rules are
`tooling/tidy.py`). It deletes and never archives, is safe to interrupt and to run twice, and removes a thing only
when a named rule proves nothing needs it. `tidy --dry-run` prints exactly what would go and why, and what is kept
and by which reference. Nobody has to ask for it; it runs:

| When | Where it is wired | What runs |
|---|---|---|
| Every session start | the SessionStart hook in `.claude/settings.json` | all of it, quietly; the bucket once a day |
| A deliberate stop | `tooling/agent_stop.sh`, before the marker | all of it |
| A lane lands | `tooling/lane_land.sh <worktree>` | that lane's worktree and branch |
| Free disk under 15 GB | `tooling/job_guard.sh run`, before the job starts | worktrees and disk, never the bucket |

**Lane worktrees.** A lane worktree goes, with its branch, when nothing works in it (its session's lock is dead, no
process stands in it, no job was started from it), nothing in it changed for 3 hours, and all its content is on
`origin/main`. A lane branch whose worktree is already gone goes by the same rule on its tip. Content is compared,
never commit ids: the worktree as it stands (commits, uncommitted edits, untracked files) is merged into main, and
what the merge would not change is landed. A file the merge would change is still landed when main's history since
the fork held the lane's version or took its change and then moved on, when every run of words the lane added
stood in the file on main at some point, or when it lies in a generated tree (`plugin/Argonia`, the records list,
the story database) that main regenerated after the lane last wrote in it. Place files are hand-edited and never
count as generated. A worktree or branch with anything else is kept and named with its age, at every session
start; idle for a day it is named as abandoned work, to land or to delete on the lead's decision.

**Disk.** The spool of every job that ended over two days ago (`~/.argonia/jobs`; a queued, running or cut-off job
is never touched), session and tool scratch under `/tmp` untouched for two days, and the cached mod archives the
bucket's `mods/` holds once they pass 1 GB or the disk is under its floor (`stack.py evict` checks each against the
manifest's hash first; `stack.py fetch` takes it back in minutes).

**Bucket** (`s3://argonia-private-050977237313`). Things are deleted only under `nw/terrain/`, `nw/plugin/` and
`nw/lod/`, and there only a build that no reference names, that is not the newest, and that is over a day old.
The references: the current terrain build (`out/newworld/terrain/build.json`); every terrain build a built place's
held ground names (`newworld/sources/terrain_held.json`); the current world file (`out/newworld/plugin`); the world
file on the play machine (the newest uploaded up to the time `lod.sh send` recorded in
`out/newworld/verify/play-esm.sha256`); the LOD on the play machine (the key whose `dyndolod` step marker under
`~/.argonia/lod-steps` is newest); any build id a tracked `.json` file names. The first three are read from the
main tree and from every lane worktree. `mods/` (the mod cache) and every other prefix are listed and never touched.

### Why worktrees were orphaned, and what prevents each

| Mechanism | What prevents it now |
|---|---|
| Nothing removed a lane's worktree when the lane ended: the Agent tool keeps a worktree that has changes, and landing was a hand rebase and push that stopped there. | `lane_land.sh` lands and removes in one command; the tidy removes any that is missed. |
| A landed branch looked unlanded: the rebase gave its commits new ids, so `git cherry`, `git branch -d` and an ancestry test all said "not on main", and nobody dared delete it. | The tidy and `lane_land.sh` compare content, never ids (`disk.sh landed <worktree>`). |
| Lanes ended with uncommitted generated files (the record YAML and the records list a build rewrites: up to 339 changed and 259 untracked files in one worktree), so every old worktree looked like unfinished work. | Generated trees count as landed once main regenerated them; a lane leaves its worktree clean and committed before it returns (CLAUDE.md, the delivery agents' rules). |
| The tidy ran only when someone asked, and archived to the bucket, which the owner's rule "delete, never archive" had since ruled out; so it was not run. | It deletes, and runs from the four triggers above. |
| A session that died left its worktree locked. | A lock counts only while the process it names is alive. |

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
