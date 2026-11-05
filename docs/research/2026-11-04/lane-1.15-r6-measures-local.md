# Lane 1.15-r6-measures-local: the stand memo keyed by the cells a measure reads

- Each memoised measure now declares a `reach` box (eye ray 4 m, clearance the eye line, frustum cover 25 m, grass 20 m, water share and frame read their near_m); the key is the digest of the padded cells' vegetation, land and creature shard lines plus cells.jsonl rows, plus the static tables (object_form, ltex_grass, canopy radii) and MEASURE_VERSION. One store `out/journeys-cache/v3.sqlite`; rows older than 3 days unused are pruned.
- The cell-hash table (34464 cells) is one pass over the shards: 3.0 s per process.
- Output: cold refresh with the global key (14.5 min, loaded machine) and cold with the local key (14.7 min) wrote byte-identical tests/ and out/journeys-refresh.json; a warm refresh also identical.
- Warm refresh (1,206,787 hits, 0 miss): 70 s, then 58.8 s after replacing `inspect.bind` with a positional defaults fill.
- Synthetic edit of one vegetation line in a temp copy, at a water-types stand: "measures: 1193392 hit, 19577 miss" (1.6 % recomputed), 76.6 s.
- Test: tools/tests/test_journeys_measures.py (a far cell leaves the key, a neighbouring cell or a static table moves it; a reach memo recomputes only the stand whose cell changed).
- First run after this change is cold once (old whole-build stores are not reusable); later land edits cost only the stands in reach.
