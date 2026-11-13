# Designing a quest that can be built

Read this whole before writing any outline. A quest of ours is a handful of stages moved by a few plain happenings,
and talk that depends on them. A story that is designed in those terms from the first line is built as written; a
story designed in scenes and then fitted to them is rebuilt. This page is the craft of the first kind: what the game
can know, what it can do, the shape that always works, the patterns that recur, and the sketch, the quest's stage
table in a form a tool checks, written with each full outline and passing `sketch` before any reader sees it.

Words of the quest form, glossed once:

- a **stage** is a numbered step of the quest with its journal entry; the quest only ever moves to a higher stage;
  an **ending** is a stage that completes or fails the quest;
- a **line** is something the player says to a person (a topic, an answer to a question, a greeting, or the one line
  a person speaks first) and what they say back;
- a **gate** is what must be true for a line to be offered; a **result** is what a stage does as it begins;
- a **trigger** moves a stage when the player takes a named thing, uses or reads a named thing, or a named person
  dies, or when another quest reaches a stage;
- an **objective** is the journal's instruction for a stage, with a **marker** on each person or thing it names;
- **who must live** names a person the quest cannot go on without: their death fails it, with a journal entry;
- **switching** a person or thing **on or off** makes it appear or vanish; it is only done **away** from the player:
  in another indoor place, across the line between indoors and outdoors, or far off outdoors.

## 1. What the game can know

A stage moves on exactly these, and nothing else:

| It can know | In plain words |
|---|---|
| a line was picked | the player said this to this person |
| a named thing was taken | it went into the player's pack (stolen, looted, bought, given ownership and taken) |
| a named thing was used or read | a door opened, a container searched, a note or book read, a lever pulled |
| a named person or creature died | by anyone's hand, at any time |
| another quest's stage was reached | this quest moves, or starts, when that one does |

A line is offered, or not, by these gates, and nothing else:

| It can check | In plain words |
|---|---|
| a stage of this or another quest | is at, is at least, or has passed through |
| a number we stored | a stage set it: which way an earlier quest ended, which side was taken |
| faction and rank | the player belongs, at this rank or above |
| a thing held, or gold | the player holds this named thing (or this many of a stock thing), or this much gold |
| a skill's level | Speech, Sneak, Lockpicking, Pickpocket, Alchemy, Restoration, a weapon skill, a school |
| alive or dead | this named person or creature |
| regard | how this person feels about the player, -4 to 4 |
| the player's race or sex | |

**What it cannot know, and what stands in.**

