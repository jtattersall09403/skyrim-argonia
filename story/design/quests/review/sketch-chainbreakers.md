# The sketch of chainbreakers.md's first three quests, as the outlines stand

`story/design/quests/lines/chainbreakers.md` §3 (BC01 to BC03), written as sketches (`.claude/skills/story-line/
buildable.md` §4) from the outlines exactly as they stand, without rewriting the story: each step is written as the
outline says it, and where the outline asks for something the game cannot do, it is written in the outline's own
terms so that `sketch` names it. Run:

    python3 -m tools.questform sketch story/design/quests/review/sketch-chainbreakers.md

The reach walk runs once the rules pass, so the faults below are the rules' and the design rules'; the walk is still
owed. Line numbers below are this file's.

## What `sketch` found: 67 faults

| Quest | Faults | By class |
|---|---|---|
| BC01 | 24 | asked-is-target 6, completes-on-target 6, line-result 5, take-unheld 4, refusal 1, line-hostile 1, number-set 1 |
| BC02 | 11 | take-unheld 4, completes-on-target 4, body 1, line-result 1, asked-is-target 1 |
| BC03 | 32 | line-result 8, asked-is-target 7, completes-on-target 7, take-unheld 5, number-set 4, line-hostile 1 |

**The three worst.**

1. *Legs as numbers set by lines.* The common rule of the three outlines ("what the player achieves on a leg is a
   stored number") cannot be built: fourteen lines set a number or unlock a door with no stage (Hulm-Tei's three ways,
   the fetcher bought, Dralas's door, the Broker's release, Ra'Jhan bought, the book's two answers), and the lines that
   read those numbers read numbers nothing sets. Each leg's result is a thing held, a death, or a stage of its own.
2. *Hand-overs the player may not be able to make.* Thirteen stages take a leaf, gold, the leaves, the tokens, the list
   or the book on every way that reaches them, including the ways that never asked for it (Hulm-Tei persuaded still
   "takes the first price"; every report to Never-Sold "takes the book if held"). A stage's results always happen:
   one stage per way, or a hand-in gated on what it takes.
3. *Markers.* Thirty-one marker faults (14 `asked-is-target`, 17 `completes-on-target`): objectives do not point at
   what moves the quest at their stage: the takes of her leaf, the
   leaves and the tokens are open from stage 10, when no marker is on them; Rows-For-Another's and Heavy-Rope's lines
   move the working stage with no marker on them. The reckoner is a body, and both fighters turn hostile by a line.

**Against the quest forms on main.** Lane Q2b (`walk6-q2b.md`, "What the form could not do") built BC01 to BC03 from
these outlines and changed exactly these classes by hand: every leg's number became a stage (BC01 40/41/45, BC02
35/36/37/38, BC03 21/22, 40/41/45, 50/51); "he attacks" became a fight the player starts, its death the player's
choice; the reckoner's body became his strongbox; the potion line that took an item and moved no stage was cut; the
book's answer became stage 70. `sketch` names each of them on the outline's line before any record is written.


## Every fault

