---
name: story-line
description: Write the overall story of Argonia's main quest or of one faction's line of quests inside the quest ceiling (the faction in a page, the arc, each quest as an outline a quest writer can build without inventing), then read it on paper with fresh readers quest by quest until a round converges. Use before any quest of a line is written, and to rework a line. Written by Fable.
---

# Writing a story line

The story of a whole line is written and read before any of its quests becomes a record, so a line that does not
hold together is caught while changing it costs a page. A minor quest (one place's people, no line) skips this skill
and starts at quest-write. Before this: [quest-system](../quest-system/SKILL.md) (the
ceiling and the order of work). After this: [quest-write](../quest-write/SKILL.md), one quest at a time, from the
outlines this skill leaves. The worked example is the Chainbreakers' line,
[chainbreakers](../../../story/design/quests/lines/chainbreakers.md): its four sections are the shape of every line
story.

## 1. Read first

- [owner-bar](../../../story/design/owner-bar.md), whole; [province-vibe](../../../story/design/province-vibe.md),
  whole (§9 says where ledgers, papers and officials belong, §10 what sings).
- [principles/questlines.md](../quest-write/principles/questlines.md) (how a line holds together, what carries
  between quests, the line record's fields) and [principles/general.md](../quest-write/principles/general.md)
  (what a quest may use, the owner's bar as craft, the trail, choices and rewards).
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

## 2. What to write

One file, `story/design/quests/lines/<line>.md`. Lore is cited as `file:line` under `story/lore/`; **X** marks the
document's own extrapolation, derived from cited lore and never from nothing. Places are those the game loads, with
their form keys.

1. **The faction (or the line) in a page.** The wrong it fights or the thing it wants; who its people are and where
   they sit; how they work, in the line's own skills; who stands against them and why each side is arguable; what it
   pays and what joining costs; what it lies about. A line that suits several builds says which, and that no quest
   shuts any of them out.
2. **The arc.** The hidden spine (the line's truth in order, and what its leader does not tell), with a table of each
   hidden truth, where it is seeded and where it is found. Then each quest in a line or two, each a **different kind
   of job** (a locked box under a household's eyes, an errand into a swamp of beasts, a planned break-in, an aftermath
   walked into, a ruin of the restless dead), with scale climbing, a turn at half to two-thirds, and a finale that is a
   hard choice or a hard place. Say what each quest carries on (a rank, stored numbers, who is alive, what is held,
   what the player knows); earlier choices change greetings and single lines, never a later quest's stages.
3. **Each quest as an outline**, full for the quests about to be built, at arc level for the rest. An outline holds:
   - *what a new player is told, and when*: the optional lines before any job (what it is, whom it serves, what it
     wants of them and why them, what it pays, one true reason to hesitate; local words glossed), and the job in a
     few sentences;
   - *the hidden truth*, as physical events;
   - *the people*: who, where they stand (cell and form key), what they want, what happens if they die;
   - *the things*: where each is, its lock, key and owner, what it holds or says;
   - *the ways through*, each by named skills, each able to go wrong as Skyrim's own systems make it go wrong (a theft
     seen, a pickpocket bungled, a fight lost, a check failed with its own refusal and another way left open);
   - *the stages*: what moves each, its journal gist, its objective and the marker's target; one working stage where
     the ways can be done in any order, results held as stored numbers, things held or people dead; the order in
     which ending lines are tried where two results are true at once;
   - *the choice*, each side argued by the person it concerns with a reason of their own, and what the other side
     winning would cost;
   - *the endings and what each leaves*, where the player will see it, and the fixed rewards;
   - *the moment a player retells*;
   - *a table of step, skill and ceiling block*: every step's mechanism named from quest-system's list, so the quest
     writer never has to invent one.
4. **What each quest needs of its places.** A table per place: every physical thing an outline relies on that the
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
5. **Read on paper**: each round's readers, what they said, what changed as one set, and what the next round checks.

## 3. The bar

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

## 4. Read it on paper

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
   one who wants the province left as it is), and run them on different models where the tools allow. Then ask
   every reader, after their own choice, to make the strongest honest case for each option they did not take. A
   choice is real when each option was some reader's own choice for that reader's own reasons, or at least when
   every option's case can be made without strain; an option nobody chose and nobody could argue is not an option.
   Even then this is a rehearsal: the owner's reading is the test.
3. **Start the deliverability reader** on the same version: a fresh agent given quest-system, the
   [quest form](../../../docs/design/quest-form.md) and the outlines in full. It checks every step against the
   ceiling: each stage moved by an allowed trigger; the ways through done in any order; a death at any moment; a
   thing taken early; a journal entry that claims what the player might not have done; a dead end; a person who must
   hand over a thing they do not hold.
4. **Gather every finding**, then make one set of changes that answers them together, written into the document, and
   record the round in section 4. A change for one reader's taste alone is not made; readers splitting on a conflict
   meant to be ambiguous is the aim, not a finding.
5. **Next round, fresh readers** on the changed version.

**Stop** when a round can retell the story, wants the next chapter, splits on the conflicts meant to be ambiguous,
the deliverability reader finds every step buildable, and nothing new is raised that the author agrees with.

## 5. Hand on

Each full outline goes to [quest-write](../quest-write/SKILL.md); the record's `foundation` names the line document
and the quest's section. A quest writer who finds a gap asks the story's author, who answers in the document; the
quest writer never invents a person, place, truth or way through the outline does not give.
