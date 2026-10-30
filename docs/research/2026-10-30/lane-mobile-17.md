# Lane mobile-17 (2026-10-30): owner issue #17, mobile gamepad, touch and phone viewports

## Phase 1: the mapping against the owner's ruling (2026-10-29, DS1 Remastered on Switch, by position)
Sources: infra/gpu-box/controlmap.py (gameplay gamepad column, laid loose by stack.ps1:134), combat_test_stage.py:172-197
(TK Dodge `bUseSprintKey`, OCPA `iKeycode=281`, Elden Parry window), stream client virtual_pad.ts (W3C standard pad;
non-standard real pads such as the GameSir X2s passed through in raw order) and touch_model.ts (every Xbox control on
screen, Xbox glyphs, standard indices).

| Ruling | Stack | Verdict |
|---|---|---|
| roll on the right button | B = Sprint; TK Dodge on the sprint key (tap rolls, hold runs) | match |
| R1 light | RB = Right Attack | match |
| R2 heavy | RT = Right Attack + One Click Power Attack key 281 (RT) | match |
| L1 block | LB = Left Attack/Block | match |
| L2 parry, L1+R1 accepted while the mod needs it | LT = Left Attack/Block (blocks); parry = L1/L2 held + R1 (bash, Elden Parry) | accepted by the ruling; L2 alone does not parry (no dedicated parry key in Elden Parry) |
| menu, journal, wait on spare buttons | Start = Tween Menu, Back = Journal, D-down = Wait, D-up = Favourites | match |
| interact / lock-on / sneak / jump | A = Activate, R3 = TDM lock-on (273), L3 = Sneak, Y = Jump, X = Ready Weapon | DS1 positions where DS1 has the action; spares otherwise |
| stream client | standard indices 0-16 straight to Moonlight; touch overlay uses the same indices | match |

No mismatch to fix at source, so no redeploy.

## Phase 2: test plan (queued as job `mobile17`, behind game-15's slot to 20:41 UTC)
Runner: scratchpad m17/run.py (Runner.apply_scene claywater on argoniabase, a 0.5 s `player` poll, bridge `events`
since the start), driving the real stream client with infra/stream-client/e2e/drive.sh:
1. `steps/mobile17-pad.json`, v5-unfolded, ARGONIA_FAKEPAD (a GameSir-like non-standard pad): LY, RX, X draw, RB, RT,
   LB, LT, LB+RB parry, B roll while moving, Y, L3 x2, R3 x2, D-left/right, Start, Back, D-down, D-up (each closed
   with B), then LY again (input after menus). Read: position/angle poll, anim and menu events, stills.
2. `steps/mobile17-touch.json`, v5-folded, touch only, after a fresh save load: X, RB, RT, B, Start, Back, D-down
   taps on the overlay. Read the same way; stills of HUD, Tween, Journal and Wait at folded size for a `reader`.
Run as job mobile17b (19:28-19:31 UTC, on the deploy live then; runner fixed after mobile17 failed on a `health` call the bridge lacks). Stream-client input goes through Sunshine as real pad/touch, so diag3-g15's os-route E/Tab/Esc loss does not apply.

## Results (bridge events and a 0.5 s position poll; stills judged by a `reader`)
Pad, unfolded 784x724, GameSir-like unmapped pad (220 events):
- PASS: LY moves (y +553 units); X draws (weaponDraw); RB attacks (attackStop x11); RT power attack (PowerAttack_Start_end x2);
  LB and LT block (blockStartOut x3 incl. the chord); LB+RB bash/parry (NPCHumanCombatShieldBash, bashStop);
  B while moving rolls (TKDR_DodgeStart x2), held B runs; Y jumps (JumpUp..JumpLandEnd); L3 sneaks (tailSneakIdle);
  Start opens/closes TweenMenu; Back opens our HTML journal (PrismaUI_FocusMenu) and B closes it in 2.6 s;
  D-down opens/closes Sleep/Wait Menu; LY after all menus moves again (input survives menus).
