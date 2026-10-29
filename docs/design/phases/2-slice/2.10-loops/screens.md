<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.10-loops/screens.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: the 2.10 screens (2.10 § Screens, lane 2.10-g)

Rule (2.10-stealth-crime-locks.md § Screens; decision 0151; 2.2 § b): the
eye and the crosshair on the HUD grid, shown while sneaking or drawing a
bow and hidden otherwise; the lock screen wired to the session's lock
state with the probe; the pickpocket sheet with a percent per row; the
guard stop as a dialogue entry with pay, serve and resist; the Owing
ledger on the character sheet. Every screen on three viewports and every
input; no input drives anything new. OpenMW Android's screens are the
mobile reference (a short page low by the thumbs, the act at the foot).

Code: `packages/ui/src/hud/Hud.tsx` (Crosshair), `packages/ui/src/screens/Lock.tsx`,
`Pickpocket.tsx`, `Dialogue.tsx` (the guard-stop entry), `Stats.tsx`
(the ledger); the live views in `packages/scene/src/interact/crimeScreens.tsx`
and `useWalkInteract` (lock, pickpocket, guard stop on the session's
screen state); the hosts in `apps/game/src/GameWorld.tsx` and
`apps/world-studio/src/character/CharacterMode.tsx` through
`packages/scene/src/interact/walkCrime.ts`.

Harness: `bash tooling/repo-standards/job_guard.sh 2.10-g --mem 4 -- node
tooling/ui/ui_lab_check.mjs --screens <ids>` (desktop mouse and keyboard,
phone 844x390 and fold-inner 905x835 touch and the pad walk). A `reader`
child judges the shots against the HUD grid checklist and the style core
(lanes/2.10/g-reader.md).

| Screen id | Viewports | Result | Elapsed | Capture |
|---|---|---|---|---|
| hud-sneak (the eye and the crosshair, four states) | desktop, phone, fold | green (hidden eye + dot; danger eye on hud-combat; caution/detected not shot) | 123 s (7 screens, 87 shots) | tooling/.reports/ui-lab |
| hud-aim (the bow reticle while drawing) | desktop, phone, fold | green (shot as hud-combat; bar 6 asserts reticle without dot, dot after lowering) | 123 s (7 screens, 87 shots) | tooling/.reports/ui-lab |
| lockpick (a pickable lock, three picks, a probe) | desktop, phone, fold | green; d2's four phone reds gone; Probes and the key line scroll under the actions (diagnosed, below) | 123 s (7 screens, 87 shots) | tooling/.reports/ui-lab |
| lockpick-refused (key-only and sealed lines) | desktop, phone, fold | green (needs-key line, Pick disabled) | 123 s (7 screens, 87 shots) | tooling/.reports/ui-lab |
| pickpocket (the target's pockets, a percent a row) | desktop, phone, fold | green; phone row 4 and hint scroll under the actions | 123 s (7 screens, 87 shots) | tooling/.reports/ui-lab |
| dialogue-guard-stop (pay, serve, resist; short of gold) | desktop, phone, fold | green (phone opens on the stop page; was red) | 123 s (7 screens, 87 shots) | tooling/.reports/ui-lab |
| character-sheet-owing (the Owing by region) | desktop, phone, fold | green (regions bold, crimes indented) | 123 s (7 screens, 87 shots) | tooling/.reports/ui-lab |

## Reader checklist

HUD: the eye above the centre with its word, the crosshair dot at the
centre only while sneaking (the bow reticle replaces it while drawing),
nothing at the centre otherwise; nothing on the touch controls or the
hinge. Lock: the lock's name and level, the trap state, every pick and
probe with its quality and condition, the score with the chosen pick and
whether it opens, the last line, Pick and Probe reachable and not cut on
the phone. Refused: the key-only or sealed line, Pick disabled. Pickpocket:
the target's name, every row with its percent, a chosen row's Take.
Guard stop: the sum owed, the gold it costs, the hours in custody, three
choices, Pay refused in words when short. Ledger: each region with its
Owing, the open crimes, how it clears.
