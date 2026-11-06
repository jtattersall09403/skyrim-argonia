# The slice's final cuts (2026-11-06)
Applied: acbbb6a7, 742e8156, ada9b368, d6d3b754, 36d5f5d2, efe2f8fa, and the LQ25/LQ30 commit that carries this line.

The last delta review, under the loop's exit rule (act1.md: "how the loop ends"). Every finding here is answered by
a single cut or rewording, applied without another review. Each fix is spelt out word for word.

## Main line outline (base 1fb7a46b): 3 blocking, all single cuts; all accepted

- B1, quest_adaptation quest.main.mq03 premise: replace "a ring of root ledges climbed to a door nobody built, and
  a voice." with "a ring of trees in fog, a door nobody built at its top, and a voice, and the dream walks the
  player to it."
- B2, quest_adaptation quest.main.mq01 premise: "gets away through the deep water." becomes "gets away to the shore
  below the camp." In quest.main.mq01's foundation, "The camp is a shore camp with the escape through the deep water
  under the plank boards (swimming depth" becomes "The camp is a shore camp; the huts are reached and left through
  the deep water under the plank boards (swimming depth".
- B3, outline line 18 becomes: "**Act I's flags** (`flag.mq01.saved-sal`, `flag.mq01.saved-deesh`,
  `flag.mq03.reed-sworn`, `flag.mq03.reed-declined`, `flag.mq05.minders-hold`, `flag.mq05.nisswo-read`;
  `flag.mq04.adopted` and `flag.mq04.reconciled` are set on every play) are read for one line of colour at most, or
  not at all."
- N1: join "Opens-the-Last- Door" and "Nesh- Deeka" in line_spirit_beat main ord 2 and in the outline's "For the
  data" block, and "Nesh-/Deeka's" at outline lines 151-152.
- N2: MQ05's title becomes "Helstrom Behind Its Marsh" (quest row; outline line 35).
- N3: outline line 38: "walked past the empty, swept Scalded Throne" becomes "walked past the hall of the empty,
  swept Scalded Throne".
- N4: quest.main.mq01 premise: replace from "and cut a Hist..." to its end with "and cut a Hist from its clutch,
  which dies that night; the player can save one of the two who saw it."
- N5: quest.main.mq01 foundation: "the shed (Destruction against the cutters)" becomes "the shed (Destruction
  against the cutters, or Sneak in the reeds)".
- N6: beat ord 1: "named by the buyer's mark and the cult's want of a Mnemic Egg" becomes "named by the buyer's
  mark, and in it the cult's want of a Mnemic Egg".
- N7: line_spirit promise: "smugglers' docks" becomes "a smugglers' dock".
- N8: quest_adaptation spirit mq07: cut "(not Murkwood, no ship interior)". mq16: cut ", whose interior is a
  recorded need".
- N9: cut MQ23's parenthesis "(not "the last"; Veezara is canon's last, in Skyrim)".
- N10: MQ07's "polite note" becomes "a polite word left with the smugglers".
- N11: Walks-Against-Current's role in beat ord 3 is marked `invented` in his npc row notes; MQ27's record will say
  why a coast pilot knows the basin.

## MQ04 and MQ05 (base 1fb7a46b): 4 blocking, each one row; all accepted

- B1, MQ04 topic.mq04-the-cut: its stages [30] becomes [40]. The intent becomes "said at stage 40, wherever he is,
  once he has been watched at the cut root or the egg-tender has spoken: he hid it because the gum and knife were
  his". The grant stays in stage 30's onEnter.
- B2, MQ04 thing.mq04.zones source: "new (TR-zone): zone.mq04.root, zone.mq04.workshop, zone.mq04.far-side" becomes
  "new (TR-zone): zone.mq04.root, zone.mq04.workshop, zone.mq04.far-side; mark.mq04.cut-root, where Pays-Late's night
  package stands him at the cut root".
- B3, npc ...low-reed-village.cell-man-1 and cell-man-2 notes: "may be killed, taken alive or slipped past" becomes
  "may be killed or slipped past".
