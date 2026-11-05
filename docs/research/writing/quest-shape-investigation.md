# Quest shapes: MURDER, MISSING, RECKONING (investigation design)

Status: **researched from page reads (2026-10-28).** Labels: [V Sn] verified on the page listed under Sources; [K] prior knowledge, unchecked; [I] inference for Argonia. Not readable: uesp.net, fandom.com, reddit.com (bot check). Not fetched: Emily Short's Obra Dinn post, Pope's GDC talks, Shadows of Doubt and L.A. Noire design talks (Shadows of Doubt is known only through S13).

## Sources (all fetched and read)
- S1 https://thealexandrian.net/wordpress/1118/roleplaying-games/three-clue-rule (Three Clue Rule)
- S2 https://thealexandrian.net/wordpress/7949/roleplaying-games/node-based-scenario-design-part-1-the-plotted-approach
- S3 https://thealexandrian.net/wordpress/7985/roleplaying-games/node-based-scenario-design-part-3-inverting-the-three-clue-rule
- S4 https://thealexandrian.net/wordpress/8049/roleplaying-games/node-based-scenario-design-part-9-types-of-nodes
- S5 https://thealexandrian.net/wordpress/8197/roleplaying-games/advanced-node-based-design-part-4-the-second-track
- S6 https://thealexandrian.net/wordpress/8202/roleplaying-games/advanced-node-based-design-part-5-the-two-prongs-of-mystery-design
- S7 https://en.wikipedia.org/wiki/Return_of_the_Obra_Dinn
- S8 https://en.wikipedia.org/wiki/The_Case_of_the_Golden_Idol
- S9 https://www.gamedeveloper.com/design/case-of-the-golden-idol
- S10 https://www.gamedeveloper.com/road-to-igf-2023/-the-case-of-the-golden-idol-i-used-frequent-testing-to-improve-its-mystery-solving
- S11 https://www.gamedeveloper.com/business/road-to-the-igf-lucas-pope-s-i-return-of-the-obra-dinn-i-
- S12 https://dukope.com/devlogs/obra-dinn/tig-27/
- S13 https://gmtk.substack.com/p/what-makes-a-great-detective-game
- S14 https://emshort.blog/2014/01/09/reading-and-hypothesis/
- S15 https://emshort.blog/2016/11/21/mailbag-mysteries-in-cyoa/
- S16 https://emshort.blog/2015/05/24/framed-invisible-parties-and-the-world-plot-interface/
- S17 https://en.wikipedia.org/wiki/L.A._Noire
- S18 https://en.wikipedia.org/wiki/Pentiment_(video_game)
- S19 https://en.wikipedia.org/wiki/Her_Story_(video_game)
- S20 https://en.wikipedia.org/wiki/Sherlock_Holmes:_Crimes_%26_Punishments
- S21 https://frogwares-studio.tumblr.com/post/45102739150/sherlock-holmes-crimes-punishments

