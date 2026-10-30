# Lane game-3: 0.2 on the game machine, continued (2026-10-30 00:50 to 02:40 UTC; hand-off at the context mark)

Commits: 33b0c26 (the dodge fix, the bridge's `graph` read, smoke changes) and the hand-off commit (this report,
the frame-time journal, the ArgoniaCore lay and the bridge timeout).

## Done and measured
1. **The dodge's cause was found and fixed.** Pandora's `animationdatasinglefile.txt` had no motion for TK
   Dodge's clip generators (TKDodgeBack, TKDodgeLeft, TKDodgeRight, TKDodgeForward), so the rolls played in
   place. `infra/gpu-box/animdata.py` (unit-tested) copies the motion from the vanilla Dodge* clips.
   `stack.py install` runs it after Pandora (`stack.py animdata`), and it has been applied on argonia-play. On
   QASmoke's open floor, the roll's own distance in units:

   | Roll | Sheathed | Sword drawn | Before the fix |
   |---|---|---|---|
   | Backstep | 121 | 213 | 0.0 |
   | Forward | 443 | 441 | - |
   | Back | 128 | 209 | - |

   **Side and diagonal rolls are still short: 2 to 126 units.** Under TDM's free movement the character has turned
   to the stick before the side clip plays. Dynamic Dodge's direction variants need a target lock or Keytrace.esp.
   The bisect's claim that all motion was zeroed was wrong: a forward power attack moves 468 to 486 units with any
   behaviours. `bAnimationDriven` is not the switch. The full table is in `journals/stack.md`.
2. **Bridge: a new `graph <actor> <name>...` read** (bool, int and float). It is built, live and used. ctest
   27/27 on MSVC.
3. **ArgoniaCore is deployed for lane 1.1.** It loads on 1.7.104, and the 9-family co-save round trip passes.
   The intercept perk and the ARG_WChance globals are missing because Argonia.esm is not laid. `bridge.ps1 prepare`
   now copies ArgoniaCore.dll into Data until `make deploy` lays our mods.
4. **Frame time on the g4dn.xlarge** (Riverwood, Defender quiet):

   | Community Shaders | Frame cap | Median fps | 1% low fps | GPU use | CPU use |
   |---|---|---|---|---|---|
   | on | capped | 42.4 | 22.1 | 42 % | 61 % |
   | on | uncapped | 44.5 | 23.8 | 43 % | 59 % |
   | off | uncapped | 52.5 | 25.4 | 40 % | 65 % |

   **The game is CPU-bound, and no CS setting can meet the bar,** because CS off misses it too. PresentMon
   records no presents even in the desktop session, so the bridge's frame times and nvidia-smi stand in for it.

## Next lane, in order
1. **Try the g6.xlarge** (the second fallback; owner-authorised):
   - Stop the machine with `run.sh stop` and record the type (g4dn.xlarge, spot `sir-k9bzpisj`, eu-west-2a).
   - Run `aws ec2 modify-instance-attribute --instance-id i-0a3a6d5d93f8dfcb2 --instance-type
     Value=g6.xlarge`. A persistent spot instance may refuse the type change; if it does, record it and use
     `clone.sh`.
   - Run `run.sh up`, then check that `nvidia-smi` names the L4 (GRID 596.86 should support it).
   - Run the scratch `g3/ft.py` with the same three variants.
   - If the bar is still missed, write the measured options for the owner (the re-plan trigger).
2. **Side and diagonal rolls:**
   - Measure the 8-way with a lock on (RS on the wolf).
   - Decide unlocked behaviour. DS1 rolls forward along the stick, which here needs TK Dodge to send
     TKDodgeForward whenever TDM is free.
   - Add Keytrace if Dynamic Dodge's 8-way is wanted.
3. Game-2's remaining list:
   - `smoke.py pad`;
   - `scene` twice, with a reader on the menu stills;
   - the Papyrus helper-cut proof from `Papyrus.0.log`;
   - `stream-e2e` latency;
   - the uncapped water frame times;
   - close 0.2: infra/README, decision 0007, the Outcome, 0.3's Starting state, PROGRESS;
   - mark 0.3 §a done;
   - 0.3 §b: the Creation Kit for the .pex, then `ArgoniaCore.Version()` through the bridge.

## Machine state
Running at Riverwood with the profile on and nothing aside. The patched animation data is laid, and
ArgoniaCore.dll is in Data. Defender is untouched.

## Gate
`tools/tests/test_animdata.py` passes 4 of 4, and the C++ ctest passes 27 of 27 on the machine. `make check` was not
run. `tools/tests/test_bridge.py` failed with "No module named 'tools'" when run outside make; re-check it under
`make check`.
