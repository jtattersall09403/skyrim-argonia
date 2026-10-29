# Lane 0.4-s0-db: the world database (decision 0030)

## Hand-off (2026-10-29, context mark reached; the next lane resumes from here)

**Done (committed).**
- `ca31b48`: `tools/argonia_world/db.py` (load with FKs on, typed rows, write path to sorted JSONL, CLI
  `build|check|query|show|counts`), `checks.py` (named-check registry, empty), `tests/test_db.py` (4 tests: a
  dangling key refused at load and at save, types/CHECK/NOT NULL/unknown column refused, sorted write-back).
- This commit: db.py writes are one transaction with FKs deferred to `save()`; typed-row attributes get `_` after a
  Python keyword (`class_`, `from_`). The one-off migrator `tools/argonia_world/migrate_0030/` (`engine.py`
  normaliser + lossless rebuild proof, `families.py` every family's spec, `run.py`).

**Measured.** `python3 -m tools.argonia_world.migrate_0030.run --no-write` (writes to `out/migrate/`, not `world/`):
472 tables (447 migrated + condition/action/vocabulary + `formid` + 24 keyed stubs), 91,350 rows, every FK
resolves, every source object rebuilds from the loaded tables (the lossless proof), 6.9 s, peak RSS 168 MB.
The vocabulary table's 62 predicates and 43 verbs equal the set brief.py parsed from 85.

**Pre-migration briefs captured** (needed for the byte-match): `out/pre-migration-briefs/` (gitignored), copied from
`/tmp/claude-1000/-home-ubuntu-skyrim-argonia/00aec70d-9f88-4179-b6de-7faca8084fef/scratchpad/pre/` (lh38/, mr01/,
place/ with 88 place briefs plus each person's exit code and stdout as `.rc`). If /tmp was cleared, regenerate them
from the commit before the sources are deleted: `git show ca31b48:...` of brief.py/place_brief.py and world/sources.

**Left, in order.**
1. Run the migrator for real (`python3 -m tools.argonia_world.migrate_0030.run`), writing `world/schema.sql` and
   `world/db/*.jsonl`; add tables over 1 MB to `tooling/guards/allowlist.txt` (check sizes), commit.
2. Add `db` to the Makefile (`db: ; python3 -m tools.argonia_world.db build`) and a `world` part to PARTS running
   `python3 -m tools.argonia_world.db check` and the world-reads grep (new `tools/argonia_world/check_world_reads.py`:
   no file under tools/ or .claude/ but db.py names `world/sources`, `world/db` or `world/schema`; allowlist
   `tools/import_old.py` with its reason; make it fail once, record it).
3. Named checks in `checks.py` for the polymorphic references SQL cannot state: `lock.owner_kind/owner_id`;
   `journal_entry_grounding.value` (a fact or a promise id); `quest_essential_topic.value` and `quest_topic.id`
   (a topic row or a record topic marked `new`); condition/action argument counts against `condition_term.args`.
4. Repoint `.claude/skills/quest-write/brief.py` (takes a quest id; reads quest_* tables, fact, npc, stance,
   culture_sheet/culture_entry, topic, condition_term), `dialogue-write/place_brief.py` (npc, place_build,
   place_person(+_topic), fact, stance, culture_*, topic), `quest-write/SKILL.md`, `quest-review/SKILL.md`,
   `dialogue-write/SKILL.md`, `quest-record.md`, `action_plan.py` paths. Write path for a quest record: a
   `db.py`-based importer of the YAML authoring view (`tools/argonia_world/quest_record.py import|export`, the
   repairs in `families.py:_yaml_record` applied); the two example YAMLs become exports.
5. Regenerate LH38 and MR01 briefs and the 88 place briefs from the db; diff against `pre/`. Expected diffs, to list:
   `Factions: {'factionId': ...}` becomes the faction id (old str(dict) bug); `setting: before witnesses (a
   council` becomes the whole phrase (YAML repair); any `0` vs `0.0` from REAL columns.
6. Delete the migrated files listed in `families.MIGRATED` from `world/sources/` (and `world/schemas/` entries for
   those families, `tools/argonia_world/integrity.py`, `promise_gate.py`, `schema.py`, which read them; their
   unmigrated rules return with their families), the example YAMLs once exported; repoint `tools/fetch_vault.py`
   to `frozen_array` (it reads `world/sources/terrain/freeze.json`). Then delete `migrate_0030/` (git history keeps it).
7. Rewrite `docs/design/world/98-data-model.md` as the schema's guide (which table is the home of what).
8. Scale: duplicate every table tenfold (suffix keys) into a temp root, `db check` and `make check` under
   `/usr/bin/time -v` and `systemd-run --user --scope -p MemoryMax=3G`, outside the default gate; record the numbers.
9. One `make check`, `/code-review` over the commits (diff > 1,500 lines), report.

**Decisions taken (record in the report).** Lookup tables are filled from the data's distinct values; place
facts, dialogue facts and quest facts are one `fact` table (3 ids overlapped: same fact, `claim` and `says`); the
registry's quest rows merged into `quest`/`quest_line` (registry `status`, `notes` kept as `registry_status`,
`registry_note`; registry `kind`, `name`, `tier` were duplicates); the LH38/MR01 records replace their data-file
rows; `place_build` holds the old bundle's `world` block (counts dropped as derived); two route places not in the
catalogue get name-only `place` rows; race `orc` repaired to `orsimer` (one npc, one culture sheet); the
`formid` table is empty: the §a allocator (`tools/argonia_world/formids.py`, `data/formids.json`, 6 ids) moves its
rows in when it switches to db.py, so there is never a second home; the sheet's tables come from
`private/old-packages/game-core/src/stats/data` (our own data; Morrowind's race numbers via UESP).

**Reds.** None in my tests (`pytest tools/argonia_world/tests`: green). No ruff/pyflakes on this VM; `make check`
not run (planner's memory note: once, before the final commit).


## db.py's API (stable; the §a lane builds on this)

```python
from tools.argonia_world import db
w = db.open()                    # the world, FKs on (reuses out/world.sqlite when newer than world/db and schema.sql)
w = db.load()                    # full load from world/schema.sql + world/db/*.jsonl; raises db.LoadError(errors)
w.get(table, *pk)                # one typed row (frozen dataclass, BOOLEAN columns as bool) or None
w.rows(table, order=None, **eq)  # typed rows where each column equals the keyword, ordered by primary key
w.query(sql, *params)            # read-only SQL -> sqlite3.Row list;  w.values(sql, *p) -> first column
w.insert(table, row=None, **cols); w.upsert(...); w.update(table, *pk, **cols); w.delete(table, *pk | **eq)
w.save()                         # FK check + named checks (tools/argonia_world/checks.py), then the changed
                                 # tables written back to world/db/<table>.jsonl sorted by key; raises LoadError
w.dump(path)                     # one SQLite file;  python3 -m tools.argonia_world.db build|check|query|show|counts
```

Writes are one transaction with foreign keys deferred to `save()`. Nothing else reads or writes `world/`.
The FormID table is `formid` in `world/schema.sql` (entity key -> FormID, append-only); the allocator writes it
through `w.insert("formid", ...)` and `w.save()`.


## Continuation (2026-10-29): steps 1–9

**Commits:** e62a0e5 (migration written), 494c417 (named checks, world-reads check, promise keys), ef720d0 (23 late
FKs), 32e0822 (formid carried over, fact.ord, stance.person_id, make db), 3f9a1c6 (migrator writes only OWNED tables,
schema end marker), 9d32f9c (skills on db.py, quest_record, sources and readers deleted, world part in the gate,
98 rewritten), c9e6222 (linear load at scale, scale.py).

**Acceptance (0.4 §0).**
- **FK load and a dangling key refused:** passes. `db check` reports 514 tables and 112,813 rows (the world-track
  lanes' tables included), green in 1.8 s with a 61 MB peak. A dangling key is refused at load, at save and at
  quest import (test_db, test_quest_record).
- **World-reads grep in the gate, made to fail once:**
  - Before steps 4 and 6 it reported 110 real hits.
  - A path planted in `tools/zz_planted.py` turned `make world` red (rc 2). With the path removed it was clean
    (rc 0).
  - It is also proved in test_checks.
- **Briefs match the baselines except the listed diffs:**
  - The 88 place briefs, 88/88, are byte-identical.
  - The 2 journal briefs are identical.
  - 9 LH38/MR01 cast briefs and 216 `.rc` outputs differ, only in the expected ways listed below.
- **Tenfold, outside the gate:** `scale.py --factor 10` gave 1,122,846 rows. Both runs below were under
  `systemd-run --user --scope -p MemoryMax=3G /usr/bin/time -v`.
  - `db check`: green in 10.5 s, peak RSS 296 MB.
  - `ARGONIA_WORLD_ROOT=out/scale make check`: 49.5 s, peak RSS 532 MB (the dotnet plugin step).
- **Default `make check`:** 24.4 s, peak 285 MB. The `world` part is green. Two other parts are red, `unit` and
  `plugin-check`. Both reds come from 2.W1's uncommitted terrain work (`tools/argonia_world/terrain/__main__.py`,
  `test_land_writer.py`), which imports numpy, and numpy is not installed on the system python. They are not §0
  paths.
  - At 10x, world-reads also flagged two uncommitted lines from other lanes: `tools/ArgoniaGen/pipeline.py:140`
    and `terrain/migrate.py:6`. They are those lanes' to fix.
- **Verdict:** every §0 acceptance check passes. `make check` is red only on other lanes' uncommitted work.

**Expected brief diffs (each listed):**
1. The Role line now reads `(npc)`; it used to say `(npcs.json)`.
2. `Factions:` shows the faction id where the old reader printed the dict (`{'factionId': ..., 'rank': None}`, its bug).
3. `before witnesses (a council` becomes the whole phrase. The YAML repair is now applied at import.
4. Map entries are listed in key order: the thing `states` (`after-70` before `before-70`) and cast `knowledge`.
   Maps are keyed rows with no `ord`.
5. Helstrom's 216 people: the old reader crashed on a facts file with no `world` block, exiting 1 with empty
   stdout. The new one exits 1 with "no place facts for place.hist-heartland.helstrom".

**Decisions taken:**
- **Migrator ownership:** the migrator writes only the tables it migrates (OWNED). It leaves every other
  `world/db/*.jsonl` table untouched, and keeps schema blocks and everything below the end marker. Tested with a
  foreign table.
- **Promise keys:** they were migrated so `groundedIn` resolves. The promise files stay in place.
- **Fact order:** `fact.ord` keeps each place's and quest's fact order.
- **Stance key:** `stance` is keyed by `person_id`, with a foreign key to `npc`.
- **Late foreign keys:** 23 were added on context columns. Some id columns still lack keys because their families
  are not tables yet (98 names them).
- **Bool arguments:** these are typed from the vocabulary shape. An untyped SQLite value stores `true` as 1.
- **Empty lists:** an empty stage list is no rows. brief.py requires only `id`, `place` and `journal`.
- **Arity defaults:** term arity allows a trailing `bool` or count to be left out. Every authored record writes
  `flag(x)` and `hasItem(x)` this way; 85 should say so (not my path).
- **Quest topic rule:** I dropped the "new but already a topic" check. It is not a stated rule, and MR01 trips it.
- **World-reads exceptions:**
  - Skill instructions may send agents to the two families that are not yet tables (`lore`, `blueprints`), read
    only.
  - Exports under `quest-write/examples/` are exempt, because their `world/sources` strings are provenance
    values.
- **Pointing tools at another world:** `ARGONIA_WORLD_ROOT` points db.py at another world root.
- **Concurrent cache builds:** these collided in a 4-way run (disk I/O errors). The cache now builds through a
  per-process temp file.

**Owed:**
- The /code-review pass: the planner runs it in a fresh context.
- `dialogue-write` writing lines as rows: that is 2.5's importer.
- 85-condition-vocabulary.md should become the guide to `condition_term`.
