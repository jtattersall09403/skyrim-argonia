# Lane 0.4-sa-pipeline: the generation pipeline (§a) and the quarantine's records (§b)

Commits: `257eb4b` (pipeline, quarantine records, drivers), `5a78506` (contract README, memory settings), and
the last (review fixes, db.py wiring, the studio sheet records).

## What exists

- `tools/argonia_world/skyrim_units.py`: the only home of unit facts (units per metre, cell, LAND, VHGT step,
  yaw → ZYX radians, FormID range, the official masters). A test greps `tools/` for the literals outside it.
- `tools/argonia_world/formids.py`: the allocator over the world database's `formid` table through db.py (the
  first six ids moved there from `data/formids.json`, which is deleted); `check` proves append-only against
  HEAD's table, loaded through db.py from `git archive` (no removal, no change, no reuse below the old maximum).
  `frozen=True` refuses to allocate (the gate uses it, so an unallocated record is a red asking for `make plugin`).
- `tools/argonia_world/pieces.py`: mesh path, asset id (`pool:path` via the registry) or `composite:` →
  base record (earliest plugin in load order, then Static before other kinds, then lowest FormID), else a new
  STAT of ours (`ARG_STAT_<path>`) when the mesh is in an archive or loose with no base record, else unresolved.
  Among several base records the latest plugin wins (Black Marsh mods, then Tropical Skyrim, then vanilla, 0006
  §8), then Static, then the lowest FormID; the index keeps each record's winning override. `pieces check` reads
  every place's `layout_place` rows through db.py (asset `pool:path` → `meshes/path.nif`, the registry's rule for
  34,119 of 34,169 rows) and exits 1 on any unresolved piece; the gate runs it on the places the plugin builds
  (none until §d). Today, over all 18 laid-out places: 502 pieces, 269 unresolved; Claywater: 46, 18 unresolved
  (16 meshes of dependency mods not yet synced to the build VM, 2 composites with no member table in the db).
