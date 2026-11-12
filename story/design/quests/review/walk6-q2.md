# Walk 6, lane Q2: the Chainbreakers' BC01 to BC03 at the ceiling

The Chainbreakers' first three quests re-authored as quest records at the walk 6 ceiling
([walk-6-quests](../../../../docs/phases/walk-6-quests.md)), each compiled to a quest form that passes
`python3 -m tools.questform check` and is off `story/data/questform_owed.json`. Records: `quest_record export
quest.bc.bc01` (and bc02, bc03). This file holds each story call with its lore source, what was cut, the review, and
the dialogue lines the re-authoring made untrue.

## The quests now

| Quest | Steps (stage: what the player does, at whom) | Endings |
|---|---|---|
| BC01 Four Months for a Boat | 0 ask Never-Sold for work (her house, Blackrose); 10 speak to Rows-For-Another at the estate landing and choose: the buy-out (to 20, or to 30 if the book is already held) or, at Speechcraft 30, the channel (to 40); 20 take the debt book from beside Hulm-Tei; 30 give it to Never-Sold; 40 tell Never-Sold she is going | 90 bought down (book), 91 slipped away (channel), 95 failed (Never-Sold or Rows-For-Another dead) |
| BC02 One Out of the Smoke | 0 ask Never-Sold once BC01 has ended (she gives 100 gold); 10 talk Third-Born Tsaxi round at Speechcraft 25 (to 30) or pay him 100 gold (to 31) at the heirs' stone house; 30/31 tell Tsaxi which of the three goes; 41/42/43 tell Never-Sold | 91, 92, 93 by who goes free; 95 failed (Never-Sold, Tsaxi or one of the three dead) |
| BC03 The Broker's Mercy | 0 ask Never-Sold once BC01 has ended; 10 speak to Heavy-Rope on the Soulrest docks; 20 hear Ussa-Rekh; 30 tell Heavy-Rope whose side (crew: to 40, or 45 if the tokens are held; Ussa-Rekh: to 60); 40 take the tokens from beside Ussa-Rekh; 45 give them to Heavy-Rope; 60 talk Heavy-Rope round at Speechcraft 30 or pay 50 gold (or turn to the crew) | 90 with the crew, 91 talked, 92 paid, 95 failed (Heavy-Rope or Ussa-Rekh dead) |

Every stage moves by a line the player picks or one named thing taken; nobody walks; each person stands in one place
for the whole quest. The only switches are the endings' switch-offs (Rows-For-Another at the landing; the one freed at
the stone house), each caused by Never-Sold's line in her house, another cell. Nobody is essential; who must live
fails the quest and, as a faction line, shows the line's message.

## What was cut, and what it became

| Quest | Cut | Became |
|---|---|---|
| BC01 | Never-Sold's sandbox walk to the landing | she stays in her house; the player reports to her |
| BC01 | the night-only, unseen channel line; the follow; the channel-end trigger box; the two estate men | Rows-For-Another talked into going now (Speechcraft 30); her going told to Never-Sold, who ends it; the men cut |
| BC01 | the steward's locked chest (the form drops a container nothing else names) | the book lies at Hulm-Tei's feet, his own: taking it is a theft he sees (Sneak) |
| BC02 | the burning stone house: smoke, the fire's enable states, the walk-in trigger box, the sneak past the gate, three exit boxes, the follow out, two held switched off in view, the second gate-keeper | the fire went through the Rose, where the player never goes; the three stand at the stone house; Tsaxi can count one lost to the smoke; the choice is three lines on him; Never-Sold's line ends it |
| BC02 | the sneak route into the post | Never-Sold's 100 gold (given at the start, so any character can pay) |
| BC03 | the sides opened by a stored flag a line set; the chest; the broker's 100 gold reward (no line of his at the ending) | sides opened by stage (hear Heavy-Rope, hear Ussa-Rekh, choose); the tokens at Ussa-Rekh's feet; no reward |
| BC03 | a start by stumbling on Heavy-Rope at Soulrest | Never-Sold sends the player, after BC01 |

**World edits left** (the forms' refs; the ledger rows `we.bc01.house`, `we.bc01.members`, `we.bc02.fire`,
`we.bc02.gate`, `we.bc03.cabin` are deleted and the kept rows re-described): Never-Sold standing in BM&V's House
(15635D); Hulm-Tei and Rows-For-Another on the landing's navmesh (095465) with the debt book on the ground there; Tsaxi
and the three held at BM&V's stone house (bmv_shell 1307CF, cell 0AFE4F); Ussa-Rekh and Heavy-Rope on Dock2's navmesh
(02F35A) with the tokens on the planks. Nothing built, no door changed. Positions are the old builder's snapped
spots; the z values are approximate and the builder resolves the spot from the anchor.

## Story calls and their lore

