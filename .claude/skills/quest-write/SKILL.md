---
name: quest-write
description: Design or rewrite an Argonia quest as a quest record (hidden truth, cast knowledge, things, clues, stages, endings, topics) from the place and culture data, then build the dialogue briefs from it. Use before any quest dialogue is written, and to rework a quest after review.
---

# Writing a quest

Draft, in practice with the owner. Quests, their dialogue and the world are made consistent by being built
from one record in a fixed order, not by checking afterwards. The record format is
[quest-record.md](quest-record.md); a worked example is [examples/lh38.yaml](examples/lh38.yaml).
Evidence for the principles: `docs/research/2026-10-27/quest-design-elder-scrolls.md` and
`quest-design-open-world-rpg.md` (both from search summaries; the source pages were blocked).

## 1. Read before designing

- The place record (facts with ids, people roster, things and sockets, routes and landmarks, quest hooks).
- The culture sheets down to each household: norms, taboos, values, contempts, opinions, never-said.
- The other quests at the place and its neighbours, so the cast is not double-booked and facts do not clash.
- The region's danger band (danger is fixed and must be warned of in dialogue).

## 2. Write the record in order

1. **Premise**, one sentence the player could say back afterwards.
2. **Truth**: what really happened before the player arrives, as numbered physical events (who, where, when,
   what, why). Write this before any stage.
3. **Plausibility pass**, event by event and person by person: would a sensible person with this person's
   wants, fears and knowledge do this? Write the reason down. If the honest answer is no, change the truth,
   never the person. (The first LH38 failed here: villagers knowingly left a corpse in their own water.)
4. **Facts**: the new facts the truth creates, each `from` a truth event.
5. **Cast and knowledge**: for every person and fact, knows, believes (the false version), suspects, hides
   (with the reason) or ignorant, and how that changes by stage. Knowledge comes only from events the person
   took part in or was told of.
6. **Things**: every physical trace the truth leaves and every object the player touches. Use an existing id
   from the place record, or mark it `new` with where it goes and its state per stage; the world builder
   places `new` things from these rows.
7. **Conclusions and clues**: what the player must work out, each with at least three clues in at least two
   forms (a line, a thing, a place, a behaviour), so one missed clue never strands them (the Three Clue Rule).
   Each clue is a trace of a truth event, carried by a person or thing in the record.
8. **Stages**: objective, precondition, postcondition, what the player learns, and directions by landmark,
   direction and distance (no markers; the journal carries them). At least one stage offers more than one
   approach (persuade, sneak, fight, pay). Say what happens if a needed person dies (fail-forward).
9. **Endings**: at least two with real costs on both sides, none presented as the right one. Each says what
   changes in the world, where the player will see it, and the reward: proportionate to risk and effort,
   tied to the story (training, a service, goods, standing, a lead onward).
10. **Topics**: for each person and stage, the topic name, essential or not, the intent, the facts it may
    state and the facts it hides, and the words that become links. An intent only rephrases its listed
    facts; anything else it needs becomes a fact first.

## 3. Shape

- A local quest has a hook, at least two lines of enquiry the player can follow in either order, a revelation,
  a decision and a visible consequence: about five stages over at least three spots.
- The player investigates or acts; nobody simply hands over the answer.
- A quest that needs disposition says so in the line that holds back (dialogue-write B09).

## 4. Hand on

1. Ask for a `quest-review` by a reviewer that has not seen your reasoning (section 1 of that skill).
2. Revise the record for every finding, or answer it in the record's notes.
3. Build the briefs: `python3 .claude/skills/quest-write/brief.py QUEST.yaml OUT_DIR --place-facts PLACE.json`.
   The builder writes nothing until every fact, thing, clue and person resolves.
4. Hand each brief to `dialogue-write`. When a writer asks for a fact, add it to the record and rebuild.
