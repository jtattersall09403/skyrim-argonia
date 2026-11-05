# Lane 1.15-r6-gate-parallel: the reach gate runs its parts concurrently

`tooling/check_reach.py` ran the reached `make <part>` one after another (chain logs: unit 181-190 s, plugin-check 137 s, skse 23 s).
It now runs them in a bounded pool (`--jobs N`, default 3), heavy parts first (unit, plugin-check, skse), each part's output captured
and printed whole in PARTS order, per-part seconds and the wall time printed, red if any part is red. `--jobs 1` is the serial run.
Shared paths: only plugin-check takes `out/.plugin.lock`; no other reached part does, so none shares a worker. `make check` already ran all parts with `-j`.
The whole-gate path (unmapped path or Makefile change) still hands over to `make check`.
Measured, build VM, shared tree, same range: serial parts 108+101+2 s (unit, plugin-check, skse); --jobs 3 wall 120 s; whole run 232 s serial vs 179 s with --jobs 3 (other lanes edited the tree mid-run).
