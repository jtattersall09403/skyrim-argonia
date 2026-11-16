---
name: story-line
description: Write the overall story of Argonia's main quest or of one faction's line of quests inside the quest ceiling (first a short plot page the owner reads, then the arc and each quest as an outline a quest writer can build without inventing), then read it on paper with fresh readers quest by quest until a round converges. Use before any quest of a line is written, and to rework a line. Written by Fable.
---

# Writing a story line

The story of a whole line is written and read before any of its quests becomes a record, so a line that does not
hold together is caught while changing it costs a page. A minor quest (one place's people, no line) skips this skill
and starts at quest-write. Before this: [quest-system](../quest-system/SKILL.md) (the
ceiling and the order of work). After this: [quest-write](../quest-write/SKILL.md), one quest at a time, from the
outlines this skill leaves. The worked example is the Chainbreakers' line,
[chainbreakers](../../../story/design/quests/lines/chainbreakers.md): its outlines are the shape of every line's
outlines; the plot page's shape is [main-plot](../../../story/design/quests/lines/main-plot.md).

## 1. Read first

- [owner-bar](../../../story/design/owner-bar.md), whole; [province-vibe](../../../story/design/province-vibe.md),
  whole (§9 says where ledgers, papers and officials belong, §10 what sings).
- [principles/questlines.md](../quest-write/principles/questlines.md) (how a line holds together, what carries
  between quests, the line record's fields) and [principles/general.md](../quest-write/principles/general.md)
  (what a quest may use, the owner's bar as craft, the trail, choices and rewards), and
  [principles/choices.md](../quest-write/principles/choices.md) (what each outcome of a choice or ending gives and
  costs in play, and the result that builds each kind).
- The line's old design, which is the foundation, improved and never replaced: the main line in
  `story/design/quests/30-main-quest.md` and `main-line-outline.md`; a faction's section of `40-factions.md`; its
  rows in `story/design/quests/review/walk6-ceiling.md` (each premise already brought under the ceiling); its
  people in `36-cast-roster.md` under the rules of `35-cast.md`.
- The lore: `story/lore/` (topics, regions, settlements) and the agreed extrapolation
  (`story/lore/extrapolation/argonia-4e201-state.md`, `settlement-register.md`, `gap-register.md`).
- The world the story is for. For a built world, what the game loads: the census
  ([census](../../../docs/research/bmv/census.md); the database's `bmv_*` tables through
  `python3 -m tools.argonia_world.db query "SELECT ..."`), and for a place you mean to use, its cells, doors, people
  and containers (`bash tools/ArgoniaPlugin/plugin.sh inspect cellrefs:<cell>`, `near:<x>:<y>:<z>:<r>`). For a world
  whose places are not built yet, its digest (`story/design/world/`: the province, each region, each place with what
  its record says it is, gives and promises) and each place's source place, which shows what kind of buildings and
  things it can be built with. A quest is set in a place that exists, or is recorded to be built, and reads as what
  the story calls it.
- The line's skill leaning: its key in [profiles.yaml](../quest-write/profiles.yaml).
- [buildable.md](buildable.md), whole, before any outline is written: what the game can know and do, the shape that
  always works, the patterns, and the sketch every full outline carries.

## 2. The plot, first

A line's story starts as a short plot page, `story/design/quests/lines/<line>.md`, in the form of
[main-plot](../../../story/design/quests/lines/main-plot.md). The owner reads and notes it in the story explorer.
No outline is written until he has passed the plot. Lore is cited as `file:line` under `story/lore/`; **X** marks
the document's own extrapolation, derived from cited lore and never from nothing.

**Its sections, in this order:**

1. `**Words.**` Every local word the page uses, each glossed in a clause.
2. **What the faction is** (for the main quest, the premise): in its first two sentences, what it is and what a
   member does all day. Then where it sits, its skills, its rival and what joining gives.
3. **The truth under the story:** what the player is shown, then what is true, each a physical fact a player
   could retell after one reading (who does what to what, and why). A truth that needs a new idea about how the
   world works is cut down until it does not.
4. **The people who matter:** a table of who, what they want, and what they hide or what it costs. Each has a
   reason of their own. One person on the player's side is tied to the enemy by something they did.
5. **Joining** (a faction): the rumours that lead to it and the small quest of finding it; what the player does to
   be let in; what shuts the door (a rival joined, a stage of a rival's line).
6. **The acts:** `### Act I: <name>` and so on, each quest one numbered paragraph of its own, written
   `**3. Title** (Place, what it is; Second Place, what it is). ...`. The paragraph says what the player is asked
   to do, the ways through by named skills, what they find, and how it leads to the next quest: who tells them
   where to go, what the journal then says and where the marker points. A report back to a handler is written
   out: what the handler says and what they send the player to do.
7. **Side quests on the road**, **the twist** and **the endings**, where the line has them. Every choice and
   ending says what it gives and what it costs in play ([choices.md](../quest-write/principles/choices.md)).
8. **What it needs, and what it changes elsewhere:** what it asks of the world (meshes, creatures, mods), the
   needs table (below, "What each quest needs of its places"), what it asks of the ceiling, and what else in the
   repository it makes untrue.

**How a plot is built:**

- *The player is a blank slate* drawn into the world's intrigue. Nothing turns on who they were.
- *The thing at stake is sold early.* In the first two quests the player sees it, hears from someone who would
  lose it what losing it means, and gets a use of it for themselves.
- *A mystery gives up its means before its motive.* The player finds how the thing is done, by clues of their own
  gathering, and is left with a stated question (why this way, and not the plain way?) that the twist answers.
  The twist calls back to things the player saw; the journal marks each oddity when it happens.
- *Every place is written from its source place.* Before a quest is set anywhere, read the place's record and its
  source place: the rough layout, each building and interior, its rooms, doors, water and containers, who and what
  already stands there (`newworld/places/`, the census, the digest). Use what it holds. Ask only for small
  additions: a thing placed, a person, a lock, a name. A cellar, a flooded passage or a great door is written
  only where the source has one; otherwise the quest moves to a place that has, or the story changes.
- *Danger climbs with the line.* Each quest's places are no harder (the place's band and the band of the way to
  it) than the line has reached. A line a new character can start opens in D1, rises a band at a time and ends in
  the hardest places it uses. Skill checks follow: a lock or a pocket in a first quest opens for a level-one
  character who has that skill. Rewards rise in step and are fixed and hand-made.
  `python3 -m tools.newworld.plot_check <the line's file>` prints the ladder and fails a step out of order.
- *A choice of ways is a choice.* No way is both free and best: a ring handed over for nothing makes the potion
  and the spell pointless. Each way is open to a build (melee of several kinds, ranged, magic, or stealth paired
  with one of them); a Speech way is an extra, never a quest's only second way.
- *Every branch is walked to its end.* For each way in, write the state it leaves (who is alive, who is friendly,
  what the player holds) and what the next step is in that state. The thing the line needs next can be got in
  every state.
- *Everyone stands somewhere for a reason.* Enemies do not stand among the people they wrong. Say where each
  person is, and why there.
- *Each quest is a different kind of job* (a locked box under a household's eyes, an errand into a swamp of
  beasts, a planned break-in, a ruin of the restless dead), with a turn at half to two-thirds and a finale that is
  a hard choice or a hard place. A title is true of its quest.
- *A faction's line* has about as many quests as a guild of Skyrim's or Morrowind's. Its early quests teach a
  pattern (a spell or recipe taught, then used as one step among several in the job it was taught for; a case
  solved by evidence the player must have found) and its late quests break that pattern. It names a rival, the
  point at which the rival's door shuts, and a late choice the player's skills can sometimes avoid.

## 3. The outlines

Once the owner has passed the plot, each quest becomes an outline in the same file, full for the quests about to
be built. Places are those the game loads, with their form keys.

1. **The arc.** The hidden spine (the line's truth in order, and what its leader does not tell), with a table of each
   hidden truth, where it is seeded and where it is found. Say what each quest carries on (a rank, stored numbers,
   who is alive, what is held, what the player knows); earlier choices change greetings and single lines, never a
   later quest's stages.
2. **Each quest as an outline**, full for the quests about to be built, at arc level for the rest. An outline holds:
   - *what a new player is told, and when*: the optional lines before any job (what it is, whom it serves, what it
     wants of them and why them, what it pays, one true reason to hesitate; local words glossed), and the job in a
     few sentences;
   - *the hidden truth*, as physical events;
   - *the people*: who, where they stand (cell and form key), what they want, what happens if they die;
   - *the things*: where each is, its lock, key and owner, what it holds or says;
   - *the ways through*, each by named skills, each able to go wrong as Skyrim's own systems make it go wrong (a theft
     seen, a pickpocket bungled, a fight lost, a check failed with its own refusal and another way left open);
   - *the stages*: what moves each, its journal gist, its objective and the marker's target; one working stage where
     the ways can be done in any order, each way's result a thing held, a person dead or the stage that finishes
     the step; the order in which ending lines are tried where two results are true at once
     ([buildable.md](buildable.md) §3);
   - *the choice*, each side argued by the person it concerns with a reason of their own, and what the other side
     winning would cost;
   - *the endings and what each leaves*, where the player will see it, and the fixed rewards;
   - *an outcome table for every choice and every ending* (choices.md): the outcome; what the player gains in play;
     what they lose or can no longer get; who in the world pays and where the player will see it; the form result
     that builds each row. Gains and losses are things to use the next day (a power, a thing, a recipe, a trader's
     stock, a trainer, a door, a bed, a group's peace or hostility, the next job), different in kind from outcome to
     outcome, none better in every column; a standing is written only with what it opens. A choice with a row that
     says only what people will say, or only that a standing moves, is not finished;
   - *the moment a player retells*;
   - *a table of step, skill and ceiling block*: every step's mechanism named from quest-system's list, so the quest
     writer never has to invent one;
   - *its sketch*: the stage table as the quest form will hold it, a fenced `sketch` block under the stage table
     ([buildable.md](buildable.md) §4), passing `python3 -m tools.questform sketch <the line's file>`, and then checked by its writer against
     [buildable.md](buildable.md) §3 and §7, line by line, before the document is read on paper.
3. **What each quest needs of its places.** A table per place: every physical thing an outline relies on that the
   world's data does not already hold (a house with a door that locks, a chest in it, a shrine, a pen, a wreck, a
   person's post), named plainly by what a player would call it on sight, with the quest that needs it and what the
   quest does there. Each row is a promise the place's record will carry and its build must keep, so write only what
   a place of that culture and source could hold, in words its buildings can read as (a "stilt hut", not a
   "hatching shed", unless a building that reads as a hatching shed exists to build with). Each row also says
   **how the player will know what it is**, from the player's side and nobody else's: a player has never read the
   record, so a house we have decided is the hatching shed is only a house to them. One or more of: its look on
   sight (the building or thing itself reads as that to someone who knows nothing); the game's own label (the name
   on its door when the player looks at it, the name of the room on entering, a map marker's name, the name shown
   on the thing); what visibly stands in or by it (nests and eggs, nets, a forge); a named person who tells the
   player, placing it by something fixed, before the player needs it. A need with no such answer is not a need a
   place can keep: change the story. The outlines themselves
   place people and things only by the place and by these needs, never by description of surroundings: where things
   stand, what is beside what, and every spoken word about the place are written later, on the built place.
4. **Read on paper**: each round's readers, what they said, what changed as one set, and what the next round checks.

## 4. The bar

- **Drama and tension of the line's own kind**: what it fights, who it fights, what it costs. Each quest is something
  daring the player does, never a chore, and names the skills it uses.
- **Moral ambiguity**: each side of a conflict arguable, a patron with something to hide, nobody who gets out free.
- **Paperwork is rare and never the play**: where a document truly belongs (an outsider's papers, an ex-Imperial
  household's count) it is a thing to steal, swap or burn; no step is won by reading, counting or filing.
- **Any build can finish the main quest**: every main quest has at least two ways through on different skills. A
  faction's quests lean on the faction's skills.
- **A new player can follow it** as it happens: names and local words given before they are used.
- **Inside the ceiling**: an event the story needs has already happened and is found, is told by a witness, or
  happens where the player is not; nobody walks for the story; a finale is never a staged sequence.

## 5. Read it on paper

Each round reads one version of the whole document, as [quest-system](../quest-system/SKILL.md) "How rounds
converge" says.

1. **Write the player's sheets.** For each quest, what a player meets in order: who speaks to them and what they say
   (as gists), what they see, what they are asked to do, the choices offered. No hidden truth, no outline, no stage
   table.
2. **Start the players**: two or three fresh agents, each told to read only the sheet it is given, each a different
   honest temperament a little hard to please (one who loves the lore and reads every word; one impatient, who skims
   and wants to act; for the main line, one playing a build the line might shut out). Give quest one's sheet; after
   each quest ask what they think is going on, whom they trust, what they expect next and what they would choose; then
   send the next quest's sheet (SendMessage to the same agent, so they carry what they believed). At the end: could
   they retell the story, do they want the next chapter, what bored or lost them.
   **Testing a choice needs players who differ in what they value**, not only in patience. Fresh agents are one
   model with one set of instincts, and left to themselves they all take the kind, careful option; that says
   nothing about whether real players would split. For each choice meant to divide players, give the readers
   different people to be, each a real kind of Elder Scrolls player with reasons of their own (one who plays to
   grow powerful and takes what is offered; one who sides with their own tribe or faction against outsiders,
   whatever it costs others; one who keeps their word to whoever hired them; one who distrusts every institution;
   one who wants the province left as it is), and run them on Sonnet 5.5 at medium effort (`model: sonnet`, `effort: medium`), which is fast and cheap enough to
   run several. Then ask
   every reader, after their own choice, to make the strongest honest case for each option they did not take, and
   to say what they think they gained and gave up in play and whether they would choose differently for the reward
   (one reader always plays only for what each side gives). A
   choice is real when each option was some reader's own choice for that reader's own reasons, or at least when
   every option's case can be made without strain; an option nobody chose and nobody could argue is not an option.
   Even then this is a rehearsal: the owner's reading is the test.
3. **Start the deliverability reader** once `sketch` passes on the same version: a fresh agent given quest-system,
   [buildable.md](buildable.md) and the outlines in full with their sketches and `sketch`'s closing lines. It is
   told what `sketch` has proved: every stage moved by an allowed trigger and only upward, a way out of every stage,
   every gate and result one the game has, every objective's marker on, hand-ins gated on what they take, switches
   made away from the player, a refusal for every check, nobody unnamed whom the quest cannot lose, takes and deaths
   early answered, and every stage and ending reached by an able and a new character after each ending before it.
   It reads for what `sketch` cannot see (buildable.md §7): that the sketch says what the outline says, journal
   entries true of every way, the needs of places, a hostile band kept from the speaker at its edge, and one story
   told by stand-ins, choices and switches.
4. **Gather every finding**, then make one set of changes that answers them together, written into the document, and
   record the round in "Read on paper". A change for one reader's taste alone is not made; readers splitting on a conflict
   meant to be ambiguous is welcome and is not a finding; readers agreeing is not a failure either.
5. **Next round, fresh readers** on the changed version.

**Stop** when a round can retell the story, wants the next chapter, `sketch` passes, the deliverability reader finds
every step buildable, and nothing new is raised that the author agrees with. Whether readers split on a choice is
something to weigh, never a bar to pass: readers all choosing alike is a prompt to check that each option has an
honest case and something of its own to give in play, and once that is so the choice stands however they chose.

## 6. Hand on

When the story lands, its needs reach each place it names by themselves: the place studio's story panel reads the
needs tables each time it opens (so keep each one a regular table under a "What each quest needs of its places"
heading, under its place's bold name or with a Place column, with the columns "The thing", "Quest", "What happens
there" and "How the player knows it", the place named as the world's data names it). Each new row is then judged
from the player's side (`python3 -m tools.places needs open <place>`; `place-build`, section 6). Where a place is
already built, a need it does not meet is answered by changing the story to what the place has.

A story that no longer holds is marked at its head, as its first paragraph: `**Status: to be rewritten.**` with what
in it is untrue by section, or `**Status: replaced by ...**` when another story holds its work. The explorer and the
studio both read it: a story to be rewritten has its rows marked, and a replaced one is not read for needs.

Each full outline goes to [quest-write](../quest-write/SKILL.md) with its sketch, which the record follows; the
record's `foundation` names the line document and the quest's section. A quest writer who finds a gap asks the
story's author, who answers in the document; the quest writer never invents a person, place, truth or way through the outline does not give.