## Principles
1. **Every conclusion the player must reach has at least three clues, by different routes, with no exceptions.** A clue is a plan; three give one plan and two backups. The author cannot judge what is "obvious", and surplus clues cost nothing. [V S1]
2. **One required clue is really four chokepoints:** search the place, care about the object, identify it, draw the conclusion. In a text game: visit, notice the topic, know what it is, connect it. [V S1]
3. **Any chokepoint problem needs three solutions**, not only conclusions. Alexander's vital secret door is found by a search, a cultist's note and a damaged journal; alternatives also give the door a builder and a user. [V S1]
4. **Clues point to nodes (people, places, things, organisations, events), not to the next clue.** Inverted rule: if the player can reach any three leads, they reach at least one conclusion. The start node holds three leads; every later node adds leads to unvisited nodes. A plotted chain with three clues per step spoon-feeds. [V S2, S3]
5. **Separate the two jobs of a clue.** A *concept* clue helps work out what happened; a *lead* takes the player to another node. Only leads count towards keeping the case moving, and concept clues can be spread thin. [V S6]
6. **Be permissive:** if a player has a sound way of investigating, give them something useful; withholding closes a route to success. [V S1]
7. **Make the player assert the answer, against facts, from a closed set.** Obra Dinn: name each person and give cause and killer from a catalogue; some deaths accept more than one valid answer. Golden Idol: drop collected words into blanks. [V S7, S8, S9]
8. **Confirm in batches, but never leave the player blind.** Obra Dinn validates fates in threes (pairs for the last six). [V S7] Golden Idol first said only right or wrong for the whole puzzle, which frustrated players on long cases. Fixes: sub-puzzles that show progress (identify the people; one custom puzzle per case) and a signal when two or fewer slots are wrong, which the team admits made it easier and shorter. [V S9] Pope saw brute-forcing as a risk from early on. [K, search snippet]
9. **Closed sets make elimination legitimate.** Obra Dinn names crew by narrowing from the roster. [V S7] Example: the captain's last words name "Abigail's brother"; the roster gives her maiden name; one man aboard shares it. [V S13]
10. **Test sufficiency by watching players.** Golden Idol used four or five friends per case and interviews, not metrics. Red flags: the player grasps everything at once then sticks on a technicality; the player is lost (add clues); one clue skips several steps (remove it); an item makes it trivial (the will written out in full was cut). [V S9, S10]
11. **A "thought path" of questions helps** (which key opens which door, whose room, so who the culprit is), with steps sequential or parallel, but the developers say it never became a reliable framework. [V S9, S10]
12. **Keep clues few and relevant.** Lived-in clutter overloaded recall, so Golden Idol kept only what the solution or a good misdirection needed. [V S9] Short: knowledge-modelling mysteries need systematic information and a model small enough to remember. [V S16]
13. **A wrong accusation needs a legible cost.** Options: rating penalty (L.A. Noire) [V S17]; 3 to 5 solutions and 6 to 10 endings per case, with a condemn-or-absolve choice, where the devblog says conclusions are reasoned but not guaranteed true (Crimes & Punishments) [V S20, S21]; one trial, no verdict told (Paradise Killer) [V S13]; accuse whoever you think guilty or deserving, with deaths following (Pentiment) [V S18].
14. **Red herrings must be refutable.** Golden Idol's inn murder: all suspects armed, several with motive, a strong herring (bloody writing), then clues remove suspects by access or occupation. Players still miss or invent clues, so routes are bumpy. [V S9] That every herring needs a refuter is [I].
15. **Culprit present early; no author-only facts.** [K] (Knox, Van Dine)
16. **Facts are fixed, interpretation is the player's.** Obra Dinn never gives names; identity comes from speech, accent, clothing, items. Pope placed characters in varied situations to leave room for clues and made each scene interesting alone. [V S11, S13]
17. **Interrogation must test what the player can know.** L.A. Noire's interrogations were praised, yet some reviewers found choices vague and sometimes illogical. Contradiction style: present the fact against the statement. [V S17, S13]
18. **Do not play the game for the player.** L.A. Noire tells you where to go; investigation-style games give a space too large to check, so skill is choosing what to follow. [V S13]
19. **Hypothesis is the pleasure:** backstory mysteries invite guesses confirmed or refuted. [V S14] A reader comment suggests a late run of closed-list questions (whose rifle, who killed, what motive). [V S15, comment]
20. **Escalate by widening the unknown.** [I] Pentiment's repeated manipulative notes across cases model linked cases. [V S18]

## Methods and patterns

### M1. Murder case template (hidden truth first)
1. Write the truth in one paragraph: killer, method, motive, time, place, what was disturbed afterwards.
2. Write the final day's timeline with everyone's whereabouts. [K]
3. Build the **knowledge matrix**: each cast member knows, saw, lies about, and why. Each lie must be refutable by one thing. [I]
4. List 3 to 6 physical things (weapon, residue, missing item, forged letter, wound, ledger entry).
5. List every **conclusion** the player must reach (killer, method, motive, plus any needed to find them: "he is a former lover", "check the butcher"). Give each three clues from different channels (thing, statement, place or record). Alexander's werewolf case yields nine paths from three conclusions. [V S1]
6. Add a **lead layer**: for every node the player must visit, three leads from other nodes, including the start node. [V S3, S6]
7. Add 2 to 3 red herrings, each with a refuting clue. Make several suspects plausible: shared means, shady habits, at least two with motive. [V S9]
8. Define the **accusation gate** (M3) and endings: right culprit, right culprit wrong motive, wrong culprit, none found; kin reactions.
9. **Dry run**: delete one clue per conclusion and confirm it still resolves; delete one lead per node and confirm the node is still reachable. Then ask a stranger to play it (see M8). [V S1, S10]

