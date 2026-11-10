# Review: the opening act and slice quests, writing and recipe side (2026-11-10)

Read from the built plugin (`plugin/Argonia/Quests`, `DialogTopics`, `DialogBranches`), the story data
(`story/data/db`, `story/data/quest_lines`, `story/data/dialogue-writer`), the builders' comments and Papyrus, the five
skills and the design docs. Nothing was run in game. CONFIRMED = read in the data or plugin; PLAUSIBLE = follows from
what was read but needs one more look (named). Engine faults met on the way are marked "for the engine reviewer".

**Live docs that cover this.** `docs/design/quests-on-a-world.md` (parts 3, 5, 7, 8) is the recipe; its claims on doors,
SEQ, answers as choices and "a stage per step with a target" are confirmed in MQ01 stages 10 to 30 only. It is
contradicted by `quest-write/quest-record.md` (objectives "no target markers", "no markers (old 0137)"), by
`quest-review` item 8 ("with no markers"), by `blocks.md` row E-stage ("objective, no target") and by the style guide's
journal rule ("each entry re-summarises the chain"). The one doc to edit first is `docs/design/quests-on-a-world.md`
(part 7 and the part 5 table); the skill texts in section D are cut from it.

Counts: 11 quests, 264 quest INFOs (160 of them warm or cool band copies), 42 objectives (3 with a target), 26
quest-people lines, 963 talk lines. Findings: A 30 bugs (29 CONFIRMED, 1 PLAUSIBLE: A29; PLAUSIBLE sub-points are marked inside A6, A11, A16, A23), B 29
repetition clusters, C 11 hygiene actions, D text for 5 skills and 3 docs, E 20 checks.

---

## A. Bugs in what the player reads or hears (most severe first)

### A1. The main quest cannot go on for a player who refused the oath; and anyone who steps out of the Reed's house at MQ03 stage 20 is locked out. CONFIRMED (for the engine reviewer too)
- Evidence: the house's outside door `0FE95A` is built `Lock: Level 255, Key 000E78` (`plugin/Argonia/Worldspaces/BlackMarsh - 23D689_Black Marsh.esm/RecordData.yaml:2061-2073`; `MainQuest.cs:574-577`). The key is given only in `ARG_QF_MQ03.psc` Fragment_90 (line 138). No MQ04 or MQ05 script touches the door. Ending 91 says "The house's door is not mine". MQ05 stage 10 then says "I'm to take what I found back to Nesh-Deeka at the fish-trader's house in Lilmoth", and her topic is gated to her ref inside that house (`ARG_MQ05_WordTopic`, `GetIsReference 000E89`).
- Player: unsworn, finishes MQ04, walks to the house, the door needs a key that does not exist for them. Sworn or not, a player who leaves the house during stage 20 (the inner door `0FE832` is not locked) cannot get back to Nesh-Deeka or Ties.
- Fix: unlock `0FE95A` in MQ03 Fragment_20 and leave it unlocked for both endings (the sworn ending keeps the key as the token of the safehouse). Journal 91 (`quest_stage` quest.main.mq03 id 91): replace "The house's door is not mine, but the Reed will send for me when it has work, and pay for it." with "I have no place in the Reed's house, but Nesh-Deeka will send for me when the Reed has work, and pay for it."

### A2. MQ03 stage 20 has a gate a new character can fail with no way left. CONFIRMED
- Evidence: `ARG_MQ03_TakeOath` and `ARG_MQ03_RefuseOath` need `ARG_MQ03_NightTold == 1`; Ties sets it only with the courier's tag or Speech 25 (`ARG_MQ03_TheNight` INFOs 000EAA to 000EAF). The tag is at the camp; the player has been moved to Lilmoth (Fragment_20). An Argonian starts with Speech 15. A player who took the phial (not the tag) is stuck; with A1 they cannot even go back for the tag and return.
- The refusal (INFO 000EB0, `quest_lines/mq03.json` topic.mq03-the-night variant `low`, default lines) says only "Give me a reason." and names nothing the player can do.
- Fix: (1) take `NightTold` off both oath topics' conditions (Ties's account becomes the optional objective it reads as: "Get Ties-The-Loose-Plank to tell the night too"); (2) default refusal text: "I saw the camp that night. I do not tell strangers what I saw. Bring me something of the courier's, or find better words."

### A3. Nesh-Deeka asks the player four questions with no reply, about jars the player never saw. CONFIRMED (the verified 9.5 fault again)
- Evidence: `ARG_MQ03_TheAttack`, all six INFOs (000EA2 to 000EA7; `quest_lines/mq03.json` topic.mq03-the-attack, both variants, three bands): "Did you see jars at the camp? Think carefully." and "Tell me about the jars once more. How many ring-marks did you see?" have no `LinkTo`. `MainQuest.cs` places no jar at the MQ01 camp (the only "jar" is the name of an enable parent for sap, trap and picks).
- Fix (default band, phial carried): "Sit. I have heard the others. Now I have heard you." / "You are carrying a phial of the sap. Give it to me. I want to look at it." / "The Reed has word of a cell. It cuts a Hist's roots and draws off the sap. Your camp is the first work of it that the Reed has seen." / "The courier's satchel was mine to see carried. I say no more of it." No-phial variant: second line "You took nothing from the shed. Then I have only your word. I will take it." Drop "The roll burnt in the camp's fire..." here (she says it again in `TheOffer`, cluster B6).

### A4. Nesh-Deeka makes her own agent pass Speech 25 or pay 40 gold to be given the main quest's next task. CONFIRMED
- Evidence: `ARG_MQ05_WordTopic` INFOs 000EC2 to 000ECA. Fallback: "I have a task, and I will not hand it to a stranger... Or give me forty gold as a gift"; cool: "I do not know you." This follows MQ03 ending 90 ("I have your word", stipend, key) and MQ04. The prompt is the bare word "Helstrom", a place the player has not heard of.
- Also in this topic: the default pass (000EC4, 000EC7) never names Kaska-Meen or Ei-Tuja (only the warm band does); the warm band (000EC2, 000EC5) ends "The Reed's house is the fish-trader's, Salts-The-Catch's, on the stilts of Lilmoth's channel. Its back room is behind the screen", said to the player standing in that back room, about a screen that was cut.
- Fix: one ungated line at stage 10 that sets 20, no gold and no Speech INFO, no fallback. Prompt: "I saw the cut root at Low-Reed Village." Lines: "Then take what you saw to Helstrom, and tell it plainly." / "The Reed wants Helstrom's tree-minders and Nisswo to hear what a cut Hist looks like, from someone we can deny." / "Kaska-Meen, a tree-minder, keeps her watch in the grove behind the Hall of the Scalded Throne. Ei-Tuja, a Nisswo, stands at the root's foot there. Tell either of them." / "Never name the Reed in Helstrom. I will not go with you." / "Board the coast ship at Lilmoth and leave it by its door for Helstrom's landing. From the landing the way in is north-east, root and shallows." Remove the `persuade` and `gift` actions from the record's stage 10 (quest-write rule D1.3 below makes a hand-out exempt).

