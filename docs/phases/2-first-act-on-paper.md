# Phase 2: the first act on paper, the whole quest system adapted to BM&V, and the block set it needs

Status: [PROGRESS.md](../PROGRESS.md). The plan: [PLAN.md](../PLAN.md). Edit this file as the phase goes; it is the phase's whole brief.

The act is written before any block is built, so the blocks are the ones the story needs and no more (owner,
2026-11-05). Nothing is built in game in this phase.

- **Review the opening act as authored** - review the opening act of the main quest in detail and the overall shape of the entire main questline at a higher level, against the mined place records from phase 1. We may make minor changes to the BM&V world (e.g. placing new objects or getting rid of old ones, adding/removing/changing NPCs, adding/removing creatures, scripting existing things differently...etc) but not major changes. So we will need to adapt our main quest to keep the *spirit* of it and each of its acts, whilst adapting the *detail* to work with (a minorly-edited/added to version of) the BM&V world.
- **Update the quest-write and quest-review skills**. New owner preferences to be added in: there should be explicit lore-checking steps, it is essential that everything about every quest is consistent with our lore (canon and extrapolated). As well as all the obvious things you can think of, this should also include things like people's roles and jobs and the structure of society in Black Marsh in 4E 201. For example I've noticed that agents seem a bit obsessed with couriers and ledgers and rolls and tallies and so on. Does this actually make sense in our context? Would we *expect* Black Marsh in 4E 201 to be this bureaucratic? Or should we reauthor to make these quests fit better with the 'vibe' of our province at the time our game is set? We should have a big picture lore-grounded vibe that we refer back to and that very quest contributes to/fits with/doesn't jar against (like how Skyrim's overall vibe was nordic, militaristic, civil war-divided society, for example).
  Done: `story/design/province-vibe.md` (the 4E 201 vibe, cited to the lore, with what jars and what sings); quest-write §4b lore, society and motif checks; quest-review item 17 blocking; dialogue-write B10 warning; gap register §8; three independent review rounds, the last with nothing blocking.
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

## Scope now: the first story slice (owner, 2026-11-06)

BM&V stays as it is (separate worldspaces, minor edits only). Fitted to it first: the main quest's opening act,
including the new-game flow and the opening scene (our Helgen equivalent, replacing Phase 1's lightest start), and a
sensible subset of factions and questlines chosen so they do not clash, each with its seat and first quests. The
method below applies to the slice: the spirit of every line is already written for all of them (steps 1 and 2), the
capacity and allocation (steps 3 and 4) are used for the slice, and steps 5 to 10 run over the slice only. The rest of
the quest system follows once the owner has tried the slice.

## Status of the first story slice (2026-11-06, hand-off)

- Done: steps 1 to 8 over the slice (adaptation §5): the ledger in the story data, the checker in `make check`,
  seven ledger review rounds, the last clean. The ledger's generators are in the repo
  (`python3 -m tools.argonia_world.slice_ledger.slice` reproduces the committed rows). Blocks: W-navmesh and W-name
  added with precedent; blocks.md's Act I stage table is generated from the records
  (`python3 -m tools.argonia_world.slice_ledger.stage_blocks`; every stage maps to the set). The 35 old camp facts are
  retired; Low-Reed Village's people have low-reed-village ids; the cell men of MQ04 are npc rows.
- Act I's records: MQ05 clean at round 4, MQ01 clean at round 6. MQ03 and MQ04 have had eight fresh rounds each.
  Every round's blocking findings were fixed as one batch, yet each fresh round raises new blocking ones (round 8: MQ03
  3, MQ04 2). They are now structural rather than slips:
  - MQ03: why the broker obeys a spoken word (QA7 buy-back); hollow stages over the one-third limit (35, 30, 50);
    facts missing for the cord and the jars; RECKONING does not fit.
  - MQ04: the charge against Pays-Late is cutting, while the law and the award fit only negligence; the naming topic
    and the workshop zone short-cut the investigation.
  Spot patches will not converge. The next step is one quest-write rework of MQ03 and MQ04 against all eight rounds'
  findings (`review` rows in each record), including the shape change to NEGOTIATION for MQ03. Then a fresh round,
  then the owner's read (draft: [2-owner-read-draft](2-owner-read-draft.md), figures checked: 63 edits, 11 quests, 706 waiting) and PROGRESS.

