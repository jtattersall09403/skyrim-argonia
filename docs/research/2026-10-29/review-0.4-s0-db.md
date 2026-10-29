# Review: 0.4 §0, the world database (decision 0030)

Commits reviewed: ca31b48, 9a59131, e62a0e5, 494c417, ef720d0, 32e0822, 3f9a1c6, 9d32f9c, c9e6222, 4792f84.
Scope: tools/argonia_world/{db.py, checks.py, quest_record.py, scale.py, records.py}, the tests, world/schema.sql's
0030 section, .claude/skills/quest-write/brief.py and dialogue-write/place_brief.py. The lane report's stated
choices are not re-judged. I proved each finding by running it (probe scripts, then a test beside each fix) with
~/.argonia/venv/bin/python (3.12.3).

## Findings

| # | Sev | Where | Scenario (run) | Status |
|---|-----|-------|----------------|--------|
| 1 | High | db.py `save(tables)` | `insert npc; insert faction; save(["faction"])` cleared `dirty` entirely, so the npc row was committed in memory and never written. A later `save()` wrote nothing, and the edit was lost. | Fixed: `dirty -= names`. Test `test_save_of_some_tables_keeps_the_rest_dirty` |
| 2 | High | db.py load/open cache | Process A loads, process B saves a table, then A dumps `out/world.sqlite`. The cache's mtime is newer than B's file, so `_fresh` treats it as fresh for good and every tool reads the world without B's row. | Fixed: the cache holds the source files' signature (mtime_ns, size), taken before the load reads them. It is fresh only when that signature matches the files now. Test `test_cache_is_not_fresh_after_a_save_during_the_load` |
| 3 | High | db.py `save` | Two processes load and each adds a different row to `faction`. The second save rewrites the whole table from its own snapshot, so the first row is lost silently. | Fixed: save refuses a table whose file changed since this world loaded it ("reload and redo"). The `.tmp` name is per-pid. Test `test_save_refuses_to_overwrite_another_writer` |
| 4 | Med | db.py `delete(table, *key)` | `delete("npc_faction", "npc.b")` on a 2-column key deleted all 3 of npc.b's rows. Extra key values were also dropped by `zip` without a word. | Fixed: a positional key must be the whole key; `where=` does partial matches. Test `test_delete_needs_the_whole_key` |
| 5 | Med | db.py `query()` | `WITH x AS (SELECT 1) DELETE FROM npc_faction` passed the read-only regex and deleted rows without marking them dirty. `PRAGMA foreign_keys = OFF` turned enforcement off. | Fixed: an SQLite authorizer allows only reads and introspection PRAGMAs. Test `test_query_refuses_writes` |
| 6 | Med | quest_record.py import | A list or map where one value belongs (`foundation: [a, b]`, or a stage's `directions: {x: y}`) was dropped silently. The column went NULL and the import reported no error. | Fixed: refused with the path. `directions`, the one field that may also be a list, is kept. Test `test_a_list_where_one_value_belongs_is_refused` |
| 7 | Med | quest_record.py import | A wrong-typed value (`journal: 1990`) or a NOT NULL, CHECK or duplicate-key violation raised partway through, after the quest's rows had been deleted. A caller that caught it and saved would lose the quest. The docstring says "nothing changed when any". | Fixed: the write runs in a SAVEPOINT; on any of these the quest's rows come back and the error is returned. Bad `facts` entries are errors, not a crash. Test `test_a_bad_value_leaves_the_quest_as_it_was` |
| 8 | Med | place_brief.py | Facts carried at the person's npc socket (`socket.<place>.npc-<slot>`, 73 of the 95 npc-carried facts) were never listed under "Facts this person carries". Example: bog-iron-workings n1 got 6 facts, and gets 12 after the fix. This was carried over from the pre-0030 tool. | Fixed: carriers include the place's npc sockets whose `roster_slot_id` is the person's slot. Test `test_place_brief_has_the_facts_at_the_persons_socket` |
| 9 | Med | brief.py | The export leaves out a list that has no rows, so a quest with no clues or conclusions crashed with `KeyError: 'clues'`. | Fixed: the record's lists default to empty. Test `test_quest_brief_reads_a_quest_with_no_clues` |
| 10 | Med | schema.sql vs the old JSON schemas | The old stance.v1 and culture-sheet.v1 had ranges and enums that the DDL lost. None of them was enforced. | Fixed (today's data satisfies all of them): CHECKs on `stance.voice_contraction_rate` 0..1 and `voice_chatter` enum; `stance_answer_length` min 6..60, max 10..80; `lean` -2..2 on culture_opinion/view/dissent and stance_topic (including deviation_lean); `culture_sheet.deviation_rate` 0..0.5; `UNIQUE (quest_id, id)` on quest_stage. Tests `test_old_schema_ranges_are_checks`, `test_stage_ids_are_unique_in_a_quest` |
| 11 | Low | db.py load | One bad row after good ones: `executemany` kept the good rows, the per-row retry inserted them again, and the error list carried one spurious `UNIQUE constraint failed` per good row. With `strict=False`, rows were left half-loaded. | Fixed: a SAVEPOINT per table, rolled back before the retry. Test `test_one_bad_row_reports_only_itself` |
| 12 | Low | db.py types | JSON `NaN` loaded into a REAL column as NULL, with no error. `Infinity` loaded and was written back as `Infinity`, which is not valid JSON. A non-object line (`[1,2]`) gave a confusing error; a `null` line crashed. | Fixed: non-finite numbers and non-object rows are refused. Test `test_non_finite_number_refused` |
| 13 | Low | checks.py `run` | A check whose tables are missing is skipped (meant for tests' small schemas). If a table were renamed, its check would turn off and the gate would stay green. | Guarded by test `test_every_named_check_runs_on_the_real_schema`. All 4 run today |
| 14 | Low | db.py save | A multi-table save is not atomic: each file is replaced atomically, but a crash between two tables leaves a partial save. | Not fixed. It needs a journal or a staging directory. The FK load at the next run reports the inconsistency |
| 15 | Low | db.py load | The committed form (rows sorted by key, columns in schema order) is not verified, so a hand-edited unsorted file loads green and only makes diffs noisy. | Not fixed. Candidate named check if hand edits appear |
| 16 | Low | place_brief.py | A roster slot with headcount > 1 (n1, n1-2, n1-3) gives its socket's facts only to n1. | Not fixed. Which person carries a shared slot's facts needs a ruling |
| 17 | Low | checks.py term-arity | Checks argument counts only, not `enum{...}` values (`evidenceState(x, "smashed")` passes). | Not fixed. A design extension, not a defect in the check |
| 18 | Info | schema.sql, other old rules | Still missing, and today's data satisfies all of them: id patterns (item/lock/quest/zone), item value/weight/ladder ranges, `item.verb`/`ladder_band`/soul-gem enums, quest_stage `ending`/`entry` enums, FKs `lock.opens_place`→place, `quest_socket.value`→socket, `socket_schedule.socket_id`, UNIQUE `socket.id`. Blocked: `lock.trap`→trap (trap.jsonl is empty and 2 locks name traps), and `place_zones.owner_id` REFERENCES npc although owner_kind allows faction. | Not fixed (beyond the brief's small-fix scope). For the families' owners |

scale.py: no defect found. `to_vocab` is used only on the factor > 1 branch, where it is always defined.

## Gate

- Focused: `pytest -q tools/argonia_world/tests/`: 52 passed (6.6 s). `python -m tools.argonia_world.db check`:
  518 tables, 115,862 rows, FKs and named checks green.
- `make check` (25 s, peak RSS 532 MB): every test part passed (132 passed). Two reds, both outside this change
  and in other lanes' uncommitted work:
  - `world`: world-reads flags `tools/argonia_world/water/__main__.py:185` (2.W2, modified in the working tree).
  - `plugin-check`: `plugin/Argonia/` is stale in 94 climate/weather files (2.W3), and the ArgoniaWorld terrain
    sample hash differs from its manifest (2.W1).
  Re-proved by running `make plugin-check` alone; neither red reads a file this review touched.
