# 0034 — Before any rule of ours: ask how Bethesda solved it in Skyrim, measure it, do the same

**Date:** 2026-11-01 · **Status:** accepted (owner ruling in the 1.15 session; a golden rule beside 0032)

## Decision

1. **Every system we build is first asked three questions:** what are we trying to achieve; did Skyrim's builders
   face the same problem; how did they solve it. The answer is measured in the game's own data (Skyrim.esm and
   its sibling files, read by our own tools; the running game where data cannot show it), written down with the
   numbers, and then **we do the same thing**, in the same records, with our own content.
2. **Our own invention is the last resort**, taken only after the measurement shows Bethesda never faced the
   problem or solved it in a way the engine no longer allows, and the record says which.
3. **The measurement is reusable:** the script that measured it lives in the tree (0020), its record in
   `docs/research/`, so the next system asks the same question the same way.
4. This applies beyond the world: combat, progression, UI, quests, AI, sound. Every chunk brief's **Read first**
   names the vanilla measurement it stands on, or says that none exists yet and owes one.

## Why

- The 1.15 planning conversation first invented "sills" at every river step. The owner asked how Skyrim does it;
  measuring Skyrim.esm's 80 stepped river edges (options record §11) gave a better rule in an hour: a sloped bed
  through the edge under a rapids chain, no sill. Everything we had invented for that problem was worse than what
  was already in the data we own.
- The owner's judgement: there are more of these, in the world and in later systems; the fix is to make the
  question a habit, not a rescue.
- Decision 0026 already says "Skyrim's own systems first"; this record makes it a measured step with a script, not
  a preference.

## Consequences

- 1.15's lanes are audited at once against Skyrim.esm (shores, entrance sites, cliffs, materials and blends, rock
  seating, vegetation density, weather values, mist, worldspace borders) and corrected where they diverge.
- CLAUDE.md carries the rule as one line; the lane brief template's Prior art field names the measurement.