## The whole quest system on BM&V (owner, 2026-11-05)

Not only the main quest: every authored questline and quest (in the story data: 717 quests in 16 lines, 33
factions; the detectives' faction of decision 0025 included) is reviewed against BM&V's whole world (all four plugins,
after the full census) and adapted to it, keeping the spirit of each line, with minor edits to the world where they
serve. Minor questlines are adapted or dropped; the wider build-out of new minor quests is Phase 5's. The set of
adaptations works as one consistent whole: it is designed once across everything, never quest by quest.

The method, in order:

1. **Inventory.** Every line and quest, its status (live, skeleton, proposed), region, settlement, faction and links
   (prerequisites, successors, shared cast, shared places, exclusivities).
2. **The spirit of each line, written down first.** For each line and each quest of it: what it is about (the promise
   to the player, the emotional and thematic core, the signature beats and the faction's identity), and which details
   are free to change. The source designs in `story/design/quests/` and the lore are the authority. Nothing is changed
   yet.
3. **The world's capacity, measured.** From the census: each BM&V settlement, region and dungeon with what it can host
   (people, interiors, faction seats, danger band, travel links), and what each line needs of the world.
4. **One allocation across all lines at once.** Every line gets its hubs (faction seats, quest-givers' homes), its
   places and its cast in BM&V's world, chosen together so no two lines compete for the same place, person or role
   unless the design wants them to meet; danger rises along each line as the fixed bands allow (decision 0035); the
   travel between a line's places fits BM&V's roads and boats.
5. **One adaptation ledger.** In the story data: per quest a verdict (keep, adapt, merge, drop), its adapted premise
   and host places; and one world-edit ledger (each edit once: an NPC added, moved or removed, a reference placed or
   disabled, a creature or boss, a changed BM&V record), linked to every quest that needs it. Act I's four records
   join the ledger like every other quest.
6. **Checks over the whole set, by code** (a checker run in `make check`): every kept quest lands on a place that
   exists or a ledgered edit; no edit undoes what another quest needs (a person removed by one and used by another,
   a place repurposed twice); faction exclusivities and the prerequisite graph still hold and have no cycles; danger
   rises along each line; no settlement is over capacity; every call cites the lore or the extrapolation (0032); no
   Nordic element (0006) and nothing levelled (0035).
7. **Critical reviewers, independent and briefed with the files only:** one per line (does the adapted line keep its
   spirit?), one across all lines (clashes, repetition, tone, the world's consistency) and one for the lore.
8. **The loop:** the reviewers' and the checker's findings are fixed in the allocation and the ledger as one batch,
   never one quest at a time; then the checker runs and fresh reviewers read the whole set again. The loop ends when a
   full round, checker and every reviewer, raises nothing blocking.
9. **The block set covers the whole story.** The mechanics every adapted line needs are mapped to the block set; any
   mechanic outside it gets a new block with its Skyrim.esm precedent (or the quest is re-authored), so Phase 3 proves
   the blocks the whole story uses, not only Act I's.
10. **The owner's read:** a summary per line (what it keeps, what changed and why, its new home in BM&V) on one issue;
    nothing waits on it.

## Done (2026-11-05)

- **The adaptation:** [act1-on-bmv](../../story/design/quests/act1-on-bmv.md). The act's spirit and shape are kept; its
  beats move to BM&V's Lilmoth (Dock1, Pusbottom, its Hist grove), Hereguard Plantation, the tribal Village east of
  Lilmoth (as the Hatching Pools, `place_bmv` row added), and Helstrom by BM&V's ship. Minor edits only: placed
  people and fixed-level enemies, enable parents, locks, a few statics; levelled and Nordic-look BM&V placements in the
  act's path are removed under parents that stay off.
- **The records:** `quest.main.mq01` (the work detail, the attack, the Hist closing), `mq03` (the Veiled Reed's
  pardon and the first dream), `mq04` (the second closed tree), `mq05` (Helstrom), in the story data, each citing its
  census rows. Each was reviewed by a fresh `quest-reviewer` six times (the last two narrowing to the fixes) and revised until nothing blocking remained;
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
