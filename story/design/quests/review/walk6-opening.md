# Walk 6: the opening (MQ01) and the next quest (MQ03, The Cutters' Jar), re-authored to the ceiling

Written 2026-11-12 by lane O of [walk 6 (quests)](../../../../docs/phases/walk-6-quests.md). The records are the source
(`python3 -m tools.argonia_world.quest_record export quest.main.mq01`, `... quest.main.mq03`); this note records the
story calls behind them, each with its source, and what Act I now hands on.

## Where the player wakes

BM&V's hold (`0F9178:Black Marsh.esm`, door `0F9399` to the deck door `005AB4`) is the inside of a big sea ship
(`ShipLarge01`) moored at the pier by Hereguard Plantation (the map's name there), about 370 m west of the map's
Lilmoth Dock. Big ships cannot reach Lilmoth's shallows (lilmoth.md, Site and fabric), so the broker keeps his gang in
an old ship's hold at that pier, and the gang came down from its camp in its longboat (BM&V's longboat at the pier).
The owner's "barge" is this ship. Character creation stays in the hold.

## Place x and person y

- **Place x: Salts-The-Catch's house.** BM&V's interior `0FE7F7:Black Marsh.esm` (editor id `01CabinIntsining1`,
  name "House", navmeshed), entered by the load door `0FE95A:Black Marsh.esm` at 31553,-7639 (inner side
  `0FE832:Black Marsh.esm`), below the map marker `082193:Black Marsh North.esp` ("Lilmoth Dock", 30909,-2852).
  Why: it is the Reed's house of the old MQ03 (QA8: the Veiled Reed keeps an unmarked Lilmoth house through a
  fish-trader), and MQ05 already starts there, so Act I keeps one Reed house. Lilmoth holds four interiors with
  doors (census, `bmv_interior_exit`): the ship's hold itself, the ship `0AA665` (MQ05's way out), the house
  `0FE8B7` (the detectives' line seat, `line_hub`) and the Chapter under Pusbottom `16BF81` (TG01 and TG02); this is
  the only one free. No walk-in shell stands nearer the pier: the closest class A or B shells are about 250 m away.
- **The route** is about 400 m and three landmarks: from the pier, east along the shore past the old lighthouse
  (BM&V's `ImpExtLighthouse01`, 7717,-4443), into Lilmoth as far as the second big ship, anchored off Lilmoth's own
  dock (`0ShipImperial`, 31851,-2027); the house stands south of it beside a wooden walkway, below the map's Lilmoth
  Dock. The objective's marker is on Nesh-Deeka.
- **Person y: Nesh-Deeka** (`npc.nesh-deeka`, the story's cast, 36-cast-roster §55: the Veiled Reed's field handler,
  "the game's Caius Cosades"), standing in the house by `we.mq03.house`, with Salts-The-Catch
  (`npc.mercantile-coast.lilmoth.fish-trader-house`) inside the door. Morrowind's opening sends the new prisoner to
  Caius Cosades; ours sends the nameless debtor to the handler written as his counterpart.
- **The man with the work roll: Buys-The-Months** (`npc.mercantile-coast.lilmoth.broker-buys-the-months`), the
  debt-labour broker (QA7), standing on the pier beside his ship (5350,-7800, Dock1 `00591F`, navmesh `079823`), the
  one way off the ship. His want and fear (a mouth on his ship that owes him nothing) make him the man with no name for
  the player. The deck door `005AB4` (5688,-9382) is in a square with no navmesh; the nearest navmeshed standing place
  is on the pier, about 23 m on. The build (lane K) checks the force-greet reaches the player there; if it does not,
  his line stays open by speaking first and the marker is on him.

## MQ01 in three steps; MQ03 in two

- MQ01 10: speak to Buys-The-Months on the pier (he speaks first); 20: find Nesh-Deeka in Salts-The-Catch's house; 30:
  tell her you will work for the Veiled Reed (rank 0, fifty gold). Ends 90; fails 96 (Nesh-Deeka dead). If the player
  kills the broker before he speaks, 21 sends them to look for work in Lilmoth with the marker on Nesh-Deeka, whose
  line for a stranger tells the same story.
- MQ03 10: ask Dives-Without-A-Rope for the jar in the ship's hold; her question's three answers move it: talked
  round (Speechcraft 25) to 15 or paid (20 gold) to 16, each giving her lockbox's key, or "Then I'll take it" to 12
  (pick the Novice lock, or lift her key); her death moves it to 13 (the key on her body). At 12, 13, 15 and 16 the
  fetch is settled at the hand-in: Nesh-Deeka's lines, gated on holding the jar however it was got, ask for a taste,
  and tasting it (or Alchemy 25 first) ends the quest with her page. Ends 90; fails 95 (Nesh-Deeka dead). The "sack"
  became vanilla's lockbox (09424C:Skyrim.esm).
- Both records compile to the quest form (`python3 -m tools.questform compile`) and fit; `story/data/questform_owed.json`
  no longer lists them. For lane A: the form gives each objective one target and every objective of a stage the same
  completing moves, so a fetch cannot carry a marker on the thing and on the person it goes to at once (MQ03's
  objective at 12 to 16 points at Nesh-Deeka; the journal says where the jar is); and who-must-live has no stage
  window, so a person needed only early (the broker) cannot be one. For lane K: one placement per ref where both
  records name a person or the lockbox; the jar goes into the placed lockbox; a death that happened before its stage
  started (Dives-Without-A-Rope killed during MQ01) must still move stage 10 to 13.

## The story calls

| Call | Source |
|---|---|
| The camp burned two nights before the game opens, on the estuary bank a night's rowing above Lilmoth; the gang came down in its longboat to the broker's ship; the camp is told, never shown or visited | QA1 (revised, gap-register §8); lilmoth.md (the estuary into Oliis Bay) |
| The broker's ship lies at the pier by Hereguard Plantation, west of Lilmoth, because big ships cannot reach the town | lilmoth.md (Site and fabric); QA7 (reworded); the census (ShipLarge01, the longboat at Dock1) |
| The gang carried the hurt stranger aboard from the bank by the fire; nobody at the camp knows how the stranger came there | 30-main-quest §18b (a nameless debtor the cell lets live); the player's past stays theirs |
| The broker has no line for the player, owes nothing, cannot hire them out, wants them gone | labour-and-bondage §2; QA7 |
| An Owing in one sentence: months of work owed for a debt or a wrong, held and sold on by a broker here | labour-and-bondage §1-2; province-vibe §2 |
| Salts-The-Catch, who sells the broker his gang's food, asked at the pier for anyone off the ship; her guest pays; the broker passed on his overseer's account | QA8 (the intermediary also sells to the trade it touches) |
| The courier's satchel was Nesh-Deeka's; Cuts-the-Old-Knot took it, had the cutting cut from its eggs, and let the player live | 30-main-quest §18b, §19; 36-cast-roster §55; province-vibe §9 (couriers: the state and its agents) |
| Nesh-Deeka recruits a hand nobody can claim; rank 0 of the Veiled Reed, "the ruling state's quiet service", and fifty gold | 36-cast-roster §55; 10-political-frame §6; 30-main-quest §24b.2 |
| The cutters' jar: one was left by the fire; Dives-Without-A-Rope, whose family answers to Nine Bends, keeps it to lick and hear her tree | hist-and-sap (Sap: licking sap lets the Hist speak in visions); hist-placement (Nine Bends); labour-and-bondage (The tell) |
| The sap was drawn into jars the cutters brought: a long work, not a raid | hist-and-sap (Sap; Silence vs severance); the old MQ03's reversal kept |
| The dream is a page Nesh-Deeka writes while the sap holds the player: the hold, roots in a ring through its deck, a door nobody built, a dry voice that makes no words | QA18; 30-main-quest §18d; province-vibe §9 (records belong to the Reed); QA8 narrowed to the arrangement of protection |
| Nobody is essential; MQ01 cannot go on without Buys-The-Months (until he sends the player on) or Nesh-Deeka; MQ03 cannot go on without Nesh-Deeka | walk-6 plan, "Anyone can die" |

## What the hold's people still say

The roll call and its three answers are cut: the broker outside is the one with no name for the player. Three of the
gang stand in the hold, each in one place: Wuleen-Sei (the overseer) answers "Where am I?" (the broker's ship, the
Owing, the gang carried the player aboard, the broker stands on the pier) and "What happened at your camp?";
Ux-Xeek and Dives-Without-A-Rope answer "Who are you?". None of these lines moves a stage, so none can go wrong.

## Removed from the world (the ledger rows deleted)

`we.mq01.camp`, `.march`, `.families`, `.cell`, `.barge-crew` (its two people folded into `we.mq01.gang`), the 26
camp-clutter rows of `we.clean.hereguardplantation`, and `we.mq03.reed`, `.hurt`, `.rooms`, `.jar-marks`,
`.dream`. Kept: `we.mq01.start`, `.hold-location`, `.no-valenwood`, `.no-welcome`, `we.mq01.gang` (three standing in
the hold), `we.mq01.broker` (one man on the pier), `we.mq03.house` (two standing in the house), `we.mq03.door` (the
house's Riften and Whiterun door models swapped for BM&V's Lilmoth door, decision 0006), `we.clean.lilmoth`,
`we.clean.hereguardplantation`. New: `we.mq03.sack` (a locked lockbox at the far side of the hold, its key on
Dives-Without-A-Rope, the jar in it, lockpicks beside it), switched on by MQ01's ending from another interior.

## What Act I hands on now (for the MQ04 and MQ05 lane)

- **MQ03 ends at stage 90 (complete) or 95 (failed, Nesh-Deeka dead).** MQ04's `startWhen` today is MQ03 ≥ 90, which
  would also start it on the failure: change it to MQ03 = 90. MQ03 is retitled The Cutters' Jar.
- **On MQ04's start the player** is rank 0 of the Veiled Reed (`factionRankAtLeast [faction.veiled-reed, 0]`;
  `flag.mq01.reed-joined`), has fifty gold from MQ01 and twenty-five from MQ03, carries Nesh-Deeka's page (the dream:
  the ship's hold with roots grown through its deck in a ring like trees, a door nobody built, a dry voice without
  words; `flag.mq03.tasted`), knows the cell cuts a Hist's roots and draws its sap into jars it brings ("a long work,
  not a raid"), has heard of the woman with the knotted cord and that she let the player live (not seen her: the
  player woke after the fire), and has been told that the Hist of Low-Reed Village, east of Lilmoth, has turned its
  face. Nesh-Deeka is at Salts-The-Catch's house.