### A5. Givers keep giving the quest after it has ended. CONFIRMED
- Evidence: "repeat" INFOs with a lower stage bound only: `ARG_BC01_TheEstate` 000CF1 to 000CF3 (`GetStage >= 10`: after 90, 91 and 94 Never-Sold still says "I will meet you there... Bring me the book"); `ARG_BC02_TheFire` 000D29 to 000D2B (`>= 20`: after the ending "is burning... Three are bound inside"); `ARG_BC03_LastSeason` 000D68 to 000D6A and `ARG_BC03_TheSeason` 000D6D to 000D6F (`>= 10`, the latter re-runs its fragment); `ARG_MQ04_CutTopic` 000DCC to 000DCE (`>= 40`: after 91 Pays-Late still "goes down to the cut root after dark to wash it"); `ARG_MQ05_QuarrelTopic` and `WatchTopic` (`>= 40`: after 91 or 92 they still argue what the player settled).
- Fix: add `GetStage < first ending stage` to each (BC01 < 90, BC02 < 91, BC03 < 90, MQ04 < 91, MQ05 < 91).

### A6. BC02's freed captive still speaks of "the keep". CONFIRMED
- Evidence: `ARG_BC02_AfterHello` 000D53 "Two did not leave the keep", 000D55 "You brought me out of the keep", 000D57 "the way you took me out of the keep", 000D5A "I am free of the keep because of you" (`story/data/dialogue-writer/quest/bc02/*.after.tsv` and the after-greeting entries of `quest_lines/bc02.json`). The quest was re-hosted to the stone house.
- Fix: "the keep" becomes "the stone house" in all four. 000D52 and 000D56 say "past the gate": PLAUSIBLE stale too (Tsaxi "stands outside the west wall"); write "past Tsaxi".

### A7. Rows-For-Another's greeting is wrong for the book ending. CONFIRMED
- Evidence: `ARG_BC01_AfterHello` 000D07 to 000D09 play on stage 90 OR 91: "I remember who took me past them", "I left the landing with my life". At 90 the player brought a book and never took her anywhere.
- Fix: gate these three to 91; add for 90 (`rows-for-another.after.tsv`): "Never-Sold tore my page out of the book. I remember who carried it." / "Eleven years on four months. It is ended, and you ended it."

### A8. Band lines that refuse while their fragment moves the quest on. CONFIRMED
- `ARG_BC03_TheTokens` 000D73 (cool) sets stage 20 and says "Earn my trust. Then I will tell you what Ussa-Rekh holds of ours"; the journal then tells the player to take the tokens nobody mentioned. Fix: "Ussa-Rekh keeps our carved tokens in the chest beside him. A crew who break their tokens before him are done with him. He said so himself."
- `ARG_MQ05_TellMinderTopic` 000DF7 (cool) sets ending 91 and says "I will not promise to carry your words anywhere. Come back when I know your face"; journal 91 says "She heard me out and will carry it". Fix: "I heard you. A silence and a cut are two things. I will carry it. I do not thank you for it."
- `ARG_BC03_TheSeason` 000D6E (cool) sets `SeasonHeard` and says "That is all I say to one I do not know"; it drops the tokens the default band names. Fix: give it the default's facts, shorter.
- Lines that promise more "when I know you" or "earn my regard" with no way to earn it: `ARG_BC01_TheBook` 000CF7, `ARG_MQ05_QuarrelTopic` 000DED, `ARG_MQ05_WatchTopic` 000DF2, `ARG_MQ04_BoatTopic` 000DC5. Fix: cut the promise sentence from each.
- Reach: ranks are set only at endings (`ARG_QF_BC03` 42, 58, 74; `LQ30` 52, 53; `LQ25` 38, 39, 55; `TG01` 54, 66; `TG02` 28, 43, 127, 135). Every banded line of MQ03, MQ04, MQ05, BC01, BC02 and the opening lines of the rest is spoken at rank 0, so its warm and cool copies never play: see C8.

### A9. Kaska-Meen calls Ei-Tuja "her". CONFIRMED
- Evidence: Ei-Tuja is male (`npc` row `npc.hist-heartland.helstrom.nisswo-interpreter-debating-house`, template `00FF4D` male; journal 92 "He gave his reading"). `ARG_MQ05_WatchTopic` 000DF2: "...you can speak to him there. Speak to her."; 000DF3: "The Nisswo Ei-Tuja stands at the root's foot, but she is not of Helstrom." (`dialogue_line` rows of topic.mq05-the-watch, `variants_low` and words).
- Fix: 000DF2 drop "Speak to her."; 000DF3 "but he is not of Helstrom".