- B4, MQ05 stage 20 directions: "at its far bend, where it turns toward the city, the nest hangs over the Heart-Mud
  by the root" becomes "at its far bend, where it turns toward the city, two giant wasps keep the root over the
  Heart-Mud". The a-shoot destruction approach's use "burn-a-nest" becomes "fight", and its note becomes "the wasps
  are burned from the bend before they rise". Search out every other "nest" in MQ05's rows and reword it the same
  way (no nest is placed).
- N1, MQ04 quest_adaptation premise: "learns what was seen by watching the tree-minder unseen at the cut root by
  night or by talking the egg-tender round" becomes "watches the tree-minder unseen at the cut root by night, or
  talks the egg-tender round".
- N2 (food or gold checked, then taken in the line): accepted as it is. The take happens in the topic's fragment at
  build, as Bethesda's bribe lines do.
- N3: accepted as it is.
- N4, MQ04 journal 40: "to the strangers' camp on the dry rise" becomes "to the camp on the dry rise".
- N5, MQ04 stage 40 directions: "past it the reed stems are bent toward a dry rise past the last stilt house, where
  the reeds bend" becomes "past it the bent reed stems lead to a dry rise past the last stilt house".
- N6, act1.md MQ04 header: "10 Speech 25 or 40 gold" becomes "10 Speech 25 or two portions of food".
- N7, MQ05 journal 40: "The hall of the Scalded Throne, by the first street" becomes "The Hall of the Scalded
  Throne, by the first street".
- N8, MQ05 journal 20: "past the levy's gate" becomes "past the gate at the city's edge".

## MQ01 and MQ03 (base 1fb7a46b): 3 blocking, all single cuts; all accepted

Where two reviews worded the same row, one wording is chosen. MQ03's premise takes B3 below, not the outline's B1.
MQ01's "gets away" takes the outline's B2, not N7.
- B1, MQ01 foundation: replace "a march (a follow scene after the answer, as Helgen's cart: each answer topic's
  fragment sets the overseer's march package)" with "a march (the last phase of scene.mq01.opening, as Helgen's
  cart: each answer topic's fragment sets the overseer's march package, and the scene ends only when the player
  stands at the camp's fire)".