| Quest | Call | Source |
|---|---|---|
| BC01 | An Owing counted in months of work, assessed by the holder's own book, grows with food, upkeep and sickness, every line true | `story/lore/topics/labour-and-bondage.md` §2 (the Owing; the four drifts) |
| BC01 | An ex-Archein estate north of Blackrose with a landing, a steward and Owing debtors | `story/lore/extrapolation/gap-register.md` QA3; `story/design/province-vibe.md` §9 |
| BC01 | She is grey from years away from her tree; free, she goes home to it | `labour-and-bondage.md` §2 (the tell); `story/design/quests/40-factions.md` §39 |
| BC01 | She cannot drown in the channel | `labour-and-bondage.md` §1 |
| BC01 | Never-Sold buys out what an Owing first was, in coin, from the holder's own book | `story/design/quests/36-cast-roster.md` §56; `40-factions.md` §39; `province-vibe.md` §5 |
| BC01 | When one held runs, the estate's men are harder on the next one held (why she has not gone) | gap: the least inventive reading of QA3's estate worked by Owing debtors |
| BC02 | A fire went through the Rose, where the heirs keep their held; they keep three at their outer post until it is mended | `40-factions.md` §39 (the Rose's fire-damaged registers); `story/lore/topics/prisons.md`; QA4 |
| BC02 | The heirs' outer post is BM&V's stone house on Blackrose's east shore; the Rose is a day's march south | QA4 (updated in this lane to the stone house the record uses) |
| BC02 | The heirs hold three by their own reckoning: words, a killing, an Owing for shelter | QA20 (updated likewise); `labour-and-bondage.md` §3 (newcomers owe the prison-born) |
| BC02 | A gate-keeper answers to the heirs for the count, and can put one short down to the smoke | `prisons.md` (the heirs' own hierarchy); `40-factions.md` §39 (the Rose keeps its own internal ledger) |
| BC02 | Never-Sold pays coin for the held and keeps every name | `36-cast-roster.md` §56; `province-vibe.md` §5 |
| BC03 | Ussa-Rekh bought out Owings for thirty years and hires out the crews he freed | `36-cast-roster.md` §56; `labour-and-bondage.md` §3 (Soulrest's indentured crews) |
| BC03 | Carved tokens kept until the last season is worked; a crew that breaks them before him is done with him | QA21 |
| BC03 | Never-Sold in Blackrose sends the player to Ussa-Rekh at Soulrest | `36-cast-roster.md` §56 (the Chainbreakers' desks) |
| BC03 | Heavy-Rope settled by persuasion or coin on a port's docks | `province-vibe.md` §5, §9 |

## What the form could not express (re-authored around)

1. **One target per objective in the compiler** (`tools/questform/compile.py`: `targets: [self.use(target, ...)]`;
   the form allows several). With `completes-on-target`, every line or take that moves a stage must concern that one
   target, so a stage cannot be moved both by taking a thing and by the hand-in line, and a choice between two people
   cannot sit at one stage. Re-authored: choices are several lines of one person; the hand-in that works when the
   thing is already held is a holding-gated variant of the line that leads into the take stage (BC01 stage 10, BC03
   stages 30 and 60).
2. **A container named only as a container is not emitted** (refs come only from what a stage, line, objective or
   trigger names), so `refs-exist` fails on the thing inside. Re-authored: the chests are cut; the book and the
   tokens lie on the ground by their owner.
3. **No owner and no lock level on a placed thing.** The theft routes (Sneak) depend on the builder making the book
   and the tokens owned by the person beside them; the records say so in `things`.
4. The gate's `adaptation_check` census has no `bmv_shell` rows (so a shell's full form key in a thing's text fails
   `census_ids`), and its Helgen rule reads "essential or protected" from the record's free text; both were met
   honestly in the text, but the rules predate the ceiling.

## Review

(filled in from the quest-reviewer rounds)

## Dialogue lines now untrue or without a stage (for the dialogue lane)

Ids are the topic keys of `story/data/quest_lines/<code>.json` (every variant listed: `lines`, `lines@low`,
`lines@high`, and `fail`/`day` with theirs) and the keys of `quest_people.json`. Topics new in the records (gists only)
are listed after them.

| Quest | Line id (variants) | Why |
|---|---|---|
| BC01 | `topic.bc01-the-estate` (3) | says "I will meet you there", "Bring me the book" and a locked chest; she now sends the player to Rows-For-Another and stays home |
| BC01 | `topic.bc01-bring-down` (3) | leaves the coin "in the steward's chest"; there is no chest: she will send it |
| BC01 | `topic.bc01-cut-loose` (6, with `day`) | night, the estate men and "I will follow you"; the prompt is now the Speechcraft 30 persuasion to go |
| BC01 | `quest_people.json` `ARG_BC01_EstateMan` (1) | the estate men are cut |
| BC02 | `topic.bc02-the-fire` (3) | the stone house "is burning"; the fire was in the Rose |
| BC02 | `topic.bc02-the-gate` (6, with `fail`) | lets the player into the burning house; now he agrees to count one lost to the smoke |
| BC02 | `topic.bc02-let-by` (6, with `fail`) | no stage: the walk out past him is cut |
| BC02 | `topic.bc02-come-speaker`, `-come-killer`, `-come-mother` (3 each) | no stage: "I will follow", "in the smoke"; the choice is now made to Tsaxi |
| BC02 | `quest_people.json` `ARG_BC02_GateKeeper` (1) | the second gate-keeper is cut |
| BC03 | `topic.bc03-last-season` (3) | "with his chest beside him"; no chest |
| BC03 | `topic.bc03-the-tokens` (3) | "in the chest beside him"; the tokens lie at his feet |

15 ids, 44 variant lines. Still true and kept: `topic.bc01-the-book`, `topic.bc03-the-season`, `topic.bc03-break`,
`topic.bc03-brawl`, `topic.bc03-yield-talk`, `topic.bc03-yield-pay`. New topics to write (gists in the records):
`topic.bc01-buy-out`, `topic.bc01-gone`, `topic.bc01-after-patron`, `topic.bc01-after-steward`; `topic.bc02-the-held`,
`topic.bc02-pay`, `topic.bc02-free-speaker`, `-free-killer`, `-free-mother`, `topic.bc02-held-speaker`,
`-held-killer`, `-held-mother`, `topic.bc02-names`, the five `topic.bc02-after-*` greetings; `topic.bc03-soulrest`,
`topic.bc03-after-rope`, `topic.bc03-after-ussa`.
