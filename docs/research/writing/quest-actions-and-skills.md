# Quest actions and skills: designing quests that use what the player can do

Date: 2026-10-27. Purpose: give quest writers and reviewers a vocabulary, patterns and counts for making almost every Argonia quest contain real action. Labels: [V url] fetched and read; [K] prior knowledge; [I] inference for Argonia.

## Sources

Fetched and read:
- Spector, Deus Ex postmortem, Game Developer, 2000: https://www.gamedeveloper.com/design/postmortem-ion-storm-s-i-deus-ex-i-
- Doran and Parberry, quest structure paper (PDF, 2011): https://ianparberry.com/pubs/pcg2011.pdf (abstract page: https://ianparberry.com/research/quests)
- Harvey Smith on player choice, Game Developer, 2015: https://www.gamedeveloper.com/design/-i-dishonored-i-s-harvey-smith-player-choice-is-paramount-in-design
- Arkane at GDC 2013, PC Gamer: https://www.pcgamer.com/dishonored-arkane-player-improvisation/
- Oblivion and Skyrim Thieves Guild compared: https://rockymountaincentral.substack.com/p/comparing-the-elder-scrolls-skyrim
- Sasko, Witcher 3 and Cyberpunk quest design (GDC 2023 report): https://www.gamedeveloper.com/marketing/10-key-takeaways-from-the-quest-design-of-cyberpunk-2077-and-the-witcher-3
- Kingdom Come: Deliverance hands-on, PCGamesN: https://pcgamesn.com/kingdom-come-deliverance/stealth-speechcraft-and-story-in-kingdom-come-deliverance
- Disco Elysium, Wikipedia: https://en.wikipedia.org/wiki/Disco_Elysium
- Hitman (2016), Wikipedia: https://en.wikipedia.org/wiki/Hitman_(2016_video_game)
- Mass Effect 2, Wikipedia: https://en.wikipedia.org/wiki/Mass_Effect_2
- The Alexandrian, "Don't Prep Plots": https://thealexandrian.net/wordpress/4147/roleplaying-games/node-based-scenario-design-part-1

Searched but only snippets seen (treated as weak): Oblivion Mages Guild commentary (forums); Mass Effect 2 loyalty guides. Not covered: Thief developer talks, Morrowind guild quests first-hand (UESP blocked) [K only].

## Principles

