# Owner rulings on factions, joining, quest design and writing style: full findings

Compiled 2026-11-16 (read-only; clone deleted afterwards). Newest last within each topic. "OR" = docs/owner-rulings.md;
"nw-05c" = docs/phases/new-worldspace-plan/nw-05c-factions-overhaul.md (the owner's explorer notes of 2026-11-16, kept
word for word; main file, line numbers below); "ESA" = jtattersall09403/elder-souls-argonia (private clone, depth 1,
HEAD b581910f); "old brief" = docs/owner-brief.md as of commit d269dbf5^ (the pre-pivot file, 329 lines);
"ESA words" = ESA lanes/2.7d/owner-words/README.md, which holds the owner's typed chat messages with timestamps.

## 0. Where the rulings live, and what could not be reached

Live docs that already cover the topic: story/design/owner-bar.md (216 lines; already updated by commit 1d914f90 on
2026-11-16 to hold the main-plot and some faction rulings), docs/owner-rulings.md (to line ~700), nw-05c (the
owner's two long faction notes, verbatim), docs/decisions/0025. ONE doc to edit: story/design/owner-bar.md (add the
rows in section B below). nw-05c must stay as written (owner wording is preserved; OR 2026-11-10).

Findings about the sources:
- GitHub issues, this repo: the owner's own comments (user jtattersall09403, not github-actions[bot]) are 89 short
  replies, #1 to #71. Only #50 (2026-11-06 18:43 and 18:43), #53, #71 and #60 touch quests; none mention heist,
  Brotherhood, thieves, pirates, mages, necromancers or slavery. Issue bodies are agent-written.
- GitHub issues, ESA: 4 issues. #1 to #3 are agent progress feeds (all comments post under the owner login with no
  owner text; 100 comments checked, 0 owner replies). #4 is an outsider's licence note.
- NOT REACHABLE: the owner's story-explorer batches (77 notes of 2026-11-16, 23 of 2026-11-13) live in the
  ArtifactData store (collections batches/drafts/draftReplies), which I cannot read. Only what agents copied into
  OR, owner-bar and nw-05c is visible. The other 75 notes of 2026-11-16 need a read through the ArtifactData tool.
- NOT FOUND ANYWHERE in either repo as the owner's own words: his earlier chat about "a thieves guild style one
  building up to a big heist like in Oblivion" and "learning from what everyone loved about the Dark Brotherhood".
  He said these in chat. What the repos do hold on them is agent text from the old repo's owner-supplied quest
  master plan and owner reviews (ESA decision 0009: "The owner supplied a quest/narrative master plan"; ESA 0026
  section 7 table, and ESA docs/quests/00-overview.md lines 222-231): "Oblivion - The Ultimate Heist" -> TG10 The
  Palace Below the Tide, with TG08-TG09 as its escalation; "Whodunit?" -> LQ31 The Bonding Feast; "Dark
  Brotherhood's bonus-condition contracts" -> SS06 The Honest Target; "Skyrim - Thieves Guild betrayal staging" ->
  TG07. Rule there: "when a new packet wants 'a quest like X from game Y', it must hit this table first".
  These are agent plan text approved by the owner, not his words.
- Nothing found by the owner on: mages-guild-style factions (beyond nw-05c), a pirate line before nw-05c (ESA 0042
  only cut the river-pirate boat system), necromancers before nw-05c, slavery before the Chainbreakers/Owing items
  below.
- Vanilla Skyrim guilds: OR 2026-11-05 (line 12) stops the main quest, dragon attacks, civil war, "Thieves Guild
  couriers" and radiant quests; it says nothing stopping the Companions, College, Dark Brotherhood or Thieves
  Guild lines themselves. 2026-11-16 supersedes with a wholly new set.

## A. Rulings by topic (owner's words quoted; newest last)

### A1. The set of factions and how many
- ESA words Q65, 2026-10-16 17:24:10 (chat 6757acae/e1784e3b): "A, as it sounds like factions need to be cleared up by
  the end of 2.4. 80 factions also sounds like a huge number! How many do Morrowind and Skyrim has? we should have
  approximately the same". (Outcome in ESA: registry cut to 32, ESA docs/quests/40-factions.md section 27a.)
- ESA words Q18, 2026-10-17 10:35:45: "villager with no guild - default to no faction. just like morrowind, not
  everyone has a faction".
- ESA words Q70, 2026-10-17 10:35:45: "I am wary of scope creep and creating more people than we need (and making some
  places too big, like Helstrom ... I don't think it should be bigger/more populated than the biggst city from
  Skyrim/Morrowind".
