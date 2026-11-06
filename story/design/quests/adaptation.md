# The whole quest system on BM&V: the adaptation plan

The human-readable plan for Phase 2's "whole quest system on BM&V" ([phase 2](../../../docs/phases/2-first-act-on-paper.md)):
per line its spirit, its new home in BM&V, what changed and why, and the world-edit ledger in summary. The story data
is the record; this file is the read of it. Act I's own adaptation is [act1-on-bmv](act1-on-bmv.md).

Status: the first story slice (owner, 2026-11-06) is ledgered in §5: Act I and the first quests of two faction lines
and two locals; the other 706 quests wait (`wait`) until the owner has tried the slice. Sections 3 and 4 stay the
whole-province draft the slice was cut from.

## 1. Inventory (step 1)

From the story data (`quest`, `quest_line`, `quest_cast`, `quest_anchor_place`, `quest.start_when`) and the line
briefs. 717 quests in 16 lines, plus the planned detectives' line of decision 0025, which has no quests yet.

| line | quests | status | faction | home region | regions | settlements |
|---|---|---|---|---|---|---|
| Local quests | 561 | 527 skeleton, 34 live | - | all eight | 8 | 88 |
| The Eye and the Root (main) | 24 | live | Veiled Reed | hist-heartland | 6 | 7 |
| Proposed from the plotted province | 18 | 17 proposed, 1 cut | - | - | 6 | 6 |
| Reed-Sail | 14 | 10 live, 4 concept | Reed-Sail Compact | mercantile-coast | 3 | 3 |
| Night-Reed | 11 | live | Night-Reed Chapter | mercantile-coast | 3 | 3 |
| League of Open Water | 10 | live | League of Open Water | saxhleel-coast | 2 | 1 |
| Many-Root | 10 | live | Many-Root Conclave | hist-heartland | 5 | 5 |
| Marsh Charter | 10 | live | Marsh Charter | imperial-fringe | 1 | 3 |
| Nisswo | 10 | live | Nisswo of the Turning Path | mercantile-coast | 2 | 1 |
| Shadowscales | 10 | live | The Empty Cradle | saxhleel-coast | 3 | 1 |
| Sunken Archive | 10 | live | Sunken Archive | mercantile-coast | 3 | 1 |
| Daedric and oddity quests | 8 | live | - | - | 5 | 3 |
| Chainbreakers | 6 | live | Blackrose Chainbreakers | imperial-penal-south | 2 | 2 |
| Rootworm Waykeepers | 5 | live | Rootworm Waykeepers | hist-heartland | 1 | 0 |
| Thorn Ash-Reed | 5 | live | Thorn Ash-Reed Accord | dunmer-north | 1 | 1 |
| Umbriel Witness | 5 | live | Umbriel Witness Society | naga-kur-deeps | 2 | 0 |
| Detectives (0025) | 0 | planned | not yet a faction row | - | - | - |

Links the adaptation must keep:

- **Prerequisites.** Within each faction line the quests run in code order (01 to 10); the main quest's order is
  its stage graph. Seven quests carry an explicit start condition (`start_when`): mq03, mq04 and five locals (lf83,
  lh38, sx08 among them).
- **Shared cast.** Six designed people appear in two quests: the mq01/mq03 overseer, clutch-keeper and witness;
  the Stormhold Reed officer of mq03 and mq05; the Greenspring spring-keeper and tree-minder of lh38 and mr01.
- **Shared places.** 1208 anchor rows over 656 quests. The cities carry several lines at once: Blackrose (42
  anchors), Lilmoth (39, three lines), Gideon (36, four lines), Soulrest (35), Helstrom (35), Thorn (35), Stormhold
  (34). The allocation must give each line its own seat in a shared city, never the same person or room.