- `tools/argonia_world/intermediate.py`: the intermediate JSON writer, layers by record id (`compose`), the
  quarantine layers, the load order (official masters, then `Skyrim.ccc`'s present plugins).
- `tools/ArgoniaGen`: `index` (26,265 modelled base records, 22,761 archive meshes), `quests` (1,859
  self-starting vanilla quests: 443 start-game-enabled, 1,426 story-manager; 64 music types), `generate`
  (GLOB, MUSC, STAT, interior CELL + REFRs, QUST with VMAD/stages/event conditions, CLAS, SPEL, LVLI).
  The intermediate JSON contract is in `tools/ArgoniaGen/README.md` (for 2.W1's `Land*.cs`).
- `tools/ArgoniaGen/pipeline.py`: `make plugin` and the gate part `plugin-check`.
- §b records: `ARG_StartQuest` (start-game-enabled, run-once, stage 10 guard, VMAD `ARG_StartQuestScript` with
  the holding marker), `ARG_HoldingCell` (interior, black lighting, can't-travel, silent music type, a marker and
  a vanilla Imperial floor tile), every self-starting vanilla quest plus `MQ101` as an inert shell (EditorID
  only, no flags, stages, aliases or scripts, an always-false event condition on `ARG_QuarantineNever`), every
  vanilla music type as a shell with no tracks. Allow-list: `data/quarantine/allowed-quests.json` (running:
  `ARG_StartQuest`; keepVanilla empty). Shells copy no vanilla content (0003): only ids and EditorIDs.

## Measured

- `make plugin`: 17.4 s with fresh scans (30.7 s the first time, with the dotnet build); peak RSS 507 MB (`/usr/bin/time -v`; the piece
  index, 7.5 s; quests 147 MB, generate 125 MB). dotnet runs with workstation GC, a 3 GB heap limit, under
  `systemd-run --user --scope -p MemoryMax=3G`.
- `pipeline.py check`: 21.5 s, peak RSS 285 MB. `make check` (all parts): `CHECK GREEN`, 7 min 6 s wall, dominated by the
  `unit` part's other lanes' tests (421 s for 81 tests); our 17 tests take 0.2 s.
- Output: `Argonia.esm` 221,909 bytes, 1,930 records, 1,932 YAML files in `plugin/Argonia/`.

## Acceptance

- `make plugin && make check` green (above).
- One-file Spriggit diff: `ARG_StartQuest` priority 90 → 95 in `data/quarantine/start.json`, `make plugin`:
  `plugin/Argonia/Quests/ARG_StartQuest - 000805_Argonia.esm.yaml | 2 +-` (`-Priority: 90` / `+Priority: 95`),
  nothing else; reverted, `make plugin` again, tree clean.
- Second `make plugin`: no diff (`git status` clean on `plugin/` and `data/formids.json`); the gate generates
  twice into `out/check/{a,b}` and compares ESM bytes and YAML trees.
- Round trip byte-identical: `plugin/Argonia/` deserialised by Spriggit equals the generated ESM byte for byte
  after `canon`. Finding: Spriggit 0.41's deserialiser writes a group's records in directory-listing order (the
  filesystem's, e.g. `WICastMagic02` first), so a raw compare differs while the content is the same; `canon`
  sorts each group by raw FormID, the order the generator writes. `spriggit standardize` crashes on our plugin.
  The check is live: one tampered YAML field gave a 1-byte difference. Mutagen's NextFormID is left to Mutagen
  (with `NoNextFormIDProcessing` the header differed at byte 39).
- Pieces L1 check fails on a deliberately unknown piece: `test_pieces_check_fails_on_a_deliberately_unknown_piece`
  (`bmv:deliberately/unknown: unresolved`, exit 1; exit 0 without it).

## Owed

- **Composites and the asset registry in the db**: `composite:` pieces resolve once a member table exists
  (the place builder's chunk, §d, or the db lane); the 50 htbm rows off the path rule need the registry rows.
- **The studio sheet records** are in (`data/quarantine/start.json` `studio`: argonian, marsh-guide, serpent):
  `ARG_Class_marsh_guide` (CLAS, skill weights from the class's majors ×3 and minors ×1 through
  `skyrim_units.SKILL_AV`), `ARG_Race_argonian` and `ARG_Sign_serpent` (ability SPELs, no effects yet: the effect
  stack maps sources onto magic effects in 2.1 §b). No names: the sheet's screens are ours. **Owed: the start
  kit**: the world database has no start-kit rows; an LVLI writer is ready.
- **Game-machine batch** (not run; `tooling/job_guard.sh run --gpu records -- infra/gpu-box/records_jobs.sh all`):
  Papyrus compile of `papyrus/ARG_StartQuestScript.psc` with the CK's compiler and `Scripts.zip`; the CK load
  check (UI Automation of the Data dialog, unproven); BSArch packing of the `.pex`. russo-2025/papyrus-compiler
  not yet compared.
- **The quarantine journey** (0.3's runner does not exist yet): new game, running quests at 0, 1, 10, 50 days
  against `allowed-quests.json`, the music type read. Risks it must settle: engine-needed quests among the 1,860
  shells (add to `keepVanilla`), where the player stands before `OnInit` moves them, and whether a shelled
  `MQ101` still starts.
- **Dependency plugins**: `data/dependencies.json` names no plugin files yet; `load_order` takes a `plugins`
  list when 0.2 adds one. The masters list currently includes the four free CC plugins and `_ResourcePack.esl`
  of the pinned runtime, because their quests are shelled.
- Shouts: no record yet; the player learns none (word walls are in Tamriel, `VoicePowers` shelled).

## Review (one /code-review pass, 10 findings; fixed)

Round trip canonicalised on both sides and interior blocks written in number order; the gate part skips loudly
without game data; the scan cache keys on the BSAs and the ArgoniaGen build too; the index and quest scan use
each record's winning override (one pass per plugin, mesh archives only, loose meshes only under `meshes/`); the
resolver prefers the later plugin (0006 §8); composite cycles are unresolved, not a crash; the CK load job sets
aside and restores `Argonia.esm` and `CreationKitCustom.ini` in a `finally`; the start script moves the player
from `OnUpdate`, so the early `OnInit` cannot spend the stage-10 guard. The rescan changed one shell: Update.esm's
`MUSSpecialWordOfPower` adds `DoesNotQueue`.

## Open conflict with the §0 lane

The 0030 migrator rewrites every `world/db/*.jsonl`, and its run empties `formid.jsonl` (seen twice, last at
20:01:19 UTC, after `7a41bde` committed the nine ids 0x800–0x808). HEAD is right; the working file is not, so
`formids check` reads as nine removals and `make plugin` would re-allocate (the same ids while the order holds).
Fix at source: the migrator carries `formid` over as it is (an append-only table it never rebuilds), or skips it.
