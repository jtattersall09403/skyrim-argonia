# Putting a quest system onto a world

How to take a written quest system (its lines, quests, factions, people, lore and voice) and make it play in a world
someone else built, with small edits to that world. This is the recipe as it stands, kept current in the same commit
as any change to the method; the skills are cut from it (PLAN Phase 4b). It states how to do the work, never how the
method was arrived at.

The work runs in this order; each part names the skill or tool that carries it.

| Part | What | Carried by |
|---|---|---|
| 1 | Make the world the game's world | stack and plugin setup |
| 2 | Measure the world | census tools |
| 3 | Fit the quest system to the world | adaptation, quest-write, quest-review |
| 4 | Edit the world lightly | world-edit builders |
| 5 | Build every quest from proven blocks | the quest kit, Papyrus |
| 6 | Give everyone something to say | talk-write |
| 7 | Write the quest dialogue | dialogue-write, text-review |
| 8 | Read back, integrate, deploy | read-backs, plugin.sh, deploy |
| 9 | Hand it to the owner | owner checks, rulings |
| 10 | Run it as parallel work | lanes, briefs, landing |

## 1. Make the world the game's world

- **A new game starts in the world**, through a start quest of our own that replaces the vanilla opening; character
  creation happens there.
- **The base game is quarantined:** its main quest, radiant and courier quests, world events and start-game quests
  that would reach the player are switched off (Start Game Enabled off, text stripped), listed in one shutdown file and
  read back. The world's own start-game quests are held back until the story releases them.
- **The world works as a world:** its map has a pan box from its measured land and terrain-detail settings; its
  regions or worldspaces have music; its marker and cell names are spelled right.
- **The mod stack** is a list of rows (source, version, why, credit), fetched and staged from the player's own copies;
  a mod's files are changed only at stage time on the player's copy (an animation trimmed, an ini set), never
  committed; nothing the player does not own is committed.
- **Gameplay settings** (HUD, combat, movement, regeneration) live in the plugin or the staged ini files, each with one
  owner check.

## 2. Measure the world

- **Census tables** of the loaded world, one row per thing with its form key and position: worldspaces, settlements
  and their cells, map markers, doors and interiors, placed people (race, class, factions, voice, status: silent,
  service, hostile, corpse), walk-in shell buildings and the navmesh inside each, containers, flora and ingredients,
  books, corpses, hostile placements, quests the world already has.
- **Read the winner:** a record's live version is the last plugin in the load order that overrides it, never the
  master alone; every override copies the winner.
- **Ground truth for placement:** a spot is usable for people only where the winning navmesh covers it, and for things
  only on a modelled surface (the surface reader gives the mesh top). A cell with no navmesh hosts no people.
- **The census is complete** when a miner and a critical reviewer agree nothing in the world is unrecorded that the
  quests could need.

## 3. Fit the quest system to the world

- **Inputs:** the quest system as data (lines, quests, stages, cast, factions, places, items), the lore dossiers and
  the agreed extrapolation, the province's vibe (the mood every quest serves), the naming rules and the voice cards.
- **The spirit of each line first:** for every line and quest, what it promises the player, its emotional core and
  signature beats, and which details are free to change.
- **Capacity:** what each settlement, region and dungeon can host (people, rooms, seats, danger band, travel links).
- **One allocation for the whole system:** each line's seat and hubs, each quest's host places and cast, chosen
  together so no two lines compete for a place or person unless the design wants them to meet; danger rises along each
  line in fixed bands; travel between a line's places fits the world's roads, boats and doors.
- **One ledger:** per quest a verdict (keep, adapt, merge, drop), its adapted premise and host places; per world edit
  one row, linked to every quest that needs it. A checker in the gate fails a quest on a place that does not exist,
  an edit one quest undoes for another, a broken prerequisite graph, a place over capacity, a levelled placement in a
  host without a clean-up, a call that cites no lore.