- OR 2026-10-28 (old brief line 157): "The old repo's main quest, factions and quest system are the foundation,
  improved not replaced". SUPERSEDED in part by OR 2026-11-12 ("keep the overall factions and spirit ... creative
  license to rewrite") and fully by 2026-11-16.
- OR 2026-10-27 / decision 0025 (this repo docs/decisions/0025-a-detectives-faction.md:3-5): "let's have a detectives
  faction! As rivals to those two. Solving murders and thefts, with quests escalating up from petty crimes to some big
  grand murder mystery finale. It will need to be grounded in lore and our lore extrapolation". Also 0025 line 20-23:
  "Must also be grounded in popular mystery storyline tropes ... Let's take some simple classic structures that are
  known to 'work' for detective/mystery storylines. We don't need to create completely original stories here."
- nw-05c lines 12-27, 2026-11-16: "We are going to overhaul our factions completely. We will have chainbreakers, the
  detectives one, thieves guild type one (don't call it Night Reed though as we're already using "reed" in the [main quest's order,
  now the Toh-Reel-Ka], and "night" sounds more like the dark brotherhood), dark brotherhood type one (Shadowscales, secretly making
  their resurgence after the canon death of the "last" one recently - that was actually just cover), the pirate one,
  an argonian magic/alchemy one with a name in Argonian/jel, and one each for a Dunmer run one based in the north near
  Morrowind (Thorn?) and an Imperial run one out of Gideon (plus the main quest two, [the Toh-Reel-Ka] and the Unbound,
  which are kind of separate, and a non playable one ...). It's fun if they're in conflict with each other in various
  combinations." "How many quests does each faction line have in morrowind/skyrim? our factions should have similar."
  "I would like all the major cities covered across the set of factions (in terms of where they are based/have
  branches)."
  EFFECT: every older line is cut; the thieves are renamed (now the Eelskins) and the detectives are the Lampbearers.

### A2. Thieves (guild-style, building to a heist)
- No verbatim "build up to a big heist like Oblivion" in either repo (see section 0). Nearest owner words:
  nw-05c, 2026-11-16: "The thieves one: sneak, pickpocket, lockpicking, speech, enchanting (for enchanting items
  with stealth enhancing effects). All deployed differently from the lamps for opposite reasons. Rivals of lamps and
  Shadowscales."
  "Join: first time you steal something, next time you rest somewhere, partway through your rest is interrupted and
  you wake up to find someone from the thieves guild in the room with you, who opens forced dialogue (non excitable),
  saying your actions have been noted and there is a place for you in a new family if you want it - give you a note
  with directions and a key or a password or something). Then fade to black and then back in and they've
  disappeared. New quest starts to follow the note, takes you to a secret location where you can then properly join
  and start the faction quests. Maybe start at an outpost, prove your loyalty before graduating to headquarters."
  "Choice point: either side with Shadowscales to kill off the lamps in order to enable your big heist, or make a
  bargain with the lamps: you'll take down the Shadowscales with them in exchange for them looking the other way
  while you do your heist. End game reward ideas: powerful permanent chamaeleon enchantment ring". Also "nobody knows
  where they are based" (rumours only).
- Agent-record of earlier owner-approved plan (ESA 40-factions section 32; ESA 0026 section 7): the line's
  escalation TG08 preliminary heist -> TG09 preparations (choose two of four) -> TG10 the grand heist with a
  multi-route approach and a free security hazard (ripper eels, eel-slime counter, from lore extrapolation
  quest-plan-deltas.md D-note). Heist as the line's climax is thus consistent across both eras.

### A3. Assassins (Dark Brotherhood-style, Shadowscales)
- No verbatim "learn from what everyone loved about the DB" in the repos (see section 0). nw-05c 2026-11-16:
  "Shadowscales: sneak, lockpicking, archery, one handed, light armour, illusion (invisibility, muffle, chamaeleon,
  diversion, night eye and similar). Rivals of thieves and lamps. Join: how does this work in Skyrim/oblivion? I
  remember one of them you get visited after you murder someone, but that's too similar to our thieves one above.
  Some other fun way to join? Choice point: side with the thieves to take down the lamps and rule as a joint criminal
  underworld, or side with the lamps to end thieving but gain protection for the assassins from the law."
  Also "Shadowscales, secretly making their resurgence after the canon death of the 'last' one recently - that was
  actually just cover", and an example quest shape: "learning a recipe for a poison, gathering the ingredients,
  making it, then sneaking into a house while they're out and poisoning someone's food, for a shadowscale plot".
  The open question "how does this work in Skyrim/Oblivion" is for the agent to research (UESP: Oblivion's DB is
  entered by a murder, Skyrim's by the Dawnstar/orphanage-style recruit; the owner wants neither the thieves' route).
