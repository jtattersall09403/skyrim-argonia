# Quest design for open-world RPGs: principles and methods

Date: 2026-10-27. Purpose: input for the quest WRITER and quest REVIEWER skills.

**Evidence limits (read first).** The session could only run web searches; page fetches (thealexandrian.net, ianparberry.com, gdcvault.com, gamedeveloper.com and others) failed on network allow-listing. Every "evidence" line below therefore rests on search-result summaries, not full texts. Items marked **[inference]** are our reasoning, not a source claim. Items marked **[unverified]** were named in the brief but not confirmed. The GDC Vault talks (Sawyer, Keenan) were not read. Re-check the key ones once those hosts are allowed.

## Sources

- Justin Alexander, Three Clue Rule and Node-Based Scenario Design series (search summaries only): https://thealexandrian.net/?p=7985 ; https://thealexandrian.net/wordpress/8122/roleplaying-games/node-based-scenario-design-collectors-edition ; https://thealexandrian.net/wordpress/8202/roleplaying-games/advanced-node-based-design-part-5-the-two-prongs-of-mystery-design
- Doran and Parberry, "A Prototype Quest Generator Based on a Structural Analysis of Quests from Four MMORPGs" (PCG 2011): https://ianparberry.com/pubs/pcg2011.pdf ; project page https://ianparberry.com/research/quests ; 2015 follow-up https://ianparberry.com/pubs/DoranParberryQuests2015.pdf
- Aarseth, "From Hunt the Wumpus to EverQuest: Introduction to Quest Theory" (ICEC 2005): https://pure.itu.dk/en/publications/from-hunt-the-wumpus-to-everquest-introduction-to-quest-theory/
- Jeff Howard, Quests: Design, Theory, and History in Games and Narratives (A K Peters 2008; 2nd ed. CRC 2021): https://www.tenlong.com.tw/products/9780367686048
- Ken Levine, "Narrative Legos" (GDC 2014), announcement and coverage: https://www.gamedeveloper.com/design/ken-levine-joins-gdc-2014-speaker-lineup-to-talk-about-narrative-legos- ; https://gameinformer.com/b/news/archive/2014/03/22/ken-levine-talks-player-participation-and-breaking-away-from-linear-narratives
- Josh Sawyer, "Do (Say) The Right Thing" (GDC 2012): https://gdcvault.com/play/1015758/Do-(Say)-The-Right-Thing (login wall; content not read). Related coverage: https://pcgamesn.com/fallout-new-vegas/making-of ; https://pcgamer.com/games/fallout/fallout-new-vegas-director-josh-sawyer-says-the-ncr-and-caesars-legion-feel-so-real-because-their-members-disagree-and-challenge-each-other-you-have-to-wrestle-with-the-fact-that-it-contains-multitudes/
- CD Projekt Red quest design: Tomaszkiewicz PAX Australia 2015 talk reported at https://www.gamespark.jp/article/2015/11/04/61465.html ; GameSpot interview https://www.gamespot.com/articles/cd-projekt-red-explains-why-the-witcher-3s-open-wo/1100-6477549/ ; Sasko GDC 2023 lessons https://www.gamedeveloper.com/marketing/10-key-takeaways-from-the-quest-design-of-cyberpunk-2077-and-the-witcher-3
- Emily Short, reviews touching mystery and knowledge: https://emshort.blog/2011/07/07/introcomp-2011-chunky-blues/ ; https://emshort.blog/2014/12/02/detective-grimoire-sfb-games/
- Story sifting: Felt (Kreminski, Dickinson, Wardrip-Fruin, ICIDS 2019) https://github.com/mkremins/felt ; Winnow https://ojs.aaai.org/index.php/AIIDE/article/view/18903
- Disco Elysium, GDC talk "Meaningless Choices and Impractical Advice": https://gdcvault.com/play/1027048/-Disco-Elysium-Meaningless-Choices
- Kingdom Come: Deliverance previews: https://store.epicgames.com/news/kingdom-come-deliverance-ii-medieval-rpg-preview ; https://www.pcgames.de/Kingdom-Come-Deliverance-Spiel-16151/Specials/Vorschau-1245393/2/
- Fan Morrowind-derived quest rules (Skywind/TES Renewal handbook; a modern fan standard, not Bethesda): https://handbook.tesrskywind.com/dev/Principles ; Rolston on writing Morrowind quest outlines: https://gamebanshee.com/k8c6c

