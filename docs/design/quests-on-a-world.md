# Putting a quest system onto a world

How to take a written quest system (its lines, quests, factions, people, lore and voice) and make it play in a world
someone else built, with small edits to that world. This is the recipe as it stands, kept current in the same commit
as any change to the method; the quest skills carry it step by step, and their map is
[quest-system](../../.claude/skills/quest-system/SKILL.md).

| Part | What | Carried by |
|---|---|---|
| 1 | Make the world the game's world | stack and plugin setup |
| 2 | Measure the world | census tools, `plugin.sh inspect` |
| 3 | Fit the story to the world | story-line, quest-write, quest-review, quest-playtest |
| 4 | Edit the world lightly | the quest form's placements; clean-up per host place |
| 5 | Build every quest from the one form | quest-build: the generic builder and scripts |
| 6 | Give everyone something to say | talk-write |
| 7 | Write the quest dialogue | dialogue-write, text-review, quest-playtest |
| 8 | Read back, integrate, deploy | quest-build |
| 9 | Hand it to the owner | owner checks |
| 10 | Run it as parallel work | lanes |

## 1. Make the world the game's world

- **A new game starts in the world**, through a start quest of our own that replaces the vanilla opening; character
  creation happens there.
- **The base game is quarantined:** its main quest, radiant and courier quests, world events and start-game quests
  that would reach the player are switched off (Start Game Enabled off, text stripped), listed in one shutdown file and
  read back. The world's own start-game quests are held back until the story releases them.
- **The world works as a world:** its map has a pan box from its measured land; its regions have music; its marker
  and cell names are spelled right; a cell has one name, so one that more than one quest uses takes a neutral name
  true of all of it in each record ("Dock Houses, Soulrest").
- **The mod stack** is a list of rows (source, version, why, credit), fetched and staged from the player's own copies;
  a mod's files are changed only at stage time on the player's copy, never committed.
- **Gameplay settings** (HUD, quest markers on the compass and the map, combat, movement) live in the plugin or the
  staged ini files, each with one owner check.

## 2. Measure the world

- **Census tables** of the loaded world, one row per thing with its form key and position: worldspaces, settlements
  and their cells, map markers, doors and interiors, placed people (race, class, factions, voice, status), walk-in
  shell buildings and the navmesh inside each, containers, flora, books, hostile placements, quests the world already
  has ([census](../research/bmv/census.md)).
- **Read the winner:** a record's live version is the last plugin in the load order that overrides it, never the
  master alone; every override copies the winner.
- **Ground truth for a spot:** a person stands on the winning navmesh (`plugin.sh inspect navnear`), or, where they
  never walk or fight, on a modelled floor with none; a thing rests on a modelled surface or the land (`plugin.sh
  surface`, `inspect cellat`, `cellgrid`). Every spot is measured, never taken from a record's guess.
- **What a place reads as** is what its built things show: a place is named for what it is only where something
  built clearly reads as that.

## 3. Fit the story to the world

- **The story first.** The main quest's and each faction's story is written whole inside the ceiling, each quest an
  outline set in places the game loads, and read on paper by fresh readers quest by quest until a round converges
  ([story-line](../../.claude/skills/story-line/SKILL.md)). The old quest system is its foundation: its premises,
  factions and spirit kept, its set pieces brought under the ceiling.
- **The ceiling** is the closed list in quest-system: stages moved by talk, taking, using, a death or another quest;
  people placed standing; nothing staged in view; anyone can die. An event the story needs has already happened and
  is found, is told, or happens where the player is not.
- **Each quest is a record** ([quest-write](../../.claude/skills/quest-write/SKILL.md)) that compiles to the quest
  form ([quest-form](quest-form.md)), routed to the design principles for its shape, with every person, thing, door
  and marker a measured placement. A fresh [quest-review](../../.claude/skills/quest-review/SKILL.md) reader judges
  it, and fresh paper players play the designed form ([quest-playtest](../../.claude/skills/quest-playtest/SKILL.md))
  before any dialogue is written.
- **Skill use.** Every step that asks something names the skills it uses, and each way through can go wrong as
  Skyrim's own systems make it go wrong (a check, a lock, a theft seen, a fight lost). Every main quest has at least
  two ways through on different skills, so any build can finish it; faction quests lean on the faction's own skills.
- **Grounding.** Every fact is a world record or a lore line; where the world and the lore disagree on something the
  player can see, the world wins. A speaker states only facts measured from where they stand.
- **A slice first:** fit the opening and a few lines that do not clash, play them, then the rest.

## 4. Edit the world lightly

- **What a quest may place** is in its form: people standing where they are needed (our base templated on a world
  base, our name, a fixed level), things on a measured surface or in a container (a lock level, a key, an owner),
  doors locked or unlocked. Nothing is built or moved for a quest; no structure, dock, hut or fire is added.
