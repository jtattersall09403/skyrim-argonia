<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9x-loops/touch.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 2.9x loop survey: touch and the dodge roll (lane u)

Owner spec: tmp/2-slice-so-far-fixes.md § Ui misc, verbatim in lanes/2.9x/owner-touch-spec.md ("spec" below).
Proof kinds: **test** = headless input or DOM test (file:test); **shot** = ui-lab still read by a reader; **pod** = needs hardware GL (the studio or game in a real fight), owed to lane t's pod re-run.

## Loop steps and elapsed time

| Step | Command | Elapsed |
|---|---|---|
| Input to roll, all devices | vitest game-core dodgeStart/input/intent | 0.2 s |
| Touch layout and drawer | vitest world-studio TouchControls.test.tsx | 1.7 s |
| One ui-lab screen (9 shots, all bars) | `npm run ui-lab:check -- --screen <id>` | 40 s |
| Sandbox evasion group (roll, backstep, dodge-followups, enemy-evasion) | `visual:check ... -- evasion` under job_guard | 48 s |
| Sandbox touch group | `visual:check ... -- touch` | ~40 s |

## Device x action matrix

| Action (spec line) | Desktop kbd+mouse | Pad | Phone touch | Fold touch |
|---|---|---|---|---|
| Move / walk-run-sprint ("walk - run - sprint depending how far you push it") | WASD: input.ts:423 | stick | test input.test.ts "sprints in the outer band" | same |
| Draw / sheathe ("draw weapon" in the drawer, "Sheathe weapon" drawn) | Tab: input.test.ts "Tab stays equip" | Y tap: input.test.ts "a tap released before the threshold is one equip" | test TouchControls.test.tsx "drawer fans sneak, draw..."; shot hud-touch-drawer, hud-touch-drawn-drawer | shot same |
| Light ("quick tap light attack") | input.test.ts "releases a short primary click" | R | test input.test.ts "main tap of 100 ms is one light" | same |
| Heavy ("as soon as time is reached, don't wait for release") | input.test.ts "triggers heavy at 0.3 seconds while primary is still held" | ZR | test input.test.ts "main hold is heavy at the threshold crossing while still held" | same |
| Block / parry, shield or two-hander or empty off hand ("hold blocks... quick tap does parry") | Mouse 2 / chord: input.test.ts "right-held then primary into parry" | L / ZL | test input.test.ts "off hand without dual wield: a tap parries", "a 400 ms hold guards" | same |
| Off-hand weapon ("acts like main hand") | input.test.ts "desktop: a guard tap ... offLight" | pad test | test input.test.ts "off hand with dual wield: tap is offLight, hold offHeavy" | same |
| Roll | Space: dodgeStart.test.ts "keyboard: a Space tap..." | B: dodgeStart.test.ts "pad" | dodgeStart.test.ts "touch: the ROLL button's pulse"; sandbox evasion PASS | same; in-world (2.9xv pod): the ROLL tap moved the body 3.4 m in 0.9 s (z 1900.13 to 1903.53), so it fires; the 8-frame strip shows a standing figure (RED, strip unusable) |
| Lock-on (planner call, spec silent) | Q | R3 | LOCK button tap: TouchControls.test.tsx "lock button"; shot hud-touch-shield | same |
| Target switch (planner call) | , . | right stick | swipe across LOCK: TouchControls.test.tsx lockGesture | same |
| Two-hand grip (planner call) | V | Y hold | drawer GRIP when drawn: TouchControls.test.tsx; shot hud-touch-drawn-drawer | same |
| Belt use ("quick belt should be tap to use") | 1-4 | d-pad | Items.test.tsx "a tap on the HUD belt uses the slot" | same |
| Belt rotate to weapon/shield/spell | 1-4 | d-pad | belt tap -> session.useBeltItem (scene/items/session.ts:291); in-world (2.9xv pod): the studio belt is empty (four slots "Empty"; `equipFightPreset`, studioFight.tsx:73, never calls `setBeltItem`), so the rotate was not exercised: OWED | OWED |
| Inventory, equip weapon then spell to a hand | I / menu | Start | Items.test.tsx "selecting shows the actions"; inventory-hands ui-lab screen; in-world: pod | pod |
| Cast each hand | Mouse 1/2 held | R / L | hand buttons hold castMain/castOff (input.ts castMain/castOff from touchHandDown); in-world (2.9xv pod): `cast=bound-dagger`, then main and off held on touch: pose changes, no spell effect or dagger visible at reader size (UNCLEAR) | UNCLEAR |
| Container tap details then take | click | A | chooseThenAct.test.tsx "the first tap chooses and shows ... Take" | same |
| Sneak | C | L3 | drawer SNEAK: TouchControls.test.tsx | same |
| More open / close (animated unfurl, refurl) | n/a | n/a | TouchControls.test.tsx "the drawer unfurls and refurls"; shots hud-touch, hud-touch-drawer-mid, hud-touch-drawer | same |

## Pod results (2.9xv, `lanes/2.9x/v-shots/touch-b/`, emulated phone 844x390)
- Draw then hands: PASS. The studio spawns drawn; SHEATHE hides ATTACK, BLOCK and LOCK; Draw brings them back.
- Hand buttons held (melee): PASS; the character turns with the sword out.
- Roll: fires (3.4 m), strip frames identical (RED; likely stale compositor frames under emulation).
- Belt rotate: OWED, belt empty in the studio.
- Spell cast each hand on touch: UNCLEAR, no visible effect at reader size.

## Pod rows for lane t's re-run
Roll in the studio walk and the game (key, pad, touch); draw then hands appear on touch in a fight with hostiles on; belt rotate; equip a spell and cast each hand on touch.
