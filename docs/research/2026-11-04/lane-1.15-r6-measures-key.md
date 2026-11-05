# Lane 1.15-r6-measures-key: the measures' build key hashes shard content

- `build_key` (tools/journeys/measures.py) now hashes sha256 of each `out/terrain/{vegetation,land}/cy*.jsonl.gz` file's bytes (name + digest), not its size; the other inputs (object_form, ltex_grass, water cells, MEASURE_VERSION) are unchanged.
- Why: r6-chain22 rewrote byte-identical vegetation shards and the refresh went cold (351 s vs 41 s); a size-equal change would have read as warm.
- Compressed bytes are content-exact here: the shards' gzip header mtime field is 0 (checked with xxd), so the writer is deterministic; no need to decompress.
- Cost on the real tree (158 MB of shards): 0.06 s with a warm page cache (0.005 s before); far under the 3 s limit, so every shard is hashed in full.
- Test `test_the_key_follows_shard_content_not_the_write`: identical-bytes rewrite (new mtime) keeps the key, a same-size one-byte change moves it.
- Green: tools.journeys check, journeys tests, ruff.
