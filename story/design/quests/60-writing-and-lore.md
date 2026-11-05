<!-- imported unchanged from elder-souls-argonia docs/quests/60-writing-and-lore.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Lore layers, dialogue, twists and rewards

> Module of the quest/narrative master plan (see [README](README.md)).

# Part X — Lore, dialogue and writing strategy

## 45. Canon, inference and project-original material

Every narrative datum should use the existing source-confidence categories:

| Layer | Treatment |
|---|---|
| **Canon/game-derived** | Preserve direct facts; surface conflicts between official sources rather than silently flattening them. |
| **Lore-inferred** | Use logical inference where Fourth-Era Black Marsh is under-described; record reasoning and era range. |
| **Project-original** | New offices, people, events and mechanisms must fill a real gap, respect known history and avoid pretending to be canon. |
| **Community inspiration** | Credit named fan contributors/projects and identify what was adapted. |

**King of the Murkmire (KotM) text** ([KotM plan](../research/placement-settlements/king-of-the-murkmire-adoption-plan.md) § 3.8): its dialogue, books and names are a register reference for Saxhleel speech, never a source; cite UESP for canon books. The extracted corpus lives in the vault (`elder-scrolls-asset-pipeline/derived/text/king-of-the-murkmire/`), never in the repo. Never reuse its invented names: [86-never-reuse-names.md](86-never-reuse-names.md).

The Veiled Reed, Unbound Root and Root of Accord are project-original. The Eye of Argonia, Hist, Sithis, Nisswo, An-Xileel, Shadowscales, Duskfall, Xanmeers, Lilmoth/Umbriel and Black Marsh cities are grounded in established lore.

## 45b. Argonian register — and the layered model it sits in

**This section binds Argonian speakers only.** Argonia holds all ten Tamrielic
races in the proportions in [world/92 §82](../world/92-demographics.md), and a
Khajiit, a Dunmer or a Nord living in the marsh does **not** speak like a
Saxhleel. Every speaker's voice is composed from four layers — race +
upbringing + region + faction — per
[text/culture-registers.md](../standards/text/culture-registers.md) §0, which is the
binding model; this section is just its Argonian race row in full.

Canon Argonian speech habits: the full set lives in the lore dossier — read it
before writing Argonian dialogue rather than rediscovering it per quest (lore:
topics/material-culture.md § *Language notes for dialogue*). Headlines: Jel has
no past or future tense; body language carries grammar, which is why Argonians
speaking Tamrielic preface statements with emotional qualifiers ("I erect the
spine of…", "My rage-quill is engorged!"); farewell "Stay moist.", curse "Hist
piss!", exclamation "Host of Stormhold."; outsiders are **ojel** (not
derogatory) — the An-Xileel's **Lukiul** very much is. Moderation: one
qualifier per scene per speaker is plenty; overuse is the failure mode. A
**lukiul** cannot use them naturally and it shows.

## 45c. The 4E 48 calibration (binding tone rule)

The owner's directive: the generational trauma of Umbriel plays at the
emotional distance our own 2026 has from the First World War (lore:
extrapolation/argonia-4e201-state.md §9). For every quest touching Umbriel, the
An-Xileel, the Lukiul question or the southern cities:

- **No living witnesses.** Argonian lifespans are human-like; anyone claiming
  to remember Umbriel is lying, mistaken, or not what they seem.
- **An NPC may be bored by it.** 153 years makes it history — argued about,
  politicised, taught badly, exploited, shrugged at by the young. Playing it
  that way is what makes the places where it *is* still raw land properly.
- **It is not universal.** Thornmarsh and Archon were barely touched; Murkmire,
  Lilmoth, Gideon and Stormhold carry it. Do not assume a province-wide wound.
- **The Nisswo counter-argument is sympathetic.** A Nisswo telling a grieving
  community to let go is preaching *shunatei*, not being callous;
  memorial-versus-letting-go must be argued honestly on both sides.

Province-wide register: **melancholy and dignified, horror kept local** (owner
decision Q5).

## 45d. The player knows nothing (binding onboarding rule)

