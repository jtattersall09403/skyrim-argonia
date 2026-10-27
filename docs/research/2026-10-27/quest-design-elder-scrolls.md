# Quest design in the Elder Scrolls: what is known

Evidence limits: WebFetch was blocked for every host tried (handbook.tesrskywind.com, gamebanshee.com, gamesbeat.com, gamedeveloper.com), so only search-result summaries were read, not full articles or GDC slides. Developer-sourced claims are thin; forum claims are opinion. Items marked (inference) are ours, not sourced. To deepen this, allow those hosts and read the primary pages listed below.

## Sources

- Skywind handbook, Quest Design Principles (quests completable without markers; descriptive objectives; detailed journal): https://handbook.tesrskywind.com/dev/Principles
- Steam thread on Morrowind vs Skyrim markers (no-marker worked because objectives were simple and directions were logged): https://steamcommunity.com/app/489830/discussions/0/594018181914310953
- Lemmy thread (Morrowind directions are relative, re-checkable in the journal): https://lemmy.nekusoul.de/post/14395/133856
- RPGHQ threads (directions sometimes wrong; many Morrowind quests are fetch or kill): https://rpghq.org/forums/viewtopic.php?p=38152
- Reddit r/Morrowind, "Top tier quest design": https://redlib.hackliberty.org/r/Morrowind/comments/1g9guax/top_tier_quest_design
- Nexus mod adding written directions to Oblivion's journal: https://www.nexusmods.com/oblivion/mods/51729
- Bruce Nesmith on Radiant Story (GamesBeat, 2012 lecture coverage): https://gamesbeat.com/bethesdas-nesmith-reflects-on-the-difficult-birth-of-skyrims-radiant-story-system/
- Radiant criticism: Nexus article https://www.nexusmods.com/skyrimspecialedition/articles/5169 ; Lisbon thesis https://labjogos.tecnico.ulisboa.pt/en/thesis/procedural-quest-generation-improving-skyrim-s-radiant-story ; GameStar https://www.gamestar.de/artikel/starfields-quests-muessen-aus-skyrims-fehlern-lernen,3397375.html
- Pagliarulo, Oblivion team Q&A (Dark Brotherhood intent): https://gamebanshee.com/k66yd ; his posts: https://app.uesp.net/wiki/General:Emil_Pagliarulo%27s_Posts
- Game Developer on Rolston's Twitch session (hands-off Oblivion, tabletop roots): https://www.gamedeveloper.com/design/-i-oblivion-s-i-lead-designer-shares-the-secret-sauce-behind-its-success
- Rolston interviews: https://gamebanshee.com/k8c6c ; https://content1.uesp.net/wiki/General:Morrowind_Italia_Interview_with_Ken_Rolston ; Goodall: https://content2.uesp.net/wiki/General:Douglas_Goodall_Interview
- UESP quest pages: Forsworn Conspiracy https://en.uesp.net/wiki/Skyrim:Read_Eltrys%27_Note ; Whodunit? https://content3.m.uesp.net/wiki/Oblivion:Whodunit ; Whodunit guides https://orcz.com/oblivion-remastered-dark-brotherhood-whodunit-guide/
- Blood on the Ice branching and bug reports: https://steamcommunity.com/app/489830/discussions/0/3109142236159105252
- Not yet read (leads): Burgess GDC transcript https://gamebanshee.com/kuuu ; Noclip "Designing the Dark Brotherhood" (2018); Pagliarulo STORY talk (2016).

## Principles

