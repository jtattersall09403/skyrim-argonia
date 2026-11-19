# The paper playtest

A quest is played in words by a fresh player who knows nothing of it, before anyone plays it in game. At every
milestone the player says what is going on, what they are expected to do next and what options they have; the
answers are graded against the record's information plan. It proves one thing: the quest gives the player what they
need, at the point they need it. It never judges whether the quest is good or fun, and the player plays as no
persona. How to run and grade it is the skill [quest-playtest](../../.claude/skills/quest-playtest/SKILL.md); this
file is how the tool works.

The tool (`tools/playtest`) is two deterministic games and one runner. The **record game** (`record.py`) plays a
quest record's YAML view directly, with no database (moment 1). The **form game** (`game.py`, `session.py`) plays
compiled quest forms ([quest-form](quest-form.md)) with the world database (moments 2 and 3). The player is a separate
headless Claude that can do nothing but send one of the games commands.

## What it does not test

Navigation, looks, combat, timing, or anything a record or form cannot say: a walk is one `go`, a fight is the
player's word `win` or `lose`, a lock is `win` or `fail` (with lockpicks held), and in the record game a skill or
gold check is the player's word `pass` or `fail`. The form game checks a skill against its character sheet.

A game plays what the record or form says, and nothing else. A condition term it does not know, a thing without a
name the player would see, a quest a form names that the run did not load: each stops the run with a harness error
naming it. Fix the cause in the record or form; never work round it in the game.

## The milestone gate

A **milestone** is every point where the journal changes: the quest starts, a stage is shown, an ending is reached
(`milestone.py`, shared by both games). The game shows the new entry and objective as a toast, then the four
questions:

1. What is going on? (who you work for, what has happened, why it matters, as far as you know)
2. What are you expected to do next, and where?
3. What options do you have for doing it? (the ways through you can see, and any choice in front of you)
4. Is there any word, name, person or thing you do not understand? Do you know how you could find out?

Until the player answers with `answer '1. ... 2. ... 3. ... 4. ...'` every other command is refused. One command that
moves several stages queues one milestone each. After the last ending's milestone the game asks for the player's
notes ("what you now know and have, as you would tell a friend picking up your save"), takes them with `answer` and
ends. A player who is stuck or out of commands gives the same notes with `end`.

## The record game (moment 1)

    python3 -m tools.playtest record <record.yaml> [--know <notes.md>] [--way <approach id>] [--choose <ending id>]
                                     [--after <earlier.yaml>[@<ending stage>] ...]
    python3 -m tools.playtest record <record.yaml> --check
    python3 -m tools.playtest record <record.yaml> --new          # a session for a hand to play with `do`

It reads the record's YAML view ([quest-record](../../.claude/skills/quest-write/quest-record.md)), a new-world record
at `newworld/story/quests/<line>/<code>.yaml` or an exported one, and nothing else. Its state is the current stage,
the things held, gold, flags, the dead, the topics heard and the place the player stands.

What it reads, by field:

| Record | The game |
|---|---|
| `start` (else the lowest stage) | the stage the game begins at; a `hidden` start waits for its successor like any stage |
| stage `place`, `journalText`, `hidden`, `objectives` (`objectiveText`, `target`) | where the player begins; the journal entry and toast; each target (refs separated by commas) is a quest marker, named |
| stage `successors`, `failForward` (`to`, `when`) | after every command, the current stage's successors then fail-forwards are tried in order; the first whose `when` holds is entered, and again from there |
| stage `onEnter`, `ending`, `endingId`; `endings[]` `world`, `rewards` | applied as the stage begins, each action as the player would see it (the actions table below) |
| `messages[]` `id`, `text` | the texts a `showMessage` names by id |
| stage `information` | the plan printed beside the player's answers in `milestones.md` |
| `topics[]` `id`, `label`, `person`, `kind`, `stages`, `when`, `intent`, `fallback` | a topic is open while the current stage is in its `stages` (all stages when it has none) and its `when` holds, a skill or gold check counting as passable; `say` shows its `intent` as what the person says; a `greeting` is said on `talk`; a `speaks-first` is said when the player arrives where the person stands |
| `placements[]` `ref`, `kind`, `name`, `anchor.place`, `anchor.room`, `container`, `carriedBy`, `count`, `lock`, `enabled`, `text`, `placeName`, `base` | who and what stands where: a ref stands at its anchor's place (a new-world place id; one with no place is wherever the player is), in its container, or on its carrier; an `anchor.room` (the room's name as its door shows it) makes the ref stand in that room, a place of its own inside the place, named by the `room` and reached by the doors whose `placeName` is that room; `enabled: false` hides it until `enableRef`; a stock item's `base.id` (`item.lockpick`) is what is held |
| `things[]` `name`, `text`; `cast[]` `name` | the names the game shows when a placement has none; a thing's words for `read` |
| `hooks[]` `thing`, `hook` (`activate` or `read`), `setsFlag` | `use` or `read` of the thing sets the flag, for a successor whose `when` is that `flag` |
| `terms[]` (`meets` beginning with the stage id) | listed under that stage's plan in `milestones.md` |

