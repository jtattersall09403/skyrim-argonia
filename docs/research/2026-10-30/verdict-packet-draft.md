# Owner packet draft: the first-place verdict (1.7)

Draft by lane 1.7-prep, 2026-10-30. **Not posted.** The planner posts it through `owner_inbox.py` once the game
lane's first-place journey has been green twice. The sections marked TO FILL are filled then.

## What to play
- From the console, type **`bat first-place`**. Play it through: walk in from the road, talk, take the quest and
  follow the journal, fight, die, recover, rest and level. It takes about 30 minutes. Play it on the phone, and once
  on the Mac.
- Type **`bat duel-ring`**. Duel at light, medium and heavy load.
- Stream latency, measured for each device and network: **TO FILL from game-6's stream-e2e**. The bar is within
  10 ms of the 0.0 record (keys 39.6 ms median).

## Five answers (reply yes, no or not yet, and why)
- Does the place feel like Black Marsh, up close and from the road?
- Does the talk feel like Morrowind?
- Could you follow the quest from the journal alone?
- Is this the game you want?
- Is combat on the tuned stack good enough to carry on with? (Its DS1 map is 2.7.)

Add anything that jarred. Use **Report here** in the studio to mark the places.

## For review
- The 1.6 wiring spec draft: [combat-wiring.md](combat-wiring.md).
- The quest, *The Well and the Landing* (LF83): its record is `quest.local.lf83` in the world database (quest,
  quest_stage, quest_objective and quest_topic rows). Its lines are in `world/db/quest_topic.jsonl` and the
  journal texts in `quest_stage.jsonl`.

## Things to look at closely (immersion)
- Claywater's block has 1,254 records a player can meet there, and every one now has a verdict: 1,246 keep,
  6 restyle, 2 replace.
- Four of these need your eyes (named in `data/immersion/verdicts.jsonl`):
  - the stable by the road (Riften's stable, to be replaced);
  - the station house and its door (Skyrim's farmhouse shape under a Black Marsh texture);
  - two Skyrim plant names in the huts.
- Fixed before you play: 30 dry-stone walls and a woodpile carried Solstheim's volcanic ash, and are now plain;
  the purple mountain flower is now a Black Marsh redwort.

## Costs
- AWS this month to date: **$360.50**, over the $100 a month bar (EC2 compute $275.42, tax $60.09). Both machines
  were running when this was drafted. Re-run `python3 tools/cost_report.py` at posting.
- Claude usage, last 24 hours: $634.85 at list price.

## The re-estimate of Parts 2 to 4 (an extrapolation; the assumptions are stated)
Measured cycle times:
- one deploy is 336 s (lane-game-5: plugin 10 s, push 90 s, skse 103 s, ESMs 17 s, launch 116 s);
- `make plugin` takes 2:18 to 2:59;
- `make check` takes 1:44 to 1:46;
- game lanes run 41 to 123 min per context (game-3 00:50 to 02:40, game-5 02:35 to 03:16, 0.2-stack 20:17 to 22:20).

Assumptions:
- each Part 2 chunk needs about one build-VM lane and one game lane, as Part 1's chunks did;
- one in-game batch is a deploy plus about 30 minutes of journeys.

**Not given as a number yet.** Part 1's per-chunk lane counts and its total wall time are not summed in one place.
The planner sums them from PROGRESS before posting; this draft invents none.

## The open calls (each needs your ruling)
- **O-2, subscription.** We are on 5x now. Do we move to 20x for Part 2's two tracks (the systems track and the
  world track at once)? The measured numbers are above. The default is 20x only from Part 4.
- **O-4, perks.** Should perks be an invisible engine layer only, or a visible Morrowind-flavoured perk layer
  merged with vastei? The default is the invisible layer.
- **O-9, armour pieces.** If no split pauldron and gauntlet meshes can be sourced, may paired pieces sit in
  separate slots? The default is yes.
- **O-11, voice.** Should dialogue stay unvoiced text? The default is yes.
- **O-16, rest.** Does one rest bank one pending level, or all of them? The default is one per rest.

## Triage (for your findings)
| # | Finding (your words) | Place or scene | Blocker or polish | Tag (P1 before-scale / P2 rolling / P3 final) | Owning chunk | Fix and status |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
