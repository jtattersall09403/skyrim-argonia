---
name: dialogue-write
description: Write Morrowind-style topic dialogue for one Argonia NPC of any race from a generated speaker brief, using matched Morrowind lines as the model. Use when authoring greetings, topic answers, quest lines or journal text for a person.
---

# Writing dialogue for one person

Draft, in practice with the owner. The goal: lines that read as if they were Morrowind's, about our people
and places. Every rule here came from an owner correction; add new bans to `bans.yaml`, new voice evidence
to `voices.md`.

## 1. The brief

The writer works only from a brief built from a record, never from a hand-written summary:

- **Quest topics:** `quest-write/brief.py` builds one brief per person from the quest record.
- **Place topics** (greeting, my trade, the place, rumours, danger, work, directions): the same brief shape,
  from the place record, the people registry and the culture sheets: `place_brief.py`, which picks the
  sheets that apply (region by place, people by race and upbringing, faction and office by faction and rank,
  settlement, group and household) and says when the talk can happen (a hostile place's flips).

A brief holds: what the player can see (race, sex, place, pose, gear); what they cannot (role, household,
faction, chattiness, friendliness, formality, backstory, wants, fears); the voice card; the others the player
may be sent to; the things lines may name, by id; and per topic the intent, the facts it may state and hide,
the speaker's knowledge, the links it grants, and what the player already knows.

**Lines set up the action.** A quest brief lists what the player does at each topic's stages (the skill
uses); the lines give what the player needs to do it: who, where, when, what danger, what they will need
(a light for the dive, the guard's hours, the lock's owner), never how the designer expects it solved.

**The writer adds no facts.** A line that needs one not in the brief is not written: the writer asks for the
fact, the quest writer adds it to the record, and the brief is rebuilt.

## 2. Speaker and listener

The speaker and the player can each be any of the ten races. Use the speaker's voice card in `voices.md`
(contraction rate, sentence length, self-reference, address). Write listener variants where the line
changes:

- **Player race:** address terms and attitude follow the speaker's race and culture sheets (`voices.md`).
- **Player faction and rank:** same faction, greet by `[player rank]` and share members' knowledge; rival
  faction, colder and less on faction topics; otherwise the default.
- **Player crime here:** the person's crime greeting replaces the normal one.

## 3. Find agents

Split the corpus (`private/dialogue/morrowind/morrowind-full.json`, never committed) **by topic kind**, one
Haiku `find` agent per group, matched on the speaker's race and sex: greetings and refusals; trade and
service; place and directions; rumours and advice; creatures and danger; quest arcs (offer, detail,
directions, reminder, success, failure). Each returns up to four lines per topic and band. Check every id
and quote against the corpus before using it. Never paste Morrowind lines into the repo.

## 4. Voice rules

- **Bands:** refusal below 10, unfriendly 10 to 40, medium 40 to 70, friendly 70 to 100. Length follows
  warmth: low bands are short; only the friendly band is chatty.
- **Essential topics have no refusal band** (decision 0145, old repo): the low band is grudging but still
  gives what the quest needs.
- **Held-back information says so** (B09), so the player knows to raise disposition.
- **Plain and explicit:** who did what and why, in plain clauses (B05); every quest line can be acted on.
- **British English** spelling and punctuation, no serial comma (B08).
- Text macros: `[player]`, `[player race]`, `[player rank]`, `[name]`.

## 5. Process

1. Read the brief, `voices.md` and the whole of `bans.yaml`.
2. Run the Find agents (section 3) and read their picks.
3. Write each topic's bands and the listener variants it needs, modelling shape and cadence on the picks.
4. Run `python3 .claude/skills/dialogue-write/lint.py LINES.txt --race <speaker race>`; fix every hit or note
   why it stands; then check each `review` ban by id.
5. Return the lines with the fact ids each states, and any fact requests.
