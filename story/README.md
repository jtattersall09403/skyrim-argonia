# Story

Our storyline, quests, factions and people, kept to be adapted onto Black Marsh & Valenwood's (BM&V's) world.
The old generated world is gone; what is here is the story and the design behind it.

## Folders

- `lore/`: the lore dossiers by tier, the regions, topics and the extrapolation. Every world, people and quest
  call cites them (decision 0032).
- `design/quests/`: the quest design: the line plots under `lines/`, the cast rules and roster, side quests,
  the condition vocabulary, the names never reused, reward gear and `index/README.md` (the shapes and the
  novelty rule).
- `design/text/`: the style guide, the core style rules, culture registers and the review process.
- `design/world/`: the lore systems, causal authoring, extrapolation, ecology and demographics notes.
- `data/db/`: the structured export of the old design, one JSONL per table (272 tables), described by
  `data/schema.sql`. `data/sources/`: the source registries (assets, demographics, dialogue exemplars and
  writer, economy, creature harvest).

## The story data

`data/db` holds 603 quest rows, 1190 NPCs, 2098 dialogue lines, 23 factions, 831 places, 507 items and 52
creatures, with their stages, facts, topics, stances, culture sheets, conditions and actions. It is mined when
a quest or person is adapted onto a BM&V place: the old places are design intent, not a map.

Read and write it only through `tools/argonia_world/db.py`, which loads every table into SQLite with the
schema's types and foreign keys:

    python3 -m tools.argonia_world.db check                       # load and check every constraint
    python3 -m tools.argonia_world.db query "SELECT id, name FROM faction"
    python3 -m tools.argonia_world.db show npc <id>
    python3 -m tools.argonia_world.quest_record export <quest id> -o QUEST.yaml

In Python: `from tools.argonia_world import db; w = db.load()`, then `w.query(sql)`, `w.get(table, key)`.
The writing skills (`quest-write`, `quest-review`, `dialogue-write`, `text-review`) build on this data.
