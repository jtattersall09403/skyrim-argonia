---
name: quest-write
description: Write or rework one Argonia quest as a record in the story database (truth, cast, things, placements, stages, objectives, lines, who must live) that compiles to the quest form inside the ceiling, routed to the design principles for its shape and line, then build its dialogue briefs. Use for each quest of a line from its story-line outline, for a minor quest from a premise, and to rework a quest after review or a paper playtest.
---

# Writing a quest

Before this: [quest-system](../quest-system/SKILL.md) (the ceiling, the order of work) and, for a quest of a line,
its outline from [story-line](../story-line/SKILL.md). After this: [quest-review](../quest-review/SKILL.md), then
[quest-playtest](../quest-playtest/SKILL.md) on the designed form, then the briefs for
[dialogue-write](../dialogue-write/SKILL.md).

A quest is one **record**: rows in the story database (`story/data`), the only source of truth, edited through its
YAML view ([quest-record.md](quest-record.md)) and compiled to the quest form
([quest-form](../../../docs/design/quest-form.md)), which the generic builder turns into the game. Read the database
only through `python3 -m tools.argonia_world.db query "SELECT ..."` or `db show <table> <id>`. Worked records at the
ceiling, read from the database so they are current: `python3 -m tools.argonia_world.quest_record export
quest.main.mq03` (a main quest: two ways through by Speech, Lockpicking, Pickpocket and Alchemy) and `... export
quest.local.lq25` (a local predator quest: a fight by three skills, a twist and a choice between people).

One recipe serves every kind of quest: the form is the same for all, and what differs by kind (a theft, a hunt, a
dispute, an induction) is what the drama turns on, which the shape routing in section 2 supplies.

## 1. Start from the outline, or from the foundation

- **A quest of a line** starts from its outline in `story/design/quests/lines/<line>.md`: its people, places, things,
  ways through, stages, choice and endings are given. Build them; invent nothing the outline does not give. A gap goes
  back to the story's author (story-line §5).
- **A minor quest with a row** (most places already hold quests as premises: `db query "SELECT id, code, premise
  FROM quest WHERE settlement = '<place id>'"`) starts from it: `python3 -m tools.argonia_world.quest_record export
  <quest id> -o <quest>.yaml`, its entry in `story/design/quests/50-side-quests.md`, its row in
  `story/design/quests/review/walk6-ceiling.md` where it has one. Keep its premise, cast and beats.
- **A new premise** with no row: export a small worked quest of the same group (`quest.local.lq25`) as the shape to
  fill, and give it a new id and code. The code is two capitals and two digits: take the prefix the place's quests
  already use (`db query "SELECT code FROM quest WHERE settlement = '<place id>' ORDER BY code"`; the longest run
  of one prefix) and the next number free in the whole `quest` table (`... WHERE code = '<code>'` returns nothing); a
  local quest's id is `quest.local.<code in lower case>`, its `line` `quest.line.local`. A code or id is never
  reused (look again just before the commit, since other lanes take codes too); the title and every name the
  quest adds are checked against
  `story/design/quests/86-never-reuse-names.md`.
- **Shapes**: the primary shape is what the player's central act is (a cure to find is CONTAMINATION, a quarrel to
  settle is DISPUTE); up to two more are secondary, from the sixteen in `story/design/quests/index/README.md`.
- **`foundation`** says in the present tense what the quest is built on (the outline, the old design, or the premise
  alone) and what it keeps.
- **Read the world it stands on**: the place's facts (`fact` by `place_id`, in `ord` order), its people
  (`place_person`, `npc`, `npc_faction`), their stance (`stance*`), the culture sheets they chain (`culture_*`), the
  other quests at the place and its neighbours (`quest` by `settlement`), the lore in `story/lore/` and
  [province-vibe](../../../story/design/province-vibe.md). A room without a load door is a walk-in building from
  `bmv_shell` (by `settlement`, class A first).
- **Cast**: a recurring person from `story/design/quests/36-cast-roster.md` under `35-cast.md`; a placed person is
  an `npc` row; a person in neither, nor placed by Black Marsh & Valenwood, is an `invented` persona to add.
- **Novelty**: scan `story/design/quests/index/coverage.md` and the other quests at the place. The quest collides if it shares its primary shape with
  a quest of the same region packet, faction line, reversal or resolution; then differentiate it, merge it or drop it.
  Declare `touches` (shared people, places, numbers, things). No primary shape over about a fifth of a line, nor in
  consecutive larger quests (a departure goes in `budgetExceptions` with its reason).

