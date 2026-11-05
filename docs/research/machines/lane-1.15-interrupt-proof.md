# Lane 1.15 interrupt-proof: report

Branch `lane-interrupt-proof` (b57b117). Not merged; the unit is not laid (the planner does both at a quiet moment).

- **Spool** (`job_guard.sh run`, under `${JOBS_DIR:-~/.argonia/jobs}`): `.cmd` (argv, NUL-separated), `.cwd`,
  `.env` (ARGONIA_*, PATH; NUL-separated), `.seq` (global counter under `.seq.lock`; `JOB_SEQ` keeps a resumed job's
  place), `.gpu` (machine), `.state` queued|running|done|stopped. A signal rc (>= 128) leaves the state running.
- **Restore rule** (`tooling/job_resume.sh`): in `.seq` order, every job with state queued|running, `.rc` absent or
  >= 128, unit not active (bare pid when no unit), state touched within `RESUME_MAX_AGE` (12 h), relaunched through
  `job_guard.sh run` with its cwd, env, argv, `--gpu=<machine>` and seq; old log kept as `.log.interrupted`;
  writes `RESUMED-<boot-id>`; once per boot.
- **Lock order**: a new internal `_turn` makes a gpu job wait while an earlier-seq job on its machine is still queued
  (flock alone wakes waiters in any order).
- **systemd check**: `launch` now accepts `is-system-running` = starting/initializing, so jobs launched during boot
  get their own transient unit rather than dying with the oneshot.
- **Unit**: `tooling/job_resume.sh --install` writes `~/.config/systemd/user/argonia-job-resume.service`
  (Type=oneshot, WantedBy=default.target, ExecStart=<tree>/tooling/job_resume.sh) and enables it. Linger=yes.
- **Tests**: `tooling/tests/test_job_resume.py` (spool write; SIGKILL-all interrupt then resume: order run1,q2,q3,n4,
  finished job not rerun, signal-rc job rerun, env/cwd kept, second run a no-op) + `test_job_guard.py`: 9 passed, 70 s.
- **Measured**: resume script to first relaunch 0.086 s (3 gpu jobs in 0.21 s), simulated with SIGKILL of the units.
  A real reboot's time to first relaunch is not measured: the planner's jobs were running on this VM.
- **Not done (outside Paths)**: the SessionStart hook in `.claude/settings.json` should print the newest
  `~/.argonia/jobs/RESUMED-*`.
