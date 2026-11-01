<!-- imported unchanged from elder-souls-argonia docs/research/dialogue/elder-scrolls-dialogue.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# What makes Elder Scrolls NPC dialogue work

Research for the 2.7d dialogue voice work. Pulled 2026-10-19. Evidence grades: **S** = developer's own
words or the game's own text; **P** = prior (fan or critic opinion, a lead to test, never a rule on its own).
*Morrowind* is 3E 427, outside the production era (4E 201) ([0002](../../old-decisions/0002-era-and-source-confidence.md)):
everything here is a register and craft yardstick, never lore.

## Limits of this pull

- No interview was found in which Kirkbride, Nesmith or Kuhlmann describes how NPC dialogue is written. Kirkbride's
  public Q&As cover lore and the Sermons ([S9]), not conversation craft. What exists is Rolston's, Nelson's, Howard's
  and Pagliarulo's remarks, plus the game text itself.
- The Imperial Library transcripts, UESP's modding page by HTML, GameBanshee and the Polygon original returned 403 to
  the fetcher. UESP was read through its MediaWiki API; Polygon through a verbatim mirror; GameBanshee and GamesRadar
  items are marked *(search-reported)* where the page body was not read.
- Length numbers come from the repo's own measured pull of 7,952 *Morrowind* lines
  ([S12](../../../world/sources/lore/morrowind-dialogue-corpus-full.md), [S13](../text-and-voice/morrowind-dialogue-corpus.md) § 10).
  Skyrim and Oblivion figures below are hand reads of UESP pages, not counts.

## Sources

| # | Source | URL | Grade |
|---|---|---|---|
| S1 | UESP, *Morrowind Mod: Creating dialogue in Morrowind* (engine rules for topics, greetings, line order) | https://en.uesp.net/wiki/Morrowind_Mod:Creating_dialogue_in_Morrowind | S |
| S2 | Polygon, "Morrowind: An oral history" (Mar 2019; read via mirror) | https://gameup24.wordpress.com/2019/03/27/morrowind-an-oral-history/ | S |
| S3 | Game Developer, "Q&A: Ken Rolston's development secrets of The Elder Scrolls IV: Oblivion" | https://www.gamedeveloper.com/design/q-a-ken-rolston-s-development-secrets-of-i-the-elder-scrolls-iv-oblivion-i- | S |
| S4 | GameBanshee, "Ken Rolston on the Shifting Design Philosophies of The Elder Scrolls" *(search-reported)* | https://www.gamebanshee.com/news/119060-ken-rolston-on-the-shifting-design-philosophies-of-the-elder-scrolls.html | S |
| S5 | GameBanshee, Ken Rolston interview ([H]Consumer) on partial vs full voice *(search-reported)* | https://www.gamebanshee.com/news/79897-ken-rolston-interview-v15-79897.html | S |
| S6 | Bethesda.net, "How an Arrow in the Knee Made Its Way to Skyrim" (Pagliarulo) | https://bethesda.net/en-EU/news/how-an-arrow-in-the-knee-made-its-way-to-skyrim | S |
| S7 | GamesRadar, "Starfield writers struggled to transition from Skyrim and Fallout" (Pagliarulo to Polygon) *(search-reported)* | https://www.gamesradar.com/starfield-writers-struggled-to-transition-from-skyrim-and-fallout/ | S |
| S8 | UESP, *Oblivion: Generic Dialogue* | https://en.uesp.net/wiki/Oblivion:Generic_Dialogue | S (game text) |
| S9 | UESP, *General: Michael Kirkbride AMA* | https://en.uesp.net/wiki/General:Michael_Kirkbride_AMA | S (scope only) |
| S10 | UESP, *Skyrim: Guard Dialogue* | https://en.uesp.net/wiki/Skyrim:Guard_Dialogue | S (game text) |
| S11 | UESP, *Skyrim: Adrianne Avenicci* and *Skyrim: Ulfric Stormcloak* | https://en.uesp.net/wiki/Skyrim:Adrianne_Avenicci , https://en.uesp.net/wiki/Skyrim:Ulfric_Stormcloak | S (game text) |
| S12 | Repo: Morrowind full dialogue pull (7,952 lines) | world/sources/lore/morrowind-dialogue-corpus-full.md | S (game text, UESP) |
| S13 | Repo: Morrowind dialogue corpus dossier, § 10 measured profile, sequences S13/S14 | docs/research/text-and-voice/morrowind-dialogue-corpus.md | S (game text, UESP) |
| S14 | Video Game Academia, "Vacationing in Morrowind: A Travelogue" (argues unvoiced reading beats voiced Oblivion) | https://videogameacademia.org/2025/05/17/vacationing-in-morrowind-a-travelogue/ | P |
| S15 | Morroblivion blog #9 (modders converting keyword topics to voiced statements) | https://morroblivion.com/blog/blog-post-9 | P |
| S16 | Bethesda/UESP, *Skyrim: Lydia* (follower barks) | https://en.uesp.net/wiki/Skyrim:Lydia | S (game text) |

