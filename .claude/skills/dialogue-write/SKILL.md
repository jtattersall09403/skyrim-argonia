---
name: dialogue-write
description: Write Morrowind-style topic dialogue for one Argonia NPC from a speaker brief, using matched Morrowind lines as the model. Use when authoring greetings, topic answers, quest lines or journal text for a person.
---

# Writing dialogue for one person

Draft, in practice with the owner. The goal: lines that read as if they were Morrowind's, about our people
and places. Every rule here came from an owner correction; add new ones to `bans.yaml` or the voice rules
below, not to a brief.

## 1. The brief (what the writer is given)

Never start without these. Missing items are asked for, not invented.

1. **What the player can see:** race, sex, place, where the person stands and what they are doing, visible gear.
2. **What the player cannot see:** name, role, household and group, faction, chattiness, friendliness,
   backstory; formality, address terms, oaths, things never said, and an opinion with a lean per topic,
   all inherited down the culture sheets (province > region > settlement > group > household > person).
3. **Facts with ids:** only the place-record facts this person carries, plus common knowledge. Every fact a
   line states cites its id. Facts are said once across a place; opinions differ per person.
4. **Neighbours:** name, office and where to find each, so a line can send the player on.
5. **Player knows:** the list of names, words and things the player has met by this point. Anything not on
   it is explained in the line that first names it (B04).
6. **Topics:** what each is for, the facts it may use, and whether it is **essential** (quest-carrying).
7. **Quest context** for quest topics: the stage, what the line must make the player know and do, which words
   become topic links, what this person hides and why, and the stage-dependent greetings and reminders.
8. **Things in the world:** every physical thing a line mentions (a pool, a stake, a satchel) carries a
   place-record, socket or quest-provision id. A thing with no id is written up as a REQUIRES row for the world
   builder and the line waits; dialogue never promises a thing the world does not hold.
9. **Morrowind lines:** the Find agents' picks for each topic (section 3).

## 2. Who is listening (variants on the player)

Morrowind conditions lines on the listener, and so do we. Write the variants the brief's person needs:

- **Player race.** Argonian speakers address an Argonian player as kin (Morrowind: marshbrother, marshsister)
  and others by race name (Morrowind: "You waste my time, Cyrodil."). Non-Argonians are ojel ("not of the
  tongue", not an insult; `fact.ojel`). A Dunmer player hears the history of slaving in some mouths.
- **Player faction and rank.** A member of the speaker's faction is greeted by rank and hears what members
  hear; a rival faction's member gets a colder greeting and less on faction topics; a stranger gets the
  default. Use `[player rank]` where the rank is spoken.
- **Player crime and standing** here: the person's crime greeting replaces the normal one.

## 3. Find agents

Split the corpus (`private/dialogue/morrowind/morrowind-full.json`, never committed) **by topic kind, not
round-robin**, one Haiku `find` agent per group: greetings and refusals (matched on speaker race and sex),
trade and service, place and directions, rumours and advice, creatures and danger, quest arcs (offer,
detail, directions, reminder, success, failure; Skink-in-Tree's-Shade and the Processus Vitellius topics are
good models). Each returns up to four lines per topic and band. Verify every id and quote against the corpus
before using them.

## 4. Voice rules

- **Disposition bands:** refusal below 10, unfriendly 10 to 40, medium 40 to 70, friendly 70 to 100. Length
  follows warmth: low bands are short, only the friendly band is chatty.
- **Essential topics have no refusal band** (decision 0145, old repo); the low band is grudging but still
  gives the player what the quest needs.
- **Held-back information says so** (B09): "I do not share my thoughts with strangers." Morrowind gates some
  answers on disposition (`mw05674`, `mw05675`) without a hint; we hint, because the player cannot guess.
- **Argonians:** full forms (B06), some speaking as "we", full sentences (never clipped telegraphese), earnest
  rather than wry (B07), our own idiom written fresh. Morrowind's Argonians are mostly strangers or slaves in
  another country; a free Argonian at home takes the generic commoner's content with the Argonian surface.
  No slave register ("muthsera") unless the person is one of the Owing.
- **Other races** follow their Morrowind contraction rates (Nord, Breton, Imperial about 85 to 90 per cent;
  Dunmer and Orc about half; Khajiit rarely).
- **Plain and explicit.** Say what happened, who did it and why, in plain clauses (B05). The player must be
  able to act on every quest line without guessing.
- **British English** spelling and punctuation, no serial comma (B08).
- Morrowind's text macros: `[player]`, `[player race]`, `[player rank]`, `[name]`.

## 5. Process

1. Read the brief and the whole of `bans.yaml`.
2. Run the Find agents (section 3) and read their picks.
3. Write each topic's bands and listener variants, modelling shape and cadence on the picks.
4. Run `python3 .claude/skills/dialogue-write/lint.py LINES.txt --race <race>`; fix every hit or note why it
   stands; then check each `review` ban by id.
5. Return the lines with the fact ids they cite, the REQUIRES rows, and any fact you had to invent, flagged.