### M2. Node and lead map (how to draw it)
Nodes: person, place, thing, organisation, event, or an activity the player must do; keep nodes modular and not too large or fiddly, and nest sub-nodes where a body (a guild, a household) has parts. [V S4] Draw leads as arrows. Checks: the start node has three leads; every necessary node has three inbound leads in total, from different nodes; and after the player has visited any two nodes, three leads to the rest still remain. [V S3] Keep each cluster to 5 to 9 nodes; for a harder feel add a **second track**, a disconnected cluster linked by a different method (a timeline of events, say) so the player sees twice as many nodes as the author handles. [V S5]

### M3. Accusation with evidence (Morrowind-friendly)
The player names a suspect in dialogue, then presents things as topics or inventory exhibits; each sets a conclusion flag; enough flags (not all) convict, too few gives an unravelling conviction or "bring me more". [I, from Ace Attorney-style presentation, K] Add a closed-list run (who, with what, why) so a lucky name cannot win [V S15, comment], and a condemn, absolve or stay silent choice [V S20].

### M4. Journal of open questions
The journal lists open questions as sentences ("X killed Y with ___ because ___") and holds statements as facts attributed to people. Pope's book is the model: it sets events in sequence though experienced out of order, with a rationale per answer. [V S11] Fill a blank only on the player's chosen statement. Validate correct answers in batches, and give coarse feedback ("close") for long cases, after Golden Idol's testing. [V S7, S9] Also provide a recall aid: Pope's manifest sketch exists so the player can match faces to names outside flashbacks, and carries identity clues. [V S12]

### M5. Lie-and-refute interview
Each NPC has a true statement, a false one, and the refuting fact. The player presents the fact (topic or exhibit); disposition decides whether they recant. Mark's "contradiction style" example: present the other witness's statement to the liar and he amends his own. [V S13] This is the fair text version of L.A. Noire. [I]

### M6. Missing-person arc: trail, turn, fate
Trail of 3 to 5 stops, each leaving a trace that the next stop explains; but build it as nodes (M2), so a missed stop has alternative leads rather than a rail. [V S2, S3] One turn: staged trail or willing departure. Fate: alive and unwilling, alive and hidden, dead, changed. The reveal recasts earlier stops. Her Story is a model for a missing-man case told as searchable testimony: the player searches words from transcripts, tags clips, and a checker shows how many have been seen. [V S19]

### M7. Cold-case surfacing
Old crime surfaces through a physical thing, a deathbed statement, or a mismatch in records. Build a guilty-party list: instigator, hand, beneficiary, silent witness, each with different culpability and a current life that justice would damage. [I] Pentiment builds investigations on ambiguous period evidence, "rumor and innuendo". [V S18]

### M8. Fairness test (a quest-writing agent can run this)
1. For each conclusion list its three clues and their channels; fail the case if two share a channel or a single NPC.
2. For each necessary node list three leads; fail if any come from one source.
3. Simulate three blind routes: one that misses the first clue everywhere, one that skips the richest NPC, one that begins at the last node. Each must reach an ending.
4. Check there are no steps that a single clue bypasses unintentionally (remove it if so). [V S10]
5. Check pacing: players must not grasp the whole case early and then stall on a detail. [V S10]
6. Check recall load: if the player must remember more than a handful of linked facts, the journal must hold them. [V S16, S9]
7. Someone who did not write the case reads the journal alone and names each open question. [I, after S10]

## Anti-patterns
- One clue gates the case (a missing key item, an unlisted dialogue topic); the "bread crumb trail" where each scene hands over its clue without any finding is also rejected by Alexander as not feeling like a mystery. [V S1]
- Clue-to-clue chains with no alternative route; or three clues at every step of a plot, which spoon-feeds. [V S2]
- Counting concept clues as leads. [V S6]
- Red herrings with no refutation; solutions needing an author-only fact. [I]
- Accusing by name alone, so trying everyone wins. [I]
- Giving only a whole-puzzle right/wrong verdict on a long case. [V S9]
- Lived-in clutter that the player cannot hold in memory. [V S9]
- A case that is obvious at a glance, bypassing deduction (a will written out in full). [V S9]
- Menu options that telegraph what to investigate; layered, world-backed choices reduce this. [V S15]
- Solutions needing out-of-world knowledge (modern forensics); Pentiment uses era-appropriate ambiguity instead. [V S18]
- Silent failure; killing the only witness without a backup path; markers; timers that destroy evidence mid-reasoning. [I]
- Tone-guessing interrogation. [V S17]