## Findings

### 1. How lines open

- **Morrowind opens on a greeting that is a line of attitude, not a menu.** Voiced greetings average 6.3 words (median 6);
  90% are 10 words or fewer and none run past 25 ([S13] § 10.1). Greetings are tiered by disposition: the voiced file number
  runs from coldest to warmest, and a line like "Save your breath..." replaces the neutral one below a threshold
  ([S12], [speech-register model](../text-and-voice/speech-register-model-morrowind.md) § 1).
- **The greeting is also the hook.** The engine scans the NPC's own words for topics and turns matching phrases into blue
  links ([S1]: "the topic will be printed in blue, be clickable"). The modding guide's model is exactly
  "give an NPC a greeting 'I need some meteor slime'", then a topic that answers it. A greeting that names a thing is already
  an offer; only 6% of greetings carry a name or number ([S13] § 10.2).
- **Address is a formula by rank and people.** Great House NPCs open "[rank] of House [name], how may I serve you?"; Legion,
  guild and Morag Tong lines are rank-and-office formulas; the Dunmer say "outlander", the Khajiit "friend" and refer to
  themselves by name ([S13] § 10.3). The listener's standing decides the line, so the opening already tells the player who is
  who in the room.
- **Skyrim opens shorter and rougher.** Guard openers are one-liners: "What do you need?", "Trouble?", "No lollygaggin'."
  ([S10]). Followers open with a service formula: "How can I serve you, my Thane?" ([S16]).
- **Oblivion opens on gossip.** Its generic pool is rumour sentences an NPC volunteers: "The Arena's faked... It's just berry
  syrup and ham-acting." ([S8]).

### 2. How NPCs say who they are and explain their place

- **Rolston seeded towns with people, not lore.** Each NPC got a three-word trait ("charming, shiftless, angry") and a faction;
  shared factions "created a large number of intersection nodes in the setting that you could build a coherent story out of"
  ([S2] Dialogue section; [S3]). Place is explained through who hates whom: Nelson's complaint was that new players asked
  "Who hates who? Why do these guys not like each other?" ([S2]).
- **Rolston's "dog's story".** God's story belongs to priests; he wanted the farmer's, soldier's and dog's view, "little
  character studies and one-off quests" ([S2]). People explain their place by what it costs them.
- **Skyrim locates an NPC by relation.** Adrianne Avenicci introduces herself through her father, her rival smith and the
  Jarl: "I don't claim to be the best blacksmith in Whiterun. Eorlund Gray-Mane's got that honor... All I ask is a fair chance."
  Her answer about the city names a ruler, a fortress and a hall in three sentences and ends on a pointer
  ("you're probably more interested in Jorrvaskr") ([S11]).
- **Place shifts with the world state.** The same Adrianne line changes when Eorlund is dead or the Stormcloaks hold the city
  ([S11]); Morrowind's generic topic lines split by town, class and disposition ([S13] S13: a miner slave, a house servant
  and a free man each answer the one question differently).

### 3. How topic answers are shaped

