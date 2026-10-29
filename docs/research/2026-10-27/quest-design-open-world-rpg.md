# Quest design for open-world RPGs: principles and methods

Date: 2026-10-27. Purpose: input for the `quest-write` and `quest-review` skills.

**Labels.** [V] fetched and read in full or in the relevant passage this session. [K] prior knowledge, or a claim seen only in a headline or search snippet, not read. [I] our inference. A line carries the label of its weakest support.

**Evidence limits.** Read: Alexander (Three Clue Rule, inverted rule, two prongs, node index), Doran and Parberry 2011, Sasko GDC 2023 write-up (Game Developer), Levine write-up (Game Informer), Short (two reviews), Ryan, Rigby and Przybylski 2006 (abstract), Skywind handbook, Aarseth (abstract). Not read: GDC Vault talks (Sawyer 2012, Keenan, Disco Elysium; the Vault was in maintenance and needs JavaScript), Howard's book (a shop listing only), the Felt and Winnow papers (project descriptions only), the PC Gamer Sawyer article (headline only; body was page furniture), Tomaszkiewicz talks, any studio quest-document template. Claims resting on these are [K] or [I].

## Sources

- Alexander, "The Three Clue Rule": https://thealexandrian.net/wordpress/1118/roleplaying-games/three-clue-rule [V]
- Alexander, "Node-Based Scenario Design, Part 3: Inverting the Three Clue Rule": https://thealexandrian.net/wordpress/8148/roleplaying-games/node-based-scenario-design-part-3-inverting-the-three-clue-rule [V]
- Alexander, "Advanced Node-Based Design, Part 5: The Two Prongs of Mystery Design": https://thealexandrian.net/wordpress/8202/roleplaying-games/advanced-node-based-design-part-5-the-two-prongs-of-mystery-design [V]
- Doran and Parberry, "A Prototype Quest Generator Based on a Structural Analysis of Quests from Four MMORPGs" (PCG 2011): https://ianparberry.com/pubs/pcg2011.pdf [V]
- Sasko, GDC 2023, as reported by Game Developer: https://www.gamedeveloper.com/marketing/10-key-takeaways-from-the-quest-design-of-cyberpunk-2077-and-the-witcher-3 [V]
- Levine, "Narrative Legos" (GDC 2014), as reported by Game Informer: https://gameinformer.com/b/news/archive/2014/03/22/ken-levine-talks-player-participation-and-breaking-away-from-linear-narratives [V]
- Short, Chunky Blues review (knowledge puzzle, evidence systems): https://emshort.blog/2011/07/07/introcomp-2011-chunky-blues/ [V]; Detective Grimoire review (clue dossier): https://emshort.blog/2014/12/02/detective-grimoire-sfb-games/ [V]
- Ryan, Rigby and Przybylski, "The Motivational Pull of Video Games" (Motivation and Emotion 2006): https://www.rochester.edu/warner/lida/wp-content/uploads/2022/11/02bfe513dd59366750000000.pdf [V, abstract and first page only]
- Skywind handbook, Quest Design Principles (fan standard, Morrowind-derived, not Bethesda): https://handbook.tesrskywind.com/dev/Principles [V]
- Aarseth, "From Hunt the Wumpus to EverQuest" (ICEC 2005), abstract: https://pure.itu.dk/en/publications/from-hunt-the-wumpus-to-everquest-introduction-to-quest-theory/ [V]
- Howard, Quests: Design, Theory, and History in Games and Narratives (2008; 2nd ed. 2021) [K]
- Sawyer, "Do (Say) The Right Thing" (GDC 2012): https://gdcvault.com/play/1015758/Do-(Say)-The-Right-Thing [K; unreadable]; PC Gamer headline on New Vegas factions [K]
- Story sifting: Felt (Kreminski et al., 2019), Winnow (AIIDE 2021): https://github.com/mkremins/winnow [K; search snippet]

## Principles

