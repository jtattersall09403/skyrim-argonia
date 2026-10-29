<!-- imported unchanged from elder-souls-argonia docs/standards/text/culture-registers.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Speech registers — the layered model

> **A speaker's voice is composed, not looked up.** There is no "the register
> of region X". Argonia holds all ten Tamrielic races in the proportions given
> by [world/92 §82](../../world/92-demographics.md), and they do not all talk like
> Argonians. Read §0 (composition rule) plus **your speaker's four rows**:
> one race row, one upbringing row, one region row, one faction row.
> Universal rules are in [style-guide.md](style-guide.md); the individual is
> the voice sheet (quests 60 §46b). Router: [README](README.md).
>
> **Why layered:** Morrowind's own dialogue engine filters every line by Race,
> Class, Faction, Rank, Region/Cell and disposition at once — the game composes
> a voice from conditions instead of storing one voice per town. Evidence and
> quoted lines: [research/text-and-voice/speech-register-model-morrowind.md](../../research/text-and-voice/speech-register-model-morrowind.md).

## 0. The composition rule

```
voice = RACE markers (§1) + UPBRINGING (§2) + REGION idiom (§3) + FACTION vocabulary (§4)
        + the individual's voice sheet (quests 60 §46b)
```

**Precedence when two layers conflict:**

1. **Faction wins on duty, for the words the institution owns** — forms of
   address, procedure nouns, how an order is phrased. A Khajiit legionary says
   *citizen* and *by the authority of the Cordon* because the Legion issues
   those words to everyone who wears the cuirass.
2. **Race markers survive underneath, at reduced strength.** Duty suppresses a
   habit; it does not delete it. The same legionary still slips into illeism
   off duty, when angry, or when speaking to another Khajiit — and *that slip
   is the characterisation*.
3. **Region supplies subject matter and place words to everyone**, whatever
   their race or faction, if they live there. It rarely fights the other
   layers; it fills them.
4. **Upbringing beats birth race** wherever the two disagree. A Dunmer born in
   Thorn is a Thorn speaker with Dunmer habits, not a Morrowind speaker.
5. **The voice sheet beats all four** for a named C1/C2. Layers are the default
   a character is written *against*; a deliberate exception is characterisation
   as long as the reason is recorded on the sheet.

**Moderation is the rule and overuse is the failure mode.** At most **one race
marker per scene per speaker**, never in every line. A register is a
seasoning, not a costume.

**No phonetic accent, ever. No broken grammar to mark a race**
(style guide §1.6). Morrowind marks no race by spelling errors. Every marker
below is syntax, address terms, or subject matter.

**Formality is a layer of its own: contractions follow the person.** Each
layer pushes formality up or down, and the voice sheet settles it. Up: an
institution on duty (§4), a devout or priestly speaker, a cold disposition,
the race rate below for Argonians and Khajiit. Down: a chatty or rambling
`chatter`, manual or trade work, a warm disposition, the coast and fringe
idiom (§3.1). A chatty beach buyer says "I'm", "doesn't", "it's"; a temple
clerk may say "I am". "Does not" and "I am" in an informal mouth is the
machine tell (style guide §2.9).

**A register sets clause shape, never answer length.** "Short main clauses
joined by *and*" or "the shortest thing that can be shouted" describes how
each clause is built; a pirate still explains a ford in thirty words of
short clauses. How much a person says is the voice sheet's `chatter`
(`terse`, `plain`, `chatty`, `rambling`) and its `answerLength` bands
(style-core §4). The numbers every layer writes to:

| measure | target |
|---|---|
| topic answer, median per place | local and role 22 words or more; rumour 25; newcomer and faction 28 |
| terse speakers | at most a quarter of a place |
| contractions | Argonian and Khajiit: at most 4 percent of answers contract (Morrowind's rate for both; the writer plan shares a place's allowance, so most of them contract in none); everyone else 6 or more per 100 words |
| answers that ask or aside to the listener | 1 in 12 or more |
| sentence length | varied, standard deviation 5 words or more per place |

---

## 1. RACE layer — what a speaker keeps anywhere in Tamriel

Applies to a speaker of that race *whatever* region or faction they are in.