- **Morrowind: one block per topic.** Topic answers have a median of 32 words, rumours 34; unique-person lines median 24;
  one in four unique-person answers is 12 words or fewer ([S13] § 10.1). A refusal is a short sentence ("I don't know
  anything about it..."). Information arrives in a block, not across a back-and-forth.
- **Candour has a price.** The same topic is answered shut at low disposition and open at high disposition. Dossier sequence S14
  shows a ladder from "The King is dead. Long live the King. What more do you want me to say?" to a speculation with a named
  broadside and a grievance ([S13] S14). The answer is deepened by trust, not by length alone.
- **Facts first, opinion in a clause, no verdict.** In 150 sampled multi-sentence lines, 93% end on a fact, an instruction,
  a pointer or a question; 3% end on an epigram and 4% on a shrug ([S13] § 10.4). Two in three topic lines and four in five
  rumours carry a name, a number or a concrete object ([S13] § 10.2).
- **Skyrim gives the long form to the powerful.** Ulfric's answers run 40 to 100 words and argue a position
  ("We're fighting because...") ([S11]); ordinary townsfolk stay at 15 to 45. Length tracks the speaker's stake.
- **Choice is player voice.** The engine's "continue" choice splits a long answer into chunks of at most 512 characters
  ([S1]); Rolston says he began to want "more explicit conversations between myself and the player in the non-quest dialogue"
  after seeing play ([S3]).

### 4. Length and rhythm

| Slot | Mean words | Median | Source |
|---|---|---|---|
| Morrowind greeting | 6.3 | 6 | [S13] § 10.1 |
| Morrowind bark | 3.7 | 3 | [S13] § 10.1 |
| Morrowind topic answer | 39.0 | 32 | [S13] § 10.1 |
| Morrowind rumour | 38.8 | 34 | [S13] § 10.1 |
| Morrowind unique person | 32.0 | 24 | [S13] § 10.1 |

- Short lines open and close; the information sits in the middle. Contractions follow the speaker: Argonian and Khajiit about
  4%, Orc 8%, Dunmer 16%, Nord 30%, Redguard 37% ([S13] § 10.2). Rumours contract in 72% of lines, formal service lines
  in 20%. Rhythm is made by who is speaking, not by a house style.
- Pagliarulo's own correction on Starfield was to keep "really pushing concise dialogue and realistic dialogue" by asking
  "How do people really talk?", playtesting the designers' scripts and cutting what took too many clicks ([S7], search-reported).
  He names the Skyrim to Fallout 4 problem too: shopkeepers saying "Hello and well met!" read as a tonal mismatch.
- Skyrim's idle barks are the extreme short form (about 3 to 12 words) and exist, in his words, "to make the guards a bit more
  interesting" ([S6]); recorded lines are costly to change ("you also have to get the actor back in to re-record the lines").

### 5. Humour

- **Humour is placed, not sprinkled.** Nelson: Todd Howard's rule was that humour has no place, so the team set out to "see what
  funny shit we could get into a game" ([S2]). Rolston's tone was "more fun for shits and giggles, and very user-focused", loose,
  ironic tabletop, not a tone-policed script ([S2]).
- **It comes from a character's own point of view.** Rolston on Caius Cosades: he is shirtless with a skooma pipe under his bed
  but "talking in another, heroic way, so you're able to give a conflicting narrative" ([S2]). The joke is the gap between the
  man and his pose.
- **Skyrim humour is the guard bark.** "Let me guess... someone stole your sweetroll." and the arrow in the knee line were written
  late and fast as "funny, quick little lines" ([S6], [S10]). They fill dead air and reflect the player back. Oblivion's is
  dry civic cynicism ("ham-acting") ([S8]).
- **Wry, in character, short.** The Morrowind flourishes that do occur ("Bribes are the lubricant of honest commerce.") are all
  tied to a grievance or a creed, spoken aloud, and never stand as a one-sentence paragraph ([S13] § 10.4).

### 6. Carrying exposition without over-compression

- **Rolston: "I'm paying for exposition."** He was surprised players would buy books; in-world documents carried what dialogue
  did not ([S2] Books). Nelson put scrolls in the Falling Wizard's pocket "to explain how he had gotten up that high" ([S2]).
  Offload lore to found documents, and keep the person's answer on the person.
- **Hyperlinked topics let one answer be small.** Howard praised "that nested, kind of hyperlinked system" ([S2]); the engine
  adds the topic only when an NPC says it ([S1]). The player pulls the next fact with a click, so no answer needs to hold the
  whole. Rolston himself judged the journal hyperlinks "a negative feature of the game" because the idea "was never refined"
  ([S3]); the cost is the wiki feel noted in fan complaints ([S15], prior): everyone has the same page with different topics.
- **Contradiction is a feature.** Each race tells its own version ("Each race has their version"); Rolston refused to confirm
  the player is the Nerevarine ([S2]). Exposition as a speaker's account, with a stake, survives without being a lecture.
- **Pagliarulo: don't tell the story through "lore bombs".** Level designers carry half the story visually, and each quest line
  pairs a quest designer with a level designer ([S7], search-reported). Dialogue should not need to explain what the place shows.
- **Unvoiced text lets the player supply tone.** Rolston prefers partly recorded dialogue: fully voiced is "less flexible, less
  apt for user projection of his own tone" and more constrained for branching ([S5], search-reported). Critics agree that reading
  can feel more immersive than Oblivion's thin voiced pool ([S14], prior). This game is text, so we take the advantage.
- **Not over-compressed.** Morrowind's median topic is 32 words and 22% of topics run past 40 ([S13] § 10.1): enough for a fact,
  a name, a stake and a pointer. What the corpus does not do is close each line on a compressed aphorism (3%, [S13] § 10.4).
  The compression to avoid is the pithy epigram, not the length.

### 7. What fails (priors, to test, not to obey)

- Oblivion's radiant conversations, built by recombining short prompts and replies, read as patchworked and stilted ([S8] pool;
  critics, prior). Few voice actors made it worse (prior).
