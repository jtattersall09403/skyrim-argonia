# Phase 3: the story's first act on BM&V

Status: [PROGRESS.md](../PROGRESS.md). The plan: [PLAN.md](../PLAN.md). Edit this file as the phase goes; it is the phase's whole brief.

- **The census, into the story data.** BM&V's locations, cells, NPCs, factions and quests are read from
  `Black Marsh.esm` (Spriggit on the build VM) into new tables of the one relational store
  (`story/data/schema.sql`, loaded by `tools/argonia_world/db.py` like every other table): `bmv_location`,
  `bmv_cell`, `bmv_npc`, `bmv_faction`, `bmv_quest`, keyed by form key, with editor id, name, worldspace and
  position. Our designed places, people and factions are then **linked, not copied**: mapping tables
  `place_bmv_location`, `npc_bmv_npc` and `faction_bmv_faction` say which BM&V record a designed row lands on, and
  our own authored records carry their form keys in `mod_form` as the Magic Expanded forms already do. The quest
  skills read the mapping, so a quest written against a designed place resolves to a BM&V cell. Where BM&V has no
  place for a designed one, the row is mapped to the nearest BM&V place or marked waiting.
- **The opening** (prisoner work detail, the attack, the Veiled Reed) and the main quest's first three or four
  quests, written with the `quest-write`, `quest-review` and `dialogue-write` skills from the story records, built
  with the blocks.
- **One faction line's first two quests** (the owner picks the faction).
- **Owner test:** play the act from the Black Marsh start.
