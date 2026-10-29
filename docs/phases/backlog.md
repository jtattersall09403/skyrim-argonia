# Polish backlog

Three queues ([README](README.md) § Polish). A blocker never goes here. Each row: id, what, where (place or
screen, with studio coordinates), the tag, the chunk that owns it, and the reason for the tag.

| Id | What | Where | Tag | Owner chunk | Why this tag |
|---|---|---|---|---|---|
| B1 | The world database's remaining old-schema rules (id patterns, item ranges and enums, several FKs, UNIQUE on `socket.id`; `lock.trap` once the trap table loads; `place_zones.owner_id` for faction owners) and the multi-table save's atomicity, sorted-file check and enum-valued vocabulary arguments (review of 0.4 §0, `docs/research/2026-10-29/review-0.4-s0-db.md`) | `world/schema.sql`, `tools/argonia_world/db.py` | `P1 before-scale` | 4.1 (each family's own chunk may close its rows first) | a data-shape wart every packet replicates |
| B2 | A roster slot holding several people gives its socket facts only to the first; a ruling on who carries them | `place_brief.py`, the socket tables | `P1 before-scale` | 2.4 | dialogue briefs at scale read it |
