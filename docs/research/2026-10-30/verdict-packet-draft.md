# Owner packet draft: the first-place verdict (1.7)

Draft, 2026-10-30. **Not posted.** The planner posts it through `owner_inbox.py` after game-13's batch
(`tests/journeys/batches/all.yaml`). Lines marked **[from batch]** are filled from that batch; the rest is
measured now.

## What to play
- From the console, type **`bat first-place`**. Walk in from the road and talk to the people of the landing and
  the station. Take the quest and follow the journal to its end at Claywater Station. It takes about 20 minutes.
  Play it once on the phone and once on the Mac.
- Play the **shaders-on** card in Moonlight. Then play the **shaders-off** card.
- Reply on #16 with the machine you want. The numbers are below.

## Five answers (reply yes, no or not yet, and why)
- Does the place feel like Black Marsh up close?
- Does it feel like Black Marsh from the road?
- Does the talk feel like Morrowind?
- Could you follow the quest from the journal alone?
- Is this the game you want?
- Is combat on the tuned stack good enough to carry on with? The Dark Souls map for it is chunk 2.7.

Tell us anything that looked or sounded wrong. Mark the places with **Report here** in the studio.

## What our checks proved
- The in-game batch: **[from batch]** (how many of the 30 checks passed, and what failed).
- The quest's four stages, set by the real talks and items: **[from batch]**.
- **Dark Souls Combat (combat groups B and B2) does not work on our setup.** The behaviour tool loads the mod, but
  none of its moves reach the game. The other tool stops responding. Combat stays on the tuned set that you
  played. Each Dark Souls move that the mod offered goes to that set or to our own build in 2.7.
- **Memory over repeated loads:**
  - a full save load grows the game by about 20 MB each time;
  - the road into Claywater grows it by about 58 MB each time;
  - reloading a single interior does not grow it.
  The batch restarts the game before memory runs out. Whether that restart held: **[from batch]**.

## Frame rate (#16)
- On the current machine (g4dn.xlarge), at Riverwood, with shaders on: 45 fps typical, 32 to 35 fps at the worst
  1%. With shaders off: 53 fps typical, 40 fps at the worst 1%.
- Our bar is 60 fps typical and 45 fps at the worst 1%. Both settings miss it.
- At Claywater: **[from batch]**.
- Stream delay from button to screen: not yet measured on this build. The bar is within 10 ms of your first
  session (about 38 to 40 ms).

## For review
- The combat wiring spec (1.6): [combat-wiring.md](combat-wiring.md).
- The quest, *The Well and the Landing* (1.4): its record is `quest.local.lf83` in the world database. Its lines
  are in `world/db/quest_topic.jsonl` and its journal entries in `world/db/quest_stage.jsonl`.

## Things to look at closely
- Claywater's block has 1,254 things that a player can meet. Each has a verdict: 1,246 keep, 6 restyle and
  2 replace.
- Two outdoor items need checking: the stable by the road (Riften's stable, which is to be replaced) and two
  Skyrim plant names in the huts. You ruled that interiors may look Nordic, so the station house is fine.
- Already fixed: 30 dry-stone walls and a woodpile carried Solstheim's ash and are now plain; the purple mountain
  flower is now a Black Marsh redwort.

## Costs
- AWS this month to date: **$369.56**, over the $100 a month bar. Most of it is the two machines' compute
  ($280.55) and tax ($61.60). Both machines were running when this was drafted. The planner re-runs
  `python3 tools/cost_report.py` when posting.
- Claude usage: **$849 at list price in the last 24 hours** and $865 in the last 30 days. The transcripts on
  this machine cover only the last week or so.

## Parts 2 to 4: the re-estimate
Measured so far:
- one deploy to the game machine takes 336 s;
- one build of the game files takes 2:18 to 2:59;
- the gate takes 1:44 to 1:46;
- a game lane runs 41 to 123 minutes per session;
- Parts 0 and 1 took 60 lane reports and 363 commits over 28 to 30 October.

Assumptions: each Part 2 chunk needs about one build lane and one game lane, as Part 1's did; checks run in one
batch per game session.

The number of days for Parts 2 to 4: **[from batch]**. The batch's run time and its first-pass green count set
how many sessions each chunk needs.

## Your open calls (none answered yet)
- **O-2, subscription.** We are on 5x. Should we move to 20x so that Part 2's two tracks can run at once?
  The cost numbers are in Costs above. We suggest 20x from Part 4 only.
- **O-4, perks.** Should perks stay hidden as an engine layer only? The other option is a Morrowind-flavoured
  perk layer that is shown to the player and merged with vastei. We suggest hidden.
- **O-9, armour pieces.** If we cannot find split pauldron and gauntlet meshes, may paired pieces sit in separate
  slots? Our suggestion is yes.
- **O-11, voice.** Should dialogue stay as unvoiced text? Our suggestion is yes.
- **O-16, rest.** When you rest, should it bank one pending level or all pending levels? We suggest one per rest.

To reply, answer each call by its name, for example "O-11 yes".

## Triage (for your findings)
| # | Finding (your words) | Place or scene | Blocker or polish | Tag (P1 before-scale / P2 rolling / P3 final) | Owning chunk | Fix and status |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
