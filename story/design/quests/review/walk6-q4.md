# Walk 6, lane Q4: the two local quests at Helstrom at the ceiling

LQ25 *The River Monster* (`quest.local.lq25`) and LQ30 *The Gates of Helstrom* (`quest.local.lq30`) were re-authored
as quest records at the walk-6 ceiling ([walk-6-quests](../../../../docs/phases/walk-6-quests.md)). Both compile to
quest forms that pass `python3 -m tools.questform check` and are off `story/data/questform_owed.json`. Each had one
`quest-reviewer` round; the blocking findings and their answers are below. Both are minor side quests: a death fails
the quest with its journal entry and no message.

## LQ25 The River Monster

**Steps.** 0 (hidden) Okan-Zish, a rafter of the landing crew, grumbles unasked that no raft goes out; asked, he
tells of the crocodile → 20 kill the crocodile in the shallows off the end of the crew's plank walk (blade, bow or
spell) → 30 tell Okan-Zish it is dead (the crocodile's death moves the quest from stage 0 too, so a kill before he is
met still leads on) → 40 he owns the bait: Wuleen-Taza dumped offal to scare traders off Sells-Dear's boat, and it
drew a real crocodile; fetch the crew's bait bucket for Sells-Dear, or take Wuleen-Taza's price → 50 (on taking the
bucket) show it to Sells-Dear, or take the price after all → 91 Sells-Dear keeps the bucket and pays 60 gold / 92
Wuleen-Taza pays 60 gold for silence. Failed: 93 Okan-Zish, 94 Sells-Dear, 95 Wuleen-Taza dead.

**Cut and what it became.** The crocodile switched on in the player's sight by Okan-Zish's line: it stands in its
lair from the start. The bucket read as the only clue: Okan-Zish now tells the player plainly. The MQ05 stage-40 gate
on the opening line: dropped (below). The ending's switch-off of the crocodile: gone (it is dead). Protected
Okan-Zish, Wuleen-Taza and Sells-Dear: nobody is protected; each one's death fails the quest.

