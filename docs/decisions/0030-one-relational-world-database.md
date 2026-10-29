# 0030: One relational world database from day one: normalised tables with keys, one source of truth per fact, everything else derived

**Status:** decided 2026-10-29 (owner: "I want us to have a properly robust, future proofed, linked data model
(like data-driven development) from day 1… I'm a data scientist so I think in data. I don't want a mess of
individual separate files or records, I want it to be like 3NF or something and interlinked with primary keys
and so on; single sources of truth for everything that needs it and with that pulling through where it's
needed. Some things like the quest skills may need to be edited to take this into account. Don't build it now
but put it in the plan where appropriate (presumably early in 0)."). Built in 0.4 §0.

## Context

The old project already held "one normalised record set" (old 0104; `docs/design/world/98-data-model.md`): one
home file per entity, stable ids with prefixes, references by id, an integrity checker. But it is a set of
hand-shaped JSON files: 23 registries, catalogues split by region, blueprints and promises per place, dialogue
split into pool, place lines, stance and culture sheets, quests in five files plus per-region locals, with
nested objects and repeated fields. Its ids are strings parsed by convention; its integrity is a script per
family. That is an entity model, not a relational one, and every skill and tool reads files directly.

## Decision

1. **One relational schema is the single description of the world's data.** `world/schema.sql`: SQL DDL in
   third normal form, one table per entity and per relationship, every row keyed by a stable primary key
   (the old id strings stay as keys where they exist), every reference a foreign key, enumerations as lookup
   tables, prose as text columns on the row it belongs to, nothing nested and nothing repeated. The DDL carries
   `CHECK` constraints for the rules that are data rules (ranges, allowed values) and comments that say what each
   table is the home of. `98-data-model.md` is rewritten as the schema's guide (which table is the home of what),
   never a second description.
2. **The committed form is one JSONL file per table** under `world/db/<table>.jsonl`: one row per line, columns in
   schema order, rows sorted by primary key, so a git diff is a row diff and two agents editing different rows
   never conflict. No other data file under `world/` is a source of truth once its family is migrated.
3. **The working form is a database built from those files.** `tools/argonia_world/db.py` loads every table into
   SQLite (DuckDB for analysis) with the DDL, foreign keys enforced, and exposes it to every tool, generator,
   skill and agent: queries, typed row objects, and **the only write path** (writes go through it and are
   written back to the JSONL tables sorted). `make db` builds `out/world.sqlite`; the integrity gate is the load
   itself plus the schema's constraints plus the few rules SQL cannot state, as named checks. A tool that reads
   or writes `world/db/*.jsonl` directly is a defect.
4. **Everything else is derived.** Intermediate JSON, `plugin/` (Spriggit YAML), `Argonia.esm`, the FormID table
   (a table too: entity key → FormID, append-only), briefs for the writing skills, directions text, the immersion
   inventory, the map image's data, reports. A derived file is regenerated, never edited.
5. **The writing skills read and write the database.** The quest record (`quest-write/quest-record.md`) becomes
   rows: `quest`, `quest_stage`, `quest_objective`, `quest_cast` (who knows what), `quest_thing`, `quest_clue`,
   `quest_action`, `quest_ending`, `topic`, `line` (with its speaker, topic, conditions and journal text as
   columns and foreign keys); `brief.py` and `place_brief.py` query the database; `dialogue-write` writes lines as
   rows; `quest-review` reads rows. The condition vocabulary is a lookup table with its predicates' argument
   shapes. 0.1 §i's fit of the skills to the import is revisited once in 0.4 §0 to point them at the database;
   their principles and formats do not change.
6. **Migration is by family, once, and the import folder dies with it.** 0.4 §0 designs the whole schema and
   migrates every family Part 1 reads (places, people, factions, items, quests, topics, lines, facts, culture,
   routes, locks, the sheet's tables, the FormID table); each later chunk that first reads a family migrates it
   (the world track the terrain patches, hydrology bodies, regions, flora rules; 2.9 magic; 2.10 recipes; and so
   on) and deletes its files from `world/sources/`, which is read-only meanwhile. Nothing is read from
   `world/sources/` by a chunk whose family is migrated.
7. **Scale is the design point.** Every table is designed for Morrowind-scale counts (hundreds of places,
   thousands of people and lines, hundreds of quests): no per-region files, no per-place files; a region or a
   place is a key, not a folder. The load must stay fast enough for the gate (`make check` under three minutes)
   at ten times the slice's counts; the first measurement is 0.4 §0's acceptance.

## Why

A data scientist's world is a database: a fact lives once, a question is a query, and a derived thing is a view.
Agents are worst at keeping hand-shaped files consistent and best at writing against a schema with keys and
constraints that refuse a bad row. The old project's record set was a step toward this; making it relational
now, before Part 1 writes its first quest or line against it, costs one chunk section; making it later costs a
migration of every system's writer.

## Consequences

- 0.4 §0 is the schema, `db.py`, the migration of Part 1's families, and the skills repointed; every Part 1 and
  Part 2 brief's "data shape" step is a set of tables in `schema.sql`, never a new file format.
- PLAN §3's `world/` line and the data rules in phases/README §"Rules that keep the slice honest" are rewritten
  to this record.
- `world/sources/` is the import, read-only, shrinking as families migrate; `IMPORTED_FROM.md` stays as the
  provenance record.