- **Changed from the old hand-on:** no sworn or unsworn split (`flag.mq03.reed-sworn` and `.reed-declined` are gone;
  every player is in the Reed); `flag.mq01.saved-sal` and `.saved-deesh` are gone (nobody was saved); the player has
  *heard of* Cuts-the-Old-Knot rather than *seen* her; Never-Writes-Twice has not appeared and is not a fallback
  sender: if Nesh-Deeka dies, the main quest fails with the "thread severed" message (`flag.main.thread-severed`).
  MQ04's opening entry ("The Reed sent me east of Lilmoth to Low-Reed Village...") still fits; MQ05's start at "the
  Reed's house" is the same house.
- **The outline's Act I paragraph** (main-line-outline.md) is owed the same changes by that lane.

## Review round 1 (one quest-reviewer agent per record)

MQ01, blocking, all fixed: the "barge" was BM&V's big sea ship at the Hereguard Plantation pier, not at Lilmoth's
dock, and there is no plank (text, QA1 and QA7 reworded); Nesh-Deeka knew facts no truth event gave her (t4: the
broker passes on his overseer's account); a `topicHeardFrom` gate on a line (dropped); the start marker's and the
plantation clean-up's ledger rows still described the march and the camp (rewritten). Judged not blocking: no skill
route in the opening (every stage is exempt; MQ03 holds the main line's first two ways through).

MQ03, blocking, all fixed: the sack and jar were in the hold from game start (now switched on by MQ01's ending, from
another interior); the persuade prompt named the Reed ("the one I work for"); stage 30 was hollow (cut: the hand-in
asks for the taste and its two answers end the quest); the dream lacked QA18's dry voice (added); Dives-Without-A-Rope's
npc row kept the cut camp's sleep socket (cleared). Also fixed: duplicate "Who are you?" prompts, a route-dependent
after-line, buy and persuade after the key is taken, QA8's "nothing is written" narrowed, the old title.

Round 2 (delta), blocking, both fixed: MQ01's broker as a who-must-live person would fail the quest at any stage
(the form has no window): he is no longer one, and his early death goes to stage 21. MQ03's take triggers left a jar
taken at stage 10 unhanded: stage 20 and the take triggers are cut, and the hand-in is open at 12, 13, 15 and 16.

Left for the owner or later lanes: the camp is told, never visitable (the plan said "can go and see the day after";
no structure may be added); the force-greet starts about 23 m from the deck door; the walk to the house is about
400 m and its reach is not proven by a check; MQ03's route doubles back (house, hold, house).