- Agent record: ESA 0026 section 7 maps the DB's "bonus-condition contracts" to SS06 (discovery and restraint
  rewarded); ESA research tes-quest-and-faction-rewards.md names Oblivion's DB "drip of unique enchanted items
  roughly one per quest" as a proven reward genre.

### A4. Detectives (the Lamp faction)
- OR 2026-10-27 / 0025 as in A1 (rival to assassins and thieves; escalating cases; murder-mystery finale; classic
  mystery structures; important NPCs in the finale).
- nw-05c lines 107-115, 2026-11-16: "Joining: simple, just go sign up at their headquarters, you're useful to them
  because you don't have a cultural 'side' or family/factional ties." Skills: "Speech, sneak + lockpicking (for
  sneakily gathering evidence), illusion (calm, charm, possibly fury and mayhem)". Finale choice: speech check
  "(level 90+, say)" to make the Shadowscales leader confess; if that fails, "make a deal with the thieves to get the
  proof and put away the Shadowscales once and for all (at the expense of you giving protections to the thieves); or
  side with the Shadowscales, steal the evidence, and frame the thieves' leader ... in exchange for you providing
  protection for the Shadowscales from the law".
- nw-05c lines 210-232 ("detectives' quests"): "establish this structure early, then gradually increasingly break
  it in later quests: you are identifying who, means, motive, opportunity. Gather evidence and present case to
  handler/choose from one of a few suspects, but you have to have found the evidence first for the dialogue options
  to be available." Red herrings: "each one except the actual culprit has some alibi or conflicting evidence". Judging:
  "take the person before the magistrate ... If right, you complete the quest and get rewarded and progress through
  faction. If wrong, pay some kind of penality, and have to do another mission at the level you're at. If you fail 3
  at the same level you're kicked out of the faction." "Don't have *every* lamp mission in this format ... use it for
  first act and most of second ... then start to break the structure later e.g. ... you confront the murderer and
  either pass a hard speech check ... or they attack you if you fail; or they find and attack you partway through the
  investigation".

