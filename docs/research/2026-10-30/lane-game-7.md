# Lane game-7: the quarantine, the refs, the door, the rolls (2026-10-30 04:35 to 06:10 UTC; hand-off at the context mark)

## Measured in game (argonia-play, left running)
1. **The quarantine journey is green (0.4 §b, 000cee0).** It ran at days 0, 1, 10 and 50, plus still-here, in 751.8 s.
   Eighteen quests run: ours (ARG_StartQuest, ARG_Q_LF83) and 16 from the allowlist. ARG_MusicSilence played at
   every step.
   - The parse. The console's `sq` returned only the buffer's tail: 1,567 lines, all `(Off)`, with the running quests
     cut off. The bridge now has a `quests` read built on TESDataHandler.
   - What "running" means. CommonLib's `IsRunning()` only means "not stopping", and it was true for 2,385 idle
     quests. Running is now `IsEnabled()`, the same test as the console's GetQuestRunning. The `quest` read changed
     the same way (`not_stopping` keeps the old value).
   - The allowlist ruling is applied in data (data/quarantine/allowed-quests.json), with a reason per row. TK Dodge,
     SkyUI's 7 quests, Precision, TDM and TrueHUD's MCMs, OCPA, the magic config, the ship's 3 quests and EVG's door
     quest stay. Everything else is shelled, including King of the Murkmire's 29 quests and Black Marsh's 01Captain.
     Our own plugins' quests are allowed by plugin. The L2 test (test_quarantine.py, 3 tests) fails on the old code,
     which never shelled KotM.
   - The `music` read crashed the game once (executing at 0x200000000). The current music type is the engine's
     NoMusic, which is not a form. The read now checks the vtable, and NoMusic counts as silence.
2. **Refs by runtime id (the root of claywater-walk's first red).** The game keeps no editor id for a ref, and none
   for most base forms: `player.moveto ARG_Ref_...` and `placeatme ARG_CampSpot` are refused. tools/ref_ids.py writes
   every `ARG_*` word from the formid table as the plugin's runtime prefix plus the local id. The prefix comes from
   the new bridge read `plugin`. A calling ref is quoted (`"100008DB".GetDisabled`). CELL, WRLD, GLOB and QUST keep
   their names. Borrowed-cell refs (KotM's) are named like ours. Bridge `console` and `teleport` calls, the runner's
   scenes, and deploy's scene send (after the launch) all resolve this way. L2: test_ref_ids.py, 4 tests.
3. **claywater-walk is green through step 7 (three runs).** The player enters the station house by its door and comes
   out again. The approach is set in the journey: 70 units out on the porch at heading 212, and 120 units before
   KotM's interior door at heading 0. The **night step is red**: none of the four people runs any AI. At noon and at
   23:00 they read GetCurrentAIPackage -1, with procedure -1 and 49. They stand at their placements. Livia "in
   combat" does not move. Neither the persistence check (11145ea) nor npc-ai's record fix (2b081c7, deployed) changed
   this. The last run was on a fresh deploy with no smoke run before it, so `tai` was not the cause. The vanilla
   control (claywater-control) has not been read yet. The bridge's `booth place` on an actor base crashed the game
   (SkyrimSE+07964F2), so it is not a way to place the control actors.
4. **Rolls and backstep (sheathed, open plain).**
   - Rolls: 338 to 373 units in all 8 directions, each within 1° of its stick.
   - The backstep now fires: 428 and 416 units, `TKdodgeback_two`, 1° off. It works after the fresh base save and
     the burden fix.
5. **Burden lock (combat.cpp's settled pass, 000cee0).**
   - Light: perk rank 1, the roll covered 335 units.
   - 600 ingots: rank 0 and no roll. ArgoniaCore logged "roll locked (burden overloaded)" on the settled pass.
   - Removed: rank 1, the roll covered 332 units, and the log reads "roll unlocked (burden fast)".
6. **The compass is gone.** stack.ps1's INI setter matched the first `bShowCompass` anywhere, a stray line under
   [Display], and left [Interface]'s line at 1. It is now section-aware, drops stray copies, and puts
   bShowQuestMarkers in [GamePlay]. Three play-camera stills show no compass, but **no reader has checked them yet**.
7. **The smoke checks are red.**
   - `pad`: a pad.ps1 call through run.sh timed out (smoke.py:213).
   - `scene`, twice: `input: unknown key in SLASH`. SLASH is now in the bridge's key table, built in deploy 5, but it
     is unknown whether any Stats-menu binding exists under our controlmap.
   - smoke no longer runs `tai`, which toggles the AI of every actor in the game.
8. **first-place, twice:** both runs fail at make-camp (step 3) with WakePoint empty. The scene's travel line is now
   last and the camp spot is placed at the road ref. The sword is now given, but no camp spot shows in the still.
   Either ARG_CampSpot has no mesh or it was not placed. Not diagnosed.
9. Deploys: 487 s full (with vegetation), 279 s full, 122 to 127 s with `--no-plugin --no-stage`.

## Open, in order (next game lane)
1. People run no AI. Run `bat claywater-control` and read the vanilla Golldir against the copy and Livia. The placed
   actors cannot be read by id yet: add a bridge read for the nearest actors, or prid by `pickrefinfront`.
2. first-place make-camp: does ARG_CampSpot get placed, and is it activatable? Then the rest of first-place, twice,
   and then the 60-minute soak (not started).
3. smoke `pad` timeout; the scene's Stats-menu key; then the reader on the menu stills and the compass stills.
4. Not run: stream-e2e, the water frame times, ui-sweep, Block-doubling (it needs the deserter's AI: blocked by 1),
   the timed loop (brief at $scratch/g6/loop-brief.txt), claywater-look (the new house of a6a2748), the world sample.
5. The scenes force weather `fw 0000081A`, which is Skyrim.esm's own clear weather (a vanilla weather; Argonia has no
   clear weather).

Closed: 0.4 §b. Not closed: 0.2 (smoke red), 0.3 §e (the loop not run), 0.4 §d (the night), the world track's L4
lists. Commits: 000cee0, d82e308, 983b022. $scratch is
/tmp/claude-1000/-home-ubuntu-skyrim-argonia/00aec70d-9f88-4179-b6de-7faca8084fef/scratchpad.
