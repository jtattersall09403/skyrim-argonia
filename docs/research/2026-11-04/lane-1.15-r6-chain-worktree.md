# Lane 1.15-r6-chain-worktree: the round chain runs on a committed tree of its own

Status: done (L1, L2). Brief: [briefs/1.15-r6-chain-worktree.md](briefs/1.15-r6-chain-worktree.md).

## What changed
- `infra/gpu-box/jobs/chain.sh`: on launch it takes the launch commit (`CHAIN_SHA`, else the resume key
  `~/.argonia/round/chain.<batch>.sha`, else the main tree's HEAD), makes or resets the detached worktree
  `~/.argonia/round/tree` (`git worktree add --detach`; `checkout -f --detach` + `clean -fd` only when the tree's HEAD
  does not descend from the sha, so a resume keeps the pre-batch's own commits), links `out/` and the ignored build
  inputs under data/world/plugin (`data/immersion/inventory.jsonl`, which the plugin's whole-build key hashes) to the
  main tree's, adds `/out` to the shared `info/exclude` (`.gitignore`'s `out/` matches directories only, not a link),
  then re-executes the worktree's own chain.sh with `ARGONIA_REPO` set. The resume key is dropped on a good end.
  `CHAIN_DRY=1` prints `CHAIN tree <path> sha <sha>` and builds nothing.
- `r5_prebatch.sh`, `r5_saves.sh`: repo root from `$ARGONIA_REPO` or their own location. The pre-batch rebases onto
  `origin/main` only when it is ahead (the worktree is clean, so it cannot be refused by a lane's edit) and pushes
  `HEAD:main`; the lanes' tree takes the commits on its next pull. The old `push || pull && push` precedence bug is gone.
- round.sh, deploy.sh, lod.sh, run.sh, run_batch.py, run_journey.py, the Makefile already resolved the root from their
  own location; job_guard records the launch cwd only (the chain moves itself). `grep /home/ubuntu/skyrim-argonia`
  over Paths: none.

## Measured
- `tooling/tests/test_chain_tree.py` (2 tests) with `test_round.py`: 7 passed in 1.10 s. It proves a lane's
  uncommitted edit made before launch is invisible to the chain, the stages run in the worktree with `out` linked to
  the main tree's, the worktree stays clean, the record is appended in the main tree, and the dry run prints tree and sha.
- Real tree: `worktree add` + links 0.58 s; two resets 0.70 s (0.35 s each). In the worktree `make plugin PLAN=1`
  reports every keyed stage skip and `whole build skip key a8cd81be58fa`, the same key as the main tree. Without the
  `inventory.jsonl` link the whole-build key differed (3dcf7a2e3c17): that is why ignored inputs are linked.
- The worktree's `tools/ArgoniaGen/bin`/`obj` are its own: the first `dotnet build` there is a one-time cost (the tree
  persists across rounds); not measured, since a real build was out of scope.

## What still reads the main tree
- `out/` and the linked ignored inputs (by design); the round record (`$2`, appended there for the planner to commit).
- `batch.yaml` and every journey/scene are read from the committed tree: a batch file must be committed before launch.
- job_guard's recorded cwd (the launch dir) and `~/.argonia/scripts`, the venv, AWS state: outside the repo.
- A local main commit that is not pushed is included (it is in HEAD) and reaches origin with the pre-batch's push.
