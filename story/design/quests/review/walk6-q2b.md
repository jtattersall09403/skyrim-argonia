# Walk 6, lane Q2b: the Chainbreakers' BC01 to BC03 rebuilt from their story

The owner rejected the talk-and-gold versions of the Chainbreakers' first three quests (OR 2026-11-13: "make them
exciting ... do you have to pickpocket somebody to get a key to break into their house"). The story writer's
[chainbreakers.md](../lines/chainbreakers.md) §3 replaced them; lane Q2b built its three outlines as quest records
(`python3 -m tools.argonia_world.quest_record export quest.bc.bc01`, `.bc02`, `.bc03`), each compiled to a quest form
that passes `python3 -m tools.questform check` alone and in the set of eleven, reaching every ending in
`python3 -m tools.playtest reach`. This file holds what was built, what the census showed, what changed from the
story and why, each story call with its lore source, the review and the paper players, and the dialogue lane's work
list. It replaces [walk6-q2.md](walk6-q2.md), which describes the rejected versions.

## What the census shows (checked 2026-11-13)

| Story's place or person | Found in the rows the game loads | Used as |
|---|---|---|
| Never-Sold's house, interior `15635D` by door `15647F` (32,-14) | `15635D` (BM&V House) holds two houses: door `15643F` to `15647F`, and door `156457` to `156479`, whose outer door stands 48 m from the stone house `1307CF` | Never-Sold stands by `15643F` (the old spot was 3,600 units from it, in the other house) |
| The estate's "store", shell `0B6B3B` on the farm (0AFC2E, 32,-13) | a walk-in inn model, class B (8 navmesh triangles inside), on the ground, no load door; BM&V keeps cows, horses and chickens round it | the estate house; the count-box inside it |
| The estate's household `0C72A6` to `0C72A8` | BM&V's villagers, named by talk-write as the north landing's fisher family (Okeemu, Heshra, Pip), 700 to 1,100 units from the house | kept as they are: the eyes on a theft, not the estate's people |
| A guard of the town near the farm | none in `0AFC2E`; the nearest Black Rose Guard (`1454F3`, Sleeps-Standing) stands at the stone houses (`0AFE4F`) | lines never say a guard comes at the farm; at the post, Tsaxi's killing is under that guard's eye |
| The landing `095465` (31,-12) and the next cell north | navmesh in both (`095465`, `095477`); nothing built reads as a landing | "the channel bank"; the fetcher in `095477` |
| The swamp tent `120DF5` (`095469`, 26,-12) | an Ashlander hut, class A, 26,000 units west of the town; BM&V's two Soul Scoungers (`12618F`, `126190`, a werebear race) within 1,300 units; bears and giant leeches (26,-11; 26,-10), swamp lamias (27,-11), crocodiles (26,-13) on the way | the reckoner's camp; one Swamp Lamia of ours (level 14, on BM&V's Lamia base) stands at it so the danger is in the form too |
| The stone house `1307CF` (`0AFE4F`, 34,-16) | walk-in, class A (16 triangles), Ree-Shaal (`1454F2`) beside it | the heirs' post; the three inside, Tsaxi at its west side |
| The Broker's house `0E96A9` by door `120E93` | `0E96A9` holds three houses: `0E971F` to `120E93` (the south house, which TG01 uses), `11ACA1` to `11ACD3`, and `11ABF3` to `120E95`, the north house (shell `0396C2`, class A) | the north house, door `120E95`: BM&V's Dunmer `0616E8` stands 560 units from it, and the armed Argonian `059BF3` ("New Order Ranger") stands inside 455 units from `11ABF3` |
| Dralas, the Dunmer by the door (`0616E8`) | BM&V's "Slave", named Feldril Nethri by talk-write, "a Dunmer labourer working off an owing of months at Soulrest ... by the north door" | Feldril Nethri, the same man under the world's name (no rename) |
| The dock and the moored boat | dock pieces `03457C` to `03457E` in `02F35A`, running west to a large ship (`03981F`) at the end | Heavy-Rope at the head of the dock, Ra'Jhan at its far end by the big ship |

New people are templated on BM&V bases of their race and sex with our names and fixed levels: Argonian women on
`02A1EE`, Argonian men on `00FF4D`, Ra'Jhan on Valenwood's Khajiit `227B7F`, the lamia on BM&V's `04F26C`. The new
names (Brings-Them-Back, Walks-Far, Mends-Nets, Seven-Floods, Ra'Jhan, Otheel) clash with no `npc`, `talker` or BM&V
name and are on no never-reuse list (`86-never-reuse-names.md`); Blackrose's Verb-the-Noun names stay under a third of
its people.

## What the form could not do, and what each became

Each is the smallest change that keeps the moment a player would retell; none bent a tool.

| Story | The limit | Built as |
|---|---|---|
| a leg's result is a stored number (BC01 fetcher bought; BC03 door unbarred, berth-master bought, Broker's release) | a record's line carries only a stage (the compiler gives a topic line no other result) | each result is a stage of its own (BC01 40/41, 45; BC02 35/36/37, 38; BC03 21/22, 40/41/45, 50/51), with its own entry and objective |
| "Told 'Then I go through you', he attacks" (BC01 fetcher, BC03 berth-master) | no record line can carry `speaker_hostile` | the player starts the fight; his death is the player's choice and sets a stage (BC01 45, BC03 45), so a fight has its journal moment and the walker can reach it |
| "a death moves no stage" (BC02 Tsaxi) | the walker fights only people a trigger watches, and ending 94 needs Tsaxi dead | Tsaxi's death sets 38 ("any of the three can go, or all") |
| the swap: put Never-Sold's leaf in the box | nothing can be put into a container | the take of her leaf removes the false leaf (stage 30) |
| the reckoner's body in the tent, searched | the form places no dead body | his strongbox in the tent, holding the leaves, his gold seal ring and his elven dagger; he is not there |
| 60 gold of tolls and six picks in the count-box; 150 gold on the reckoner; 120 and 200 gold on the two fighters | a record has no container contents, and a carried or contained stock item has no count | cut; the count-box holds a silver ring, the fighters carry their weapons (Brings-Them-Back a mace and an iron shield, the story's hide shield having no item row; Ra'Jhan a scimitar) |
| Seven-Floods eased by a Potion of Minor Healing the line takes | a line that moves no stage takes nothing | Alchemy 25 (the player knows what eases a smoke-chest), beside Restoration 25 and Speech 40 |
| giving stolen tokens back to the Broker | as above | cut |
| the confession as a stored number for the finale | as the first row | stage 70 (between the crew's end and the report), whose being reached the finale reads |
| rings and gloves enchanted for Lockpicking, Pickpocket, Sneak | no vanilla enchanted jewelry has a form in the repo's item lists | lockpicks and gold; the enchanted forms are owed to the build lane |
| the "store" | nothing built reads as a store | "the estate house" |
| Dralas | BM&V's man by that door is already Feldril Nethri | Feldril Nethri |
| the Broker's door `120E93` | that is the south house (TG01's); Feldril and the armed Argonian are at the north house | door `120E95` |

## Story calls and their lore (decision 0032)

Every call is the story document's, sourced or marked there as extrapolation (X); the records' `review` L-rows carry
the same citations.

| Call | Source |
|---|---|
| No jails; the Owing in nushmeekos, worked off and never mentioned again; the holder assesses; food, breakage and sickness grow it | `story/lore/topics/labour-and-bondage.md:68`, `:75`, `:84`, `:94`, `:198` |
| A written count is the ex-Archein and prison-born families' borrowed habit (the leaves, the Broker's list and book) | `labour-and-bondage.md:26`, `:84` to `:88`; `province-vibe.md` §5, §9 |
| The Tulm-Varo estate and its keeper of the count | X, gap QA3 (`extrapolation/gap-register.md:141`) |
| The held go grey far from their Hist; one who dies far away may never get home | `labour-and-bondage.md:112`, `:119` |
| A thief's sentence is an Owing | `labour-and-bondage.md:200` |
| The fetcher who knows the way to a runaway's tree; the three legs | X, chainbreakers.md §1 |
| The heirs of the Rose, a day south; their outer post in Blackrose | `story/lore/topics/prisons.md:23`, `:64`; X, gap QA4 |
| The gate over the dead levels; "put under" | `prisons.md:67` |
| Newcomers owe the heirs for shelter | `labour-and-bondage.md:136` |
| The fire in the Rose's upper cells | `story/design/quests/40-factions.md` §39 |
| A berth bought with somebody's months at Soulrest; Thorn, where it is worst | `labour-and-bondage.md:132`, `:135` |
| The Broker who founded the work and bought Never-Sold out | X, gap QA21 (`gap-register.md:155`) |
| A Khajiit berth-master at Soulrest | `story/lore/soulrest.md:21`, `:54` |

