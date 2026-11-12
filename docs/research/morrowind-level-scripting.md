# Morrowind-level quest scripting, in practice

What "nothing above Morrowind level" means for an Argonia quest: how Morrowind's quests were actually built, five
real quests taken apart, each Morrowind mechanism set beside Skyrim's matching record, a test of the ceiling in
[walk-6-quests](../phases/walk-6-quests.md#the-ceiling-what-a-quest-may-use), the essential-death message, and
rules for the quest writer. Skyrim counts are from [quest-block-precedent](skyrim/quest-block-precedent.md)
(Skyrim.esm, measured); block names are from [blocks](../design/blocks.md).

**What could be measured, and what could not.** Morrowind.esm is not held on any of our machines, so no Morrowind
count below comes from the game's data. The private Morrowind dialogue corpus
(`~/argonia-private/dialogue/morrowind/morrowind-full.json`, 7,952 lines pulled 2026-10-19) holds speaker, topic,
kind, race, sex, faction, disposition band and the spoken text, plus a free-text `condition` note on 5,160 lines
taken from the wiki page's context; it holds **no filter fields and no result scripts**, so it cannot count them.
Mechanics are therefore cited from *Morrowind Scripting for Dummies*, 9th edition (MSFD; source
[github.com/sultan-of-rum/morrowind-scripting-for-dummies](https://github.com/sultan-of-rum/morrowind-scripting-for-dummies),
file `MSFD9.tex`, cited by its line number), the Construction Set notes, and UESP. UESP refuses automated page
fetches; UESP facts below come from its pages as quoted in search results and carry the page's URL. Where a
number is given it names its source; "common" without a number is a judgement from the sources, said as one.

## 1. How Morrowind's quests work

**The journal is the quest's state.** A quest is one journal topic (an id such as `A1_1_FindSpymaster`) holding
entries by index; the index only ever means "the furthest entry given" ([MSFD L6329-6395](https://github.com/sultan-of-rum/morrowind-scripting-for-dummies)).
- `Journal "ID" n` adds entry n and sets the index; `SetJournalIndex` sets it with no entry (used to restart or as
  a hidden flag; it does not finish a quest, and an index with no entry is lost on reload) (MSFD L6343-6365).
- `GetJournalIndex "ID"` is how every script and line asks "how far is this quest?" (MSFD L6382-6390).
- Indices run low to high, with the finishing entry flagged (from Tribunal, entries carry a quest name and a
  finished flag) ([tes3cs: Dialogue](https://1443481d.tes3cs.pages.dev/actors/dialogue)). Entries are written in the
  first person, past tense: "I have given Caius Cosades the package" ([UESP, Report to Caius Cosades](https://content1.m.uesp.net/wiki/Morrowind:Report_to_Caius_Cosades)).

**Dialogue lines and their filters.** Each response (INFO) under a topic carries
([tes3cs: Dialogue](https://1443481d.tes3cs.pages.dev/actors/dialogue)):
- *Speaker:* ID, race, class, faction, rank (that rank or above), cell (name prefix), disposition (above a value),
  sex.
- *Player:* PC faction, PC rank.
- *Six function/variable slots* ([Notes for Modmakers: Function/Variable](https://morrowind-nifs.github.io/NotesForModmakers-ver.3.3/funcvar.htm)),
  each one of: **Function** (Choice, PC Sex, PC race and class, Talked to PC, Rank Requirement, Same Race, Same
  Faction, reputation, level, and more), **Global**, **Local** (a variable in the speaker's own script),
  **Journal** (an index), **Item** (count the player holds), **Dead** (death count of an ID), and the "not" forms
  **Not ID / Not Faction / Not Class / Not Race / Not Cell / Not Local** (MSFD L6400-6545; L7328 for Dead).
- A topic can also be given to the player by a result (`AddTopic`), so a quest can open a subject only once a line
  has been heard ([Notes for Modmakers: Result](https://morrowind-nifs.github.io/NotesForModmakers-ver.3.3/result.htm)).

**Result scripts.** Each response may carry a short result script that runs each time that line is delivered,
after it is shown ([Notes for Modmakers: Result](https://morrowind-nifs.github.io/NotesForModmakers-ver.3.3/result.htm);
tes3cs says one-line commands only, no `if` blocks). The calls MSFD's list of "useful and frequently used" result
commands names (MSFD L5903-5950), with the others the sources show in use:

| Call | What it does |
|---|---|
| `Journal "ID" n` | advance the quest (the most used call in quest lines; judgement, from every quest page read) |
| `Player->AddItem` / `RemoveItem` | reward, hand-over, take the fetched thing |
| `ModDisposition n` | the speaker likes the player more or less |
| `PCJoinFaction`, `PCRaiseRank`, `ModPCFacRep` | faction entry, promotion, guild reputation (MSFD L5154-5234) |
| `Choice "a" 1 "b" 2` | ask a question; the same topic is checked again with the Choice filter (MSFD L6290-6300) |
| `Goodbye` | close the conversation (often after `Disable`) |
| `StartCombat player`, `SetFight` | the speaker turns hostile |
| `Disable` / `Enable` | the speaker or a thing vanishes or appears |
| `AIFollow`, `AIWander`, `AITravel`, `AIEscort` | follow, stop following, walk somewhere, lead |
| `StartScript` | start a global script for anything a line cannot do |
| `PositionCell`, `cast`, `SetHealth`, `set <var> to n` | move, spell, stat, a variable (local or global) |

**Local scripts on people and things.** A script attached to an object runs every frame while its cell is loaded.
Quest uses: `OnActivate` (the player uses it), `OnDeath` (true for one frame; only one script sees it), `OnMurder`,
`GetDeadCount "ID"` (MSFD L7291-7335), `GetDistance` to the player (MSFD L3670-3700), `GetItemCount`, and
`GetJournalIndex` polled to act once at the right point. Every such script needs a do-once flag, or it repeats each
frame (MSFD L1189; L6209-6232 on a looping ForceGreeting).

**Global state.** Globals were few: 73 GLOB records in all of Morrowind.esm, of 48,228 base records
([UESP mw_esm.txt, 2003](https://chat.uesp.net/morrow/tech/mw_esm.txt), as quoted in search results). Quest state
lived in journal indices and in speakers' own local variables, not in a shared store.

## 2. Five quests taken apart

**The opening: Census and Excise, then Report to Caius Cosades (`A1_1_FindSpymaster`).** Character creation is
the one place Morrowind is heavily scripted: local scripts on the chargen people and doors (`CharGenBoatNPC` says a
recorded line when the player is within 180 units and repeats a short bark on a timer; `CharGenWalkNPC` walks the
player through the ship; `CharGenDoorExit` catches a player who runs out early), and the `CharGenState` global
locks saving and menus until it ends (MSFD L4461, L4826, L8180-8196, L8787-8792, L9969-9996). Socucius Ergalla's
lines open the class and birthsign menus and the release papers appear on his table
([UESP, Character Creation](https://en.m.uesp.net/wiki/Morrowind:Character_Creation)). From there the main quest is
plain talk and things: Sellus Gravius takes the papers, gives a package and sets index 1 (go to Balmora, find
Caius); in Caius's line the result takes the package and sets 14, pays 200 gold (18), then gives the cover
identity (20 or 22: the UESP mirrors disagree)
([UESP](https://content1.m.uesp.net/wiki/Morrowind:Report_to_Caius_Cosades),
[pt mirror](https://pt.m.uesp.net/wiki/Morrowind:Report_to_Caius_Cosades)). Nothing moves the journal but a line;
the only gate is "holds the package"; Caius never comes to the player.

**A faction fetch: The Code Book (Fighters Guild, Eydis Fire-Eye).** Index 10 when Eydis gives the order; the book
is held by Sottilde in the South Wall Cornerclub and can be bought, stolen or taken from her body; Eydis's turn-in
line is gated on the player holding it, and its result takes the book, pays 50 gold, +10 disposition, +5 Fighters
Guild reputation and -10 Thieves Guild, and sets 100. UESP's table has 10, 30, 50 and 100 and notes that 30 "doesn't
appear to trigger" ([UESP, The Code Book](https://content1.uesp.net/wiki/Morrowind:Code_Book)). The quest does not
care how the thing arrived: three ways of doing it, one condition.

**A choice: Fargoth's Ring (`MS_FargothRing`).** The ring is found in Seyda Neen; giving it back is a topic with
Fargoth whose line checks the ring is held, takes it and sets 100 (+50 disposition); keeping or selling it is the
other choice, made by not doing it (a Nexus guide gives -20 disposition for selling it)
([UESP, Fargoth's Ring](https://en.uesp.net/wiki/Morrowind:Fargoth's_Ring);
[Nexus article 366](https://www.nexusmods.com/morrowind/articles/366)). A follow-on quest gives a second chance at
it. The choice costs no script: an item check and a line.

**An escort: A Man and His Guar (`MV_RichTrader`).** Teris Raledran asks to be led with his guar to a safe spot and
then to a clothier in Vivec; the journal moves when he arrives, and he must survive the road
([UESP, A Man and His Guar](https://En.UESP.net/wiki/Morrowind:A_Man_and_His_Guar)). Escort quests in the
base game named on UESP pages found: eleven (Tarvyn Faren, Itermerel, Tenyeminwe, An Escort to Molag Mar, A Man and
His Guar, the Koal Cave pilgrim, Reeh-Jah, Pemenie, Paur Maston, the Ahemmusa Nerevarine escort, To the Fields of
Kummu) ([Followers](https://content2.uesp.net/wiki/Morrowind:Followers),
[Miscellaneous](https://content3.uesp.net/wiki/Morrowind:Miscellaneous)). **Reliability:** Tarvyn Faren catches on a
bridge post with no known fix ([UESP](https://content2.uesp.net/wiki/Morrowind:Escort_Tarvyn_Faren)); escorts stop
for good after leaving a tent ([talk page](https://www.uesp.net/wiki/Morrowind_talk:Ahemmusa_Nerevarine)) or freeze
behind a shrine ([talk page](https://en.m.uesp.net/wiki/Morrowind_talk:To_the_Fields_of_Kummu)); mods raise escorts'
health and speed to make them survivable ([Nexus article 495](https://www.nexusmods.com/morrowind/articles/495)).
MSFD records `AIEscort` as unreliable through load doors (an NPC using a load door crashed the game) and
`AITravel` as stopping whenever the walker is distracted or the player rests (MSFD L4755-4830, L4461-4475).

**Speaking first and arriving: Mephala's quest (`DA_Mephala`) and Dreams of a White Guar (`MS_WhiteGuar`).**
Balyn Omavel's script, as MSFD prints it (it sets the game's own `DA_Mephala` journal), checks every five seconds, once only: the player within 1,024 units, the player within 256
of his door, and in his line of sight; then `ForceGreeting` and `Journal DA_Mephala 55`
([MSFD script balynScript](https://github.com/sultan-of-rum/morrowind-scripting-for-dummies/tree/main/scripts)).
UESP warns that if he sees the player the quest is ruined
([UESP, Mephala's Quest](https://content1.uesp.net/wiki/Morrowind:Mephala's_Quest)). In the white guar quest a
script sets index 60 when the player and the guar are both within 256 units of Ashamanu's body and the index is at
most 50 (MSFD L3680-3700); the guar walks west on its own when approached
([UESP](https://content1.m.uesp.net/wiki/Morrowind:Dreams_of_a_White_Guar)). ForceGreeting only works remotely if
the player met the person in the last 72 game hours (MSFD L6177-6195). So Morrowind **did** move the journal by
where the player stood, through distance checks in local scripts.

## 3. Mechanism by mechanism

"How common" is a judgement from the sources above unless a count is given. Skyrim counts are Skyrim.esm's.

| Morrowind mechanism | How common in Morrowind | Skyrim's record or vanilla script (count in Skyrim.esm) | Our ceiling |
|---|---|---|---|
| Journal entry by line result | every quest | TIF_ fragment `SetStage` (5,540 INFOs with a fragment); TR-topic | inside |
| Line gated on journal index | every quest | GetStage / GetStageDone (8,029 / 4,175 uses) | inside |
| Item filter; take or give items | most fetch and delivery quests | GetItemCount (678); TIF_ AddItem/RemoveItem; E-item | inside |
| Faction, rank; join and promote | every guild line | GetInFaction / GetFactionRank (6,904 / 259); ALFC (1,215); E-faction | inside |
| Faction reputation (`ModPCFacRep`) | every guild quest reward | none in Skyrim; a global per faction (GetGlobalValue, 1,579) | inside as a stored number |
| Disposition filter; `ModDisposition` | very common, 0 to 100 | relationship rank -4 to 4 (`SetRelationshipRank`); E-regard | inside, coarser |
| Dead filter; `GetDeadCount`; `OnDeath` | every kill quest | GetDead (1,028); `defaultSetStageOnDeathRefAlias` (20 quests); `defaultCounterIncrementOnDeath` (47 records) | inside |
| Choice | common | an answer INFO in the question's branch; TR-choice | inside |
| Global variable | rare: 73 globals in the game | GLOB + GetGlobalValue (1,579) | inside |
| Speaker's local variable | common (Nolore, flags) | quest-held global or stage; no per-actor variable in records | inside as a stored number |
| PC race, sex, class filter | common in greetings | GetPCIsRace / GetPCIsSex conditions | **missing from the list** |
| Speaker ID, race, faction, cell | every line | GetIsID (19,169 uses); location conditions | inside ("who is speaking"); cell is cut |
| Talked to PC | common in greetings | GetTalkedToPC | not listed |
| `OnActivate` local script | common | `defaultSetStageAliasScript` family (119 quests); TR-activate | inside |
| Pick-up (`OnPCAdd`) | rare; turn-in checks the item instead | `defaultSetStageOnPlayerAcquire` (16 quests); TR-acquire | inside |
| `GetDistance` local script moves the journal | occasional (white guar, Balyn) | trigger box `defaultSetStageTrigScript` (327 refs); TR-zone | **cut** |
| `ForceGreeting` | occasional, by distance check | ForceGreet AI package | inside, once per quest |
| `StartCombat` in a result | common for confrontations | TIF_ `StartCombat(player)` | **missing from the list** |
| `Enable` / `Disable` | common, often in view after `Goodbye` | enable parent XESP (23,239 refs); E-enable | inside, away from the player only |
| `PositionCell` | rare (chargen, a few moves) | `MoveTo` a marker; E-move | inside for the player through a door |
| `AIFollow` / `AIEscort` / `AITravel` | eleven escort quests and more followers | alias packages (4,125 ALPC in 365 quests); E-package | cut |
| `MessageBox` | common in scripts | `Debug.MessageBox` or a MESG record | inside |
| `StartScript` (global script) | the escape hatch for anything else | quest script | cut |
| Time of day, days passed | rare | GetCurrentTime (518); GameDaysPassed (8 records) | cut |
| Scripted chargen set piece | once, the opening | MQ101 (scenes, packages, triggers) | cut, beyond the barge |

## 4. The ceiling, tested

**Where the plan allows what Morrowind did without, or did differently:**
1. **Taking a named thing moves a stage.** Morrowind almost never did; it checked the item at the turn-in line
   (The Code Book, Fargoth's Ring). A pick-up trigger fires whenever the thing is taken, including before the quest
   reached that stage or after it ended, and the item may arrive by purchase, theft or a body. Keep the pick-up
   trigger only for a journal note ("I have the book"); the stage that matters is set by the turn-in line, gated on
   the item count. A quest must work if the player already holds the thing.
2. **The force-greet is an AI package.** Skyrim's speak-first is a ForceGreet package, which sits under the plan's
   own cut ("any package that makes a person walk"). The ceiling should name it as the single allowed package and
   say how it ends (the line's result removes it), or the form check will either refuse it or let packages in.
3. **Moving the player through a door.** Morrowind used `PositionCell` on the player almost only in chargen. A
   door the player walks through needs no result at all; a result that teleports is a set piece. Limit it to
   unlocking or opening the door.

**Where the plan cuts what Morrowind used, and whether that loses anything:**
4. **Walking into an area.** Morrowind moved the journal by distance (the white guar, Balyn). Cutting it is
   stricter than Morrowind. What is lost: "I found the place" entries. The substitute is a named thing at the place
   that the player uses or reads (a body, a marker stone, a note), which gives the same entry from a deliberate act.
   The cut is right for us; the note says plainly that it is stricter than Morrowind.
5. **Escorts and following.** Eleven named escort quests, and the sources show them as the most fragile kind. The
   cut loses "bring this person safely to X". Substitute: the person says they will go ahead, is disabled where
   they stand once the player is in another cell, and is enabled at the destination; the player meets them there.
   The danger of the road becomes a fight the player has on the way.
6. **A line that starts a fight.** Missing from the allowed results, and common in Morrowind: the smuggler who
   draws a blade when refused, the target who attacks when named. Without it, every confrontation must be a person
   placed hostile from the start. `StartCombat` from a line result is a single engine call with no package or
   timing; add it ("this person attacks the player") to the results.
7. **The player's race and sex.** Missing from the allowed conditions. Morrowind filtered greetings and some quest
   lines on PC race all the time, and in Black Marsh whether the player is Argonian is the first thing anyone
   notices. GetPCIsRace and GetPCIsSex are plain conditions; add them.
8. **Talked to the player before.** Not listed; a first-meeting greeting needs it. Add it, or model it as a stage.
9. **Where the player stands, as a line condition.** The plan cuts it; Morrowind's Cell filter was used for
   place-specific lines (a guard who speaks of his own town). It is not needed for quest progression; the cut is
   fine if place lines are written as the speaker's own topics.
10. **A global script.** Morrowind's escape hatch for everything a line could not do. Cutting it is the point of
   the ceiling; there is no substitute and none is needed if a quest stays inside sections 1 and 3.
11. **Regard is coarser.** Morrowind's 0 to 100 disposition allowed "persuade until she likes you enough". Skyrim's
   relationship rank has nine steps. Gate on a stored number for any quest-specific liking, not on regard.

**What Morrowind shows the plan already has right:** its quest state was one number moved by talk (sections 1 and
2); a choice cost an item check and a line, not a branch of script; and the one heavily scripted part of the game,
character creation, is the part we keep (the barge) and should not grow.

## 5. The message when an essential person dies

Morrowind's text, exactly ([UESP, Essential NPCs](https://content1.uesp.net/wiki/Bloodmoon:Essential_NPCs),
[Morrowind talk: Essential NPCs](https://content2.uesp.net/wiki/Morrowind_talk:Essential_NPCs)):

> With this character's death, the thread of prophecy is severed. Restore a saved game to restore the weave of
> fate, or persist in the doomed world you have created.

It appears in a message box at the moment a person flagged essential dies. The game does nothing else: saving is
not blocked, the flag is never cleared, and no quest is failed by the engine (the talk page above; UESP says the
main quest can no longer be finished, and a Steam thread disputes that it changes anything:
[Steam discussion](https://steamcommunity.com/app/22320/discussions/0/1694914735992552654)).

Three candidates for Argonia, each two sentences (what is broken; load a save or go on), checked with
`.claude/skills/dialogue-write/lint.py --race argonian` (0 hits). The root echoes the Hist's roots and the main
quest's name, *The Eye and the Root* (`story/design/quests/30-main-quest.md`); the mood is the province's
"melancholy and dignified" ([province-vibe](../../story/design/province-vibe.md) §1).

1. **Recommended.** "With this death the root of what was to come is cut: the main story can no longer be
   finished. Load an earlier save to let it grow again, or go on in the marsh as it now is."
2. "This death cuts the Eye from the Root. Load an earlier save to mend it, or go on in a marsh where the main
   story cannot end." (Shorter, but "the Eye" means nothing to a player who has not met it.)
3. "A life on which the marsh's fate rested has ended: the main story can no longer be finished. Load an earlier
   save to undo it, or live on in a world that this death has changed."

## 6. What this means for a quest writer

1. A quest is one number moved by talk. Every stage is set by a line the player picks, a thing the player uses or
   reads, a death, or another quest's stage.
2. Write each journal entry as Morrowind did: first person, past tense, only what the player has just done.
3. Gate the turn-in line on the thing being held, never on how it was got; the quest must work if the player
   already has it, bought it, stole it or took it from a body.
4. A choice is a question with answers, or an act the player may simply not do; each answer sets a stage or a
   stored number and nothing else.
5. People do not walk for a quest. If someone must be elsewhere, they are moved while the player is in another
   cell, and the line says they went ahead.
6. One person per quest at most may speak first, standing a few steps from where the player arrives.
7. A confrontation is a line whose result makes the speaker attack, or a person placed hostile; never a scene.
8. Nothing appears, vanishes or burns where the player can see it. Events that matter have already happened and
   are found, or are told.
9. Anyone can die. Every line of a quest must read sensibly with each named person dead, or the quest names them
   as one it cannot go on without.
10. If a step needs anything not in sections 1 and 3 of this note, rewrite the step; never add a script.
