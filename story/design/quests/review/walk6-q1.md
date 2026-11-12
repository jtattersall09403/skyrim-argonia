# Walk 6: MQ04 (The Tree That Turned Its Face) and MQ05 (Helstrom Behind Its Marsh), re-authored to the ceiling

Written 2026-11-12 by lane Q1 of [walk 6 (quests)](../../../../docs/phases/walk-6-quests.md). The records are the
source (`python3 -m tools.argonia_world.quest_record export quest.main.mq04`, `... quest.main.mq05`); this note
records the story calls behind them with their sources, the dialogue that is now untrue, and what Act I hands on.

## MQ04 in steps

MQ04 starts when MQ03 reaches 90 (its completed ending), in Salts-The-Catch's house, where Nesh-Deeka has just said
that the Hist of Low-Reed Village has turned its face.

| Stage | The step | Its one target | What moves it |
|---|---|---|---|
| 10 | Speak to Hires-By-The-Season, the root-herald | her | her line (20); her death (21) |
| 20, 21 | Get the truth out of Pays-Late, the tree-minder, who stands by the Hist's roots and is blamed (Turns-The-Clutch, at the egg pool, tells of the boat and where the gum comes from) | him | talked round, Speech 25 (30); shown his gum pot, taken from the locked gum box at his feet, Sneak and Lockpicking (30); leaned on with the village's blame, no skill (31: his regard falls, and he will not offer to keep his secret) |
| 30, 31 | Take the jars of sap from the dry rise north of the leech water, out of the village's sight, where two of the cell stand hostile | the jars | the jars taken (fight One-Handed or any weapon, or Sneak past): 30 to 40, 31 to 41 |
| 40 | Bring the jars to Pays-Late, who puts the choice | him | three answers: give them and keep his secret (90); give them on his word that he tells the root-herald (91); keep them for the Reed (46) |
| 41 | The same, after leaning on him | him | two answers: on his word (91); keep them for the Reed (46) |
| 46 | Bring the jars to Nesh-Deeka in Lilmoth | her | the hand-in (92) |
| 90, 91, 92 | Completed endings; each starts MQ05 at 10 | | |
| 95, 96 | Failed: Pays-Late or Nesh-Deeka dead (the main quest's message) | | |

## MQ05 in steps

| Stage | The step | Its one target | What moves it |
|---|---|---|---|
| 10 | Tell Nesh-Deeka what happened at Low-Reed Village | her | her line, no check (20) |
| 20 | Take the coast ship from Lilmoth's stop and go ashore by its door to Helstrom's landing | the landing door 23D496 | the door used (40) |
| 40 | Tell Ei-Tuja, the Nisswo in the grove past the gate, who reads for anyone (two giant wasps stand on the way in: fight them or sneak past) | him | his line (92); asking for the tree-minder (45) |
| 45 | Talk Kaska-Meen, the tree-minder, round | her | Speech 25 (91); "I'll take this to the Nisswo instead" (44); her death (44) |
| 44 | Tell Ei-Tuja after all | him | his line (92) |
| 91, 92 | Completed endings: the tree-minders guard their trees, or the Nisswo preach it openly; either teller names the Mnemic Egg | | |
| 95, 96 | Failed: Nesh-Deeka or Ei-Tuja dead (the main quest's message) | | |

LQ25 still starts at MQ05 >= 40: stage 40 is set when the player comes ashore at the landing.

## The story calls

| Call | Source |
|---|---|
| BM&V's unnamed Village east of Lilmoth is Low-Reed Village, a tribal stilt village on fresh water with its own Hist, a root-herald who speaks outward, a tree-minder and an egg-tender | gap-register QA6; topics/hist-placement.md (Low-Reed Village); topics/material-culture.md (the offices) |
| The cell cut a root of the Hist, drew its sap into jars and sealed the cut with the village's own black gum; the eggs died of the cut and the tree turned its face | topics/hist-and-sap.md (Sap; Silence vs severance; Reproduction); MQ03's "long work, not a raid" |
| The leeches crowd the root because the sap weeps there; the village blames them and the tree-minder | gap-register QA11 |
| Pays-Late found the cut and hid it because the gum and the knife were his: the man the village blames is the one who knew the truth (the reversal kept from the 2026-11-06 design) | 30-main-quest §21 MQ04; topics/material-culture.md (tree-minder) |
| The two men on the dry rise wear the knotted cord, as the woman at the burnt camp did | MQ01 fact.mq01.her-face; 36-cast-roster §55 |
| The end is a choice of who keeps the sap: the tree's own keeper (with his secret, or with his word to own it), or the Reed as proof; the village's judgement of Pays-Late is left to the village | province-vibe §5 and §9 (the Reed's records are its trade); topics/material-culture.md; Morrowind's Fargoth's Ring (morrowind-level-scripting §2) |
| The Reed pays coin in Lilmoth | province-vibe §5 |
| hist-placement's Low-Reed row now says the jars go back to the root unless the player keeps them for the Reed, when the tree stays dark | changed with this rewrite (the row was extrapolated from MQ04) |
| The Reed sends a deniable hand alone to say at Helstrom what a cut Hist looks like, and is not named there | 10-political-frame §6; 36-cast-roster §55 |
| Helstrom is reached by river and root; BM&V's coast ship joins Lilmoth's stop to Helstrom's river landing; the way in is the marsh itself | topics/roads-and-routes-4e201.md; helstrom.md (the marsh is the wall); bmv_door 0AA837, 23D496 |
| Two giant wasps at a fixed level keep the way's far bend | topics/fauna-hazards.md; BM&V's Giant Wasp 166381; province-vibe §7; decision 0035 |
| Kaska-Meen, a tree-minder of the assembly, keeps a watch in the grove; Ei-Tuja, a travelling Nisswo, reads for anyone and preaches in villages | argonia-4e201-state §2.2; gap-register QA19, QA12; topics/sithis-nisswo-shadowscales.md |
| A silent Hist kills no clutch, a cut one does; tree-minders and Nisswo read a silence differently | topics/hist-and-sap.md (Silence vs severance) |
| A dying Hist leaves a Mnemic Egg, a seed of its sap holding its memories, once used by the Dominion to stop a generation of eggs hatching; the tellers name it as what a gatherer of sap might be after | topics/hist-and-sap.md (Mnemic Egg, CANON_EXPLICIT); the outline's MQ08 (the first plain sight of the Egg) |
| Showing Nesh-Deeka's page in Helstrom was cut: a Reed record in the interior (province-vibe §9) | review R1-2 |
| Cut from MQ05: the Scalded Throne's hall as a place visited, its seat, broom and name, the young Hist static | QA10 stays lore; the ceiling allows no structure added |

## What was cut, and what it became

- MQ04: the root-herald's leave and the salt fetch (a gate with no story) became her account of the village's blame;
  the dive to the root and its two trigger areas, the night watch and Pays-Late's night package became Pays-Late
  standing by the roots all day, asked three ways; the Hist statics switched dark and light, the camp's fire, tent and
  boat, the enable parents, the way-back leeches, the village's lodging and healing are gone; the pour at the root is
  told by the ending (Pays-Late pours it, off the page). The jars stand on the dry rise from the start, guarded.
- MQ05: Nesh-Deeka's Speech and gold check on the hand-over, the grove's trigger area, the wasps' enable parent, the
  levy warden's line, the hall, the throne and the grove's added Hist are gone; arrival is the landing door used;
  the choice between the two tellers is put through Ei-Tuja (who must live, so stage 40 always has its speaker), with
  Kaska-Meen behind a Speech check; the wasps moved down the way, 19,000 units from the grove and out of LQ30's gate cell.

## World edits left

- MQ04 (`we.mq04.people`, `.cell`, `.items`, `.name`, `we.clean.village`): three villagers standing; two cell men
  standing hostile on the dry rise (about 91000,-5100, out of the north huts' sight); the jars on the ground there; a locked lockbox at Pays-Late's feet holding his
  gum pot; the village's name. Removed from the ledger: `we.mq04.village`, `we.mq04.leeches`.
- MQ05 (`we.mq05.people`, `.way`, `.ship-door`, the cleans): Kaska-Meen and Ei-Tuja standing in the grove; two giant
  wasps standing hostile on the way (cell 0D776B); the ship's inner door pair, kept as built (the only way between the ship's
  Lilmoth door and its landing door; a door added, so it is the one edit outside "people, things, locks"). Removed:
  `we.mq05.grove`, `we.mq05.throne`, `we.mq05.hall-name`; the hall's merchants dropped from the needs.

## Dialogue now untrue or with no stage (for the dialogue lane)

Every written line of the old MQ04 and MQ05 keys a topic the records no longer have (37 `dialogue_line` rows):
`line.mq04-the-boat.turns-the-clutch.{default.00, speech.00-02}`, `line.mq04-the-cut.pays-late.{default.00-04,
item.00-02}`, `line.mq04-the-village.hires-by-the-season.{default.00-03, item.00-01, speech.00-02}`,
`line.mq05-tell-minder.kaska-meen.default.00`, `line.mq05-tell-nisswo.ei-tuja.default.00-02`,
`line.mq05-the-basin.the-levy-warden.default.00-01`, `line.mq05-the-quarrel.ei-tuja.default.00-02`,
`line.mq05-the-watch.kaska-meen.default.00-01`, `line.mq05-the-word.nesh-deeka.speech.00-04`. Also
`story/data/quest_lines/quest_people.json` entries `ARG_MQ04_HidesHisWake` and `ARG_MQ04_CountsTheJars` (2). Some
words can be kept under the new topic ids (the egg-tender's boat, Pays-Late's "the gum and the knife were mine",
Ei-Tuja's and Kaska-Meen's views); the root-herald's salt lines, the warden's basin lines and Nesh-Deeka's "the
fish-trader's house" are untrue now. The new topics are gists in the records.

## What Act I hands on to Act II

- Every player is in the Veiled Reed at rank 0, has Nesh-Deeka's page of the sap-dream, has heard of (not seen) the
  woman with the knotted cord, and has now seen her mark: two men of the cell on Low-Reed Village's dry rise wore the
  knotted cord.
- The player knows the cell cuts living Hist and draws their sap into jars for keeping, and asks the question every
  ending of MQ04 ends on: what does the cell want with jars of a living tree's sap? MQ05's tellers answer with a
  question that points at Act II: a dying Hist leaves a Mnemic Egg of its sap and memories, once used to stop a
  generation hatching; is that what the cell gathers sap for?
- The player stands in Helstrom's grove, past the wasps and the gate, having told Kaska-Meen (`flag.mq05.minders-hold`:
  the interior's tree-minders close their trees to strangers) or Ei-Tuja (`flag.mq05.nisswo-read`: the Nisswo
  preach it openly). Ei-Tuja is alive in every completed ending (his death fails MQ05); Kaska-Meen may be dead.
- Low-Reed Village: `flag.mq04.reconciled` (the sap went back to the root, 90 or 91) or `flag.mq04.jars-to-reed`
  (the Reed holds the jars as proof and the tree stays dark, 92). Pays-Late's regard is lower if the player leaned
  on him.
- The Scalded Throne's hall is not visited in Act I; the outline's Act I paragraph (lane S) still says the player
  "walked past the hall of the empty, swept Scalded Throne" and "Kaska-Meen and Ei-Tuja (one may be dead)": both are
  now untrue (the hall is not on the way; Ei-Tuja's death fails MQ05), owed a one-line change by whoever owns the
  outline next.

## Review (one quest-reviewer round each; the rows are in each record's `review`)

- MQ04, blocking: jars taken before stage 30 stick the quest (owed to the builder: a take trigger fires when its
  prerequisite stage starts with the thing already held, as MQ03's death case); the compiled form drops placements no
  line, objective or trigger names (owed to the compiler: emit every placements row; the cell men now have a placed
  line, the gum box and pot are still left out); hist-placement's "every ending" (fixed); journal 46 named the Reed,
  the lean prompt named the dead root-herald, t2 had the pot carried off, the camp stood in the north huts' sight (all
  fixed). High notes fixed: Turns-The-Clutch leads to the gum, journal 21, the knotted cord not shown, a reason for
  e-reed. Left: Pays-Late's and Nesh-Deeka's who-must-live rows hold for the whole quest (the form has no window).
- MQ05, blocking: Kaska-Meen dead before 40 left 40 with no way out (fixed: Ei-Tuja, who must live, is 40's target);
  the page shown in Helstrom (cut). High notes fixed: the wasps moved off LQ30's gate cell and away from the grove,
  the endings hand on the Mnemic Egg instead of repeating MQ04's question, the opening prompt, the argument with no
  scene. Left: the same choose-who-carries-it shape as MQ04's end (one target per stage), and no stage but 45 has a
  check (the wasps are the second way through).

## Paper playtests (designed forms; `--know` from MQ01's, MQ03's and, for MQ05, MQ04's journals)

Runs under `story/playtests/quest.main.mq04/` and `quest.main.mq05/`, names in `story/playtests/walk6-q1.names.json`.
All four finished with no stall and no harness error (MQ04 runs played on into MQ05).

- MQ04 careful: clear chain, liked the cut-tree mystery and the jars choice; leaning on Pays-Late "felt grimy"; the
  wasps never showed; could not tell whether the gum-pot route had worked. MQ04 impatient: easy to follow, wants to
  know what the cell does with the sap; "neither choice seemed to cost me anything". Changed: leaning now leads to
  stage 41, where Pays-Late no longer offers to keep his secret.
- MQ05 careful and impatient: short and clear (Nesh-Deeka, the ship, Ei-Tuja); the Mnemic Egg hook works; both say
  the warned wasps never appeared and the quest ends with no next objective. Not changed: the wasps are missing
  because the compiler drops placements nothing names (owed to lane A); the open end is Act II's to pick up.
- Both: the gists ("[not yet written; the gist:]") show; dialogue is the dialogue lane's.

## Tool faults met (for lanes A, H and K; not worked round)

- The compiler emits only refs a line, objective or trigger names, so hostile people, creatures and containers vanish
  from the form (MQ04's gum box and pot, MQ05's wasps).
- The paper game's take counts the placement's base id; a hand-in line checks the item id. MQ03's jar (base
  03EADD, item `thing.mq03.sap-jar`) can never be handed in on paper, which a MQ01 run on main hit. MQ04 and MQ05
  give a new item its own id as base id, which plays.
- The paper game cannot start a later quest with the items an earlier one gave (Nesh-Deeka's page), and models no
  lock levels or pickpocketing.
- A failed skill line shows its gated twin and a fallback with the same prompt twice in the menu.

## The dialogue and the paper players (lane D2a)

- **Stale lines gone.** The 37 old `dialogue_line` rows of MQ04 and MQ05 and the two `quest_people.json` entries of the
  cell men are removed; nothing of the old wording was still true of the new topics and standing places.
- **Written.** 102 lines in `story/data/quest_lines/mq04.json` and `mq05.json` (Pays-Late 34, Nesh-Deeka 23, Kaska-Meen
  13, Ei-Tuja 12, Hires-By-The-Season 10, Turns-The-Clutch 8, the two men on the dry rise 1 each), per speaker with
  dialogue-write (a Morrowind find step on every run), a fail wording for each checked topic, the echo check clean.
  The player's word for the cell is "the cutters" (MQ03's word) in every line, prompt and journal; a man on the dry
  rise names "the Root", left as a hook. Journals rewritten one step and why; objectives 20, 21 and 45 reworded.
- **Text review.** One reader pass over the lines by place, journals and objectives: 44 hits, 36 rewrites applied.
  Not applied: the fail rows' "sets stage" (an artefact of the review table), "is dead" journals (the register allows
  them), the closing question of the endings (kept as the Act's hook).
- **Record changes.** MQ05 stage 40's Archery use is `snipe` (the brief builder refused `fight`); the persuade and
  minder-wait labels follow the lines' prompts; MQ05 journal 40 says how each teller would carry the word.
- **Paper players** (`story/playtests/quest.main.mq04/20261112T2346*`, `T2349*`, `T2351*`; the same for MQ05): eight
  runs, no harness error. All could say what was going on (the cutters cut Hist roots for their sap; the Reed wants
  it known without its name), who wanted what, and what they want next (what the cutters want with the sap, the
  Mnemic Egg, why the woman with the knotted cord spared them). Changed after the first four: Kaska-Meen's greeting
  after the player chose Ei-Tuja (was "nothing to add"; now her side and its cost), the choice of teller foreshadowed
  by Nesh-Deeka and journal 40, Pays-Late's promised "who took the sap" topic now asks and answers where the sap went.
- **Still weak, outside the lines.** A failed check shows the success text and the same prompt twice (both
  confirming players were misled at Pays-Late and Kaska-Meen); the gum box, the pot and the wasps are missing from the
  form; MQ04's stages 40 and 41 both fire after leaning (two journal entries); every run ends with no next objective
  (Act II's); Nesh-Deeka and Hires-By-The-Season say the same after every MQ04 ending (a flag-gated wording needs a
  record change); give-truth asks Pays-Late to tell a root-herald who may be dead (stage 21's branch).
- **Tool faults met.** `quest-write/brief.py` refuses a hand-in or door stage as having "no skill action", though
  quest-write §3 exempts it (`moves_only` ignores `hasItem` and `flag`); `echoes.brief_section` crashes sorting a
  greeting's topic (None) beside MQ01's and MQ03's greetings. Both were worked round in a scratch runner, not edited.