| Race | Marker (use one at a time) | Anchor |
|---|---|---|
| **Argonian (Saxhleel)** | Jel has no past or future tense and carries grammar in body language, so Tamrielic comes out prefaced by an **emotional qualifier**: *"I erect the spine of…"*, *"I extend the claw of welcome, warrior."*, *"My rage-quill is engorged!"* Farewell **"Stay moist."**; curse **"Hist piss!"**; exclamation **"Host of Stormhold."** Outsiders are **ojel** (neutral). Formal, guarded, deflecting about their own culture: *"we have always been a private, even secretive people…"* | **Morrowind:Huleeya**; lore topics/material-culture.md, `CANON_EXPLICIT` |
| **Khajiit** | Third-person self-reference (illeism) — *this one*, or their own name — present tense, few contractions. **Not absolute**: a group takes "we"; educated or long-settled Khajiit drop it under pressure of business | **Morrowind:Ajira**, **Morrowind:Sugar-Lips Habasi** |
| **Dunmer** | The honorific ladder **sera / muthsera / serjo** (peer / respected superior / lord) — who uses which for whom is the fastest status information in a scene. Abstract honour-nouns in formal mouths; the loan-slurs *n'wah*, *s'wit*, *fetcher* in coarse ones | **Morrowind:Bolvyn Venim**, **Morrowind:Ghost-Free Papers**, **Lore:Profanity** |
| **Imperial** | Officialese: procedure recited neutrally, legal vocabulary, nominalisation, deniability. Also the colonial commentator — contractions, sarcasm, confident wrong opinions about native custom | **Morrowind:Dumbuk gro-Bolak**, **Morrowind:Larrius Varro**, **Morrowind:Eldafire** |
| **Nord** | Short declaratives, no hedging, an oath or a blunt boast where another race would qualify; drink, weather and cold as reference points. Refuses euphemism — the opposite pole to the Imperial clerk | `LORE_INFERRED` (research §2) |
| **Orc (Orsimer)** | Directness with no apology attached, plain contract language (a job is a job and a debt is a debt), oath and blood vocabulary used literally, not poetically. Often *more* correct and formal than expected — an Orc legionary out-procedures the Imperials | **Morrowind:Dumbuk gro-Bolak**; `LORE_INFERRED` |
| **Bosmer** | Fast, familiar, wry; nicknames the player early; food, meat and the forbidden-plant edge as running subject; light on ceremony and heavy on the concrete | `LORE_INFERRED` from Morrowind Bosmer greetings |
| **Breton** | Educated hedging — *perhaps*, *one might say* — courteous qualification, arcane or contractual precision. The race most likely to say a hard thing politely and at length | `LORE_INFERRED` |
| **Redguard** | Terse and proverbial; a saying where an argument would go; sword, sea and ancestry as the metaphor stock; pride expressed as understatement | `LORE_INFERRED` |
| **Altmer** | Precise diction, complete clauses, no contractions, condescension worn as courtesy; corrects the terms of a question before answering it | `LORE_INFERRED` (research §2) |

Where a row is `LORE_INFERRED`, a better in-game line found later should replace
it — record the page in [99-sources](../../world/99-sources.md).

---

## 2. UPBRINGING / CULTURE layer — who raised them, and when

Applies across race. This is the layer that stops "all Dunmer sound alike".

| Upbringing | What it does to the voice |
|---|---|
| **Marsh-raised (any race)** | Jel-shaped *word order* and marsh subject matter without the Argonian qualifiers: tide, egg, root, season, the Hist named casually as furniture. A third-generation Argonia-born Dunmer **speaks better Jel than Dunmeris and knows it** (35-cast §54) |
| **Newcomer (any race, <10 years)** | Explains Argonia to the player. Explains it **badly**; exonyms for places the locals name in a verb-clause; asks questions a resident would not need to ask |
| **Argonian, tribal / interior-raised** | Qualifiers at full strength; address by category, not name; proverb-and-riddle mode |
| **Argonian, city / port-raised** | Qualifiers worn smooth by daily contact with *ojel*; complete sentences, practical imperatives |
| **Lukiul (assimilated Argonian)** | **Cannot use the qualifiers naturally and it shows** — either omitted entirely or used one beat late. *Lukiul* is the An-Xileel's slur, so hearing it applied is an event |
| **An-Xileel-era (raised after the rise)** | Political certainty; invitation in place of threat; the province as a settled fact, not a contested one |
| **Older generation (remembers the Empire / the Accession War)** | Provisional phrasing about the state; Imperial place-names used out of habit and corrected by the young |
| **Slaver-descended / freed-descended (Dunmer and Argonian both)** | The subject both sides route around. Neither says it plainly; each says it differently |