### A10. Lines and journals describe things that were cut from the build. CONFIRMED
- MQ03 stage 20 journal: "In the back room, behind a screen, a woman..." (the screen was cut; phase file "Cut: ... the screen"). Fix: "In the back room a woman who calls herself Nesh-Deeka sits by the mats".
- Sal-Sei after the strike (`quest_people.json` ARG_MQ01_SalSei, second entry): "The roots of the Hist cutting were cut before its light went out." (the cutting's light was cut). Fix: "I kept the clutch of eggs. The cutters cut the roots of the Hist cutting. The eggs are grey now."
- MQ03 stage 40 journal: "I stood in fog among a ring of trees whose roots climbed up and up... A dry voice spoke that I could not place. In the dream I walked to the door." Built: the empty barge hold with six thorn roots and a zone at its stair door (`MainQuest.cs:564-571`); no fog, no voice; and the entry says the walk is done while objective 40 asks for it. Fix: "I lay down on the mats in the house in Lilmoth with the camp's sap still on my tongue, and dreamed. I stood in the barge's hold again, empty now, with roots grown up through its deck, and the door at the top of the stairs stood where it had. I'm to walk to the door." Stage 90 and 91 keep "I walked to the door in the dream".
- MQ05 warm band, "Its back room is behind the screen": see A4.

### A11. MQ01's journal tells the walk in one entry, narrates a scene the game does not play, and the lines disagree on who reads the roll. CONFIRMED
- Stage 10 (`quest_stage` quest.main.mq01 id 10) tells stages 10, 20 and 30 at once. Fix: "I came to in the hold of a broker's barge at Lilmoth's dock, among an Owing gang. My line on the roll is blank. I'm to speak to Wuleen-Sei, the overseer, and answer her when she asks for my name."
- Stage 40 opens "As Wuleen-Sei read the roll at the camp's fire... naming Sal-Sei, keeper of the clutch, and Deesh-Duun aloud". Stage 40 is set the moment the player enters the fire zone (`ARG_QF_MQ01.psc` Fragment_40); nothing is read or named. Fix: "At the camp's fire a tall Argonian woman with a knotted cord at her wrist came in off the water with two of her people. She killed Mee-Tuja, the quiet man who walked with us, took his satchel, looked at me and left. His strap with a brass tag fell through the burnt boards into the deep water, and the roll went into the fire. Her two cutters are at the Hist cutting by the hatching shed, at the camp's north-east end, where Sal-Sei keeps the clutch. The huts over the water to the west are burning with Deesh-Duun inside. I'm to reach one of them; I cannot reach both."
- Who reads the roll: Wuleen-Sei (journal 10 and 40; her line "I have read your line") against Ux-Xeek ("I call the names in the hold every day"; Finds-The-Other-Bank "Be quiet while Ux-Xeek reads the roll"; Nesh-Neel "when Ux-Xeek reads the roll"; the record's role `roll-reader`). Fix, one reading everywhere: Ux-Xeek calls the names, Wuleen-Sei keeps the roll and asks the blank line's name. `mq01.json` topic.mq01-the-roll line 2: "Ux-Xeek called your line, and it has no name on it. What name do I write?"
- Wuleen-Sei's answer lines narrate what is not shown: "Ux-Xeek, who calls the names, laughed once and stopped." and "We all heard you in the hold." (said in the hold). Fix: defy "The gang heard you. Your line stays with no name on it."; name "Your line had no name on it, and now it has one."
- PLAUSIBLE, for the engine reviewer: `HoldParent` stays enabled until stage 40 and `MarchParent` is enabled at 10, so at stage 30 the hold's Wuleen-Sei and the pier's Wuleen-Sei both exist; journal 10's "follow Wuleen-Sei up the plank" is never seen.

### A12. Ux-Xeek hands over water that does not exist. CONFIRMED
- `ARG_MQ01_TheWater` 000E6B has no fragment: "Here is the day's water. Drink what you need and pass the cup to the next hand." The prompt is "Is that water for me?" with no water in sight.
- Fix (`mq01.json` topic.mq01-the-water): prompt "Who are you?"; lines "I am Ux-Xeek. I call the names in the hold every day, in order. I have never lost one." (drops her copy of the months-for-food fact).

### A13. The Reed's second stranger speaks as if he were in Lilmoth. CONFIRMED
- `quest_people.json` ARG_MQ03_ReedStranger: "If you were at the Hereguard camp, a person in Lilmoth wants to hear about it." He stands on the camp's shore (`MainQuest.cs:550`).
- Fix: "You do not know me. We take the hurt to Lilmoth by boat. Speak to the one beside me when you are ready to go."

### A14. MQ03 stage 10's objectives do not say how. CONFIRMED
- Objective 10 "take a phial of the spilled sap, if I know the craft": the craft is Alchemy 25 (Fragment_11), never named; tasting, the step that is required (`GetStageDone 11`), has no objective; objective 10 is completed only on the phial path and stays open otherwise; none of the seven objectives has a target.
- Fix (`quest_objective` quest.main.mq03): "Taste the spilled sap on the floor of the hatching shed." (target the SpilledSap alias; completed at 11); "(Optional) Bottle a phial of the sap (Alchemy 25)."; "Dive under the burnt boards by the fire, pick the lock of the sunk fish-trap and take Mee-Tuja's brass tag." (target FishTrap); "Tell the stranger on the shore you are ready to go." (target NeverWritesTwice). Stage 20: targets Nesh-Deeka, Ties, Nesh-Deeka. Stage 40: target the door zone.

### A15. MQ04 and MQ05's prompts are bare topic labels. CONFIRMED
- Built prompts: "the tree", "the boat", "the cut", "Helstrom", "the basin", "the silent Hist", "the watch", "what I saw" (twice). They are the `topic.label` values (`topic.jsonl` 208-216); every other quest uses a sentence.
- Fix: "the tree" to "May I see the Hist?"; "the boat" to "Did you see who came to the tree?"; "the cut" at 30 to "This is your gum pot. Who cut the root?" and at 40 to "Tell me about the cut root again."; "the basin" to "What is the warning at this gate?"; "the silent Hist" to "What do you and Kaska-Meen quarrel over?"; "the watch" to "What is your watch here?"; "what I saw" to "I saw a Hist cut at the root. It is not the same as a silent one."; "Helstrom": see A4.

### A16. Prompts that say what the player cannot yet know. CONFIRMED
- `ARG_BC01_TheEstate` at stage 0: "Who is Rows-For-Another?" (never named before). Fix: "What do the Chainbreakers need done?"
- `ARG_BC02_TheFire` at stage 0: "What is burning at Blackrose's east edge?" (the smoke is enabled by this line's own stage 20). Fix: "Is there more to do?"
- `ARG_TG01_TopicTest` at stage 0: "S'Tabi sent me about the Chapter." with no condition that S'Tabi was heard, and S'Tabi never says "Chapter". Fix: "I hear you have a use for careful hands."
- `ARG_MQ01_TheMarch`: "What have the years away cost you?" Fix: "Why is your colour so thin?"
- PLAUSIBLE: `ARG_TG02_TopicSellBeads` "These beads are Kothringi glass from the old cairns." needs the item or a line to tell the player so first (not found in the lines read).

### A17. Payments and checks the player cannot see; gated topics with no fallback. CONFIRMED
- `ARG_TG01_TopicBed`: one prompt "Where does Keeps-What-Floats sleep?" serves Speech 25 and a 10-gold payment ("That is a good drink, thank you"); the gold goes without being offered. Same in `ARG_TG01_TopicGiveBack` (Speech 35 or 60 gold) and `ARG_TG02_TopicClaimCharm` (Speech 30 or 20 gold).
- No fallback INFO, so the topic is simply absent when the player fails: TG01 Bed, GiveBack; TG02 ClaimCharm, SellBeads, SellCharm, SellFigurine. Okan-Tei's claim is required for TG02 stage 40; a player with Speech under 30 and under 20 gold (TG01's no-pay path) sees nothing to say to him.
- The two GiveBack routes contradict: "I could not sell it anyway" (Speech) against "I had a buyer for this, you know" (gold).
- Fix: separate topics per route with the route in the prompt, Skyrim's way: "(Persuade) Where does Keeps-What-Floats sleep?" and "Let me buy you a drink. (10 gold)"; a fallback INFO per gated topic that names what is needed (Sits-By-The-Water: "My cup is empty and you are a stranger. Buy me a drink and I may remember."; Okan-Tei: "Why would I tell a diver what is mine? Talk sense to me, or make it worth my while with twenty gold."). GiveBack gold line: "Sixty gold. I could not sell it anyway. Here, it is yours."

### A18. Garbled sentences. CONFIRMED
- `ARG_MQ04_CutTopic` 000DCB and 000DCE (default band; `dialogue_line` topic.mq04-the-cut): "The black gum is the gum the workshop where the village works sap works, and the knife-peg by its door is empty." Fix: "The black gum is the gum the village's sap-workshop works, and the knife-peg by its door is empty."
- `ARG_LQ25_TellCaptain` 000C49: "This proves it did not." Fix: "This proves it was not."
- `ARG_LQ25_KeepQuiet` 000C4D, 000C4E: "to fake a beast" (the beast is real; journal 40 "the crew's offal drew the beast"). Fix: "to draw a beast".
- BC03 stage 90 journal: "he will hire neither of them again" (no two). Fix: "he will not hire them again."
- TG01 objective 20: "or get it out of his drinking friend" ("it" has no noun). Fix: "Follow Keeps-What-Floats on Soulrest's dock to his bed, or ask Sits-By-The-Water where he sleeps."

### A19. Rows-For-Another says "Not in daylight" at night. CONFIRMED
- `ARG_BC01_CutLoose` 000CFE to 000D00 are the fallback for both "it is day" and "it is night but an estate man can see the player". Fix: "Not while the estate's men can see us. Come to me after dark, when none of them is looking."

### A20. Journals name people by a role the game never shows. CONFIRMED
- LQ25 stage 40, 91, 92, 93 and objective 40: "the boat captain"; the person is the talker Sells-Dear (`08D5F1`, phase 4a). LQ30 stage 30 and MQ05: "the levy warden", "the warden at the gate"; he is Gih-Xaleel (`08D5E9`). MQ04 stage 10 and objective 10: "the root-herald" (give her name with the role, as the base carries it).
- Fix: "Sells-Dear, the boat captain, who stands at Helstrom's north edge west of the levy's gate"; "Gih-Xaleel, the levy warden".
- LQ30 objective 30 tells what journal 30 leaves to find: "Kill the viper that keeps Sei-Wan pinned among the roots". Fix: "Find Sei-Wan in the shallows east of Helstrom's basin gate."

### A21. "Four hours ago" whenever the player arrives. CONFIRMED
- `ARG_LQ30_WalkedOut` (six INFOs) and `ARG_LQ30_ComeBack` (three): "He walked out into the basin alone four hours ago." The quest is Start Game Enabled; the player may come days later. Fix: "He walked out into the basin alone and has not come back." / "I walked out alone, to prove myself to Helstrom's Agaceph."

### A22. Okan-Zish offers a crossing his own quest says nobody makes. CONFIRMED
- `talk_line` 08D5EE talk.self: "Give me the work and I will cross anything, any day. Now, are you crossing or not?" against `ARG_LQ25_TheBeast` (stage 0 from the first day): "Now no crew member will take a raft out." The question has no reply and no ferry exists.
- Fix: "I am Okan-Zish, an Agaceph rafter. I pole goods across this water with Wuleen-Taza, when the water lets us."

### A23. The same warden gives two different basin warnings at once. CONFIRMED
- `ARG_MQ05_BasinTopic` (MQ05 >= 20): "Anyone who walks into the basin round Helstrom dies there." `ARG_LQ30_TheBasin` (LQ30 == 30): "may die there". Both topics can be open together; MQ05's own road in is "root and shallows". PLAUSIBLE: "A warning is posted at the gate" (five speakers' lines) has no sign placed by `LocalQuests.cs` or `MQ05.cs`.
- Fix: MQ05's topic: "Hear me. Anyone who walks into the basin round Helstrom may die there. What lies in the reed roots bites. Keep to the marsh way." Remove the topic while LQ30 is at 30.

### A24. MQ05's journal: engine words and a stray paragraph. CONFIRMED
- Stage 20: "I'm to take the coast ship at Lilmoth's stop: one of its doors opens on Helstrom's river landing." Fix: "I'm to board the coast ship at Lilmoth and leave it by its door for Helstrom's landing."
- Stage 40 ends with "The Hall of the Scalded Throne, by the first street on the left inside the gate, has a plain seat of root and reed, with no dais, swept with a broom, and people sell goods in the room before it.": nothing the player is asked to do. Fix: delete the sentence.

### A25. Nobody sends the player to Low-Reed Village. CONFIRMED
- MQ03's endings set MQ04 to 10 from a script; no line of Nesh-Deeka's names the village. Journal 10 opens "The Reed sent me east of Lilmoth to Low-Reed Village", also on the unsworn path.
- Fix: add to both `topic.mq03-take-oath` and `topic.mq03-refuse-oath` a last line: "The first work is this. East of Lilmoth, at Low-Reed Village, a Hist has shut. Go and see why." Objective 10 gets a target on the root-herald.

### A26. Forty-two objectives, three markers; three voices. CONFIRMED
- Only MQ01 10, 20, 30 have targets. The owner passed that shape in walk 5 ("Good now up to the point after you leave the hold. Update the skills"); the other ten quests and MQ01 40 to 42 were not brought to it.
- Voice: MQ01 "answer her when she reads your blank line"; MQ03, MQ05, BC02 "tell the stranger on the shore I am ready"; TG01, TG02 without full stops. Fix: imperative, no pronoun for the player, a full stop (Skyrim's own form), and a target alias on each (person, door, container or marker).

### A27. No greeting after the ending for most people left standing. CONFIRMED
- Built: Rows-For-Another, BC02's freed one, Sei-Wan. Missing: Never-Sold (BC01, BC02), Heavy-Rope and Ussa-Rekh (BC03), Tilts-The-Jug and Keeps-What-Floats (TG01), the three clients (TG02 91: "none of them will greet me kindly again"), Sells-Dear and Wuleen-Taza (LQ25), Haj-Wan (LQ30), the root-herald, Pays-Late and Turns-The-Clutch (MQ04 91: "The villagers have taken me in"), Kaska-Meen and Ei-Tuja (MQ05), Nesh-Deeka (MQ03).
- Fix: one or two Hello lines each, gated on the ending stage, written through dialogue-write.

### A28. The gate-keeper asks and answers himself, against Tsaxi. CONFIRMED
- `quest_people.json` ARG_BC02_GateKeeper: "Only those with their word may go in. Do you have it? Then go." Tsaxi, beside him, refuses entry. Fix: "I keep this gate for the heirs. The stone house is their outer post. Third-Born Tsaxi says who goes in. Speak to him."

### A29. Topic order decides the outcome where INFOs are not exclusive. PLAUSIBLE (for the engine reviewer: read the ESP's INFO order)
- `ARG_MQ03_TheBoat`: "ready" (000E9A to 000E9C) and "where" (000E9D to 000E9F) can both pass; `ARG_MQ04_VillageTopic`: the fallback (000DBC to 000DBE) has no "Speech < 25 and salt < 2"; `ARG_BC01_CutLoose`: the day fallback has no "not night". The phase file says Spriggit's YAML does not keep INFO order. If a fallback sorts first, the pass line never plays.

### A30. LQ25's record gate is not in the build. CONFIRMED
- `LocalQuests.cs:308` and the phase file say Okan-Zish's topic opens "once MQ05 is at 40"; `ARG_LQ25_TheBeast` 000C3F to 000C41 carry `GetStage(ARG_LQ25) == 0` only. Decide once: drop the gate from the record and the comment (a local quest with a rumour needs none), or build it.

---

## B. Repetition clusters (for the dialogue-write lane)

Each: the space, the speakers, the fact, who keeps it. "Journal" means the entry repeats it too.

| # | Space and stage | Speakers | Repeated fact | Keep with |
|---|---|---|---|---|
| 1 | Hold and pier, MQ01 10-30 | Wuleen-Sei, Buys-The-Months, Ux-Xeek, Ri'Sakka, Llarvi Maryon; journal 10 | months are added for food (the owner's case) | Wuleen-Sei |
| 2 | Hold, pier, camp, MQ01 10-40 | Wuleen-Sei, Buys-The-Months, Ux-Xeek, Finds-The-Other-Bank, Ri'Sakka, Tsanji, Llarvi, Deesh-Duun, Nesh-Neel | "I owe / every hand owes months to the broker, like you" | Buys-The-Months (he holds them) |
| 3 | Hold, pier, march | Buys ("Walk with the gang"), Tsanji ("Stay close to the gang"), Wuleen-Sei march ("Keep up with the gang"), Finds march ("Stay with the gang on the path") | stay with the gang | Wuleen-Sei (march) |
| 4 | Hold, pier, march | Wuleen-Sei's three answers, Buys, Dives-Without-A-Rope, Wuleen-Sei march, Finds march, Mee-Tuja; journal 10, 20, 30; objective 30 | where the camp is (shore path, Hereguard, "where the shore path meets the reeds") | Wuleen-Sei's answer; the objective |
| 5 | Hold and camp | Finds, Nesh-Neel, Cuts-The-Old-Knot | sit and be quiet for the roll | Finds |
| 6 | Camp after the strike; the Reed's house | Finds, Ri'Sakka, Llarvi; Nesh-Deeka in `TheAttack` and again in `TheOffer`; journal MQ01 90, 91, 93 and MQ03 20 | the roll burnt, nobody can show what is owed | Nesh-Deeka `TheOffer`; Llarvi at the camp |
| 7 | Camp after the strike; the house | Tsanji, Deesh-Duun, Ties; journal MQ01 40, 42, 91 | a tall woman with a knotted cord led them | Ties (his line is the tag's reward); Deesh-Duun when saved |
| 8 | Camp shore, MQ03 10 | the officer's "ready" and "where" lines, the second stranger | sent by a friend of the courier; the hurt go to a house in Lilmoth by boat | the officer's "Who sent you?" |
| 9 | The Reed's back room, MQ03 20 | Nesh-Deeka in `TheOffer`, `TakeOath`, `RefuseOath`; journal 90 | the protection, the door in Lilmoth and the stipend, listed three times in one talk | `TheOffer` |
| 10 | Low-Reed Village, MQ04 10-40 | root-herald (fail and pass lines), Turns-The-Clutch, Pays-Late; journal 30 | Pays-Late goes down to the roots after dark | root-herald |
| 11 | Low-Reed Village | Turns-The-Clutch, Pays-Late (>= 40); journal 30 | Turns-The-Clutch keeps the uxith by day | Turns-The-Clutch |
| 12 | Low-Reed Village | Pays-Late at 30 and again at >= 40 | gum, knife-peg, why he hid the cut, said twice in full | the stage-30 line; >= 40 keeps only the way to the camp |
| 13 | Low-Reed Village talk | Mends-The-Nets, Hulee-Tah (`talk.lore`) | a root-herald speaks for a village to outsiders: news, trade, terms | Mends-The-Nets |
| 14 | Helstrom's gate | Gih-Xaleel in `BasinTopic` and in `TheBasin`, Haj-Wan (opening and repeat) | who walks into the basin may die; a warning is posted | Gih-Xaleel, one topic |
| 15 | Helstrom's gate | Haj-Wan, Gih-Xaleel | the custom forbids our own to follow a walk-out; it does not bind an outsider | Haj-Wan |
| 16 | Helstrom talk | Hauls-Wet-Rope, Bejeen-Ul (`talk.rumours`) | the LQ30 rumour, one sentence word for word | either one |
| 17 | Helstrom's grove, MQ05 40 | Ei-Tuja in `QuarrelTopic` and `TellNisswoTopic` | "I give my reading freely and ask nothing for it" | `TellNisswoTopic` |
| 18 | Blackrose and the landing, BC01 | Never-Sold (`BringDown`), Hulm-Tei (`TheBook`) | every line of the book is true: food, the boat's upkeep, sick days | Hulm-Tei |
| 19 | The whole slice | Wuleen-Sei, Never-Sold, Hulm-Tei, Heavy-Rope, Ussa-Rekh; journal BC01 10; three Lilmoth talkers (`fact.lilmoth.lore.owing`); three Thorn talkers (`fact.thorn.01cce0.lore.extend`, which is cluster 1's fact again) | what an Owing is | the first speaker of each line: Wuleen-Sei, Never-Sold, Ussa-Rekh |
| 20 | Stone house, BC02 | Tsaxi in `TheGate` and again in `LetBy`; journal 30 | the way out bears one trip; whoever is left dies; the heirs lost nothing worth fetching | `TheGate` |
| 21 | Blackrose talk | Ree-Shaal, Sleeps-Standing | smoke; "People are shut inside it, and Third-Born Tsaxi keeps the door" | Ree-Shaal |
| 22 | Blackrose talk | Talks-To-Water, Mends-The-Hulls, Pays-In-Reeds | the BC01 rumour, one sentence nearly word for word | one speaker; the others get a different lead |
| 23 | Soulrest's dock, BC03 | Heavy-Rope (`LastSeason`, `Brawl`), Ussa-Rekh (`TheSeason`), Seeks-The-Channel, Feldril Nethri; journal 10, 90, 91, 92, 94 | the crew asked to end the last season early and was refused | Heavy-Rope |
| 24 | Soulrest's dock, BC03 | Heavy-Rope, Ussa-Rekh; five journal entries | he bought out Owings for thirty years, freed the crews, now hires them out | Ussa-Rekh |
| 25 | Soulrest's dock, BC03 | Heavy-Rope in `TheTokens` and `Break`; journal 20, 90 | tokens in the chest; a crew who break them before him are done with him | `TheTokens` |
| 26 | Soulrest's dock, TG01 | S'Tabi, Plaits-The-Reed, Xeeh-Nah | Tilts-The-Jug in the house on the dock has use for careful hands | S'Tabi and one talker |
| 27 | Helstrom's landing, LQ25 | Counts-Every-Crate, Azum-Kai | the LQ25 rumour, one sentence nearly word for word | one |
| 28 | Blackrose, Thorn, Low-Reed talk | 18 of Blackrose's 38, 5 at Thorn, 4 at Low-Reed | the friend greeting opens "You came back, my friend" or "You are back, my friend" | each person's own opening |
| 29 | Thorn talk | 6 to 7 soldiers | "a soldier of the hired Imperial company" as self-description | two; the rest say their post |

Clusters 16, 21, 22, 26, 27 share one cause: the rumour fact's `claim` is a finished sentence and each writer copies it.
The journal repeats (4, 6, 23, 24) come from the style guide's "each entry re-summarises the chain from its start".

---

## C. Data hygiene actions

1. **One shape for lines: `dialogue_line` rows in the story database.** Today: `story/data/quest_lines/*.json` (MQ01, MQ03, BC01-03, LQ25, LQ30, quest_people), `dialogue_line` rows (MQ04, MQ05; 2,290 rows, most `imported` reference), `story/data/dialogue-writer/quest/tg/nightreed.lines.tsv` with fallback strings in `NightReed.cs:400-416`, and the writers' `*.lines.tsv`, `*.bands.tsv`, `*.after.tsv` (136 tracked files with the generated briefs). The skills already call the database the one source (quest-write line 11). Give `dialogue_line` the columns the builders need (`prompt`, `band`, `stage_lo`, `stage_hi`, `check`, `sets`, `kind` of `topic|hello|who`), import the JSON and TSV once, point `MainQuest.LinesOf`, `LocalQuests.Lines`, `NightReed.WrittenPath` and `Talk.QuestPeople` at `QuestKit`'s row reader, then delete `story/data/quest_lines/`, `nightreed.lines.tsv`, every `*.tsv` and brief under `story/data/dialogue-writer/quest/`, and the string literals in `NightReed.cs`. Briefs are generated: never committed.
2. **Prompts live on the line row**, not in `topic.label` (the Morrowind label; cause of A15) and not in C#.
3. **TG journal text is duplicated in `NightReed.cs:379-380`** beside the `quest_stage` rows (all 11 quests' built entries equal their rows today). Delete the literals; the builder reads the rows.
4. **The record does not hold what was built:** hidden stages (MQ01 35; MQ03 11, 45; TG02 21-23, 43-45) have no `quest_stage` row; objective targets have no column (`quest_objective` has none; MQ01's are in `MainQuest.cs:446`). Add `hidden` stage rows and `quest_objective.target`.
5. **Stale rows to rewrite to the build:** `world_edit` we.mq03.dream (fog, a scene), we.mq03.rooms (the screen), we.mq05.people ("quarrelling in the evening"), we.bc02.mesh, we.bc02.name, we.door.rose-jail (the old host; the phase file lists them); `quest` quest.bc.bc02 (`01cyKeep`); `quest_adaptation` bc02 ("cells", Black Rose Jail) and mq03 (fog, a voice, behind a screen); `quest_review_finding` bc02 L6; `quest_host` mq03 ord 2 (fog); `quest_thing` thing.mq03.dream; `quest_shape_data` mq03 image; `quest_truth` mq03 t3, `quest_action` and `quest_action_plan` mq03 ("behind a screen"); we.lq30.trail, we.lq25.beast, we.lq25.crew (pre-B1 wording, phase file).
6. **`docs/design/blocks.md` lines 142-195** (the generated stage table) describes superseded builds: MQ01 10 "the new-game start (ARG_Opening)... E-scene", "BC01 the hearing... cut the boat loose", BC02 "cells... the book", BC03 "barge, shelf". Re-run `slice_ledger.stage_blocks` after action 5, or delete the table. Row E-stage says "objective, no target": merge E-target into it.
7. **`docs/phases/4-first-act-built.md`:** the status line still says the walk is owed; the open items "LQ25's MQ05 >= 40 gate" and "the freed one's after-state greeting is not built" are stale (A30; the greeting is built). PLAUSIBLE: the table row "The ship stop in Black Marsh North (thorn1), visited by MQ05, 33 talkers" is the ship interior's census tag; MQ05 leaves the ship at BlackMarsh2 -10,12 (`bmv_door` 0830A8), not at Thorn (27274, 64170 in worldspace 005900).
8. **Band copies nobody can hear:** 160 of 264 quest INFOs are warm or cool copies; ranks change only at endings (A8). Delete the bands of every line spoken before its speaker's rank can differ from 0 (all of MQ03, MQ04, MQ05, BC01, BC02, TG01; the opening lines of BC03, LQ25, LQ30, TG02) and keep bands only on lines after a rank change.
9. **`bans.yaml` has two ids B11** (`B11-warm-address`, `B11-macro`); rename the second B12 and update talk-write's "lint B11".
10. **`quest-write/quest-record.md` §3** maps fields to "generator chunks 1.4, 2.12, ArgoniaCore", a build that does not exist; §5 "what 2.5 and 2.12 must add" likewise. Replace §3 with the table in D2; delete §5 and the "Needs a decision" table.
11. **`docs/skill-fixes.md`:** delete the four verified rows (9.2, 9.4, 9.5, 9.1 and 9.3) in the commit that lands D.

---

## D. Skills and docs: text to paste

### D0. The four verified rows, generalised

| Row | The class of mistake | Where the rule goes |
|---|---|---|
| 9.2 stages with markers | A step the player must take that has no stage, entry, objective or pointer of its own | quest-write §3 item 4 (D1.1); quest-record stage and objective fields (D2); quest-review item 8 (D3); quests-on-a-world part 7 (D7) |
| 9.4 quest people have lines | A person the player can walk up to who was outside the pipeline that gives people lines | talk-write (D5.1); quest-write §6 item 11 (D1.5) |
| 9.5 unanswerable question | A line that asks or offers what the game gives the player no way to answer, take or see | dialogue-write §4 (D4.2); text-review step 1 (D6); lint (E3) |
| 9.1 and 9.3 doors and SEQ | A thing that looks usable and is not; state that exists only after a load | already in quests-on-a-world parts 4 and 8, which read clean; add one line to quest-write §4 (D1.4) and quest-review (g) (D3) |

### D1. `.claude/skills/quest-write/SKILL.md`

D1.1 Replace §3 item 4 ("Plain next steps") with:

> 4. **One step, one stage.** Each thing the player must do next (speak to someone, leave a room, follow, reach a
>    place, fetch, choose, return) is its own stage with a journal entry, one objective and the objective's target: the
>    person, door, container or marker to go to (`objectives[].target`, an id from `cast`, `things` or the place's
>    refs). The entry tells this step only: what just happened in one or two sentences, then "I'm to ..." with the
>    place by a name the player can see. It never tells a later step, and never tells an event the build does not
>    show the player. Objectives are imperatives with a full stop and no "I" or "you" ("Speak to Wuleen-Sei in the
>    barge's hold."). A requirement the player must meet is in the objective with its number ("(Alchemy 25)").

D1.2 Add to §3, after item 3:

> 3b. **The critical path is never closed to a new character.** A line that hands out the next task, or takes a
>     report, has no check on it. Where a stage on the only way forward has a check, a second route needs no skill
>     level and no gold, is open at the place the player then stands, and the refusal line names it. Before hand-on,
>     walk the quest as a new character (every skill at its racial start, no gold): every stage must have a way on.

D1.3 In §3 item 3, after "a pure choice stage and an ending are exempt" add: "; so is a stage whose only act is hearing
the task or reporting back".

D1.4 Add to §4, "Places, people and things":

> - The player can get to every person and place a stage names, by every path that reaches that stage: a locked door
>   on the way has its key or its unlock on each path, both directions.
> - Everything the record says is at a place (a jar, a sign, a screen, a trail of bent reeds) is a `things` row the
>   build places, or it is not said. When a host, prop or scene is cut or moved, search the quest's rows and lines for
>   its nouns and change every hit in the same commit.

D1.5 Replace §6 item 11 ("Topics") with:

> 11. **Topics**: `topic.` ids; per person and stage window (first and last stage, the last before the first ending
>     unless it is an after-quest greeting), the prompt, the intent, the facts it may state and hide, what it sets.
>     - The prompt is a sentence the player would say, using only names and facts the player has at that stage; the
>       opening prompt of a quest names nothing the giver has yet to tell.
>     - A route that costs gold or checks a skill is its own topic with the cost in the prompt ("(Persuade) ...",
>       "... (10 gold)") and a fallback line that names what is needed.
>     - A question the speaker asks is a choice: one answer topic per reply. Otherwise the speaker tells.
>     - Every cast member the build places has at least a "Who are you?" line per stage window in which the player can
>       reach them, true of where they stand then.
>     - Everyone an ending leaves standing has a greeting for that ending.
>     - Within one place and stage window a fact is given to one speaker; the others get a different fact.
>     - Warm and cool wordings are written only for lines spoken after a fragment has changed that speaker's regard.

D1.6 Remove as history or dead reference: "(old 0145)", "(old 0137)", "(40-factions §30b)" where it only cites; in
`quest-record.md` the phrases "the consumers named here are the old plan's generator chunks", "2.5 adds it", "for 2.4
to write back".

### D2. `.claude/skills/quest-write/quest-record.md`

Stage table, replace the `objectives` and `directions` rows and add `hidden`:

> | `objectives` | `{id, text, target, completeWhen}`; + `objectiveText`: an imperative with a full stop; `target`: the cast, thing or ref id the compass marker points at (`none` only for a choice between several) |
> | `hidden` | `true` for a stage the build needs and the player never reads (a zone that moves people, one part of an "all of"); it has no journal or objective |
> | + `directions` | how the player finds the place in words (landmark, direction, distance), written into the journal entry beside the objective's target |

Replace §4 "Journal rules":

> Journal text follows the style guide's `journal` register: first person, past tense for what happened, "I'm to ..."
> for the one step now owed; full names and place names as the game shows them (a person by the name their base
> carries, with the role beside it at first mention). One entry per stage, this step only, two to four sentences. An
> ending's entry may sum up the quest. A failure has its own flat entry with its consequence.

Replace §3 (the engine mapping) with a table of the built shapes only: stage to QUST stage and log entry; objective
and target to QOBJ and QSTA on a forced-ref alias; topic line to DIAL/INFO with GetIsID or GetIsReference, the stage
window and the check; `sets` to the INFO's fragment; choice to linked topics in the question's branch; greeting to a
Hello topic gated on the ending stage. Delete §5 and "Needs a decision" (C10).

(The style guide's "Deliberate redundancy: each entry re-summarises the chain from its start" in
`story/design/text/style-guide.md` § journal contradicts this and must be changed with it to "An ending's entry sums
up the quest; other entries tell their own step.")

### D3. `.claude/skills/quest-review/SKILL.md`

Blocking list: extend (a) to "a path the player cannot finish, a stage that cannot be left, or a stage on the only way
forward that a new character (skills at racial start, no gold) cannot pass"; extend (g) with "a person or place the
player cannot reach on some path into the stage (a locked door without its key on that path)".

Replace checklist items 8 and 11 and add 8b to 8f under "Play":

> 8. Is each thing the player must do next its own stage, with an entry that tells that step only, one objective and a
>    target? Can the step also be followed from the entry's words alone (landmark, direction, distance)?
> 8b. Does any entry, objective or topic intent tell something the build does not show or place (a scene with no
>     lines, a prop not in `things`, a host that was replaced)?
> 8c. Can the player say each prompt with what they know at that stage? Does every question a speaker asks have reply
>     topics? Does every offer ("here is", "take this", "I will follow") have the action that delivers it?
> 8d. Does every topic have a last stage, and does anyone still offer or describe the task after an ending?
> 8e. Is any fact given to two speakers in one place and stage window?
> 8f. Does each ending leave its people a greeting that is true of that ending and no other?
> 11. Does every `journalText` follow the journal register (first person, "I'm to" for one step, names as the game
>     shows them, failure entries flat) and every `objectiveText` the objective form (imperative, full stop, its
>     requirement in numbers)?

In §1, "Run as a fresh agent given only the quest record..." add: "For a quest already built, read the built quest and
topics as well (`plugin/Argonia/Quests`, `DialogTopics`) and report any difference from the record as blocking (b)."

### D4. `.claude/skills/dialogue-write/SKILL.md`

D4.1 Delete "Every rule here came from an owner correction; add new bans to `bans.yaml`, new voice evidence to
`voices.md`." (history) and write: "Bans are in `bans.yaml`, voice evidence in `voices.md`." Change the description's
"Morrowind-style topic dialogue" to "topic dialogue in Morrowind's voice, built as Skyrim topics". Delete "(1.3's
three, by disposition)", "(old 0145)", "(decision 0024 §7)".

D4.2 Replace §4's first two bullets (Bands, Essential topics) and add the rules the slice broke:

> - **A line tells; a question is a choice.** A speaker asks the player something ("What name?", "Did you see?", "Give
>   me a reason", "Are you crossing?") only when the brief lists the reply topics. With none, the speaker says what
>   they know or what they need, as a statement.
> - **A line promises only what the brief's `sets` delivers.** "Here is", "take", "I will follow", "I will meet you
>   there", "come back when I know you" are written only where the brief names the item given, the package, the place
>   or the way to earn it.
> - **A line is true wherever its window lets it be said.** The brief gives each line's place, first and last stage and
>   conditions. Write nothing that is false at the window's far end, in the fallback's other cases (a "not now" line
>   covers every reason the pass line failed), or once the clock moves ("four hours ago").
> - **The prompt is the player's sentence.** A full sentence the player would say with what the brief lists under
>   "the player already knows"; a cost or check is in it ("(Persuade)", "(10 gold)").
> - **People by the name the game shows.** A person the player can meet is named as their base is named, with the role
>   beside it once; pronouns follow the brief's sex for that person.
> - **One speaker, one fact, per place.** The brief lists what the others in the same place and stage window say. Do
>   not restate it; give this speaker's own fact or their view of it in one clause.
> - **Wordings by regard.** The default wording is written for every line. A warm (regard 1 or more) and a cool (below
>   0) wording are written only where the brief marks the line "after a regard change". All three wordings state the
>   same facts and make the same commitment as the line's `sets`; only manner and length differ.
> - **A refusal says what would change it** (B09): the skill, the thing to bring or the price.

D4.3 §2, replace "greet by `[player rank]`" with "greet by the rank's name written out" (the same section bans macros).

D4.4 `brief.py` must supply what D4.2 reads: per topic the place, stage window, conditions, `sets`, reply topics, the
co-located speakers' facts, the person's sex and shown name, and "after a regard change". (The other lane owns the
co-location part.)

### D5. `.claude/skills/talk-write/SKILL.md`

D5.1 Replace the first paragraph's second sentence ("The four rules below are the owner's (walk 3, 2026-11-08);
`talk_check` enforces each.") with "`talk_check` enforces each rule." and the description's "(Phase 4a's recipe v2)"
with nothing. Add after the paragraph:

> **Who is covered.** Everyone the player can walk up to in the settlement: the census's people, and every person a
> quest places there. A quest's person gets their lines from the quest record (quest-write, Topics); this loop checks
> that none is left without one (`plugin.sh inspect silent` reads 0) and that a census person who is also in a
> quest's cast says nothing in their own topics that the quest's lines contradict at any stage.

D5.2 Add rule 5 and 6 to "The rules":

> 5. **Rumours are retold, never copied.** A rumour fact holds who, where and what is wanted as fields. At most two
>    people in a settlement carry one rumour; each says it from where they stand and what they would know of it, in
>    their own words, and no sentence of it is shared. A rumour is gated to the stages in which the quest can start.
> 6. **No shared formula.** No opening or closing phrase is used by more than two people in a settlement (the friend
>    greeting most of all); a trade or company is named in a self-description by two people at most.

D5.3 Loop step 1: replace "(Phase 4 part B's rule; a kept talker leaves the clean-up)" with "(a kept talker leaves the
clean-up list)". Loop step 9: add "and the shared-phrase check (`talk_check` repeats)".

### D6. `.claude/skills/text-review/SKILL.md`

Replace step 1's check list sentence ("...and names personification as a check: ...") so the brief names these checks
for dialogue and journal text, each a hit with a rewrite:

> - personification: a thing, place, document, institution or abstraction doing a person's act;
> - a question or demand put to the player with no reply topic listed beside the line;
> - an offer, hand-over or promise with no `sets` listed beside the line;
> - a fact two speakers of the same place and stage window both state;
> - a noun for a place, prop or scene that is not in the quest's hosts and things;
> - a pronoun that disagrees with the person's listed sex; a person named by role where a name is listed;
> - a sentence that does not parse on a slow read (a verb doubled, a referent missing).

And add to the reader's inputs: "Dialogue is reviewed as a table from the database, one row per line with its speaker,
place, stage window, prompt, reply topics and `sets`, grouped by place, never as bare text files."

### D7. `docs/design/quests-on-a-world.md`

Part 7, replace the paragraph with:

> Per speaker from the record with `dialogue-write` (matched lines from the reference corpus as the model; the
> speaker's brief generated from the data, holding that speaker's sourced facts, each line's place, stage window,
> check and effect, the reply topics, and what the others in the same place say), one `text-review` pass by another
> agent over the lines grouped by place, then loaded. Lines live in the story database and nowhere else. A line
> tells; a question is a choice with a topic per reply. A line offers only what its effect delivers. A prompt is a
> sentence the player would say with what they know, with its cost or check in it. Every topic has a first and a last
> stage; nobody offers the task after its ending. A refusal names what would change it. A fact has one speaker per
> place and stage window. Warm and cool wordings exist only for lines spoken after that person's regard has changed.
> Everyone an ending leaves standing has a greeting true of that ending. Journal entries tell one step each;
> objectives are imperatives with a target.

Part 3, replace "Every stage says plainly what to do;" with "Each thing the player must do next is its own stage, entry,
objective and target; a new character can always go on along the main quest;".

Part 5 table, add rows:

> | a check the player can fail | its own topic with the check or cost in the prompt, and a fallback line naming what is needed; INFOs of one topic are exclusive by condition |
> | a line said again later | the same INFO with a first and a last stage; the last is before the first ending |
> | after the ending | a Hello topic gated on the ending stage for each person left standing |
> | a task handed out or reported | an unconditioned line; never a skill or gold check |

Part 8, "Everyone talks": replace "answer "Who are you?" from `quest_lines/quest_people.json`" with "answer "Who are
you?" from their line rows, true of where they stand at that stage".

Part 9, add: "**A passed check teaches the recipe:** when the owner passes a fix, its class of mistake is written into
the recipe and applied to every other quest of the slice before the next walk."

### D8. `docs/design/talk.md`

Reads as history in: the opening ("Owner, 2026-11-07...", "Status: Lilmoth's 30 built..."), "Personality (owner walk
2026-11-07)" ("The first twelve had...", "the owner found them..."), "Recipe v2 (owner walk 3, 2026-11-08)" under
Truth rules, "Quest rumours wait for Phase 4's quests", "Proposed next", and the Cost section's dated run. Rewrite
each as the rule alone (the dated facts belong in the phase file). Add under "Assignment": D5.1's "Who is covered",
D5.2's rules 5 and 6, and "a rumour fact is fields (giver, place, want), not a sentence".

---

## E. Automatic checks to add

One new off-game checker over the built plugin's YAML and the database (`tools/argonia_world/quest_text_check.py`,
run by `make check` and named in quests-on-a-world part 8), except where a home is named.

| # | Catches | Check |
|---|---|---|
| 1 | A26, 9.2 | every objective has a target alias, or its row says `target: none` |
| 2 | A11, A24 | a non-ending journal entry has one "I'm to" and at most 60 words; it names no target of a later stage |
| 3 | A3, A22, A28, 9.5 | a response containing "?" or "Give me a", "Tell me", "Show me" in an INFO with no `LinkTo` fails unless the row is marked rhetorical |
| 4 | A5 | every INFO of a quest topic has a stage upper bound below the first Complete or Fail stage, unless its topic is a Hello |
| 5 | A29 | any two INFOs of one topic whose conditions can both pass for one speaker fail |
| 6 | A8 | the wordings of one line carry the same fragment; an INFO with a fragment contains none of "come back", "earn", "not yet", "I will not" |
| 7 | C8 | a warm or cool INFO whose speaker's rank no fragment sets at an earlier stage is reported as unreachable |
| 8 | A6, A10 | each quest's lines, entries and objectives are searched for the nouns of its retired hosts and cut things (`world_edit` and `quest_thing` rows marked cut or replaced); 0 hits |
| 9 | A9 | a pronoun in the sentence that names a cast person, or the next, agrees with `npc.sex` |
| 10 | A15, A17 | a prompt starts with a capital and ends with ".", "?" or ")"; an INFO with a gold condition has the amount in its prompt, one with a skill condition has "(Persuade)" or the skill |
| 11 | A16 | a stage-0 prompt contains no cast name other than the speaker's; a prompt naming a person requires a condition that the naming line was heard |
| 12 | A17 | each (speaker, topic, stage) with a skill, gold or item condition has a complement INFO |
| 13 | A2, A4 | walk each main quest's stage graph as a new character (skills 15, gold 0, no optional item): every stage reaches an ending (extend `skill_routes`) |
| 14 | A1 | every speaker and target of a stage is reachable: a RequiresKey door on the only way has its key added on every path into that stage (for `placecheck`) |
| 15 | B | per place and stage window: no fact id on two speakers; no five-word run shared by three speakers; no sentence shared by two (talk lines, quest lines and journals together; the script used for section B) |
| 16 | A20 | an entry or objective that names a placed person uses the name their base carries |
| 17 | A21 | "hours ago", "yesterday", "tonight", "this morning" in a line with no time condition: warn |
| 18 | A12 | "Here is", "Here are", "Take " in an INFO with no fragment: fail |
| 19 | A27 | every alias alive and enabled at an ending has a Hello INFO gated on that ending |
| 20 | C1, C3, C4, C9 | no string literal over 40 characters in `tools/ArgoniaPlugin/*.cs` outside comments; built hidden stages and targets equal the record's; `bans.yaml` ids unique; a read-back NOTE for a missing gate (A30) is a failure |

---

## Recommendations

- Apply A1, A2 and A4 before the next owner walk: with them open the main quest cannot be walked past MQ03 by an
  unsworn player or past stage 20 by a phial-only Argonian (evidence in each).
- Land C1 before any further line edits, so A's text fixes are made once, in rows (seven quests' lines are in JSON,
  two in rows, two in a TSV with C# fallbacks).
- Give the fixer A in this order: A1-A5 (cannot finish or wrong after the end), A6-A14 (false to the build), A15-A28
  (unclear or unseen), then B through the dialogue-write lane.

Covered: docs/phases (4, 4a), docs/design (quests-on-a-world, talk, blocks: block rows and stage table), docs/skill-fixes.md, docs/owner-rulings.md and docs/owner-walk-checks.md (quest and dialogue entries), tmp/walk-5-feedback (Quests in BM&V), .claude/skills (quest-write SKILL and quest-record, quest-review, dialogue-write SKILL, voices, bans ids, talk-write, text-review), .claude/agents (dialogue-writer, reader, quest-reviewer), story/data/quest_lines (all 8), story/data/db (quest_stage, quest_objective, dialogue_line, talk_*, talker, npc, world_edit, bmv_door, bmv_talker), plugin/Argonia (Quests, DialogTopics, DialogBranches for the 11 quests, every INFO read; the BlackMarsh worldspace record for one door), tools/ArgoniaPlugin (MainQuest, MQ04, MQ05, NightReed, LocalQuests, QuestKit: comments and text paths), papyrus (ARG_QF_MQ01, MQ03; rank calls in the rest). Skipped: packages, navmesh, aliases' engine behaviour and the gang's march (the second reviewer); the 963 talk lines beyond the phrase and fact scans and the lines touching quest people; quest-write's principles files and examples; brief.py, lint.py and talk_check.py bodies (read for what they hold, not audited); BM&V's own refs for the workshop, knife-peg, bent reeds and gate sign (unverified, marked PLAUSIBLE); the ESP's INFO order (A29).