## 2. Route to the principles

Read [shapes.yaml](shapes.yaml): always [principles/general.md](principles/general.md) and
[principles/actions.md](principles/actions.md), the group's file, each shape's file (primary first). The principle
files are the quest design research (`docs/research/writing/`) and the owner's bar distilled at the ceiling; each
principle ends with its source tag (general.md holds the key). Every principle binds this record; a minor quest
reads only the "Local quests" bullet under "Line types" in questlines.md.

| File | What it holds |
|---|---|
| `principles/general.md` | what a quest may use and how each dramatic job is done at the ceiling; the owner's bar as craft; truth, trail, world, choices and rewards |
| `principles/actions.md` | the player's skills, patterns of uses, the action plan, the profiles |
| `principles/questlines.md` | a whole line: how it holds together, what carries between quests |
| `principles/investigation.md` | MURDER, MISSING, RECKONING, and a THEFT or FRAUD to solve |
| `principles/crime-and-deceit.md` | THEFT, FRAUD, SMUGGLING |
| `principles/social.md` | DISPUTE, NEGOTIATION, SUCCESSION, BONDAGE |
| `principles/threat-and-journey.md` | PREDATOR, CONTAMINATION, EXPEDITION |
| `principles/otherworldly.md` | HAUNTING, RITE, WONDER, Daedric and oddity quests |

Each shape names the `shapeData` sections the record holds (`shapes.yaml`), each described under "Record additions"
in its file: what the drama turns on (a theft's prize, where it is kept and who carries the key, the ways in by
skill, what goes wrong, who pays afterwards).

## 3. Design at the ceiling

Every step uses only what [quest-system](../quest-system/SKILL.md) lists; a step that needs more is rewritten with
general.md's table of dramatic jobs, never scripted.

1. **Skills win the steps.** Each stage that asks something of the player names the skills it uses (the list is
   general.md's principle 1); climbing and swimming are movement, not skills. A way
   through can go wrong as Skyrim's own systems make it go wrong: a check with a fixed threshold, a lock level, a
   theft or pickpocket the crime system sees, a fight that can be lost. A main quest has at least two ways through on
   different skills; a faction quest leans on its faction's skills (`profiles.yaml`). Hearing the task, handing over
   and reporting carry no check; every way forward a check guards has at least one other way on a different skill, a
   price or a fight (general.md principle 20 aims at three), and the refusal line names it. A failed check may stay
   closed until the player returns stronger.
1b. **How the quest begins.** One of three ways. *A giver*: the record's `start` is 0, stage 0 is `hidden`, and the
   giver's opening topic, open at stage 0 and gated on the giver alive, sets the first shown stage (the build makes
   the quest run from a new game, waiting at stage 0, and starts it with the game; nothing is listed by hand).
   *Another quest*: `startWhen` names that quest's stage. *Speaking first*: the giver's opening line is the quest's
   one speaks-first line (rule 8). The settlement's talkers point at a quest that can start through their rumours,
   which the build gates on the quest's start window.
2. **A stage moves only by an allowed trigger**: a line the player picks, a named thing taken, a named thing used or
   read, a named person dying, another quest's stage. To have the player find a place, put a named thing there to
   use, read or take, or a person there to speak to. A person who must be elsewhere next is switched off while the
   player is in another cell and on where they are found, and their line says they went ahead.
3. **A hand-in is gated on the thing held**, however it was got. Taking a thing writes only a journal note; a thing
   held before its step opens moves the quest as the step begins (`set_stage` `if_held`).
4. **Several ways at once: one working stage.** Where the player may do a quest's parts in any order, the quest sits
   at one working stage; each part's result is a stored number, a thing held or a person dead, never a stage of its
   own; the lines that carry results to the person waiting for them set the stages, in a stated order where two
   results are true at once.
5. **Who must live.** Name only the people the quest cannot go on without: their death fails it with its own journal
   entry, over the window of stages where it matters (from the first shown stage at the earliest); a main or faction
   quest also shows its kind's message, a minor quest does not. Every other line reads sensibly with any named person
   dead, gated on who is alive; where either of two people alive is enough, neither is a who-must-live row.