### A5. Pirates
- ESA 0042 section 2 (owner rulings on the ambitions batch, ESA decisions/0042): river-pirate boat-encounter system
  "CUT as a system - pirates survive as shore ambushes". ESA 0026 section 6: "rails-following craft is a minefield"
  (no boat chasing boats). Boat travel itself is now a mod question (Sailable Ship mod; #11 2026-10-29).
- nw-05c lines 148-157: "Pirates: pure combat + scrolls for water breathing, water walking, swift swim, maybe some
  of the illusion ones like mayhem and frenzy ... light armour, heavy armour. If rivals of the imperials, base out
  of the island in topal bay or similar? But maybe also with an inland/river pirate branch? Check the region lore."
  Join: recruited in a coastal bar, a brawl with an Imperial ("an unarmed fight ... at some point they yield and you
  accept"). "Would it be possible to have fights at sea? Needs some thinking. Could do some smuggling too. Ends with
  climax against imperial merchant headquarters and Gideon guards, if successful you take over Gideon and make it a
  pirate stronghold." (Supersedes ESA 0042's cut only if fights at sea prove deliverable; the owner asks, does not
  rule.)

### A6. Imperial merchants (Gideon) and Dunmer necromancers (Thorn)
- nw-05c lines 159-173 and 135-147, 2026-11-16: Imperial: "rivals of the pirates ... Joining: simple, sign up at
  headquarters. Jobs: you're buying & selling things (and perhaps using speech or bribery on customs officials),
  smithing goods to be traded ... protecting shipping and taking down smugglers. Speech, heavy armour, smithing,
  block, one and two handed. Climax is invading the pirate island in Topal Bay ... stronghold for the player and a
  Ravens Rock style settlement building post-game."
  Necromancers: "fronted by a supposedly reputable dunmer in Thorn. If you talk to them when you have conjuration
  above a certain level (not high, maybe 20) then they ask you to demonstrate your skills ... send you somewhere to
  some secret-ish place". Skills "All of conjuration plus necromantic healing from restoration ... enchanting,
  destruction". "Penultimate climax defeating the Argonian magic faction, then Arc ends with in-faction breakdown and
  infighting and you killing the old leader and taking over."

### A7. Argonian magic and alchemy order (and necromancy/slavery taboo)
- nw-05c lines 119-134: "Nature magic, deep connection with the marsh and the hist, specialists in potions,
  poisons, making, healing ... some role in funereal rituals and paying respect to the dead. Rivals of the dunmer
  necromancers. Long seated enmity there. History of enslavement, deep cultural taboos against disturbing and
  enslaving the dead (enslaving the dead evokes argonians own history of enslavement at the hands of the dunmer),
  generational trauma". Join: a tree minder gives "a small quest to gather some specific ingredients and make a
  healing potion". "Early quests around healing people but also creating poisons or similar to help end someone's
  suffering painlessly when they can't be saved." "Arc ends with taking on and destroying the dunmer faction and
  eradication of threat of slavery." Name must be Jel.
- ESA owner-questions.md Q5 (2026-08-24, accepted): "generational trauma from 4E 48 plays out in backstories and
  politics at the emotional distance our world in 2026 has from the First World War". ESA docs/quests/60 section 45c.

### A8. Chainbreakers, the Owing, slavery
- OR 2026-11-10 (law): "A native Argonian place has no jail ... The Owing is the playable sentence ... a person who
  resists arrest is fought to the death by the guards."
- ESA owner-questions.md Round 2 (2026-08-24, accepted): Q7 "informal bondage as the Chainbreakers' target"; ESA 0151
  (owner, 2.10 plan review): "The Owing is the sentence, paid in coin or time, or resisted."
- ESA decision 0028 (owner 2026-08-26) on the Reed: "the Reed's record-rewriting is the mechanism ... never an end in
  itself".
- OR 2026-11-13, nw-05 (see owner-bar line 28-31): "The chainbreakers main thing being about buying people out sounds
  kind of boring by itself ... that's basically just chores. 'Chainbreakers' sounds like an exciting faction ...
  do you have to pickpocket somebody to get a key to break into their house to change something on a record about
  owed months, for example. Use your imagination, make them fun. Same goes for all the factions. They should be fun
  and intriguing and exciting and have drama and tension, all of their own".
- nw-05c lines 175-208, 2026-11-16 (newest, binding): "Chainbreakers: allies of the pirates. Semi-outlawed as in
  theory the Owing is a cornerstone of the legitimate legal system. ... mainly operate inland and in east/north,
  against the Owing wherever it serves as indentured/pseudo slavery, and especially against a non-joinable faction
  of Dunmer merchants who specialose in profiting from it. Skills: all the combat skills, plus sneak and lockpicking
  and speech (but purely for intimidation scenarios ...)". Joining: many visibly working NPCs "each has their own
  unique story" (some legitimate debt, many abused); a story leads to "a specific farm/plantation (with quest marker)";
  get "the work roll" by sneaking, intimidating or fighting; give it to the person; they "reveal they're part of the
  Chainbreakers, invite you to join ... screen fade to black and back and they've disappeared". Quests: "outlaw like/
  robin hood esque prison break type quests, mainly combat based but usually with an intimidated speech option first
  ... and a stealth option". "Should also be a quest defending a safe house ... like a tower defense where you have an
  hour to prep some traps and things in advance (... Defensive rune scrolls perhaps?) ... if the escaped person
  you're protecting dies you fail and are expelled from the faction". Freed people "(a) then appear at permanent posts
  in various places across the province and provide you with services - e.g. cheap trainers, merchants who will give
  you good prices. And also they should pop up in other major questlines and be helpful ... but never be essential".
  Dunmer merchants: "Not joinable and no quests but flesh them out a bit".

### A9. Joining, discovery, rivalry and exclusion (all factions)
- OR 2026-11-12 walk 6 / OR: main quest faction is entered by induction by a named person (see owner-bar line 117-120).
- nw-05c lines 91-98, 2026-11-16: "All factions: must be able to find out about them through rumours and chatting to
  people around the province and find out where they're based (except for Shadowscales and thieves, nobody knows where
  they are based, but you can hear rumours about them generally and speculation about how they recruit people ...).
  When you first have dialogue where you hear about a faction, it should start a minor quest in your journal about
  finding that faction, and give quest markers for the less secretive ones. For the secretive ones, your journal could
  be updated when you hear new rumours ... the quest is complete when you find and join the faction, and failed if
  you get to the point in a rival's faction that prevents you from joining that one."
- nw-05c lines 100-103: "Three way rivalry and arcs between lamps, thieves and Shadowscales. Whichever faction you
  join, at some point you're locked out from joining the others, and late in the arc you have to choose one of the two
  rivals to ally your faction with in order to best the third." Also rivalry pairs: Argonian magic vs Dunmer
  necromancers; pirates (with Chainbreakers) vs Imperials; Chainbreakers vs the Owing-profiting Dunmer merchants.
- ESA plan (agent text the owner supplied/approved; ESA 40-factions sections 27-30): 3-5 stationary desks with distinct
  ethics per line, a mid-line desk choice, senior-membership incompatibilities "telegraphed before the commitment",
  tier protection, a main-quest independent route always. Dated 2026-08-23 to 08-26.

