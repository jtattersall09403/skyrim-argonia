# w3-interior-sun (draft, 2.W3 §a; owed L4; specified in docs/research/2026-10-29/interior-sun.md)

**Checks:** sunlight through interior windows follows the sun, through Community Shaders' interior sun (the best of
the options studied).

- **Scene:** the base save. Two interiors with different window facings: a hall with several windows and a room with
  one. Step 0 forces clear weather; the scene sets nothing about light.
- **Stills:** at game hours 06, 12, 16 and 20, set by console, from a fixed camera in each interior: 8 stills.
- **Control:** the same still with the cell's bit 15 cleared shows no lit patch, so the check can fail.
- **Pass:** the lit patch moves or vanishes between hours, the control shows none, Community Shaders' log shows the
  feature loaded, and nothing crashes in five minutes.
- **Runtime:** 1.7.104 first. If it fails there, repeat on 1.6.1170 before any change to the pin (decision 0002).
- **Fallback:** static light beams at windows, faded by time of day (owner-accepted), with the same stills.
