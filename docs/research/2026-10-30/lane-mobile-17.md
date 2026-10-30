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
