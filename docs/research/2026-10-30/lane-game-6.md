# Lane game-6: the coc crash, the base save, rolls on the plain, the journeys (2026-10-30 03:20 to 04:30 UTC; hand-off at the context mark)

## Measured in game (argonia-play, left running for the next lane)
1. **The crash, diagnosed and fixed (d146564).** `coc ARG_HoldingCell` died at SkyrimSE.exe+0327DC4 with RDI = BGSMusicType
   ARG_MusicSilence (0F000801): every MUSC we wrote had no track, and every vanilla MUSC has one (vanilla _NONE plays the
   silent track 0137FA). Every MUSC now carries `skyrim_units.SILENT_MUSIC_TRACK`, and the writer refuses an empty one.
   Second cause, from the crash log's load order: Argonia.esm named Cipactli.esp but not its master HTBM.esp, so the engine
   hoisted Cipactli above HTBM (slots D and 14). Generate.cs now lists every master's own masters.
2. **The gate:** `ArgoniaGen links` (tools/ArgoniaGen/LinkCheck.cs) runs in plugin-check against the staged profile's
   plugins.txt, in the engine's order (masters first, ESP masters hoisted). It checks that every FormLink resolves as its
   type (Argonia.esm 404 targets, ArgoniaWorld.esm 86, 0 bad), that every master loads first, that every master's
   masters are listed, and that every MUSC has a track. Made to fail once: on the old ESMs it reported 102 trackless
   MUSCs and 3 master findings. Run time 18 s, 637 MB.
3. **The base save** `argoniabase`: a new game in ARG_HoldingCell in 7.9 s, 11 to 13 s in all. The bare `make deploy`
   took 160 to 162 s (SKSE build 42 s, launch 62 to 118 s).
4. **The quarantine shelled the dependency mods' own start quests** (TK Dodge's controller, which gives the roll's perk;
   SkyUI's MCM; the ship's input quest). It now shells only the base game's and the Creation Club's (L2 test_quarantine).
   King of the Murkmire's quests now run: a content call for the owner, if they should not.
5. **The coc test kit** (96.5 kg of iron gear) put the sheet-less studio character at overloaded (Str 0, carry 30 kg),
   so the perk lock held every roll. base_save.py strips it (0a126bd); carried 0.00 after.
6. **The rolls on the open plain** (tamriel 10700,-13025, third person, perk lock on), by the roll's own distance:
   - Sheathed: N 351, NE 356, E 363, SE 354, S 361, SW 347, W 367, NW 360. Every roll is within 1° of its stick.
     The backstep did not fire (0 units).
   - Drawn: N 315, NE 282, E 292, SE 321, S 322, SW 342, W 327, NW 304. The backstep covered 420 units, 45° off.
7. **The burden lock** (perk FE00D809):
   - Light: perk 1, the roll 300.
   - Overloaded (600 ingots): no roll, and the walk fell to 102 units against 481.
   - The tier lags one change behind. ArgoniaCore logged "roll locked (overloaded)" only at the removal, and left the
     roll locked at 0 kg. The cause is that TESContainerChangedEvent comes before the item moves.
   - The fix is uncommitted in skse/ArgoniaCore/src/combat.cpp: a second pass 500 ms after a carried change. It is not
     yet built or checked.
8. **The greeting read:** `bridge.py greeting <speaker id>` (0eb061d) returns the dialogue.state that ArgoniaCore opens
   on. The well-keeper at disposition 0 reads "The station is open. What do you want?". `npc.nobody` is refused.
9. **The journeys:**
   - `smoke` passed twice (173.6 s and 206.7 s).
   - `broken` fails at stand-still with "moved 0 units, wanted gt 100" and a still.
   - A forced crash is reported in 19.5 s.
10. **Two crashes came from scene lines that ran after a `cow` in the same bat** (setpos/fw during the load,
    SkyrimSE+0EAE206, BSMultiBoundAABB). Every scene now ends with its travel line, and the scene-author skill says so.
11. **The idle-stop fix:** bridge calls refresh the busy flag every 240 s (8aa0ff3, an L2 test made to fail once). Since
    then the machine has not stopped mid-lane.
12. **No compass, not yet:** the play camera still shows the compass. A --no-stage deploy left an old stack.ps1 on the
    machine, without the SkyrimPrefs lines. I pushed it by hand, and deploy.sh now sends stack.ps1 and bridge.ps1 every
    time. The next launch has to confirm the compass is gone.

## Open reds, in order (next game lane)
1. **quarantine** fails at day-0: 1,567 "running" quests, starting AchievementsQuest and ArenaCombatQuest00.... The
   `sq` parse in run_journey.running_quests() likely counts every listed quest, not the running ones. Read one `sq`
   output, fix the parse (L2 test), then re-run at days 0, 1, 10 and 50. MQ101 reads running=true, enabled=false in the
   base save.
2. **claywater-walk** fails at "arrived": GetInWorldspace ARG_Province is 0 after `player.moveto
   ARG_Ref_ClaywaterStationRoadIn`. Check that the ref is persistent and that the moveto lands. The must-fail copy
   (scene holding) fails at the same step, as it should.
3. Build and deploy combat.cpp's settled pass, then re-run the burden script
   ($scratch/g6/burden.py: light, overloaded, after).
4. The sheathed backstep (0 units), against game-5's 320.
5. Not run:
   - `smoke.py pad`; `scene` twice with the reader on the menu stills;
   - `stream-e2e` (infra/stream-client/e2e/e2e.sh);
   - the water frame times ($scratch/g5/water_ft.py);
   - `ui-sweep` (still a draft: run `smoke.py menus`, and give the stills to a reader);
   - the Block-doubling check. Block is not pinned (kPinned is OneHanded, TwoHanded, Marksman), so the vanilla
     Block term is live. Measure a blocked hit at Block AV 15 against 100 in `bat claywater-ambush`.
6. **The timed loop (§e).** The brief is ready at $scratch/g6/loop-brief.txt. Give it to a deliver-small with
   `make deploy DEPLOY_ARGS="--no-stage"` and the greeting read, the machine stopped first, and record the cycle in
   journals/bridge.md.
7. `claywater-look` and the reader. Then the closes: 0.2 (but the frame bar, #16), 0.3 (Papyrus #15), 0.4 §b, the
   Outcomes and PROGRESS rows. **None is written yet**, because quarantine and claywater-walk are red.

`make check` was green at d146564 (CHECK GREEN, 286 pytest, 29 ctest). $scratch is
/tmp/claude-1000/-home-ubuntu-skyrim-argonia/00aec70d-9f88-4179-b6de-7faca8084fef/scratchpad.
