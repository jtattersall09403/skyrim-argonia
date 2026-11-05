<!-- imported unchanged from elder-souls-argonia docs/standards/text/style-core.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Style core: the reviewer's checklist

The rules a prose reviewer holds, in one file. Writers read the full
[style guide](style-guide.md); its sections and the
[banned-constructions table](../../quests/60-writing-and-lore.md) (§45e.1)
carry the evidence and the worked examples. Where this file and the guide
differ, the guide wins and this file is fixed.

**Scope.** Player-facing text is any string shown in the game or in any of
our apps: every record under `world/sources/` (place `why`/`vibe`/`hook`,
notes, quest rows, blueprints, routes, registries) and every string in
`packages/text-catalogue`. `docs/` is not player-facing.

**What you never change.** A fact, name, number, lore claim or typed field.
Note a doubt in the report instead. Never swap one device for another, never
apply the same fix across a whole set, and keep a speaker's voice.

## 1. House grammar

- British spelling: armour, colour, defence, realise, grey, learnt.
- No em dashes. Ellipsis is `…`, for hesitation in speech only, never mood.
- No Oxford comma ("reed, rope and tar"). No comma before a clause-joining
  *and*: split the sentence or rephrase.
- A comma before *but* that joins two clauses or a contrasting tail; a comma
  after a fronted conditional ("If the spring soured, the village would
  move").
- Single quotes inside a line. Stage and system cues in `[brackets]`.
- No sentence or clause ends on a preposition ("the river through which he
  escaped"). Phrasal-verb particles (*set off*) are fine.
- A relative clause keeps its pronoun (*that, which, who, where*): "ground
  that the tribes avoid", never "ground the tribes leave alone".
- Capitals for institutions, offices, unique places and coinages (House
  Redoran, the Hist, the An-Xileel); lower case for creatures, goods,
  materials and building types (guar, sap, xanmeer). If a hundred of them
  exist, it is lower case.
- One to ten in words; numerals above, and always for coin and counts the
  player tracks. "Drakes" in a mouth, "gold" in system text.

## 2. The linter's hard bans

`lint_prose` fails on these; read past them for the forms it misses.
`comma-and`, `final-preposition`, `zero-relative`, `if-comma`; `canon-marker`
("the player can hire"); `second-person` in records; `the-one-thing`,
`only-one`, `exactly-n`, `the-very`; `register-vocab` (*nestled, testament,
tapestry, intricate, delve, realm, pivotal*); `it-is-said`, `not-x-but-y`,
`self-gloss`, `ellipsis`; `feelings-formula` and `soft-idiom` ("quietly
resentful", "gets by", "leave alone"); `eat-figurative` ("a road that eats
iron"); `within-span` ("would move within a season"); `personified-thing`;
`nobody-somebody`; `rather-than`; `call-what`; `squashed-relative`.

## 3. The shape faults (what a phrase list cannot catch)

The diagnosis in one line: **a sentence doing more than stating its fact.**
For each sentence, ask what else it is doing; any answer is a finding.

1. **The closer.** A record ends on a plain fact. Read the last sentence
   alone: if it would work as a tag-line, replace it with the next fact.
2. **The flat and-pair.** A fact, *and*, then a clause that adds no new noun,
   only an attitude ("set the route each year and will not explain it").
   Cut the second clause, give it its own sentence with a person in it, or
   turn it into a fact. At most one per record, never in a `hook`.
3. **And for but.** For every *and* joining two clauses, ask whether the
   second contradicts or surprises the first. If so, it is *but*, or cut.
4. **Compression for impact.** Two facts squeezed into one clever sentence;
   a clause squashed into a noun phrase ("a column left unpaid at the
   recall hold a junction"); a fused object ("call what they take a levy").
   One fact per clause; write the second sentence. Length is not a fault.
   This is clause shape: in dialogue the second sentence makes the answer
   longer, never curter (§4).
5. **Precision as emphasis.** *Exactly one, only one, none of it, not one,
   never once, the one thing that.* State the number plainly if it matters,
   else drop it.
6. **The withheld secret, and the vague person.** "Nobody will say", "no one
   knows", "has never been explained". A fact, or a named person who does
   say. "Nobody", "somebody", "no one" and "someone" are not used in place
   records: write the sentence so they are not needed, by naming the role
   ("the ferry crews") or stating the fact ("the pool is not fished").
   Never swap in a stand-in ("anyone", "one").
   "Rather than" is rare too: at most once in a record, and a second use
   is a rewrite. Do not swap in "instead of" or "in place of"; state what
   is done and leave out what is not.
7. **Personified things.** Ports, roads, rivers, houses and the marsh do not
   pay, want, remember or wait. Name the people who act, or state the
   physical fact. Institutions may act.
8. **Antithesis and negation.** "Not a shrine but a warning"; "everyone knows
   and nobody says"; a colon reveal ("one purpose: fear"); a question
   answered in the next clause. Say the true half as a plain sentence.
9. **Tricolons and stacked labels.** "The lost, the drowned, the forgotten";
   "callous, efficient, deeply resented". One noun, or two beats.
10. **Repetition for effect.** A noun repeated inside a sentence, anaphora,
    the same verb twice by accident. Say it once.
11. **The turn on the reader.** "So are you." No sentence written to be
    quoted; no telling the player what they feel.
12. **Grandeur without specifics.** "Enduring presence", "ancient", "whispers",
    "timeless". A number, a name or an object instead.
13. **Metaphor budget.** At most one per record, and a marsh thing someone in
    the place could have said. No abstract metaphors; no figurative verbs on
    inanimate subjects.
14. **Design voice in fiction.** Pipeline, quest-shape or session words
    ("the reveal is the beat", "where the game starts", "a quest can",
    "Canon:") inside world prose or `note` fields. Describe the place.
15. **Echoes.** The same image in two fields of one record; a label field
    restating the field above it; a sentence restated with an appended clause.
16. **Set uniformity.** The same shape across a set (forty records as
    fact-image-closer; every `mood` an adjective pair with a twist). Vary the
    shape between records, not just the words. Uniform sentence length is a
    fingerprint too: let one sentence be four words and the next twenty.
17. **Modern idiom.** "Okay", "issue", "leverage", "infrastructure", "reach
    out", "ordinary until it isn't". The plain word a fourth-era speaker
    could hold.

## 4. Registers

- **Place records** (`why.*`, `vibe.*`, `hook`, quest premises, siting notes)
  are reference register: a UESP place page. Third person; present tense for
  the current state, past for history; concrete nouns and numbers; no
  device, no address to the reader, no closer. Test: could it be pasted into
  a wiki article without an editor flagging tone?
- **Label fields** (`vibe.mood`, `vibe.condition`) are one or two plain
  lower-case words or a plain fact, never a sentence with a full stop.
- **Dialogue** keeps its speaker's race, region and faction voice and its
  wit, but obeys every ban. Accent is marked by syntax and address terms,
  never phonetic spelling. Exclamation marks and ALL-CAPS emphasis at most
  once a scene; semicolons almost never. People talk the way Morrowind's
  people do: they spell things out, chat, describe and wander, each in the
  way their personality does it. Anyone may explain a thing in their own
  words, as helpful as their personality, faction and race make them; no
  one repeats another speaker's wording
  ([0143](../../old-decisions/0143-anyone-may-explain-restatement-is-near-verbatim-only.md)).
  Topic answers are written by the
  [dialogue-write](../../../.claude/skills/dialogue-write/SKILL.md) skill,
  which holds the rules, their measured reasons and the tells list; the
  `dialogue_style` and `dialogue_corpus` gates hold the numbers.
- **Books** may use semicolons and longer periods; they are not dialogue.
- Prose names a quest, person, place or item only when the same record
  carries its typed reference.

## 5. Fixing

Prefer, in order: split into plain sentences; cut the flourish; swap the
device for a number, name, object or direction. A dull sentence is a
correct sentence. Write the rewrite, never only the critique.
