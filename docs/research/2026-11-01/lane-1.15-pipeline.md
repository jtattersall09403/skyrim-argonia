# 1.15 lane pipeline: the world step's memory and the FormID step without a world build

Lane 1.15-pipeline, 2026-11-01. It follows [the sample lane's report](lane-1.15-sample.md) §Pipeline: `make plugin` on
the whole province stopped at "plugin: ArgoniaWorld.esm failed / Out of memory".

## The world step's peak, measured

ArgoniaGen `world` was run alone on the existing whole-province terrain output (`out/terrain`: 15,876 LAND cells,
`out/water`), under `systemd-run MemoryMax=8G` with an 8 GB GC heap limit, timed with `/usr/bin/time -v`:

| run | peak RSS | wall time |
|---|---|---|
| world, no navmesh | 2.34 GB | 1:38 |
| world with the province navmesh (what `master_world` runs) | 2.82 GB | 2:05 |
| vegetation splice (`ArgoniaGen vegetation`, ~532k REFRs) | 0.37 GB | 0:05 |

The cause was the GC heap limit and not the scope: `WORLD_ENV` set `DOTNET_GCHeapHardLimit=0x60000000` (1.5 GB, from
an older 1.1 GB measurement), so the managed heap hit its limit long before the 3 GB scope. The vegetation splice
already streams and needs no change.

**Decision: a raised cap, not a streaming write.** Mutagen builds the worldspace (every cell's LAND, water steps and
NAVM) as one object graph and writes it with its group writer. To stream it, ArgoniaGen would need its own
worldspace and cell group writer outside Mutagen, which means rewriting LandWorld.cs, WaterRecords.cs and
NavmeshRecords.cs to save 2.8 GB on a 15 GB VM. `WORLD_ENV` now sets a 4 GB heap and the world step runs under its
own `WORLD_CAP` of `MemoryMax=5G`. That is about 1.8 times the measured peak, and the other steps keep their 3 GB cap
(`tools/ArgoniaGen/pipeline.py`, `WORLD_ENV` and `WORLD_CAP`). If the province grows past about 4 GB, a streaming
writer is the next step.

## FormIDs without the world build

`pipeline.py ids` (`make plugin-ids`) runs `plugin` with `master_world(rebuild=False)`. It reuses
`out/ArgoniaWorld.esm`, builds it only when it is missing, and leaves `out/plugin.stamp` unwritten, so the next
`make plugin` still does the full build. It writes Argonia.esm, plugin/Argonia/ and the FormIDs the allocator adds.
Run on this VM: green in about 4 min, Argonia.esm 802,100 bytes, 2,822 YAML files, 39 new rows in
world/db/formid.jsonl (the weather lane's WTHR, IMGS including `ARG_ImageSpace_montane`, and the WChance globals,
plus the materials lane's 19 ground TXSTs).

That run first stopped on `ValueError: not an Argonia EditorID: 'ArgGroundTxstRiverBottom01'`. The materials lane's
`terrain/texture_sets.py` used the prefix `ArgGroundTxst`, which `formids.EDID` (`^ARG_`) rejects. The prefix is now
`ARG_GroundTxst`.

## `make plugin-check` after it: still red, but not on FormIDs

The FormID table check and the comparison with the committed plugin/Argonia/ pass. Four other reds remain, and none
of them comes from the FormID step:
- links, 35: Argonia.esm's regions name `0C000D`-`0C0013:ArgoniaWorld.esm`, which the stale `out/ArgoniaWorld.esm`
  (copied from the main checkout) does not have. A whole-province `make plugin` (master rebuilt) clears them.
- regenerate: the two ESMs differ in 4 placed refs of cell (-8, 1) (`Worldspaces/ARG_Province/-2, 0/-8, 1/01293E`
  and others): `generate` is not deterministic there.
- the vegetation sample: tree density is red for dunmer-north.northern-transition (1.7 per cell) and
  hist-heartland.flooded-forest (2.7). That belongs to the vegetation and ground lanes.
- the navmesh sample hash: 6a2f8a0ed407 against the manifest's 5eed6ffd1177, after the ground changed. That belongs
  to the ground lane.

## Owed and hazards

- A whole-province `make plugin` has not been rerun with the new cap; the measurement above is the evidence.
- The worktree's `out/terrain` is a symlink to the main checkout's. A `pipeline.py ids` started before
  `out/ArgoniaWorld.esm` was copied into the worktree began a terrain build into it. That build was stopped, but
  it left `~/skyrim-argonia/out/terrain/land` with 8 row files instead of the whole grid, while `terrain.stamp`
  still matches. The next `make plugin` would reuse the broken land. Delete `out/terrain/terrain.stamp`, which forces
  a rebuild, before the next whole-province build. This lane was not permitted to touch the shared output.