1. **A quest is a problem, not a puzzle, and it has more than one way through.** Spector's Deus Ex rules: "problems not puzzles", "there should always be more than one way to get past a game obstacle", and Smith's addendum that every mission and problem be keyed to skills, objects and weapons, using several "tools" (capabilities, resources, combat, character interaction). [V Deus Ex postmortem] Arkane says the same: "multiple solutions, multiple stylistic approaches". [V Smith 2015]
2. **The game should recognise how the player plays.** Deus Ex was meant to "tune itself" to the player's style rather than force one. [V Deus Ex] Arkane's systems "listened" to play (rats scale with the player's corpses). [V PC Gamer] [I] For Argonia, report which skills a player used in the journal and let later NPCs mention it.
3. **Multiple paths cost real effort; plan the cost.** Spector admits the simulation was too shallow, so designers had to "brute-force" a skill path, an alternative path and so on per problem. [V Deus Ex] Smith: avoiding an unlock schedule is "much more expensive and much harder". [V Smith 2015] [I] So Argonia should author a small fixed set of reusable approach slots per quest (see Combination patterns), not unlimited freedom.
4. **Guide and attract; do not chain.** Smith: doing the only possible thing, then the next only possible thing, "really doesn't feel as creative or as rich". [V PC Gamer] [I] This is the project's "never talk to X, then Y, then Z" rule restated by a studio that ships.
5. **Prep situations, not plots.** A situation is a set of circumstances whose events depend on player action; a plot is a fixed A-B-C sequence. [V Alexandrian] [I] The quest record's hidden truth plus cast knowledge is a situation; stages should be states, not a script.
6. **A guild's quests must use the guild's skills, or the guild feels fake.** Oblivion's Thieves Guild is praised because fencing quotas, a code, and heists demand lockpicking and sneaking, while Skyrim's has "little thieving" and becomes dungeon-crawling and intimidation. [V Substack] The Oblivion Mages Guild is criticised as linear, isolated recommendation errands with skill requirements removed. [K, forum-grade; snippets only]
7. **Skills should be checked in the world, and failure should keep the game going.** Kingdom Come ties speech outcomes to reputation, NPC temperament and even the player's bloodied armour; a failed approach closes that route but others remain, and the target may be killed by others if the player dawdles. [V PCGamesN] Disco Elysium resolves events through skill checks and dialogue instead of combat, and failures can be interesting. [V Wikipedia] [I] Argonia's persuasion should read the NPC and the situation, not just a number.
8. **Each mission should teach and reward a way of playing.** Hitman uses public spaces where players learn social stealth without penalty, then private spaces needing disguises, with overheard conversations opening creative opportunities. [V Wikipedia Hitman] Mass Effect 2 ties loyalty missions to unlocking a power and the finale. [V Wikipedia ME2]
9. **Build a verb vocabulary and a grammar.** Doran and Parberry analysed over 750 MMORPG quests: nine NPC motivations (Knowledge, Comfort, Reputation, Serenity, Protection, Conquest, Wealth, Ability, Equipment), each with 2-7 strategies as verb-noun pairs ("steal supplies", "rescue NPC"), each breaking into 1-6 actions, built from atomic actions (goto, get, give, use, kill, steal, spy, listen, report, damage, repair, escort, defend, capture, take, and similar). [V Doran] Their sample strategies are mostly 2-3 steps such as get-goto-give, which shows how thin typical MMO quests are. [V Doran, table fragments]
10. **Vary and cull repetition deliberately.** Sasko: avoid repeating the same ideas across designers, create varied content, cut repeated exposition. [V Sasko] [I] Variety needs counting (see Variety measures).
11. **Consequences must be visible.** Players miss subtle effects. [V Sasko] [I] If the player used stealth and the guard later has a cold, the journal or an NPC should say so.

## An action vocabulary for Argonia

Each verb has a skill family and variants. A quest step is one verb with its object and a place; a quest is a sequence or graph of steps. [I] throughout.

**Fight family** (Long Blade, Axe, Spear, Blunt, Hand-to-hand, Block, Marksman; DS1 combat)
- Clear: empty a hist-shrine cave of bog-wraiths; drive reed-pirates off a moored hulk; hold a causeway.
- Duel: a contested name-fight against a rival, no armour allowed; a spear duel on a rocking raft.
- Defend: hold a village gate until the tide turns; guard a boatload through a night attack.
- Hunt: kill one named creature (a swamp-drake) after finding its range.

**Stealth family** (Sneak, Security, Short Blade, Light Armor, Acrobatics)
- Infiltrate: cross a guarded stilt-house by roofs and rope bridges.
- Steal: lift a ledger from a sleeping factor; take a ceremonial knife from a locked shrine chest.
- Plant: leave evidence in a rival's cache; swap a forged tally.
- Spy: hide in rafters and overhear a smugglers' parley; watch a courier's route from reeds.
- Assassinate: poison a feast cup, drown a target at a ford, or garrote from the water, with a non-lethal option.
- Pickpocket: lift a key from a boatman mid-conversation.

**Social family** (Speechcraft, Mercantile, disposition, disguise)
- Persuade: talk a ferryman into a night crossing by reading what he fears.
- Barter: buy a favour with stock, not coin; undercut a rival at market day.
- Interrogate: press a drunk clerk, or bribe him.
- Disguise: pass as a tax-collector's party, a priest's retinue, or a mourner at a river funeral.
- Mediate: end a clan feud by getting both sides' terms agreed.

**Magic family** (Destruction, Alteration, Illusion, Conjuration, Mysticism, Restoration, Enchant)
- Cast to solve: Alteration to cross water or hold breath; Illusion to calm a guard or mask a smell; Mysticism to find a hidden thing; Conjuration to bind a guardian.
- Heal: Restoration against a marsh fever for a whole village before dawn.
- Enchant: imbue a charm with a specific effect the client needs.
- Ward or break: dispel a shrine curse by a ritual sequence.

**Traversal family** (Athletics, Acrobatics, climbing, swimming, diving, boats)
- Climb: scale a living Hist trunk to a high shrine; cross a collapsed ziggurat by ledges.
- Swim and dive: recover a sunken chest from a flooded ruin on one breath, with a rope as the route marker; follow an underwater passage.
- Sail and pole: pole a flat-bottomed boat through reed mazes to a hidden village; race a rival boat to a landing; tow a barge through a current.
- Chase: pursue a thief over roofs and rafts; flee a patrol by water.
- Explore: map a flooded ruin's breathing pockets.

**Craft and lore family** (Alchemy, Armorer, Enchant, tracking, reading)
- Brew: make an antivenom from three marsh plants whose location is clues.
- Repair: mend a hull, a ward-stone, or a bridge under time pressure.
- Track: follow a wounded animal or smuggler's trail by broken reeds and mud.
- Investigate: read a scene (marks, wounds, tide level) and decide who did it; compare two documents.
- Forage and gather: collect eggs from nests without waking the mother.

**Logistics family** (Mercantile, Athletics, escort)
- Escort: bring a witness upriver and keep them alive.
- Smuggle: carry goods past a checkpoint by false bottom or night route.
- Courier: deliver a letter against a deadline through flood.

## Combination patterns

A pattern is a named template of 2-4 verbs from at least two families. Writers fill the template with place, cast and stakes. [I]

1. **Gate and Choice (multiple solutions).** One goal, three or more ways in: fight the guards, sneak the roofs, talk or bribe the gatekeeper, or swim the intake. Each way costs something different. Add a fourth for a mage or climber if the place supports it. [Spector/Smith principle]
2. **Forger's Chain.** Sneak in, steal a ledger, forge or alter a copy (Alchemy/Enchant/Security tool), return it, persuade the clerk to confirm the false entry. Mixes stealth, craft, social.
3. **Cover Story.** Obtain a disguise (steal, buy or make), enter a restricted place, spy while hidden, then exit before a check. Fail state: disguise slips and combat or flight follows.
4. **Watcher Then Act.** Spy and learn a routine (listen, track), choose a moment, then use the knowledge (assassinate, steal, ambush). Hitman-style learning loop. [V Wikipedia Hitman]
5. **Dive and Return.** Learn the flooded ruin's layout from an elder (social), prepare breath (alchemy or Alteration), dive, retrieve, and then deal with a pursuer on the surface.
6. **Escort Under Pressure.** Escort, defend, then change role midway (carry the wounded across water, or the escortee must be hidden while passing a patrol).
7. **Trade the Trade.** Barter for an item, find it spoiled, track the seller, then recover payment by persuasion or force. Reverse of a straight fetch.
8. **Climb to Judge.** Climb to a high place, investigate a scene, then confront or persuade a suspect with the evidence. Detective profile.
9. **Fix the Flood.** Repair a structure, protect it from an attack, then use the result (a bridge, ward or boat) to reach a second step.
10. **Mirror.** The same goal offered from two clients with opposite methods (one wants it quiet, one wants it loud). Doran's motivation lens (Protection against Conquest) gives the reasons. [V Doran]

Escalation along a line: 1) quest 1 uses one family with a single verb pair; 2) mid-line quests combine two families; 3) late quests combine three and remove the player's safest tool (no weapons, no light, no boat). The final job may cite earlier pieces: reuse a forged ledger or a learned route. [I]

