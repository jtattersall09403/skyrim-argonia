# r6-chain32 deploy pre-flight refusal (lane 1.15-r6-clone-disk)

Finding: the pre-flight (infra/gpu-box/deploy.sh:78, stack.cmd_plan + stack.room) measures the BUILD VM's disk
(`shutil.disk_usage(HOME)`), not the clone's. The clone was never involved and was not started.

1. Why bmv restages: not a lost marker or a deleted pack. `~/.argonia/stack/staged/bmv.json` (written 2026-11-04 10:32)
   holds the old stage key; `data/dependencies.json` bmv row changed since (commit 3a6800ca 2026-11-05 04:42, "BM&V keep
   list gains the mesh the rescaled canopy uses"; be1fffd6 05:36 removed gorse), so `stage_key` differs and the row is
   rightly restaged (a keep-list change needs the 9 GB vault tar unpacked again, 3x = 28.96 GB). MO2/mods/bmv (191 MB) is
   intact. "machine holds nothing" in chain29 is the clone's deployed.key, unrelated to the stage.
2. Disk (build VM, 116 GB): 80 GB used, 36 GB free. Big: stack/MO2 11 GB, mods/vault-bmv.tar 9 GB, out/batch 4.7 GB
   (round-6 3.4 GB), .cache/argonia/png 2.4 GB, games 23 GB.
3. Deleted: 304 files in ~/.cache/argonia/png (*.npy decode cache keyed by file bytes, rebuilt on demand by
   tools/argonia_world/terrain/png.py): 2.4 GB. Nothing else touched.
Result: 41.1 GB free; plan needs 28.96 GB; leaves 12.1 GB (>= 10); `stack.room` passes.
Residual: the next keep-list edit of bmv repeats this; the chain's restage is ~15 min and correct, so no detection fix.