- line 140: BC01 `take-unheld`: stage 30 takes falseleaf from the player and is reached by take.herleaf.10-30, which does not ask that it be held: give each way its own stage, or gate the line on holding it
- line 141: BC01 `take-unheld`: stage 40 takes gold from the player and is reached by persuaded@10, which does not ask that it be held: give each way its own stage, or gate the line on holding it (and 2 more like it from this line)
- line 143: BC01 `take-unheld`: stage 90 takes keeperleaf from the player and is reached by early@0, which does not ask that it be held: give each way its own stage, or gate the line on holding it
- line 145: BC01 `take-unheld`: stage 92 takes herleaf from the player and is reached by cut@55, which does not ask that it be held: give each way its own stage, or gate the line on holding it (and 1 more like it from this line)
- line 161: BC01 `asked-is-target`: line persuaded@10 moves the quest at stage 10 and no objective active there targets its speaker hulm
- line 161: BC01 `completes-on-target`: objective 10 is completed by line persuaded@10, whose speaker hulm is not one of its targets
- line 161: BC01 `line-result`: line persuaded: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 162: BC01 `asked-is-target`: line leaf@10 moves the quest at stage 10 and no objective active there targets its speaker hulm
- line 162: BC01 `completes-on-target`: objective 10 is completed by line leaf@10, whose speaker hulm is not one of its targets
- line 162: BC01 `line-result`: line leaf: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 163: BC01 `asked-is-target`: line purse@10 moves the quest at stage 10 and no objective active there targets its speaker hulm
- line 163: BC01 `completes-on-target`: objective 10 is completed by line purse@10, whose speaker hulm is not one of its targets
- line 163: BC01 `line-result`: line purse: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 163: BC01 `refusal`: line purse@10: its check of skill or gold has no refusal: add `else "..."`, what the speaker says when it fails
- line 164: BC01 `line-result`: line look: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 165: BC01 `line-result`: line pay: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 166: BC01 `line-hostile`: line through: a line cannot turn its speaker hostile: a person is placed hostile, or the player starts the fight (mark the death `choice`)
- line 167: BC01 `asked-is-target`: line openbought@20 moves the quest at stage 20 and no objective active there targets its speaker rows (and 1 more like it from this line)
- line 167: BC01 `completes-on-target`: objective 20 is completed by line openbought@20, whose speaker rows is not one of its targets (and 1 more like it from this line)
- line 167: BC01 `number-set`: line openbought@10 reads the number bc01.bought, which no stage of this file sets (and 2 more like it from this line)
- line 168: BC01 `asked-is-target`: line opendead@20 moves the quest at stage 20 and no objective active there targets its speaker rows (and 1 more like it from this line)
- line 168: BC01 `completes-on-target`: objective 20 is completed by line opendead@20, whose speaker rows is not one of its targets (and 1 more like it from this line)
- line 174: BC01 `asked-is-target`: trigger take.herleaf.10-30: herleaf is to be taken at stage 10 and no objective active there targets it
- line 174: BC01 `completes-on-target`: objective 10 is completed by trigger take.herleaf.10-30, which concerns none of its targets
- line 195: BC02 `body`: person reckoner: nobody is placed dead: a container that is theirs (a satchel, a strongbox) holds what their body would, or they are alive and killed
- line 203: BC02 `take-unheld`: stage 35 takes leaves from the player and is reached by lose@20, which does not ask that it be held: give each way its own stage, or gate the line on holding it
- line 208: BC02 `take-unheld`: stage 91 takes leaves from the player and is reached by rep1@41, which does not ask that it be held: give each way its own stage, or gate the line on holding it
- line 209: BC02 `take-unheld`: stage 92 takes leaves from the player and is reached by rep2@42, which does not ask that it be held: give each way its own stage, or gate the line on holding it
- line 210: BC02 `take-unheld`: stage 93 takes leaves from the player and is reached by rep3@43, which does not ask that it be held: give each way its own stage, or gate the line on holding it
- line 227: BC02 `line-result`: line potion: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 229: BC02 `completes-on-target`: objective 20 is completed by line lose@20, whose speaker tsaxi is not one of its targets (and 1 more like it from this line)
- line 230: BC02 `completes-on-target`: objective 20 is completed by line losegold@20, whose speaker tsaxi is not one of its targets (and 1 more like it from this line)
- line 231: BC02 `completes-on-target`: objective 20 is completed by line loseleaves@20, whose speaker tsaxi is not one of its targets (and 1 more like it from this line)
- line 247: BC02 `asked-is-target`: trigger take.leaves.10-30: leaves is to be taken at stage 10 and no objective active there targets it
- line 247: BC02 `completes-on-target`: objective 10 is completed by trigger take.leaves.10-30, which concerns none of its targets
- line 281: BC03 `take-unheld`: stage 60 takes tokens from the player and is reached by void@20, which does not ask that it be held: give each way its own stage, or gate the line on holding it
- line 283: BC03 `take-unheld`: stage 62 takes list from the player and is reached by sail@20, which does not ask that it be held: give each way its own stage, or gate the line on holding it
- line 284: BC03 `take-unheld`: stage 90 takes book from the player and is reached by r1@60, which does not ask that it be held: give each way its own stage, or gate the line on holding it
- line 285: BC03 `take-unheld`: stage 91 takes book from the player and is reached by r2@61, which does not ask that it be held: give each way its own stage, or gate the line on holding it
- line 286: BC03 `take-unheld`: stage 92 takes book from the player and is reached by r3@62, which does not ask that it be held: give each way its own stage, or gate the line on holding it
- line 297: BC03 `line-result`: line unbar: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 298: BC03 `line-result`: line unbarpay: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 299: BC03 `line-result`: line release: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 300: BC03 `line-result`: line releasepay: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 301: BC03 `line-result`: line hire: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 302: BC03 `line-result`: line hirepay: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 303: BC03 `line-hostile`: line done: a line cannot turn its speaker hostile: a person is placed hostile, or the player starts the fight (mark the death `choice`)
- line 305: BC03 `asked-is-target`: line tokens@20 moves the quest at stage 20 and no objective active there targets its speaker rope
- line 305: BC03 `completes-on-target`: objective 20 is completed by line tokens@20, whose speaker rope is not one of its targets (and 2 more like it from this line)
- line 306: BC03 `asked-is-target`: line released@20 moves the quest at stage 20 and no objective active there targets its speaker rope
- line 306: BC03 `completes-on-target`: objective 20 is completed by line released@20, whose speaker rope is not one of its targets (and 2 more like it from this line)
- line 306: BC03 `number-set`: line released@20 reads the number bc03.released, which no stage of this file sets (and 1 more like it from this line)
- line 307: BC03 `asked-is-target`: line void@20 moves the quest at stage 20 and no objective active there targets its speaker rope
- line 307: BC03 `completes-on-target`: objective 20 is completed by line void@20, whose speaker rope is not one of its targets (and 2 more like it from this line)
- line 307: BC03 `number-set`: line void@20 reads the number bc03.void, which no stage of this file sets (and 1 more like it from this line)
- line 308: BC03 `asked-is-target`: line voiddead@20 moves the quest at stage 20 and no objective active there targets its speaker rope
- line 308: BC03 `completes-on-target`: objective 20 is completed by line voiddead@20, whose speaker rope is not one of its targets (and 2 more like it from this line)
- line 309: BC03 `asked-is-target`: line sail@20 moves the quest at stage 20 and no objective active there targets its speaker rope
- line 309: BC03 `completes-on-target`: objective 20 is completed by line sail@20, whose speaker rope is not one of its targets (and 2 more like it from this line)
- line 309: BC03 `number-set`: line sail@20 reads the number bc03.void, which no stage of this file sets (and 7 more like it from this line)
- line 310: BC03 `asked-is-target`: line saillist@20 moves the quest at stage 20 and no objective active there targets its speaker rope
- line 310: BC03 `completes-on-target`: objective 20 is completed by line saillist@20, whose speaker rope is not one of its targets (and 2 more like it from this line)
- line 310: BC03 `number-set`: line saillist@20 reads the number bc03.void, which no stage of this file sets (and 3 more like it from this line)
- line 314: BC03 `line-result`: line yourbook: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 315: BC03 `line-result`: line wrote: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 317: BC03 `asked-is-target`: trigger take.tokens.10-30: tokens is to be taken at stage 10 and no objective active there targets it
- line 317: BC03 `completes-on-target`: objective 10 is completed by trigger take.tokens.10-30, which concerns none of its targets

