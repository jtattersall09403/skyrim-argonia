<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.8-loops/screens.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: screens (2.8 § Loops, lane 2.8e)

Rule (world/76 §120, §126, §127; decision 0144): the character sheet, the
level-up screen, rest and wait show the progression system whole on every
device and input. Code: `packages/ui/src/screens/Stats.tsx` (the sheet, in
the pause deck's stats window), `LevelUp.tsx`, `Rest.tsx`; fixtures
`apps/ui-lab/src/fixtures.ts` `statsFixture` (compiled by
`compileCharacter`: Argonian warrior, the Atronach, Speed drained 10, one
level to take, 4210 vastei, the owned bed's rested entry) and
`apps/ui-lab/src/screens/fixtures-c.ts` `levelFixture` (the sitting takes
level 11, one more waiting, 120 000 vastei, Strength bought to the cap of 5).

Harness: `bash tooling/repo-standards/job_guard.sh 2.8e --mem 4 -- npm run
ui-lab:check -- --screen <id>` per screen; the lab shoots desktop (mouse and
keyboard), phone and fold-inner (touch and pad focus order). Shots copied to
`lanes/2.8/e-shots/`. The lab has one colour scheme (no dark scheme in
`packages/ui/src/tokens` or the lab); light and dark is one pass.

| Screen id | Bar | Result | Elapsed (last shoot) | Capture |
|---|---|---|---|---|
| character-sheet (new: the sheet alone; the deck opens other panes on phone) | bars green; reader clear | bars PASS; reader clear; phone shows levels to take, vastei and effects after scrolling (P3) | 33 s | e-shots/character-sheet__* |
| pause-deck | bars green | PASS (first pass only) | 42 s | e-shots/pause-deck__* |
| level-up | bars green; reader clear | PASS; reader clear; "Bought" header over the price column (P3) | 28 s | e-shots/level-up__* |
| rest | bars green; reader clear | PASS; reader clear | 26 s | e-shots/rest__* |
| wait | bars green; reader clear | PASS; reader clear on 4 of 9 tiles | 26 s | e-shots/wait__* |
| wait-dungeon | bars green; reader clear | PASS; reader saw phone touch only | 24 s | e-shots/wait-dungeon__* |
| sleep | bars green; reader clear | PASS; reader clear | 24 s | e-shots/sleep__* |
| death (seam) | bars green; reader clear | PASS; reader clear on 3 tiles | 25 s | e-shots/death__* |
| hud-notices (seam) | bars green; reader clear | PASS; "Your Long Blade skill rose to 49." | 41 s | e-shots/hud-notices__* |
| training (seam) | bars green; reader clear | PASS; reader clear; dear-offer dimming on phone (P3) | 24 s | e-shots/training__* |
| reader-book (seam) | bars green | PASS; reader saw phone touch only | 29 s | e-shots/reader-book__* |

Combat and hunted refusals open no window (2.8c: the line alone, a sign
window), so they have no rest screen to shoot.

## Reader checklist

Sheet: attributes; skills with experience toward the next rank (tooltip);
level; birthsign row; levels to take; vastei; the effect list naming the
race (Argonian) and birthsign (the Atronach) as headings, the rested entry
with hours left, the drained Speed as a negative; nothing cut, overlapping
or illegible on any viewport.

Level-up: the new level; levels still to take; the one-line vastei
explanation; the cap line; balance, spent and carried; the attribute rows
with value, bought and next-point price; Strength stopped at the cap
(no price, the raise button disabled); health after; Done reachable.

Rest, wait, sleep: the title per mode; the reason line on each wait
(settlement, dungeon); the hours slider; the buttons per mode (Rest until
healed only in rest); nothing cut.

## Reader verdicts

Every tile of level-up, character-sheet, rest, sleep and training shot
fresh (desktop, phone and fold-inner, 9 tiles each); two readers opened
every tile, and a second read after the fixes covered level-up, rest and
sleep (27 tiles). The lab has one colour scheme, so light and dark is one
pass.
- level-up: clear. The attributes scroll in their own panel; the cap line
  and Done sit under them inside the window. On phone `longest` (the
  stress strings) the header cell fills the list panel; the panel scrolls,
  so the rows are reachable.
- rest, sleep: clear; the where line shows on every tile.
- character-sheet: clear; on phone, levels to take, vastei and effects sit
  below the scroll (`P3` backlog row: a two-column phone sheet).
- training: clear; on phone the third offer sits below the scroll and dear
  offers do not read as dimmed beside the capped row (`P3` backlog row).
- The 2.2 "Bought" header over the price column stands (`P3` backlog row).
