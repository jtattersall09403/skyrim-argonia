# Quest design in the Elder Scrolls: what is known

Labels: [V] read in full or in the relevant section this pass, with URL; [K] prior knowledge, unverified; [I] our inference. Paraphrased throughout.

Hosts not read: uesp.net and fandom.com (blocked), gamebanshee.com (empty even via archive), reddit.com, gdcvault.com (login stub only), the Noclip and STORY Pagliarulo talks (not found), Burgess's GDC 2010 storytelling talk (only seen in search results).

## Sources actually read

- Skywind Handbook, Quest Design Principles (read whole): https://handbook.tesrskywind.com/dev/Principles
- Nesmith on Radiant Story, GamesBeat report of his 2012 Vancouver talk: https://gamesbeat.com/bethesdas-nesmith-reflects-on-the-difficult-birth-of-skyrims-radiant-story-system/
- Burgess, "Skyrim's Modular Approach to Level Design" (Game Developer write-up of his GDC 2013 talk): https://www.gamedeveloper.com/design/skyrim-s-modular-approach-to-level-design
- Rolston, Game Developer Oblivion interview: https://www.gamedeveloper.com/design/-i-oblivion-s-i-lead-designer-shares-the-secret-sauce-behind-its-success
- Rolston, Tribunal interview (RPGCodex repost): https://rpgcodex.net/article.php?id=339
- Goodall interview (RPGCodex repost): https://rpgcodex.net/article.php?id=4151
- Wikipedia: Morrowind https://en.wikipedia.org/wiki/The_Elder_Scrolls_III:_Morrowind ; Oblivion https://en.wikipedia.org/wiki/The_Elder_Scrolls_IV:_Oblivion ; Skyrim https://en.wikipedia.org/wiki/The_Elder_Scrolls_V:_Skyrim ; Pagliarulo https://en.wikipedia.org/wiki/Emil_Pagliarulo

Still unread: Radiant criticism (Nexus, Lisbon thesis, GameStar), UESP quest pages (Forsworn Conspiracy, Whodunit?, Blood on the Ice), Pagliarulo's own words. Claims resting on those stay [K].

## What the sources establish

**Markers and directions.** Skywind's Rule 0 is to follow Morrowind as closely as possible, and every quest must be completable without markers, which means descriptive objectives and detailed journal entries. [V handbook] A marker appears only where Morrowind had a map marker; a quest giver may place one only if the dialogue says so; revealed markers never enable fast travel, because exploration is part of the quest. [V handbook] Their worked example: in Beneran's Bounty the giver does not know the cave and sends you to Maar Gan, so the marker points to Maar Gan first and to the target only after that NPC has spoken; likewise the first main-quest step sends you to the South Wall for directions, not to Caius. [V handbook] Detective quests get no markers on clues. [V handbook] Markers are a subset of objectives, not the objective itself. [V handbook]

**The journal was Morrowind's weak point.** Skyrim's journal drops old entries, so Skywind must rewrite entries to carry old information, or hand the player notes holding key facts, since Morrowind's scrollable history cannot be reproduced. [V handbook] But reviewers of Morrowind almost universally disliked its single chronological journal as a muddle, with no grouping by quest or completion; Tribunal added sorting by quest. [V Wikipedia Morrowind] Rolston himself admitted the original design had wicked limitations and said the expansion let players browse and filter. [V RPGCodex Tribunal] This corrects the earlier draft, which presented the journal as a strength: the strength is directions written into it, the weakness is its organisation.

**Topics.** Morrowind's dialogue hyperlinks keywords; Goodall liked the system on paper but felt it made roleplaying a character harder, and disliked putting words in the player's mouth. [V RPGCodex Goodall] Rolston's Morrowind Italia goal of tracking information through hyperlinked topics and journal is still [K] (only seen in a search snippet).

**Radiant Story.** Bethesda started from 30 player actions and possible world reactions. [V GamesBeat] Using it for the main quest sounded great but "would play horribly"; a hand-written story is more compelling. [V GamesBeat] Corrections made: job quests limited to fitting NPCs such as innkeepers, custom lines per voice type, tighter conditions on how often events fire, and more custom-built quests because that felt better. [V GamesBeat] A real-world-plausible reaction can still be bad design: an NPC claiming a bought item was stolen was cut because the player always ended up killing him. [V GamesBeat] Skyrim quests can also have parameters adjusted to nearby unexplored areas. [V Wikipedia Skyrim]