**World edits left.** One crocodile (a new base named Crocodile templated on BM&V's Alligator `0BCB00:Black
Marsh.esm`, fixed level band 1, hostile) and one bait bucket (a new misc item `ARG_LQ25_BaitBucket`, *Bait Bucket*,
a vanilla bucket's model) in the shallows of cell `0D77AF` at about (-34400, 64100), anchored on the place `bmv.dock5`
with the navmesh and surface rules. The crew (`08D5EE`, `08D5EF`) and Sells-Dear (`08D5F1`) are BM&V's own people,
unchanged and named by the talk pass. Nothing built, nothing moved, no lock.

## LQ30 The Gates of Helstrom

**Steps.** 0 (hidden) Haj-Wan, by the levy warden at Helstrom's gate, asked what she waits for → 30 find her kin
Sei-Wan, who walked out east into the basin → (Sei-Wan's line) 35 a viper in the roots west of him keeps him up on
the roots: kill it (bow or blade), or straight to 40 if it is already dead → 40 speak to Sei-Wan: (Persuade, Speech
25) talk him home → 50 tell Haj-Wan he is coming → 92 she pays 60 gold, he counts the walk-out lost; or tell him to
walk home on his own feet → 91 the walk-out stays his, nothing said at the gate. Failed: 93 Sei-Wan, 94 Haj-Wan dead.

**Cut and what it became.** The gate zone that ended the quest when the player walked back unseen (a walk-in area
and a "being seen" check) became Sei-Wan's own line ("Walk home on your own feet; I will say nothing at the gate").
Sei-Wan moved to the gate at either ending (a moved person) became told: he says he will come in when he chooses,
and he stands among the roots for the whole quest and after it; every greeting is true there. Sei-Wan switched on at
stage 30 under the viper's enable parent: he stands there from the start. Protected Sei-Wan and Haj-Wan: their
deaths fail the quest.

**World edits left.** Haj-Wan (a new placement templated on BM&V's villager `02A1EE`) beside the warden `08D5E9` at
the gate (cell `0D787F`); Sei-Wan (templated on `00FF4D`) among the roots of `0D7883` at (-18324, 77678), the old
builder's snapped navmesh point; one viper (a new base templated on BM&V's Viper `17BC83`, fixed level band 3,
hostile) in the roots at about (-22000, 77650), between him and the gate and out of his reach. Nothing built,
nothing moved, no lock.

## Story calls and their lore

| Call | Source |
|---|---|
| The landing crew are Agaceph rafters; Agaceph pole one-person rafts | `story/lore/helstrom.md` (Agaceph, tail-poled rafts), `story/lore/tribes.md` (Agaceph) |
| The beast is a crocodile at a fixed level, never the extinct Helstrom Crocodile; crocodiles attack inside town limits | `story/lore/topics/fauna-hazards.md` (Crocodiles); decision 0035 |
| The crew's tale put the beast in the deep channel Sells-Dear's boat runs, so it scared trade off her boat and not their rafts | invented to make the lie work (review LQ25 finding 6); nothing in the lore against it |
| Okan-Zish blurts the crew's secret once the beast is dead; Wuleen-Taza does the crew's bargaining and pays | `story/data/db/talker.jsonl` 08D5EE (boastful, talks fast and big), 08D5EF (does the crew's bargaining) |
| Sells-Dear sells below cost on the landing side to starve the rafters out, and lets it slip at the exposure ending | `story/data/db/talker.jsonl` 08D5F1 (her secret) |
| Rewards are coin | `story/design/province-vibe.md` §5 (coin tier: cities); `story/lore/extrapolation/settlement-register.md` (Helstrom a city) |
| Nothing written: the bait is a thing found and a thing told | `story/design/province-vibe.md` §9 |
| LQ25 no longer waits for MQ05 stage 40 (decided once): nothing in it depends on the main quest, the landing's talkers rumour it from the start, and a gated giver would just be silent | planner's call within the brief |
| A youth may walk out into the basin alone to prove himself; his tribe's own may not follow; an outsider may; the walk-out ends when he comes back through the gate on his own feet; a return at an outsider's word does not count | gap-register QA5 (`story/lore/extrapolation/gap-register.md` §8), the Dead-Water rites of passage in `story/lore/topics/loading-facts.md` |
| The walk-out is the custom of Sei-Wan's tribe, the Agaceph, not of Helstrom; the levy keeps the gate and leaves a tribe's rite to that tribe | `story/lore/helstrom.md` line 50 (Agaceph of Middle Argonia); `story/lore/extrapolation/argonia-4e201-state.md` §2 (Helstrom's levy answers to the assembly of the interior tribes) |
| The viper is the red hooped tree-viper whose bite kills; BM&V places vipers in the basin's roots | `story/lore/topics/loading-facts.md`; census `17BC83` placements at -7,17 and -9,18 |
| The basin's Heart-Mud holds a walker who stands still | `story/lore/helstrom.md` (Heart-Mud); `story/lore/topics/fauna-hazards.md` |

## Review round 1 (quest-reviewer), blocking findings and answers

- **LQ25 (b), deaths scoped by stage in the record and unscoped in the form.** Every non-ending stage now carries all
  three deaths, as the form has it, and 93 to 95 read true at any stage without giving the twist away ("Whatever the
  landing wanted of me ends with him").
- **LQ30, the quest fails before it starts.** Same answer: the failed entries read true at any stage. Still owed to
  the tool lane: `must_live` has no first stage, so a who-must-live death at the hidden stage 0 shows a failed quest
  the player never began (see the tool faults).
- **LQ30, the viper beside an unarmed villager.** Moved about 3,700 units west of Sei-Wan, still between him and the
  gate; the builder lane should give the templated villagers no sandbox or home package so they stay at their spot.
- **LQ30, the viper kill had no stage.** Stage 35 (kill the viper, its own objective and marker), entered by Sei-Wan's
  line while it lives; his line goes to 40 when it is already dead; the death trigger runs from 35.
- High and lower findings answered in the records: LQ25's crocodile moved off the end of the plank walk, about
  2,000 units from the crew and the soldiers (unmeasured: the builder resolves the navmesh spot); Okan-Zish greets the
  player unasked at stage 0; fetching the bucket is its own stage; the endings pay alike, and exposure costs the
  crew's goodwill; LQ25's unfailable Speech claim dropped. LQ30's after-death greeting by Haj-Wan cut (nobody told
  her); her topic and the warden's reworded to the tribe's rite; greetings made timeless; the npc notes no longer say
  protected. Kept as is: Speech 25 on talking Sei-Wan home (never the only way; a new character can only leave the
  walk-out his own, which is a fair ending).

## Dialogue lines now untrue or without a stage (for the dialogue lane)

Ids are `<file>:<topic>/<variant>/<line index>`; `quest_lines` files are `story/data/quest_lines/`, the tsv files
`story/data/dialogue-writer/quest/<code>/`.

LQ25 (untrue):
1. `lq25.json:topic.lq25-the-beast/prompt` and the bands' prompt: now "What lives under your walk?" (answers the new
   stage-0 greeting).
2. `lq25.json:topic.lq25-the-beast/lines|lines@low|lines@high/0,1`: "lairs in the shallows under our plank walk",
   "lies in the water beneath it": it lairs off the end of the walk. Same rows in `lq25-crew-poler.bands.tsv`.
3. `lq25.json:topic.lq25-tell-captain/lines|lines@low|lines@high/0` ("I believed the beast had always been there.
   This proves it was not."): the beast is real; the bucket proves the crew drew it. Same rows in
   `boat-captain.bands.tsv`. Her refusal without the bucket is unwritten.
4. `lq25.json:topic.lq25-keep-quiet/lines|lines@low|lines@high/0` ("to draw a beast"): they faked one; and `/3`
   ("40 gold"): she now pays 60, all the crew has put by. Same rows in `lq25-crew-steerer.bands.tsv`; the allow-list
   row `quest_text_allow.json` "Here are 40 gold".
5. `boat-captain.after.tsv:greet.lq25-after/after91` and `/after92`, `lq25-crew-steerer.after.tsv:greet.lq25-after/
   after91` and `/after92`: true in substance, re-keyed to `topic.lq25-after-exposed`, `topic.lq25-after-quiet-captain`,
   `topic.lq25-after-exposed-crew`, `topic.lq25-after-quiet`; after91 for Sells-Dear gains the slip about her
   undercutting.
6. Talk rumours `talk_line` 08D5EA `talk.rumours`/1 and 08D5EC `talk.rumours`/1: "took one of the landing crew" /
   "has taken one of their crew": it took a raft.

LQ25 (no lines yet): `topic.lq25-greet-idle` (Okan-Zish, stage 0), `topic.lq25-beast-dead` (Okan-Zish, 30).

LQ30 (untrue):
7. `lq30.json:topic.lq30-walked-out/lines|lines@low|lines@high/1,2` ("to prove himself to Helstrom's Agaceph, the
   tribe that rules this city", "The levy will not go"): his tribe, the Agaceph; the levy leaves a tribe's rite to
   that tribe. Same rows in `lq30-kin.bands.tsv`.
8. `lq30.json:topic.lq30-the-basin/*`: now also says Sei-Wan walked out days ago and has not come back, and why the
   levy leaves it (the rows say only the gate and the roots). `levy-warden-01.bands.tsv`.
9. `lq30.json:topic.lq30-come-back/prompt` gains "(Persuade)"; `/lines|lines@low|lines@high/3` ("Walk ahead of me"):
   he does not follow; he comes in his own time. `lq30-youth.bands.tsv`. The refusal under Speech 25 is unwritten.
10. `lq30-kin.after.tsv:greet.lq30-after/after91` ("Sei-Wan walked home alone ... I thank you"): she knows nothing
    and he has not come home. `/after92` re-keyed to `topic.lq30-after-brought`; `/after93`: cut (nobody told her).
11. `sei-wan.after.tsv:greet.lq30-after/after91` both lines ("I walked home alone", "I am home on my own feet"): he
    is still among the roots. `/after92` both lines true, re-keyed to `topic.lq30-after-brought-youth`.

LQ30 (no lines yet): `topic.lq30-found` (Sei-Wan, 30 to 40, both cases), `topic.lq30-own-feet` (40),
`topic.lq30-coming-home` (Haj-Wan, 50), `topic.lq30-after-own`, `topic.lq30-after-own-kin`.

Stale ledger rows (not dialogue; the old build's, until the generic builder takes these quests): `we.lq25.beast`
("on from stage 20", the old spot), `we.lq30.youth` ("at either ending the youth is moved"), `we.lq30.trail`.

## The paper playtest

One `careful` player on each designed form after the review fixes, lines as gists (runs in
`story/playtests/quest.local.lq25/20261112T224321Z-careful-designed/` and `.../quest.local.lq30/...`). Both finished
the quest (LQ25: 19 commands; LQ30: 21), with 0 stalls and 0 harness errors, and could retell the story. LQ25's
player took the exposure ending and LQ30's the walk-out-his-own ending. What confused them: the unwritten gists (owed
to the dialogue lane); in LQ25, why Okan-Zish left out what Wuleen-Taza then said (the dialogue should have him say
plainly that she will pay); in LQ30, what the other answer would have changed. Both wanted a visible consequence
after the choice, which the after-ending greetings give once written. Nothing in the records was changed for these.

## Tool faults met (for the lanes that own them)

- `must_live` has no first stage. The compiler widens a record's stage-scoped fail-forwards to every stage, and a
  who-must-live death at the hidden stage 0 fails a quest the player never began. The answer here is entries that
  read true at any stage; the form needs a `from_stage`.
- `adaptation_check` (helgen) wants a fail-forward for every person a stage names. Under the ceiling that makes every
  speaker a who-must-live (LQ25's Sells-Dear and Wuleen-Taza, where one of them alive is enough).
- A gated line gets an ungated twin with the same words. The refusal of a hand-in or a skill line therefore says the
  success gist, and two condition variants of one line cannot be written.
- `hasItem` names a ref as a mover (take trigger) but an item base as a gate. One record needs both ids.
- The compiler reads written dialogue only as `infos`. The `quest_lines/*.json` files hold `prompt`/`lines`, so
  written lines come out as gists.
- An objective's `target` is one record column. Several targets were dropped. Fixed in `compile.py`: a comma-separated
  target becomes several, with a test.
- The form cannot name or level a new base (`template_person`, `item`). The crocodile's name and both creatures'
  fixed levels live only in prose, and so does the new item's name and model.
- `rule_placed` in `adaptation_check` ignores the record's `placements` section.
- `quest-record.md` says `hidden: true`, but the column is an integer (`hidden: 1`).
- `quest_ending.world` cannot be empty, so a failed ending can carry no ending row.
- The new union merge on rebase kept both the old and the new rows of each record changed on both sides, and the
  database did not load. The fix was a re-import on `origin/main`.

## Dialogue (lane D2c, 2026-11-13)

The lines are in `story/data/quest_lines/lq25.json` and `lq30.json`, rewritten into the `infos` shape the compiler
reads; every stale row listed above is replaced. One `dialogue-writer` per speaker with its Morrowind find step,
one `text-review` pass over all four quests. The band and after TSVs under `story/data/dialogue-writer/quest/lq25/`
and `lq30/` stay only while `tools/ArgoniaPlugin/LocalQuests.cs` (the old builder) reads them. The two talk rumours
of item 6 are not quest lines and were not touched here.

Record changes made with the dialogue:
- LQ25: Okan-Zish greets the player after each ending (`topic.lq25-after-exposed-poler`, `-after-quiet-poler`), so
  the man who asked for help says what the choice cost the crew.
- LQ30: Haj-Wan greets the player at stage 0 with the hook (`topic.lq30-greet-waiting`); a wanderer who never asked
  her found no quest.

Fixes from the paper runs, each confirmed by a later careful player:
- LQ25: the bribe prompt now names the deal ("Pay me, and I will say nothing to Sells-Dear"); a careful player had
  asked about the offal only to hear Wuleen-Taza out and found the quest ended with her coin.
- LQ25: the bucket is "left in the shallows", not "still lies" there; two players had already picked it up.
- LQ25 stage 91 and LQ30's walk-home prompt say the consequence in words (the crew have no work at the landing;
  "not even to Haj-Wan").
Ten runs after dialogue (careful and wanderer twice, then a confirming careful each); all LQ25 runs and four of five
LQ30 runs complete. The first LQ30 wanderer started beside the hostile viper (the default start is the first
marker's target) and stopped without a quest; later LQ30 runs start at the gate warden.
