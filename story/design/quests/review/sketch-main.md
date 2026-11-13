# The sketch of main.md's Act I, as the outlines stand

`story/design/quests/lines/main.md` §3 (MQ01 to MQ04), written as sketches (`.claude/skills/story-line/buildable.md`
§4) from the outlines exactly as they stand, without rewriting the story: each step is written as the outline says
it, and where the outline asks for something the game cannot do, it is written in the outline's own terms so that
`sketch` names it. The story's writer changes the outlines and these sketches together in the second round and then
moves each block under its outline. Run:

    python3 -m tools.questform sketch story/design/quests/review/sketch-main.md

The reach walk runs once the rules pass, so the faults below are the rules' and the design rules'; the walk is still
owed. Line numbers below are this file's.

## What `sketch` found: 37 faults

| Quest | Faults | By class |
|---|---|---|
| MQ01 | 12 | line-result 3, needs-living 1, body 1, give-placed 1, number-set 1, line-hostile 1, asked-is-target 1, completes-on-target 1, give-twice 1, sketch 1 |
| MQ02 | 8 | line-result 5, sketch 1, line-window 1, give-twice 1 |
| MQ03 | 11 | line-result 6, owner 1, take-unheld 1, line-hostile 1, number-set 1, sketch 1 |
| MQ04 | 6 | line-result 2, owner 1, take-unheld 1, refusal 1, give-twice 1 |

**The three worst.**

1. *Lines that do things.* Sixteen lines (and two uses) give, set a number, unlock, sell ownership or show a message
   with no stage of their own (the witness's word, Geel-Masu's charm, Heem-Jasa's gate, Rask's sale, Haj-Deesh's hatch, the naming
   choices). In a record a line only moves a stage, so each of these is a stage, and with the stage the "one working
   stage" tables of all four quests change shape: every talked way becomes a stage below the stage its thing's take
   sets.
2. *One thing given and taken.* MQ01's purse, MQ02's jar and MQ04's draught are each "taken, or given by a line" onto
   one stage that gives the thing: a player who steals it holds two, and the purse is carried by the man who would
   hand it over (give-placed). The talked way must give ownership of where the placed thing lies, or the thing given
   must be the only one.
3. *People the quest cannot lose, and bodies.* Dralin dies before his first words and MQ01 cannot move from stage 5;
   Tarries is a body, which nothing places; and the fighter's ways in MQ01 and MQ03 rest on a line turning its
   speaker hostile, which a record cannot do.

