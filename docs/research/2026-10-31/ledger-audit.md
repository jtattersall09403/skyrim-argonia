# Ledger audit (2026-10-31): every in-game check in Parts 0 and 1 and 2.W1–2.W4

The owner asked (2026-10-31) whether we have kept a record of everything that was meant to be checked in game, and
what has been checked. This audit read PLAN's goals for Parts 0 and 1, both part READMEs (their exits and the world
sample), and every chunk brief in docs/phases/0-foundation/ and docs/phases/1-core-loop/ (2.W1–2.W4 included). It
then found the evidence for each check: the run history (merged across every worktree's out/batch and out/runs,
because lanes g18e, g19 and g21 kept their own), the lane reports, commits and owner-brief rows.

The result is two ledgers: [Part 0](../../phases/0-foundation/checks.md) and
[Part 1](../../phases/1-core-loop/checks.md). They replace the hand-made in-game-owed.md, which has been deleted and
its links fixed.

## What is now standard

- `tools/check_ledger.py` runs in `make check` as the `ledger` part. It checks that every row has a valid Status,
  that each proven or dropped row's evidence resolves (a commit, a file and its line, a journey, an owner-brief
  date), that every `journey:` token names a journey, and that every journey in `batches/all.yaml` appears in a
  ledger. Tests: `tools/tests/test_check_ledger.py`, covering a good ledger, nine seeded bad rows and a batch
  journey missing from every ledger.
