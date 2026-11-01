# tools/argonia_world/vanilla: how Skyrim.esm does it (decision 0034)

Read-only measurement of vanilla Tamriel, so that a world rule of ours copies Bethesda's measured answer.
Nothing it reads or caches enters git (decision 0003): the cache is `~/.cache/argonia-vanilla/`.

- `load.py`: parses Skyrim.esm (and Update.esm's cell overrides) once: every Tamriel cell's heights (33x33,
  rows south to north), VCLR, BTXT/ATXT/VTXT, XCLW and regions; every REFR (cell from its position, base,
  position, rotation, scale, teleport flag); base forms with EDID and OBND; LTEX, TXST, WTHR, REGN, GRAS raw.
  `python -m tools.argonia_world.vanilla.load` rebuilds the cache (about 15 s). `ground(t, x, y)` is bilinear.
- `measure.py`: one function per 1.15 audit question, each printing JSON:
  `python -m tools.argonia_world.vanilla.measure q1 [q2 ...]` (or `all`; q4 and q6 take about a minute).
  q1 shore profiles, q2 lake footprints and dry holes, q3 slopes and cliff dressing, q4 materials and VCLR,
  q5 rock seating, q6 tree and flora density, q7 weathers and region lists, q8 placed mist, q9 the border and far
  ground, q10 dungeon entrances.

The record of results: `docs/research/2026-11-01/skyrim-does-it-this-way.md`. Run with the project venv
(`~/.argonia/venv/bin/python`; numpy). The game root is `$ARGONIA_GAME_ROOT` or `~/games/skyrimse`.