### A10. Ranks, rewards, progression
- ESA 0028 (owner decisions 2026-08-26, "all three as recommended"): reward ladders of five tiers per side;
  "Stack low, lock high": tiers 1-3 freely stackable, tiers 4-5 mutually exclusive and "telegraphed before
  commitment"; "no companions anywhere"; the Reed's headline reward is "an informant network that marks things on the
  map"; one stronghold, phased, re-skinned by allegiance. Reward genres researched there (signature gear at a named
  rank; a drip of unique enchanted items; fence/trainer access; capability unlock). Only partly superseded
  (main-quest sides are now Reed/Unbound only; map markers now exist: see A12).
- OR 2026-11-13, nw-05: "A faction's ranks bring rewards in proportion, and things unlocked, as Skyrim's guilds do."
- OR 2026-11-13: "'Standing' by itself doesn't sound like very much ... 'standing' is only as useful as what it
  unlocks/enables"; rewards "items and gold are the simplest and stand first; also 'crafting recipes, potions
  recipes, perhaps some other fun stuff from Morrowind like unlocking spellmaking in an Argonian lore friendly way'".
- nw-05c lines 72-79 (2026-11-16): "Core skills determine types of quest, what you learn while gaining promotion
  through the faction ... some quests start with you learning a specific spell/recipe, then the quest is tailored such
  that some part of it involves you using that spell/recipe/thing specifically ... multistage quests where you're doing
  a series of things, each of which enables or links to the next". Spell sets by faction listed lines 56-70.
  Last paragraph: "quests should escalate in difficulty over the course of their story (I.e. objective difficulty -
  skill levels required, danger bands of areas visited, etc. I don't mean they should level to the player ...).
  Rewards should get progressively better in proportion (and be hand authored, not random)".
- nw-05c line 128 / thieves: end-game reward idea "powerful permanent chamaeleon enchantment ring".

### A11. Quest shape in general
- OR 2026-10-28 (old brief 157): "Nearly every quest has 'action' (use of the player's skills), varied and creatively
  combined, led by faction profile; no talk-to-X-then-Y quests."
- OR 2026-11-06 #50 (2026-11-06 18:43): "I specified that every quest must make use of at least one of these skills.
  ... they need to write quests that explicitly use at least one of these skills (and name which ones) for every
  quest ... the whole main quest should be possible for different builds so each quest should have options for
  completing it in different ways using different named skills." And (18:43): "Faction quests can be more tied to
  specific builds, and in fact should be for consistency and immersion". #53: "Swimming and climbing are not
  skills."
- OR 2026-11-06 (quest review loop): lean on action, danger and discovery, not law and custom; branching budget; earlier
  choices must not change later stages.
- OR 2026-11-12 (walk 6): "nothing more complicated than Morrowind-level scripting ... much less world-editing";
  markers wanted; "Anyone in our game can die" (thread-of-prophecy message only for main/faction-essential people);
  "no talk" opening; replaces the old brief's "no quest markers on maps" (old brief 2026-10-27/28, SUPERSEDED).
- OR 2026-11-12: "Lean towards activity and action ... over processes and procedures and records" and 2026-11-13
  "Doesn't have to be absolutely *no* records or ledgers ... at most a very small amount across the board".
- OR 2026-11-13: choices must have play effects; riddles for side quests; ranks with rewards; "Talker" is not a build;
  details in owner-bar.
- OR 2026-11-16 (in OR line 667+ and owner-bar 71-83, 130-148): a choice of ways is real only when no way is free; early
  skill ways must work for a level-one character; sneak ways truly possible; quest places match the danger band of
  their point in the line; stories written from the source place; nobody walks ahead to be followed; the line's plot is
  a short page of numbered paragraphs, with Acts, before any quest records.
- ESA 0027 (owner directive 2026-08-26 in ESA): "the same quests per km², places per km² and quests per city as
  Morrowind" (about 450-550 finite quests; Vivec 90-100, villages 3-8). ESA 0026 (owner, 2026-08-26): main quest cut
  to Morrowind's length (23 core), three endings "named by what the player takes", stakes "visceral and legible
  (owner: 'I don't get or feel consent architecture')", "No boats chasing boats". ESA 0153 (owner, 2.11 plan review):
  quests ship as data over one world record; "logic apart from text". ESA 0152 etc. are engine rulings, not quest shape.
- Minimum for each faction's size: nw-05c "How many quests does each faction line have in morrowind/skyrim? our
  factions should have similar" (ESA 00-overview section 2: Morrowind 21-39 per guild/house; Oblivion 5 lines;
  Skyrim 4 guilds; the Morrowind audit lists 31 Fighters, 35 Mages, 21 Morag Tong, 31 Thieves, 30 Temple, 39 Redoran,
  30 Hlaalu, 29 Telvanni).