- `tools/run_batch.py` rewrites every `journey:<id>` row at the end of each run. A pass sets the row proven with
  its run dir. A fail sets it owed with the failing run. A `journey:<id>#<prefix>` row follows only the steps with
  that prefix (the world-sample stops, die-and-recover's pile), and a row whose steps the run never reached is left
  alone. Dropped rows never change. The lane commits the rewritten ledgers with its report.
- CLAUDE.md (60f733d) already makes a ledger row due from the moment a brief is written.

## Counts

| Chunk | proven | owed | dropped |
|---|---|---|---|
| 0.0 | 4 | 0 | 0 |
| 0.2 | 3 | 4 | 1 |
| 0.3 | 6 | 0 | 0 |
| 0.4 | 4 | 2 | 1 |
| 1.1 | 2 | 1 | 0 |
| 1.2 | 5 | 10 | 0 |
| 1.3 | 3 | 3 | 0 |
| 1.4 | 4 | 1 | 0 |
| 1.5 | 4 | 5 | 0 |
| 1.6 | 5 | 0 | 2 |
| 1.7 | 2 | 5 | 1 |
| 2.W1 | 4 | 1 | 0 |
| 2.W2 | 4 | 2 | 1 |
| 2.W3 | 3 | 1 | 2 |
| 2.W4 | 3 | 3 | 1 |
| **Total (103)** | **56** | **38** | **9** |

The ledgers are newer than PROGRESS and the briefs' Outcomes in two places:
- world-sample passed all 13 stops in game-21's run out/batch/adhoc/20261031T103633 (s09, the border, included);
- smoke, attributes, quest-board, fight-archetype, grow-at-rest, lf83-components and ui-probe have passed since
  in-game-owed.md's table.

`run_batch --owed` in the main tree still shows those journeys as failed, because it reads only that tree's out/.

## Mapping: each acceptance line that needs the running game, and its row

Rows are named by ledger and chunk section, then the row's opening words.

**0.0**
- the owner's "playable" → P0 0.0 "The owner calls a setup playable";
- latency logged → P0 0.0 "Latency and stream health";
- frame time 60/45 → P0 0.0 "Frame time at least 60";
- combat verdict → P0 0.0 "The owner's combat verdict".

**0.2**
- §b install and verify → P0 0.2 "`stack.py verify`";
- §c dodge and pad: rolls → "Rolls cover distance"; RT → "RT power-attacks"; LB block → P0 0.2 "The smoke journey"
  (its block step); RS lock-on → P1 1.6 "Lock on by R3";
- §c scene: walk, draw, swing, roll, block, menus → "The smoke journey"; climb, ladder, boat → "Climbing
  (FreeClimb)"; swim and dive → "Swimming and diving"; parry → P1 1.6 "Guard, parry and riposte"; twice with no
  crash → "The smoke scene passes twice"; each menu's paper theme → P1 1.2 "The sweep of every menu";
- §d → P0 0.2 "Frame times on the play machine".

**0.3**
- §a, and §d's ten scenes → "The bridge answers";
- §b → "ArgoniaCore loads" and "The Creation Kit compiles";
- §d → "The smoke journey" (P0 0.2), "A broken journey" and "A forced crash";
- §e → "One unattended edit".

**0.4**
- §b → "The quarantine";
- §d:
  - the road into the place and an interior → "The player walks the road";
  - heights within 0.5 m → P1 2.W1 "Stop 1";
  - grass, trees, and each person's full-body still → "Vantage and full-body stills" and "A reader passes the
    block's stills";
  - the people path between spots → "The three people path" (dropped);
  - sleep at night → "A person sleeps in her own bed";
- Part 0 exit: the owner's walk, climb, swim and boat → "The owner walks Claywater".

**1.1**
- save, quit, reload, read back → "Every co-save family";
- a view with live data at L4 → "A view opened from the schema";
- the router's intercept → P1 1.2 "Our dialogue window opens";
- the reset leaves nothing → "The scene-reset path".

**1.2**
- readable on the folded V5 → "Text readable on the folded Magic V5";
- no vanilla dialogue menu → "Our dialogue window opens";
- §0 → "The screen technology's numbers";
- §a:
  - the sweep → "The sweep of every menu";
  - the reader → "A reader's Nordic-tells pass";
  - the owner's before-and-after still → "The owner sees a before-and-after still";
  - favourites → "Favourites open on D-up";
  - quit → "Quit from the menus";
- §b → "Our dialogue window opens", "Our screens in play", and the L5 hand-off "The dialogue and journal open and
  close hand-offs";
- §c → "Our screens in play" (the journal's entry), "B closes the journal", "Touch B closes the journal" and the L5
  row;
- §d → "The HUD's states", "Our HUD is hidden over the loading screens" and the V5 row;
- §e → "The HUD's states" (the chart opens and reveals, in ui-probe) and "The chart closes".

**1.3**
- §a five characters → "Every derived value read for 5 test characters" (plus the implied mirror check,
  "Every attribute equals");
- §b:
  - A to B → "A topic learned";
  - disposition variants and the essential topic → "Low and high disposition";
  - the learned set across a save → P1 1.1 "Every co-save family";
- §c:
  - slots and paperdoll → "Each slot stacks";
  - burden thresholds → P1 1.6 "The roll is locked when overloaded";
  - Long Blade → "A swing trains Long Blade".

**1.4**
- start in dialogue → "LF83 starts";
- read the entry, follow, act, return, consequence, journal stage → "Each stage set by its real path", "The four
  endings", "The assault is reported" and P1 1.7 "The first-place walk-through";
- the quest across a save → P1 1.1 "Every co-save family";
- no marker → "A reader confirms no marker";
- the owner follows it from the journal → P1 1.7 "The owner plays `bat first-place`".

**1.5**
- skill uses to spend → "Skill uses, a pending level";
- die, wake, pile → "Die with vastei" and "A still of the pile";
- a second death → "A second death";
- the archetype respawns → "The archetype respawns";
- every family across a save → P1 1.1 "Every co-save family";
- the L5 sitting hand-off → "The rest-to-sitting hand-off";
- implied → "A clearable place", "Rest is the only save" and "The suspend save".

**1.6**
- draw, lock on, roll, guard, parry, riposte, kill, loot → "Group A wired", "Lock on by R3", "The deserter's record
  values", "The crocodile" and "Guard, parry and riposte" (dropped);
- a hit trains Long Blade → P1 1.3 "A swing trains Long Blade";
- the respawn → P1 1.5 "The archetype respawns";
- the five-minute loop → "A five-minute duel loop" (dropped);
- combat to the bars → P1 1.2 "The HUD's states";
- the owner's verdict → P1 1.7 "The owner plays".

**1.7 and the Part 1 exit**
- the batch → "The whole batch";
- first-place → "The first-place walk-through";
- immersion → "No Nordic element";
- the cards → "The Moonlight cards launch" and "The owner plays the shaders-on";
- frame times → P0 0.2 "Frame times on the play machine";
- latency → "The stream latency";
- the five answers → "The owner plays `bat first-place`";
- the soak → "The 60-minute soak".

**2.W1**
- §a probes → "Stop 1", "Stop 2" and "Stop 3" (the 1,000 points are met by L1 and the sample, the Part 1 README's
  world-sample note);
- 20 vantage stills → "A reader finds no obvious texture tiling";
- §b the border → "Stop 9";
- the apron → P1 2.W2 "Stop 7".

**2.W2**
- stops 4 to 7 → "Stop 4" to "Stop 7";
- stop 12 → P1 2.W4 "Stop 12";
- implied by its Loops and Outcome → "The plane budget's frame time", "Mist stills" and "The player swims"
  (dropped).

**2.W3**
- §a:
  - the 7-day skip → "Stop 11";
  - 12 weather stills → "A reader panel on 12 weather stills" (dropped);
  - the interior sun (Loops) → "The interior sun";
- §b:
  - road legs → "Each road leg" (dropped);
  - gates → P1 2.W1 "Stop 9";
  - signposts → "Stop 10";
- Outcome → "Tear Road Stage" and P1 1.4 "The assault is reported".

**2.W4**
- §a → "Stop 8" and "The densest 10 cells";
- §b:
  - 200 path requests → "Stop 12" (the README's sample note);
  - 20 NPCs on sandbox packages → "20 NPCs on sandbox packages" (dropped);
- §c → "Stop 13" and "Distant terrain (xLODGen) restored";
- the L5 hand-off → "The near-to-LOD hand-off".

**Dropped rows and their rulings.** Each cites an owner-brief row:
- 2026-10-30, the soak dropped;
- 2026-10-30, no arena, and the fight checks simplified;
- 2026-10-30, NPC movement is not checked;
- 2026-10-30, base-Skyrim behaviour is not checked (weather stills, swimming).

Flag: the road-hops drop cites the 2026-10-30 row "the one-hour road walk is dropped". The only text that names
w3-road-hops is 2.W3's Outcome ("owner ruling 2026-10-30"), and no owner-brief row names it. The planner should
confirm it with the owner or reinstate the check.

## The missed checks

These checks were owed, but none was ever run or ever added to the batch. They are ranked by what the player would
meet.

1. **The owner's own play of the thread** (`bat first-place`, the five answers), the Moonlight cards and the
   latency on the owner's device. Never posted. The Part 0 owner check (walk Claywater, climb, swim, boat) never
   ran either; it rolls into this packet.
2. **No Nordic element outdoors: a reader on the block's stills, and on the immersion rows the owner meets.** No
   reader report is on record for claywater-look's stills, for the full-body faces (seams, dark face) or for the
   sweep's menus. This is a blocker class (CLAUDE.md), and it is unproven.
3. **Climbing, ladders and the boat.** These are in the goal (owner, #11) and in 0.2 §c's scene, but no journey or
   run covers them. Whether each mod is wired and loaded has never been checked.
4. **Carry and equip.** No journey runs the brief's take-the-sword-and-cuirass, equip, paperdoll still and read the
   book steps.
5. **Talk variants.** No run on record shows low and high disposition giving different variants, or an essential
   topic answering at disposition 0.
6. **The 0.2 §d frame times on the g6** against the revised bar, and the 1.2 §0 numbers that follow from them. Not
   measured: the run died at the stop.
7. **Distant terrain restored, with a Claywater still judged.** The terrain was lost with the g4dn and is queued in
   game-21. Stop 13 passes only as stills.
8. **Text readable on the folded V5 (the drive.sh phone runs) and touch B on the journal.** Not run.
9. **The densest 10 cells with a reader on Nordic flora** (`w4-veg-densest`), **the plane budget's frame time**
   (`water-budget`) and **the clearable place** (`rest-respawn-cleared`). These are drafts that were never added to
   the batch.
10. **Smaller rows never run:**
    - the derived values for 5 characters;
    - the scene-reset read;
    - the no-marker reader on the quest stills;
    - the pile still;
    - RT power attacks;
    - the texture-tiling reader;
    - mist stills;
    - Tear Road Stage;
    - the three L5 hand-off clips (dialogue and journal, the sitting, LOD).

**Owed, and being worked on.** These are in the batch but red:
- ui-sweep (favourites);
- menus-quit (no MainMenu after quit);
- die-and-recover (the deserter does not kill, so the death is never reached);
- ui-review;
- `stack.py verify` (2 bad hashes);
- our HUD over the load screens.

Until these pass, the 1.7 batch cannot be green.
