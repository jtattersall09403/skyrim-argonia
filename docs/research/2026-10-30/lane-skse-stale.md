# lane skse-stale

Cause: the tar keeps file times; a source edited on the build VM can be older than the .obj Ninja built earlier on
Windows, so Ninja skips it and the link fails (LNK2019 set_skill, setskill-build3).

Fix (on the build VM, so it is testable on Linux; skse_build.ps1 is unchanged): `infra/gpu-box/skse_manifest.py`
keeps a manifest (path, SHA-256) in `~/.argonia/skse-manifest.<machine>.<preset>`. Before tarring, files whose hash
differs or is new get mtime=now; unchanged files keep their time. The manifest is saved only after SKSE-BUILD OK, so
a failed build leaves its edits to be touched again; deleted files drop out on save.

Source mode (planner add-on): default is `git archive HEAD skse` (committed only), so another lane's half-done edits
no longer break your build (the first run here failed on world-fixes' ep_world.cpp). `--worktree` tars the working
tree as before; `deploy.sh` passes it. In committed mode every file is set to a fixed old time first (git archive
stamps the commit time, which a new commit would make newer than every .obj and force a full rebuild; seen once).
Lane convention: commit, or use `--worktree` knowingly, then build.

Proof:
- `tooling/tests/test_skse_manifest.py` (1 test: new and edited-with-old-time files touched, unchanged keep time, a
  failed build does not save, deleted files drop out): passes.
- On argonia-play (no-deploy): a comment appended to skse/core/src/seam.cpp (committed in a scratch worktree, mtime
  2020) gave "1 of 165 files changed"; Ninja ran 36 steps: seam.cpp.obj, argonia_core.lib, 33 relinks of the
  dependants (30 core tests, ArgoniaCore.dll, ArgoniaBridge.dll), no other compile; ctest 33/33. Before the fixed-time
  line a new commit rebuilt all 126 steps.