### A12. Quest markers, discovery and the journal
- Old brief 2026-10-27/28: "no quest markers on maps". SUPERSEDED by OR 2026-11-12 (walk 6): markers on the map and in
  game "like in skyrim". OR 2026-11-13: side-quest riddles carry no marker until found. nw-05c 2026-11-16: markers for
  less secretive factions; journal rumour updates for secretive ones.
- Old brief 2026-10-31: the journal is a Morrowind-style paper book (UI era; mostly moot after the pivot).

### A13. Tone, lore and grounding that bind factions
- ESA owner decisions Q1-Q9 (2026-08-24, accepted): An-Xileel as successor state; Hist speak through a great Root Talk
  at Helstrom; Blackrose a reoccupied ruin; Lilmoth rebuilt not restored; tone "melancholy and dignified province-wide,
  horror kept local" plus the WWI-distance trauma rule; Q9 Gideon's Hist is a disputed planted cutting. The first-repo
  extrapolation file is now at story/lore/extrapolation/owner-questions.md.
- OR 2026-11-01 / decision 0032 golden rule; OR 2026-11-09: no invented-from-nothing; 0006 no Nordic element.
- ESA 60-writing section 45d (binding): "assume no Elder Scrolls lore beyond having maybe played Morrowind".

## B. Not yet in owner-bar.md (checked against its current 216 lines)

Held already: escalation ladder and hand-authored rewards (line 77-79); teach-then-use spell/recipe quests (82-83);
detective who/means/motive/opportunity (130-132); rumours start a small find-the-faction quest; rival-lockout (146-149);
the pointer to nw-05c. NOT held, as a list of rows to add:

1. The 2026-11-16 faction roster as rulings, with its conflicts: detectives, a thieves' guild (now the Eelskins),
   Shadowscales (resurgent, the "last one" a cover), pirates, an Argonian magic and alchemy order with a Jel name,
   Dunmer necromancers fronted by a reputable trading house at Thorn, Imperial merchants at Gideon, Chainbreakers, a
   non-joinable Dunmer house of Owing-profiteers, plus the Toh-Reel-Ka and the Unbound. All other old lines are out.
2. Size: each line "similar" in quest count to Morrowind's and Skyrim's guild lines (31-39 in Morrowind guilds, about
   15-25 in Skyrim); every major city is home or branch to some faction (nw-05c 14-16, 40-41).
3. Each faction's plot is a page in the main plot's form with Acts; the old stories and database rows are deleted and
   the plots written fresh (Opus 5.5 medium, no reader loops) (OR 2026-11-16; in OR but not in owner-bar).
4. Three-way arc (lamps, thieves, Shadowscales): locked out of the others at some point; late in the arc choose which
   of the two rivals to ally with against the third (nw-05c 100-103). The owner-bar has only "a late point in a
   rival's line shuts its door".
5. The per-faction choice points and endings (lamps' confession/deal/frame; thieves' side-with-Shadowscales vs
   bargain-with-lamps; Shadowscales side-with-thieves vs side-with-lamps; Argonian order destroys the necromancers and
   ends the slavery threat; necromancers' infighting and a takeover; pirates take Gideon; Imperials take the pirate
   island and build a stronghold; Chainbreakers' finale open) (nw-05c).
6. How each is joined, in his words: thieves (woken while resting, fade, note and key), Shadowscales (a new way, not
   after a murder), pirates (bar, brawl, yield), necromancers (conjuration demonstration), Argonian order (tree-minder
   potion quest), Chainbreakers (a unique-story worker, work roll, fade), lamps and Imperials (sign up). A faction's
   join gets a "fade to black and the contact has disappeared" beat where he asked.
7. Discovery of every faction by rumour; secret ones (Shadowscales, thieves) only by rumour about their recruiting;
   the minor "find the faction" quest ends on joining and fails if a rival's line shuts the door (partly held).
8. Detective quest structure details: evidence gates dialogue options, red herrings with alibis, magistrate scene,
   wrong answer = penalty and another mission at that level, three fails at a level = expelled, structure broken
   later (hard speech confrontation, culprit attacks you) (nw-05c 210-232).
9. Chainbreakers specifics: safe-house defence with prep time and rune scrolls, a rescued person who dies fails the
   quest and expels, freed people reappear at permanent posts giving cheap training and good prices and help other
   lines but never essential, prison-break shape with an intimidation option first and a stealth option.
10. Combat/skill and magic sets per faction (nw-05c 56-70): the Morrowind and Magic Expanded spells to be reviewed and
    recorded in the explorer.
11. Necromancy and slavery as an Argonian taboo (nw-05c 128-131); that enslaving the dead mirrors Argonian history;
    the Dunmer slaver-merchants as non-joinable backdrop.
12. Old-repo owner rulings with no row: Q65 "approximately the same" faction count as Morrowind/Skyrim (now partly
    moot); Q18 "villager with no guild - default to no faction"; ESA 0028 "stack low, lock high" (tiers 1-3
    stackable, 4-5 exclusive and telegraphed), "no companions anywhere", "informant network that marks things on the
    map"; ESA 0026 stakes made visceral and legible in the first two hours with zero assumed lore (binding rule: "assume
    no Elder Scrolls lore beyond having maybe played Morrowind"); ESA 0027 Morrowind quest density (450-550 quests,
    quests concentrated at settlements, wilderness carries places); ESA fan-favourite premises table (Ultimate Heist,
    Whodunit?, DB bonus conditions, Skyrim TG betrayal staging) as the owner-approved target; ESA 0042 on pirates as
    shore ambushes; ESA tone rule: melancholy and dignified, horror local; the WWI-distance trauma rule.
    (Several of these are old-world specific and may be superseded: confirm before adding.)

