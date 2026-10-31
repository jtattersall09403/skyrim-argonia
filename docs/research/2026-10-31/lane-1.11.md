# lane-1.11: our HUD, rebuilt from the old game's

Chunk [1.11](../../phases/1-core-loop/1.11-our-hud.md); owner play test item 5. Built at L3 on the build VM; the L4
batch is written and owed (no game machine until the move to Stockholm).

## Sources

The old repo (`$ARGONIA_PRIVATE/old-repo`) holds documents only, no source and no HUD screenshots. Its HUD is
specified in `docs/phases/2-slice/2.2-ui-system.md` (the "Bars" bullet and §b "HUD and the prompt") and
`docs/research/ui/reference/README.md` §E (the Dark Souls crops and the hybrid: long thin bars of one shape, a dark
frame, a faint tick every 50 points, Morrowind trim on the frame). The "old" column below comes from those; our
"before" is the HUD at 9c156da.

## Inventory (19 elements: 11 built, 8 not on our HUD)

| # | Old element | Old position, style, behaviour | Ours before (9c156da) | Now | Why |
|---|---|---|---|---|---|
| 1 | Health, stamina, magicka bars | top left, that order; slim, inset trough with trim, soft fill with depth, lagging ghost of what was lost; length grows with the maximum; no numbers | top left, flat primary fills, thin frame, no ghost | built: bronze-framed glass trough, lit gradient fill with an edge, spine, ticks; earthy hues | the owner's "flat, primary" |
| 2 | Damage ghost | a lagging segment of what was just lost | none | built: warm amber trail, holds 0.9 s, falls in 0.5 s; combos read as one loss | |
| 3 | Bar drain motion | "bars drain smoothly" | none | built: fill eases 0.12 s, trail falls 0.5 s | |
| 4 | Regeneration | (not specified) | none | built: a light runs along a rising bar | the brief |
| 5 | Low health | (not specified) | none | built: pulsing fill, red-clay frame, breathing rim vignette at ≤25% | the brief |
| 6 | Breath bar | below the bars only while submerged | built, named | kept, restyled | |
| 7 | Grip (climb) bar | old: climbing had no screen presence | built, named | kept, restyled | our climbing needs the stamina-like grip |
| 8 | Vastei | under the bars, a small plaque in the trim's gold line, word in small capitals and the number; a gain counts up over 1 s with one glint along the frame and the gain beside it; a loss shows at once | a parchment box bottom right | built: under the bars, lacquer plate, our lozenge mark, the count, the word; a gain shows +N rising, the frame warms, one glint | the owner's "top left, styled differently"; the count-up is not built: the push carries the new total, and a counting number would mis-state the carried sum for 1 s |
| 9 | Notices | one toast queue top centre under any banner, stacking, timed, never modal | paper strips left at 28% height | built: lacquer strips in the left column under vastei, kind rule, rising in | top centre holds the eye and the banner; the column keeps the play centre clear |
| 10 | Place discovered banner | top of screen, name and kind beneath, fades | paper box | built: no box, the name on a dark band between bronze rules, one line at every viewport | |
| 11 | Floating prompt | glyph for the device in use, verb beneath, nearest-centre choice | built | kept, restyled to lacquer | the choice is Skyrim's crosshair target |
| 12 | Sneak eye | screen centre while sneaking, four states | top centre, three words | kept, restyled | |
| 13 | Active effects | bottom right beside the minimap: symbol, draining ring, name on focus | top right, symbol, name, time | kept top right, dark medals | no minimap to sit beside; the bottom corners are touch controls on the phone |
| 14 | Minimap | bottom right | none | not built | Morrowind's minimap breaks 0137 (directions, not markers, until discovered) and our "no marker" rule; the chart is 1.13 |
| 15 | Time readout | discreet, beside the minimap | none | not built | no field in the interface; a later chunk adds it with a schema change |
| 16 | Target health bar and lock-on marker | combat | none | not built | TDM draws the lock-on reticle in the world (1.6); a target bar needs a field the interface lacks (boss bars join in 2.7, schema/hud.ts) |
| 17 | Crosshair while sneaking or drawing a bow | centre | none | not built | Skyrim's own crosshair serves (quarantine review, 0012) |
| 18 | Equipped hands | bottom left, item or spell icon, condition bar | none | not built | no field; item icons need the renderer (2.3, 2.9) |
| 19 | Quick belt | (2.3 decision 4) | none | not built | Skyrim favourites serve (1.12) |

## Design

The HUD page in `ui/DESIGN.md` ("The HUD (1.11)"): layout, plates, bars (length, frame, fill, trail, regeneration,
low health), vastei, notices, motion, and what is not on our HUD. New theme tokens in `ui/views/core/theme.css`:
`--bar-*-hi`, `--trail`, `--hud-plate`, `--hud-trim(-hi)`, `--hud-text(-soft)`; the bar hues moved to oxblood,
moss and slate.

## Build

`ui/views/hud/render.ts` (the column, the trail and fill per bar, `remember` and `isLow`), `main.ts` (the memory
between pushes and the trail's fall), `hud.css`. The interface (`ui/schema/hud.ts`) is unchanged. Fixtures:
`fight` (hud.bars after `play`: health 96→58, stamina 95→34) and `lowHealth` (health 22/120). L1 test: "the HUD's
damage trail …" in `ui/views/tests/views.test.ts`; `make ui` green.

## The loop (L3; Playwright, 1920x1080, Magic V5 folded 2376x1060 and unfolded 2352x2172)

Stills in `out/ui/l111/` (not committed): `r0` before, `r1`–`r3` rounds, `side-by-side-{calm,hit,vastei,notices}.png`
(before left, after right, 1080p), `shoot.py` the loop script. Every still: harness judge clean (text size,
offscreen, errors) and no box overlap among bars, vastei, notices, effects, eye, banner, prompt.

| Round | Stills | Reader | Changed after |
|---|---|---|---|
| 1 | 10 states x 3 | all six checks pass; weakest: trail tan like the bronze and reads as a second bar; hues still stock red/green/blue; banner wraps on the unfolded V5 | trail rust-ash with a fade; hues oxblood/moss/slate; softer edge lip; bars thicker; banner one line |
| 2 | 10 x 3 | 1-3, 5, 6 pass; trail "partly": pale, reads as ghost more than loss | trail warm amber with a lit end |
| 3 | play, fight, lowHealth, vasteiGain x 3 | all 12 pass all six checks; "a finished, modern HUD in its own style"; minor: one trail colour for both bars | none: stopped here, the remainder is polish for the L4 round |

## Owed

- L4: `tests/journeys/batches/lane-1.11.sh` (calm, a hit as a six-still strip, regeneration, low health, a vastei
  gain, on `argoniabase`), when the machines move to Stockholm.
- L6: the owner plays it.
