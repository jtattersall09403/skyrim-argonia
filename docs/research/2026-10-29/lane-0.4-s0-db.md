# Lane 0.4-s0-db: the world database (decision 0030)

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

## Status

In progress.
