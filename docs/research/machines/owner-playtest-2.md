# Owner play test 2 (2026-10-31, Paris, the build of a04fa6d deployed at cc4b9c4) and the HUD fixed in game

## The owner's verdicts (chat, 2026-10-31)
- "ArgoniaWalk does load." (1.9 walk save)
- "Loading screens look OK for now. Main menu looks OK for now." (1.9: classic loading screens, no scrolling bar,
  the front door)
- "The player character has been fixed." (1.10)
- "Basically everything from 1.8 to 1.11 is done except the HUD update."
- The HUD: "hasn't been updated at all"; "we end up with two stamina bars".
- "There are lots of other issues in game right now but don't worry about those yet."

## The HUD, diagnosed and fixed
- **Not updated:** deploy never rebuilt the views; worktrees linked the main tree's out/ui, built at 04:00, before
  the redesign. Deploy now builds the views and the theme from source (e01be6c); worktrees no longer link them.
- **Two stamina bars:** not Skyrim's (the log: "vanilla-hud hidden 11/11"); TrueHUD's player widget drew its own
  bars. `bEnablePlayerWidget = 0` in TrueHUD's row (e01be6c); its enemy and boss bars and lock-on stay.
- **Vastei shown 0 while ArgoniaCore held 180:** vastei rode only in the full HUD state; a change now pushes it
  (a5abfd5), with the +N cue on a rise (64d9eae), shown ~2 s then gone (5efb33d).

## In game (L4, argonia-play, ArgoniaWalk, tests/journeys/batches/lane-1.11.sh, rc 0 three times)
Stills in /home/ubuntu/wt-paris-hud/out/l111 (archived with the worktree by tooling/disk.sh): calm, a hit (six),
regen, low, stamina-used, vastei-gain, vastei-later. Read by the coordinator: one set of framed bars top left with
recessed tracks; one stamina bar after stamina is drained (no TrueHUD widget); health falls on the hit and refills;
vastei top left reads 180 with "+180" on the gain and plain 180 after; nothing overlaps. Not seen in stills: the
damage trail (it lasts ~1.4 s; a still takes longer).