- **Clean-up per host place:** placements that break the setting or level with the player are disabled by override;
  each templated survivor gets a fixed level (nothing levelled against the player). A person given talk is kept.
- **Anyone can die:** no person of ours or of the world is made unkillable; each quest names those it cannot go on
  without.
- **Things of ours** only where no world or base-game item serves, each on an item whose model reads as what it is
  called; no new art, never a Nordic-specific model.
- **Traders:** a trader whose stock does not fit gets a vendor faction and chest of their own with a fixed stock.
- **Moving a quest spot** within its place to the nearest measured ground is a record edit, not a redesign.

## 5. Build every quest from the one form

Every quest is one form built by one generic builder into the same shape of records; no quest has code of its own
([quest-form](quest-form.md) "How a form becomes records"; the vocabulary and its engine shapes:
[blocks](blocks.md)). A handful of generic scripts carry out every result and are proven once in game by the owner's
walk of real quests chosen so that every operation any quest uses runs at least once. A step needing anything
outside the form is rewritten; a new block changes the form, the builder, the reader, the paper game and the block
test (the agents' diagnostic, never shipped: [block-test](block-test.md)) together, and is proven in game by the
walk of the first real quest that uses it. The gate (`make check`) compiles
and checks every quest record that fits the form, holds the ones that do not on a list that only shrinks, and walks
every compiled quest to a completed ending ([quest-build](../../.claude/skills/quest-build/SKILL.md)).

## 6. Give everyone something to say

Every person who can be talked to gets a name, a short backstory, a personality and their own true topics through
[talk-write](../../.claude/skills/talk-write/SKILL.md): facts from the loaded world, directions told the Morrowind way
by landmark, way, compass point and a word for how far (checked against the measured route), a cool first greeting
and warmth only with regard, a trader's services matching their stock, and rumours that point to a quest only while
it can start. A settlement's people do not repeat each other: each fact has one holder there, and anyone else points
to that holder. Everyone the player can walk up to is covered, a quest's people included.

## 7. Write the quest dialogue

Per speaker from the record's briefs with [dialogue-write](../../.claude/skills/dialogue-write/SKILL.md): matched
Morrowind lines as the model; the brief holding that speaker's sourced facts, the measured surroundings where they
stand, each line's stage window, check and result, and what the others in the same place say. Then
[text-review](../../.claude/skills/text-review/SKILL.md) by another agent: a style reader, and a truth reader who sets
each line beside its speaker's measured surroundings and lists every claim the facts do not support. Then the paper
players play the written quest. Lines live in the story data (`story/data/quest_lines/<code>.json` beside the record) and nowhere else. A line tells; a question is a
choice with a topic per reply; a line offers only what its result delivers, and a line that moves a stage never
refuses. A prompt is a sentence the player would say with what they know. Journal entries tell one step each, in the
first person and the past tense, only what the player has done; objectives are imperatives with a target.

## 8. Read back, integrate, deploy

[quest-build](../../.claude/skills/quest-build/SKILL.md) carries it: every form compiled and checked as a set; the
plugin seeded on the merged tree (a refused form fails the seed and is fixed in its record); the Spriggit round trip
clean; every built quest read back into its form and compared with the designed form to zero; the quest check and the
placement check at 0 failures; everyone placed has a line; the built quests played on paper; the plugin, its ini, its
start-quest list and the compiled scripts deployed to the play machine only when no stream is live. The builder never
plays the game.

## 9. Hand it to the owner

- **Owner checks:** the fewest checks that prove what was built (a new kind of result, one quest of each line, a
  death that shows the message), each in plain words with the place, what to do and what passing looks like, in
  [owner-walk-checks](../owner-walk-checks.md); ticked checks stay as the record.
- **A fix the owner passes teaches the recipe:** its class of mistake is written into the skill that produced it, as
  a plain instruction, and applied to every other quest before the next walk.
- **Looks are the owner's call:** a model's or a placement's look goes to the owner, never decided by a reviewer.
- **Rulings** are recorded the day they are made, in [owner-rulings](../owner-rulings.md) and, for quests and story,
  in [owner-bar](../../story/design/owner-bar.md).

## 10. Run it as parallel work

- **One lane per independent deliverable** (a line's story, a quest, a settlement's people, a tool change), in its
  own worktree, with a brief that names the inputs, what not to touch and a measurable acceptance.
- **The lead rules on gaps** at once (a rewrite inside the ceiling, a moved spot, a cut recorded in the review) so a
  lane never waits.
- **Shared things** (a person two quests use, a thing two forms place, form ids) are stated alike in both and agreed
  in the briefs; a lane that runs out of room commits and leaves a hand-off note.
- **Writers are started by the lane that orchestrates**, never through an intermediate driver agent: a
  `dialogue-writer` starts its own `corpus-find` agents, and an agent started by another agent cannot start agents.
- **Scratch** lives in a folder of the lane's own and is deleted by that lane.
- **Costs** are measured per quest and per run and reported with each check-in.
