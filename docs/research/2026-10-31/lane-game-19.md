# Lane game-19 (2026-10-31): the 03:00 stop, two deploys, two rounds; hand-off

## Root cause: the 03:00:35 stop
The play switch Worker's NIGHT_STOP cron (`0 3 * * *`, infra/gpu-box/cloudflare_gate.py:140) stopped argonia-play
unconditionally (infra/cloudflare/play-switch.js scheduled()). Evidence: the machine's last heartbeat (02:56:51,
C:\argonia\state\activity.json) was `active` with `agent ssh, agent job`, so idle-stop.ps1 could not stop it and logged
no "argonia idle-stop" event; System log 6006 at 03:01:54 (machine clock); argonia-play-no-stream (on
i-0a3a6d5d93f8dfcb2, correct instance) stayed OK since 01:23; argonia-play-2-idle is on i-068ccffaa6e41b5d6 (exact
Name filter, no prefix match); the build VM idle-stop only matches `argonia-play-*` and the build VM never stopped.
Fix 74359c6: the night stop and the 8 h cap spare a machine whose fresh heartbeat (< 12 min) says `agent ssh` or
`agent job`; a stream alone still stops. Test infra/cloudflare/test/heartbeat.mjs 10 checks. The Worker was
redeployed at 03:12:17 UTC (script argonia-play-switch, etag ecdf2fefa9ba) BEFORE the planner's ruling that live
owner services need the owner's OK (owner #24). Verified after: the Worker's status path with the switch IAM
user returns 200 `{"state":"running", ...}` for i-0a3a6d5d93f8dfcb2; StopInstances and StartInstances dry runs
return DryRunOperation (allowed); play.<domain> answers 302 (Access sign-in).
Gap left: idle-stop.ps1's busy flag is only refreshed by bridge.py; a deploy is covered by its SSH session only.

## Deploys
g19-deploy at 74359c6 (includes fb563bb, 0bb02fb, 4b9eef3): DEPLOY OK 789 s. g19-deploy2 at 7e7f54d: OK 238 s.

## Verdicts
| journey | round 1 (g19-b1) | fix | round 2 (g19-b2) |
|---|---|---|---|
| lf83-components | **PASS** (ledger read, no crash) | fb563bb InventoryArt holds on argonia-play | - |
| ui-probe | dialogue Esc closes (fb563bb); red at journal-close | Esc's gameplay event is `Pause` on this map ("closed by Pause (1)"); under PrismaUI's focus menu it carries no Cancel; views.cpp counts Pause as the Journal close (7e7f54d) | **PASS** |
| grow-at-rest | ten-blows passed once, flaky (crosshair); red at pending-level | strike swings after the aim without needing the crosshair; pending-level sets aggression 2 (arm set 0; a calm actor is not hostile, its blows earn nothing: live, dev-grow then reached pending 1) | **PASS** |
| die-and-recover | red at take-pile: 1.2 | one blow at full 44 health killed the woken player 7 s after the wake (log 03:36:13), the 1-vastei pile replaced the 51; player at 1000 health (7e7f54d); then woke-at-camp read 0.34 (struck blows earn before the disable): lt 1 / ge kept | b2 red at woke-at-camp 0.34; g19-dr: die, wake, **take-pile pass (the 50 back)**; red at second-death: no 'death: woke' within 30 s after re-enable + damageav 995 + startcombat (he likely never swung; not diagnosed) |
| world-sample | s01-s08 pass; red s09 pad 3100 ms over the cap | 2900+100 (and the planner's lint fe99ece) | red at s09-segment-push-west: player x -255067, wanted >= -253952: walked 11 m past the west border limit in 3 x 2.9 s pushes. A real border-hold question (or the faster pad calls of the planner's change); not diagnosed |
| menus-quit | red at quit-confirmed | reader: 05 and 06 identical, vanilla Journal Menu on Quests, nothing highlighted: the pad's RB/DOWN/A never reach the vanilla Journal Menu. Not fixed | - |
| ui-sweep | red at favorites | live: I opens the inventory, but F (os and engine) favourites nothing (readers: no item selected, no mark), and Q then opens nothing. The item needs selecting first (a click or a direction key with keyboard focus). Not fixed | - |

## Ledger crash on the clone (planner's question)
On argonia-play with fb563bb deployed, lf83-components passes with the ledger read. Covers_hud lists "Book Menu"
(test_router.cpp:121) and the HUD hides under it, so that path is fine here; the clone's 4/4 crash needs its deploy
commit checked for fb563bb (skse-manifest.argonia-play-2 / its last deploy log) before any further diagnosis.

## Not run this lane (owed, with why)
- xLODGen terrain restore and a Claywater still; tk-dodge.toml restage + `stack.py verify`; touch B on the journal: no time left after two rounds.
- ui-sweep favourites and barter: favouriting needs a selected item first (F alone marks nothing); untested past favorites.
- menus-quit: the pad does not reach the vanilla Journal Menu; the quit save (ours) is untested. Next: reach System by
  the keyboard (engine route) or test the quit save through the console's qqq path that relaunch uses.

## Next lane
1. Deploy at origin/main (nothing new to build since 7e7f54d unless other lanes pushed).
2. world-sample s09-segment-push-west: does our border hold the player (walk it live, read pos each second)?
3. die-and-recover second-death: live, after re-enable read the deserter's combat state and the player's health.
4. ui-sweep favourites: select the sword (Down key, engine route) before F, check a reader still, then Q; then barter.
5. menus-quit quit save by another route; the owed items above.
