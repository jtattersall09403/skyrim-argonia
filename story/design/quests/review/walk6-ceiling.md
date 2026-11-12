# Every line and faction at the Morrowind-level ceiling

The owner, 2026-11-12: "review everything else for all the quests and stories and factions that we've authored so
far. I want to keep the spirit of what we intended, but massively row back the scripting ambition. Nothing higher
than Morrowind level." The ceiling is the closed list in [walk-6-quests](../../../../docs/phases/walk-6-quests.md)
("The ceiling: what a quest may use"); the substitutes are those of
[morrowind-level-scripting](../../../../docs/research/morrowind-level-scripting.md) §4 and §6. This file lists, for
the main line and each faction line, every premise or set piece that asks for more than the ceiling and what it
becomes at the ceiling, keeping its spirit; quests that already fit are counted, not listed. The local quests are
counted by kind of excess, with one standard substitute per kind.

Sources read: [main-line-outline](../main-line-outline.md) (Acts I to V), [40-factions](../40-factions.md) (each
line's table), [50-side-quests](../50-side-quests.md), [adaptation](../adaptation.md) §2, and the premise and spirit
of every quest without stages (`story/data/db/quest.jsonl`, `quest_adaptation.jsonl`; 668 quests). The 49 quests
with stages are records and are fitted to the quest form one by one (`story/data/questform_owed.json`).

## The standard substitutes

One substitute per kind of excess, used the same way on every line. A quest that needs a step none of these covers
is rewritten until one does; it never gains a script.

| Kind of excess | At the ceiling |
|---|---|
| Walking into a place moves the quest ("find the den", "reach the house") | A named thing at the place that the player uses or reads (a dropped tool, a carved stake, a book), or the person who stands there and is spoken to |
| A place cleared | The death of the one named person or creature whose death matters |
| Escort, follow, lead, a procession | The person says they will go ahead: that line switches on their placement at the destination (far away), and the player's first line with them there switches off the one left behind (far away in turn); the road's danger is a fight the player has on the way |
| Chase, manhunt, race, intercept with a timer | The quarry is already where the evidence says (a placed person or a thing left behind); the player reads the evidence and goes there; nothing runs and nothing is timed |
| By the clock: tonight, before dawn, before the rains, a season, a tide, a deadline, a schedule | A state the player finds or is told of; the quest waits for the player; a person keeps one post for the whole quest |
| Unseen, at night, in disguise, under cover | The deed itself moves the quest (the take, the use, the line); being seen is left to the game's own crime and combat, never a quest gate; a cover is a Speech line that opens a door or gives a pass |
| A scene: a sermon, a council, a hearing, a trial, a vote, a rite, a ceremony played out, a crowd | One person speaks for the gathering: what it says is a line, what it decides is a question with one answer line per outcome; the gathering itself is told |
| A staged attack, ambush, raid, riot, battle | Hostiles placed where they wait from the start, or one line whose result makes the speaker attack; a raid or a riot is aftermath the player finds or is told of |
| Fire, flood, collapse, storm happening | It has already happened: the burnt, flooded or fallen state is what the place holds when the player arrives |
| A dream, vision or sap-dream sequence | A message box and a journal entry when the player takes, reads or uses the named thing (the sap, the jewel) |
| A moving boat, cart, ferry or rootworm ride | Boats stay moored; travel is the player's own walk or swim; a ride is told |
| A transformation, summoning or magic effect a script must run | Told in lines, or a thing given (a scroll, a potion) that the player uses in the fight |
| Local state variants, schedule swaps, end-state swaps | Named things or people switched on or off away from the player (another cell, or set by a line spoken far away), and a letter given |
| A new structure (a hull, a hut, a door pair, an interior) | An existing place of BM&V's or the load order's; nothing is built |

## The main line (The Eye and the Root)

17 quests in the outline (Act I records MQ01, MQ03, MQ04, MQ05; MQ32 is a staged record folded into MQ31). 16 set
pieces are rowed back; MQ08 and MQ09 already fit. The outline ([main-line-outline](../main-line-outline.md)) now carries
the ceiling versions; nothing in it promises a staged set piece.

| Quest | Above the ceiling | At the ceiling |
|---|---|---|
| Act I hook | The camp burns, a woman takes the courier's satchel and spares the player, a clutch dies "that night" | Told and found: the camp has burned before the player reaches it, and its ruin, the satchel's loss and the dead clutch are what people say and what the place holds (lanes O and Q1 own the records) |
| MQ07 | A sale played out to rival buyers; the Collector withdraws at the last moment; the smugglers find the setting gone and give chase | The sale is told; taking the setting from the strongroom chest moves the quest; the Collector's word is a note left with the smugglers' chief; guards stand at their posts and fight as guards do if they catch the player |
| MQ10 | "Word comes" that a second Hist has been cut; a hull placed in the water | The handler tells it when the three pieces are handed in (a line gated on holding all three); the wreck is an existing one, chosen when the quest is fitted |
| MQ16 | The Collector's divers race the player through the dry chambers | The divers are already in the chambers, placed hostile |
| MQ16 | A light alignment opens the way | The inner door is opened by a lever or by a key the guardian carries |
| MQ16 | On touching the Eye the sap-dream comes unbidden | Taking the Eye shows the dream as a message box and a journal entry |
| MQ18 | The sermon as a scene in the undercroft | The Collector's sermon is what he says when the player speaks to him |
| MQ18 | A failed cover turns the house on the player (six hostiles) | A failed Speech line turns the player out; the cult's mark is then taken from the undercroft's locked chest instead; both reach the same stage |
| MQ20 | The freed dreamers leave on their own | The player opens the cells; the dreamers are switched off when the player reports to the handler far away |
| MQ21 | The Reed's raid burns the house and its stock while the player is inside; the volunteers walk out | Telling the truth is a line; the house's stock is switched off and its volunteers are gone when the player next comes (switched by that line, far away); lying is a line that lets the player keep the stock |
| MQ23 | The Eye lights marks no one else can see | The marks are carved stones always there; using one while holding the Eye moves the quest and shows what the Eye reads in a message |
| MQ26 | The Eye reads the carvings | Using the carving while holding the Eye moves the quest; the reading is a message and a journal entry |
| MQ27 | Walks-Against-Current leads and waits at the far side of every swim and climb | Her blazes mark the way; she goes ahead once and is found at the basin's far side; the dangers are placed predators |
| MQ27 | The guide's boat as a return route | Her map of the basin (a thing given); the way back is walked |
| MQ29 | The consent rubbing weakens the Last Warden; the Lost City's Xanmeer is a new interior | Using the rubbing at the Warden's seal gives a ward-breaking scroll the player can use in the fight; the city is an existing ruin chosen when the quest is fitted |
| MQ31 | Cuts-the-Old-Knot "mid-rite"; CUT, CLAIM or MEND as acts; a closing scene and end-state swaps | She stands at the door holding the Egg; the three ends are three named things at the Root, each used while holding the Egg or the Eye; a closing message and journal entry; the changes in Helstrom and Low-Reed Village are switches far from the Root |

## Faction lines

### Shadowscales (The Empty Cradle): 8 rowed back, 2 fit (SS03, SS07)

| Quest | Above the ceiling | At the ceiling |
|---|---|---|
| SS01 | The last Shadowscale dies in the player's hands; one small ambush | He gives the task as a dying man; when the player comes back with the list his body lies where he lay (switched while the player was away); the facility's hostiles wait where they are placed |
| SS02 | A target's home and work route | The target keeps one post for the quest |
| SS04 | A claimant's schedule; a duel arena | The claimant stands in his yard; a duel is a line whose result makes the challenger attack |
| SS05 | A four-actor negotiation | The emissary speaks for the Brotherhood; the others are told |
| SS06 | Patrol schedules | Guards stand at posts; the approaches are the player's own (poison, sneak, speech) |
| SS09 | The Night Mother rite with a staged deception, lighting variants and a secret observer route | The rite has happened: its leavings and the witnesses' lines show the deception |
| SS08, SS10 | Banner and guard states; schedule swaps and four headquarters states | One question with four answer lines; the headquarters' changes are switches away from the player; a letter given |

### Night-Reed Chapter: 7 rowed back (TG04 re-authored as a record), 1 fits (TG05); TG01 and TG02 are lane Q3's records

| Quest | Above the ceiling | At the ceiling |
|---|---|---|
| TG03 | Dock patrol schedules and a boat route | Posted guards; the boat is moored |
| TG04 | A houseboat moved between moorings by schedule; take it unseen or fail | It stays at one mooring; taking the tally is a journal note and handing it in (gated on holding it) ends the quest; being seen is the crime engine's |
| TG06 | The packet intercepted during a rootworm transit; impersonation | The packet is taken from the station's strongbox before transit; the cover is a Speech line that opens the strongroom door |
| TG07 | Surveillance perches and a staged accusation scene | The informer is shown by things found in three homes; the accusation is a line to the den's head |
| TG08 | Patrol routes in the vault | Posted guards; four entrances, each a door or a swim |
| TG09 | The "inside schedule" preparation | A duty roster that names an unwatched door and gives its key |
| TG10 | Patrol schedule, disguise checkpoints, boat escape | Posted guards; each checkpoint is a Speech line or a pass held; the way out is a door; eel-slime stays (a thing used) |
| TG11 | Fence schedules and property changes | Switches away from the player and letters given |

### Marsh Charter: 7 rowed back (FG07 re-authored as a record), 3 fit (FG02, FG04, FG09)

| Quest | Above the ceiling | At the ceiling |
|---|---|---|
| FG01 | Creatures come at the village along approach lanes | The creatures wait in their den; the player goes to them |
| FG03 | Relocate the juvenile wamasu | Return the eggs to the nest (a thing used); the wamasu is gone when the player reports to the farms (switched there, far away) |
| FG05 | Council scenes; guard assignment variants | The commander's question with answers; the guards' change is a switch away |
| FG06 | Reason that comes and goes | He speaks sense once given the healer's draught (a line gated on the draught held) |
| FG07 | Clear the roadside camp, an ambush route | The bandits' chief's death moves the quest (record) |
| FG08, FG10 | Branch banners; four guildhall states, patrol and board swaps, letters | Switches away, a letter given |

### Sunken Archive: 6 rowed back, 4 fit (SA01, SA03, SA04, SA06)

| Quest | Above the ceiling | At the ceiling |
|---|---|---|
| SA02 | A ritual pool and a memory effect | The fragment is a thing read; its memory is a message |
| SA05 | A negotiation scene | The Synod envoy's lines |
| SA07 | Access and occupation variants | Switches away from the player |
| SA08 | A construct met "later, in a worse place" if the wake is misread | The player tells the warden which point to hold (one answer line each); the construct is switched on at that point, far from where the player chose |
| SA09 | Office schedules | Each scholar keeps one post |
| SA10 | Final state variants and reaction sockets | Switches away and a letter given |

### Nisswo of the Turning Path: 7 rowed back (NI05 re-authored as a record), 3 fit (NI01, NI03, NI09)

| Quest | Above the ceiling | At the ceiling |
|---|---|---|
| NI02 | A silent Nisswo takes the player with her for a day along six stops; wrong order is played out in public | She stays at her shrine and gives six signs; each is a named thing at a stop, used in order (each use gated on the one before); using one out of order gives its keeper's rebuke line; what it meant is never said |
| NI04 | A dream-light state | The mourner tells the dreams |
| NI05 | The offering at the bend as a local variant | Dropped; the nisswo takes the offering in a line (record) |
| NI06 | Home schedules and role swaps | Each person keeps one post; the swap is a switch away |
| NI07 | A travelling priest on a pilgrimage route | He is found at one camp for the quest |
| NI08 | A hearing room; a ritual death | The hearing is the elder's question with answers; the death, if chosen, happens away and is told |
| NI10 | Travelling-NPC schedules and rumour pools | Switches away and greetings that change with the stage |

The Seven-Graces-style pilgrimage circuit in the authoring nudge fits as it stands: each shrine is a named thing used.

### Many-Root Conclave: 10 rowed back (MR01 re-authored as a record), none fit as written

The line's rule "discover in danger, decide in council" is kept: the danger is the player's own (a dive, a den, a
fence), and every council or hearing is one speaker's question with an answer line per outcome.

| Quest | Above the ceiling | At the ceiling |
|---|---|---|
| MR01 | Start on entering the village; the council scene; local cure variants | Ixo-Vaal's line starts it; his question with three answers ends it (record) |
| MR02 | The nursery floods tonight; a night boat run through a drowning forest; terms answered standing in the boat | The nursery has flooded; the player carries the clutch basket by the root path to the receiving dock; the terms are answer lines there; the weir is found opened upstream |
| MR03 | A night entry past the garden watch; the hearing | Past the posted watch (the crime engine); the hearing is Tuwul's question |
| MR04 | A night shift, a disguise flag, blown cover turns the camp hostile along an escape route | In over the fence or by the foreman's hiring line (a Speech line that opens the gate); the roster is a thing taken; the camp's guards fight as guards do |
| MR05 | The council decides | The elder's question with answers |
| MR06 | A span fails; a teamster pinned with the tide coming in (a timer) | The span has failed; the teamster is freed by using the beam, with no timer |
| MR07 | A sap-dream sequence with fog, light and rearranged props | Taking the vigil sap shows the dream as a message |
| MR08 | A great council of 6 to 8 actors run by procedure | Each obstacle cleared is a stage; the council is the chosen desk's question with answers; the delegates are told |
| MR09 | A hearing staged by survivors | The survivors' spokesman's question |
| MR10 | Reach the loading dock ahead of the boat, on a shared timer | The crew is found loading at the dock; the player stops them by a line or a fight; nothing sails |

### Reed-Sail Compact (with the Salt-Teeth arc): 9 rowed back, 5 fit (RS03, RS05, RS06, ST01, ST04)

| Quest | Above the ceiling | At the ceiling |
|---|---|---|
| RS01 | Qualify on a working ferry: current, passengers, a staged obstruction | Clear the snag at the crossing (a thing used), answer the old pilot's questions of the river (a question with answers) and carry a passenger's goods across on foot |
| RS02 | A night ferry evading watcher boats by route and lights | The fugitive waits at the landing; the player names the hidden landing (an answer line); the fugitive is switched off and found there; the watchers are posted people the player may face or avoid |
| RS04 | Patrol schedules | Posted guards |
| RS07 | Ships trapped in a storm; a boat-trip timer; survivors landed; a letter read aloud | The storm has driven three craft aground; the harbour master's question allocates the rescue (one answer each); the player swims to one craft for its people's word; the letter is a book read |
| RS08 | A physical chain across the river | Told; nothing built; the checkpoint is an office |
| RS09 | A dock assembly and an election | The electors are persuaded one by one in lines; the hall's keeper announces the result |
| RS10 | Service variants across hubs | Switches away and a letter given |
| ST02 | A prize that carries passengers home | Told |
| ST03 | A mud bank at low tide settles the lead | A duel on the mud bank, begun by a line; no tide |

### League of Open Water: 8 rowed back, 2 fit (LW01, LW09)

| Quest | Above the ceiling | At the ceiling |
|---|---|---|
| LW03 | A ration queue scene | The shortage is told; the warehouse is a door and a ledger taken |
| LW04 | The killer bolts; three intercepts on a timer; a gate dropped; hunted on the way back with the witness | The evidence names his hiding place; he is found there; the witness goes ahead to the League hall; the road's hostiles are placed |
| LW05 | The ordeal played out | Challenged or defended in lines before the court; if undergone, the player dives the basin for the token (a take) |
| LW07 | A vote counted | The electors are lines; the result is told |
| LW08 | Canal alternatives as built local states | The design chosen is an answer line; the works are told; nothing built |
| LW02, LW06, LW10 | Ownership, occupancy and district state swaps | Switches away and a letter given |

### Blackrose Chainbreakers: 4 rowed back, 2 fit (BC01, BC03; both lane Q2's records)

| Quest | Above the ceiling | At the ceiling |
|---|---|---|
| BC02 | The heirs' outer post is burning; one of three brought out (record, lane Q2) | The fire has burned; one of three is still held and freed |
| BC04 | A riot prepared and played | The riot is aftermath; the choice is lines with the three leaders |
| BC05 | A procession on a waypoint leash through contested crossings | The player opens each crossing first (a line or a fight); Grave-Singer Ossu goes ahead and is found at the burial ground |
| BC06 | Rose, estate and toll state swaps | Switches away; a letter given |

### Thorn Ash-Reed Accord: 3 rowed back, 2 fit (TA01, TA03)

| Quest | Above the ceiling | At the ceiling |
|---|---|---|
| TA02 | A manhunt down the border channels by scheduled ferry to timed intercepts | The departure boards and pilots name one landing; the partner is found there; the player walks or swims |
| TA04 | Evacuation scenes | The lists are things taken; the evacuation is told |
| TA05 | Guard and schedule variants | Switches away |

### Umbriel Witness Society: 1 rowed back, 4 fit (UW01 to UW04)

UW05's archive state variants become switches away and a letter given. UW04's trek is the player's own walk.

### Rootworm Waykeepers: 3 rowed back, 2 fit (RW01, RW03)

The worm is never on screen and nobody rides it: transit is told. RW02's traveller is switched off at the pen while
the player is away and is gone; RW04's two route states and RW05's four ends are switches away from the player.

## Daedric quests: 4 rowed back, 4 fit (DQ01, DQ04, DQ06, DQ07)

| Quest | Above the ceiling | At the ceiling |
|---|---|---|
| DQ02 | A memory the game really removes | The price is a named keepsake taken (take_item) |
| DQ03 | Hunters pursue a beast; the player marked as prey | The beast waits in its lair; the marked hunter is told by the hunt's priest; the hunt ends at the lair |
| DQ05 | A cowl that erases its wearer from memory | The villagers' lines never name the wearer; nothing runs on the player |
| DQ08 | A mask that hears and swaps wants | The mask's whispers are lines gated on holding it |

## Proposed quests: 4 rowed back of 18

PP10's yearly recession, PP14's moonless light, PP15's power over weather and PP16's seasonal sluices are states
found or told, never clocks; nothing else in the bin asks for more than the ceiling.

## Local quests (527 without stages)

Scanned by keyword (escort, follow, lead, chase, ambush, raid, timed, before dawn, at night, unseen, disguise, race,
siege, battle, ceremony, trial, crowd, fire, flood, collapse, dream, vision, boat, cart, transform, summon, set
piece); 90 premises matched and were read. 70 are false matches: the rite, council or trial is the custom at stake,
not a scene to play, or "burn" names the burn country. 20 need the ceiling's substitute:

| Kind | Count | Ids | Standard substitute |
|---|---|---|---|
| Clock, night or timetable | 8 | ld04, ld16, lf45, lf88, lh31, lh55, lm41, ln12 | The nightly or timed act is found by its traces or told by a witness |
| Race or dawn deadline | 2 | lm05, lm85 | The rival's work is found done (the forged page, the emptied boat) |
| Escort or follow | 1 | ln13 | The scholar has gone in ahead and is found inside |
| Ceremony, game or crowd played out | 4 | ld33, lm24, lm64, lq02 | One speaker's question decides it; the gathering is told |
| Staged haunting, wonder in motion, signal | 3 | lf07, lf64, lv09 | The state is found (a diary, a lit pyre, a stone turned since the last visit) |
| A thing burning or flooding now | 2 | lf31, lr41 | The fire is kept or put out by a thing used; nothing burns in view |

**Premises rewritten in the database** (the text promised a cut mechanism): lf07, lf45, lh31, ln12, ln13.

**Proposed cut:** lm64 (A Side in the Court). Its quest is a Teeba-Enoo match the player plays in, short two
players; at the ceiling the match cannot be played and a told match leaves nothing of the premise. Cut, or merge its
diplomatic problem into another quest at the same port. Every other local premise survives.

## Premises rewritten in the database (faction and main lines)

MQ07, MQ23, MQ27, MR02, MR04, MR06, NI02, RS01, RS02, RS07, ST03, TG06: each premise and its spirit line
(`quest.premise`, `quest_adaptation.spirit`) kept its title and meaning and lost the mechanism the ceiling cuts (an
auction played, marks that light up, a guide who leads, a flood tonight, a night harvest, a span that fails in
view, gestures copied, a staged obstruction, a night ferry, a storm in progress, a tide, an interception in
transit). The five local premises above had their spirit lines rewritten the same way.

## Still to carry over

- The written dialogue of LF83 (Claywater Station) still names the keepers' timetables (the well in the morning,
  the counter in the afternoon) and the rains as a deadline; lane D rewrites those lines with the record.
- [adaptation](../adaptation.md) §2's beats and the `line_spirit` rows repeat a few of the set pieces above in
  the words of the original design (MR02's night boat run, MR04's blown-cover escape, RS02's watcher boats, TA02's
  manhunt, NI02's six-stop day); a line's beats are rewritten from this file when the line is first fitted.
