# Lane game-22 (2026-10-31): loading screens, the three reds, LOD restore (London)

Machine: argonia-play-london only. Worktree /home/ubuntu/wt-g22. Batch g22-b1: out/batch/adhoc/20261031T120411.

## Fixed and proven
- **Our HUD over the load: fixed (L4, reader).** Menu events during a moveto showed the Loading Menu *does* open
  (seq 46, 70; game-21's "no open" read came from a load too fast to catch). The black frames around it are the
  Fader Menu and the Mist Menu, open for 2.5-12 s around a Loading Menu of 0.8-9 s, and the hide covered the
  Loading Menu only. Now `router::hides_hud_at_once` covers Loading, Fader and Mist. HudLoading keeps a set of the
  open load menus, hides the HUD on the first and shows it on the last, and logs `views: hud hidden for the load`.
  Unit tests: 33/33. In game, the log line came at the Loading Menu's open. The reader saw no HUD on either load still.
- **Our loading screen shows (reader):** the sheet and our fact text ("Teeba-Hatsei, or 'Hip and Tail Ball'...").
  So our 12 LSCRs are eligible.
- **LOD restore: proven, and deploy now does it.** `lod.sh ensure` (deploy's "lod" step before the launch) compares
  `argonia-lod.key` in the LOD mod with the ArgoniaWorld sha12. On a mismatch it restores from
  s3://argonia-private-…/lod/<sha12>.tar. With no archive it prints a loud WARNING and keeps the old LOD. On London
  the archive is fd21cee6d408 (610 MB), and the deploy logged `LOD restored: 20601 files`. The Claywater distant
  still (`lod.sh still`) was NOT taken: the planner stopped the lane.

## BLOCKER found (not fixed: tools/ui_theme is outside this lane)
- **The loading sheet has a Celtic-knot frame** at the top and bottom centre and all four corners (reader, 2 of 2
  stills). It comes from the Oblivion-like Loading Menu (38708) loadingmenu.swf, which tools/ui_theme/retheme.py
  recolours but does not clear. Fix at source: add the knot bitmap(s) to retheme.py `CLEAR` (path and measured size),
  or replace the frame. Then rebuild argonia-theme. The reader also notes the player's hair is neon yellow-green
  (a tint bug?).

## Diagnosed, still red (g22-b1: 0/3)
- **die-and-recover:** a native kill now replaces the deserter's AI. The deserter stays disabled after the rest,
  and each death is `player.damageav health 1100`, the essential player's lethal blow into our bleedout intercept.
  The journey now passes setup, rest, earn, die, woke-at-camp, take-pile and second-death, and fails only at
  third-death-replaces: `ARG_VasteiPileActivator enabled = 0`. The death with an untaken pile left no enabled pile.
  Either ArgoniaCore's replace path (RemovePileRef, then the drop: Disable+SetDelete on the old ref, which the refs
  read may still list first) or the read's ref order. Next step: read `PileState` and all refs listed, not refs.0.
- **ui-sweep favourites:** the harness was at fault. Q opens nothing with an empty favourites list (game-17), and
  the os-key favouriting never took. A new DEV call `dev-favorite <form>` (ep_dev.cpp, InventoryChanges::SetFavorite)
  marks the item natively. It failed with `no form ARG_Weap_SteelSword`: find_any's LookupByEditorID misses weapons
  at run time. Next step: pass the form id (the steel sword's id from `refs`/vocab) or resolve via ArgoniaCore's map.
- **menus-quit:** the vanilla Journal's Quit confirmation calls `GameDelegate.call("QuitToMainMenu")`
  (quest_journal.swf in the Interface BSA). SKSE 2.3.1 has no Game.QuitToMainMenu native (strings: absent).
  dev-quit-to-menu now opens the Journal and calls that callback on the Journal's FxDelegate, the engine's own
  handler. In g22-b1 the quit save line did not come (1 new log line). The bridge reply came, so either the menu
  never opened in time (the 600-frame wait logs `did not open`) or the callback ran and ArgoniaCore's quit watch did
  not see resetGame on the close. Next step: grep the bridge log for `dev-quit-to-menu:`, then watch for MainMenu.
  The callback route is unproven, not disproven.

## Not done
- The Claywater LOD still, the argonia-theme verify mismatches, and London's six unarchived MO2 folders
  (argonia-edge, combat-overlay, combat-state, pandora-adopted, pandora-out, ut), with a live
  `machine_inventory.sh` run. These are owed to the next lane.