6. **Deaths.** A death moves the quest only for a person the player is asked to fight (`hostile`, at a fixed level,
   with a reward in proportion), a who-must-live person, or a killing marked the player's choice. A confrontation is a
   line whose result turns its speaker hostile, or a person placed hostile.
7. **Switching a person or thing on or off** is the result of a line, a take or a use only, for a reference in
   an interior other than the speaker's or the thing's, or across the line between interior and exterior, or, both
   outdoors, at least 18,000 units from it (a town's streets are one exterior: a person who "went ahead" waits in an
   interior); nothing appears or vanishes in view.
8. **One person may speak first**: placed a step from the door the player arrives through, they greet the player
   there (the quest's one force-greet), with a marker on them and the same line open as a topic.
9. **Every check is its own line with its fallback**: the line that passes, then the line said when the check fails,
   gated on everything but the check; a refusal names what would change it. The compiler adds the check's label to
   the prompt (`(Persuade)`, `(Alchemy)`, `(20 gold)`); a label written by hand must be that one, and never a
   threshold.
10. **One stage, one step.** Every shown stage has an objective with one or more targets switched on at it, and the
    entry says, first person and past tense, what the player has just done and "I'm to ..." for the one step owed,
    with the place by a name the player can see; never a later step, never an event that did not happen. Objectives
    are imperatives with a full stop ("Speak to Wuleen-Sei in the barge's hold.").
11. **Placements are measured from the world.** Every person, thing, door and marker the quest names is a
    `placements` row: an existing reference by its form key from the census, or a new one with its base, its anchor
    and an `at` measured with `bash tools/ArgoniaPlugin/plugin.sh inspect navnear:<x>:<y>:<z>`, `near:...`,
    `cellrefs:<cell>`, `cellat:<cell>:<x>,<y>` or `cellgrid:...` (a person on navmesh, a thing on a modelled surface).
    A body to be found is one the world already holds (an existing reference from the census's corpses) or a
    person the quest places hostile and the player kills; a dead stranger the story needs is told, and what the
    player examines is a thing at the spot (a satchel, a cut net, a note) to take or read. A new thing is a
    `template_item` on an item whose model reads as what it is called (a lidded jar, a bucket, a
    necklace; never a Nordic-specific model: `inspect items:<regex>` finds one). A container carries its lock level,
    key and owner where the play needs them; a person carries a thing to be pickpocketed (`carriedBy`). Where an owner
    means to give a container's contents, the giving line's stage carries `giveOwnership` of it.
12. **True of the built world.** Every place, person and thing the record or a line names is a placement or stands
    there in the census; a place is called what its building reads as; a person's work is work they are seen doing.
    When a host, prop or person is cut or moved, search the quest's rows and lines for its nouns and change every hit
    in the same commit.
13. **Simple and active.** At most two real choices and three endings; about 8 stages for a middle-sized quest, 12
    for a large one. Action, danger and discovery drive it; law and procedure are background, never the climax.

## 4. Write the record in order

The sections are those of [quest-record.md](quest-record.md) §2.

1. **Action plan**: `python3 .claude/skills/quest-write/action_plan.py --profile <line key> --shapes <SHAPE,...>
   --band <D0..D5> --line <dir of the line's records>` (the band is the place's danger, D0 a safe town to D5 the
   worst country, `story/design/quests/20-world-provisions.md`; for a first or minor quest `--line` is an empty
   folder); drop any proposed use the place cannot host (a creature it has no ground for), then choose or adapt
   the uses the quest is built round
   ([skill-uses.yaml](skill-uses.yaml), weighted by [profiles.yaml](profiles.yaml)) and the `centrepiece` tag.
2. **Premise** and **truth**: numbered physical events, written so the planned actions follow from them; then the
   plausibility pass, person by person (change the truth, never the person).
3. **Facts** the truth creates, each `from` a truth event, a place fact or a culture-sheet entry.
4. **Cast and knowledge** (registry ids; `persona` only for what the registry lacks).
5. **Things** and **placements** (§3.11).
6. **Conclusions and clues**: three clues per conclusion, in two forms at least.
7. **`shapeData`** for each shape.
8. **Stages**: journal, objectives with targets, `successors` and `failForward` with their gates, `onEnter`,
   `ending`, `actions` or `approaches`, `learns`, `directions`, `hidden` for the stage the quest waits at before its
   opening line. Conditions and actions only in the terms the compiler accepts (quest-record.md §intro; a use or a
   read is a `thing_hook` row there); a term the compiler refuses is outside the ceiling.
9. **Endings**: two or more with real costs, each saying where the player will see it; fixed rewards.
10. **Journal text** is each stage's `journalText` in the record, its one home; a rewrite from the journal brief is
    written back there.
11. **Topics**, per person and stage window, in the order the player meets them:
    - the prompt is a sentence the player would say with only the names and facts they have then, never a bare label;
    - a line that sets a stage the journal relies on never refuses;
    - a question the speaker asks has one answer topic per reply; otherwise the speaker tells;
    - every person the quest places answers "Who are you?" in each window the player can reach them, true of where
      they stand then; everyone an ending leaves standing has a greeting for that ending;
    - within one place and stage window a fact has one speaker; warm and cool wordings only after a regard change.

## 5. Check it against the lore and the vibe

Every lore source read goes in `recordSources.lore` (`"<path> §<section>"`); every claim's verdict in `review.findings`
as `id: L<n>`, `severity: lore`, with `answer` `sourced: <file §>`, `gap: <QA id>` or `changed: <what to>`.

1. **Lore.** Every person, role, place, institution, object, custom, belief and price against `story/lore/` (first
   `extrapolation/argonia-4e201-state.md`, `settlement-register.md`, `gap-register.md`) and province-vibe. Each is
   sourced, a gap (the least inventive reading of what is sourced, added as a `QA<n>` row under the gap register's
   "Quest assumptions", status `ASSUMED`; take the next free id and re-read before commit), or changed.
2. **Society.** Each role exists in this settlement and culture in 4E 201 (province-vibe §3 and §4); information,
   authority, trade and debt move as §5 says for the place.
3. **Motifs only where §9 puts them.** Couriers, letters, ledgers, tallies, clerks, officials, permits, papers, fines
   and prisons appear only where province-vibe §9 places them, and the `L<n>` entry says where; no stage is won by
   delivering, filing, counting or reading a record.

## 6. The writer's own loop

Run until all pass, before anyone else reads the quest:

1. `python3 -m tools.argonia_world.quest_record import <quest>.yaml --dry-run`, then without `--dry-run`. It refuses
   the whole record on any unknown field, wrong type, dangling key or unknown lookup value.
2. `python3 -m tools.questform compile <quest id> --out out/<lane>/questform`: each refused term is printed with where
   it stands and a hint; re-author it, never work round it.
3. `python3 -m tools.questform check out/<lane>/questform/<quest id>.json` (and `check --set` with the quests it
   chains to): each failed rule is one line naming the rule ([quest-form](../../../docs/design/quest-form.md) "The
   rules" says what each means).
4. `python3 -m tools.playtest reach out/<lane>/questform/<quest id>.json` (with the forms of the quests it waits on):
   every stage and ending reached.
5. `python3 -m tools.argonia_world.adaptation_check | grep <quest id>` and `make questtext`: no line for this
   quest (the hidden stage 0 a quest waits at is expected).
6. A quest listed in `story/data/questform_owed.json` that now fits: `python3 -m tools.questform owed --write`.

## 7. Hand on

1. [quest-review](../quest-review/SKILL.md) by a `quest-reviewer` agent that has not seen your reasoning. Answer
   every finding in the record's `review` (fixed, or why it stands); set `recordStatus: reviewed`.
2. [quest-playtest](../quest-playtest/SKILL.md), moment 1, on the designed form; its findings come back here.
3. The briefs: `python3 .claude/skills/quest-write/brief.py <quest id> <out dir>` writes one brief per person with
   topics in the record (every person the quest places has at least "Who are you?") and a journal brief. It writes nothing while the record is not whole
   (a missing reference, vocabulary term, `shapeData` section or ending, a step with no skill, a form that fails its
   rules). Then [dialogue-write](../dialogue-write/SKILL.md) per brief, by one `dialogue-writer` agent per person
   that this lane starts itself (a writer starts its own find agents, which an agent started through another cannot).
   The lane puts the returned lines into the quest's lines file (quest-record.md "The lines file") and compiles
   again: the lines replace the gists. A writer's fact request comes back here: add the fact to the record and rebuild the briefs.
4. **A fact lives in one row; a cut is a search.** To change or cut a thing, `grep -rn` its id, name and words over
   `story/data/` and change every hit in the same commit.