**Not found:** no usable sources surfaced for Pentiment, Baldur's Gate 3, Planescape: Torment, Arcanum or Gothic quest design, nor for a specific Tomaszkiewicz GDC talk or a "no simple fetch quests" quote [unverified]. Do not cite those.

## Principles

1. Build every investigation from conclusions the player must reach, each supported by at least three independent clues. Evidence: Three Clue Rule (Alexander).
2. Make leads redundant in both directions: each node should be reachable by at least three clues and should offer at least three onward clues, so one missed clue never strands the player. Evidence: Alexander, inverted Three Clue Rule and node design.
3. Separate the hidden truth from the investigation that uncovers it: design what really happened first, then the trail. Evidence: Alexander, "two prongs of mystery design" (title and summary only; detail not read).
4. Treat quest structure as reusable patterns with preconditions and postconditions, so a quest can be validated mechanically. Evidence: Doran and Parberry found shared structure across 750+ MMORPG quests, each pattern with an implicit pre- and postcondition.
5. Describe a quest in terms of spaces, objects, actors and challenges, so each can be checked against the world. Evidence: Howard's four components. Aarseth's work likewise treats quest and landscape types as the base structure of gameplay.
6. Do not force a single "right" resolution; give options that carry both virtue and cost. Evidence: forum relay of Sawyer's GDC 2012 talk (secondary).
7. Make factions and parties feel like groups of people who disagree, not blocks. Evidence: Sawyer coverage (PC Gamer headline). Reactivity was a stated priority for New Vegas (Sawyer, 2010 statement via search summary).
8. Offer several solution paths with distinct trade-offs, including non-violent ones. Evidence: Hardcore Gaming 101 on New Vegas; PC Games preview of Kingdom Come: Deliverance (many routes, each with advantages and disadvantages).
9. Make consequences visible to the player; poorly signalled consequences are mostly wasted effort. Evidence: Sasko, GDC 2023 (search summary).
10. Quests must work if the player takes a different path or order in an open world. Evidence: Tomaszkiewicz via GameSpot summary.
11. Ensure the player's knowledge and available actions stay in step; evidence the player holds should gate the questions or accusations they can make. Evidence: Short on "knowledge conflicts" and evidence notebooks (Chunky Blues, An Act of Murder reviews).
12. Log discovered clues automatically in a player-facing record that dialogue can reference. Evidence: Short on Detective Grimoire dossier. **[inference]** The Morrowind journal plus topic list is our equivalent.
13. Where there are no markers, objectives and journal text must carry the whole route, and detective quests should not point at specific clues. Evidence: Skywind handbook (fan standard; Morrowind-inspired, not Bethesda's own). Mark this as a design choice we adopt, not a proven industry norm.
14. Keep content internally varied and interesting; Morrowind's writers reportedly held that boring content was wrong. Evidence: community-sourced quote attributed to Kirkbride (weak).
15. Quest content should be recombinable "bricks" with explicit interfaces rather than one-off scripts. Evidence: Levine, Narrative Legos (coverage inconsistent on details). **[inference]** for our use as data records.
16. Simulation state can be mined for stories: define patterns over recorded events instead of hand-scripting every outcome. Evidence: story sifting (Felt, Winnow). **[inference]** Relevance to a hand-authored mod is limited; use the idea for validation queries, not generation.

## Methods

**Hidden-truth record ("what really happened").** Before any stage exists, write a timeline of events with who, where, when and why, in physical terms (bodies, objects, locations, dates). Every later clue, rumour and line must be derivable from it. Source basis: Alexander's two prongs; the rest is **[inference]**.

**Knowledge matrix.** Rows are facts from the hidden truth; columns are cast members and the player. Each cell is one of: knows, believes (state what, true or false), suspects, hides (with reason), ignorant. Dialogue is then written only from a character's own column. Add a "reveal condition" per cell (topic, item, rank, time). Basis: Short on knowledge modelling and knowledge conflict; the matrix form is **[inference]**.

**Three-clue graph.** List the conclusions the player must reach. For each, list three clues in different forms (a spoken line, a found object, an observed place or behaviour). Then check each node for three inbound and three outbound leads. Basis: Alexander. Add a "fail-forward" rule **[inference]**: a missed or failed check delays or costs, but does not stop, the quest.

**Pattern skeleton with pre/postconditions.** Express each stage as a typed step (go, get, learn, speak to, deliver, kill, escort, persuade) with explicit precondition and postcondition on world state. A stage is valid only if its precondition is produced by an earlier postcondition. Basis: Doran and Parberry. Also record a motivation per actor (why they want this) **[their taxonomy not read; do not quote categories]**.

**Quest needs list (for world builders).** Derive mechanically from the quest data: every location, container, item, NPC, route, time-of-day and altered state the quest names, each with a status (exists, to create, to modify) and a location reference. The writer cannot mark a quest ready while any entry is "unknown". Basis: **[inference]**; no studio template was found in the sources reached. Howard's spaces/objects/actors/challenges is the natural checklist.

**Single source of truth.** Keep one structured data file per quest plus a shared world-facts file. Dialogue, journal text and needs lists are generated or checked from them, so a claim in a line must cite a fact ID. **[inference]**; consistent with the Doran/Parberry and "narrative Legos" data-driven approaches but not itself reported in the sources.

**Choice and consequence table.** For each ending list who benefits, who pays, what changes in the world and where the player will see it. Basis: Sawyer (secondary), Sasko.

**Direction-by-dialogue pass.** For each location the player must reach, write the spoken or journal route (landmark, distance, direction, a sign they have arrived) and check the NPC could plausibly know it. Basis: Skywind handbook (fan standard) plus **[inference]**.

**Plausibility test for premise.** State the premise in one sentence, then list what each involved party knows and what they would do about it. If a sensible villager would act otherwise, the premise fails. This is the check the failed attempt missed. **[inference]**.

## Anti-patterns

- A premise that depends on people behaving against their own interest or knowledge (the corpse in the water). **[inference]**
- Fetch or collection quests with no story or twist (Tomaszkiewicz reportedly criticised collection-heavy design; Attack of the Fanboy headline on removing fetch quests, body not read).
- A single clue gating a conclusion; a clue behind a failable check with no alternative (breaks the Three Clue Rule).
- The player is told the answer rather than finding it. **[inference]**, from the failed attempt.
- Quest objects, places or routes that the world does not contain. **[inference]**
- A "right" answer the writer prefers, with the other choices punished (Sawyer, secondary).
- Consequences the player never sees (Sasko).
- Markers or journal lines that name the exact clue in a detective quest (Skywind handbook).
- Dialogue where an NPC states a fact they could not know (knowledge conflict, Short).
- Over-long branching text with no reuse; Disco Elysium's volume reportedly broke its authoring tool (secondary news item), which suggests tooling and structure matter.

## Reviewer checklist (yes/no)

1. Can the premise be said in one sentence, and would a sensible person in that setting act as the premise requires?
2. Is there a hidden-truth timeline in physical terms, and does every clue derive from it?
3. Does each required conclusion have at least three clues in at least two different forms?
4. Does each investigative node have at least three leads in and three out?
5. Can the player finish if they miss any one clue, fail any one check, or arrive in a different order?
6. Does the player investigate or deduce something, rather than being told?
7. Does the knowledge matrix exist, and does every line use only what its speaker knows or believes?
8. Does each giver and each suspect have a plausible motive, stated?
9. Is every location, item, NPC, route and state the quest uses on the needs list, with a status other than "unknown"?
10. Can the whole quest be followed with no markers from journal text and dialogue directions alone?
11. Are there at least two solution paths with distinct costs?
12. Does each ending change something the player will visibly meet later?
13. Is no ending presented as the only correct one?
14. Is there a reward that is concrete, proportionate to risk and effort, and tied to the story?
15. Does the quest avoid being a plain fetch, kill or delivery without a twist or discovery?
16. Does every stage have a precondition produced by an earlier stage?
17. Is the danger fixed (not scaled to the player) and signposted by dialogue or world cues?
18. Is there anything Nordic, vanilla-Skyrim or out-of-setting in names, objects or lines?

## Gaps to close (when hosts are allowed)

Read in full: Alexander's Three Clue Rule and two-prongs articles; Doran and Parberry 2011 (motivation categories); Sawyer GDC 2012; Sasko GDC 2023; Keenan GDC 2021. Find real sources for Pentiment, BG3, Planescape, Arcanum, Gothic, and for reward psychology (this report found none; reward items above rest on **[inference]**).