## The sketches

## BC01

```sketch
quest BC01 faction "Four Months for a Boat"
start game 0

place house indoors "Never-Sold's house"
place landing outdoors "the estate's landing"
place farm outdoors "the Tulm-Varo farm"
place store indoors "the estate's store"
place channel outdoors "the channel north of the landing"

person neversold at house "Never-Sold"
person rows at landing "Rows-For-Another"
person hulm at farm "Hulm-Tei"
person fetcher at channel level 12 "Brings-Them-Back"
thing hulmkey on hulm "the keeper's key"
thing box at store container locked adept key hulmkey owner hulm holds gold 60, lockpick 6 "the count-box"
thing herleaf in box readable "Rows-For-Another's leaf"
thing keeperleaf in box readable "the keeper's leaf"
item falseleaf readable "the false leaf"

stage 0 hidden
stage 10 "Never-Sold asked me to end an eleven-year Owing at the Tulm-Varo estate. She gave me a leaf to put in the count-box, and the Owing's first price." do give falseleaf, give-gold 100
stage 20 "She told me the three things that hold her: her leaf in the keeper's box, the keeper's word and the fetcher on the channel."
stage 30 "I took her leaf from the count-box and put Never-Sold's where it had been." do take falseleaf
stage 40 "Hulm-Tei struck her leaf himself." do take-gold 100, take herleaf, take keeperleaf
stage 55 "She said she would go when I had gone, and gave me a word for Never-Sold."
stage 90 completed "Lifted. I gave Never-Sold the leaf." do take herleaf, take keeperleaf, set bc01.settled 1, give-gold 100, rank chainbreakers 1
stage 91 completed "Struck. I told her it is closed." do set bc01.settled 1, give-gold 100, rank chainbreakers 1
stage 92 completed "Cut loose. I told Never-Sold she has gone by the channel." do take herleaf, take keeperleaf, off rows, set bc01.settled 1, rank chainbreakers 1
stage 95 failed "The Owing cannot be ended now."

objective 10 at 10 "Speak to Rows-For-Another at the estate's landing" -> rows
objective 20 at 20 "End her Owing" -> box, hulm, fetcher
objective 30 at 30 "Bring the leaf to Never-Sold, or face Hulm-Tei" -> neversold, hulm
objective 40 at 40 "Tell Rows-For-Another" -> rows
objective 55 at 55 "Tell Never-Sold" -> neversold

line owing neversold at 0-55 ask "The Owing?" says "a month of work nobody thanks you for"
line grey neversold at 0-55 ask "The grey ones?" says "the Hist"
line who neversold at 0-55 ask "The Chainbreakers?" says "the oath and the three legs"
line pays neversold at 0-55 ask "What does it pay?" says "a thief's share"
line job neversold at 0 ask "What is the job?" if alive rows -> 10 says "the job in three sentences"
line early neversold at 0 ask "I already have her leaf." if holds herleaf -> 90 says "she takes it"
line held rows at 10 ask "Tell me how you are held." -> 20 says "the three things"
line persuaded hulm at 10-39 ask "Strike her leaf." if skill Speech 50 do set bc01.way 1 -> 40 else "A true count is the only thing between me and the mud." says "I have carried worse"
line leaf hulm at 10-39 ask "I have your leaf." if holds keeperleaf do set bc01.way 2 -> 40 says "the damp had his"
line purse hulm at 10-39 ask "I will pay what it has grown to." if gold 1000 do set bc01.way 3 -> 40 says "the estate is paid"
line look fetcher at 10-39 ask "Look away." if skill Speech 35 do set bc01.bought 1 else "No." says "he looks away"
line pay fetcher at 10-39 ask "Look away for coin." if gold 150 do set bc01.bought 1 says "he looks away"
line through fetcher at 10-39 ask "Then I go through you." hostile says "he attacks"
line openbought rows at 10-39 ask "The channel is open." if number bc01.bought = 1 -> 55 says "she will go"
line opendead rows at 10-39 ask "The channel is open." if dead fetcher -> 55 says "she will go"
line lifted neversold at 30 ask "Here is the leaf." if holds herleaf -> 90 says "I read it aloud and burn it"
line struck rows at 40 ask "It is closed." -> 91 says "struck"
line cut neversold at 55 ask "She has gone by the channel." -> 92 says "cut loose"
line knew neversold at 90-92 ask "You knew about the keeper's leaf." says "every count has a last leaf"

take herleaf from 10 -> 30
must-live neversold fails 95
must-live rows fails 95
```