## C. Writing-style rules in ESA not in style-core.md or style-guide.md (here)

Checked by grep of story/design/text/style-core.md, style-guide.md, culture-registers.md, .claude/skills/dialogue-write/
(SKILL.md, bans.yaml, voices.md) and old-decisions 0143/0145. Already present (so NOT gaps): personification, rather
than, nobody/somebody, claim/count/tally, and-for-but, stranded preposition, contractions, "goes to the" (guide line),
"everyone knows" closer, fronted-phrase comma (core line 21), anyone may explain (0143), disposition and essential
topics (0145), landmark directions, newcomer-phrased lore.

Gaps (ESA words id, date, quote):
1. Non-sequitur closing question. Q12 2026-10-18 16:25:06 (34bff929): 'The second part of the sentence ("Have you stood
   under one before? ") also seems kind of nonsensical here?? like a non sequitur?' Also ESA lanes/2.5x/handoff.md:34
   item list "no non-sequitur closing question". No hit in the shelf.
2. A speaker never describes their own doings in the accuser's words. Q15 2026-10-19 08:45:06 (75b80ffc): '"and
   nothing else" is another classic AI overuse tell ... it's also odd that they admit to robbery ... Infer some
   general rule from that.' Agent-recorded rule in ESA memory dialogue-owner-rules-2026-10-19. Not in the shelf
   ("nothing else" is a ban only; the general rule is not).
3. Overuse of "never" and "count" and "keep/hold" as a cap across a body of lines. Q13 2026-10-18 16:25:06: 'fails
   the 'overuse of never' rule ... "count" overuse is also very AI.' Style-core bans "count" lightly; there is no
   per-corpus cap on never/keep/hold (ESA handoff 2.5x:34 "cap never/count/keep/hold").
4. Talk is true to what the player must really do: Q25 "they should only be saying all this stuff about salt and items
   if you actually do have to pay in salt and items!" and Q26 rumours of bandits must mean bandits. owner-bar holds the
   general truth rule; the dialogue skill should say it for trade and rumour specifically (Q25, Q26, 2026-10-18).
5. The helper explains what the thing IS, from lore, with the player knowing nothing about the speaker's job: Q3, Q4,
   Q5, Q6, Q72, Q76-Q78 ("As the player, I don't know this person is a net-mender!"). Partly in style-guide (newcomer)
   but the "player does not know the speaker's role or profession" rule is not stated.
6. Formality follows person: Q81 2026-10-19: "Formality should derive from personality and role ... The chatty beach
   buyer should say 'I'm' instead of 'I am'". In voices.md/style-guide as contractions; the Argonian-contraction rule
   conflict recorded in ESA lanes/2.7d/r1-report.md ("The owner wants formality to follow the person") is unresolved.
