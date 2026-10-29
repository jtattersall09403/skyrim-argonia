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