## Faction action profiles

Method [I]:
1. Write the faction's identity in one sentence: what it values, what it fears, how it earns.
2. List its Doran-style motivations (Knowledge, Protection, Conquest, Wealth, and so on). [V Doran]
3. Pick two **signature** verb families (60 to 70 percent of the faction's steps), one **support** family (20 to 30 percent), and one **forbidden or rare** family that gives the faction character.
4. Each rank unlocks an escalation of the signature pair, not a new type.
5. Give each faction one verb that only it uses (for example a ritual or a rule-bound duel).
6. Check against the guild-skills lesson: a player should be able to tell the faction from three random quests. [V Substack]

Examples (to be fitted to real Argonia factions):
- **Assassins:** signature stealth plus killing; support investigation; rare open combat, and persuasion limited to cover stories.
- **Thieves:** signature stealth and theft; support social (fencing, barter); rare killing, which would break a code, as in Oblivion's no-killing rule. [V Substack]
- **Fighters:** signature combat and escort or defend; support traversal (marching, boats); rare stealth.
- **Mages:** signature spellcasting solutions and enchanting; support lore and craft; rare melee.
- **Detectives or magistrates:** signature investigate, track, interrogate; support social and stealth (spy); combat as the climax only.
- **Boatmen or river clans:** signature sail, pole, dive; support barter and escort.

## Variety measures

Per quest (record in the quest record header):
- Verb list: ordered list of steps using the vocabulary above.
- Families used: at least 2 for any quest bar a deliberate short job; target 3 for mid and late quests.
- Approach slots: number of distinct valid routes through the main problem, and which build each favours (fighter, thief, mage, talker). Target at least 3 for main problems, minimum 2. [V Deus Ex]
- Talk steps: no more than one pure-talk step in a row; count talk-only quests (target 0 as owner rule).
- Pattern used: name from the list.
- A failure branch that continues play. [V PCGamesN]

Per line (faction or major thread):
- Family share against the faction profile (signature at least 60 percent).
- Pattern list with no repeats of the same pattern in adjacent quests; no more than 2 uses of one pattern per line.
- Escalation: each later quest adds a family or removes a tool.
- Setting variety: at least three of land, water surface, underwater, climb, interior.

Per region packet:
- Verb-pair heat map: count each (family, verb) used across quests in the packet; no verb above 25 percent of steps; every family appears at least once; at least one quest using each Black Marsh traversal verb (dive, pole, climb) per packet where the place allows.
- No repeated verb sequence (exact ordered list) within a region. Two quests may share a pattern but not the same ordered list.
- Build coverage: for each of the four builds, at least one quest in the packet where that build is the best fit, and none where it is locked out. [I]
- Reuse log: each repeated location or gimmick noted.

A reviewer script could parse the header and flag breaches; this fits the "measurable" gate in CLAUDE.md. [I]

## Anti-patterns

- **Fetch chain:** talk, go, talk, go, report. Doran's sample strategies show this is the default MMO shape. [V Doran]
- **Skill label with no skill use:** quest says "thief" but is combat in a dungeon. [V Substack]
- **Linear errands with skills stripped out:** the Oblivion Mages Guild complaint. [K]
- **Single required skill:** one lock only a lockpicker can pass, no alternative. [V Deus Ex]
- **Forced failure** that the player cannot react to. [V Deus Ex]
- **Hidden paths with no signal:** the player never learns the other routes exist. Arkane balanced this by guiding and attracting. [V PC Gamer]
- **Check-spam persuasion:** try every option until one works. [V PCGamesN]
- **Variety by cosmetics:** same verb pair, new names.
- **Padding a verb:** twelve bog-wraiths instead of one good fight.
- **Over-design:** details that do not matter. [V Sasko]
- **Invisible consequences.** [V Sasko]
- **Verbs that the engine cannot yet support** (for example diving objectives before swimming is in), which contradicts the "systems ship whole" rule. [I]

## Checklist

1. Can the quest be described as a situation (hidden truth, cast, clock) rather than a script? [V Alexandrian]
2. At least two skill families, and not talk-talk-talk?
3. At least three approach slots for the main problem, covering fighter, stealth, magic and social builds where plausible?
4. Does the quest use a named pattern, and is it not repeated in the neighbouring quest?
5. Does it fit its faction's signature and support families?
6. Is there a Black Marsh verb (water, dive, climb, boat) where the setting allows?
7. Does failure of one approach leave a route open and show a visible consequence?
8. Is the player's chosen method acknowledged afterwards (journal line, NPC remark)?
9. Is every verb supported by built systems at the quest's phase?
10. Are the counts above recorded in the quest record, and does the line and packet total pass?
