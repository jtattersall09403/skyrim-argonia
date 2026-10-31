# Owner packet draft: the morning packet for the first-place verdict (1.7)

Draft, refreshed 2026-10-31. **Not posted.** The planner posts it through `owner_inbox.py` once tonight's last batch
has run. Every number that depends on that batch is marked **[from batch]**. The rest is measured now. The verdict
questions are on issue #19.

## How to play
- Open the play page and start the Moonlight card **Argonia (shaders on)**. Later play **Argonia (shaders off)**.
  Tell us which looks and runs better (#16). Play once on the phone and once on the Mac.
- In the game console, type `bat first-place`. It puts you on the road to **Claywater**, the landing and the
  station. About 20 minutes.
- What to try, in this order:
  1. Walk in from the road and talk to **Livia**, the well-keeper. Ask her about the topics she offers.
  2. Take the quest, *The Well and the Landing*, from the people there.
  3. Follow the journal. It should tell you the next step by itself. Open it with the Back button on the pad, or with J.
  4. Trade with Livia: ask to trade, then buy and sell something.
  5. Fight the deserter on the road. Try the lock-on (R3) and a roll (B while moving).
  6. Let him kill you, then get your vastei back from the pile where you fell.
  7. Make camp and rest. Notice the level you can take, and that the deserter comes back.
- Tell us anything that looked or sounded wrong. Use **Report here** in the studio to mark the place.

Answer the five verdict questions on #19.

## What changed overnight
- **The map and journal close properly.** B, Tab, M and the touch Close button all close the map. B closes the
  journal without making you roll; B while moving still rolls.
- **Favourites work.** Q on the keyboard and D-up on the pad open them once you have favourited something.
- **Livia now trades.** She is Claywater's general trader, using Skyrim's own trading system.
- **Dialogue and journal screens were redesigned** after we looked at them in game: the window sits lower so you
  see the speaker, topics have more room, the journal names the quest on its own line and shows "Pages 1-2 of 6",
  and the trading list is tidier. People now start with a sensible attitude (the bar was empty for everyone).
- **Resting only resets our own people.** It used to reset about 2,930 Skyrim actors; now only Argonia's. The
  deserter returns after a rest; the crocodile does not.
- **After you die, you now wake up able to act,** so you can pick up the vastei pile. Whether this works in
  play: **[from batch]**.
- **Enemies are armed.** The deserter had his sword and shield in his bag but held nothing. He now wears them and
  fights with them.
- **The mortar tub** in the quest no longer sits under the well head, so you can use it.
- **Two crashes are fixed.** Growing a level in a fight no longer crashes the game. The test tours no longer
  crash the game when they travel between places.
- **Phone:** touch buttons are held long enough to register (the journal closes, heavy attacks fire) and the
  folded phone puts its buttons beside the picture, not over the health bars.
- **Dark Souls Combat (combat groups B and B2) does not work on our setup.** Combat stays on the tuned set you
  played; each Dark Souls move goes to that set or to our own build in 2.7.

## What our checks proved
- The in-game batch: **[from batch]** (journeys passed of those run, and what failed). The last full snapshot,
  before the fixes, was 18 passed, 14 failing, 3 drafts (`docs/phases/1-core-loop/in-game-owed.md`).
- The quest's stages, set by the real talks and items: **[from batch]**. In the last run first-place passed on
  its first try and the quest's four endings passed.
- Respawn: the deserter respawns and the crocodile does not (proven, 3 runs).
- **Memory over repeated loads:** a full save load grows the game by about 20 MB; the road into Claywater by about
  58 MB; reloading one interior does not grow it. The batch restarts the game before memory runs out. Whether that
  held: **[from batch]**.

## Frame rate (#16)
- On the old machine (g4dn.xlarge) at Riverwood: shaders on 45 fps typical, 32 to 35 fps at the worst 1%; shaders
  off 53 fps typical, 40 fps at the worst 1%. That is below your bar of a 60 fps median (50 acceptable), with 95% of frames at or above 45.
- Claywater on the g4dn: **[from batch]**. On the g6.xlarge you approved: **[from batch]**; the move to it is not done yet.
- Stream delay from button to screen: 35.6 ms median, measured on the build machine's emulated client. A real
  device is for you to feel.

## For review
- The quest's dialogue, *The Well and the Landing* (#14): its lines are in `world/db/quest_topic.jsonl`, its
  journal entries in `world/db/quest_stage.jsonl`.
- The combat wiring spec (1.6): [combat-wiring.md](combat-wiring.md).
- Claywater's block has 1,254 things a player can meet: 1,246 keep, 6 restyle, 2 replace. Two outdoor items need
  your eye: the stable by the road (to be replaced) and two Skyrim plant names in the huts. Interiors may look
  Nordic by your ruling.
- Already fixed: 30 dry-stone walls and a woodpile that carried Solstheim's ash; the purple mountain flower is now
  a Black Marsh redwort.

## Costs
- AWS this month to date: **$374.19** at 2026-10-31 (`python3 tools/cost_report.py`), over the $100 a month bar;
  compute $283.55, tax $62.36, other $28.28. Three machines were running when this was drafted. Re-run in the
  morning: **[from batch]**.
- Claude usage (`python3 tooling/session_tokens.py`): **$506.64 at list price in the last 24 hours** and
  **$1,010.46 in the last 30 days**. Re-run in the morning: **[from batch]**.

## Parts 2 to 4: the re-estimate
Measured so far: one deploy takes 336 s; one build of the game files 2:18 to 2:59; the gate 1:44 to 1:46; a game
lane 41 to 123 minutes; Parts 0 and 1 took 60 lane reports and 363 commits over 28 to 30 October. The days for
Parts 2 to 4 depend on the batch's run time and first-pass green count: **[from batch]**.

## Your open calls
None of these is answered in the owner brief or the decisions index. Reply with the call's number, for example 'O-11 yes'.
- **O-2, subscription.** Stay on 5x, or move to 20x so Part 2's two tracks run at once? We suggest 20x from Part 4
  only. Costs are above.
- **O-4, perks.** Hidden engine layer only, or a visible Morrowind-flavoured layer merged with vastei? We suggest
  hidden.
- **O-9, armour pieces.** If we find no split pauldron and gauntlet meshes, may paired pieces sit in separate
  slots? We suggest yes.
- **O-11, voice.** Keep dialogue as unvoiced text? We suggest yes.
- **O-16, rest.** Should one rest bank one pending level, or all? We suggest one per rest.

Already answered, so not asked: #16's machine move (g6.xlarge) and the frame bar; respawn; Nordic interiors.

## Not fixed, and why
Empty until the morning. You ruled that fixes come before deferrals. Anything not fixed tonight is listed here with the reason it could
not be.

## Triage (for your findings)
Blocker means you cannot do the action, or you see a Nordic element at the play camera. Polish means anything else.

| # | Finding (your words) | Place or scene | Blocker or polish | Tag (P1 before-scale / P2 rolling / P3 final) | Owning chunk | Fix and status |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