7. No two people share a word-for-word sentence, but views may match: Q24 2026-10-17 11:12:26 ("nobody should have word
   for word identical sentences to each other, otherwise they're just clones"). 0143 covers near-verbatim restatement;
   the "converging on one AI voice" corpus read (Q33 broad read) is not specified in the shelf.
8. UESP-wiki register for place prose: Q7 (already style-core section 4, present).
9. "I tend it and I don't explain it": and-joined contradictory halves (Q12) present as style-core 3.3.
10. Q2/Q8 "less AI ... too abrupt ... pack too much information into each pithy phrase ... It's ok for some
    personalities to be short and curt but not everyone!" Core 4 says the second sentence makes an answer longer,
    never curter; the owner's complaint is both too curt AND too clipped. Partly present.
11. Q29 branching topic trees unlocking others (Morrowind), and Q30/Q31: verbatim real Morrowind lines matched to the
    speaker's race and personality are "the single most useful thing" for the writer. Present in SKILL.md only as a
    corpus idea (corpus_split.py); check the dialogue-write references include race-matched Morrowind exemplars.
12. ESA 60-writing section 45e example: "With this death, a root the story grew along is severed" -> "With this death,
    a root is severed." (stranded preposition, portentous gravitas; "When a line feels portentous, cut it in half").
    Present in story/design/quests/60-writing-and-lore.md, not in style-core.
13. Overuse of "does not" vs contractions; "claim" and "the count/the tally" (Q81-Q83): present in the bans list.
14. Method rules for style (not style rules): lean on qualitative critics, not gates (Q32, Q42); owner's EveryDay-Writer
    and creative-writing-skills links (Q85, 2026-10-19): not reviewed in this repo, unknown if done.
15. Today's own rule (nw-05c line 29-30 and OR 2026-11-16): the explorer's own text obeys the writing rules, "The
    story" not "the story, all of it". In OR but not in the shelf.

No owner style rules were found in ESA beyond these and the ones already imported into this repo (style-guide.md and
style-core.md are marked "imported unchanged from ESA @ b581910f").

## D. Supersession map (older -> newer)

- Quest markers: none (2026-10-27) -> markers wanted (2026-11-12) -> riddle exceptions (2026-11-13) -> faction markers
  and journal rumours (2026-11-16).
- Quest scripting ceiling: "nothing harder than an average Skyrim quest" (2026-11-06) -> Morrowind-level (2026-11-12) +
  six narrow additions (2026-11-13, #71).
- Faction set: ESA 32 factions / eight majors (Aug-Oct) -> "fewer factions" (2026-11-13) -> the new
  nine-plus-two roster (2026-11-16).
- The thieves -> "thieves guild type one" (2026-11-16), now the Eelskins, same heist climax idea.
- The detectives -> the Lampbearers (same line; now with the who/means/motive/opportunity form and the three-way arc).
- Pirates: cut as a boat system (ESA 0042) -> a full joinable line with possible sea fights (2026-11-16).
- Chainbreakers: Owing record-rewriting as mechanism (ESA 0028) -> must be drama not chores (2026-11-13) -> full
  prison-break, safe-house and freed-people service design (2026-11-16).
- Factions' skills: "tied to the faction's own skills" (2026-11-06, #50) -> per faction in nw-05c.

## Recommendations
1. Add section B items 1-11 to owner-bar.md's "Shape of a quest" under a new "Factions" heading, each quoting nw-05c, in
   the same commit as the faction skill update (CLAUDE.md rule on same-day recording). Evidence: owner-bar line 146-149
   only points at the file.
2. Read the owner's full 77-note batch of 2026-11-16 through ArtifactData; only 2 notes are verbatim in the repo.
   Evidence: the story-feedback skill; nw-05c line 3-4 says 77 notes, two long ones kept.
3. Ask the owner one question: where did he say the heist and Brotherhood things (chat transcripts of 2026-08, in
   ESA's lanes/2.7d/owner-words crawl? That crawl covers dialogue only). The old repo's agent-held master plan section
   ESA docs/quests/00-overview.md lines 222-231 is the nearest record; use it as the reference table for the new thieves
   and Shadowscales lines (TG08-TG10, SS06).
4. For the Shadowscales join, research UESP for how Oblivion and Skyrim join their assassins (the owner asked "how does
   this work in Skyrim/oblivion?"); no source in either repo answers it.
5. Style: fold section C items 1, 2, 3, 4, 5 and 15 into style-core.md or dialogue-write's bans.yaml/SKILL.md.

Covered: this repo docs/owner-rulings.md (all 700 lines), story/design/owner-bar.md (all), docs/decisions/0025, story/design/old-decisions/0028 (and 0026/0027/0018/0143/0145 headers), docs/phases/new-worldspace-plan/nw-05*.md and walk-6-quests-handover.md, owner-brief.md and inherited-rulings.md at d269dbf5^, all owner-authored issue comments (89) in this repo, all 4 issues and 100 comments in ESA, ESA CLAUDE.md, decisions 0009/0025/0026/0027/0028/0042/0043/0151/0153, docs/quests/00-overview, 40-factions (sections 27-32), 60-writing, lanes/2.7d/owner-words/README.md and the transcript indexes, lanes/2.7/dialogue/owner-goals-crawl.md, world/sources/lore/extrapolation/owner-questions.md and quest-plan-deltas.md; style-core.md, style-guide.md (grep), dialogue-write skill (grep) · Skipped: ArtifactData explorer notes (no tool), ESA owner tmp/ files (not in repo), ESA transcripts-a..d bodies (merged into owner-words README, only grepped), git history of docs/owner-brief.md before d269dbf5^ beyond the final version, story/design/quests/lines/*.md (agent story files), ESA lanes/2.7d/rollout packets (agent output).