1. Make every objective findable from text alone: name a landmark, a relative direction and a distance. Evidence: Skywind handbook; Lemmy thread on Morrowind's relative directions.
2. Keep each step simple, and put the difficulty in the investigation, not in finding the place. Evidence: Steam thread says no-marker worked because objectives were simple and directions were logged.
3. Let the journal carry the directions so the player can reopen it mid-journey. Evidence: Lemmy thread; Skywind handbook.
4. Give an investigation several suspects or leads that can be worked in any order, with partial payment for partial progress. Evidence: UESP, Forsworn Conspiracy (Eltrys pays gold per person looked into; branching follow-up).
5. Give the player more than one way to the answer, including unadvertised shortcuts. Evidence: Steam thread on Blood on the Ice (talking to Wuunferth skips ahead); Whodunit? guides (stealth kills, persuasion, turning guests on each other).
6. Make a choice carry a consequence the player sees later. Evidence: UESP, Forsworn Conspiracy (the investigation sets up an ambush and a side-picking follow-up).
7. Make the player's role distinctive and give the faction line a point of view. Evidence: Pagliarulo said the Dark Brotherhood asks what if the hero were a cold, remorseless killer (Oblivion Q&A).
8. Reserve hand-written content for anything the story depends on; keep generated content for upkeep tasks. Evidence: Nesmith: radiant was rejected for the main quest because hand-crafted storytelling is better; radiant is easy to overdo.
9. Let the world react to how the player behaves. Evidence: Rolston, Morrowind Italia interview ("merchant prince" example).
10. Pay out: a reward that matches the effort, such as a permanent skill bonus for a clean Whodunit? run. Evidence: Whodunit? guides. Fits the gold-per-lead payment above.
11. (Inference) Every clue is a physical item, a person, or a topic that exists in the world and is reachable before it is needed.
12. (Inference) The hidden truth must be consistent and each clue must contradict at least one false theory, so deduction is possible.
13. (Inference) A quest should be several scenes long: set-up, at least two independent lines of enquiry, a revelation, a decision, a consequence.

## Anti-patterns

1. Implausible premise: NPCs behave against their own interests to create a problem. Evidence: first attempt (villagers leaving a corpse in the drinking water). Inference for the general rule.
2. Fetch-and-kill templates repeated until they feel the same. Evidence: Nexus article and forum complaints on radiant quests; RPGHQ on Morrowind fetch quests.
3. Directions that are vague or wrong. Evidence: RPGHQ thread (disputed, but a known risk); Steam thread that Skyrim text is often too vague to navigate.
4. Reliance on markers in place of text. Evidence: Skywind handbook; Oblivion directions mod.
5. Linear talk-to-A-then-B-then-C with no deduction. Evidence: first attempt; contrast with branching UESP quests above.
6. Generated quests left in the log after they become impossible. Evidence: Nexus article on radiant objectives.
7. Fragile scripted triggers, such as a victim's scripted death, that break the quest. Evidence: Steam thread calling Blood on the Ice among the buggiest.
8. Unannounced shortcuts or blocked branches that strand players (e.g. unable to speak to Helgird after taking the blood trail first). Evidence: same thread. Fine as a bonus route, bad as a trap.
9. Hands-off structure with weak urgency: Rolston said Morrowind's main plot lacked narrative urgency. Evidence: Wikipedia summary of Rolston.
10. Faction work as radiant upkeep with no story. Evidence: Thieves Guild criticism on the Skyrim forum threads (opinion).
11. (Inference) Required objects or places that do not exist in the data; no reward; no refusal or failure state.

## Checklist for a reviewer

- Would every named person act this way given their own interests and knowledge?
- Is the hidden truth written in one paragraph, and is every clue consistent with it?
- Is each clue a placed item, person or topic that exists in the world data now?
- Can the player reach the solution with at least two orders of enquiry?
- Is there a false lead or red herring that a clue can refute?
- Can the player solve it by reading and thinking, not only by following the next prompt?
- Does the player have to compare or combine two pieces of information?
- Does each objective give landmark, direction and distance in text?
- Are there at least five distinct stages and three locations?
- Is there a real choice, and does it change an ending, a reward or a later line?
- Can the player refuse, fail, or accuse the wrong person, with a defined result?
- Does every ending have a reward, and does it fit the effort?
- Does the quest use no vanilla Nordic element and fit Black Marsh?
- Does the journal read correctly after each stage, whatever the order?
- Are all scripted triggers and kills safe if the player acts early or out of order?

## Notes for a Morrowind-style text-led game without markers

- Directions are quest content: put them in the journal at the moment the NPC gives them, and test them against the map (Skywind handbook; forum evidence that bad directions anger players).
- Teach through topics: each clue should add a hyperlinked keyword that opens a new question for another NPC. (Inference; consistent with the topic design.)
- Investigation shape suggested by the Forsworn Conspiracy: a hub NPC, three suspects, partial pay, then a branching consequence.
- Whodunit? shows a social puzzle with several solution routes and a skill reward; no clue-by-clue analysis was found, so clue logic is untested here.
- Fixed, non-levelled danger means the quest should warn of danger in dialogue. (Inference.)
- Before approving, list every physical thing the quest needs and mark it as existing, planned, or missing. (Inference from the first attempt's failure.)