- **Exclusivities** (40-factions, each line's "senior exclusions"): senior Shadowscale state rank against senior
  Night-Reed and League roles; Night-Reed oligarch leadership against League office; Reed-Sail pirate leadership
  against Marsh Charter command, League law office and An-Xileel auxiliary; Sunken Archive's Synod, College and
  independent endings against each other; Nisswo state alignment against the Unbound Root; League hardline
  leadership against plural Many-Root; the main quest's tier 4 and 5 ends against each other across tracks.

## 2. The spirit of each line (step 2)

Per line: the promise, the core, the beats any adaptation must keep, and what is free. Per quest the same is in the
staging file [adaptation-spirit.jsonl](adaptation-spirit.jsonl) (one row per quest, 717 rows, plus the 17 line
rows), which moves into the `line_spirit` and `quest_adaptation` tables at step 5 and is then deleted.

**Detectives (0025).** Join a band of crime solvers in Black Marsh and climb from petty thefts and larcenies through murder mysteries to a grand murder finale involving highly important people of the province. Solving crimes the Shadowscales (assassins) and the Night-Reed Chapter (thieves) live by, using classic mystery structures made to fit the lore and the world.
Beats kept: Early cases are petty crimes: thefts and larcenies; Cases escalate in series of thefts, larcenies and murder mysteries as rank rises; Rivalry with the Shadowscales and the Night-Reed Chapter runs through the line; Recurring cast and a rival, with clues for the finale seeded along the way; Grand finale: a murder mystery that must involve highly important NPCs of Black Marsh. Free: Almost everything is open: the faction's name, founding, patrons, headquarters, ranks, number of cases per rank, the cast, which regions host cases, and the finale's victim and culprit. Fixed by the decision only: escalation by case, a joinable faction, rivalry with the two guilds, a grand finale with important NPCs, grounded in lore and in simple classic mystery structures.

Re-read against the [province vibe](../province-vibe.md) (2026-11-06): bureaucratic dressing the lore does not put there is gone from 57 rows; the motifs stay only where the vibe's §9 places them.

**The detectives (decision 0025).** Join a band of crime solvers in Black Marsh and climb from petty thefts and larcenies through murder mysteries to a grand murder finale involving highly important people of the province. Solving crimes the Shadowscales (assassins) and the Night-Reed Chapter (thieves) live by, using classic mystery structures made to fit the lore and the world.
Beats kept: Early cases are petty crimes: thefts and larcenies; Cases escalate in series of thefts, larcenies and murder mysteries as rank rises; Rivalry with the Shadowscales and the Night-Reed Chapter runs through the line; Recurring cast and a rival, with clues for the finale seeded along the way; Grand finale: a murder mystery that must involve highly important NPCs of Black Marsh. Free: Almost everything is open: the faction's name, founding, patrons, headquarters, ranks, number of cases per rank, the cast, which regions host cases, and the finale's victim and culprit. Fixed by the decision only: escalation by case, a joinable faction, rivalry with the two guilds, a grand finale with important NPCs, grounded in lore and in simple classic mystery structures.

**Chainbreakers.** You fight the Owing, a humane native debt-labour custom that drifted into inherited bondage, by proving it and burying its dead, and you pay for each win. Injustice with no villain: correct arithmetic, kind brokers and a ruin that is implicated rather than evil. Burial work and abolition work are the same work.
Beats kept: An Owing correct at every step: four months for a boat, eleven years running (BC01); The burnt Rose registers and estate ledgers as one class of document (BC02); Ussa-Rekh's thirty years of forgiveness and the brokerage that now indentures the dock crews (BC03); The procession of the Argonian dead carried home by name by Grave-Singer Ossu through contested crossings (BC05); What the Rose Becomes, ending in a unglamorous reform of assessment itself (BC06); Protected in every end: the archive wing, the confiscation-ledger record class and the Rose heirs as a community. Free: Which estate, crossing or dock hosts each case, minor workers and witnesses, ledger contents beyond the stated arithmetic, route of the procession.

**Daedric and oddity quests.** Eight strange, standalone encounters, one per Prince plus the unexplained, that feel like intrusions of Oblivion into a Hist-and-Sithis world and leave at least one thing unexplained. Wonder and unease: each Prince's bargain is technically intact and practically ruinous, and the choice is the player's, with Argonians reacting from their own cosmology rather than as followers of the Princes.
Beats kept: Each quest is found by rumour, shrine, book or strange encounter, never a quest board; Each Prince's bargain or curse is literally true and quietly ruinous (door wishes, mask wants, drowned-library price); The player makes a real choice about which side or hunt to finish (cure, quarantine, expose or let it run; which hunt); At least one element in each stays unexplained (wonder budget); Fixed unique artifact rewards, not scaled loot; Horror is found through hospitality, memory or rite rather than only through combat. Free: Which settlement or ruin hosts each quest, minor cast names, route and set dressing, which of the eight sit in Milestone 1 (DQ01-DQ04) versus wave 2, and which vanilla artifact mesh is re-skinned as the reward.

**League of Open Water.** You stand up for people the old tribal and Hist order has no place for, and every victory sharpens the question of who a free city is really for. Citizenship, property and plural identity, and the risk that openness turns into rule by wealth.
Beats kept: A resident is refused registration because no Hist claims them (LW01), and the lore remedy of the Hissmir trials sharpens rather than solves it; The murdered delegate who was exposing League financiers, with the hate-crime story that suits many groups (LW04); The traditional ordeal demanded in a mixed court (LW05); The canal that improves sanitation but cuts a sacred route and displaces households (LW08); The charter negotiation where prior cases limit credible clauses (LW09); The finale: plural civic movement, merchant oligarchy, municipal service, or collapse after exposing its own contradictions (LW10). Free: Which city hosts each case, minor people, street and building layouts, route names, market and warehouse dressing, the names of blocs and officials other than the named ones (Advocate Oshu-Kai).

**Local quests.** The province feels lived in: each place has its own problem that comes from its ground, water, history and people, not from a hero's errand. Local trouble is caused by real arrangements (tolls, rites, debts, records, stone and water) and the player settles it by reading them, with choices that favour some people over others.
Beats kept: Every quest starts from a causal local situation (geography, culture, politics, someone's motive) rather than a fetch list.; No quest is only collecting objects; recovery needs ownership, route, danger or interpretation to make it a problem.; The quest-giver is the payload: a person with a local occupation and one stated want.; Each region packet holds at least one oddity with no faction stakes, reward or explanation.; Cross-line texture comes through shared places and networks, never imported characters; delivery stays mostly low-tier (moved evidence, aftermath, retrieval).. Free: Which places host which quest, the names of minor people, routes, set dressing and the order of regional packets; skeleton premises may be reshaped as long as the shape of the problem survives.

**The Eye and the Root.** A debtor the law thinks dead is carried from a burnt work camp to the empty throne and the sanctuary door, and in the end holds the jewel, the city and the outcome, and must choose what to take. Can a people be protected by a bond they are not free to refuse, and when the fight over that bond is done, what do you do with what you are holding? The cult's grievance is real; its severance is indiscriminate.
Beats kept: MQ01: the Owing-gang processing, then the Unbound Root's attack led in person by Cuts-the-Old-Knot, who takes the courier's satchel and decides the player is not worth killing; a Hist turns its face and its egg clutch dies that night; The recurring sap-dreams begin the night of the attack (circle of trees, a door not yet built, a voice) and return at authored beats; MQ05: the arrival walk at Helstrom passes the Hall of the Scalded Throne, empty for centuries and still swept, so the endgame's third option stands in a room in Act I; MQ26: the hidden archive shows the Root of Accord was an ancient voluntary accord converted into a compulsory state instrument; MQ20 and MQ22: the Reed's own sap-dream files and the two incompatible reports, where a lie or truth has a visible victim and the player's handler falls; MQ18: the preacher at the sermon house is the Collector, Opens-the-Last-Door, who knows the player and says nothing; MQ29 to MQ31: the Lost City and its Last Warden, then the door confrontation where a seeded principal stands opposed, with a speech route and a hard fair duel always available, ending in the three families CUT, CLAIM or MEND. Free: Which settlement, cell or building hosts a beat; names of minor people; the exact routes, boats and roads; which of the regional leads (MQ07, 09, 10, 13, 14) are used as long as three suffice; set dressing; the exact room for the Scalded Throne; levels and enemy placements (nothing levelled against the player).

**Many-Root.** You are the one who goes into the danger and finds the truth, then stands in council and decides what it is worth. Every hearing pays off something won underwater, upriver or inside someone's work camp. Consent, stewardship and the limits of traditional authority: no Hist speaks for all Hist, and every remedy benefits some residents at the cost of others.
Beats kept: Discover in danger, decide in council: each quest's evidence is gathered in a dive, boat run, camp infiltration or den before the hearing.; MR01 root-cave dive finds the founders' hand-cut breach; the cure and whether the founders are named are the player's call.; MR02 night boat run with the eggs aboard, adoption terms answered at the far dock, the flood being engineered upstream.; MR04 night entry into the harvest camp with a blown-cover escape; the loudest ban campaigner is the biggest quiet buyer.; MR05 the den in the abandoned grove and the truth that the curer led the clutch out that night.; MR08 the council convened by clearing the channel, the toll and the falsified minutes, then run by one procedure (Ixo-Vaal or Kaska-Meen).; MR10 the loading-dock intercept of a genuine-paper cutting taking, then the finale choice of what the Conclave becomes.. Free: Which Hist settlement, grove, channel or dock hosts each quest; names of minor people; exact routes and hazard points; set dressing. The mid-line procedure choice and the end states must stay.

**Marsh Charter.** You take paid, practical defence work in a swamp frontier and discover that who is protected, and who is billed, is the real contract. Professional competence versus exploitation, public service, ecology, and whether accepting a charter means becoming foreign.
Beats kept: The first contract understates the danger and overcharges residents (FG01); Patrol vanished after refusing an unsafe order: negligence, not a monster (FG02); The juvenile Wamasu: kill, relocate, return eggs or expose trophy hunters (FG03); Charter War, with Ka-Deelith Ushu's hereditary-defence argument as the hardest to answer and least practical (FG08); The extermination order that targets a marsh community for its land and water, read aloud by Halvar the Damp before he signs (FG09); The four outcomes: public service, disciplined mercenary company, An-Xileel auxiliary, broken protection cartel (FG10). Free: Villages, forts and creature habitats used, minor officers, trophy and ledger details, exact routes, which old guild hall is reused.

**Night-Reed.** You rise from proving yourself on a small recovery to a province-famous heist on Lilmoth's Crown Ledger, and then decide who owns the night. Skill and loyalty among the dispossessed, professional restraint, criminal mutual aid, and the pull of blackmail power.
Beats kept: TG01: prove value by recovering stolen goods without harming the thief, observation and social leverage over burglary; TG02: the drowned lockbox whose contents expose all three clients; TG07: Silt is innocent, is never told she was suspected, and is cleared without alerting the real informer the den trusts too much; TG08 and TG09: the Pusbottom vault as route-planning lesson, and two of four optional preparations, none mandatory; TG10: the Tidal Palace heist with player-chosen methods and the ripper eels turned aside by eel-slime; TG11: the ledger proves patrons, merchants and officials jointly engineered housing seizures, and you expose, sell, redistribute or build an oligarchy. Free: Which docks, dens, houses and mooring spots stand in; names of minor people and fences; tool and route details; the Archon fence den location. Palace and vault names may change with the world's own seat of government.

**Nisswo.** You learn a living Argonian tradition of death, change and mediation by taking part, and help decide whether it stays dispersed or builds a school. Plural belief, grief, mercy and fraud, and the danger of turning change into dogma. You end as a respected interpreter, not an unquestioned prophet.
Beats kept: NI01: a funeral dispute teaches that Nisswo practice is interpretive, not a rigid death cult; NI02: a silent Nisswo takes you through a six-stop day and you err publicly at least twice; she never says what it was for; NI05: the Teeth of Sithis, a violent Sul-Xan splinter, and telling sincere theology from opportunism and state provocation; NI07: the admired priest who invents revelations and also made a real peace; NI08: a condemned murderer, victims and the state, resolved by process, not a pardon or execution binary; NI09 and NI10: dispersed order or teaching house, ending as plural network, formal school, itinerant tradition or dissolved order. Free: Which shrines, platforms, homes and settlements are used, names of minor people, routes. The pilgrimage circuit in the authoring nudge is optional, to keep or drop on fit.

**Proposed from the plotted province.** A holding bin of unauthored ideas raised by the 2026-09-04 quest and world co-design pass; no promise to the player until an author picks one up. Each proposal is a mystery or dispute grown out of a place in the plotted province (weirs, sluices, crossings, stations, stakes); the bin itself has no theme beyond that.
Beats kept: No beat is binding: none is authored, none has a brief or cast; Any author picking one up must re-run the collision test against the current index first; Any proposal may be dropped without loss. Free: Everything: the whole line is unauthored and any row may be dropped, reshaped or merged.

**Reed-Sail.** You run the water routes that keep Argonia moving, and decide whether the pilots' trade stays mutual aid or becomes a cartel. Mobility, labour, monopoly and sacred routes, and the line between mutual aid and cartel power.
Beats kept: Earning the pole on a working ferry with current, passengers and a staged obstruction, not a combat test (RS01); Ferry in the Dark: hunted passenger evaded by route and timing past static watcher boats (RS02); Pirates of Topal: a crew of ferry workers displaced by a monopoly (RS05); Storm at Archon: allocating limited rescue capacity, with Ahnjazzi's letter read aloud (RS07); Compact or Cartel: the internal election and which votes stay legitimate (RS09); Open Channels: worker compact, merchant cartel, pirate confederation or regulated public ferry (RS10). Free: Docks, routes and hubs used, minor pilots and passengers, boat and cargo detail, cove and ship placement; the pirate-branch quests are concept and wave 2.

**Rootworm Waykeepers.** You serve a small order that keeps the secret root-transit routes running, and decide what the order becomes. Sacred routes and access: mutual aid against monopoly, safety against secrecy. The worm is never seen, only its effects.
Beats kept: The worm is never on screen: presence reads through a tunnel mouth, churned water, wake, sound.; RW01 the refusal read entirely from behaviourless evidence.; RW03 a sacred route sold to smugglers to fund repairs the state refused.; RW04 reopen the route by cutting living roots or abandoning a dependent settlement.; RW05 four end states (open public service, restricted sacred order, state bureau, dispersed keepers), all keeping the Helstrom terminus in service.. Free: Station positions (the layout is a placeholder awaiting Hist-node placement), pen and cavern layouts, minor handlers, smuggler identities.

**Shadowscales.** You are drawn into the contest over reviving an order everyone wants and nobody made, and you decide what the Shadowscales become. Duty, consent and political assassination: whether birth, tradition, state power or consent can recreate a real order, or only a useful costume.
Beats kept: SS01: the last trained Shadowscale dies in the player's hands and the list of surviving initiates is the prize; SS02: a writ from an authority that does not exist, and each choice states the order's legal philosophy; SS03: the ruined hatchery and a survivor who never consented; SS04, SS05 and SS08: three bidders (Black-Tongues, Brotherhood, Veiled Reed) each offer legitimacy for control; SS07: two knives, one name, where authentic and innocent diverge and executing either claims the empty throne's authority; SS09: the Night Mother ritual with ambiguous evidence and a staged deception; SS10: the final choice among state service, Brotherhood, independent ethical order, or dissolution with records returned to victims. Free: Where the ruined facility, hatchery, safehouses, courthouse and meeting rooms sit, names of minor people, rooftop and canal routes, which city fabric is reused. The design says not to build a province-scale assassin network.

**Sunken Archive.** You work among scholars and custodians who all want a piece of what lies under the water, and you decide whose knowledge it is and what gets published. Ownership of knowledge, research ethics, translation, and the political force of archives, with the fight over whether such a body should become an institution at all.
Beats kept: SA01 recovering a waterproofed text from an inhabited ruin whose owners are present.; SA04 the College's offer of independence hiding a binding experiment and the exhumation of Umbriel's dead.; SA05 the Synod's funding against exclusive custody, with Hierem the Synod grandee in the archive's own records.; SA08 reading an escaped construct's wake at fixed breach points and choosing which containment point to hold.; SA09 Three Charters: Synod, College and independent futures are incompatible and earlier conduct changes support.; SA10 What We Publish: open archive, local custody, Imperial institution or suppression.. Free: Which ruins, camps and offices host each quest; names of minor scholars; the choice of creature or construct; routes. Staffing must stay non-robed and local.

**Thorn Ash-Reed.** You help Argonian and Dunmer neighbours contain border violence without erasing slavery, invasion or living claims. Competing memory and present economics: the hardest question (saltrice title) cuts across the ethnic line, not along it.
Beats kept: One memorial site, two commemorated atrocities (TA01); A body on the ferry: the victim moved Owing-held labourers as freight, ending in a manhunt via ferries and static intercepts (TA02); Saltrice fields with no titles, only occupation, worked under Owings by an ex-Archein family (TA03); Both militias keep lists of civilians to seize (TA04); Ash-Reed Accord: truth commission, security pact, closed separation or factional victory (TA05). Free: Neighbourhoods, field and dock locations, minor suspects and family names, militia room layouts.

**Umbriel Witness.** You handle an inherited catastrophe that nobody alive saw, and decide how the truth of Umbriel is kept, told or buried. History argued over at the distance of inherited memory: edited testimony, missing households, and a Society whose own founding account is compromised.
Beats kept: UW01 two witness texts, one edited after its author's death.; UW03 a household omitted from every casualty list.; UW04 the expedition to the Refuge at Deepmire, Old Nusa who is bored of Umbriel, and proof the Society's founding testimony came from a collaborator of Hierem's agents.; UW05 the choice of full archive, protected testimony, official narrative or sealed evidence, now including the Society itself.. Free: Archive, home and workshop locations; names of minor people; the route and shelters of the UW04 trek, provided it remains the line's one traversal spike.

## 3. The world's capacity (step 3)

From the census of all four plugins (`bmv_settlement`, `bmv_settlement_cell`, `bmv_placement`, `bmv_door`;
[census](../../../docs/research/bmv/census.md)). Black Marsh is three separate worldspaces joined by ships and
doors, and Valenwood a fourth entered only from Skyrim. What limits the story is not ground but people and rooms:
the three Black Marsh worlds have 26 reachable interiors (24 of them BM&V's own: 7 houses or halls, 13 caves, ruins and dungeons, 4 ships or dock rooms) behind 53 load doors, and 12 more doorless; Lilmoth has 6, Helstrom 4 (9 of its 12 doors share one house), Blackrose 2, and Murkmire, Thorn, Tear and Hereguard none; and the people are generic (guards, villagers, soldiers).

| settlement | marker | world | interiors | navmesh squares | people | other actors |
|---|---|---|---|---|---|---|
| blackrose | Black Rose | Black | 2 | 53 | 66 | 66 |
| altenmeirhall | Alten Merihall | Black | 0 | 27 | 21 | 17 |
| lilmoth | Lolmoth; Lilmoth Dock | Black | 4 | 34 | 20 | 65 |
| village | - | Black | 0 | 30 | 17 | 87 |
| hereguardplantation | Hereguard Plantation | Black | 0 | 19 | 11 | 35 |
| dock2 | Docks | Black | 1 | 11 | 8 | 20 |
| longmont | Longmont | Black | 1 | 32 | 7 | 88 |
| castle | - | Black | 1 | 21 | 6 | 21 |
| swamplandsrose | - | Black | 0 | 48 | 1 | 104 |
| grass | - | Black | 1 | 9 | 0 | 25 |
| murkmire | - | Black | 0 | 54 | 50 | 3 |
| murkwood | - | Black | 0 | 79 | 35 | 25 |
| dwarven | Dwarven Ruins | Black | 2 | 88 | 17 | 78 |
| banditcamp1 | - | Black | 1 | 44 | 12 | 25 |
| helstrom | - | Black | 2 | 58 | 11 | 7 |
| tribe | - | Black | 0 | 46 | 11 | 22 |
| dock5 | Helstrom | Black | 1 | 30 | 8 | 1 |
| temple | - | Black | 0 | 59 | 8 | 54 |
| murkwoodext | Bandit Dock | Black | 0 | 29 | 5 | 12 |
| temple2 | Road to Docks | Black | 1 | 19 | 4 | 9 |
| templepass | - | Black | 0 | 40 | 3 | 26 |
| outercave | - | Black | 0 | 23 | 1 | 17 |
| abondedtemple | - | Black | 1 | 35 | 0 | 60 |
| groot | - | Black | 0 | 63 | 0 | 17 |
| blackmarshnorth.thorn1 | Thorn | Thorn | 1 | 30 | 36 | 0 |
| blackmarshnorth.manor | Dres village | Thorn | 0 | 40 | 7 | 26 |
| blackmarshnorth.treehouse | - | Thorn | 0 | 31 | 6 | 10 |
| blackmarshnorth.marsh | - | Thorn | 1 | 81 | 4 | 44 |
| blackmarshnorth.ruin12 | - | Thorn | 1 | 88 | 2 | 101 |
| blackmarshnorth.1 | - | Thorn | 0 | 108 | 0 | 54 |
| blackmarshnorth.dessert | - | Thorn | 0 | 115 | 0 | 42 |
| blackmarshnorth.lizardmen | - | Thorn | 0 | 75 | 0 | 45 |
| blackmarshnorth.tear | Tear | Thorn | 0 | 56 | 0 | 14 |
| blackmarshnorth.test1 | - | Thorn | 0 | 58 | 0 | 35 |
| blackmarshnorth.waterfalls | - | Thorn | 1 | 71 | 0 | 55 |
| site.01goblincave | - | Thorn | 1 | 1 | 0 | 6 |
| site.01templecave | - | Thorn | 1 | 1 | 0 | 14 |
| valenwood.woodhearth | Woodhearth | Valenw | 3 | 10 | 25 | 31 |

Valenwood's other 46 settlements (Elden Root 73 people and 7 interiors, Haven 44, Falinesti) are left to BM&V's own
two quests. 12 interiors have no door (Gallows Rock, Darklight Tower, 01Cavebig, 01cell1 "Manor", 01Cell2 and
others): one new door makes each a room we can use.

The travel spine is BM&V's own: ship `01Ship` stops at Lilmoth (BlackMarsh 7,-1), the Docks (10,-2),
Helstrom's landing (BM2 -10,12), Bandit Dock (-10,7), Murkmire (-23,20), Thorn (BMN 5,13) and Tear (25,19), the
very coast line the lore runs from Lilmoth through Soulrest to Tear (settlement-register §2, Archon). Blackrose
reaches Murkwood by `01dock3to4`; the house `01CabinInt2` joins BlackMarsh and BlackMarsh2 by doors.

What the lines need of it: 156 line quests and 34 live local quests need about 60 distinct places and 40 rooms.
Rooms are the shortage, so the rules of the allocation are: an existing interior first; a doorless one given a
door next; an exterior scene on navmesh (a camp, a hut, a platform) after; a copied interior last and rarely.

## 4. One allocation across all lines (step 4)

**Where the designed cities land** (the nine waiting places and the census's open items, resolved together):

| designed place | BM&V home | why |
|---|---|---|
| Lilmoth, Blackrose, Helstrom, Hereguard, Thorn | as mapped | BM&V's own names |
| Alten Meerhleel, Longmont, Murkwood | as mapped | BM&V's own names |
| a Hist village for MQ04 | Village (BlackMarsh 22,-4), named from the lore's Murkmire villages | a Hist village on leech water east of Lilmoth; not the Hatching Pools, which the lore puts in central Shadowfen (not visited for now) |
| Soulrest | Docks (`dock2`) | a port on the ship line between Lilmoth and Tear; a known trade-off: the lore puts Soulrest on Topal Bay's south-west coast, far from Lilmoth |
| Gideon | Castle (BlackMarsh 2,6), with doorless "Manor" as the Governor's Mansion | the city around the old mansion, reduced |
| Stormhold | BMN's Marsh (-7,15), with the Underdark beneath | a northern town; the Conclave of Baal's books |
| Alten Corimont | BMN's Tear1, beside Tear | the north port, smuggling and transit |
| Tear, Tearmouth | Tear, and its ship landing (25,19) | canon Tear; Tearmouth is its landing |
| White Rose Prison | the unused old Black Rose (`gg`, far west) | inland in the west, a stone prison in ruin |
| Greenspring | `temple2` near Helstrom | a Hist village close to the capital |
| Rockgrove (Sul-Xan) | Temple Pass | a held ruin on the northern road |
| Dead-Water (Naga-Kur) | BM&V's "Murkmire" village (BM2 -22,20) | Murkmire stays the region's name; the village is the Naga-Kur's |
| Teeth of Sithis | Temple (BM2 7,-6) | a tended Sithis temple |
| Deepmire, the Refuge | Outercave (BM2 16,-3) | a place survivors climbed to |
| the Dres Rows | BMN's "Dres village" | the old Dres estate rows |
| Archon, Rockspring, Hissmir | not visited: named in talk only | no room for them without new towns; their quests move (below) |
| Falinesti | Valenwood's Capital and `falinesti` are one city | four squares apart; ours uses neither |

**Each line's seat and hubs** (`line_hub`): no two lines share a seat; a shared city gives each line its own
building and people.

| line | seat | hubs and field |
|---|---|---|
| Main (Eye and the Root) | Helstrom, the hall of the empty throne | Lilmoth, Hereguard, the village east of Lilmoth, Helstrom's landing, Blackrose; the Lost City not yet homed (the lore reviewer ruled BM&V's Dwemer pyramid ruins out as they stand) as the Lost City |
| Night-Reed | under Lilmoth (BMN's Lilmoth dungeon) | Blackrose market dock, Soulrest |
| Shadowscales | the Empty Cradle (Gallows Rock, a new door at BMN's treehouse) | Longmont's ruins (the hatchery), Helstrom |
| Nisswo | Teeth of Sithis | Dead-Water's necropolis, Soulrest's funerals |
| Many-Root | the conclave grove (`groot`) | Greenspring, the village east of Lilmoth, a tribe village |
| Sunken Archive | the abandoned temple's underground | Stormhold, the ruin at Grass |
| Umbriel Witness | Dead-Water | Deepmire, Pusbottom |
| Rootworm Waykeepers | Helstrom's station (`01Exit2`) | the house between the worlds (`01CabinInt2`), a tribe village |
| League of Open Water | Alten Meerhleel | Longmont |
| Marsh Charter | Gideon's mansion | Hereguard as the frontier fort, a tribe village |
| Reed-Sail | Soulrest's harbour | Bandit Dock (the Salt-Teeth), the Blackrose ship, Woodhearth in Valenwood |
| Chainbreakers | Blackrose | an ex-Archein estate east of Blackrose, the Rose's lower levels; later the Dres Rows and White Rose (empty of the living: its dead only) |
| Thorn Ash-Reed | Thorn | Tear |
| Daedric | none | the Underdark book portal as Apocrypha's edge; the rest by quest |
| Detectives (0025) | a house in Lilmoth, across the water from the Chapter (rivals by design) | Blackrose, Helstrom for the finale |

**Valenwood.** The lore gives one honest thread: Kothringi sailors carried Z'en to Valenwood and Argonian
refugees lived there (lore: topics/sithis-nisswo-shadowscales.md). Valenwood hosts the Reed-Sail's Southern Sea
run to Woodhearth, by one new ship door from Soulrest, and nothing else; no Thalmor thread (canon has none in 4E
Black Marsh, topics/foreign-powers.md).

**The shared world edits** (`world_edit`, 18 so far): ten place names, four doors (the Cradle, the Mansion, the
Rose's lower levels, the Woodhearth run), and four small peopled places (Tear, Alten Corimont, the conclave grove,
White Rose), every actor Argonian at a fixed band.

**Exclusions** (`line_exclusion`, 6): the senior exclusions of 40-factions, kept; no exclusive pair shares a seat.

**Local and proposed quests.** The 527 skeleton locals and the 17 proposals were premises written for 88 designed
settlements that BM&V does not have; Phase 5 commissions minor quests against BM&V's places and draws on them. The
34 live locals are weighed one by one against the hubs above at step 5.

Held: the per-quest verdicts and adapted premises (step 5) wait on the province vibe and the updated quest skills
(owner, 2026-11-06); the step 2 rows are re-read against the vibe then.

**Found while drafting (held for the world ruling).** BM&V's seats are dressed with vanilla actors that jar: Gallows
Rock holds Silver Hand, werewolf and Imperial-corpse actors; BMN's Lilmoth dungeon holds Volkihar skeletons; the
Temple and Murkmire hold Imperial MQ101 soldiers and an Arkay priestess, and Longmont, Blackrose and Murkwood more.
One world-wide clean-up edit decides them all at step 5, never line by line.
Also found: the Marsh Charter's patron Halvar the Damp is a Nord in 36-cast-roster.md (decision 0006); he is recast
(a Breton of Gideon, renamed) when the line's ledger rows land. FG03's wamasu becomes BM&V's crocodile (decision 0027 §3).

## 5. The first story slice (steps 5 to 8)

The owner ruled (2026-11-06) that BM&V stays as it is and that a slice is fitted first. The slice is chosen for
fit and variety, and so that nothing in it clashes. It holds 11 quests and 45 world edits:

- **Act I of the main quest** (MQ01, MQ03, MQ04, MQ05), with the new-game flow and the opening scene: the game opens
  in a debt-labour broker's barge at Lilmoth's Dock1 (the state's only presence is the An-Xileel courier, owner Q7),
  the gang is marched to its camp on a river island at the edge of Hereguard's paddies, where the gang families keep
  a Hist cutting from Nine Bends (gap-register QA1); the Reed's house in Lilmoth is unmarked and kept through a
  Lilmoth go-between; the ship takes the player to Helstrom's river landing.
- **Night-Reed** (TG01, TG02): a Khajiit fence at Soulrest and a thief's round on the boardwalk, the Chapter under
  Pusbottom, a dive into a sunk house.
- **Chainbreakers** (BC01 to BC03): a witnessed hearing at an ex-Archein estate just north of Blackrose (QA3), a
  fire in the Rose's lower levels at its gate outside the town (QA4), a broker's barge at Soulrest.
- **Two locals** in Act I's towns: a river-beast at Helstrom's landing ending in an arbitration (LQ25), and a youth
  gone into the basin (LQ30).

The Marsh Charter left the slice in round 2: Gideon's only room is an unfurnished, doorless shell with no navmesh,
BM&V's Gideon has no living people once its skeletons go, and its first quest's village lies in another worldspace.
It waits with the others: Shadowscales (Gallows Rock full of Silver Hand and werewolves), the Nisswo and Umbriel
lines (villages with no rooms and an Imperial garrison), Reed-Sail, the Sunken Archive, the Many-Root, Thorn
Ash-Reed (no enterable building), the League (no room) and the detectives (no quests yet). No two slice lines are
exclusive, and none shares a seat. Of the allocation's shared edits only two serve the slice (Soulrest's name, the
Rose's door pair); the rest leave the ledger until their lines are fitted.

**The clean-up** (one `we.clean.<place>` edit per host place, its every form in `world_edit_target`): every Nord,
Thalmor, vanilla Imperial official, skeleton, draugr-race walker, Soul Cairn shade, Lurker, werebear-race beast,
gargoyle, Dremora, Dwemer construct, fox-race person and named vanilla horse, cow or dog in the place and its rooms
is set initially disabled in its own override, with each place's extras (Soulrest's bears, glowing deer, spriggan
and slave; Blackrose's Breton merchants and Shadowscale recruit; the village's lurker sharks; the Naga at Lilmoth's
ship stop); every templated actor that stays gets a fixed level at the place's band. Per place (disabled / fixed), the place's own squares, the squares next to them and its rooms: blackmarshnorth.thorn1 3/0; blackrose 34/4; dock2 16/1; dock5 3/0; helstrom 2/2; hereguardplantation 28/1; lilmoth 50/10; village 11/0.
The checker fails a slice quest hosted where any templated or levelled placement is not in its clean-up, and one that
places people in a room with no navmesh without a navmesh edit.

| quest | line | band | where | the adapted premise, in short |
|---|---|---|---|---|
| BC01 Four Months for a Boat | Chainbreakers | 1 | blackrose | At the Chainbreakers' house in Blackrose, Never-Sold, born owing and long free, the one who remembers every bought-out name, sends you to an ex-Archein estate on the swamp road just north of the town. |
| BC02 Names Scratched Out | Chainbreakers | 2 | blackrose | Outside Blackrose, at the Rose's gate, the heirs' lower levels have caught fire. |
| BC03 The Broker's Mercy | Chainbreakers | 1 | dock2 | Ussa-Rekh lives on a mooring-barge at Soulrest's dock. |
| LQ25 The River Monster's Rent | Local quests | 2 | dock5 | At Helstrom's river landing a river-beast has begun to take rafts. |
| LQ30 The Gates of Helstrom | Local quests | 3 | helstrom | A young Argonian of Helstrom has walked out into the basin to prove something to the tribe. |
| TG01 A Dry Hand in a Wet City | Night-Reed | 1 | dock2,lilmoth | At Soulrest a Khajiit fence passes you the Chapter's word: its people want to see how you work, and they set the job. |
| TG02 The Drowned Lockbox | Night-Reed | 2 | lilmoth | In Pusbottom, Lilmoth's drowned quarter, a merchant's house has sunk into the canal with a lockbox of pledged things in it, a carved token, a charm and a deed-stake. |
| MQ01 No Name on the Work Roll | The Eye and the Root | 1 | lilmoth,hereguardplantation | A new game opens in the hold of a debt-labour broker's barge moored at Lilmoth's Dock1, where an Owing gang hired to Hereguard Plantation is processed: the broker's overseer reads the roll aloud with the months added for food, and character creation is the processing itself. |
| MQ03 A Dead Prisoner's Use | The Eye and the Root | 1 | hereguardplantation,lilmoth | At dawn the Veiled Reed's people take the survivors off the island, through the camp's aftermath, to an unmarked house in Lilmoth that a Lilmoth fish-trader keeps for them. |
| MQ04 The Tree That Turned Its Face | The Eye and the Root | 2 | village | East of Lilmoth, the Hist of a stilt village on the leech water has turned its face. |
| MQ05 Helstrom Behind the Thorns | The Eye and the Root | 1 | lilmoth,blackmarshnorth.thorn1,dock5,helstrom | The Veiled Reed takes the player on the coast ship from Lilmoth to Helstrom's river landing and walks them inland to the city, the basin's danger named at every turn. |

### Review rounds

- **Round 1** (five fresh reviewers: Act I, the three faction lines, cross-line, lore, vibe and society; the checker
  green): 11 blocking. Fixed as one batch: the camp's Hist (Hereguard has none) is the gang families' cutting from
  Nine Bends (QA1); Act I's levelled fox-race first mate, Hereguard's and Lilmoth's levelled and named vanilla beasts
  and the Naga at the ship stop and Gideon's door join the clean-up, and the checker now fails a host with levelled
  placements and no clean-up; the Rose's door is a pair (its exit led to another world); the Chapter's seat is
  peopled and named Pusbottom; Soulrest's one room is the fence's, the thief lives outdoors; the Chainbreakers'
  record-reading becomes a hearing, a fire and a broker's deck, each with a cost; the estate moves into Blackrose's
  world (QA3); White Rose keeps only its dead; Gallows Rock's door and every shared edit outside the slice leave the
  ledger. Minor: the Charter is a hired company with a Nibenese captain (QA2), FG02 gains the Naga at the ford and
  the patrol's own choice, LQ25 ends in an arbitration, TG02's counting house is a merchant's, MQ05's landing is a
  river landing, BM&V's greeting quest waits until MQ03 ends, MQ03 starts at the camp's aftermath. Ruled: the Lost
  City is not BM&V's Dwemer pyramid ruins as they stand (lore: no Dwemer in Black Marsh; a xanmeer is needed); its
  home is chosen when Act IV is fitted.
- **Round 2** (seven fresh reviewers: Act I, Night-Reed, Marsh Charter, Chainbreakers, cross-line, lore, vibe and
  society): 21 blocking, fixed as one batch. The Marsh Charter left the slice (above). Act I: the barge is a
  broker's, not the state's (Q7); the Reed's house is unmarked; the pier gets navmesh; the house's Riften door takes
  a BM&V base; the empty seat is plain root and reed in the hall where the state's seat is lodged and ignored. The
  clean-up is per form, initially disabled in each override (an enable parent cannot span rooms and exteriors), and
  fixes every templated actor's level (the census holds no levelled lists, so a template is treated as scaling); the
  checker now tests both and navmesh. Chainbreakers: the estate is north of the town and peopled with witnesses;
  the Rose's door pair is corrected (1F5AE4 re-pointed, 1EEB70 disabled), the cell renamed and navmeshed, the fire
  is a rescue of people; the broker moves to Soulrest, where the lore puts the crews; QA2 withdrawn, QA4 added.
  Night-Reed: a Khajiit fence, the thief's round placed, the Chapter peopled; TG02 hosted at Pusbottom with an air
  pocket, pledges not accounts. LQ25's beast waits behind its quest's enable parent; LQ30's guards keep off tribal
  ground. Explicit prerequisites now order each line.
- **Round 3** (six fresh reviewers): vibe, lore and Night-Reed raised nothing blocking; Act I, Chainbreakers and
  cross-line raised 9, fixed as one batch. The coast ship's own cell is a host and is cleaned (a Naga and two
  corpses); BM&V's uniformed 'New Order', 'Tax Heel' and 'Rebelion' soldiers, in no lore file, leave every slice
  place and the squares next to it (LQ30's gate soldier stays); the clean-up reaches neighbouring squares. MQ01: the
  camp is placed at a named square (-1,0) with its creatures cleared, the gang starts in the hold, the roll burns in
  the attack and the cell's harvest is what kills the clutch; Valenwood's two start-game quests wait until the player
  enters Valenwood. BC01's estate and BC02's gate have named squares; the Black Rose Guard are the Rose's own watch at
  the gate; the lower levels' 67 refs are a build-time check. Minor fixes taken: the Chapter tests as a peer, two of
  the fence's three doors shut, Pusbottom named, the pledges are things, BC03 is a refusal and a side taken, LQ30 is
  a rite no one trails and follows LQ25, MQ04's tending-ground and its officer from outside.

