# Read every place on your map tiles

You read tiles of Project Tamriel's Black Marsh map and record every place symbol on them, exactly. Completeness
and exact spelling matter more than speed: nothing on a tile may be missed.

## Inputs
- Tiles: `/home/ubuntu/skyrim-argonia/out/newworld/tiles/<tile>.png`. Each is a 12 x 12 cell crop, upscaled 2x
  (80 px per cell), framed by rulers giving every cell's true coordinate: x along the top and bottom, y (negative,
  north at the top) down both sides. Only the **core** 10 x 10 cells belong to your tile: their ruler numbers are
  coloured (x red, y blue); the grey outer ring overlaps the neighbouring tile. **Record a symbol only if its glyph's
  centre lies in a core cell** (a label may spill outside).
- The legend: `/home/ubuntu/skyrim-argonia/newworld/sources/maps/PT3-key-Hammerfell-High-Rock.png` (the icon key of
  the same map series for Hammerfell and High Rock, and the settlement tiers). Black Marsh uses the same or similar
  icons; some may be new.

## What counts as a place symbol
- Settlement glyphs (tier by shape): megalopolis = large nonagon; metropolis = ringed octagon; large city = octagon
  or heptagon; small city = hexagon; town = pentagon; village = square; outpost/fortress/important camp = triangle;
  minor location = small dot (often with a bracketed generic label like `[Farm]`). Some glyphs are concentric (a
  ring or a square inside a square): record them as you see them.
- Icons (ruins, caves, grottos, mines, camps, shipwrecks, landmarks, dreugh hives, barrows, ...): the small pictures.
- Every name label, even with no glyph you can see (record it with `glyph: "none"`).
- Ignore: the grid, the rulers, the faint cell labels like `20.80`, roads, rivers, dashed lines.

## For each symbol record
```json
{"cell": [x, y], "fx": 0.0-1.0, "fy": 0.0-1.0,
 "glyph": "settlement" | "icon" | "none",
 "shape": "nonagon|ringed-octagon|octagon|heptagon|hexagon|pentagon|square|triangle|dot|concentric-square|concentric-circle|other",
 "icon": "<the key name it matches, e.g. 'Cave', 'Grotto', 'Mine', 'Camp', 'Shipwreck', 'Landmark', 'Dreugh hive', 'Aldmer ruin', 'Other ruin', ...> or 'new: <describe it>'",
 "fill": "<glyph fill colour in words, e.g. dark green, crimson, lime, white, purple>",
 "outline": "<glyph outline colour, e.g. white, dark>",
 "square": "<colour of the shaded square behind it, or null>", "square_cells": <its width in cells, e.g. 1, 2>,
 "label": "<the label text exactly as printed, including [brackets] and capitals as shown; null if none>",
 "label_style": "bold-caps-italic|caps|regular|italic|bracketed|null",
 "sure": true | false, "note": "<anything odd: overlapping symbols, unreadable letters (mark them ?), a second glyph>"}
```
`fx` runs west to east across the cell, `fy` north to south (0.5, 0.5 is the cell's centre); estimate to 0.1.
For a settlement glyph give `shape` and leave `icon` null; for an icon give `icon` and leave `shape` null.

## Method
1. Open the tile. Scan it cell row by cell row (all ten core rows), left to right; list each symbol.
2. Zoom where needed: crop with Python (`/home/ubuntu/.argonia/venv/bin/python`, PIL) from the full-resolution map
   `/home/ubuntu/skyrim-argonia/newworld/sources/maps/PT3-map-Black_Marsh.png` (40 px per cell; the cell (x, y)
   spans px left = 1640 + 40x, top = -1920 - 40(y+1)), upscale 4x, save under your scratch folder and read it, for
   every small label, every icon you are not sure of, and every dense cluster. Spelling of names must be exact.
3. Re-scan the tile once more for anything missed (small dots, faint italic labels, icons on water).

## Output
Write one JSON file per tile to `/home/ubuntu/skyrim-argonia/out/newworld/reads/<tile>.json`:
`{"tile": "<tile>", "symbols": [ ... ], "unclear": ["<anything you could not resolve>"]}`. Write each file as soon as
its tile is done (an interruption then loses only the tile in hand); skip a tile whose file already exists.
Return at most 10 lines: the tiles done, symbol counts, and any new icon types you met.
