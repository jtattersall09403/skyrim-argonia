# Story

Our storyline, quests, factions and people, kept to be adapted onto Black Marsh & Valenwood's (BM&V's) world.
The old generated world is gone; what is here is the story and the design behind it.

## Folders

- `lore/`: the lore dossiers by tier, the regions, topics and the extrapolation. Every world, people and quest
  call cites them (decision 0032).
- `design/quests/`: the quest design: overview, political frame, main quest, cast and roster, factions, side
  quests, the condition vocabulary, and `index/` (the quest index by line and region, coverage).
- `design/text/`: the style guide, the core style rules, culture registers and the review process.
- `design/world/`: the lore systems, causal authoring, extrapolation, ecology and demographics notes.
- `design/research/`: the old design's research (dialogue, lore audits, quests and cast, settlements, voice).
- `design/old-decisions/`: the old design's rulings that still bind the story (main quest, density, rewards).
- `data/db/`: the structured export of the old design, one JSONL per table (233 tables), described by
  `data/schema.sql`. `data/sources/`: the source registries (assets, demographics, dialogue exemplars and
  writer, economy, creature harvest). `data/IMPORTED_FROM.md`: where the import came from.

## The story data

`data/db` holds 717 quest rows, 1162 NPCs, 2195 dialogue lines, 33 factions, 830 places, 511 items and 52
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