- B2, MQ01 foundation: replace "Mee-Tuja and Sal-Sei are essential until stage 40 starts (as Helgen's Hadvar and
  Ralof)" with "Mee-Tuja is essential until stage 40 starts, and Sal-Sei and Deesh-Duun until stage 40 ends (as
  Helgen's Hadvar and Ralof)".
- B3, MQ03 quest_adaptation: in the premise, replace "a ring of root ledges climbed to a door nobody built, and a
  voice." with "a ring of roots in fog, a door nobody built, and a voice." In changed, replace "with fog and a ring
  of root ledges (placed statics, no tree) to climb." with "with fog and a ring of root shapes, a vision scene that
  walks the player to the door."
- W, MQ01 premise: "reads the roll aloud with" becomes "reads out each name with"; "An An-Xileel courier walks"
  becomes "An An-Xileel agent walks"; "strikes the courier at dusk" becomes "strikes the agent at dusk"; cut "the
  roll burns in the camp's fire, and ".
- N1, MQ03 journal 10: replace "I'm to taste the sap, and take a phial of it or dive for the tag, before the boat
  goes." with "I'm to taste the sap, take a phial of it or dive for the tag, then tell the stranger on the shore I
  am ready to go."
- N2, MQ03 objective taste: "In the hatching shed at the camp's far end, take a phial of the spilled sap, if I
  know the craft." Objective go: "Having tasted the sap, and holding the phial or the tag, tell the stranger on the
  shore I am ready to go."
- N3, topic.mq03-the-attack intent: "and takes the phial to look at" becomes "and takes the phial to look at, if
  the player has one".
- N4 (planner): one mark, mark.mq01.shore, is added. The exits of 41 and 42 need npcAtMark for the saved one at
  mark.mq01.shore, so bringing them out decides the stage.
- N5, MQ03 journals 90 and 91: "The dream led me to the door and woke in the house in Lilmoth." becomes "The dream
  led me to the door, and I woke in the house in Lilmoth."
- N6, MQ01 objective answer-roll: "(give a name, say nothing, or tell her" becomes "(give a name, say nothing or
  tell her".
- N8, MQ01 journal 42: "I'm to bring Deesh-Duun round the burning end of the camp to the shore." becomes "I'm to
  bring Deesh-Duun south under the plank boards to the shore below the camp."
- N9: append " (stages 44 and 50 cut by the #50 delta)" to the answers of review rows R1-1, R3-1, R4-2 and R5-3;
  append " (the OneHanded route cut by the #50 delta; the knife is e-sal's reward)" to R2-5.
- N10: cut the orphan condition place_build_hostility_flips:place.pirate-freeholds.opening-work-camp|0:when, its 3
  condition_arg rows, and the upriver-hist-village build orphan.
- N11, we.mq03.jar-marks: "and a phial taken (a" becomes "and a phial taken with Alchemy 25 (a".
- N12: cut "At dawn " from MQ03's journal 10.

## BC01 to BC03 (base 1fb7a46b): 8 blocking; all answered by cuts or rewordings

B7 and B8 had additive fixes. The planner answers them by subtraction instead, as worded below.
- B1: BC02 foundation: "(a kill in stage 30's begin fragment, Bethesda's way)" becomes "(a kill in each 'come with
  me' topic's end fragment, Bethesda's way)". thing.bc02.people: "stage 30's begin fragment kills the two not
  following" becomes "each 'come with me' topic's end fragment kills the other two".
- B2: BC01 shapeData.aftermath becomes, whole: "Bought down, she greets the player in Blackrose by name; slipped
  away, she is gone, and Hulm-Tei will not speak to the player."
- B3: BC02 startWhen becomes all: [questStage: [quest.bc.bc01, ≥, 90], {inCell: '15635D:Black Marsh.esm'}].
  Foundation: "Start: Never-Sold's line at BC01's end sets stage 20." becomes "Start: after BC01, entering the
  Chainbreakers' house (15635D) sets stage 20, where Never-Sold gives topic.bc02-the-fire."
- B4: BC03 startWhen becomes all: [questStage: [quest.bc.bc01, ≥, 90], {inCell: '02F35A:Black Marsh.esm'}].
  Foundation: "The quest starts on Heavy-Rope's greeting;" becomes "The quest starts when the player reaches
  Soulrest's open dock (02F35A) after BC01, on Heavy-Rope's greeting;".
- B5: "or the crew's trade" becomes "or the crew's season" in the foundation and in quest_adaptation's changed. In
  the premise, "stand with him and the crew lose their trade on the dock." becomes "stand with him and the crew work
  their last season out under him."
- B6: cut "- skillAtLeast: [sneak, 25]" from the objective's completeWhen and from the successor to 30. Cut " (Sneak
  25)" from the Sneak action note.