## BC02

```sketch
quest BC02 faction "One Out of the Smoke"
start game 0

place house indoors "Never-Sold's house"
place post outdoors "the heirs' post on the east shore"
place stonehouse indoors "the first stone house"
place tent outdoors far "the swamp tent west of the lake"

person neversold at house "Never-Sold"
person tsaxi at post level 15 "Third-Born Tsaxi"
person walks at stonehouse "Walks-Far"
person mends at stonehouse "Mends-Nets"
person seven at stonehouse "Seven-Floods"
person reckoner at tent dead "the reckoner"
thing leaves on reckoner readable "the singed leaves"
item potion "Potion of Minor Healing"

stage 0 hidden
stage 10 "Never-Sold sent me to the heirs' post on the east shore. Three are held there and one can be got out." do give-gold 100
stage 20 "I learned that one of the three can be lost to the smoke and no more, and that the leaves that say which are with a reckoner who never came in from the western swamp."
stage 30 "I took the singed leaves from the reckoner's body in the swamp."
stage 35 "Tsaxi will count one lost to the smoke. I have only to say which." do take leaves
stage 41 "I told the one I chose to go. The other two stay."
stage 42 "I told the one I chose to go. The other two stay."
stage 43 "I told the one I chose to go. The other two stay."
stage 44 "I told all three to go."
stage 91 completed "I told Never-Sold who came out, and who did not." do take leaves, off walks
stage 92 completed "I told Never-Sold who came out, and who did not." do take leaves, off mends
stage 93 completed "I told Never-Sold who came out, and who did not." do take leaves, off seven
stage 94 completed "I told Never-Sold the post is empty." do off walks, off mends, off seven
stage 95 failed "Nobody can be brought out now."

objective 10 at 10 "Speak to the keeper of the post" -> tsaxi, walks, mends, seven
objective 20 at 20, 30 "Learn who is who" -> walks, mends, seven, reckoner
objective 21 at 20, 30 "Get one out" -> tsaxi, walks, mends, seven
objective 35 at 35 "Tell one of the three to go" -> walks, mends, seven
objective 41 at 41, 42, 43, 44 "Tell Never-Sold" -> neversold

line job neversold at 0 ask "Is there more work?" if stage BC01 >= 90, alive walks, alive mends, alive seven -> 10 says "three held at the post"
line three tsaxi at 10 ask "Who are the three?" -> 20 says "one can be lost to the smoke"
line threew walks at 10 ask "Who are the three?" if dead tsaxi -> 20 says "the same"
line threem mends at 10 ask "Who are the three?" if dead tsaxi -> 20 says "the same"
line threes seven at 10 ask "Who are the three?" if dead tsaxi -> 20 says "the same"
line otheel tsaxi at 20-30 ask "How did Otheel die?" says "drowned in a net"
line ease seven at 20-30 ask "Let me ease your breathing." if skill Restoration 25 else "Ask me which of my daughters I would drown." says "the truth"
line potion seven at 20-30 ask "Take this potion." if holds potion do take potion says "the truth"
line press seven at 20-30 ask "Tell me gently." if skill Speech 40 says "the truth"
line lose tsaxi at 20-34 ask "Lose one to the smoke." if skill Speech 35 -> 35 else "Three would be my own neck." says "he will lose one"
line losegold tsaxi at 20-34 ask "Lose one to the smoke." if gold 100 -> 35 says "he will lose one"
line loseleaves tsaxi at 20-34 ask "Nobody is coming. Here are the leaves." if holds leaves -> 35 says "the count is mine"
line gow walks at 20-39 ask "You are the one. Go when I am gone." if stage BC02 >= 35 -> 41 says "he will go"
line gowl walks at 20-39 ask "You are the one. Go when I am gone." if holds leaves -> 41 says "he will go"
line gowd walks at 20-39 ask "You are the one. Go when I am gone." if dead tsaxi -> 41 says "he will go"
line gom mends at 20-39 ask "You are the one. Go when I am gone." if stage BC02 >= 35 -> 42 says "she will go"
line goml mends at 20-39 ask "You are the one. Go when I am gone." if holds leaves -> 42 says "she will go"
line gomd mends at 20-39 ask "You are the one. Go when I am gone." if dead tsaxi -> 42 says "she will go"
line gos seven at 20-39 ask "You are the one. Go when I am gone." if stage BC02 >= 35 -> 43 says "she will go"
line gosl seven at 20-39 ask "You are the one. Go when I am gone." if holds leaves -> 43 says "she will go"
line gosd seven at 20-39 ask "You are the one. Go when I am gone." if dead tsaxi -> 43 says "she will go"
line allw walks at 20-39 ask "The keeper is dead. All of you, go." if dead tsaxi -> 44 says "they go"
line rep1 neversold at 41 ask "Walks-Far came out." -> 91 says "pleased and uneasy"
line rep2 neversold at 42 ask "Mends-Nets came out." -> 92 says "cold"
line rep3 neversold at 43 ask "Seven-Floods came out." -> 93 says "silent, then kind"
line rep4 neversold at 44 ask "The post is empty." -> 94 says "the heirs will not treat with us"

take leaves from 10 -> 30
must-live neversold fails 95
must-live walks fails 95
must-live mends fails 95
must-live seven fails 95
```