**Morrowind's structure.** Free-form by design; Rolston saw the main plot as an introduction to a "distracting crosscurrent" of factions and themes, and he later said it lacked narrative urgency and could have been presented more forcefully, as Oblivion's was, without losing freedom. [V Wikipedia Morrowind] The main plot had seven high-level tasks completable in partial order, with sub-tasks also in any order. [V Wikipedia Morrowind] Goodall thought the main quest made no sense to him and that the game did not react to the player being good or bad except when caught in a crime. [V RPGCodex Goodall]

**Rolston's writing rules.** Per Goodall: key NPCs may not betray the player, lie after being honest, or steal from the player; only one coincidence is allowed; everything must be grounded in something familiar. Goodall preferred writing a true account hidden among false ones, whereas Rolston wrote a dozen accounts with no preferred truth. [V RPGCodex Goodall] Goodall is an openly disgruntled source, so treat his characterisation of Rolston as one side. Rolston also advises keeping a list of your ten favourite quests and analysing them for the team. [V Game Developer Rolston]

**Pagliarulo.** Credited with writing and quest design on Bloodmoon, wrote the Oblivion Dark Brotherhood and Arena lines, and was senior designer and writer on Skyrim. [V Wikipedia Pagliarulo] His own statements on design remain [K].

**Burgess.** The write-up is about modular dungeon kits, not narrative. Findings usable by us: copy-pasted "warehouse" rooms made Oblivion dungeons feel cookie-cutter; players noticed repeated clutter before repeated architecture; kit mashups and a few unique assets keep a place fresh; only ten of about ninety staff built Skyrim's dungeons. [V Game Developer Burgess] Burgess's environmental-storytelling claim is not on this page and stays [K].

**Other.** Skyrim has 244 quests and about 150 dungeons built by eight designers. [V Wikipedia Skyrim] Oblivion's Radiant AI was scaled down later because NPCs killed each other after witnessing thefts. [V Wikipedia Oblivion] Rolston wanted fast travel excluded for immersion; a prototype from Todd Howard won the argument. [V Game Developer Rolston]

## Principles, each with a method an agent can follow