**`--after`.** `record <record.yaml> --after <earlier.yaml>[@<ending stage>] ...` loads each earlier record, in the
order given, and before the player starts plays it to a completed ending by a shortest path (to the named ending stage
with `@<stage>`; a `fail` ending is never chosen unless named), as an able character who passes every check and wins
every fight, applying every stage's `onEnter` and every ending's `world` and `rewards`. The path takes what a
condition or action wants held, sets the flags a condition reads, hears the topics a successor waits on, kills the
people a condition needs dead and presses each button of a choice. What carries into the played quest: things held,
gold, flags, counters, the dead, faction ranks, enabled and disabled refs, doors, topics heard and each earlier quest's
current stage (so `questStage` and `stageEverReached` on it hold); the played record's `startWhen`, when it has one, must
hold of that state. The earlier quests' journals are not shown to the player (what it knows comes from `--know`).
After each action in the played quest every loaded quest's successors that depend only on state (`questStage`,
`stageEverReached`, `hasItem`, `flag`, `counterAtLeast`, `npcAlive`) are tried and applied silently. A record that
cannot reach the ending asked for stops the run with a harness error saying so. The run's `run.json` names the
`after` records and the ending each reached.

**Names.** A person's name is its placement's `name`, else its cast row's; a thing's is its placement's, else its
thing row's; a door's is its `name`, else "Door to" its `placeName`; a stock item's is its id's last word. A place's
name is the `placeName` of a placement anchored there (not a door's, which names where it leads), else its id's last
part in capitals (`jal-veesa` is Jal-Veesa). A door leads to the place of that name.

**Conditions** played: `all`, `any`, `not`, `topicHeardFrom` [topic, person], `hasItem` [ref or item id, n],
`npcAlive`, `questStage` [quest, op, n], `stageEverReached`, `flag` [flag, value], `objectiveComplete`,
`counterAtLeast` [counter, n], `placeEntered` [place] (the player stands in that place: the block "an objective
with no marker until found", the arrival setting a stage), and `skillAtLeast`, `goldAtLeast` and `spellCastNear` [school, npc] (labelled
"(<School>)"), which hold by the player's word: a command that meets one with no word is undone
and the game asks for `pass` or `fail` at its end. `say` of a topic whose successors from the current stage all fail
on that word shows the topic's `fallback` and the topic is not heard.

**Actions** played, and what the player is shown (a message box is printed as `[Message box]` and its text):

| Action | The player sees |
|---|---|
| `giveItem`, `takeItem`, `giveGold`, `takeGold` | "Added: <name>", "Removed: <name>", "<n> gold added", "<n> gold removed" |
| `showMessage: <text or a messages id>` | a message box with the text |
| `fadeToBlack: true` | "The screen goes black." before the next message |
| `showChoice: {text, buttons: [{label, sets}]}` | a message box with numbered buttons; every command but `answer` is refused until `choose <label or number>`, which sets that stage |
| `endingScene: <id>`, siblings `messages: [texts]`, `before: [actions]` | `before` applied silently, then "The screen fades to black." and each message in order |
| `setPlayerName: true` | "What is your name?"; every command but `answer` is refused until `name <name>`, which `look` uses after |
| `killNpc: <npc>` | "<name> is dead." |
| `raiseSkill: [skill, n]` | "<Skill> increased by n." |
| `grantMapMarker: <ref or place>` | "Map marker added: <name>" |
| `setFactionRank: [faction, rank]` | "You are now <rank> of <faction>" |
| `makePeace`, `makeEnemy: <faction>` | "<faction> is now friendly to you", "<faction> is now hostile to you" |
| `grantAbility: [spell id, name]` | "Spell learned: <name>" |
| `giveHome: <ref or place>` | "<name> is now yours." |
| `addCounter: [counter, n]` | nothing (state a `counterAtLeast` reads) |
| `setDoorAccess: [door, open\|locked]` | the door's state on `look` ("(locked)", "(open)"); a locked door opens by key or pick |
| `enableRef`, `disableRef`, `setFlag`, `setStage`, `killRef`, `giveOwnership` | the ref appears or goes; the rest are silent |

Names of factions, ranks and places are the record's (placement, thing, cast, term, place) else the id's last word
capitalised.

**Commands**: `look` (the place by its name; the people, things and doors there, a quest marker marked, and where each
marker away from here points), `journal` (the entries so far, the objectives, each marker by name and place, what the
player carries and their gold), `talk <person>`, `say <topic or number> [pass|fail]`, `take <thing>` (from the
ground, an opened container, or a body), `use <thing or door>` (opens a container, unlocking it with its key held;
goes through a door; fires an `activate` hook, a locked door's too, before it says the door is locked), `read <thing>` (its `text`; fires a `read` hook), `fight <who>
win|lose` (a win leaves what they carried on the body; a loss changes nothing), `pick <lock> win|fail`, `pickpocket
<person> win|fail`, `go <place, person, thing or marker N>`, `choose <button label or number>` (only while a message box has buttons),
`name <name>` (only while the game asks it), `answer '<text>'`.

**`--check`** validates the record and prints one line per fault, exiting 1 on any: every successor and fail-forward
stage, objective target, topic person and stage, hook thing, condition and action ref exists; every condition term and every action term
is one the game plays (an unknown one is a fault naming the term and where it stands, so no message box is hidden);
a `showMessage` names a `messages` row or is a text, a `showChoice` button sets a stage, an `endingScene` has messages; `topicHeardFrom` names the topic's own person; every person, thing and door the player can see,
and every item a stage gives, has a name; every shown stage has `journalText` and `information` with `going`, `next`
and `ways` (an ending needs only `going`); every carrier channel names what exists, and has a channel other than
`ask:`; a `line:` carrier names a topic on the path. A **topic is on the path** when a successor or fail-forward of
any stage names it in `topicHeardFrom`, or it is a `greeting` or `speaks-first`; any other topic is one the player may
pick, a carrier of `ask:` only. A record with a fault is refused before a run starts, with the same lines.

`--way` and `--choose` add one sentence to the player's brief naming the way their build favours or the ending they
mean to take. `--know` is a file (or a text) the player is told they already know. The fixture
`tools/playtest/examples/satchel.yaml` shows every field the game reads.

## The form game (moments 2 and 3)

    python3 -m tools.playtest run --forms <dir|files> [--after <quest id>...] [--know <notes.md>] [--names <file>]
                                  [--at <ref id>] [--source built]

1. **After dialogue**: the compiled forms (`python3 -m tools.questform compile <quest>`) with the written lines.
2. **The built plugin**: the form read back (`plugin.sh questform-read <dir>`) after `python3 -m tools.questform diff
   <designed> <built>` shows no difference (results compare in order; a ref placed by an anchor is equal when built
   in the designed `at`'s cell within `PLACED_UNITS` of it).

`--at` is where the player stands when the game begins (default: the first marker's target). A later quest is played
with `--after` and the earlier quests' forms loaded beside it: the game first plays each named quest to a completed
ending by itself along a shortest path (the walker, `tools/playtest/walk.py`), so the player starts with the state,
items, gold and rank they leave; a quest no path completes stops the run with a harness error. `--know` is a file
(the `notes.md` of the passing run of the quest before) or a text. The plan beside each milestone is the stage's
`information` from the quest's record in the story database. By hand: `python3 -m tools.playtest new ...`, then
`do <session> "<command>" --think "..."`.

What the form game shows:

| Command | Shows |
|---|---|
| `look` | the place's name; the people near, each as who they are (an Argonian woman) and hostile or dead; the things on the ground and the containers; the doors; each locked one with its level, each owned one marked; two of one name told apart as `<name> 1` and `<name> 2` |
| `journal` | each quest's entries in order and its active objectives |
| `magic` | the spells, powers and abilities quests have taught, by the names the player sees |
| `map` | the player's position; each active marker: what it marks, where, how far, which way; the places known |
| `go <marker N, person, thing, place>` | arrival, roughly how far it was, then the `look`; into another interior only through a door of the run that is unlocked or whose key is held |
| `talk <person>` | who they are, the greeting (the first whose conditions hold), then the topics open now |
| `say <topic, answer or number>` | the spoken words (a prompt with a check carries its label: "(Persuade)", "(Alchemy)", "(20 gold)"; a failed check the record's own fallback words); what comes up; the topics now open, or a question's answers |
| `use <container, door or thing>` | a container's lock or contents (its key held opens it); through a door; a thing with `text` read; a body searched |
| `take <thing> [unseen\|seen]` | one thing from the ground, an opened container, a pocket or a body, counted by the form's item id; an owned thing asks `unseen` or `seen` |
| `pick <lock> win\|fail [unseen\|seen]` | needs lockpicks (a failure breaks one); a key-only lock cannot be picked; a level above `LOCK_SKILL` for the sheet's Lockpicking is beyond the player |
| `pickpocket <person>` | what they carry; `take` then takes one |
| `fight <who> win\|lose\|flee`, `wait` | what happens, as the game shows it |
| `answer '<text>'` | the milestone's answers, or the notes at the end |

Stages are by done, as the engine has them ([quest-form](quest-form.md)): a stage already done is never set again; a
trigger is open while its prerequisite is done, its stage is not and the quest's stage is below its `until`. An
ending closes every objective still shown. Regard stays between -4 and 4. A speaks-first line fires when the player
arrives near its speaker at its stage. A must-live person's death within the row's window fails the quest; a seen
crime says what Skyrim would do and goes no further. Items are held and matched by the form's item id.

A name comes from the form first (its `names`, `places` and `texts`, a ref's `name`, a door's `destination`), then
from a names file (`<quest>.names.json`), then from the world database; each id a names file had to give is listed in
`run.json` (`names_from_file`).

`python3 -m tools.playtest reach <forms>` (and `make reach` on every compiled quest, part of `make check`) proves,
for each quest and each way through the quests it waits on, that every stage and every ending is reached by one of
two characters with 1,000 gold, one able in every skill and a new one. A quest parked with its reason in
`tools/playtest/reach_owed.json` is skipped with a printed line; `reach --compiled --ratchet` takes off each parked
quest now wholly in reach. The walker (`walk.py`) acts on the walked quest's own references first, takes and uses
everything, and can fight anyone; a later quest starts once per distinct state the earlier ones can leave, as far as
its conditions can read it (`walk.Reads`), and one search serves every question asked of one state (`walk.Explorer`).

## The player

One brief for both games, built by `runner.py`: a new player who has played Skyrim, who wants to understand the story
and decide for themselves, who reads what people say and the journal, picks a topic when they want to know something,
answers the milestone questions honestly from what the game has shown them (saying plainly what they do not know),
and never tries to test or break the game. `--way`, `--choose` and `--know` add their sentences; nothing else
steers the player.

The player is `claude -p` with the model and effort of `.claude/agents/paper-player.md`'s frontmatter, run from a
new empty folder with its own system prompt, the project's setting sources only, no MCP servers and one tool: Bash
allowed only to run the run's `play` wrapper, a Python script that passes the player's words to the game as
arguments with no shell between (the words before `--think` are the one command; `play end '...'` stores notes).
Every command carries `--think`, the player's reason in their own words. `python3 -m tools.playtest probe` proves the
player cannot read the repo (its stream is kept in `story/playtests/probe/`). A silent player is killed at the run's
timeout; three attempts refused before a first command end the run, keeping the last attempt's folder. A form run
that stops without notes is asked four closing questions on what the player understood, as a separate final turn,
kept as `answers.md`.

## The run folder

`story/playtests/<quest id>/<utc>-<designed|written|built>/`, committed, never deleted:

| File | Holds |
|---|---|
| `milestones.md`, `milestones.json` | per milestone: the stage, its kind (start, stage, ending), the journal entry, the record's `information` going, next and ways (and the terms first met there) beside the player's four answers |
| `notes.md` | the player's notes at the end: what they knew and had |
| `transcript.jsonl` | one line per command: time, the player's think, the command, exactly what they saw, a state summary |
| `run.json` | quest, moment, model, effort, cost, minutes, way, choose, know file, the commands used, the stages played, how it ended, why the player stopped (`stopped`, `subtype`, `player_error`) |
| `stream.jsonl`, `brief.md` | the model's whole stream; the system prompt and first message the player got |
| `session.json` | the record or forms played, the world snapshot, the final state |

`python3 -m tools.playtest page` writes the owner's page (`out/playtest/index.html`, one self-contained file,
published as a private artifact): each quest, each run's milestones with the plan beside the answers, and its notes.
Runs kept from before milestones are counted, not shown. Make it again after new runs are kept.

Grading, whose each miss is, and the loop until a run passes are in
[quest-playtest](../../.claude/skills/quest-playtest/SKILL.md) §4 to §6.
