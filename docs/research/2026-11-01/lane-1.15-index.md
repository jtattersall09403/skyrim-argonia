# Lane 1.15-index: the repo-wide document index (2026-11-01)

Done on main (f511c90). `tools/doc_index.py --write` generates `docs/INDEX.md` (922 documents: docs 863, of which
docs/design 567; world/sources/lore 58; world/IMPORTED_FROM.md); `--check` exits 1 when stale and runs in the
Makefile's `records` part. CLAUDE.md's session-start bullet "Find documents in INDEX" routes agents to it (1,098
words). `tooling/tests/test_doc_index.py` covers the purpose extraction and staleness.

Extraction rule: a `purpose:` line wins; else the first heading, " — ", the first sentence of the first prose
paragraph (front matter, key lines, tables, quotes and lists skipped); lines about 120 characters.

**Rule for every lane:** a commit that adds, removes or retitles a document runs `python3 tools/doc_index.py --write`
in the same commit; a rebase conflict in `docs/INDEX.md` is resolved by regenerating it.

Owed: the gate's time on its own was not measured (9m08s queued behind other lanes' gates on `out/.check.lock`).