**Assume the player has no Elder Scrolls lore
beyond, at most, having played Morrowind** — and none of Argonia's. The player
character is an outsider (Morrowind's model), so ignorance is diegetic and
asking basic questions is in character.

- **Every load-bearing proper noun has a dialogue topic** (Hist, sap, Nisswo,
  Sithis, An-Xileel, Lukiul, the Owing, Shadowscales, Xanmeer, the Eye, the
  Scalded Throne…), phrased for a newcomer, discoverable from ordinary NPCs —
  the Morrowind topic system used as a teaching instrument. The obligation is
  scoped by the **glossary** (defined in 80 §59b): only load-bearing/
  stakes-bearing nouns need topics, not every lore word. Entries flagged
  `opaque` are the carve-out — deliberate wonder content whose topic returns
  folk speculation, never truth, and which is exempt from newcomer coverage.
- **Act I is the lore onboarding**: by the end of MQ05 the player has had a
  natural opportunity (never a lecture) to learn what a Hist is and how the
  cult's harvest kills a clutch — its Mnemic-Egg interference severs the
  egg-connection, and the eggs die with it; the tree's silence is the *sign*,
  the severed connection the *cause* (`CANON_DERIVED` — canon ties egg death
  to the connection, not to withdrawal as such) — what the Wardens are, what
  an Owing is, and that the throne is empty. Each is taught by a *scene*, not
  a codex: the dead clutch, the ledger read-out, the empty hall.
- **No quest may require outside-game knowledge** to understand its stakes or
  its choice. If a brief's premise needs a lore fact, the quest itself must
  surface that fact en route.
- Explanations use plain speech in character; NPCs may disagree about the
  facts, but a newcomer must be able to assemble the working truth — enough to
  weigh the main choice, not doctrinal resolution.
- Validator: glossary terms carry topic coverage and an Act-I availability
  flag; `opaque` entries are exempt (80 §59b, §63).

## 45e. TES voice, and the AI-voice failure mode (binding)

Decision
[0042 §6](../old-decisions/0042-buildout-steers-and-engineering-standards.md).
**Model-written prose reaches for gravitas and produces constructions nobody
writes.** The owner's example, from a death message: *"With this death, a root
the story grew along is severed"* — a stranded preposition wrapped round a
relative clause, reaching for weight. Grammatical would be *"a root along which
the story grew"*; **good** is *"With this death, a root is severed."*

**TES prose is plainer than people remember.** Short declaratives. Concrete
nouns. Archaism carried by *vocabulary and idiom* — not by inverted or twisted
syntax. When a line feels portentous, cut it in half; what remains is usually
the line.

**All three stages below are built** (decision
[0043](../old-decisions/0043-text-quality-workstream.md)): the research
pass is done, the rulebook is [docs/standards/text/](../standards/text/README.md), and the reviewer's
brief is [docs/standards/text/review-process.md](../standards/text/review-process.md). Writers read
that shelf; **this section keeps the banned-constructions table below**, which is
the single place new rows are added.

Three stages, and this is a *requirement on writing*, not a cleanup afterwards:

1. **A voice research pass** derives the rulebook from the actual corpus
   (Morrowind dialogue and books, Skyrim's better-written material): register,
   sentence length, permitted archaism, how each culture and class speaks, and
   — the place AI voice hides best — **how system messages sound** (deaths,
   tutorials, item descriptions, failure text, where no character anchors the
   register).
2. **The rulebook binds every text-producing agent** as an input to writing.
3. **An independent voice-review agent** — a different agent from the writer,
   by design, because a writer will not catch its own register — reviews
   written text against the rulebook and proposes the specific edit.

Engineering standard 4 (one keyed text catalogue,
[../engineering-standards.md](../standards/engineering.md)) is what makes stage
3 mechanical: the reviewer sweeps one catalogue instead of hunting through code.

### 45e.1 Banned constructions (grows — add on sight)

Evidence, examples and the reviewer's qualitative tests:
[docs/research/text-and-voice/ai-writing-tells.md](../research/text-and-voice/ai-writing-tells.md). **Density is the
tell, not any single instance** — these are checks, not a lint.

| Don't | Do | Why |
|---|---|---|
| A figurative *eat / devour / swallow / feed on / gnaw* with an inanimate subject ("a road that eats iron") | the literal verb: rusts, rots, sinks, wears | the metaphor is decoration; lint `eat-figurative` |
| An object, place, road, river or weather acting as an agent that pays, wants, decides, remembers ("the road will pay for it") | name the people who act, or the physical fact | personification of things reads as a slogan; reader checks it |
| "would … within a season / year / month / week / day" as the consequence | name the consequence ("would have to move to find new fresh water") | the set's single promise formula; lint `within-span` |
| A fronted "If X" clause with no comma before the main clause; a contrasting "but" tail with no comma ("nothing for water and a great deal for beds") | "If the spring soured, the village…"; "nothing for water, but a great deal for beds" | British punctuation; lint `if-comma`, reader checks the *but* |
| "a root the story grew along is severed" | "a root is severed" | stranded preposition reaching for weight; cut to the image |
| "With this act, the very fabric of…" | name the actual thing | "the very" is always padding |
| "You feel a sense of unease wash over you." | "You are uneasy." / say what is wrong | telling the player their feelings, at length |
| Tricolons in system text ("the lost, the drowned, the forgotten") | one noun | the single loudest AI tell |
| "Perhaps… perhaps not." / trailing ellipses for mood | end the sentence | |
| "It is said that…" as an opener | say it, or attribute it to someone | |
| "…, which is the point / the problem / the whole story" as a sentence-final gloss | cut the clause; the fact already said it | the writer explaining its own image |
| `faintly / quietly / slightly / genuinely` + adjective as a mood formula | one plain adjective, or what happens | the hedge is the model reaching for nuance; at scale every place gets the same beat (46 in one region) |
| Adjective or abstract-noun tricolons in label fields ("callous, efficient, deeply resented"; "Contested reverence") | two beats, or one concrete fact | the tricolon rule applies to fragments; the third term is the reader's reaction |
| Design or pipeline voice inside world prose ("the reveal IS the beat", "per the two-culture kit rule", "the province's default dungeon", "band 5", "POI", "Owner decision Q2") | describe the place; put the decision in a decision record or a typed field | authorial rationale is not fiction |
| Game/session references in in-world prose ("where the game starts", "the first quiet the player gets") | describe the place, not the playthrough | |
| Sentence restated with an appended clause ("The seal leaks. The seal leaks, and the Waykeepers…") | write the long sentence once | a Phase 11 writer artefact, ~400 instances province-wide |
| Two stock phrases welded with an em dash ("worn but sound — everything load-bearing is new") | one clause | the dash doing the work a choice should do; often contradictory |
| Modern idiom no one in the world could hold ("unionised", "brute-forced", "ordinary until it isn't", "infrastructure", "leverage") | the plain word for the thing | |
| "X — the only such thing in the province" flourish after a concrete image | end at the image; uniqueness goes in a fact field | |
| Provenance markers inside world prose ("Canon:", "Canon-named as", "canon says") | state the fact; the citation goes in `sources` | design sourcing voice in fiction |
| A label field (`mood`, `condition`) restating the field above it, or a `hook` copying `siteAdvantages` | cut the echo; the hook says what the player gets | a writer artefact, four to eleven per region |
| "everyone knows X and nobody does Y" as a closer | end at "everyone knows" | the owner's named tell |
| A one-word address sentence in a greeting or bark ("Citizen.", "Friend.", "Traveller.") | fold the address into a sentence ("Mind the step, citizen.") | the bare word repeats across the province; the dialogue duplicate gate reds it |
| The same label-field SHAPE across a whole set ("adjective pair, and appended judgement" in 77 of 134 moods) | vary the shape between records | convergence is a set property; fix the set, not the line |
| Game or session references in `note` fields ("the game's first loss", "before the game does") | describe the thing | the in-world-prose row was being dodged via notes |
| Contrast joined with *and* where the sense is *but* ("The bridge is new and no one uses it") | use **but** — it is allowed and usually better — or cut the second clause | the model avoids *but*; see the and/but test in [research/text-and-voice/ai-writing-tells.md](../research/text-and-voice/ai-writing-tells.md) §5 |
| Sentence-final antithesis pair ("…the one thing everyone knows and nobody will talk about") | end at the first half | a balanced closer bolted to a finished sentence; the most distinctive AI beat in the Phase 11 catalogue |
| Negative parallelism ("it is not a shrine, it is a warning"; "not just a ford but a boundary") | say the true half only | ~3× more frequent in post-2022 web text (Pew); reads as machine contrast |
| Colon-reveal ("The garrison has one purpose: fear") | write it as a sentence | the colon doing a drum-roll |
| Question answered in the next clause ("Who guards it? No one.") | state it | rhetorical scaffolding, not speech |
| Register vocabulary: *delve, tapestry, testament, realm, intricate, interplay, underscore, pivotal, showcase, meticulous, landscape, foster, harness, navigate* | the plain word for the thing | the standard AI-vocabulary list; *tapestry* and *testament* are the loudest |
| Scene-setting defaults: *nestled, whispers, echoes, timeless, ancient* | one concrete noun ("a village on the sandbar") | unchecked, these open half the descriptions |
| Grandeur without specifics ("the fort's enduring presence") | a number, a name or an object | vagueness is a stronger tell than vocabulary |
| One-sentence paragraph dropped for punch | fold it into the paragraph above | |
| Constructions with a comma followed by 'and' | Avoid. Phrase differently. | British English convention. e.g. don't write constructions like e.g. "this name is important, and nobody will tell you why", or "the answer is wrong, and it changes the picture in an interesting way" |
| "has never once …", "not once …" | "has not …" or state what did happen | the emphatic negative absolute; a tell in its own right |
| "the one thing / the one place / the one stretch of road that …" | name the thing plainly; put uniqueness in a fact field if it matters | uniqueness flourish; 20 in one pass of the catalogue |
| "the only …" more than once in a record, or as a closer | say what it is; keep *the only* for a plain fact ("the only smith south of the lake") | overused to manufacture importance; density is the tell — the linter counts it per 1,000 words |
| "nobody ever …", "no one will say / explain …", "will not explain it", "has not been discussed" as a beat | a fact, or a person who does say | the withheld-secret beat; fine once, a tic at scale |
| **The flat and-pair**: a clause, *and*, then a second clause that turns the first into a wry shrug ("Trial-keepers set the route each year and will not explain it"; "The trial kills someone every few years and the tribes have decided that is correct") | split into two sentences, or drop the second clause, or make the second clause a plain fact that does not comment on the first | the second clause is the writer's *judgement* delivered deadpan; one per region is wit, one per record is a voice; style guide §2.6 has the diagnosis |

| Encounter scripting inside a `note` field ("fought one at a time if the player is quiet") | describe the people; staging belongs in typed fields | the session-reference row dodged via notes |
| `vibe.mood` as "adjective and undercutting-adjective" ("businesslike, with an undertow") | one word, or a plain fact | the antithesis pair in miniature; 46 of 140 in one region |
| A label that negates its own noun ("undressed stone, never dressed"), a trailing "…either", a simile-as-inheritance flourish | cut | set-level tells |
| **Trying too hard** — any sentence written to land: the tag-line turn on the reader ("So are you."), the portentous closer ("a machine no living engineer can read"), the epigram ("The pace-count is a song"), the pithy predicate ("whose entire livelihood is that the falls exist") | two plain sentences; end the record on a fact | the general class behind the and-pair, the antithesis and the colon-reveal; style guide §2.8 has the examples and the rules |
| Precision as emphasis: "exactly one", "exactly four", "only one", "one and only", "none of it", "none of them", "not one" | the plain number if it matters ("four expeditions", "this channel"), otherwise drop it | the successor tic to *the only* / *nobody*; *exactly N* and *only one* are hard linter rules |
| Repetition for effect ("the tree named … as the tree that stood") | say it once | a device, and a cheap one |
| A sentence or clause ending on a preposition ("the river Red Bramman escaped through", "dry enough to stack on") | "the river through which Red Bramman escaped"; "dry enough for stacking" | house grammar rule, all surfaces; hard linter rule |
| Rhetorical voice in a place record (address to the reader, a closer, a metaphor) | reference register: the voice of a wiki page about the place | place records are reference text, not dialogue; style guide §2.8 |
| "the total absence of X" as a `senses` closer ("the total absence of stone above knee height", "the total absence of any gate-bell", "the total absence of scavenger birds") | "no gate-bell anywhere"; or name what *is* heard | the sensory list ending on a grand negative; three in one region, always in the last slot |
| Design or session voice in a quest premise or `questHooks.opportunity` ("so a forged grade is a quest and a bad one is a war", "every beat points at…", "the pattern is the point", "paid for with what the player can already see") | describe the situation in the world | the session-reference row was being dodged via premises and opportunity fields |
| The quest-shape tail on `questHooks.opportunity` ("…, which is a delve with a market's stock at stake", "…so the ledge is evidence before it is a fight", "…worth a whole quest with no faction attached") | end at the situation; the quest's shape belongs in the quest row | eleven in one region; the writer explaining the quest's design inside world prose (soft linter rule `design-voice`) |
| A zero relative clause ("ground the surrounding tribes leave alone", "the house he lives in", "the name they gave it") | write the pronoun, or turn it round: "ground that is left untouched by the surrounding tribes", "the house in which he lives" | the contact clause reads as speech and stacks a second subject on the noun; style guide §2.8 rule 8 |
| Soft modern idiom for a plain fact ("leave alone", "put up with", "make do", "keep to themselves") | the concrete verb: "do not cross", "tolerate", "have no", "the ground is untouched" | idiom that a fourth-era Argonian would not hold, and vaguer than the fact (style guide §2.8 rule 9) |
| The verbless epigram ("Short tide, short ledger.") | a sentence with a verb ("The tide was poor.") | a proverb the writer invented; an epigram in miniature |
| The same verb twice in one sentence by accident ("returns stolen goods, then refuses to return captives"; "the hold holds cargo") | a different verb | reads as the repetition device even when it was not meant |
| `vibe.mood` or `vibe.condition` as abstract noun + wry qualifying phrase ("cheerful extortion, priced by the hull"; "hospitable, on a scale a size too large"; "temporary by design, used for years") | one plain word, or a plain fact | the antithesis pair wearing a comma; label fields are labels |
| The same image in two prose fields of one record (`signatureFeature` "the mound is longer than the village that made it" + `hook` "a grave mound longer than the village that dug it") | say it once, in the field it belongs to | the player reads both panels; a repeated image reads as a device (soft linter rule `field-echo`) |
| Oxford comma before the last list item ("reed, rope, and tar") | drop it: "reed, rope and tar" | British house style; half of the comma-and hits were this, not rhetoric |
| A one-word label field punctuated as a sentence for weight ("Still.", "Patient.", "Cold.", "Heavy." in `mood`) | lower-case, no full stop: "still" | the full stop is the flourish; a label is not a sentence |
| The whole `questHooks.opportunity` set built to one formula: a fact copied from the record, then "so a quest can X" (34 of 51 in one region) | state the opportunity alone ("A quest can audit the repair ledger"); vary the opening across the set | the hook-copies-siteAdvantages row applies to opportunity fields too, and here it had become the set's single shape |
| The concealed-arrival formula in `vibe.approach` ("You are inside it before you see it"; "you are on the ground before you can see it"; "you are in the village before you have entered a building") | say what is visible, and from where: "There is no line of approach; the first houses are overhead when you reach them" | seven records in one region used the same reveal beat; it is a set-level tell, not a line |

**Reader-only rows.** No regex can catch these; a `reader` or `voice-reader`
checks them by the tests in the
[research §5](../research/text-and-voice/ai-writing-tells.md). Each has a
fault, a fix and a ceiling: past the ceiling it is a finding on the set,
not a line edit. The ceilings are counted in words of the text under review
and are set from the Morrowind yardstick in
[corpus §10](../research/text-and-voice/morrowind-dialogue-corpus.md#10-what-the-corpus-shows):
greeting median 6 words, bark 3, topic 32, rumour 34; 3% of lines end on a
flourish and 93% on a fact or instruction; 67% of topic lines and 78% of
rumours carry a particular; contractions run 4% (Argonian, Khajiit) to 37%
(Redguard).

| Tell | Fault | Fix | Ceiling |
|---|---|---|---|
| Grand abstract nouns doing a concrete noun's work: *presence, essence, significance, legacy, spirit, weight* | "The fort's enduring presence still shapes the ford." | "The fort's garrison still takes a toll at the ford." | 1 per 500 words |
| The resonant closer: a line or paragraph that ends on a judgement written to land | "She keeps the ledger. Some debts outlive the debtor." | "She keeps the ledger. It is in the chest by the door." | 1 in 15 lines per batch (Morrowind: 3%, corpus §10) |
| Uniform sentence length | "The ferry crosses at dawn each day. The poler takes two drakes a head. The water is high this time of year." (8, 7, 8 words) | "The ferry crosses at dawn. The poler wants two drakes a head before you board. High water." | in any 4 sentences, the longest at least twice the shortest; greetings 4 to 10 words, barks 1 to 6, topic answers near 32 (corpus §10) |
| Bland politeness: everyone pleasant, no one blunt or unfair, nothing left unresolved | "Of course, friend. I would be glad to help you find the ferry." | "The ferry? Down the bank. Ask the poler, not me." | 1 in 3 speakers in a scene may be warm; at least 1 is curt |
| "Here's the thing" and kin: throat-clearing before content (*here's the thing, the truth is, it's worth noting, at its core, in a world where, make no mistake, let me be clear*) | "Here's the thing about the spring: it is souring." | "The spring is souring." | 0 |
| Stacked triads: three-part lists in successive sentences or lines, each third term a mood | "Root, water, silence. Egg, shell, memory. We keep them all." | "We keep the eggs in the shed and the tally by the tree." | 1 triad per 300 words, and never two in a row |
| Every line a hook: each line of a conversation ends on a tease or a withheld fact | "There is more to that ferry than you know." / "Ask me again after dark." | Most lines answer the question and stop: "The ferry runs at dawn. It costs two drakes." | 1 hook line in 10; at least 9 in 10 end on a fact or instruction (Morrowind: 93%, corpus §10) |
| Too tidy and too balanced: each claim answered by its counterweight in the same line | "The toll is harsh, but it keeps the road safe." | "The toll is harsh." (the defence goes to another speaker, or nowhere) | 1 balanced line in 5 |
| Emotional labelling: the text names the feeling instead of the cause | "He is clearly frightened of the vault." | "He will not walk past the vault door." | 1 per 500 words |
| Overuse of one word or image across a set (*root, tide, ledger, water, shadow* in every line of a speaker or place) | three lines of one speaker each built on *root* | one image per speaker per scene; the rest plain nouns | any content word (not a function word) above 1 per 200 words of a set |
| Slogan closer in a greeting ("For the museum.", "For the Marsh and its people.") | "Welcome, traveller. For the Marsh and its people." | "Mud on the step. Wipe your feet." (a plain fact the speaker would say at the door) | 0 banner lines; greetings stay 4 to 10 words of address and question (corpus §10.1) |
| Bland service politeness as a greeting ("How may I help you?", "What can I do for you?", "Good to see you. Keeping well?") | "How may I help you?" | "Ojel. The eels are two drakes each." (an address plus one concrete noun the speaker is holding) | at least 1 greeting in 10 carries a particular (corpus: 11%, §10.2); 0 stock service phrases |
| A set of greetings opening on one oath shape ("By <power>, ...") or one question shape ("X? Or Y?") | "By the roots, a stranger." / "By the roots, you again." / "By the roots, what now?" | vary the opener; drop the oath where it adds nothing: "A stranger." / "You again." | 1 opener shape in 5 greetings of a set |
| Mirror pair across standing tiers ("The way remembers you" / "The way forgets you now") | "The way remembers you." (friendly) / "The way forgets you now." (after a crime) | write the crime line as its own fact: "You stole from the poler. Find another boat." | 0 mirrored pairs across a speaker's standing bands |

**Dialogue set rows** (corpus read 1, `lanes/2.5/corpus-read-1.md`, and the
place panels). These are judged over a speaker's set or a whole place, never
one line.

| Tell | Fault | Fix | Ceiling |
|---|---|---|---|
| The speaker's trade prop in every slot | a stone-cutter's eleven lines each name a stone or a bucket | the prop in some lines; the rest speak of weather, kin, a neighbour, the road | the prop in 1 line in 3 per speaker |
| "Mind the [prop]" as the stock caution | "Mind the rope." / "Mind the bucket." / "Mind the step." across one place | one caution per place; others warn of a person or say nothing | 1 "mind the" line per place |
| One pun carried through a speaker's set | *hold* and *give* played on in 16 lines of a rope-seller | use it once | 1 use per speaker |
| One plot in one set of words across a place: the same fact verbatim from many speakers | six speakers at a ford each say "pay both" | give the fact to 2 or 3; the others have a grudge, a mistake, a refusal or ignorance | a pool fact in at most 3 mouths per place; 0 verbatim repeats of a claim across speakers |
| Every `about-X` gloss reassures | "No harm meant by it." / "Don't take it hard." from six speakers | one speaker glosses curtly, one is insulted, most do not gloss | at most 2 glossing speakers per place |
| The three-beat roll-call people answer | "Reesa mends nets. Teeka poles the ferry. Old Haj counts tolls." | one name with one fact, or "I don't know them", or a grievance | 1 roll-call per place |
| Address term on every greeting variant | "Traveller, the spring is cold." / "Traveller, back again?" / "Traveller." | "The spring is cold." / "Back again?" | the term on 1 greeting in 3; none for most Argonian speakers |
| The hospitable-host template: every base greeting is a service | 34 base greetings, each an offer of food, a bed or a boat | some greetings are curt, tired or hostile, as the pool's are | at least 1 greeting in 5 curt or hostile |
| One temper per state: night means shop-closed, high standing means "kept it back for you", crime means "off my X" | 15 of 34 night lines close the shop | vary the temper: tired, drunk, afraid, bargaining, silent | one stock form per state per place |
| Occupation as the only reason to deviate | every stance deviation is "because of the job" | deviations from temper, kin, creed or grudge | at least 1 deviation in 3 not from occupation |
| `place` topic answered with the speaker's chores | "I gut fish and mend the weir." for "Tell me about this place." | one concrete fact about the place per speaker, in some slot | 1 place fact per speaker |
| A formula opener on every answer | "Well, ojel, …" opening the greeting and seven answers | keep it on the greeting; start answers on the content | the greeting plus 2 answers per speaker |
| One image in most of a speaker's lines | *root* in 7 of 10 lines of one minder | one image per speaker per scene; the rest plain nouns | the image in under 60% of a speaker's lines |
| Flourish closers across a corpus | a pool batch where 1 answer in 6 ends on a judgement | end on the fact | 1 in 15 lines (Morrowind: 3%, corpus §10) |
| Barks that speak like topics | "The marsh remembers every footstep you take, stranger." as an idle bark | "Watch your feet." | 1 to 6 words, median 3; 1 bark in 100 carries a particular; 0 closers (corpus §10.1, §10.2) |
| One noun for a speaker: the trade noun in most lines (corpus read 2) | a smokehouse hand says "fish" in 10 of 10 lines | the noun in the base greeting and one answer; `place`, `people` and `rumour` name something else | 1 line in 3 per speaker |
| Directions that only deflect: the speaker's limit or a referral | "I have never poled it." / "Ask the carrier." | give the way: "Two bends up, then the left channel." | 1 directions answer in 5 per place deflects |
| A wry or balanced last sentence on an explanatory answer | "The keeper's office is unpaid, which means mine." | "The keeper's office is unpaid. I hold it." | 1 in 8 answers per speaker |
| "Kept back for you" on every high-standing greeting | "I kept the fattest fish back." / "I saved you a live trodh." / "Sit by me." | most high greetings curt, tired, or a trade point: "Eels are cheap today." | 1 in 5 high-standing variants per place |
| The Argonian emotional qualifier on every Argonian greeting | "I extend the claw of welcome." in three places | the plain greeting; the qualifier from one tribal speaker | 1 per place, tribal speakers only |
| *walker* as the province's address | an Imperial and an Argonian both say "Walker" | the zone's term (culture-registers §3.1) | *walker* only in Khajiit and Naga-camp mouths |
| A set with no short answers | 36 answers at a stage, none under 12 words | some answers are short; one speaker refuses, deflects or asks back | at least 1 answer in 4 at 12 words or fewer; 1 such speaker per place |
| Stance deviation reasons in design voice | "Doubts the elders (record lines); she is the one who is right." | "Doubts the elders since her brother drowned on their word." | 0 design-voice tags in a reason |
| Sheet contraction against the people norm | Riverwalk Argonians set at 0.35 to 0.65 | Argonians near 0.05 in every region; Western peoples 0.25 to 0.35 | an Argonian set above 1 contracted line in 10 |

**Mechanical floor:** `python3 -m worldgen.lint_prose` (from
`tooling/world-generation`) catches every phrase-level row above it can express
as a pattern — comma-and, never-once, the-one-thing, nobody-ever, the-very,
it-is-said, self-gloss, negative parallelism, register vocabulary, ellipses,
provenance voice, hedged-adverb formulas — and counts the density of *the
only*, *never*, the flat and-pair and the withheld-secret beat. It runs over
the place catalogue in `npm test` (`--strict`) and over any markdown you pass
with `--md`. It is a floor, not the review: the shape tests in
[docs/standards/text/review-process.md](../standards/text/review-process.md) §3 still run by eye.

## 46. Dialogue model

Most dialogue should use Morrowind-like text and topics:

- NPC-specific introductions;
- topic knowledge unlocked through conversation, evidence and faction rank;
- long-form testimony where the speaker has reason to provide it;
- short ordinary exchanges for daily life;
- regional rumours responsive to local state;
- documents, laws, contracts, letters, songs and oral histories;
- player responses that express position without inventing biography;
- race-sensitive reactions that never assume birthplace or guilt;
- generic voiced greetings/combat barks where suitable audio exists.

Avoid:

- every NPC delivering an encyclopaedia;
- identical exposition in several mouths;
- modern bureaucratic prose for all institutions;
- one developer-approved lore narrator;
- choices labelled as obviously good/evil;
- plot twists dependent on characters withholding facts for no reason.

## 46b. Voice — how a character is told apart in text

There is no full voice acting, so **the prose is the performance**. Who a
character *is* lives in [35-cast.md](35-cast.md); this is how they sound.

Every C1 and C2 gets a one-page voice sheet before any dialogue is written,
carrying exactly six things:

1. **Their four layers, named explicitly** — **race**, **upbringing**,
   **region** and **faction** ([text/culture-registers.md](../standards/text/culture-registers.md)
   §0). All four fields are mandatory, even when one is "none" (no faction) or
   "default for their race". A sheet missing a layer produces a character who
   defaults to the province's majority voice, which is the exact failure the
   layered model exists to prevent. Note here any deliberate departure from a
   layer, and why — the voice sheet outranks the layers, but only on the record.
2. **Sentence length and rhythm.** The cast's registers must not converge:
   Sings-Over-Stone corrects in clauses; Never-Writes-Twice speaks in finished
   sentences she could defend under oath; Spills-The-Ink starts twice; Ei-Tuja
   answers a different question than the one asked and it turns out to be better.
3. **Their one race marker, and how strong it is** (culture-registers §1).
   For an Argonian that is the Jel qualifier (§45b) and *which* one they reach
   for is characterisation — an office-hardened Argonian may have dropped them
   entirely when speaking to *ojel*, and that loss is worth a line somewhere.
   For a Khajiit it is how completely duty suppresses the illeism; for a Dunmer,
   which rung of *sera / muthsera / serjo* they use for whom.
4. **What they will not say.** Every character has one subject they change
   direction around, and the player can notice it long before they find out why.
5. **How they address the player** — and whether it changes across the game. This
   is where trust, rank and the branch state become audible without a meter.
6. **One repeatable formula** the player will recognise on sight after three
   meetings. Cheap, and it is most of what memorability actually is.

Additional rules:

- **No two characters in a scene share a register** — and where two characters
  *do* share a race, they must differ on at least one other layer (strong default — a
  deliberate shared register can be the joke; record the one-line reason). A
  scene with three grave people in it by accident is one character having an
  argument with itself.
- **A character's name form constrains their voice** (35-cast §54): a Jel-named
  interior elder and a translated-name city clerk should not be
  interchangeable in a blind read.
- **Comic characters carry real information.** Ei-Tuja and Sings-Over-Stone are
  funny *and* are the two people who tell the player what the Eye and the cult
  actually are. Humour is not a decoration on the texture tier.
- **C4 texture NPCs get one line of specificity and no worldview** (35-cast §59).

## 47. Staged scenes

Use staged scenes sparingly — for example:

- opening attack;
- first Helstrom arrival;
- key auction/heist moments;
- council;
- cult sermon;
- sap-dream/vision sequences (fog-dressed reuse of existing interiors; see the wonder budget in Section 4);
- Last Warden entrance;
- sanctuary confrontation;
- epilogue meetings.

Scenes should:

- use 2–6 active speakers where possible;
- remain fully comprehensible in text;
- survive an actor failing to reach a mark;
- permit player movement or a clean skip/recovery;
- avoid bespoke facial capture or one-off animation;
- use existing locomotion, gesture, combat and interaction animations.

## 48. Twist discipline

Every major twist must be:

1. seeded earlier;
2. reinterpretive;
3. actionable;
4. caused or suffered by a character/institution;
5. compatible with all player races;
6. implementable without a new art set or world simulation.

Principal main-quest revelations:

- the cult has a coherent grievance rather than generic madness — but it is met
  first as what it also truly is: a movement that kills trees, and with them
  eggs and the dead's way home;
- the woman from the opening attack and the voice in the dreams are the same
  person, and she is the end of the road;
- the Veiled Reed allowed or manipulated some evidence to identify the network;
- the cult leader once served the Veiled Reed — and designed the apparatus she
  now fights;
- the player's own handler falsified records, and the honest officer destroys
  her for it;
- the Root is a voluntary historical accord converted into compulsory authority;
- the Eye grants access/understanding, not automatic sovereignty — **but the
  throne is empty, and late in the game the player realises the claim is
  genuinely available to them**;
- both state custody and full severance impose choices on communities;
- the mend-and-walk-away ending exists only if the player has done difficult
  evidential and coalition work.

## 49. Fixed difficulty and quest guidance

Quests never inspect player level to substitute easier enemies or better loot.

They may inspect capabilities and knowledge to offer routes:

- water breathing;
- swim competence;
- climbing;
- lock skill;
- stealth;
- **speechcraft and standing** — the persuasion score (Speechcraft + Personality
  + evidence + standing) crossing an authored threshold, never a roll and never
  skill alone (world [76 §125](../world/76-stats-progression.md); speech is an ending-grade system here, so it belongs on this
  list);
- faction standing;
- spells;
- boat ownership;
- disease resistance;
- known fast-travel nodes.

Warnings are diegetic. A D4/D5 quest giver should describe route deaths, required supplies and available guides. The player can enter danger early and fail naturally.

## 50. Rewards

Rewards should be fixed and causal:

- faction equipment issued at rank;
- unique items belonging to named characters or sites;
- training, safe houses, ferry rights, rootworm access and legal permissions;
- fixed gold/valuable goods appropriate to employer;
- documents and knowledge;
- local service changes;
- reputation and sponsorship.

No reward quality scales to player level.

**The reward genres, and where the ladders live.** The genres proven by the
three reference games — signature gear at a named rank; a drip of unique
enchanted items roughly one per quest; economic access (fences, trainers, free
guild property, bounty relief); disposition and price effects; a capability
unlock; a salary with a strategy attached; a base built in phases; consumables
with a unique rule; a permanent change with real trade-offs; new abilities;
prestige gear and a title at the finale; and recognition that changes how the
world treats you — are catalogued with evidence in
[../research/quests-and-cast/tes-quest-and-faction-rewards.md](../research/quests-and-cast/tes-quest-and-faction-rewards.md).

Two structural rules taken from that research:

- **Rewards teach the fantasy.** A line's rewards must match its playstyle, the
  way thieves get fences and a cowl while mages get a crafting system. A faction
  whose rewards could belong to any other faction has been designed lazily.
- **One reward per quest is affordable** *if* items are re-materialled variants
  with distinct enchantments rather than bespoke models — which is exactly our
  no-new-art constraint. Oblivion's Dark Brotherhood is the model.

The main quest's four allegiance reward tracks — their DNA, five tiers each,
the stack-low/lock-high rule and the single phased stronghold — are specified in
[30-main-quest.md](30-main-quest.md) §24b.

