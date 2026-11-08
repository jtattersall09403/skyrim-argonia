# The new world: Project Tamriel's Black Marsh

Our own worldspace, built from Project Tamriel's Black Marsh map, in parallel with the BM&V work
([plan](../docs/phases/new-worldspace-plan/README.md)). It is laid out like the repo root, so the same tools
load it: `db.open("newworld")` (`tools/argonia_world/db.py`) reads `story/data/schema.sql` and
`story/data/db/*.jsonl`.

| Path | What |
|---|---|
| `sources/maps/` | The base map, the regions map and the Hammerfell/High Rock key (public domain, UESP, Project Tamriel) |
| `sources/reads/` | The tile-by-tile reads of every map symbol, the readers' brief, and the corrections found on review |
| `story/data/schema.sql` | The database: map key, cultures, regions, cells, places, research notes, roads, borders, water, terrain builds |
| `story/data/db/` | One `.jsonl` per table |

The code is `tools/newworld/` (see each module's docstring); its generated rasters and previews go to
`out/newworld/` and are rebuilt, never edited.