---

## 3. REGION layer — the eight zones, for anyone who lives there

These are the same eight zones as the place catalogue's naming register
([world/sources/catalogue/README.md](../../../../world/sources/catalogue/README.md)),
so how a place is *named* and what its people *talk about* stay in agreement.
**A region row is idiom and subject matter, not a race.** An Imperial fisher in
`saxhleel-coast` uses the coast's words; a Khajiit smuggler in
`imperial-penal-south` knows the cordon's paperwork by name.

| Zone | Local idiom and place words | What people here talk about | Avoid |
|---|---|---|---|
| `hist-heartland` | Short main clauses joined by *and* / *but*; near-total absence of subordination (**Morrowind:Nibani Maesa**). Naming and gift-giving are **performative** — a status conferred in a sentence binds (**Morrowind:Sul-Matuul**). Proverb mode, lowercase and unpunctuated, only when the riddle *is* the information | Root, tree-health, season, who is owed what; outsiders as a category | Imperial abstractions, legal vocabulary, "perhaps" |
| `naga-kur-deeps` | **Menace written as hospitality** (**Morrowind:Dagoth Gares**) — courteous delivery, appalling content, never a snarl. Liturgical parallelism and noun-stacking (the one licensed tricolon exception, in a mouth only). Counts and stakes as imagery | Rite, flesh, tally, what the deeps are owed. Rite-keepers ceremonial, raiders corporeal (**Morrowind:Anhaedra**) | Spelled-out hissing, cackling, broken grammar |
| `saxhleel-coast` | Practical advice given imperatively; verb-clause place names used unselfconsciously | Tide, catch, wrecks, passage, safety on water | Grandeur — the coast is competent, not mystical |
| `mercantile-coast` | Transactional euphemism: difficult things become *business*, an *accommodation*, "a... trivial matter" (**Morrowind:Odral Helvi**). Prices in **drakes**. Two naming systems side by side. The seam is audible | Cargo, licence, who is late paying, whose quarter is whose | Open threats — a mercantile threat is a scheduling problem |
| `pirate-freeholds` | The shortest thing that can be shouted across water. Elision and contraction; mixed-crew loan-slurs. **Criminality by omission** — what is not said is the characterisation | Weather, shares, the next hull, who is ashore | Ceremony, long sentences, "arr" |
| `imperial-penal-south` | **The manual page in a mouth**: procedure recited flatly, including when monstrous — *"Outlaws have no rights, and may be killed without scandal or sanction."* (**Morrowind:Dumbuk gro-Bolak**). Deniability as a genre (**Morrowind:Larrius Varro**). Passive voice and nominalisation are permitted **here and nowhere else** | The ledger, the Owing, sentences, transfers, what the paperwork will bear | Officers written as straightforwardly villainous; several must be decent people running a bad instrument |
| `imperial-fringe` | Modern speech: contractions, sarcasm, rhetorical questions, moral commentary on native custom that **the game does not correct** (**Morrowind:Eldafire**). Chivalric vocabulary for the soldiery, kept plain (**Morrowind:Varus Vantinius**) | Harvest, roads, the border, whether any of this was worth it | Colonials written uniformly as bigots; a settler who knows more about the Hist than the player |
| `dunmer-north` | Two modes in one zone. **Redoran**: full sentences, abstract nouns, contempt delivered formally (**Morrowind:Bolvyn Venim**). **Telvanni**: fast, elliptical, fragmentary, amoral because power is assumed (**Morrowind:Divayth Fyr**, **Morrowind:Aryon**) | Plantation, ash, lineage, the crystal trade, the war two centuries back | Treating residents as visiting Morrowind Dunmer — two centuries without an Empire happened to them too |

### 3.1 Address, vocabulary and formality per zone

