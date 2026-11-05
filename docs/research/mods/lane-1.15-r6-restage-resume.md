# 1.15 r6: the BM&V restage resumes (decision 0037)

## Where the restage runs (the brief assumed the machine side)
`deploy.sh` runs `stack.py stage` then `stack.py push`. The unpack of BM&V is on the BUILD VM (stage): tar of the 9.2 GB
vault part, then `unrar` of Data1.rar and Data2.rar into 21 GB, then prune. The machine side is only join-and-untar of
pushed parts. The reclaims cut the build-VM stage (r6-chain33 was in "== stack stage" both times), so that is what is fixed.

## Measured (deploy logs, step times)
- stage with bmv: 446 s (deploy-r1, r2c), 377 s (r3r), 441 s (r5-close8), 466 s (round-r4): about 6-8 min, restarted from zero.
- push with bmv: 185-207 s (r1, r2c, r3r, round-r4), 329 s (d112), 394 s (watch-new3), 545 s (r6-chain17), 42 s (r5-close8, partial).
- Together 10-15 min against a reclaim every 6-30 min: the stage or the push was cut before it finished, again and again.

## What changed (infra/gpu-box/stack.py)
1. `Resume` + `stage_nested`: a nested row (bmv) marks each step (`unpack`, `rar:Data1.rar`, `rar:Data2.rar`) in
   `~/.argonia/stack/progress/<id>.json`, keyed by the row's stage key, written atomically. A rerun skips done steps, redoes
   a cut step over its partial files (`unrar -o+`), and clears the partial copy when the key changed or no mark exists.
   The marker is removed when the row's staged stamp is written.
2. `send_tar`: a part put and size-checked on the machine leaves a marker under `push/parts/<mod>-<digest>/`. A rerun cuts
   the same parts (the tar of an unchanged folder is the same bytes) and uploads only unmarked ones; machine parts that
   are cut short or from other content are removed first (the join would take them).
3. Tests: `tools/tests/test_stack_resume.py` (kill at Data2 resumes at Data2; changed key starts clean; cut mark write;
   part markers vs machine sizes; send_tar resends only the lost part, with a fake machine, no AWS).

## Not done
- The machine-side join/untar is not detached (a scheduled task): untestable without the game machine, which the chain
  holds. It is minutes after the upload and restarts cheaply (parts stay until joined). Follow-up when the machine is free.
- A cut `unrar` redoes its whole rar (Data2 is 8 GB): unrar of a solid archive cannot resume inside.
