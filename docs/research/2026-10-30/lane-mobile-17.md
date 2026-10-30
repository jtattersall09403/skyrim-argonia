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
Results: pending.