The research names address terms, formality and vocabulary as the carriers
of a voice ([research, How we use it](../../research/text-and-voice/speech-register-model-morrowind.md#how-we-use-it)).
This table gives each zone's defaults. The region culture sheets
(`world/sources/dialogue/cultures/regions/`) point at these rows through
`speech.registerRef` and hold the zone's oaths, never-said list and talk.
Formality is the sheet's enum: `low`, `plain`, `formal`, `ceremonial`.

| Zone | Stranger is called | Peer or superior | Formality | Vocabulary it owns |
|---|---|---|---|---|
| <a id="region-hist-heartland"></a>`hist-heartland` | *ojel*, or by errand: courier, tapper | by office: minder, naheesh | ceremonial | root, pocket, owing, Root Talk |
| <a id="region-naga-kur-deeps"></a>`naga-kur-deeps` | guest, or by what he carries | by the hunt shared | ceremonial | tally, stake, cut, the Lily |
| <a id="region-saxhleel-coast"></a>`saxhleel-coast` | by boat or errand | by the lot dived | plain | lot, fathom, stroke, tally book |
| <a id="region-mercantile-coast"></a>`mercantile-coast` | friend, until he owes | by house or hull | plain | drakes, licence, berth, accommodation |
| <a id="region-pirate-freeholds"></a>`pirate-freeholds` | mate, until he is trouble | by job or nickname | low | roll, share, hull, landing |
| <a id="region-imperial-penal-south"></a>`imperial-penal-south` | by status: debtor, holder, transferee | by family and generation (Rose-born) | formal | balance, transfer, list, carriage charge |
| <a id="region-imperial-fringe"></a>`imperial-fringe` | citizen, sir, madam | serjeant and the old ranks (Legion heirs) | plain | title, milestone, well, harvest |
| <a id="region-dunmer-north"></a>`dunmer-north` | *ojel* (Argonian), *sera* (Dunmer) | *muthsera*, *serjo* up the ladder | formal | field, title, egg record, toll |

Formality per layer: race and upbringing do not set formality alone. The
faction layer sets it on duty and the region row sets it off duty; a voice
sheet may move it one step either way with a recorded reason.

Who owns *walker*: it is a Khajiit word for a traveller. The Naga camps
take it from Khajiit traders. Only Khajiit sheets and the Naga-camp
groups use it. Everyone else addresses a stranger by their zone's term
in the table above. Fault: an Imperial ferryman says "Walker, the ford is
up." Fix: "Citizen, the ford is up." Ceiling: no *walker* outside those
sheets.

Contraction rate is set by the people layer, not by the region. Argonians
and Khajiit almost never contract in any zone: Morrowind contracts about
4 percent of their lines, so a place's Argonian answers, and its Khajiit
answers, each contract in at most 4 percent of them, rounded up. Other peoples contract 6 or more times per
100 words, as speech does (§0 table). Fault: a Riverwalk Argonian with
"Ford's high, I don't cross, it's not mine to cross" because the zone
is Dunmer. Fix: "The ford is high this week. I do not cross it. I would
not send you over either." Fault the other way: an Imperial clerk
with "I do not know. It is not my post." Fix: "I don't know, and it isn't
my post to know."

Address-term families per faction (pool greetings): each faction owns one family, so no two collide. *citizen*: An-Xileel; *civilian*: Legion remnant; *friend* or none: Legion-descended; *guest*: Bright-Throat; *outsider*: Naga-Kur; *neighbour*: Stillrise; *grower*: Thorn-Ash-Reed Accord; *delegate*: League of Open Water; *colleague*: College of Whispers; *agent*: Cyrodilic Collections; *muthsera*, *serjo*: Dres remnant; *root-kin*: Many-Root; *root-sibling*: Unbound Root; *friend of the roots*: Root-Whisper; *stone-kin*, *Reed-folk*: Xit-Xaht; *traveller*: Rootworm Waykeepers; *seeker*: Nisswo; *pilot*: Reed-Sail; *mate*: Salt-Teeth; *reed*, *water-rat*: Night Reed; *blade*, *captain*: Marsh Charter; *hunter*: Murkwater; *offering*: Sul-Xan; *reader*: Sunken Archive; *attendant*: Synod; *soft-skin*: tribeless Naga; *witness*: Umbriel; *young one*: Shadowscales; *brother*: Blackguards; *sibling*: Chainbreakers; *friend*: Veiled Reed; *comrade*: Morrowind veterans (their sheet's address; never *sera*). Peoples keep their own words (Argonian *ojel*, Dunmer *sera*, Bosmer *Longshanks*, Khajiit *walker*); outsiders are named by homeland or role, never *outlander* or *stranger* in Black Marsh lines.

---

## 4. FACTION / CLASS layer — the words an institution issues

Applies to **every** member regardless of race. It governs on-duty speech.

| Institution | Imposed vocabulary and address | Anchor |
|---|---|---|
| **Imperial Legion / cordon guard** | *citizen* to the compliant, the suspect's status-noun to the rest; four-word idle barks; orders as regulation numbers; honour/oath/duty kept plain | **Morrowind:Ordinator**, **Morrowind:Varus Vantinius** |
| **The Owing (penal administration)** | Debt and ledger nouns for people; sentences described as balances; the passive voice carve-out | region row `imperial-penal-south` |
| **Nisswo / Sithis clergy** | Doctrinal, numbered structures, one mandatory formula used every time (Morrowind's "(Blessed Be Their Holy Names)"). Preaching *shunatei* is consolation, not callousness (quests 60 §45c) | **Lore:The Anticipations**, **Morrowind:Tholer Saryoni** |
| **Shadowscales** | Understatement. Divinity and killing both written small: *"When I was young like you, I was very impatient. So I will keep our business short."* | **Morrowind:Vivec (god)** |
| **The An-Xileel** | Political certainty; *lukiul* as a weapon; invitation in place of threat | **Morrowind:Sleepers Awake** |
| **East Empire Company / chartered trade** | Contract nouns, tonnages, "the Company" as a person; complaint routed as procedure | `mercantile-coast` row |
| **Smugglers and free crews** | Trade in euphemism (*cargo*, *passengers*); names withheld; a question answered with a different question | `pirate-freeholds` row |
| **House Dres remnants** | Antique legal formality about property, applied to people, by speakers who no longer have the law behind them | **Morrowind:Bolvyn Venim** (register), `LORE_INFERRED` (Dres in 4E 48) |
| **Class-conditioned (any faction)** | Guard, commoner, noble and scholar greet differently within one race — the shortest, cheapest variation available and the one most often forgotten | **Morrowind:Generic Dialogue** class filter |

---

## 5. Worked examples

Same region, different composition — these must be sortable in a blind read.

| Speaker | Race layer | Upbringing | Region (`imperial-penal-south`) | Faction | Resulting line |
|---|---|---|---|---|---|
| **Khajiit legionary** | illeism, suppressed on duty | Elsweyr-born, 12 years in post | cordon procedure nouns | Legion: *citizen*, regulation numbers | "Citizen, the transfer list closed at dusk. [Pause.] This one will look again, though the entry will not have changed." |
| **Khajiit outlaw** | illeism at full strength | port-raised, no Legion | same ledger words, used as a threat to *avoid* | smuggler: euphemism, omission | "This one carries passengers. The ledger has its own word for them. Does the ledger ask about Khajiit?" |
| **Imperial legionary** | officialese, legalism | Cyrodiil-born newcomer | cordon procedure nouns | Legion: same forms of address | "Citizen. The list closed at dusk. The prefect reopens it at eight most mornings." |

Same market in Thorn, different races:

| Speaker | Resulting line |
|---|---|
| **Argonian stallholder** (marsh-raised, no faction) | "I extend the claw of welcome. The eels came up short this tide. Two of them are yours for the price of one. Stay moist." |
| **Dunmer counting-house clerk** (Thorn-born, third generation, EEC) | "Sera. The tide was poor. The Company will want the ledger written up regardless. That name lives in Company ledgers; the stalls use the old one." |

Note what the second speaker does *not* do: she has no Morrowind nostalgia; her
Jel is better than her Dunmeris (36-cast, Dravyna Andalen). Her Dunmer layer amounts to the word *sera*.

---

## 6. The convergence test

The failure this document exists to prevent is **the whole province growing one
voice** — historically, the Argonian one, because the province is
Argonian-majority and the register file used to assume it. At every phase wrap
the reviewer reads the phase's dialogue with speaker IDs hidden and sorts it by
**race and by region** ([review-process.md](review-process.md) §3.4–3.5). If
either sort fails, the layers above were not used.
