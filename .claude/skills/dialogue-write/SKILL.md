---
name: dialogue-write
description: Write topic dialogue in Morrowind's voice, built as Skyrim topics, for one Argonia NPC of any race from a generated speaker brief, using matched Morrowind lines as the model. Use when authoring greetings, topic answers, quest lines or journal text for a person.
---

# Writing dialogue for one person

The goal: lines that read as if they were Morrowind's, about our people
and places in Black Marsh & Valenwood's (BM&V's) world; the lines become Creation Kit dialogue records on top of BM&V. Bans are in `bans.yaml`, voice evidence in
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

The imported written lines (`dialogue_line` rows) are reference only and never models; the
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
- **Player faction and rank:** same faction, greet by the rank's name written out and share members' knowledge; rival
  faction, colder and less on faction topics; otherwise the default.
- **Player crime here:** the person's crime greeting replaces the normal one.

## 3. Find agents

Every run finds its models first, a rewrite of one line included. The corpus
(`$ARGONIA_PRIVATE/dialogue/morrowind/morrowind-full.json`, never committed; `ARGONIA_PRIVATE` is
`/home/ubuntu/argonia-private`) is split by topic kind into `groups/` by `corpus_split.py` (run it once if the
folder is missing). Spawn one `corpus-find` agent per group the brief's topics touch, in parallel, each given its
group file, the speaker (race, sex, role, chattiness, friendliness), its topics with their bands, and its report
path `$ARGONIA_PRIVATE/dialogue/morrowind/finds/<speaker ref6 or brief name>/<group>.txt`. The groups: greetings
(the speaker's race file) and refusals; trade and service; place and directions (with each route's shape from the
brief); rumours and advice; creatures and danger; quest arcs (offer, detail, directions, reminder, success,
failure); topics in general. Each returns up to four lines per topic and wording. Check every id and quote against
the corpus before using it, and name the ids each topic is modelled on in the return. `talk_brief.py load`
refuses a person with no finds. Never paste Morrowind lines into the repo.

## 4. Voice rules

- **A line tells; a question is a choice.** A speaker asks the player something ("What name?", "Did you see?", "Give
  me a reason", "Are you crossing?") only when the brief lists the reply topics. With none, the speaker says what
  they know or what they need, as a statement.
- **A line promises only what the brief's `sets` delivers.** "Here is", "take", "I will follow", "I will meet you
  there", "come back when I know you" are written only where the brief names the item given, the package, the place
  or the way to earn it.
- **A line that advances a stage never refuses.** When its fragment sets a stage or a flag the journal then relies
  on, every wording of the line agrees to what the fragment does.
- **A line is true wherever its window lets it be said.** The brief gives each line's place, first and last stage and
  conditions. Write nothing that is false at the window's far end, in the fallback's other cases (a "not now" line
  covers every reason the pass line failed), or once the clock moves ("four hours ago"). Once a quest has ended, no
  line offers or describes its task; only the greeting for that ending speaks of it.
- **The prompt is the player's sentence.** A full sentence the player would say with what the brief lists under "the
  player already knows", never a bare label ("the boat"; "Did you see who came to the tree?" is a prompt); a cost or
  check is in it ("(Persuade)", "(10 gold)").
- **People by the name the game shows.** A person the player can meet is named as their base is named, with the role
  beside it once; pronouns follow the brief's sex for that person.
- **One speaker, one fact, per place.** The brief lists what the others in the same place and stage window say. Do
  not restate it; give this speaker's own fact or their view of it in one clause.
- **Wordings by regard.** The default wording is written for every line. A warm (regard 1 or more) and a cool (below
  0) wording are written only where the brief marks the line "after a regard change". All three wordings state the
  same facts and make the same commitment as the line's `sets`; only manner and length differ. Length follows
  warmth: cool is short, only warm is chatty.
- **Directions as Morrowind gives them.** A way is told by what the player will see: named places, the path or
  shore and where it goes, bridges, buildings and ruins, with compass points in words (B13: never a count of
  paces, steps or metres). How far is a word from the brief's distance band: "just" (in sight, under 60 m), "a
  short way" or "not far" (under 200 m), "a fair way" (under 600 m), "a long walk" (under 2 km), "far" beyond; or
  it is the landmark itself ("until you reach the wreck", "just past the burnt-out house"). Most often a place is
  placed beside another the player knows ("it is just north of the dock"); a route is two to four steps in order,
  each ending at its landmark and its side, and a longer way names the place to ask at next. A speaker may hedge
  ("I think", "they say") or warn of a miss ("if you reach the water, you have gone too far") as their personality
  would. Never add a landmark, change a heading, skip a turn or make a way longer or shorter than its word;
  `talk_check` reads compass points, landmark order and distance words back against the measured route.
- **A refusal says what would change it** (B09): the skill, the thing to bring or the price.
- **Plain and explicit:** who did what and why, in plain clauses (B05); every quest line can be acted on.
- **British English** spelling and punctuation, no serial comma (B08); the style guide
  (`../../../story/design/text/style-guide.md`) and its culture registers bind every line.
- No text macros: Skyrim prints `[player]`, `[player race]` and the like as written. Address the player by a word the
  speaker would use; where the address changes with the player's race, write a variant line for that race (it is built
  as its own line, gated on the player's race).

## 5. Process

1. Read the brief, `voices.md` and the whole of `bans.yaml`.
2. Run the Find agents (section 3) and read their picks.
3. Write each topic's wordings and the listener variants it needs, modelling shape and cadence on the picks. Give
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