- FAIL: D-up opened no FavoritesMenu (no event; still shows the HUD).
- UNPROVEN: RX camera (the poll read no angle), R3 TDM lock-on (no event or visible change; no target in view), D-left/right hotkeys (nothing assigned).
Touch, folded 970x432, after a fresh save load (58 events):
- PASS: overlay shown and the virtual pad the only pad; X draws, RB attacks, B rolls, Start opens/closes TweenMenu, Back opens the HTML journal.
- FAIL: the touch B tap did not close the HTML journal (focus held 8 s, closed only by later taps), so D-down then gave no wait menu; RT tap gave no power attack.
Views (reader): tween, wait and HTML journal readable at both sizes, nothing clipped. Unfolded shows the 16:9 picture with ~40% black bands. Folded: the LB pill covers the left end of the health/stamina bars, A sits over the currency counter and buttons overlap the journal's top edge, A next to Close. A "Controller Disconnected" toast appears at start (the fake pad joining 3 s after load; expected in the harness).

## Open (P2 rolling)
1. D-up Favourites does not open (check the controlmap row and whether favourites needs a favourited item).
2. Touch taps (50 ms) do not close the PrismaUI journal or fire OCPA's RT power attack, though a 150 ms pad press does: likely the tap is too short for those readers; test a longer MIN_HOLD_MS.
3. Folded touch layout overlaps the HUD bars and counter.
4. R3 lock-on and the right stick need a reading with a target and an angle field.

## Lane touch-fix (2026-10-30): the #17 findings fixed at source
Changes (infra/stream-client, commit 75fae90): touch buttons are held at least 150 ms (`MIN_HOLD_MS`, was 50: the
measured pad press that worked); the folded phone in landscape puts every button in a band at each side
(`bandLayout`, `bandWidth` = 3.8 button units) and the client streams only the picture between the bands
(`pictureCss`), so nothing covers the HUD; e2e `hold` step; steps `touchfix-pad.json`, `touchfix-touch.json`.
Run touchfix (19:57-20:01 UTC, scratchpad m17/run2.py; bridge events and a 0.5 s player/tdm-target poll):
- PASS touch B: a tap closed the HTML journal (PrismaUI_FocusMenu closed 3.4 s after opening, at the tap). The same
  B press also rolled once the journal had closed (TKDR_DodgeStart 0.2 s later): polish, P2.
- PASS touch RT: a tap and a 700 ms hold each gave PowerAttack_Start_end (2 of 2).
- PASS right stick: LY forward before and after a 1 s RX push moved the player along headings ~170 deg and ~59 deg
  (position deltas -541/+95 then +273/-459 units): the camera turned ~110 deg with RX alone.
- PASS folded layout (still drive-t-hud): health, stamina and magicka bars and the money counter are clear; every
  button sits in the side bands, Back and Start over the black strip above the picture.
- FAIL D-up Favourites, pad and touch: no FavoritesMenu event. controlmap.py maps Favorites to D-up as the ruling
  says; the keyboard check (Q) in that run was malformed.
- UNPROVEN R3 lock-on: tdm-target read locked=true with no target all run (no NPC in reach at claywater-ambush).
- Aspect, first run: still 16:9. Cause: the runner ran sunshine-prep.ps1 through `run.sh ps` (session 0), which cannot
  see the virtual display, so the game kept SkyrimPrefs 1920x1080 (read on the machine).
Run touchfix4 on argonia-play-2 (20:48-20:55 UTC; prep in the desktop session, game relaunched per shape):
- PASS aspect: unfolded 2340x2160 request gave a 2240x2068 virtual display and the game fills the 784x724 phone
  view with no bands (still drive-p-up); folded picture request 1484x1058 gave 1600x1200 (nearest 4:3).
- PASS again: touch RT tap and hold (PowerAttack_Start_end x2); touch B closed the journal (2.7 s, at the tap).
- Still open: D-up opens no FavoritesMenu by pad or touch, though controlmap maps Favorites to D-up (likely Skyrim
  needs a favourited item; the keyboard Q control check was malformed both runs). R3: TDM's lock flag toggled with
  each R3 (6 changes) with the deserter on screen, but tdm-target never named a target.
- Open: a stream started while Skyrim is already running keeps the game's old shape (sunshine-prep leaves a running
  game alone), so folding or unfolding mid-session brings bands back until the next launch.
- The clone needed `stack.ps1 on` first (the image held a bare Data: no Address Library, our DLLs disabled).
  argonia-play-2 ran 20:29-~21:00 UTC, about 0.5 h, ~$0.13; terminated, spot request cancelled, alarm deleted.