## BC03

```sketch
quest BC03 faction "The Broker's Mercy"
start game 0

place house indoors "Never-Sold's house"
place dock outdoors far "Soulrest's dock"
place broker indoors "the Broker's house"

person neversold at house "Never-Sold"
person rope at dock "Heavy-Rope"
person ussa at dock "Ussa-Rekh"
person rajhan at dock level 18 "Ra'Jhan"
person dralas at dock existing "Dralas"
person ward at broker existing "the Broker's door-ward"
thing brokerkey on ussa "the Broker's key"
door brokerdoor at dock locked adept key brokerkey "Door to the Broker's house"
thing chest at broker container locked expert key brokerkey owner ussa holds gold 40 "the token chest"
thing tokens in chest "the crew's tokens"
thing list at broker readable owner ussa "the list of eleven"
thing book at broker readable owner ussa "Never-Sold's count"

stage 0 hidden
stage 10 "Never-Sold sent me to Soulrest's dock, where the Broker holds a freed crew's tokens for one season more."
stage 20 "Heavy-Rope told me the tokens are in the Broker's chest, the key is on the Broker, a dock hand bars his door, and the berth-master Ra'Jhan is to pay for the season."
stage 30 "I took the crew's tokens from the Broker's chest."
stage 60 "The crew are free of the last season." do take tokens
stage 61 "I told Heavy-Rope the Broker has let them go."
stage 62 "Heavy-Rope will sail the last season." do take list
stage 90 completed "Broken off. I told Never-Sold how it ended." do take book
stage 91 completed "Released. I told Never-Sold how it ended." do take book
stage 92 completed "The season worked. I told Never-Sold how it ended." do take book
stage 95 failed "The crew have nobody to speak for them now."

objective 10 at 10 "Speak to Heavy-Rope on the dock" -> rope
objective 20 at 20 "Free the crew" -> chest, ussa, rajhan
objective 21 at 20, 30 "The book on the shelf" -> book
objective 30 at 30 "Bring the tokens to Heavy-Rope" -> rope
objective 60 at 60, 61, 62 "Tell Never-Sold" -> neversold

line job neversold at 0 ask "Is there more work?" if stage BC02 >= 91, alive rope -> 10 says "the Broker"
line where rope at 10 ask "Where are the tokens?" -> 20 says "the plan"
line unbar dralas at 20-39 ask "Leave the door unbarred." if skill Speech 25 do unlock brokerdoor else "No." says "he unbars it"
line unbarpay dralas at 20-39 ask "Leave the door unbarred." if gold 30 do unlock brokerdoor says "he unbars it"
line release ussa at 20-39 ask "Let the crew go." if skill Speech 50 do set bc03.released 1 else "In his own words, no." says "I have two hands"
line releasepay ussa at 20-39 ask "Let the crew go." if gold 1000 do set bc03.released 1 says "the season's hire"
line hire rajhan at 20-39 ask "Give up the season." if skill Speech 40 do set bc03.void 1 else "No." says "he gives it up"
line hirepay rajhan at 20-39 ask "Give up the season." if gold 1000 do set bc03.void 1 says "he gives it up"
line done rajhan at 20-39 ask "The crew are done." hostile says "he draws"
line boat ussa at 20-39 ask "Never-Sold's book." if holds book says "ask her whose boat"
line tokens rope at 20-39 ask "Here are your tokens." if holds tokens -> 60 says "the crew are free"
line released rope at 20-39 ask "The Broker has let them go." if number bc03.released = 1 -> 61 says "released"
line void rope at 20-39 ask "The hire is void." if number bc03.void = 1 -> 60 says "the crew are free"
line voiddead rope at 20-39 ask "The hire is void." if dead rajhan -> 60 says "the crew are free"
line sail rope at 20-39 ask "Sail the season." if skill Speech 30, alive ussa, alive rajhan, number bc03.void = 0, number bc03.released = 0 -> 62 else "No." says "he will sail"
line saillist rope at 20-39 ask "Sail the season, for these eleven." if holds list, alive ussa, alive rajhan, number bc03.void = 0, number bc03.released = 0 -> 62 says "bitterly"
line r1 neversold at 60 ask "It is done at the dock." -> 90 says "broken off"
line r2 neversold at 61 ask "It is done at the dock." -> 91 says "released"
line r3 neversold at 62 ask "It is done at the dock." -> 92 says "the season worked"
line yourbook neversold at 60-62 ask "Here is your book." if holds book do set bc03.book 1 says "she takes it"
line wrote neversold at 60-62 ask "You wrote the first lines of her Owing." if holds book do set bc03.confessed 1 says "four months, then the food"

take tokens from 10 -> 30
must-live neversold fails 95
must-live rope fails 95
```