1. For every conclusion the player must reach, supply at least three clues. The rule is deliberately exceptionless, because the designer already knows the answer and cannot judge how obvious a clue is. If the player finds all three, they confirm it. [V Alexander]
2. Treat any chokepoint (a problem that must be solved for the quest to continue) as needing at least three distinct solutions, not just three clues. Solutions should differ in kind (a check, a note elsewhere, a document, a second route, a villain's behaviour, an interrogation). Adding them tends to make the scene richer, because the secret door acquires a builder, users and an escape role. [V Alexander]
3. Invert the rule for navigation: if the player holds any three clues pointing at three possible nodes, they will reach at least one. So give each node several leads out, and the structure keeps moving without a fixed order. Clue access is assumed, not guaranteed discovery. [V Alexander]
4. Separate two kinds of clue. Concept clues reveal what happened; scenario clues (leads) send the player to the next place or person. A node may carry only leads. A clue that explains but does not point onward does not count towards the lead quota. Clue density can rise with depth or with the difficulty of reaching a node. [V Alexander, two prongs] (The earlier draft read "two prongs" as hidden truth versus trail; that was wrong.)
5. A quest's skeleton is a small set of reusable structures. Doran and Parberry found 750+ MMORPG quests from four games share one: an NPC motivation selects a strategy (a verb-noun pair), each strategy a sequence of 1 to 6 actions, and actions may recurse into subquests. Each atomic action has a stated precondition and postcondition (for example, goto needs "you know where to go and how to get there"). [V]
6. Give every quest-giver a motivation. The nine they found: knowledge, comfort, reputation, serenity, protection, conquest, wealth, ability, equipment. The authors argue motivations make quests look intentional rather than random. Observed counts were uneven (conquest 20%, equipment and knowledge and protection about 18% each, comfort 1.6%), and a designer can steer flavour by shifting the mix. [V]
7. Choose among variant structures by what the player is assumed to know and the state of the world, not at random: their rules for "learn where to go" differ on whether the player already knows. [V]
8. Do not rely on a single "right" resolution. Sawyer is reported as holding that for each character neither choice is correct, since each carries virtue and sacrifice. [K, secondhand] Sasko agrees in spirit: build dilemmas that are ambiguous and open to interpretation, and stake them properly before the choice. [V]
9. Make consequences visible. Sasko: subtle consequences go unseen, and effort on a consequence that is not telegraphed is mostly wasted. Delayed consequences, returned at an unexpected moment, leave the biggest impression. [V]
10. Offer choices the player and character would naturally expect to have; when the player's urge and the available options line up, the design is good. [V Sasko]
11. Separate signal from noise: deliver important information in focused, isolated moments, put minor talk in action (walking to a place), move some exposition into the world, and cut repeated summaries by several characters. [V Sasko]
12. Keep the player's knowledge and the protagonist's abilities in step. Short names the failure a "knowledge conflict": the player has deduced something the protagonist cannot yet act on, or the protagonist is pushed to act while the player has no idea why. [V Short] (This is about player and protagonist, not about NPC knowledge; our NPC-knowledge rule below is our own extension. [I])
13. Evidence systems have known costs. Presenting evidence at the right moment rewards insight, but players cannot tell "I lack a clue" from "I have not made the leap", and are driven to try every item on every claim; they also feel they are reacting rather than constructing. Letting the player combine known facts into hypotheses, which can be wrong, addressed this. [V Short]
14. Record discovered clues automatically in a player-facing record that conversation can reference (clue book, dossier, notebook). Morrowind's journal and topic list is our equivalent. [V Short on dossiers; I for the Morrowind mapping]
15. Without markers, the objective text and journal must carry the route: quests completable with no markers; quest-givers who do not know a place point to whoever does, and the marker moves only when the player has been told; detective quests never mark clues. [V Skywind; a fan standard we adopt, not an industry norm [I]]
16. The world does not wait: quest NPCs and items exist before the quest, can be killed or taken early, quests fail when the player kills the wrong person, and a debt can be paid by the player directly if dialogue signals that. [V Skywind]
17. Levine's model, as reported: give each key NPC a small set of obvious "passions" that respond to player action, make factions' goals conflict so choices cost something, and model only a limited set of believable, impactful things. [V, via coverage; slides unread]
18. Motivation research: games pull through autonomy, competence and relatedness, each predicting enjoyment and future play independently. [V abstract] Reward design should therefore support these (choice of approach, visible mastery, bonds with people), not just item value. [I]
19. Reduce overdesign: details matter only when they have meaning, and a game is not a life simulation. Remove dialogue that does not do work. [V Sasko]
20. Quest content should be recombinable parts with explicit interfaces, and simulation events can be mined for stories by pattern queries (story sifting). For a hand-authored mod, use that for validation queries, not generation. [K Winnow; I]
21. Design for the team you have: the quest designer should give other disciplines something to show. [V Sasko] Pair with a handoff rule in Methods. [I]

## Methods

**Hidden-truth record.** Write what really happened as a timeline in physical terms (who, where, when, how, why) before any stage exists. Every clue, rumour and line must be derivable from it. Alexander separates the mystery from the route to it, which supports doing this first. [I, built on V]

**Clue register with kinds.** For each conclusion list at least three clues of different form (spoken, found object, observed place or behaviour). Tag every clue as concept (what happened) or lead (where next). Check each node has at least three leads out and that the player can reach it from at least three. [V Alexander; tagging scheme I]

**Chokepoint list.** Mark every problem the quest cannot continue without (a locked door, a name, a person who must be met). Give each three solutions of different kind. [V]

**Knowledge matrix.** Rows are facts from the hidden truth; columns are cast and the player. Cell values: knows, believes (true or false, state what), suspects, hides (with reason), ignorant, plus the reveal condition (topic, item, rank, time). Dialogue is written from a character's own column only. [I; motivated by Short on knowledge puzzles]

**Pattern skeleton with pre/postconditions.** Express each stage as a typed step (goto, get, learn, give, listen, report, use, kill, escort, steal, explore) with a precondition and postcondition on world state. A stage is valid only if an earlier postcondition produces its precondition. Record the giver's motivation from the nine. Treat "goto" as needing a prior "learn" unless the player already knows the way, so a route is always taught by someone or something. [V Doran and Parberry; wording I]

**Choice and consequence table.** For each ending: who benefits, who pays, what changes in the world, and where the player will see it. A consequence with no "where seen" entry fails. [V Sasko; table I]

**Direction-by-dialogue pass.** For each place the player must reach, write the spoken or journal route (landmark, distance, direction, a sign of arrival) and check that the speaker could plausibly know it. [V Skywind; I]

**Quest needs list.** Derive from the record every place, container, item, NPC, route, time of day and altered state, each with a status (exists, to create, to modify) and a location reference. A quest is not ready with any "unknown". No studio template was found; this is a record handed to world builders, modelled on Aarseth's and Howard's spaces, objects, actors and challenges. [I; K Howard]

**Single source of truth.** One structured record per quest plus a shared world-facts file; dialogue and journal text cite fact IDs and are generated or checked against them. A line claiming a fact the speaker's column does not give them fails the check. [I] Skywind keeps scripting in quest stages and leaves dialogue entries with only stage and disposition changes, so revision is cheap; the same separation of data from lines suits generated briefs. [V Skywind; I]

**Plausibility test for premise.** State the premise in one sentence, then list what each party knows and would do about it. If a sensible person would act otherwise, the premise fails. [I]

**Handoff to level and world builders.** Searches found only generic level-design documents (objectives, layout, enemy placement, environmental storytelling); none showed quest-specific fields. The needs list, with the stage list and the fact IDs behind each item, serves as the handoff. [I; weak search evidence]

## Anti-patterns

- A premise needing people to act against their own interest or knowledge. [I]
- A single clue gating a conclusion, or a clue behind a failable check with no alternative. [V Alexander]
- Judging a clue "obvious enough" and skipping the third. [V Alexander]
- Clues that explain but give no lead out, so the player has facts and nowhere to go. [V Alexander]
- A node reachable by only one lead. [V Alexander]
- Quests that are plain fetch, kill or deliver steps with no motivation or discovery; Doran and Parberry's data show how common such bare strategies are. [V; judgement I]
- Hidden-state conflicts: the player knows something the protagonist cannot act on, or the protagonist is pushed into an action the player cannot explain. [V Short]
- Evidence systems that force trying every item on every claim. [V Short]
- Consequences that are too subtle to see. [V Sasko]
- Repeated summaries by several NPCs, and information buried in noise. [V Sasko]
- Over-detailing, such as intricate elements with no meaning. [V Sasko]
- Markers or journal lines that name the exact clue in a detective quest. [V Skywind]
- Quest NPCs or items that appear only when the quest starts, so the player cannot meet or kill them early. [V Skywind]
- Quest items flagged undroppable, chests that can only be opened by one key with no other route. [V Skywind]
- Quest objects, places or routes the world does not contain. [I]
- A preferred ending with the others punished. [K Sawyer; I]
- Dialogue in which an NPC states a fact they could not know. [I]
- Rewards that ignore autonomy and competence, such as an item with no choice of approach. [I]

## Reviewer checklist (yes/no)

1. Can the premise be said in one sentence, and would a sensible person in that setting act as it requires?
2. Is there a hidden-truth timeline in physical terms, and does every clue derive from it?
3. Does each required conclusion have at least three clues, in at least two forms?
4. Is every clue tagged concept or lead, and does each node have at least three leads in and three out?
5. Does every chokepoint have three solutions of different kinds?
6. Can the player finish if they miss any one clue, fail any one check, or arrive in a different order?
7. Does the player investigate or deduce, rather than being told?
8. Does the knowledge matrix exist, and does each line use only what its speaker knows or believes?
9. Can the player always act on what they have deduced, and always tell why they are asked to act?
10. Does each giver have a stated motivation, and each suspect a plausible one?
11. Does every stage have a precondition produced by an earlier stage, and is every route taught by someone who could know it?
12. Is every place, item, NPC, route and state on the needs list with a status other than "unknown"?
13. Can the quest be followed with no markers, from the journal and dialogue directions alone?
14. Do quest NPCs and items exist before the quest starts, and can the player fail it by killing or taking them?
15. Are there at least two solution paths with distinct costs, and is no ending the only correct one?
16. Does each ending change something the player will see later, with the place recorded?
17. Is the reward concrete, proportionate to risk, tied to the story, and does it respect the player's choice of approach?
18. Does the quest avoid being a plain fetch, kill or delivery without a discovery?
19. Is important information given in a focused moment, with no repeated summaries?
20. Is the danger fixed (not scaled to the player) and signposted by dialogue or world cues?
21. Is there anything Nordic, vanilla-Skyrim or out-of-setting in names, objects or lines?
