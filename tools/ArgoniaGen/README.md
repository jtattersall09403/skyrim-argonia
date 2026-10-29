ArgoniaGen: .NET 10 + Mutagen 0.54.4, the record writer of the pipeline (decision 0009): `tools/argonia_world` plans and resolves into intermediate JSON; this maps it onto Mutagen records and writes `Argonia.esm`; Spriggit 0.41.0 serialises it to `plugin/Argonia/`.

- `make plugin` runs `pipeline.py plugin`: build, `quests` and `index` scans of the masters (cached in `out/` until a plugin changes), `intermediate.py`, `generate`, Spriggit.
- The gate's `plugin-check` runs `pipeline.py check`: FormIDs append-only, pieces resolved, regenerate twice identical, `plugin/Argonia/` current, Spriggit round trip byte-identical (after `canon`, since Spriggit's deserialiser orders a group by directory listing).
- Commands: `counts`, `index`, `quests`, `generate` (see `Program.cs`). Record writers so far: GLOB, MUSC, STAT, CELL (interior, with REFRs), QUST (flags, stages, VMAD object properties, event conditions), CLAS, SPEL, LVLI; a type without a writer is an error.
- Needs `bash infra/build-vm/setup.sh` and Skyrim's Data at `$ARGONIA_GAME_ROOT/Data` (default `~/games/skyrimse/Data`). Heavy runs go under `systemd-run --user --scope -p MemoryMax=4G` (pipeline.py does this).
