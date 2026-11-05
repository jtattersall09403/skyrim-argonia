<!-- imported unchanged from elder-souls-argonia docs/research/text-and-voice/dialogue-rulings-index.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Dialogue rulings index

Every place the repo rules on, discusses or researches NPC dialogue, reconciled into one row per ruling or finding. Built by a `find` fan-out on 2026-10-18 over docs/decisions, docs/standards, docs/research, docs/quests, docs/phases, lanes/**, tmp/*.md and owner inbox issue 2. `docs/world` does not exist. "Open" means no tool, gate or line applies it today; every open row is a line in [2.6 § Dialogue, continued from 2.5x](../../phases/2-slice/2.6-trade-and-services.md#dialogue-continued-from-25x). Gate and tool paths are under `tooling/world-generation/worldgen/`.

## Owner rulings

| Source | Rule | Applied today |
| --- | --- | --- |
| tmp/2-slice-so-far-fixes.md:27-30 | Less curt, less AI; an answer says what the thing is; "x goes to the y" not overused; not everyone curt; loop against Morrowind with a critical judge | ANSWER_LENGTH bands, `style.spread`, `dialogue_critic` (pairwise, 40 percent bar) |
| lanes/2.5x/handoff.md:31; decisions/0079:59 | Dialogue writing and reviewing run on Sonnet: `dialogue-lane`, `dialogue-writer`, `voice-reader`, `corpus-reader` | .claude/agents/ |
| lanes/2.5x/handoff.md:28 | The writer has no other context: the packet carries the person's whole world (world, place, person, personality, culture, topics, province awareness, exemplars, usage, tells, worked example, task) | dialogue_packet.py (13 sections) |
| lanes/2.5x/handoff.md:28 | Personality profile, corpus awareness, tagged Morrowind exemplar bank and bad-example bank grown by every corpus read; cold sense check before a trial | dialogue_packet.py, dialogue_exemplars.py, exemplars/*.json |
| owner 2026-10-19 (Naga tally-keeper) | A speaker describes their own doings in the words they would use to a stranger, never an accuser's; no confession of a crime, flaw or lie unless the stance marks it | SKILL.md, tells 68, `check` red `self_image_reds` (`ACCUSER_WORDS`, stance reasons exempt) |
| owner 2026-10-19 | "and nothing else", "nothing more", "and that's all", "no more, no less" and the family are AI tells; an "and" may not tack on a denial | SKILL.md, tells 69, `PET_PHRASES` and `AND_TACKED` reds in `self_image_reds` |
| lanes/2.5x/handoff.md:30,32 | One self-check before the draft freezes; the tool counts, the writer writes; one draft plus two tool-assisted revisions, measured at freeze (owner's "one draft, one revision" widened to two revisions: planner call, for the owner) | WRITER_BRIEF, `check` counter and `freeze` in dialogue_rewrite.py |
| lanes/2.5x/handoff.md:30,32; culture-registers.md:61 | Argonian and Khajiit contractions follow Morrowind: at most 4 percent of their answers | `style.contraction` (hard) |
| lanes/2.5x/handoff.md:37 | Dialogue continues in 2.6; unpassable new gates warn with a reason until 2.6 turns them hard | applied: `dialogue_gates.WARN_GATES` is empty, every gate hard (2.6z1) |
| handoff.md:34 (review A) | British comma after a fronted adverbial | tool: `fronted-no-comma` hard in dialogue (`lint_prose.DIALOGUE_HARD_RULES`), gated as `prose.review` (hard) |
| handoff.md:34 (review B) | No contradictory "and" joins | tool: `and-negated-same-subject` hard in dialogue, gated as `prose.review` (hard) |
| handoff.md:34 (review C) | No non-sequitur closing question | tool: `style.closingQuestion` (a closing question sharing no noun with its answer or topic; hard) and `style.closers` (two in a row) |
| handoff.md:34 (review D) | A helpful speaker explains so a newcomer understands; fact rows get a plain gloss | tell, packet fact gloss line, critic prompt (dialogue_critic.py) and voice-reader `explains` lens; corpus not rewritten |
| handoff.md:34 (review E) | Lore said in full, not hinted | tell in the skill, critic prompt and voice-reader `explains` lens; corpus not rewritten |
| handoff.md:34 (review F) | Cap "never", "count", "keep", "hold" | tool: `style.wordCap`, each word (any form) in at most 5 percent of a place's answers (Morrowind 3.5, 1.9, 0, 0.4; ours 12.4, 15.6, 6.2, 5.7); hard |
| handoff.md:34 (review G) | No inanimate subject with a human verb | tool: `inanimate-keeps` hard in dialogue, gated as `prose.review` (hard) |
| handoff.md:34 (review H) | Delete the explain-once rule and explainer cap: anyone may explain in their own words; helpfulness by personality, faction, race | applied ([0143](../../old-decisions/0143-anyone-may-explain-restatement-is-near-verbatim-only.md)): the cap is deleted; `corpus.restatement` reds near-verbatim wording across speakers only (hard); `corpus.paraphrase` deleted too (2.6g3; its copy case is `corpus.restatement`) |
| handoff.md:34 (review I) | Grounding gate: every rumour, place, road, distance, item, person, price, service and payment in kind resolves to a real record; a lie only where the stance marks it with the true fact | tool: `corpus.grounded` (`dialogue_grounded.py`; `groundedIn` on a line, a lie by the stance's `lie.trueFactId`); hard; a travel time passes when its sentence names a place, a slice place's plain name or a direction |
| handoff.md:34 (review J) | The closing read gains a sixth check, "grounded" | corpus-reader.md check 6 |
| lanes/2.5x/diag/owner-calls.md:50-54 | Boat crews addressed by boat name | partly: rule at world/sources/dialogue/cultures/settlements/riverwalk.json:91; no line uses it |
| lanes/2.5x/diag/owner-calls.md:56-60 | Write the Cut Circle explaining line | open |
| issue 2, 2026-10-18 | Owner sample read in the studio decides whether the corpus is good enough | open |
| issue 2, 2026-10-18 | Dialogue screen cssGzip 12800 to 12950: confirm or trim | measured 12900 under budget 12950 (2.6g2); no cheap trim in lane scope; owner confirms 12950 |
| issue 2, 2026-10-18 | Walk-by voice barks need about 2 GB of Skyrim archive | open (owner step; 2.14) |

## Decisions and standards

| Source | Rule | Applied today |
| --- | --- | --- |
| decisions/0139:3-9 | Morrowind-shaped mechanics; voice layered culture to person; each fact once in a pool line; a stance per topic class and a voice sheet with one quirk | world/sources/dialogue/ layers, dialogue_sheets.py |
| decisions/0139:6-9; 2.5-dialogue.md:180 | Sameness judged by reader panels, one lens each; the linter is not the bar | voice-reader, corpus-reader |
| decisions/0139:38-40 | A topic across a village shows the norm and its dissenter | culture-sheet `dissent` list (17 entries); closing read 2 found 2 voices missing: open |
| decisions/0043:13-18 | Two failure modes: AI voice and convergence | text-review skill, corpus read |
| decisions/0043:67 | No phonetic accent spelling; accent by syntax and address terms only | style-guide.md (rule text) |
| decisions/0043:85-94 | British spelling provisionally; owner choice open | open (owner call) |
| decisions/0042:115; engineering.md:212 | Dialogue lines are typed content units | packages/dialogue records |
| decisions/0137:22-25 | Every direction in dialogue is authored from the real world and walked | `corpus.road`, dialogue_walk.py |
| decisions/0026:20-21; quests/60:71 | Every load-bearing proper noun has a newcomer-phrased topic from ordinary NPCs | `dialogue_newcomer.py`, hard in `dialogue_gates` as `newcomer.gaps` and `newcomer.ambient` (0 in 13 places) |
| decisions/0054:33 | `raceIs` is race-and-sex keyed | open |
| decisions/0140:12-14; 2.5-dialogue.md:325 | Gates run per changed record id; adding lines republishes no people | `--place` on every dialogue tool |
| engineering.md:302 | The prose linter lints dialogue by exclusion | lint_prose.py |
| style-core.md:121-128 | Dialogue keeps race, region and faction voice but obeys every ban; ALL-CAPS and "!" once a scene; semicolons rare | dialogue-write skill, dialogue_style.py |
| style-core.md §4 | One person explains, the rest react | replaced by 0143: anyone may explain in their own words; style-core §4 says so |
| style-guide.md:193-204, 482-490 | Plainer than remembered; the NPC simply knows; greeting states trade or office; rumour is the only unreliable register | dialogue-write skill |
| culture-registers.md:74-157 | Contraction rate set by the people layer (Khajiit few, Imperial fringe and pirates contract, Altmer none) | `style.contraction` |

## Quest and research rules

| Source | Rule | Applied today |
| --- | --- | --- |
| quests/60:22 (§45b) | The Argonian register binds Argonian speakers only; voice is race, upbringing, region, faction | culture-registers.md |
| quests/60:86-90 (§45d) | Act I teaches by scene, not a lecture; NPCs may disagree on facts | open (2.11, 4.3) |
| quests/60:96 (§45e) | The reviewer is not the writer | text-review skill |
| quests/60:165-263 (§45e.1) | Banned rows: one-word greeting address, "How may I help you?", hospitable-host template, "kept back for you", "walker" outside Khajiit and Naga mouths | lint_prose.py banned table |
| quests/60:213-215 | Corpus targets: greeting median 6, bark 3, topic 32, rumour 34 words; 3 percent end on a question | ANSWER_LENGTH, CLASS_MEDIAN |
| quests/60:277-278 (§46) | Topic unlocks by conversation, evidence, rank; rumours follow local state; race reactions do not assume birthplace or guilt | packages/dialogue topic web; rumour state open (2.11) |
| quests/35-cast.md:277 | An ambient NPC does not explain the world or opine on the main quest | `dialogue_newcomer.py` ambient (C4 on Hist, An-Xileel, throne, Owing, war topics); 6 flags open |
| quests/80:97-116 | An `opaque` topic returns folk speculation, not truth | open |
| quests/85:52-65 | `topicHeardFrom` records who told the player, the basis for catching a lie | open (needed by review I) |
| quests/90:100-107 | A content-format spec for topic naming, length norms and rumour formats | open (not located) |
| research/text-and-voice/speech-register-model-morrowind.md:140-149 | Topic by condition set; rank strongest, race a thin substrate, region subject matter only | dialogue layers |
| research/text-and-voice/morrowind-dialogue-corpus.md | 259 Morrowind lines, the yardstick; comparison only, names masked | exemplars/morrowind.json, dialogue_critic |
| research/text-and-voice/ai-writing-tells.md | What reads as machine-written and the fix | dialogue-write references/tells.md |
| research/text-and-voice/skyrim-voice-barks.md:10-15 | Walk-by barks are Skyrim clips; a greeting is a branch topic, not a bark | open (2.14) |
| research archive stats-progression-mapping-inventory.md:94-97 | Speech checks are Speechcraft, Personality, evidence, disposition and rank; no random rolls | packages/dialogue persuasion |

## Phase and lane findings

| Source | Rule or finding | Applied today |
| --- | --- | --- |
| 2.5-dialogue.md:132-141 | One person per writer call; neighbours not in one call | dialogue-write sequence |
| 2.5-dialogue.md:162-174, 203-249 | Loop 1 exit: two batches with no new row, blind mix at chance, owner sample read | open |
| 2.5-dialogue.md:251-268 | ui-lab dialogue at three viewports and three input modes | 8 dialogue screens, 72 shots (desktop mouse+keyboard, phone and fold touch+pad), no dialogue finding (2.6g2) |
| 2.5-dialogue.md:302-311 | Panels stop after two fix rounds; run as one Workflow | rule |
| 2.6-trade-and-services.md:79 | Trainers (Claywater well-keeper, Riverwalk stage-mistress, upriver smith) get lines by dialogue-write | open (2.6) |
| 2.10:37 | Greetings read the crime and faction ledger | open (2.10) |
| 2.11:21-58 | Directions and journal lines written against real state; dialogue starts quests | open (2.11) |
| 4.2-region-packets.md:20-38 | Every packet runs the dialogue gate and walker; every NPC gets full dialogue | open (Part 4) |
| corpus-read-close.md:5 | Over-corrected: median override 43 words | `style.spread` |
| corpus-read-final.md:5 | Restatement, hand-off loops, aphorism closers | `corpus.restatement`, `corpus.handOff` |
| corpus-read-final-2.md:5 | Per-speaker hooks, by-meaning restatement, missing dissent | `corpus.restatement` (hard); hooks and dissent open |
| dialogue-report.md Part 9 | `npc_roster` FEMALE_WORDS lacks "mistress", MALE_WORDS lacks "master" | npc_roster.py (009ce3e8d) |
| dialogue-skill-report.md Part 2 | 12 stance-deviation pronoun clashes (greenspring, upriver, flotilla, chasepoint n1, n1-2) | open |
| dialogue-skill-report.md Part 2 | Packets reach 15k words; trim by chatter | packets trimmed by chatter (`dialogue_packet.manner`) |