- Overlapping topic phrases break the keyword parser ([S1]); a topic name must be unique and must appear verbatim in the speaker's
  text. A design lesson for any hyperlinked system: topic names are a controlled vocabulary.
- Over-designed one-liners as an end in themselves became a meme (arrow in the knee) ([S6]); the line works because it is rare and
  in a guard's mouth.

## Writing instructions

For one-person game dialogue (our voiced-in-text, topic-based NPCs):

1. **Open short, and make the opening an attitude.** Greetings are 4 to 10 words; none over 15. Let rank, standing and disposition
   change the line. No fact, name or number in a plain greeting unless it is the hook.
2. **Plant the topic in the speaker's own words.** If a topic should be asked about, an NPC says its exact phrase first. A greeting
   or answer that names a thing is an offer.
3. **Say who someone is by their stakes and relations.** Name a person they depend on or resent, a rival, a ruler, a cost. Give
   each NPC a faction and a three-word trait before writing.
4. **Answer in one block of 15 to 45 words.** Median about 30. Put the fact first, one opinion in a clause, then stop. Longer only
   for a speaker with a stake and a position to argue.
5. **End on a fact, an instruction, a pointer or a question.** About 1 line in 25 may end on an aphorism, and only if a person
   would say it aloud and it ties to a grievance. Never a closing verdict nobody asked for.
6. **Anchor lines in particulars.** Two topic lines in three and four rumours in five name a place, person, number or object.
   Greetings and barks almost never do.
7. **Let disposition price candour.** The same topic gets a shut answer at low trust and an open one at high trust, while the
   essential fact is never gated (decision [0145](../../old-decisions/0145-disposition-changes-the-talk-essential-topics-never-gated.md)).
8. **Make refusals short.** A plain "nobody" answer is 12 words or fewer, and a refusal is a sentence, not a paragraph.
9. **Vary rhythm by speaker, not by house style.** Match contractions to the people (near 5% for formal or reptilian voices, about
   15% Dunmer-like, 25 to 35% for casual ones); a whole batch at one rate reads as one voice.
10. **Carry exposition through accounts and documents.** A speaker gives their version, which may disagree with another's; bulk lore
    goes in books and notes the player can find. Never a lore bomb in a greeting or a bark.
11. **Keep each answer small and let the next topic carry on.** Offer the next link by naming a person or place the player can ask
    about; keep topic names unique and verbatim.
12. **Put humour in the character's pose, and in barks.** The joke is the gap between who someone is and how they carry themselves,
    or a short bark (3 to 12 words). Rare, fast, and never at the cost of the fact.
13. **Write barks as 1 to 6 words.** They fill dead air and show personality; they are not exposition.
14. **Let the place carry half the story.** Do not have an NPC explain what the player can see in the scene.
15. **Test by reading aloud and cutting clicks.** If a conversation takes more selections than the information is worth, cut
    (the Pagliarulo playtest rule). Check against the measured profile in [S13] § 10.5.
