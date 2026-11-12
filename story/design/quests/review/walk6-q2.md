# Walk 6, lane Q2: the Chainbreakers' BC01 to BC03 at the ceiling

The Chainbreakers' first three quests re-authored as quest records at the walk 6 ceiling
([walk-6-quests](../../../../docs/phases/walk-6-quests.md)), each compiled to a quest form that passes
`python3 -m tools.questform check` and is off `story/data/questform_owed.json`. Records: `quest_record export
quest.bc.bc01` (and bc02, bc03). This file holds the quests' shape, each story call with its lore source, what was
cut, what the form could not say, the review, the paper playtest and the dialogue lines the re-authoring made untrue.

## The quests now

| Quest | Steps (stage: what the player does, at whom) | Endings |
|---|---|---|
| BC01 Four Months for a Boat | 0 ask Never-Sold for work in her house in Blackrose (she gives the Owing's first price, 100 gold); 10 speak to Rows-For-Another on the channel bank north of town: the buy-out (to 20) or, at Speechcraft 30, the channel (to 40); 20 pay Hulm-Tei the first price (to 31) or talk him round at Speechcraft 25 (to 30): he strikes her page and gives it; 30/31 give the page to Never-Sold; 40 tell Never-Sold she is going | 90 bought down, 91 slipped away, 95 failed (Never-Sold, Rows-For-Another or Hulm-Tei dead) |
| BC02 One Out of the Smoke | 0 ask Never-Sold once BC01 has ended well (she gives 100 gold); 10 talk Third-Born Tsaxi round at Speechcraft 25 (to 30) or pay him (to 31) at the heirs' stone house; 30/31 tell Tsaxi which of the three goes; 41/42/43 tell Never-Sold | 91, 92, 93 by who goes free; 95 failed (Never-Sold, Tsaxi or one of the three dead) |
| BC03 The Broker's Mercy | 0 ask Never-Sold once BC01 has ended well; 10 speak to Heavy-Rope on the Soulrest docks; 20 hear Ussa-Rekh; 30 tell Heavy-Rope whose side (crew: to 40; Ussa-Rekh: to 60); 40 talk Ussa-Rekh round at Speechcraft 30 (to 45) or pay him the crew's 50 gold, which Heavy-Rope gives (to 46): he gives up the tokens; 45/46 give them to Heavy-Rope; 60 talk Heavy-Rope round at Speechcraft 30 or pay 50 gold, or turn to the crew | 90 with the crew, 91 talked, 92 paid, 95 failed (Heavy-Rope or Ussa-Rekh dead) |

Every stage moves by a line the player picks; nobody walks; each person stands in one place for the whole quest. The
only switches are the endings' switch-offs (Rows-For-Another on the bank; the one freed at the stone house), each
caused by Never-Sold's line in her house, another cell. Nobody is essential; who must live fails the quest and, as a
faction line, shows the line's message. BC01's good endings set `flag.bc01.settled`, which gates BC02's and BC03's
start lines. Every check has a way round open to a new character: the coin for each payment is given by the person
who asks for it (Never-Sold, Heavy-Rope), and a player who keeps it by talking instead is told to keep it.

## What was cut, and what it became

| Quest | Cut | Became |
|---|---|---|
| BC01 | Never-Sold's walk to the landing | she stays in her house; the player reports to her |
| BC01 | the night-only, unseen channel line; the follow; the channel-end trigger box; the two estate men | Rows-For-Another talked into going now (Speechcraft 30); her going told to Never-Sold, who ends it |
| BC01 | the steward's locked chest and the theft of his book (Lockpicking, Sneak) | Hulm-Tei paid the first price or talked round on the custom that a first price closes an Owing (Speechcraft 25); he gives her struck page |
| BC02 | the burning stone house: smoke, the fire's enable states, the walk-in trigger box, the sneak past the gate, three exit boxes, the follow out, two held switched off in view, the second gate-keeper | the fire went through the Rose, where the player never goes; the three stand at the stone house; Tsaxi can count one lost to the smoke; the choice is three lines on him; Never-Sold's line ends it |
| BC02 | the sneak route into the post | Never-Sold's 100 gold (given at the start) |
| BC03 | the sides opened by a stored flag a line set; the chest; the theft of the tokens; the crew breaking them before him (told, never seen); the broker's 100 gold reward | sides opened by stage; Ussa-Rekh talked round or paid the crew's coin gives the tokens up; a crew holding its own tokens owes him nothing more; the broker's side moves standing and regard instead |
| BC03 | a start by stumbling on Heavy-Rope at Soulrest | Never-Sold sends the player, after BC01 |

**World edits left** (the forms' refs; the ledger rows `we.bc01.house`, `we.bc01.members`, `we.bc01.landing`,
`we.bc02.fire`, `we.bc02.gate` and `we.bc03.cabin` are deleted, the kept rows re-described): Never-Sold standing in
BM&V's House (15635D); Hulm-Tei and Rows-For-Another on the channel bank's navmesh (095465); Tsaxi and the three held
at BM&V's stone house (bmv_shell 1307CF, cell 0AFE4F); Ussa-Rekh and Heavy-Rope at the head of Dock2 (02F35A). No
thing placed, nothing built, no door changed. Positions are the old builder's snapped spots; the z values are
approximate and the builder resolves the spot from the anchor. To verify at build: Never-Sold's spot (520,-120) is
about 3,600 units from the House's door 15643F in a cell that holds two houses.

## Story calls and their lore

| Quest | Call | Source |
|---|---|---|
| BC01 | An Owing assessed in months of work for a damaged boat grows with food, upkeep and sickness, every line true | `story/lore/topics/labour-and-bondage.md` §2 (the Owing; the four drifts); `40-factions.md` §39 |
| BC01 | By custom an Owing paid at its assessed price is closed and never mentioned again | `labour-and-bondage.md` §2 |
| BC01 | An ex-Archein estate north of Blackrose, its steward and its Owing debtors | `story/lore/extrapolation/gap-register.md` QA3; `story/design/province-vibe.md` §9 |
| BC01 | She is grey from years away from her tree; free, she goes home to it | `labour-and-bondage.md` §2 (the tell); `40-factions.md` §39 |
| BC01 | She cannot drown in the channel | `labour-and-bondage.md` §1 |
| BC01 | Never-Sold buys out what an Owing first was, in coin | `story/design/quests/36-cast-roster.md` §56; `40-factions.md` §39; `province-vibe.md` §5 |
| BC01 | When one held runs, the estate's men are harder on the next one held | gap: the least inventive reading of QA3 |
| BC02 | A fire went through the Rose; the heirs keep three at their outer post until it is mended | `40-factions.md` §39 (the Rose's fire-damaged registers); `story/lore/topics/prisons.md`; QA4 |
| BC02 | The outer post is BM&V's stone house on Blackrose's east shore; the Rose is a day's march south | QA4 (updated in this lane) |
| BC02 | The three owe the heirs work by the heirs' own reckoning: for words, for a killing, for shelter | QA20 (updated in this lane); `labour-and-bondage.md` §3 (newcomers owe the prison-born) |
| BC02 | A gate-keeper answers to the heirs for the count and can put one short down to the smoke | `prisons.md` (the heirs' own hierarchy); `40-factions.md` §39 (the Rose's internal ledger) |
| BC02 | Never-Sold pays coin for the held and keeps every name | `36-cast-roster.md` §56; `province-vibe.md` §5 |
| BC03 | Ussa-Rekh bought out Owings for thirty years and hires out the crews he freed; he can say the year it turned | `36-cast-roster.md` §56; `labour-and-bondage.md` §3 (Soulrest's indentured crews) |
| BC03 | Carved tokens kept until the last season is worked; a crew holding its own owes him nothing more | QA21 |
| BC03 | Never-Sold in Blackrose sends the player to Ussa-Rekh at Soulrest | `36-cast-roster.md` §56 (the Chainbreakers' desks) |
| BC03 | Heavy-Rope and Ussa-Rekh settled by persuasion or coin on a port's docks | `province-vibe.md` §5, §9 |

## What the form could not express (re-authored around)

1. **One target per objective in the compiler** (`tools/questform/compile.py`, `targets: [self.use(target, ...)]`;
   the form allows several). With `completes-on-target`, every line or take that moves a stage must concern that one
   target: a stage cannot be moved both by taking a thing and by a hand-in line, and a choice between two people
   cannot sit at one stage. Re-authored: choices are several lines of one person.
2. **A container named only as a container is not emitted** (refs come only from what a stage, line, objective or
   trigger names), so `refs-exist` fails on the thing inside it.
3. **No owner and no lock level on a placed thing.** A thing on the ground is a free pickup, so a theft or a lock is
   no route that can fail (both reviewers blocked on it). Re-authored: every fetch is now given by its holder's line,
   for a skill or for coin. The cost: all three quests turn on Speechcraft or coin; Lockpicking and Sneak, the
   Chainbreakers' own skills, come back only when the form carries an owner and a lock level.
4. **An ungated fallback line at a gated start.** The compiler adds a condition-free line beside every gated mover,
   so Never-Sold's BC02 and BC03 start topics are offered at stage 0 before BC01 ends (their gist says "nothing yet").
5. `adaptation_check` predates the ceiling: its census has no `bmv_shell` rows, its Helgen rule reads "essential or
   protected" from the record's text, and its skill rule does not count a theft. Each was met honestly in the text.

## Review (quest-reviewer round 1, 2026-11-12)

Each record's `review.findings` holds every finding and its answer (`R<n>`); the blocking ones and how they were met:

| Quest | Blocking finding | Fix |
|---|---|---|
| BC01 | Stage 20 could not fail: the book at Hulm-Tei's feet was a free pickup (no owner in the form) | the theft cut; Hulm-Tei paid the first price from Never-Sold's coin or talked round (Speechcraft 25) gives the struck page |
| BC02 | The fire "two days before" while the held stand there from a new game | the fire is "before the player came to Blackrose" |
| BC03 | Stage 40 could not fail: the tokens were a free pickup | Ussa-Rekh talked round (Speechcraft 30) or paid the crew's coin gives them up |
| BC03 | The crew ending was an unseen breaking of the tokens before him | it ends on the hand-over: a crew holding its own tokens owes him nothing more |

High findings answered: BC01 the channel prompt named things not yet heard (now "Why wait? Leave now."), and nothing
said why the book mattered (the custom is now said); BC02 the start passed on BC01's failure (now `flag.bc01.settled`),
Never-Sold's brief was open throughout, one line per held person held three states (split by state); BC03 Never-Sold's
start line covered two states (gated; the compiler's fallback remains, item 4 above), no crews stand on Dock2 (the crew
are out on the boats), why the crew could not take the tokens (they are his to give). Kept and noted: the novelty
collision across the line (item 3 above); Keeps-The-Old-Count's name, also a Helstrom person's (a rename touches the
npc row and every written line: for the dialogue lane); stages that only report or hand over name no skill (each is
the report that lets a switch-off happen away from the player, or a hearing).

## Paper playtest (designed forms, before dialogue)

One `careful` player (Sonnet) per designed form, 2026-11-12, runs in `story/playtests/quest.bc.bc0<n>/`:

| Quest | Run | Path | What confused them | Changed |
|---|---|---|---|---|
| BC01 | `20261112T223237Z-careful-designed` (11 commands, 0 stalls) | 10, 20, 31 (paid), 90 | told to keep "whatever of her coin was left" when none was left | the keep-the-coin clause only on the talked route (stage 30 and her line); the buy-out line says why the Owing grew |
| BC02 | `20261112T223540Z-careful-designed` (11, 0) | 10, 31 (paid), 43, 93 | "will not pass to Rows-For-Another while she lives" | ending 93 and her line say she will see the mother's reckoning is never put on her daughter |
| BC03 | `20261112T223540Z-careful-designed` (14, 0) | 10, 20, 30, 40, 46 (paid), 90 | "the year it turned" said without the year's reason; the crew paying anyway | Ussa-Rekh's line and entry 30 say what turned; entry 46 says the crew's coin bought the season as if worked |

All three understood who asked, what for and where to go, finished without a stall, and named the placeholder lines
(the gists) as the main gap: dialogue is owed. The first BC01 run (`20261112T223037Z`) stopped on a harness error, the
story vocabulary's `speechcraft` unknown to the game's sheet; the game now reads the vocabulary's skill names as
Skyrim's (`SKILL_ALIASES` in `tools/playtest/game.py`, with a test). The runner stops when the first quest ends and
starts every run from a new game, so BC02 and BC03, gated on `flag.bc01.settled`, were played from copies of their
forms with that one condition dropped and a "what you know" text of BC01's bought-down path; the harness owes a way to
start a run from a later state.

## Dialogue lines now untrue or without a stage (for the dialogue lane)

Ids are the topic keys of `story/data/quest_lines/<code>.json` (every variant: `lines`, `lines@low`, `lines@high`,
and `fail` or `day` with theirs) and the keys of `quest_people.json`.

| Quest | Line id (variants) | Why |
|---|---|---|
| BC01 | `topic.bc01-the-estate` (3) | "I will meet you there", "Bring me the book", a locked chest; she now gives the first price and sends the player to Rows-For-Another |
| BC01 | `topic.bc01-bring-down` (3) | the book and coin left "in the steward's chest"; now the struck page, closed by custom |
| BC01 | `topic.bc01-cut-loose` (6, with `day`) | night, the estate men, "I will follow you"; the prompt is now "(Speechcraft 30) Why wait? Leave now." |
| BC01 | `quest_people.json` `ARG_BC01_EstateMan` (1) | the estate men are cut |
| BC02 | `topic.bc02-the-fire` (3) | the stone house "is burning"; the fire was in the Rose |
| BC02 | `topic.bc02-the-gate` (6, with `fail`) | lets the player into the burning house; now he agrees to count one lost to the smoke |
| BC02 | `topic.bc02-let-by` (6, with `fail`) | no stage: the walk out past him is cut |
| BC02 | `topic.bc02-come-speaker`, `-come-killer`, `-come-mother` (3 each) | no stage: "I will follow", "in the smoke"; the choice is made to Tsaxi |
| BC02 | `quest_people.json` `ARG_BC02_GateKeeper` (1) | the second gate-keeper is cut |
| BC03 | `topic.bc03-last-season` (3) | "with his chest beside him" |
| BC03 | `topic.bc03-the-season` (3) | points to Heavy-Rope "of the tokens", now cut from his line |
| BC03 | `topic.bc03-the-tokens` (3) | "in the chest beside him", "Bring them to me"; now he gives the crew's coin to get them from Ussa-Rekh |
| BC03 | `topic.bc03-break` (3) | "We will break them before Ussa-Rekh"; the ending is the hand-over |

15 ids, 50 variant lines. Still true and kept: `topic.bc01-the-book`, `topic.bc03-brawl`, `topic.bc03-yield-talk`,
`topic.bc03-yield-pay`. New topics to write (gists in the records): `topic.bc01-buy-out`, `-strike`, `-first-price`,
`-gone`, `-after-patron`, `-after-steward`; `topic.bc02-the-held`, `-pay`, `-free-speaker`, `-free-killer`,
`-free-mother`, `-held-<speaker|killer|mother>` with their `-going` and `-staying`, `-names-<speaker|killer|mother>`,
the five `-after-*` greetings; `topic.bc03-soulrest`, `-release`, `-buy-season`, `-after-rope`, `-after-ussa`.