- **Each quest is written as a record** with `quest-write` (hidden truth, cast knowledge, things, clues, actions,
  stages, endings, topics) and reviewed by a fresh `quest-review` reader; the loop ends when a full round raises
  nothing blocking. Each thing the player must do next is its own stage, entry, objective and target; a new
  character can always go on along the main quest; every main quest offers at least two ways through with
  different named skills; faction quests use the faction's own skills; everything is checked against the lore and
  the vibe.
- **Every sequence the player must finish keeps them in it:** an opening happens where the player already is, with no
  long unescorted walk; a person the player is told to follow sets off only once the player can see them and walks
  one navmesh island.
- **A check that can fail is never on the only way forward**, and never on a hand-over from an ally (a task given or
  a report taken).
- **A slice first:** fit the opening act and a few lines that do not clash, play them, then the rest.

**Skill use.** Quests are played with the game's own skills, named in the record:
- Every stage that asks the player to do something names the skill it uses (One-Handed, Two-Handed, Archery, Block,
  Destruction, Alteration, Illusion, Conjuration, Restoration, Alchemy, Sneak, Lockpicking, Pickpocket, Speech, and the
  stack's added schools). Climbing and swimming are movement, not skills.
- Every main quest offers at least two ways through using different skills, so different builds can finish it.
  Faction quests lean on the faction's own skills.
- A skill route can fail: a Speech check has a threshold and a gold or goods alternative; a lock has a level; a theft
  or pickpocket can be seen; a fight can be lost. A failed check may simply stay closed until the player comes back
  stronger, as Skyrim's own checks do: the player can reload, train and try again. A fail-forward is used where the
  story wants failure to matter, not as a rule.
- Each route is built from the matching block: a skill condition on a line, a lock level, the crime engine, a
  fixed-level enemy and a death trigger.

**Grounding.** Everything a quest or a line tells the player is true in the loaded world:
- Every fact is a world record (its form key and position) or a lore line (its file and line).
- Where the world and the lore disagree on something the player can see, the world wins and the lore line is not used.
- A quest's places, people, things and clues are real references in the world or world edits in the ledger. Its
  journal names what the player can find there.
- A speaker's brief lists only the facts that speaker knows, measured from where they stand. The writer states no
  other fact.
- The checkers fail a line or fact without a source, a source the world contradicts, a place or person that is not
  there, and a fact given to someone who could not know it.

## 4. Edit the world lightly

- **Clean-up per host place:** placements that break the setting or level with the player are disabled by override;
  each templated survivor gets a fixed level (nothing levelled against the player). A person given talk is kept.
- **People:** our own base templated on a world base (face, race, voice, outfit and behaviour kept; our name, fixed
  level, factions as needed); a person with no voice type, through the template chain, gets a silent voice; one whose
  drawn height (the template's, through Use Traits) is off 1 is scaled on the ref to stand at 1; placed on existing
  navmesh; essential where the story must not lose them.
- **Things:** placed on a read surface; containers with ownership and lock level; items of our own only where no world
  or base-game item serves; no new art.
- **Rooms:** an existing interior first, a walk-in shell with navmesh next, an exterior scene on navmesh after. No new
  navmesh.
- **Doors:** lock, unlock or re-point existing doors first; a new linked pair only where no existing door serves. A
  load door (a model with no opening animation) always teleports to its pair, and the pair back; a door with a room
  behind it never teleports. A room the player must not leave before a stage has its way out locked with no key, and
  that stage's fragment unlocks it. `plugin.sh inspect doors` lists every door we touch, with its pair, lock and model.
- **Walking:** one navmesh island per walk. Every walk a quest asks of a person (travel, follow to an end zone,
  sandbox) lies on one winning navmesh, proved off game with `plugin.sh inspect navpath` and `plugin.sh questcheck`
  (the world has 5 link entries in 17,591 navmeshes, none on a route a quest uses). We author no navmesh and no edge
  links in BM&V's worlds. A quest whose people would have to cross islands is hosted where they need not, or the
  person is moved by a stage's fragment while the player can see neither spot (an unloaded cell or another cell),
  never in view. A spot is taken from the winning undeleted navmesh under it.
- **A walk starts in front of the player:** a walk is gated on a hidden stage that the quest script sets once every
  walker's 3D is loaded (a once-a-second update in game mode, bounded at 60 checks), and that stage's fragment calls
  `GetActorRef().EvaluatePackage()` on each walker. A schedule or clock-gated package may start unseen and says so. A
  follow starts from the person's own line.
- **A guide never ends in nothing:** the walk ends inside the zone (or within the distance) that sets the next stage;
  the objective marker sits on that place; if the player arrives first, the stage's fragment puts the walkers there.
- **One person, one ref enabled at a time:** where two refs stand for one person (inside and outside a door), the
  fragment that enables one disables the other while the player sees neither.
- **Doors on a quest path** are openable on every path: its key or its unlock on each path.
- **Offers:** every quest topic INFO has a last stage below the quest's first ending; nobody offers a task after its end.
- **Moving a quest spot** within its settlement to the nearest usable ground is a record edit, not a redesign.
- **Traders:** a trader whose stock does not fit gets a vendor faction and chest of their own with a fixed stock.
- **Overrides** of a world, cell or placed reference are made once and shared through one lookup; anything a quest
  alias or condition names is persistent.

## 5. Build every quest from proven blocks

The block set (`docs/design/blocks.md`): triggers (a dialogue line, entering an area, activating, picking up, a death,
another quest's stage, a scene's end), conditions (stage, global, faction, item, skill, time, alive, detected,
relationship rank, the speaker's placed reference), effects (stage with journal and objective, enable parent, item or
gold, move, faction, scene, alias package, global, regard), world edits (templated person, fixed-level actor, placed or
disabled reference, overridden world record). Each is proved; every quest is a composition of them joined by stages.
A step needing anything else is rewritten into these shapes; only when no rewrite keeps the quest's point is a new
block built, read back and given one owner check.

| Needed | Proven way to do it |
|---|---|
| a quest that starts when the player arrives somewhere | Start Game Enabled with an empty stage 0; the giver's opening line sets the first stage, or the previous quest's ending starts it |
| a quest gated on another quest's progress | a stage condition on the opening line |
| a trigger area that should also check time, detection or who is present | an unconditioned trigger area gated only by its prerequisite stage; the extra check moves to a package schedule, a line's condition, a death trigger's fail-forward, or the crime engine |
| "do it unseen" | a detection condition on a line, or theft and pickpocket judged by the crime engine |
| "after dark" | a time condition on a line, or a package schedule that puts the person there only at night |
| people who lead the player somewhere | a Travel package on each alias to a marker on their own navmesh, gated on a hidden stage set when their 3D is loaded; the walk ends in the zone that sets the next stage |
| an escort reaching a place | the kit's Follow package (a copy of a vanilla follow package, never of a template), gated on the stage the person's own line sets; a zone the player enters at the destination, on the follower's navmesh, ends it |
| a person at a place by the clock | a schedule package on the alias to a marker on their navmesh; it may start unseen |
| a person who must be somewhere else for the next step | a fragment's MoveTo to a marker while the player sees neither spot; never a package across navmeshes |
| a quest that is over | the ending's fragment completes the shown objectives, disarms every zone of the quest, counts the side quest, and stops the quest last; the quest is Run Once |
| a zone | fires when the player walks in, once its prerequisite stage is done: it is placed where the player is not standing when that stage is set, and it does not overlap the zone before it |
| "bring N of a kind of thing" | N of one named item |
| several things that must all happen | one hidden stage per thing, each checking the others before setting the joint stage |
| any of several people dying | a death trigger on each alias setting one guarded stage |
| a person whose death moves the quest | Protected on the alias and a death trigger; a person who must live is Essential and has no death trigger |
| removing people from a scene | disable through their own enable parents; never kill in a line's fragment |
| a fight or brawl | a fixed-level enemy and a death trigger, or a Speech or gold route |
| a person the player must not lose | essential, with no fail-forward |
| a person picked out to speak | a condition on their placed reference, made persistent |
| standing with a faction | a global the endings add to |
| a question the player answers | the question's INFO links to one choice topic per answer, in its own branch and not top level, so the answers follow it at once and come back with it |
| where to go next | a stage per step (speak, leave, follow, arrive), each with a journal entry and an objective whose target is an alias on the person, door or marker |
| a door the player uses to move the quest on | the door as a forced-ref alias with the vanilla set-stage alias script on activate, gated by its prerequisite stage |
| a thing the quest needs back from the player | an alias flagged Quest Object, created in its container by the alias, cleared by the ending |
| a check the player can fail | its own topic with the check or cost in the prompt, and a fallback line naming what is needed; INFOs of one topic are exclusive by condition |
| a line said again later | the same INFO with a first and a last stage; the last is before the first ending |
| after the ending | a Hello topic gated on the ending stage for each person left standing |
| a task handed out or reported | an unconditioned line; never a skill or gold check |

- **Engine rules every quest keeps:** every quest is Run Once; aliases are forced references to persistent refs, never
  find-matching; every stage two triggers can set guards itself with a variable read and set with no call between;
  every objective has a target alias whose ref is enabled at that stage; a quest shows in the journal only with an
  objective; side quests count on the Stats page through their ending; every ending stops the quest and disarms its
  zones; every stage has a setter the player can reach and every stage but an ending has a way out; quest types as
  Bethesda uses them; save and reload mid-quest leaves state intact.
- **Code:** one builder per line on the one quest kit (`tools/ArgoniaPlugin/QuestKit.cs`): its helpers make
  conditions, stages and objectives from the story rows, forced aliases, topics and choices with their wording bands,
  Travel / Follow / Schedule packages (copies of vanilla packages of type Package with the owner quest set), zones
  (filling the quest script's `Zones` array for `DisarmZones()`), doors, objective targets, endings and `Snap` to the
  winning undeleted navmesh; a builder never copies a helper or builds one of these by hand, and the kit refuses an
  objective with no target and a death trigger on an Essential alias or base. A condition that needs another
  builder's quest is added in a finish step after both exist, and the build fails if it cannot be. Builders run in a
  fixed order so form ids never move; Papyrus fragments compiled with the game's compiler; editor ids unique; rewards
  fixed, never levelled.

## 6. Give everyone something to say

Every person who can be talked to gets a name, a short backstory, a personality and their own true topics through
`talk-write`: facts from the loaded world (the world wins over a lore line it contradicts), directions as routes of two
to four landmarked steps (a longer way gives its first three, then "from there, ask again"; never the speaker's own
place as a step), a cool first greeting and warmth only with regard, names by the naming rules, a trader's
services matching their stock, and rumours that point to a quest only while it can start. A settlement's people do
not repeat each other: each fact has one holder there, and anyone else who would know it points to that holder.
Everyone the player can walk up to is covered, the people a quest places in the settlement as well as the census's.

## 7. Write the quest dialogue

Per speaker from the record with `dialogue-write` (matched lines from the reference corpus as the model; the
speaker's brief generated from the data, holding that speaker's sourced facts, each line's place, stage window, check
and effect, the reply topics, and what the others in the same place say), one `text-review` pass by another agent
over the lines grouped by place, then loaded. Lines live in the story database and nowhere else. A line tells; a
question is a choice with a topic per reply. A line offers only what its effect delivers, and a line that advances a
stage never refuses. A prompt is a sentence the player would say with what they know, never a bare label, with its
cost or check in it. Every topic has a first and a last stage; nobody offers the task after its ending. A refusal
names what would change it. A fact has one speaker per place and stage window: the echo check fails any line set
where two speakers of one place and stage state the same fact or the same long clause, outside a named list of
deliberate echoes (a quest rumour several people tell). Warm and cool wordings exist only for lines spoken after that
person's regard has changed, separated by the engine's relationship rank; race forms of address only where the brief
asks. Everyone an ending leaves standing has a greeting true of that ending. Journal entries tell one step each;
objectives are imperatives with a target.

## 8. Read back, integrate, deploy

- **Read-backs** from the built plugin and the compiled scripts, never from the source: every stage, journal,
  objective, fragment, alias, trigger area, enable parent, condition, line and band against the record; the talk
  check over every talker; the clean-up list; the shutdown list; a clean Spriggit round trip; the gate (`make check`).
- **Placement check** (`plugin.sh placecheck`) over every actor and object the plugin places: actors on the winning
  navmesh (0 to 40 above, within 150) and not inside a static or furniture; objects resting on their surface (within
  10; structures may sink, never float); the seed rests failing objects on their surface; 0 failures before deploy.
- **Models exist** (run with the placement check): every ref the plugin places, and every load-order ref whose bounds
  hold one of ours (the building a quest uses as a place), has a model that resolves in an archive or loose file of the
  load order (without case); a host whose model is missing is an empty hill in game, so the quest moves to one that has.
- **Quest check** (`plugin.sh questcheck`), generic over every quest of ours in the built plugin; it fails the build
  on: a package route not on one island (or on a deleted navmesh), a walk that can start unseen, a template-type
  package on an alias, a stage with no reachable setter or (non-ending) no way out, a visible stage with no objective
  or an objective with no target, a death trigger on an Essential alias, a quest not Run Once or an ending that does
  not stop it and disarm its zones, overlapping consecutive zones, two refs of one person enabled at once, an opening
  INFO with no upper stage bound, a key-locked door not opened on every ending path. It runs beside the per-quest
  read-backs (mainquestcheck, mqcheck, bccheck, nightreedcheck, localcheck) and placecheck; 0 failures before deploy.
- **Integration:** parallel work lands as source only; the plugin is re-seeded once on the merged tree and every
  read-back runs on that one build before deploy.
- **Everyone talks:** every person the plugin places has a voice and at least one line (`plugin.sh inspect silent`);
  the slice quests' own people with no quest topic answer "Who are you?" from their line rows, true of where they stand at that stage.
- **Every door works:** every door a quest sends the player through is usable on every path: a locked door has its key
  or its unlock on each path, in both directions, and a door that looks usable is usable.
- **A new game starts whole:** quest state the build adds exists from the first frame of a new game (start-game quests
  in the SEQ file), and is checked on a new game, never only after a load.
- **Deploy** the plugin, its ini, its SEQ file (`SEQ/Argonia.seq`: every start-game quest of ours, which the engine
  starts before a new game's first frame; without it their dialogue is missing until a save is loaded) and the compiled
  scripts to the play machine; stage-time mod changes with the stack.
- **The builder never plays the game.**

## 9. Hand it to the owner

- **Owner checks:** the fewest checks that prove what was built, each in plain words with the place, what to do and
  what passing looks like; ticked checks stay as the record; superseded checks are marked.
- **A passed check teaches the recipe:** when the owner passes a fix, its class of mistake is written into the
  recipe and applied to every other quest of the slice before the next walk.
- **Looks are the owner's call:** a model or a placement's look goes to the owner, never decided by a reviewer.
- **Rulings** are recorded the day they are made, and the plan is updated from the walk before new work starts.

## 10. Run it as parallel work

- **One lane per independent deliverable** (a quest line, a settlement's people, a stack fix), in its own worktree,
  with a brief that names the inputs, the proven shapes, what not to touch and a measurable acceptance.
- **The planner rules on gaps** at once (a rewrite in proven shapes, a moved spot, a cut recorded in the review) so a
  lane never waits.
- **Shared things** (the generator's call order, overrides, editor ids, a person two lanes use) are agreed in the
  briefs; a lane that runs out of room commits and leaves a hand-off note, and a fresh lane resumes from it.
- **Costs** are measured per person and per quest and reported with each check-in.
