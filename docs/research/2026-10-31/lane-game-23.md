# Lane game-23: hand-off (stopped by the planner, 2026-10-31)

- Stopped before any check ran: the owner is replanning the remaining work into one-session chunks.
- argonia-play-2 was NOT created (no instance in eu-west-2 by that name); machines.conf is unchanged.
- Found: clone.sh looks up its source in eu-west-2, and argonia-play is now in Paris, so `--from argonia-play` fails.
- Fix pushed: `clone.sh --image ami-...` takes a named London image (ami-0b28d03211e7d92d2, tagged argonia-image=argonia-play). Syntax-checked only (bash -n); it has not been run.
- To resume: add `argonia-play-2 eu-west-2 private` to machines.conf, then
  `tooling/job_guard.sh run --gpu=argonia-play-2 clone-play-2 -- infra/gpu-box/clone.sh --image ami-0b28d03211e7d92d2 argonia-play-2 g6.xlarge eu-west-2a`,
  deploy.sh, then the Paris first-boot fixes (pnputil oem81.inf; NewNetworkWindowOff). clone.sh already disables cloudflared.
- None of the 38 owed ledger rows (ledger-audit.md) changed; no journeys or scenes were written.