## The old written lines

The three records' written lines (`story/data/quest_lines/bc01.json`, `bc02.json`, `bc03.json`: 11, 26 and 14
topics) are removed. None survives unchanged: every one speaks of the rejected versions (a debt book on the bank, a
page struck for 100 gold, the channel at Speech 30; a fire at the post and Tsaxi choosing; the crew's 50 gold and a
brawl), or names people renamed or cut (Says-It-Plain, Hides-In-Reeds, Keeps-The-Old-Count, "the steward"). Six topic
ids were reused for new greetings (`topic.bc01-after-patron`, `topic.bc02-after-patron`, `topic.bc02-after-tsaxi`,
`topic.bc03-after-rope`, `topic.bc03-after-rope-season`, `topic.bc03-after-ussa`); with the files gone they compile
to their new gists, so no old word reaches the player. Words worth carrying over, rewritten to the new truth:
Rows-For-Another's "Eleven years away from my tree"; Tsaxi's "three would be my own neck"; Heavy-Rope's "I will not
tell you he is a bad man. He freed me." No `dialogue_line` row held a BC line. The rumour
`fact.dock2.rumours.quest-bc03` (told by Seeks-The-Channel and Feldril Nethri) stays true ("the crew want their season
ended early; the broker who hires them out refuses"); its source now cites the new record.

## The quests now

| Quest | Ways through, by skill | Endings |
|---|---|---|
| BC01 Four Months for a Boat | the count: lift Hulm-Tei's key (Pickpocket) or pick the Adept count-box (Lockpicking, with five picks from Never-Sold), under the fishers' eyes (Sneak), take her leaf, find the keeper's own leaf under it; the word: Hulm-Tei at Speech 50, or his own leaf given back, or 1,500 gold; the hand: Brings-Them-Back at Speech 35 or 150 gold, or killed (a weapon skill or Destruction) | 90 her leaf to Never-Sold; 91 Hulm-Tei struck it; 92 cut loose, fetcher bought; 93 cut loose, fetcher dead; 94 her leaf taken before the job; 95 failed (Never-Sold or Rows-For-Another dead) |
| BC02 One Out of the Smoke | the reckoner's leaves from the western swamp: the lamia and BM&V's beasts fought (a weapon skill or Destruction) or crept past (Sneak), his Apprentice strongbox picked (Lockpicking); Seven-Floods at Restoration 25, Alchemy 25 or Speech 40; Tsaxi at Speech 35 or 300 gold, or given the leaves; Tsaxi killed (all three may go) | 91 Walks-Far, 92 Mends-Nets, 93 Seven-Floods came out; 94 the post emptied; 95 failed (Never-Sold dead) |
| BC03 The Broker's Mercy | the break-in: Feldril Nethri unbars the door (Speech 25 or 30 gold) or the Adept door is picked; the key lifted off the old man in his room (Pickpocket) or the Expert chest picked (Lockpicking), under his eye (Sneak); the word: Ussa-Rekh at Speech 50 or 1,000 gold hands over his key; the hand: Ra'Jhan at Speech 40 or 1,000 gold, or killed; or Heavy-Rope sails the season (Speech 30, or the list of eleven put in his hand) | 90 broken off, 91 released, 92 the season worked (each after an optional confession, stage 70, with the book held); 95 failed (Never-Sold or Heavy-Rope dead) |

## The review and the paper players

One fresh `quest-reviewer` per record, one round; six paper players on the first designed forms (a careful and an
impatient player per quest), then one confirming careful player per quest on the changed forms (BC02 twice: its
second change, the journal of stage 30 saying what the leaves say, was made after its first confirming run). Runs:
`story/playtests/quest.bc.bc0{1,2,3}/20261113T01*`.

**What they found, gathered.**
- The theft was out of reach for a new character (no picks; Pickpocket not named), so both BC01 players killed the
  fetcher; the false leaf then meant nothing. BC02's Never-Sold handed over exactly Tsaxi's price, so the cheapest
  path was a paid talking room in town and the swamp went unvisited. BC03's talkers never entered the house, and the
  house was empty in game (BM&V's ranger `059BF3` is switched off by `we.clean.dock2`).
- Every quest ended on an empty journal with no pointer to the next.
- Truth faults: the keeper's leaf taken by Never-Sold would spread the shortfall over all the hands while the journal
  said it fell on Hulm-Tei; the cut-loose journal said her leaf stayed in the box when the player held it; the leaf's
  arithmetic could not reach 1,500 gold; "Struck" said Never-Sold would pay later while the reward came at once;
  Never-Sold knew who killed Otheel; two invented Hist names; Rows-For-Another's grey not shown by her base; BC03's
  directions pointed west; "the eleven at Thorn" offered before anyone told of them; the crew "have their tokens" on
  routes where the tokens stayed in the chest.
- Deaths: a held person's death ended the whole faction line with the message; Tsaxi dead before the briefing left
  stage 10 stuck; the fetcher dead before stage 20 lost the channel.

**The one set of changes.** BC01: Never-Sold gives five picks and the objective names Pickpocket and Lockpicking with
their numbers; the relay to Rows-For-Another after Hulm-Tei's word is cut (he reports to Never-Sold, Rows-For-Another's
greeting carries her reaction); the leaf counts eleven a year against six worked to sixty nushmeekos; endings no
longer take the keeper's leaf and say where the years fall; her leaf can still be handed in at 50; the fetcher dead
before 20 opens the channel line; distinct bases for Never-Sold and Hulm-Tei; "grey" is her fear, not her look; no
one-word labels in the journal. BC02: no gift; Tsaxi's price is 300; the objective leads with the swamp; the strongbox
is Apprentice-locked; the reckoner's death is not claimed (his camp is empty and a lamia keeps it); only Never-Sold
must live; Seven-Floods' fallbacks each name their check and the leaves; her "the girl who kept the count wept" seed
is in; Seven-Floods can be asked if Tsaxi died first; Never-Sold no longer knows the killer; the journal at 30 says
what the leaves say. BC03: Ussa-Rekh sits in his room by the chest, so every route but the berth-master's goes
through the house and the theft is under his eye; his word hands over his key and the tokens still come out of the
chest; he says, to anyone, that he bought the Tulm-Varo keeper out for a boat ("Ask her whose boat"); Heavy-Rope
tells of the eleven in his plan; the book keeps its marker on every working stage; the endings set
`flag.bc03.settled`; directions east and south. All three: each ending says to come back to Never-Sold.

**Answered, not changed.** Report and briefing stages name no skill: they are exempt (quest-write §3.3), and BC03's
40/41/45 are reports of a leg won. The record cannot give a line `speaker_hostile` or a number (see the limits).
The guard's swamp warning has no line: BM&V's Sleeps-Standing would need an `npc` row and a placement, left to the
talk-write pass of Blackrose. Shared rooms in `0E96A9`: the Broker's things stand by door `11ABF3`, 2,500 units from
TG01's den by `0E971F`; whether the rooms join inside is for the build's read-back to show (the census gives the
cell one entrance, `120E93`, which the form's `places` repeats). Never-Sold's 100 gold is the player's if words do
the work.

**The confirming players.** BC01: "the keeper Hulm-Tei, who seemed honest, ends up carrying the eleven years ... Never-Sold
knew this and did not tell me. That moral sting was the best part." BC02 (first confirming run): went into the swamp,
fought the lamia, picked the box; then handed the leaves over unread and chose on a hunch, which the stage-30 journal
now answers. BC03: "Ussa-Rekh is a tragic figure. His line 'ask her whose boat' suggests a history I would like to
know." None called a quest errands or a talking room; all wanted the next. What they still asked for and the form or
the paper game cannot give: a crime seen has no consequence on paper; a book taken is not read on paper (in game,
taking a book opens it).

## The dialogue lane's work list

Every topic below needs words; none has any (the old files are gone). The 17 marked need a `fail` info as well.
Write in the record's order; each topic's gist is its `intent` in the record.

### BC01 (27 topics)

| Topic | Speaker | Prompt | Stages | Check |
|---|---|---|---|---|
| `topic.bc01-owing` | Never-Sold | What is an Owing? | 0, 10, 20, 30, 40, 41, 45, 50, 60, 61, 62 |  |
| `topic.bc01-grey` | Never-Sold | Why do the held go grey? | 0, 10, 20, 30, 40, 41, 45, 50, 60, 61, 62 |  |
| `topic.bc01-who` | Never-Sold | Who are the Chainbreakers? | 0, 10, 20, 30, 40, 41, 45, 50, 60, 61, 62 |  |
| `topic.bc01-pay` | Never-Sold | What does it pay, and why might I not want it? | 0, 10, 20, 30, 40, 41, 45, 50, 60, 61, 62 |  |
| `topic.bc01-the-job` | Never-Sold | What is the job? | 0 |  |
| `topic.bc01-again` | Never-Sold | Tell me the job again. | 10, 20, 30, 40, 41, 45, 50, 60, 61, 62 |  |
| `topic.bc01-rows-who` | Rows-For-Another | Who are you? | 0, 10, 20, 30, 40, 41, 45, 50, 60, 61, 62 |  |
| `topic.bc01-how-held` | Rows-For-Another | Never-Sold sent me. Tell me how you are held. | 10 |  |
| `topic.bc01-fetcher-dead` | Rows-For-Another | Brings-Them-Back is dead. The channel is clear. | 20, 45 |  |
| `topic.bc01-channel-clear` | Rows-For-Another | Brings-Them-Back will look the other way. The channel is clear. | 40, 41 |  |
| `topic.bc01-hulm-who` | Hulm-Tei | Who are you? | 0, 10, 20, 30, 40, 41, 45, 50 |  |
| `topic.bc01-hulm-persuade` | Hulm-Tei | Take the first price and strike her leaf. You have carried worse. (Speech 50) | 20, 30, 40, 41, 45 | fallback owed |
| `topic.bc01-hulm-his-leaf` | Hulm-Tei | I have your leaf. (Give it back with the first price, 100 gold.) | 20, 30, 40, 41, 45 | fallback owed |
| `topic.bc01-hulm-purse` | Hulm-Tei | (1,500 gold) I'll pay the whole of what her leaf has grown to. | 20, 30, 40, 41, 45 | fallback owed |
| `topic.bc01-fetcher-who` | Brings-Them-Back | Who are you? | 0, 10, 20, 30, 40, 41, 45, 50, 60, 61, 62 |  |
| `topic.bc01-fetcher-persuade` | Brings-Them-Back | Look the other way when Rows-For-Another goes. (Speech 35) | 20, 30 | fallback owed |
| `topic.bc01-fetcher-pay` | Brings-Them-Back | (150 gold) Take your head-price from me and look away. | 20, 30 | fallback owed |
| `topic.bc01-fetcher-threat` | Brings-Them-Back | And if I go through you? | 20, 30 |  |
| `topic.bc01-her-leaf` | Never-Sold | I have Rows-For-Another's leaf. | 30, 40, 41, 45, 50 |  |
| `topic.bc01-she-goes` | Never-Sold | Rows-For-Another is going by the channel. | 50 |  |
| `topic.bc01-struck` | Never-Sold | Hulm-Tei struck Rows-For-Another's leaf himself. | 60, 61, 62 |  |
| `topic.bc01-knew` | Never-Sold | You knew about the keeper's leaf. | 90, 91, 92, 93, 94 |  |
| `topic.bc01-after-patron` | Never-Sold | (greeting) | 90, 91, 94 |  |
| `topic.bc01-after-patron-cut` | Never-Sold | (greeting) | 92, 93 |  |
| `topic.bc01-after-rows` | Rows-For-Another | (greeting) | 90, 91, 94 |  |
| `topic.bc01-after-hulm-lifted` | Hulm-Tei | (greeting) | 90, 92, 93, 94 |  |
| `topic.bc01-after-hulm-struck` | Hulm-Tei | (greeting) | 91 |  |

### BC02 (33 topics)

| Topic | Speaker | Prompt | Stages | Check |
|---|---|---|---|---|
| `topic.bc02-more` | Never-Sold | Is there more work? | 0 |  |
| `topic.bc02-again` | Never-Sold | Tell me the job again. | 10, 20, 30, 35, 36, 37, 38, 41, 42, 43, 44 |  |
| `topic.bc02-children` | Never-Sold | Tsaxi called the Chainbreakers the Broker's children. Why? | 20, 30, 35, 36, 37, 38, 41, 42, 43, 44 |  |
| `topic.bc02-report` | Never-Sold | It's done at the post. | 41, 42, 43, 44 |  |
| `topic.bc02-seven-keeper-dead` | Seven-Floods | The keeper is dead. Who are you three? | 10 |  |
| `topic.bc02-tsaxi-who` | Third-Born Tsaxi | Who are you? | 10, 20, 30, 35, 36, 37, 41, 42, 43, 44 |  |
| `topic.bc02-tsaxi-three` | Third-Born Tsaxi | Who are the three you keep here? | 10 |  |
| `topic.bc02-tsaxi-otheel` | Third-Born Tsaxi | How did the dead man die? | 20, 30, 35, 36, 37 |  |
| `topic.bc02-tsaxi-persuade` | Third-Born Tsaxi | Count one of them lost to the smoke. (Speech 35) | 20, 30 | fallback owed |
| `topic.bc02-tsaxi-pay` | Third-Born Tsaxi | Here is 300 gold. Count one lost to the smoke. | 20, 30 | fallback owed |
| `topic.bc02-tsaxi-leaves` | Third-Born Tsaxi | Your reckoner's camp is empty and a lamia keeps it. Here are his leaves. | 30 |  |
| `topic.bc02-walks-who` | Walks-Far | Who are you? | 10, 20, 30, 35, 36, 37, 38 |  |
| `topic.bc02-mends-who` | Mends-Nets | Who are you? | 10, 20, 30, 35, 36, 37, 38 |  |
| `topic.bc02-seven-who` | Seven-Floods | Who are you? | 10, 20, 30, 35, 36, 37, 38 |  |
| `topic.bc02-seven-ease` | Seven-Floods | Let me ease your breathing. (Restoration 25) | 20, 30, 35, 36, 37, 38 | fallback owed |
| `topic.bc02-seven-herbs` | Seven-Floods | Let me tell you what eases a smoke-chest. (Alchemy 25) | 20, 30, 35, 36, 37, 38 | fallback owed |
| `topic.bc02-seven-press` | Seven-Floods | You know which of them killed him. Tell me, gently. (Speech 40) | 20, 30, 35, 36, 37, 38 | fallback owed |
| `topic.bc02-go-walks` | Walks-Far | You are the one. Go when I am gone. | 30, 35, 36, 37, 38 |  |
| `topic.bc02-go-mends` | Mends-Nets | You are the one. Go when I am gone. | 30, 35, 36, 37, 38 |  |
| `topic.bc02-go-seven` | Seven-Floods | You are the one. Go when I am gone. | 30, 35, 36, 37, 38 |  |
| `topic.bc02-all-walks` | Walks-Far | The keeper is dead. All of you, go. | 38 |  |
| `topic.bc02-all-mends` | Mends-Nets | The keeper is dead. All of you, go. | 38 |  |
| `topic.bc02-all-seven` | Seven-Floods | The keeper is dead. All of you, go. | 38 |  |
| `topic.bc02-stay-walks` | Walks-Far | (greeting) | 42, 43 |  |
| `topic.bc02-stay-mends` | Mends-Nets | (greeting) | 41, 43 |  |
| `topic.bc02-stay-seven` | Seven-Floods | (greeting) | 41, 42 |  |
| `topic.bc02-after-patron` | Never-Sold | (greeting) | 91, 92, 93, 94 |  |
| `topic.bc02-after-tsaxi` | Third-Born Tsaxi | (greeting) | 91, 92, 93 |  |
| `topic.bc02-after-walks` | Walks-Far | (greeting) | 92, 93 |  |
| `topic.bc02-after-mends` | Mends-Nets | (greeting) | 91, 93 |  |
| `topic.bc02-after-seven` | Seven-Floods | (greeting) | 91, 92 |  |
| `topic.bc02-rows-coming` | Rows-For-Another | (greeting) | 93, 94 |  |
| `topic.bc02-rows-stayed` | Rows-For-Another | (greeting) | 91, 92 |  |

### BC03 (28 topics)

| Topic | Speaker | Prompt | Stages | Check |
|---|---|---|---|---|
| `topic.bc03-more` | Never-Sold | Is there more work? | 0 |  |
| `topic.bc03-again` | Never-Sold | Tell me the job again. | 10, 20, 21, 22, 30, 40, 41, 45, 50, 51 |  |
| `topic.bc03-who-to-you` | Never-Sold | Who is the Broker to you? | 10, 20, 21, 22, 30, 40, 41, 45, 50, 51 |  |
| `topic.bc03-rope-who` | Heavy-Rope | Who are you? | 10, 20, 21, 22, 30, 40, 41, 45, 50, 51 |  |
| `topic.bc03-where-tokens` | Heavy-Rope | Never-Sold sent me. Where are your tokens? | 10 |  |
| `topic.bc03-tokens` | Heavy-Rope | Here are your crew's tokens. | 30, 40, 41, 45 |  |
| `topic.bc03-void` | Heavy-Rope | The hire is void. Ra'Jhan will not pay for the season. | 40, 41, 45 |  |
| `topic.bc03-released` | Heavy-Rope | The Broker has let your crew go. Here are your tokens. | 50, 51 |  |
| `topic.bc03-sail` | Heavy-Rope | Sail the season, for the eleven at Thorn. (Speech 30) | 20, 21, 22 | fallback owed |
| `topic.bc03-sail-list` | Heavy-Rope | Read this list. Then tell me you won't sail. | 20, 21, 22 |  |
| `topic.bc03-ussa-who` | Ussa-Rekh | Who are you? | 10, 20, 21, 22, 30, 40, 41, 45, 50, 51, 60, 61, 62, 70 |  |
| `topic.bc03-ussa-case` | Ussa-Rekh | Why do you still hold their tokens? | 20, 21, 22 |  |
| `topic.bc03-ussa-persuade` | Ussa-Rekh | Let the crew go. You can find another way for the eleven. (Speech 50) | 20, 21, 22 | fallback owed |
| `topic.bc03-ussa-pay` | Ussa-Rekh | I'll pay the season's hire myself. (1,000 gold) | 20, 21, 22 | fallback owed |
| `topic.bc03-ussa-book` | Ussa-Rekh | I found Never-Sold's book on your shelf. | 20, 21, 22, 30, 40, 41, 45, 50, 51, 60, 61, 62, 70 |  |
| `topic.bc03-rajhan-who` | Ra'Jhan | Who are you? | 10, 20, 21, 22, 30, 40, 41, 50, 51, 60, 61, 62, 70 |  |
| `topic.bc03-rajhan-persuade` | Ra'Jhan | Give up the season. Find other hands. (Speech 40) | 20, 21, 22 | fallback owed |
| `topic.bc03-rajhan-pay` | Ra'Jhan | Here is 1,000 gold. Give up the season. | 20, 21, 22 | fallback owed |
| `topic.bc03-rajhan-threat` | Ra'Jhan | The crew are done. Step aside or be put aside. | 20, 21, 22 |  |
| `topic.bc03-feldril-persuade` | Feldril Nethri | Leave the Broker's door unbarred for me. (Speech 25) | 20 | fallback owed |
| `topic.bc03-feldril-pay` | Feldril Nethri | Here is 30 gold. Leave the Broker's door unbarred. | 20 | fallback owed |
| `topic.bc03-report` | Never-Sold | It's done at the dock. | 60, 61, 62, 70 |  |
| `topic.bc03-confess` | Never-Sold | You wrote the first lines of her Owing. | 60, 61, 62 |  |
| `topic.bc03-after-patron` | Never-Sold | (greeting) | 90, 91, 92 |  |
| `topic.bc03-after-rope` | Heavy-Rope | (greeting) | 90, 91 |  |
| `topic.bc03-after-rope-season` | Heavy-Rope | (greeting) | 92 |  |
| `topic.bc03-after-ussa` | Ussa-Rekh | (greeting) | 90, 92 |  |
| `topic.bc03-after-ussa-released` | Ussa-Rekh | (greeting) | 91 |  |

## Lane D3: the dialogue written and played on paper

Every line, journal entry, objective and readable thing of the three quests is written (no gist left): 359 lines in
`story/data/quest_lines/bc01.json`, `bc02.json`, `bc03.json`, per speaker with dialogue-write (Morrowind finds on
every run), one text-review pass (57 hits; the rewrites applied, the "offer with no result" rows answered by the
stages' own results and `gives`), then the linter and the echo check clean. Record changes, each where a line could
not do the work: stage actions so the briefs build; `topic.bc01-leaf-first` (the leaf held before the job has its own
words); each shared hand-in split into one topic per ending, so each says only what is true of it;
`topic.bc02-seven-leaves` with `fact.bc02.take-her-first` (the moment: told what the leaves say, Seven-Floods asks
for Mends-Nets to be taken anyway); `until` on four triggers a side step had closed too early (BC03's token take and
berth-master death after Feldril's door, BC01's fetcher death, BC02's keeper death); the leaf and book texts made
short and true to the built bank; the two Blackrose rumours that spoke of smoke now speak of the three held.

Runs: `story/playtests/quest.bc.bc0{1,2,3}/20261113T04*` and `T0456*`, ten kept. Found and answered as one set: a
refusal that gave no hint of what would work (each now names the kind of thing: a better tongue, a surer healer's
hand, someone who knows herbs, coin, the thing in hand); the briefing's wall of text (cut to four short paragraphs);
a journal route with no matching option ("face Hulm-Tei" now names his own leaf); BC03's hand-over unreachable after
Feldril unbarred the door (the take's `until`); a greeting that spoke of a settled job as open; the leaves' moment
missed (the journal and objective send the player to Seven-Floods with what they read); the book missed on the
season's route (the report objectives carry it). Still weak: Seven-Floods' "take her anyway" is reached only by a
player who tells her what the leaves say (no confirming player did); a seen theft has no consequence on paper; the
fights and locks are one command each; `make reach` on the three is slow until the walker's fix lands.

## Lane Z1: built, read back and played on the plugin

The three records were put on main with X1 and D3 and changed as one set: BC02's choice now opens only after
Seven-Floods has heard what the leaves say (stage 32: her "take her anyway" is said on every leaves route), and its
three choices name what the player knows; BC03's book is named by every report objective and journal and its text is
short, its confession prompt names what the book says, Ra'Jhan stands on the bare shore where the dock meets the land,
Ussa-Rekh's pronouns are his own. Ussa-Rekh stands upstairs with no navmesh and is not fought on any way through; if
he is killed his key is on him and the chest way runs as written (stage 30, ending 90). The truth reader's findings
(BC01 11, BC02 14, BC03 18) are fixed or answered in `truth/bc0{1,2,3}.md`.

Built runs (`story/playtests/quest.bc.bc0{1,2,3}/20261113T0552*` and `T0554*`, a careful and an impatient player
each): BC01 both completed and both told the keeper's leaf turn ("freeing her dumps her eleven years onto Hulm-Tei";
"her admission that she withheld what she knew"). BC02 both went through stage 32 and chose with the killer known
("learned that Mends-Nets drowned a man for the old woman, and still sent Walks-Far out"). BC03 both completed
(endings 90 and 92) and neither said the book's turn: one never took the book, the other took the list. Open: the
book's turn in BC03 (no player yet retells Never-Sold's name on it), and three players asking what a failed
persuasion in BC03 would have needed; a seen theft has no consequence on paper.