**Against what the round-one deliverability reader found** (main.md §5): the stand-in speakers, the stages out of
order and the "both dead" failure are gone from the outlines as they stand; what `sketch` finds now is what the
rebuilt tables still ask of lines (results without stages), of things (one given and one taken) and of people (a
death before the first words, a body, a turn to hostile by a line). The switches that depend on a choice (MQ01's
Counts-His-Luck gone if named, MQ02's Teemal moved) sit on one ending stage each: a stage's results always happen, so
each needs a stage per answer; the sketch shows the switch, and the naming line's number shows the fault.

## Every fault

- line 97: MQ01 `needs-living`: ref dralin: if they die at stage 5, nothing moves the quest on to a completed ending: name them in must-live, or leave another way that does not need them
- line 102: MQ01 `body`: person tarries: nobody is placed dead: a container that is theirs (a satchel, a strongbox) holds what their body would, or they are alive and killed
- line 108: MQ01 `give-placed`: stage 30 gives purse, which already lies in the world: a person cannot hand over a thing that is placed elsewhere (give a second item of its own, or let the player take the placed one)
- line 120: MQ01 `line-result`: line saw: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 121: MQ01 `number-set`: line witness@10 reads the number mq01.witness, which no stage of this file sets
- line 123: MQ01 `line-hostile`: line knife: a line cannot turn its speaker hostile: a person is placed hostile, or the player starts the fight (mark the death `choice`)
- line 125: MQ01 `line-result`: line name: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 126: MQ01 `line-result`: line stranger: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 130: MQ01 `asked-is-target`: trigger take.purse.10-30: purse is to be taken at stage 10 and no objective active there targets it
- line 130: MQ01 `completes-on-target`: objective 10 is completed by trigger take.purse.10-30, which concerns none of its targets
- line 130: MQ01 `give-twice`: stage 30 gives purse and is reached by taking it (trigger take.purse.10-30): the player would hold two
- line 131: MQ01 `sketch`: a use moves a stage (`-> <stage>`); what it shows or sets is that stage's `do`
- line 178: MQ02 `line-result`: line son: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 182: MQ02 `line-result`: line threat: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 185: MQ02 `sketch`: `met` is no gate: the record cannot gate on having spoken before: gate on a stage done at which they spoke
- line 186: MQ02 `line-result`: line notnamed: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 187: MQ02 `line-result`: line young: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 189: MQ02 `line-result`: line bow: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 189: MQ02 `line-window`: line bow is offered before the first ending (90) and stays open to stage 90
- line 191: MQ02 `give-twice`: stage 30 gives sapjar and is reached by taking it (trigger take.jar.20-30): the player would hold two
- line 213: MQ03 `owner`: ref gate: only a thing has an owner
- line 222: MQ03 `take-unheld`: stage 50 takes phial from the player and is reached by truth@30, which does not ask that it be held: give each way its own stage, or gate the line on holding it
- line 232: MQ03 `line-result`: line speech: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 233: MQ03 `line-result`: line ease: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 234: MQ03 `line-result`: line boat: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 235: MQ03 `line-result`: line sell: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 236: MQ03 `line-result`: line buy: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 237: MQ03 `line-hostile`: line fight: a line cannot turn its speaker hostile: a person is placed hostile, or the player starts the fight (mark the death `choice`)
- line 242: MQ03 `number-set`: line seen reads the number mq03.root, which no stage of this file sets
- line 244: MQ03 `line-result`: line thanks: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 247: MQ03 `sketch`: a use moves a stage (`-> <stage>`); what it shows or sets is that stage's `do`
- line 269: MQ04 `owner`: ref hatch: only a thing has an owner
- line 275: MQ04 `take-unheld`: stage 30 takes gall from the player and is reached by question@20, which does not ask that it be held: give each way its own stage, or gate the line on holding it (and 1 more like it from this line)
- line 290: MQ04 `refusal`: line coin@20: its check of skill or gold has no refusal: add `else "..."`, what the speaker says when it fails
- line 291: MQ04 `line-result`: line guest: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 293: MQ04 `line-result`: line taste: a line only moves a stage (`-> <stage>`); what it gives, takes, sets, switches or unlocks is that stage's `do`
- line 296: MQ04 `give-twice`: stage 30 gives draught and is reached by taking it (trigger take.dipper.20-30): the player would hold two

## The sketches

## MQ01

```sketch
quest MQ01 main "No Name on the Roll"
start game 5

place hold indoors "the barge's hold"
place camp outdoors "Sedge-Kal Camp"
place herald indoors "Neeva-Tul's house"

person dralin at camp "Dralin Uveran"
person counts at camp level 2 "Counts-His-Luck"
person okan at camp "Okan-Jei"
person tsuna at camp "Tsuna"
person neeva at herald "Neeva-Tul"
person tarries at camp dead "Tarries"
thing holdchest at hold container owner player holds gold 15, lockpick 5 "hold chest"
thing purse on counts "the purse"

stage 5 "I woke in the hold of a barge with a fever going out of me and no memory of coming aboard."
stage 10 "The gang-master at Sedge-Kal Camp, Dralin Uveran, has no name of mine on his roll. He wants the coin Counts-His-Luck was paid to burn reed taken to Neeva-Tul at Jal-Veesa."
stage 30 "I have the purse: new coin, and a cord tied in a knot I do not know." do give purse, give-gold 60
stage 90 completed "I gave Neeva-Tul the purse. She knew the knot." do take purse, give-gold 40, off counts, start MQ02 10
stage 95 failed "The one person who could read the knot is dead."

objective 5 at 5 "Go out to the man on the landing" -> dralin
objective 10 at 10 "Get the purse" -> counts
objective 30 at 30 "Take the purse to Neeva-Tul at Jal-Veesa" -> neeva

line job dralin first at 5 ask "Where is this?" -> 10 says "Sedge-Kal Camp; the job"
line owing dralin at 10-30 ask "The Owing?" says "no cells; you work off what you owe"
line fire dralin at 10-30 ask "The fire?" says "Tarries is dead in his hut"
line aboard dralin at 10-30 ask "Why am I aboard?" says "somebody carried you down here"
line saw tsuna at 10-30 ask "The fire?" do set mq01.witness 1 says "a tall woman carried someone to the barge"
line witness counts at 10 ask "Tsuna saw the woman who paid you." if number mq01.witness = 1 -> 30 says "he gives up the purse"
line word counts at 10 ask "The watcher will have it out of you. Give it to me." if skill Speech 20 -> 30 else "And who are you? You are not even on the roll." says "he gives it"
line knife counts at 10 ask "You lit it, and a man burned." hostile says "he draws"
line paid counts at 10-30 ask "Who paid you?" says "a tall woman with a cord at her wrist"
line name okan at 10 ask "It was Counts-His-Luck." if alive counts do set mq01.named 1 says "the elders will hear it"
line stranger okan at 10 ask "A stranger paid." if alive counts do set mq01.named 0 says "then a stranger"
line hand neeva at 30 ask "Here is the purse." if holds purse -> 90 says "she knows the knot"
line bought dralin at 90 ask "You bought me." says "the cart and the eight drakes"

take purse from 10 -> 30
use tarries from 10 do message "His purse-string is cut."
must-live neeva fails 95
```

## MQ02

```sketch
quest MQ02 main "The Cutters' Jar"
start from MQ01 at 10

place herald indoors "Neeva-Tul's house"
place town outdoors "Jal-Veesa"
place nenria outdoors "Nenria"

person neeva at herald "Neeva-Tul"
person asheem at town "Asheem-Lei"
person geel at town "Geel-Masu"
person xoh at town "Xoh-Reesha"
person teemal at nenria "Teemal"
person teemaljetty at town off "Teemal"
person kharzal at nenria hostile level 8 "Kharzal"
person ushk at nenria hostile level 5 "Ushk"
person deshra at nenria hostile level 5 "Deshra"
thing jar at nenria stock sapjar owner cutters "the cutters' jar"
thing kharzalkey on kharzal "Kharzal's key"
thing chest at nenria container locked apprentice key kharzalkey owner cutters holds gold 80 "the cutters' chest"
item charm "Geel-Masu's eel-charm"
item phial "Asheem-Lei's phial"

stage 10 "Neeva-Tul has work for a hand that is on nobody's roll."
stage 20 "I am to bring Neeva-Tul the jar that strangers keep at Nenria." do give-gold 50, join veiledreed
stage 30 "I have a jar of sap from the camp at Nenria." do give sapjar
stage 40 "Neeva-Tul sent me to the tree-minder, Asheem-Lei, to learn whose sap this is." do off teemal, on teemaljetty
stage 90 completed "Asheem-Lei tasted it. It is young sap, from Vel-Sapha Stand." do give phial, start MQ03 10
stage 95 failed "Nobody at Jal-Veesa can tell me whose sap this is."

objective 10 at 10 "Hear Neeva-Tul's work" -> neeva
objective 20 at 20 "Get the cutters' jar" -> jar, teemal
objective 30 at 30 "Take the jar to Neeva-Tul" -> neeva
objective 40 at 40 "Show the jar to Asheem-Lei" -> asheem

line herald neeva at 10-40 ask "A root-herald?" says "I hear what comes up every road"
line hist neeva at 10-40 ask "The Hist?" says "the tree in our pool"
line sick neeva at 10-40 ask "Sick ground?" says "white ruins; stakes"
line reed neeva at 10-40 ask "The Veiled Reed?" says "people in Helstrom who listen for a tree going wrong"
line yes neeva at 10 ask "I will do it." -> 20 says "the job at Nenria"
line notyet neeva at 10 ask "Not yet." says "she does not ask twice"
line son geel at 20 ask "Your son?" do give charm says "show him this"
line dry xoh at 20-30 ask "The ruins?" says "the dry way from the Urvyn Farm side"
line charm teemal at 20 ask "(Show the charm.)" if holds charm -> 30 says "he hands over the jar"
line ear teemal at 20 ask "Give me the jar." if skill Speech 25 -> 30 else "No." says "talked round"
line threat teemal at 20 ask "Give it to me or the herald hears your name." do set mq02.threatened 1 says "he gives it, never forgives"
line jar neeva at 30 ask "Here is the jar." if holds sapjar -> 40 says "was one of ours there?"
line ours neeva at 40 ask "Was one of ours there?" asks named, notnamed says "her question"
line named neeva answer at 40 ask "Teemal." if alive teemal, met teemal do set mq02.named 1 says "the elders will give him a season at the weirs"
line notnamed neeva answer at 40 ask "No." do set mq02.named 0 says "then nobody"
line young asheem at 40 ask "It is young sap." if skill Alchemy 25 do give potions says "two potions"
line taste asheem at 40 ask "Whose sap is this?" if holds sapjar -> 90 says "young sap, Vel-Sapha"
line bow xoh at 20-90 ask "The cutters are dead." if dead kharzal, dead ushk, dead deshra do give bowbook says "a book of the bow"

take jar from 20 -> 30
must-live neeva fails 95
must-live asheem fails 95
```

## MQ03

```sketch
quest MQ03 main "The Tree at the Edge"
start from MQ02 at 10

place stand outdoors far "Vel-Sapha Stand"
place creek outdoors far "the creek landing below the stand"
place herald indoors "Neeva-Tul's house"

person heem at stand "Heem-Jasa"
person wuleen at stand "Wuleen-Tei"
person rask at creek level 9 "Rask"
person naga1 at creek level 5 "a Naga of Rask's crew"
person naga2 at creek level 5 "a Naga of Rask's crew"
person neeva at herald "Neeva-Tul"
thing gatekey on heem "Heem-Jasa's key"
door gate at stand locked adept key gatekey owner heem "the root gate"
thing root at stand "the cut root"
thing hook at creek owner rask "a root-cutter's hook"
thing boatchest at creek container locked novice owner rask holds gold 90 "the crew's boat chest"
item rootknot "the stand's root-knot"

stage 10 "I am carrying Asheem-Lei's greeting to the Root-Folk at Vel-Sapha Stand."
stage 20 "Heem-Jasa will not have a stranger at the root. Her people think Wuleen-Tei has bled the tree."
stage 30 "I have a root-cutter's hook from a Naga boat on the creek below the stand."
stage 50 "Heem-Jasa asked me what the minder said, and I answered her. She gave me the stand's root-knot." do take phial, give rootknot
stage 90 completed "I told Neeva-Tul what was done at Vel-Sapha." do start MQ04 10
stage 95 failed "Nobody is left who can carry this on."

objective 10 at 10 "Speak to Heem-Jasa at Vel-Sapha Stand" -> heem
objective 20 at 20 "Find what is killing the young tree" -> root, wuleen
objective 30 at 30 "Show Heem-Jasa the hook" -> heem
objective 50 at 50 "Tell Neeva-Tul at Jal-Veesa" -> neeva

line greet heem at 10 ask "Asheem-Lei sends her greeting." if holds phial -> 20 says "she will not have a stranger at the root"
line speech heem at 20 ask "Your minder asks only that someone look." if skill Speech 30, holds phial do unlock gate else "No stranger's hand at the root." says "she unlocks the gate"
line ease heem at 20 ask "I can ease your tenders' hands." if skill Restoration 25 do unlock gate says "she unlocks the gate"
line boat wuleen at 20 ask "What do you think?" do set mq03.creek 1 says "a boat on the creek at night"
line sell rask at 20 ask "Sell me the hook." if skill Speech 35 do own hook else "No." says "a hook is a hook"
line buy rask at 20 ask "Sell me the hook." if gold 150 do own hook says "a hook is a hook"
line fight rask at 20 ask "You cut the heart-root." hostile says "they attack"
line know rask at 20-30 ask "Who are you?" says "the unwritten one"
line ask heem at 30 ask "Here is the hook." if holds hook asks truth, comfort says "what did she say?"
line truth heem answer at 30 ask "She said it will be dead by the season's end." if holds hook -> 50 says "you unmade us"
line comfort heem answer at 30 ask "She sent her own pool's sap to strengthen it." if holds hook -> 50 says "they died ours"
line seen heem at 30 ask "Here is the hook." if number mq03.root = 1 says "so that is what fits the wound"
line report neeva at 50 ask "It is done at Vel-Sapha." -> 90 says "she hears it"
line thanks wuleen at 50-90 ask "Your name is clear." do give alchemybook says "a book of alchemy"

take hook from 20 -> 30
use root from 20 do message "Cut clean through from the water side."
must-live heem fails 95
must-live neeva fails 95
```

## MQ04

```sketch
quest MQ04 main "The Sour Spring"
start from MQ03 at 10

place boathouse indoors "the boatman's house"
place city outdoors "Helstrom"
place mud outdoors "the mud below the city landing"

person nesh at boathouse "Nesh-Deeka"
person never at boathouse "Never-Writes-Twice"
person haj at city level 25 "Haj-Deesh"
person ruxa at city existing "Ruxa-Neel"
person wujeel at city existing "Wujeel"
person croc at mud hostile level 8 "marsh crocodile"
thing hajkey on haj "Haj-Deesh's key"
door hatch at city locked adept key hajkey owner assembly "the spring's hatch"
thing dipper at city stock draught owner assembly "the spring's draught"
thing gall on croc "the crocodile's gall"

stage 10 "Neeva-Tul sent me by the rootworm to Helstrom, to find Nesh-Deeka and show her the root-knot."
stage 20 "Nesh-Deeka wants a draught from the shut spring under Helstrom's city tree."
stage 30 "I have a gourd of water from Helstrom's spring." do take gall, give draught, take-gold 200
stage 90 completed "Nesh-Deeka tasted the spring and the jar. They are the same sourness." do take draught, take sapjar, give-gold 150, rank veiledreed 1, give dagger
stage 95 failed "The one person in Helstrom who would speak to me is dead."

objective 10 at 10 "Speak to Nesh-Deeka" -> nesh
objective 20 at 20 "Get a draught of the spring's water" -> hatch, wujeel
objective 30 at 30 "Take it to Nesh-Deeka" -> nesh

line need nesh at 10 ask "What do you need?" if holds rootknot -> 20 says "a draught from the shut spring"
line helstrom nesh at 20-30 ask "Helstrom?" if holds rootknot says "the oldest city"
line reed nesh at 20-30 ask "The Reed?" if holds rootknot says "three of us in this house"
line talk nesh at 20-30 ask "The Root Talk?" if holds rootknot says "late this year"
line pays nesh at 20-30 ask "What does it pay?" if holds rootknot says "coin, a bed and a name"
line price wujeel at 20 ask "Here is the gall." if holds gall -> 30 says "he gives his gourd"
line question wujeel at 20 ask "It is sap gone sour." if skill Alchemy 30 -> 30 else "Then you know nothing I need." says "he gives his gourd"
line coin wujeel at 20 ask "I will pay for the gourd." if gold 200 -> 30 says "he gives his gourd"
line guest haj at 20 ask "I am a guest of the Root Talk." if skill Speech 40, holds rootknot do unlock hatch else "Then drink when they do." says "he looks at the river"
line river ruxa at 20-30 ask "The water?" says "three weeks of river water"
line taste nesh at 30 ask "Let me taste it." do message "sour, then a singing" says "do not make a habit of it"
line hand nesh at 30 ask "Here is the draught." if holds draught, holds sapjar -> 90 says "the same sourness"

take dipper from 20 -> 30
must-live nesh fails 95
```
