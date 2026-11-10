---
name: dialogue-write
description: Write Morrowind-style topic dialogue for one Argonia NPC of any race from a generated speaker brief, using matched Morrowind lines as the model. Use when authoring greetings, topic answers, quest lines or journal text for a person.
---

# Writing dialogue for one person

The goal: lines that read as if they were Morrowind's, about our people
and places in Black Marsh & Valenwood's (BM&V's) world; the lines become Creation Kit dialogue records on top of BM&V. New bans go in `bans.yaml`, new voice evidence in
`voices.md`, deliberate echoes in `echoes.yaml`.

## 1. The brief

The writer works only from a brief built from a record, never from a hand-written summary:

- **Quest topics and journal text:** `../quest-write/brief.py <quest id> OUT_DIR` builds one brief per person,
  one per quest person with no topic of their own (their "Who are you?" reply in `quest_people.json`) and one
  journal brief, from the quest record's rows.
- **Settlement talk:** `talk_brief.py brief --talker REF --out BRIEF.md` (the talk-write skill).
- **Place topics** (the person's topics in the place record: the place, its work, people, danger,
  directions, rumours, their role): `python3 .claude/skills/dialogue-write/place_brief.py --person <npc id>
  --out BRIEF.md`. It reads only the story data (`story/data`, through `tools/argonia_world/db.py`): the person's `npc` row, the `stance` rows
  and the culture sheets they chain, the place's `fact` rows and people (`place_person`) and
  the `topic` rows, and says when the talk can happen (a hostile place's flips).

A brief holds: what the player can see (race, sex, look, outfit); what they cannot (role, services,
factions, wants, fears); the voice card and the stance voice (chatter, contraction rate, address term, quirk,
never-mentions); the culture chain; the others the player may be sent to; the things lines may name, by id;
and per topic the intent or opinion, the facts it may state and hide, the speaker's knowledge, the links it
grants, and what the player already knows.

The imported written lines (`dialogue_line` rows) are reference only and never models (decision 0024 §7); the
facts (`fact`), topics (`topic`), glossary (`glossary_term`) and culture sheets are the source. Read them only
through the database (`python3 -m tools.argonia_world.db query "SELECT ..."`).

**One teller per fact in one place and stretch of play.** The player hears everyone in a window one after another:
a quest stage at its place (every quest topic live at that stage, every quest person whose stage window covers it,
the talkers of that settlement) or a settlement (all its talkers). `tools/argonia_world/echoes.py` builds the
windows from the data, and every brief generator gives each fact of a window to one owner: the speaker of the first
topic that states it, in the order the player meets them (the quest record's topic order; quest people; talkers).
The brief's **Already said near you** lists who else speaks in the person's windows, what they answer and which
facts they own; a fact this person shares with an owner is listed under **Facts you leave to their owner** (in a
quest brief, under the topic as "Said by its owner near you"; in a talk brief, a pointer fact "Ask <owner> about
it"). The writer says what only this person would say (their work, their stake, what they saw) and, where the player
needs the fact, points to the owner in a few words ("ask Wuleen-Sei about the months"), never tells it and never
reuses a neighbour's wording. Every person still answers every topic.

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

Split the corpus (`$ARGONIA_PRIVATE/dialogue/morrowind/morrowind-full.json`, never committed) **by topic kind**, one
`corpus-find` agent per group, matched on the speaker's race and sex: greetings and refusals; trade and
service; place and directions; rumours and advice; creatures and danger; quest arcs (offer, detail,
directions, reminder, success, failure). Each returns up to four lines per topic and band. Check every id
and quote against the corpus before using it. Never paste Morrowind lines into the repo.

## 4. Voice rules

- **Bands** (1.3's three, by disposition): `low` below 30, `words` 30 to 69, `high` 70 and over. Length follows
  warmth: the low band is short; only the high band is chatty.
- **Essential topics have no refusal band** (old 0145): the low band is grudging but still
  gives what the quest needs.
- **Held-back information says so** (B09), so the player knows to raise disposition.
- **Plain and explicit:** who did what and why, in plain clauses (B05); every quest line can be acted on.
- **British English** spelling and punctuation, no serial comma (B08); the style guide
  (`../../../story/design/text/style-guide.md`) and its culture registers bind every line.
- No text macros: Skyrim prints `[player]`, `[player race]` and the like as written. Address the player by a word the
  speaker would use; where the address changes with the player's race, write a variant line for that race (it is built
  as its own line, gated on the player's race).

## 5. Process

1. Read the brief, `voices.md` and the whole of `bans.yaml`.
2. Run the Find agents (section 3) and read their picks.
3. Write each topic's bands and the listener variants it needs, modelling shape and cadence on the picks. Give
   every act to a person: a roll, a hold, a town, a ship or a law never hears, wants, adds, knows or decides (B01);
   name who does it, or state the plain fact.
4. Run `python3 .claude/skills/dialogue-write/lint.py LINES.txt --race <speaker race>` (required; exit 1 on
   any hit, 0 when clean; a `warn` hit such as B10 never fails the run); fix every hit or note why it stands, and
   justify each B10 warning against `story/design/province-vibe.md` §9 or reword it; then check each `review`
   ban by id.
5. Once the lines are in their file (quest_lines JSON, quest_people.json with each reply's `facts`, or loaded talk
   lines), run `python3 -m tools.argonia_world.echoes check` (exit 1 on any cluster): two different speakers of one
   window stating one fact id or sharing a run of seven words (four of them more than glue, numbers and compass
   points); one speaker saying such a run in two topics; two greetings opening with the same words. Reword the later
   line; a person's greeting opens in their own way, never a formula the settlement shares. A deliberate echo (a quest rumour two talkers tell so the
   player meets the hook) is named in `echoes.yaml` with its speakers and why.
6. Return the lines with the fact ids each states, and any fact requests.