- *That the player is somewhere.* A thing used there (a door, a stone, a body's satchel) or a person spoken to there.
- *That a thing was looked at, or a place found.* A thing used or read there; or a person there who speaks.
- *That a theft, a killing or a trespass was seen.* Skyrim's own crime system answers it under the place's law; the
  quest knows only that the thing is held or the person dead.
- *How many.* It cannot count. One named thing or one named death per stage; or a hand-in gated on holding several
  of a stock thing (three ash eggs); or a line gated on each named person dead.
- *That time passed, or the hour.* "Night" and "dusk" are words people say; no step waits.
- *That a spell was cast.* A line gated on that school's skill stands in (Restoration 25 to ease a burnt hand).
- *That a fight was fled, or someone spared.* Who is still alive, and a line said to them, stands in.
- *That the player has met someone before.* A stage done at which they spoke stands in.
- *What happened in an order.* Only what is held, who is dead and which stages are done; never which came first.

## 2. What the game can do

A line does one thing: it moves the quest to a stage. **Everything else is done by a stage as it begins:**

| A stage can | In plain words |
|---|---|
| give or take a thing, or gold | into or out of the player's pack |
| set or add to a stored number | for a later line or quest to read |
| make the player join a faction, or set their rank | |
| change a person's regard | -4 to 4 |
| switch a named person or thing on or off | only away from the player |
| lock or unlock a named door | |
| give the player ownership of a container | what it holds is theirs to take, no theft |
| show a message box | a few words, on the screen |
| start another quest | at a stage |
| move on at once to a higher stage | if the player already holds a named thing |

A person can be **placed** standing where they are needed, at a fixed level, hostile (they attack on sight) or not;
a thing on a surface, in a container or carried by a person; a container with a lock, a key and an owner; a door
locked or not.

**What it cannot do, and the nearest it can.**

- *Move anyone, or the player.* A person who has gone ahead is a second placement of them, switched on away from
  the player; the first is switched off later, away from where the player then stands.
- *A scene, a walk, someone following, a timetable.* It has already happened and is found; a witness tells it; or
  it happens where the player is not.
- *Make a speaking person hostile.* A person is placed hostile, or speaks; never both. If they are to be fought
  after talking, the player starts the fight (the game lets anyone be attacked) and the death is marked as the
  player's choice.
- *Make a hostile person talk, sell, stand aside, or let anyone pass.* The band stays hostile; the one who speaks is
  someone else, placed apart and not of the band.
- *Place a body.* A container that was theirs (a satchel, a strongbox) holds what their body would; or they are
  alive at the start and the player finds them killed by what the place holds.
- *Change a price, teach a skill, change a look, build or burn anything in sight.* A gold check on a line is a
  price, and it is fixed; a skill book teaches; a burnt camp is a second set of things switched on far away.
- *Do something only sometimes.* A stage's results always happen. Two outcomes are two stages.
- *Give what a person carries, or what lies in a chest.* A thing placed in the world is got by taking it; a stage
  can only give a thing nobody has placed (a letter written for the player, a second copy of its own).

## 3. The shape that always works

1. **The job is a line.** A quest waits at a hidden stage 0; the giver's line moves it to the first stage the player
   reads. A main quest started by the last one starts at its first stage.
2. **One working stage.** After the briefing the quest sits at one stage at which every way through is open at once.
   Each way ends in something the world holds: a thing in the player's pack, a person dead, a door open, or a stage
   of its own when it is the way that finishes the step. Two ways that must both be done are two things held or two
   deaths, never two stages.
3. **Number the stages in the order a player can meet them.** Stages only climb, so every in-between stage of the
   working step (the keeper let me in; the keeper sold it) sits below the stage its thing's take moves to; a take
   that could fire after the quest has passed it closes there and is lost.
4. **Every stage has a way out**, and every way through can be done by an able character and by a new one with a
   little gold.
5. **Every check has its own refusal**, said when it fails, and another way left open (a talked way, a bought way, a
   stolen way, a fight).
6. **Ending lines are tried in a stated order** where two could be true at once; the first that holds is said.
7. **Nobody the quest cannot go on without, unless named.** For every person: if they die at each stage, what moves
   the quest on? If nothing, they must live: name them, with a failed ending and its journal entry.
8. **A person stands in one place for the whole quest**, and speaks or is hostile, never both.
9. **One name for one thing.** Two people, two bodies, two jars of one name are one thing to the player. A thing
   given in place of a placed one is a stock thing, counted, and every gate checks the stock thing.
10. **Taken early, dead early.** For every named thing: if the player holds it before the stage that asks for it, the
    stage notices (a take moves on at once when held). For every named person: if they are dead before the stage
    that needs their death, a line at or before that stage gated on them dead moves it.
11. **Switched only by a line, a take or a use, and far away.** Never by a death or another quest's stage, and never
    in the cell where the player stands.
12. **The journal says only what the player has just done.** A stage reached several ways has an entry true of
    each, or one stage for each way.

## 4. The sketch

Each full outline carries its **sketch**: its stage table as the quest form will hold it, in a fenced block in the
story document, directly under the outline's own stage table. It is a small fixed text, not JSON, because a writer
can keep it beside the outline and change it with the outline, a reader can read it, and the tool reads it exactly
and names the story line of each fault. It holds the stages, objectives and their targets, the people and things by
name, the lines as gists with their gates and the stage each moves to, the triggers and who must live. It holds no
spots: the places are not built. Each reference stands in a named place, indoors or outdoors, and an outdoor place
marked `far` is out of sight of every other place, so that "away" can be judged.

Check it, and keep checking until it passes:

    python3 -m tools.questform sketch story/design/quests/lines/<line>.md [--quest <id>] [--paths]

It reads every block of the file, builds each quest form as the quest writer's record will compile it, and runs the
form's rules, the design rules below, and the reach walk: every stage and ending reached by an able character and by
a new one with 1,000 gold, after each completed ending of the quests before it in the same file. Each fault is
printed as `<file>:<line>: <quest> <rule>: <what>` with a line saying what it means; the last line says `passes` or
how many faults. `--paths` prints the shortest way to each ending. What only the built place can show (exact spots,
the speaker's spot by the door, the names the game shows, the words) is listed as checked when built.

**The statements**, one a line; words, "quoted text", commas between list items, `#` starts a comment:

| Statement | Says |
|---|---|
| `quest <id> main\|faction\|minor "<name>"` | the quest |
| `start game <stage>` / `start when <quest> <stage> at <stage>` / `start from <quest> at <stage>` | running from a new game (a hidden 0 for a job offered by a line); started when another quest reaches a stage; started by another quest's `start` result |
| `place <id> indoors\|outdoors [far] "<name>"` | a place; outdoor places are near one another unless `far` |
| `person <id> at <place> [level <n>] [hostile] [existing] [off] "<name>"` | a person or creature; `existing` for one the world already holds; `off` until a stage switches them on |
| `thing <id> at <place>\|in <container>\|on <person> [container] [locked <level> [key <thing>]] [owner <person or faction>] [holds <item> <n>, ...] [readable] [stock <item> [count <n>]] [off] "<name>"` | a thing; `stock` for a counted stock item (gold, lockpick, or one of ours given in several places) |
| `door <id> at <place> [locked <level> [key <thing>]] "<name>"` | a door |
| `item <id> [readable] "<name>"` | a thing nobody places, which a stage gives |
| `stage <n> hidden` / `stage <n> [completed\|failed] "<journal>" [do <result>, ...]` | a stage, its entry and its results |
| `objective <n> at <stage>, ... "<words>" -> <target>, ...` | an objective shown at those stages, its markers; it is done when the quest moves on |
| `line <id> <speaker> [first\|greeting\|answer] at <stage>[-<stage>] [ask "<words>"] [if <gate>, ...] [-> <stage>] [else "<refusal>"] [asks <line>, ...] says "<gist>"` | a line: offered at those stages, gated, moving to a stage; `else` is said when its check fails; `asks` makes it a question whose answers are `answer` lines; `first` is the one person who speaks first |
| `take\|use\|death <id> from <stage> -> <stage> [until <stage>] [choice]` | a trigger, open from a stage; `choice` marks a killing as the player's |
| `when <quest> <stage> from <stage> -> <stage>` | another quest's stage moves this one |
| `must-live <person> fails <stage> [from <stage>] [to <stage>]` | who must live, and the failed ending their death sets |

Gates: `stage <quest> is <n>`, `stage <quest> >= <n>`, `done <quest> <n>`, `number <id> = <v>`, `number <id> >= <v>`,
`rank <faction> <n>`, `holds <thing or item> [<n>]`, `gold <n>`, `skill <skill> <n>`, `alive <person>`, `dead
<person>`, `regard <person> <n>`, `race <race>`, `sex <sex>`. Results: `give <thing> [<n>]`, `take <thing> [<n>]`,
`give-gold <n>`, `take-gold <n>`, `set <number> <v>`, `add <number> <v>`, `join <faction>`, `rank <faction> <n>`,
`regard <person> <n>`, `on <ref>`, `off <ref>`, `lock <door>`, `unlock <door>`, `own <container>`, `message "<words>"`,
`start <quest> <stage>`, `stage <n>`.

As the quest writer's record will, `sketch` adds three things for you: a take's stage moves on at once when the thing
is already held; a take, use or death that could fire after the step it stands for closes there; a job offered at a
hidden stage 0 is offered only while who must live are alive. It names everything else.

**The worked example**: a break-in for a thing, with a talked way, a bought way, the stolen way, a fight (kill the
keeper, loot his key) and a hand-in; the job offered to a player who already holds the thing; a patron who must
live.

```sketch
quest EX01 faction "The Eel-Wife's Ledger"
start game 0

place lamphouse indoors "the Lamp House"
place landing outdoors far "Teeth Landing"
place netstore indoors "the net store"

person patron at lamphouse "Asks-Twice"
person keeper at landing "Ojel"
thing storekey on keeper "net-store key"
door storedoor at landing locked adept key storekey "Door to the net store"
thing chest at netstore container locked expert key storekey owner keeper holds gold 40 "net chest"
thing ledger in chest readable "the eel-wife's ledger"

stage 0 hidden
stage 10 "Asks-Twice wants the eel-wife's ledger, which Ojel keeps in a chest in his net store at Teeth Landing." do give lockpick 5
stage 20 "Ojel let me into his net store and told me to take the ledger." do unlock storedoor, own chest
stage 25 "Ojel sold me the right to take the ledger from his chest." do take-gold 300, unlock storedoor, own chest
stage 30 "I have the eel-wife's ledger."
stage 90 completed "I gave Asks-Twice the ledger." do take ledger, give-gold 150, rank lamp 1
stage 95 failed "Asks-Twice is dead. Nobody wants the ledger now."

objective 10 at 10 "Get the eel-wife's ledger from Ojel's net store" -> ledger, keeper
objective 20 at 20, 25 "Take the ledger from the net chest" -> ledger
objective 30 at 30 "Bring the ledger to Asks-Twice" -> patron

line job patron at 0 ask "Is there work?" -> 10 says "the ledger, whose it is and why she wants it"
line early patron at 0 ask "I have the eel-wife's ledger." if holds ledger -> 90 says "she takes it without asking how"
line why patron at 10-30 ask "Why the ledger?" says "who it names"
line talk keeper at 10 ask "Let me see the ledger." if skill Speech 40 -> 20 else "It stays in my chest." says "he unlocks the store"
line buy keeper at 10 ask "Sell it to me." if gold 300 -> 25 else "Three hundred, and not a coin less." says "he takes the coin"
line hand patron at 30 ask "Here is the ledger." if holds ledger -> 90 says "she takes it"

take ledger from 10 -> 30
must-live patron fails 95
```

## 5. The patterns

Each is a whole quest that passes `sketch`; copy its shape.

**A break-in for a thing** is the worked example: the thing placed in an owned, locked container; the key carried by
its owner; the talked way and the bought way are stages below the take's stage that unlock the door and give
ownership of the container, so the thing is still taken (no theft); stolen, looted or bought, it is one take.

**A hunt**: learn, find, kill, report. The death moves the quest from the stage that gives the job; a kill made before
the job is answered at the offer, by a line gated on the beast dead.

```sketch
quest P02 minor "The Pen-Breaker"
start game 0

place village outdoors "Hatchwater"
place den outdoors far "the drowned pen"

person elder at village "Old Saxhleel"
person beast at den hostile level 6 "the pen-breaker"
thing tooth on beast "the pen-breaker's tooth"

stage 0 hidden
stage 10 "Old Saxhleel asked me to kill the beast that breaks the eel pens, at the drowned pen."
stage 30 "I killed the pen-breaker."
stage 90 completed "I told Old Saxhleel the pen-breaker is dead." do give-gold 80
stage 91 completed "I told Old Saxhleel I had already killed the pen-breaker." do give-gold 80
stage 95 failed "Old Saxhleel is dead. Nobody will pay for the pen-breaker now."

objective 10 at 10 "Kill the pen-breaker at the drowned pen" -> beast
objective 30 at 30 "Tell Old Saxhleel" -> elder

line job elder at 0 ask "Any work?" if alive beast -> 10 says "the beast at the pens"
line before elder at 0 ask "I killed a beast at the drowned pen." if dead beast -> 91 says "then it was the one"
line report elder at 30 ask "It is dead." -> 90 says "he pays"

death beast from 10 -> 30
must-live elder fails 95
```

**A choice between people**: each side is a line of its own, gated on that person alive, each moving to its own
stage; the giver hears the choice; a stored number keeps it for later quests.

```sketch
quest P03 minor "Two Claims on a Boat"
start game 0

place yard outdoors "the boat yard"
place hut indoors "the elder's hut"

person elder at hut "Elder Tsleeixth"
person sister at yard "Ei-Ja"
person brother at yard "Meer-Ra"

stage 0 hidden
stage 10 "Elder Tsleeixth asked me to hear the two who claim the boat and give it to one of them."
stage 41 "I gave the boat to Ei-Ja."
stage 42 "I gave the boat to Meer-Ra."
stage 91 completed "I told the elder Ei-Ja has the boat." do set p03.boat 1, give-gold 30
stage 92 completed "I told the elder Meer-Ra has the boat." do set p03.boat 2, give-gold 30
stage 95 failed "Elder Tsleeixth is dead, and nobody else can settle the boat."

objective 10 at 10 "Give the boat to Ei-Ja or Meer-Ra" -> sister, brother
objective 40 at 41, 42 "Tell Elder Tsleeixth" -> elder

line job elder at 0 ask "Is there anything I can do?" -> 10 says "two claim one boat"
line hers sister at 10 ask "Why should it be yours?" says "her case"
line his brother at 10 ask "Why should it be yours?" says "his case"
line toher sister at 10 ask "The boat is yours." if alive sister -> 41 says "she takes it"
line tohim brother at 10 ask "The boat is yours." if alive brother -> 42 says "he takes it"
line tell1 elder at 41 ask "Ei-Ja has the boat." -> 91 says "so be it"
line tell2 elder at 42 ask "Meer-Ra has the boat." -> 92 says "so be it"
must-live elder fails 95
```

**A hand-in gated on what is held**: the thing is a stock thing, so several can be held and counted; the hand-in is
gated on holding enough and takes them.

```sketch
quest P04 minor "Three Eggs of Ash"
start game 0

place pool outdoors "the hatching pool"
place nest outdoors far "the ash nests"

person tender at pool "Hatch-Mother Wuja"
thing egg1 at nest stock ashegg "ash egg"
thing egg2 at nest stock ashegg "ash egg"
thing egg3 at nest stock ashegg "ash egg"
item ashegg "ash egg"

stage 0 hidden
stage 10 "Hatch-Mother Wuja wants three ash eggs from the ash nests."
stage 90 completed "I gave Hatch-Mother Wuja three ash eggs." do take ashegg 3, give-gold 60
stage 95 failed "Hatch-Mother Wuja is dead."

objective 10 at 10 "Bring three ash eggs to Hatch-Mother Wuja" -> tender, egg1, egg2, egg3

line job tender at 0 ask "Can I help?" -> 10 says "three eggs"
line hand tender at 10 ask "Here are three eggs." if holds ashegg 3 -> 90 says "she takes them"
must-live tender fails 95
```

**An aftermath found**: the earlier quest's ending, set by a line indoors, switches the aftermath on far away; the
later quest is started by that ending and finds what it left.

```sketch
quest P05A minor "The Raid Told"
start game 0

place inn indoors "the Salt Inn"
place camp outdoors far "the burnt camp"

person teller at inn "Ruuk"
thing wreckage at camp off "the camp's wreckage"
thing survivor at camp off "a burnt strongbox"

stage 0 hidden
stage 10 "Ruuk says a raid is coming to the river camp."
stage 90 completed "I told Ruuk I could not stop it. The camp burned." do on wreckage, on survivor, start P05B 10
stage 95 failed "Ruuk is dead."

objective 10 at 10 "Hear Ruuk out" -> teller

line job teller at 0 ask "News?" -> 10 says "a raid is coming"
line nothing teller at 10 ask "I cannot stop it." -> 90 says "then it burns tonight"
must-live teller fails 95
```

```sketch
quest P05B minor "What the Raid Left"
start from P05A at 10

place inn indoors "the Salt Inn"
place camp outdoors far "the burnt camp"

person teller at inn "Ruuk"
thing letter at camp readable "a raider's letter"

stage 10 "Ruuk asked me to look at what is left of the river camp."
stage 30 "I read a letter in the ashes of the river camp."
stage 90 completed "I told Ruuk what the letter said." do give-gold 40
stage 95 failed "Ruuk is dead."

objective 10 at 10 "Search the burnt camp" -> letter
objective 30 at 30 "Tell Ruuk" -> teller

line tell teller at 30 ask "The raiders wrote this." -> 90 says "he reads it"

use letter from 10 -> 30
must-live teller fails 95
```

**A person who has gone ahead**: a second placement of them, switched on far away by the line that sends the player;
the first placement is switched off when the player meets the second, far from the first.

```sketch
quest P06 minor "The Guide Who Went Ahead"
start game 0

place lodge indoors "the guides' lodge"
place ruin outdoors far "the white ruin"

person guide at lodge "Keema"
person guideahead at ruin off "Keema"

stage 0 hidden
stage 10 "Keema went ahead to wait for me at the white ruin." do on guideahead
stage 90 completed "I found Keema at the white ruin." do off guide, give-gold 20
stage 95 failed "Keema is dead."

objective 10 at 10 "Meet Keema at the white ruin" -> guideahead

line job guide at 0 ask "Will you guide me?" -> 10 says "meet me at the ruin"
line met guideahead at 10 ask "Here I am." -> 90 says "the way in"
must-live guideahead fails 95
```

**Evidence read and a name given**: reading the thing moves a stage; the name is a question whose answers are lines,
each moving to its own ending.

```sketch
quest P07 minor "The Name in the Ledger"
start game 0

place office indoors "the toll office"

person clerk at office "Tollkeeper Vel"
person accuser at office "Hesh-Ra"
thing ledger at office readable "the toll ledger"

stage 0 hidden
stage 10 "Hesh-Ra says someone has been robbing the toll box, and the toll ledger will show who."
stage 20 "I read the toll ledger. Two hands wrote in it."
stage 91 completed "I named Tollkeeper Vel." do set p07.named 1
stage 92 completed "I named nobody." do set p07.named 2
stage 95 failed "Hesh-Ra is dead."

objective 10 at 10 "Read the toll ledger" -> ledger
objective 20 at 20 "Tell Hesh-Ra who robbed the toll box" -> accuser

line job accuser at 0 ask "What is wrong?" -> 10 says "the toll box"
line who accuser at 20 ask "I read the ledger." asks vel, nobody says "who was it?"
line vel accuser answer at 20 ask "Tollkeeper Vel." -> 91 says "she believes it"
line nobody accuser answer at 20 ask "I cannot say." -> 92 says "she is not pleased"

use ledger from 10 -> 20
must-live accuser fails 95
```

**A fight that can be avoided**: the person speaks and is not hostile; a check or a price lets the player past; the
player may attack instead, and the death, marked the player's choice, moves the quest; a killing before the job is
answered at the offer.

```sketch
quest P08 minor "The Toll at the Bridge"
start game 0

place bridge outdoors "the reed bridge"
place town outdoors far "Lilyhall"

person giver at town "Sarel"
person tollman at bridge level 8 "the bridge's tollman"

stage 0 hidden
stage 10 "Sarel wants word taken across the reed bridge, and its tollman lets nobody over."
stage 30 "The tollman let me over the bridge."
stage 40 "I killed the bridge's tollman."
stage 90 completed "I took Sarel's word across the bridge." do give-gold 50
stage 95 failed "Sarel is dead."

objective 10 at 10 "Get over the reed bridge" -> tollman
objective 30 at 30, 40 "Tell Sarel the way is open" -> giver

line pass tollman at 10 ask "Let me over." if skill Speech 30 -> 30 else "Pay or swim." says "he steps aside"
line pay tollman at 10 ask "Let me over." if gold 50 -> 30 says "he takes the coin"
line done giver at 30-40 ask "The way is open." -> 90 says "she pays"
line job2 giver at 0 ask "Any work?" if alive tollman -> 10 says "the bridge"
line already giver at 0 ask "The tollman at the reed bridge is dead." if dead tollman -> 90 says "then the bridge is free, and she pays"

death tollman from 10 -> 40 choice
must-live giver fails 95
```

**A place the record makes hostile, that the story must speak in**: the band stays hostile and moves nothing; the one
who speaks is placed apart, not of the band, at fixed low level; their death before they speak fails the quest
(who must live, until the stage their line sets).

```sketch
quest P09 minor "Word from the Raiders' Ford"
start game 0

place ford outdoors far "the raiders' ford"
place town outdoors "Stormhold's west gate"

person giver at town "Captain Neel"
person raider1 at ford hostile level 6 "a raider of the ford"
person raider2 at ford hostile level 6 "a raider of the ford"
person outcast at ford level 4 "Fen-Tooth, cast out of the band"
item map "Fen-Tooth's map of the ford"

stage 0 hidden
stage 10 "Captain Neel wants to know how many hold the ford. A man the band cast out camps at its edge."
stage 30 "Fen-Tooth gave me his map of the ford." do give map
stage 90 completed "I gave Captain Neel the map of the ford." do take map, give-gold 60
stage 95 failed "Fen-Tooth is dead, and the ford's numbers with him."
stage 96 failed "Captain Neel is dead."

objective 10 at 10 "Speak to Fen-Tooth at the raiders' ford" -> outcast
objective 30 at 30 "Bring the map to Captain Neel" -> giver

line job giver at 0 ask "Any work?" -> 10 says "the ford"
line maptalk outcast at 10 ask "Tell me about the band." -> 30 says "here is my map"
line hand giver at 30 ask "Here is the map." if holds map -> 90 says "good"
must-live outcast fails 95 to 10
must-live giver fails 96
```

## 6. If your outline says this, write that

**What the game can know.**

- "When the player enters the barn / reaches the ruin / finds the camp": a thing used there or a person spoken to
  there moves it.
- "Counting three deaths", "once all the guards are dead": one stage per named death, or a line gated on each dead.
- "Seen or unseen", "if the theft is noticed": nothing; Skyrim's crime system answers it. The quest knows the thing
  is held.
- "Once the stone has left its stand", "the door was forced": the stone held, the door used.
- "If the player has met Teemal": a stage done at which Teemal spoke.
- "A journal note when the player takes the jar" that is not a stage: every journal entry is a stage; if the note
  must not close the working step, it is not written.
- "The kill is open from stage 0": open it from the stage that gives the job; answer an earlier kill with a line at
  the offer.
- A gate on a skill the game does not have (Mysticism, Mercantile, Marksman): a skill it has.

**What the game can do.**

- "He gives the player the charm when asked" (a line that gives, takes, sets a number, unlocks or switches): the line
  moves to a stage, and the stage does it. One stage per outcome.
- "He sells it for 150 gold or Speech 35" on the thing he carries: the stage gives ownership of where it lies, or
  the thing is taken from him; a person cannot hand over what is placed.
- "Told this, he draws": he is not hostile; the player attacks; the death is the player's choice.
- "The roost lets the bearer pass", "the warband stands aside": hostile people do not; the way past is round them,
  through them, or another speaker's line elsewhere.
- "A hostile camp's leader who also sells": two people, or one who is not hostile.
- "His price changes if the player is kind": two lines with two fixed prices, each gated.
- "Two corpses", "a body with the leaves on it": a container that holds them, or a person alive at the start.
- "A ward-stone used as the door's key": the key is a thing the player holds; the stone may be that thing.
- "Teemal is found hauling at the jetty afterwards": a second placement, switched on by a line away from the jetty.
- "If named, he is gone": a stage for named and a stage for not named, each with its own switches.
- "A lesson from the trainer as the reward": a skill book.

**The shape.**

- "Stages 30 and 50 in any order": one working stage; each way's result held, a death, or one stage for the way that
  finishes the step.
- "A failure if both Joxhi speakers die": one person per who-must-live row; or a third speaker whose line is open
  when both are dead.
- "Asheem-Lei speaks for Neeva-Tul if she is dead" (a stand-in): either name who must live, or give the stand-in
  their own line and their own journal entry naming them.
- "A thing on a ledge outside the room": everything the quest uses stands in the place it is used from.
- "A gate the place does not have": the outline's needs of places name it, and the place is built with it.
- "The away rule at the seat": a switch made by a line inside the seat may switch only what is outside it.
- "Forced markers on things the player was meant to discover": a marker is on what the objective names; name the
  place's speaker or a thing to use instead of the secret.
- "Journal entries that claim what the player may not have done": one stage per way, or an entry true of every way.
- "Things taken or people killed before the stage that expects them": a take moves on at once when held; a line
  gated on dead answers a death made early.
- "A dead end once she is dead": she must live, or another way is left open.

## 7. What `sketch` cannot see

These stay the deliverability reader's to check, on the outline and its sketch together:

- that each step of the outline is in the sketch, and each line of the sketch says what the outline says;
- that a journal entry is true of every way that reaches its stage, and names the person who truly spoke;
- that every place need is in the outline's table of needs, and that what it asks a place to hold can be built
  there (a ledge, a gate, a landing);
- that a hostile band cannot reach the person who speaks at its edge, and that a level is right for its place;
- that a stand-in person's lines, a choice's two sides and an ending's switches tell one story;
- that a thing placed in a container is one the container could hold, and a thing the player is told to take is
  where they are told it is.