1. **Every objective is findable from text alone.** [V handbook] Method: write each location as landmark, relative direction, distance, and walk it on the map before approval. Give an objective for the person to find first, and only reveal the final place when someone in the world tells the player.
2. **Chain information, not markers.** [V handbook, Beneran's Bounty] Method: a giver who lacks the location names a second NPC; the journal logs that referral as its own step.
3. **The journal carries old facts forward.** [V handbook] Method: each new entry restates the standing question and every still-relevant fact (names, places, directions) in plain words, so a returning player needs nothing earlier. Write the entry for every order the clues can arrive in, and consider a note item the player holds with key facts. The Skywind devs say a toggle back to old entries is unproven, so do not rely on one.
4. **Topics carry clues.** [I] Method: each clue is a keyword that appears when learned and opens a question for another NPC; a dead topic answers briefly rather than looping. Lock topics by stage so a conversation unfolds instead of dumping everything. [V handbook flags instant, unstaged dialogue as a port bug]
5. **The world does not wait.** [V handbook] Method: place quest NPCs and items in the world before the quest starts, make them killable and droppable, let faction work be done before joining, and write a failure stage for each way to ruin the quest (dead giver, lost item, wrong target).
6. **Consequences are real.** [V handbook] Method: for each quest list its failure and refusal states; if a dead NPC blocks progress, the quest fails with a journal line saying so.
7. **Prefer a bypass that is flagged.** [V handbook] Method: if the player can skip a step by doing the task themselves, mark the dialogue option as a lie or shortcut so it is not taken by accident.
8. **No pointless locks.** [V handbook] Method: block a door or chest by something in the fiction (barred, warded), not a bare "requires key", and keep it pickable otherwise.
9. **Hand-write anything the story relies on.** [V GamesBeat] Method: generated content only for upkeep; limit it to NPCs for whom it fits and write per-voice lines to cut repetition.
10. **A plausible reaction is not automatically a good one.** [V GamesBeat] Method: for each branch ask what the player will do next; if the answer is always "kill them", cut or reshape it.
11. **Give every NPC an honest hidden truth.** [V Goodall, as a counter to Rolston] Method: write one true account first, then add false ones that each clue can refute; keep the no-betrayal and one-coincidence rules unless a decision record overrides them. [I] for adopting them.
12. **Vary the places.** [V Burgess] Method: do not reuse a staging room or clutter set across quests; give each location one unique prop or enemy tied to its quest.
13. **Urgency belongs in the text.** [V Wikipedia Morrowind] Method: freedom is fine, but state in dialogue why this matters now, and what changes if the player waits.
14. **Reward in proportion to effort.** [K] guides; method: tie reward tier to route difficulty.
15. **Several leads, any order, partial payment.** [K] Forsworn Conspiracy summary, unverified; method: at least two independent lines of enquiry, each logged separately.
16. **Environmental clues.** [K] Burgess GDC; method: a posed scene may carry a clue if a topic or journal line confirms it.

## Anti-patterns

1. Implausible premise: NPCs acting against their own interests to create a problem. [I]
2. Fetch-and-kill templates repeated until they feel the same. [K]; Nesmith's team saw the same and moved to more custom quests. [V GamesBeat]
3. Vague or wrong directions. [I]; the handbook's marker rules exist because text must do the work. [V handbook]
4. Markers used instead of text, or pointing straight at clues in a detective quest. [V handbook]
5. Linear talk-to-A-then-B with no deduction. [I]
6. One chronological journal with no grouping. [V Wikipedia Morrowind; Rolston Tribunal]
7. Generated objectives left impossible in the log. [K]
8. Fragile scripted triggers, or an unflagged shortcut that strands the player. [K] forum reports; Skywind's dead-NPC rule supports the principle. [V handbook]
9. Whole-conversation dumps and directions available before the quest is given. [V handbook]
10. Hands-off structure with weak urgency. [V Wikipedia Morrowind]
11. A world that does not notice the player's good or bad conduct. [V Goodall, opinion]
12. A reaction that always ends in a fight. [V GamesBeat]
13. Cloned set dressing across locations. [V Burgess]
14. Missing required items or places; no failure state. [I]
15. Directions never walked in play. [I]

## Checklist for a reviewer

Each item [I] unless marked.

- Would every named person act this way given their own interests and knowledge?
- Is the hidden truth one paragraph, and is each clue consistent with it? Does at least one clue refute a false account?
- Is each clue a placed item, person or topic that exists in the world data now?
- Can the player reach the solution through at least two orders of enquiry?
- Does each objective give landmark, direction and distance in text, and has it been walked on the map? [V handbook basis]
- Does the first marker-free step point to the informant, not the target? [V handbook]
- Does every journal entry restate old facts and read correctly in any order? [V handbook basis]
- Are quest NPCs and items present, killable and droppable before the quest starts? [V handbook]
- Is there a defined result for refusal, death of the giver, loss of an item, or accusing the wrong person? [V handbook basis]
- Is any shortcut flagged in the prompt, and can it never strand the player? [V handbook basis]
- Is there a real choice that changes an ending, a reward or a later line?
- Does a dead topic answer briefly and not loop? Do topics unlock by stage?
- Does the quest state its urgency, and does its reward fit the effort?
- Does it use no vanilla Nordic element, and fit Black Marsh?
- Is any scripted trigger safe if the player acts early or out of order?

## Notes for a Morrowind-style game without markers

- Directions are quest content: log them in the journal at the moment they are spoken. [V handbook]
- Because Skyrim's journal keeps no history, our journal text must be cumulative. [V handbook] Whether our own UI can offer a per-quest history is an open build question for the HTML screen route. [I]
- Danger is fixed and not levelled, so dialogue must warn of it. [I]
- Before approval, list every physical thing the quest needs and mark it existing, planned or missing. [I]
- To raise the remaining [K] claims to [V], read the UESP quest pages, the Radiant criticism, and any Pagliarulo transcript, when those hosts become reachable.