- B7 (subtraction): the freed one does not go to the house. Journals 91 to 93: "He spoke ... and she keeps them."
  becomes "He walked free from the jail door, to speak their names to Never-Sold." (92 and 93 read "She walked
  free..."). Cut "in the Chainbreakers' house" and "keeps to the back of the Chainbreakers' house" from the endings'
  seen and aftermath texts.
- B8 (subtraction): BC01 has no lead. Cut we.bc01.lead and its links. BC01 starts on entering the Chainbreakers'
  house (15635D), where Never-Sold's topic at stage 0 sets stage 10. The foundation's "his topic sets stage 10"
  becomes "Never-Sold's topic in her house sets stage 10". quest_host BC01 ord 0 "what" becomes "Never-Sold, in the
  Chainbreakers' house in Blackrose".
- N1: BC02 stage 20's Sneak exit is inZone zone.bc02.gate-inner (the passage behind Tsaxi) and not detectedBy
  Tsaxi. topic.bc02-the-gate's intent becomes "said only at Speech 25: the heirs will not go in; the three ways in;
  plainly, only one will come out; he opens the gate".
- N2: BC01 journal 40's first sentence becomes "Never-Sold of the Chainbreakers sent me to free Rows-For-Another,
  who took a boat from an estate north of Blackrose on four months' work eleven years ago. She will not wait on the
  book of Hulm-Tei, the estate's steward."
- N3: BC02 journal 30: "Inside the burning cells under the outer post three are held, each reached its own way."
  becomes "Never-Sold of the Chainbreakers sent me into the burning cells under the Rose's outer post at Blackrose's
  edge. Three the heirs hold are inside, each reached its own way."
- N4: BC03 journals 10, 90 and 91: "refused Heavy-Rope's crew their last season" becomes "refused to let
  Heavy-Rope's crew end their last season early".
- Lows:
  - cut flag.bc02.who-lived;
  - 94 disables ref.bc02.smoke;
  - cut " nor me" from BC03 journal 90;
  - thing.bc01.never-sold gets "after-90: in the house";
  - append "; a crew that breaks its tokens before him is done with him" to BC03 t1;
  - cut book-shed from Never-Sold's knowledge at stage 10.

## TG01 and TG02 (base 1fb7a46b): 5 blocking, all single cuts; all accepted

- B1, TG02 stage 20: topic.tg02-charm-claim's intent ends "(takeGold 20, setFlag flag.tg02.okan-paid true)". In
  objective claims' completeWhen and in successor 40, `{goldAtLeast: 20}` becomes `flag: [flag.tg02.okan-paid,
  true]` inside the existing any().
- B2, TG02 failForward 92's `when` becomes:
  any:
  - all: [not: {npcAlive: npc.mercantile-coast.lilmoth.tg02-clutch-client}, not: {npcAlive:
    npc.mercantile-coast.lilmoth.tg02-charm-client}, not: {npcAlive: npc.mercantile-coast.lilmoth.tg02-beads-client}]
  - all:
    - any: [topicHeardFrom: [topic.tg02-sell-back, ...clutch-client], topicHeardFrom: [topic.tg02-sell-back,
      ...charm-client], topicHeardFrom: [topic.tg02-sell-back, ...beads-client]]
    - any:
      - all: [not: {npcAlive: ...clutch-client}, not: {topicHeardFrom: [topic.tg02-sell-back, ...clutch-client]}]
      - all: [not: {npcAlive: ...charm-client}, not: {topicHeardFrom: [topic.tg02-sell-back, ...charm-client]}]
      - all: [not: {npcAlive: ...beads-client}, not: {topicHeardFrom: [topic.tg02-sell-back, ...beads-client]}]
  (Here ... stands for npc.mercantile-coast.lilmoth.tg02-.) Journal 92 becomes "With Neeta-Haj, Okan-Tei or Dar-Zeel
  dead before I had settled with them, the lockbox's pledges cannot be settled, and the job for Bent-Spine has come
  to nothing."
- B3, TG02: each sell-back topic row uses only its own fact (ord 7 [fact.tg02.figurine-old], ord 8
  [fact.tg02.charm-remounted], ord 9 [fact.tg02.beads-kothringi]). The hand-over rows (ords 4 to 6) use
  [fact.tg02.box]. Cut these stage-40 cast changes: Neeta-Haj ords 1 and 2, Okan-Tei ords 0 and 2, Dar-Zeel ords 0
  and 1.
- B4, TG02 touches: `- {id: npc.mercantile-coast.lilmoth-divers-yard.night-reed-fence, access: write}`.
- B5, npc ...soulrest.tg01-thief notes become "TG01's thief (we.tg01.thief): a cowardly dock thief with a round of
  the dock, a drinking spot and an awning he sleeps under, the necklace on him all the while."
- N1: the hand-over's Speech 25 check is not applied. The sell route already needs Speech 30, so the hand-over
  stays the low-Speech route. This is recorded in the review rows.
- N2: add the quest_budget_exception row {"packet":"quests-factions","line":"quest.line.night-reed","shape":"THEFT",
  "reason":"The Chapter's first two jobs, TG01 and TG02, are both takings won by its own skills (slice-premises.md,
  full records round 1)."}, and cut the notes text.
- N3, TG01 stage 20: cut `skillAtLeast: [sneak, 25]` from completeWhen and from successor 30. Not detectedBy alone
  gates it.
- N4, TG01 stages 40 and 41 directions: append "Below, Bent-Spine keeps to the Chapter's inner room, past the foot
  of the trapdoor's ladder."
- N5: the first sentence of the stage 40/41 ship directions becomes "The coast ship's door is on Soulrest's dock
  (039827); inside the ship, the other door (0AA837) comes out at Lilmoth Dock (0AA664), on Lilmoth's east side."
- N6: journal 20's last sentence becomes "I'm to follow him on the dock and boardwalk without being seen until he
  sleeps, or get out of the friend he drinks with where he sleeps."
- N7: cut the clause in journal 20 that says S'Tabi sent the player.
- N8: e-dead's seen becomes "Bent-Spine greets the player coldly in the Chapter".
- N9: topic.tg01-welcome's intent gains "then turns to the work he has (topic.tg02-the-job)".
- N10: item.tg01.jasper-necklace and the three TG02 items are quest items.
- N11 and N12: accepted as they are.

## LQ25 and LQ30 (base 1fb7a46b): 4 blocking, all single cuts; all accepted

- B1, LQ25 journal 40 becomes "The beast is dead. In its lair, in the shallows by the pilings under the landing
  pier, lie fish offal and the landing crew's bait bucket: the crew laid the bait to scare the boat captain's trade
  off the river. I'm to take their bait bucket to the boat captain, who stands at Helstrom's north edge west of the
  levy's gate, or put it to the crew and take their price to keep quiet."
- B2: add to thing.lq25.beast and we.lq25.beast ", named Crocodile by a reference alias display name on the
  placement, as the crew are, never a base edit".
- B3: e-expose's seen becomes "The boat captain greets the player; Okan-Zish and Wuleen-Taza do not". e-quiet's seen
  becomes "Wuleen-Taza nods to the player; the boat captain still talks of the beast in the deep channel".
- B4: cut "Haj-Wan will pay me at the gate." from LQ30 journal 92.
- N1, LQ30 stage 30: the journal becomes "A woman, Haj-Wan, waits inside Helstrom's basin gate, beside the levy
  warden, for her kin Sei-Wan, who walked out alone into the basin. I'm to ask her where he went, and find him." The
  objective becomes "Find Sei-Wan in the basin, east of Helstrom's basin gate."
- N2 (planner: accepted, one action and one mark): both LQ30 endings move Sei-Wan to mark.lq30.gate, with the mark
  in we.lq30.youth. Each runs once the player has left 0D7883.
- N3: Sei-Wan sits under ref.lq30.beast. thing.lq30.people's states become "{before-30: Haj-Wan by the gate,
  Sei-Wan absent; during: Sei-Wan in the shelter and Haj-Wan by the gate; after-90: Sei-Wan at the gate}".
- N4: in the LQ25 rows, the npc rows lq25-crew-* and we.lq25.crew, Wuleen-Sei becomes Wuleen-Taza and Okan-Tei
  becomes Okan-Zish (each name is used elsewhere).
- N5: LQ25 starts on inZone zone.lq25.landing at 08D5EE (-10,15) with MQ05 at 40 or more (one zone, block TR-zone).
- Lows:
  - LQ25's directions: "basin gate" becomes "levy's gate";
  - journal 91: "She paid me for it" becomes "She paid me for what it showed her";
  - weakSample becomes "none: one crocodile at the landing's band 1";
  - thing.lq25.crew says the captain speaks through a reference alias on 08D5F1;
  - LQ30 journal 40 becomes "The viper that kept Sei-Wan in the reed shelter in the basin is dead. I can slip back
    west along the cut reeds to Helstrom's basin gate without Sei-Wan seeing me and let him walk home alone, or
    talk to him and bring him back myself.";
  - LQ30 journal 91 becomes "I am back at Helstrom's basin gate, and Sei-Wan did not see me leave the basin. I leave
    him to walk home alone, and his walk-out is his own.";
  - topics walked-out and the-basin add fact.mq05.basin-lethal to their uses;
  - blocks.md is regenerated.
