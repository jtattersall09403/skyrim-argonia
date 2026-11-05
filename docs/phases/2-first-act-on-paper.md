# Phase 2: the first act on paper, and the block set it needs

Status: [PROGRESS.md](../PROGRESS.md). The plan: [PLAN.md](../PLAN.md). Edit this file as the phase goes; it is the phase's whole brief.

The act is written before any block is built, so the blocks are the ones the story needs and no more (owner,
2026-11-05). Nothing is built in game in this phase.

- **Review the opening act as authored** - review the opening act of the main quest in detail and the overall shape of it at a higher level, against the mined place records from phase 1. We may make minor changes to the BM&V world (e.g. placing new objects or getting rid of old ones, adding/removing/changing NPCs, adding/removing creatures, scripting existing things differently...etc) but not major changes. So we will need to adapt our main quest to keep the *spirit* of it and each of its acts, whilst adapting the *detail* to work with (a minorly-edited/added to version of) the BM&V world.
- **Write the act as quest records.** The opening (prisoner work detail, the attack, the Veiled Reed) and the main
  quest's first three or four quests, through `quest-write` and `quest-review`, from the story data and the census's
  BM&V mappings. Records only: hidden truth, cast, things, clues, actions, stages, endings, topics. Dialogue is
  written in Phase 4, once the blocks it rests on are proven.
- **Derive the block set from the records.** List every engine mechanic the act's records use, then factor them into
  the smallest set of blocks that composes into all of them. A quest on Skyrim's engine is stages joined by
  connectors, so the set has a fixed shape:
  - **triggers** (what moves a stage): a dialogue topic or choice, entering an area, activating or reading a thing,
    picking up an item, a death, another quest's stage, waiting or resting;
  - **conditions** (what gates a trigger or a line): a quest stage, a global, faction membership or rank, an item
    held, a skill or attribute check, a location, time of day;
  - **effects** (what a stage does): set another stage, write a journal entry or objective, add or remove an item,
    enable or disable a reference, place or move an actor, change a faction or rank, start an AI package or scene,
    give a reward;
  - **the world edits** under them: a new NPC from a template on existing navmesh, a creature or boss at a fixed
    level, a new or removed reference, a changed BM&V record.
  Each block has one record shape and at most one script shape; every quest is a composition of blocks wired through
  quest stages, which is the engine's own glue.
- **The induction argument, written down.** A short note in this file: why proving each block once (the base cases)
  and proving the connectors once in a composite quest (the inductive step: every trigger type moving a stage that
  fires every effect type, gated by every condition type) means any quest built only from these blocks works. Name
  where the argument does not hold on this engine and guard each: two triggers racing for one stage, alias filling
  at quest start, persistent references, AI package priority, and a save and reload mid-quest. Each guard becomes a
  rule of the block or a case in the composite.
- **Feasibility, before anything is built.** For each block, the agent finds Bethesda's precedent in Skyrim.esm (how
  many vanilla quests use that record and script shape; decision 0034) and checks it is expressible in our route
  (Spriggit YAML plus a small Papyrus fragment). A block with no precedent, or one that needs our own SKSE code, is
  dropped and the quests that used it are re-authored around the blocks that remain.
- **Loop**: re-run `quest-review` on the re-authored records and the block mapping until every stage of every quest
  maps to blocks in the set and the review raises nothing blocking. Do not build anything in game.
- **Owner test:** none in game. The act outline and the block list go to the owner as one issue to read and rule
  on: a short summary of each quest, what changed from the authored design and why, and the block list with the
  induction note.

## Done (2026-11-05)

- **The adaptation:** [act1-on-bmv](../../story/design/quests/act1-on-bmv.md). The act's spirit and shape are kept; its
  beats move to BM&V's Lilmoth (Dock1, Pusbottom, its Hist grove), Hereguard Plantation, the tribal Village east of
  Lilmoth (as the Hatching Pools, `place_bmv` row added), and Helstrom by BM&V's ship. Minor edits only: placed
  people and fixed-level enemies, enable parents, locks, a few statics; levelled and Nordic-look BM&V placements in the
  act's path are removed under parents that stay off.
- **The records:** `quest.main.mq01` (the work detail, the attack, the Hist closing), `mq03` (the Veiled Reed's
  pardon and the first dream), `mq04` (the second closed tree), `mq05` (Helstrom), in the story data, each citing its
  census rows. Each was reviewed by a fresh `quest-reviewer` three times and revised until nothing blocking remained;
  the findings and answers are in each record's `review` section. `brief.py` builds every brief.
- **The blocks:** [docs/design/blocks.md](../design/blocks.md), with the precedent counts in
  [quest-block-precedent](../research/skyrim/quest-block-precedent.md). Seven triggers (topic, zone, activate, acquire,
  death or counted deaths, another quest's stage, a scene's end), seven conditions (stage, global, faction, item, skill,
  time, alive), nine effects (stage with journal and objective, enable parent, item or gold, move, faction, scene, alias
  package, global, regard), four world edits (templated NPC, fixed-level actor, new or removed reference, overridden BM&V
  record). Dropped: sleeping or waiting as a trigger (no vanilla precedent; re-authored as an activated bed and a
  time-gated topic), change-location starts and location conditions (BM&V has no locations). Every stage of the four
  quests maps; nothing needs SKSE.
- **The induction note** is in blocks.md: the stage is the only joint, so base cases plus one composite prove any
  quest of the set; guards for racing triggers, alias fills, persistent refs, package priority and save-reload.
- **Owed to Phase 4:** the quest vocabulary's skill names are Morrowind's (mapped to Skyrim's in C-skill for now); a
  0006/0035 audit of the coast road and Longmont before MQ04 is built.