## Player-perspective notes
- The journal is working memory; write entries as facts attributed to people ("Hlaren says...") so contradictions can be spotted. [I] Pope's late book was exactly this fix. [V S11]
- Facing an empty book is itself motivation to fill it. [V S11]
- Players invent clues that are not there and miss real ones, so expect bumpy, individual routes. [V S9]
- Skyrim's "Blood on the Ice" lacks true deduction; Oblivion's "Whodunit?" is closer to our aim; Morrowind's investigations rely on topics and journal entries. [K]

## What changes without quest markers in a text-led game
- Directions are given in dialogue as human descriptions; every location in a case needs a describable approach in at least two NPCs' mouths (this is the lead rule, S3, in speech). [I]
- The journal is the only map: record who said what and what is unknown, not instructions. [I]
- Keywords are the clue-picking mechanic, as in Her Story, where search terms taken from statements are the way through a body of testimony. [V S19, S13] Never put a required fact outside a hyperlink or a readable thing. [I]
- Disposition gates information; give each essential fact a path that does not need high disposition (bribe, document, other witness). [I]
- Short statements, one new fact each; a place check only for objects described in text beforehand. [I]
- The engine cannot see what the player concludes, so make conclusions explicit acts: a presented exhibit, a journal blank, a named suspect. [I]

## Design checklist

### MURDER
- [ ] Truth paragraph, timeline, knowledge matrix.
- [ ] Each conclusion (killer, method, motive, and any "go there" conclusion) has three clues by different channels.
- [ ] Each necessary node has three leads from different nodes; start node has three.
- [ ] Each lie has one refuting thing; each herring is refutable; several suspects plausible.
- [ ] Culprit appears before the midpoint.
- [ ] Accusation needs killer plus exhibit; wrong accusation has a defined outcome.
- [ ] Endings: right, partial, wrong, unsolved; kin reaction.
- [ ] M8 fairness test passed.
- [ ] No required fact behind high disposition only.

### MISSING
- [ ] Fate and reason decided first.
- [ ] 3 to 5 stops as nodes with leads from more than the previous stop.
- [ ] Trace at each stop explains the next; describable approach without markers.
- [ ] A turn that recasts earlier stops.
- [ ] Fate reveal earned by a deduction, not a cutscene.
- [ ] A fate for every ending: found alive, found dead, never found, wrongly believed found.

### RECKONING
- [ ] The old crime as a timeline with each party's role and what they have now.
- [ ] Surfacing event physical, specific, discoverable by three routes.
- [ ] More than one guilty party with different blame.
- [ ] Justice and mercy both have a cost and a beneficiary.
- [ ] The wronged party's view is present and may disagree with the law.
- [ ] Outcomes recorded in the world.

## Notes for the detectives' faction line
- **Escalation:** (1) petty theft with one unknown; (2) a missing person with a trail; (3) a murder with a closed cast; (4) a cold case implicating a respected figure; (5) a grand murder with linked cases. Each tier adds a skill: statement comparison, trail-following, accusation with exhibits, multiple guilty parties, synthesis. [I] Obra Dinn's structure is a model: break the whole into discrete disasters, each a manageable unit, then place each death on two axes, story time and order of discovery. [V S11]
- **Second track for the finale:** run the grand murder as two clusters that the player only later realises are one conspiracy, each 4 to 6 nodes. [V S5]
- **Recurring thread:** a hidden hand seen in several cases (Pentiment's repeated manipulating notes across a quarter-century is the model). [V S18] The rival detective (competent, sometimes provably wrong, conclusions offered as testimony) is [I].
- **Finale:** reuse earlier cases as evidence: a clue from case 2 refutes a lie in case 5, which Alexander's note that a later node may reveal something about an earlier one supports. [V S5] Final accusation uses the full M3 gate with three exhibits and a choice of what to do with the truth (law, mercy, silence). [V S20 for the condemn/absolve choice] Fix the ending first; let individual cases find their way. [V S10]
- **Fairness contract:** teach the system in case one: the journal lists open questions, keywords carry clues, exhibits unlock accusation. [I]
- **Cross-faction:** assassins create bodies, thieves create missing things; detective cases start from their aftermath. [I]
