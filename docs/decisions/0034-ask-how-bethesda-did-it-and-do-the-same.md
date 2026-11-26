# 0034: Before any rule of ours: ask how Bethesda solved it in Skyrim, measure it, do the same

**Status:** decided 2026-11-01 (owner ruling; a golden rule beside [0032](0032-every-world-call-is-grounded-in-the-lore.md)).

## Decision

1. **Every system we build is first asked three questions:** what are we trying to achieve; did Skyrim's builders
   face the same problem; how did they solve it. The answer is measured in the game's own data (Skyrim.esm and its
   sibling files, read by our own tools; the running game where data cannot show it), written down with the
   numbers, and then **we do the same thing**, in the same records, with our own content.
2. **Our own invention is the last resort**, taken only after the measurement shows Bethesda never faced the
   problem or solved it in a way the engine no longer allows, and the record says which.
3. **The measurement is reusable:** the script that measured it lives in the tree and its record in
   `docs/research/`, so the next system asks the same question the same way.
4. This applies to the world, combat, progression, quests, AI and sound alike. A brief names the vanilla
   measurement it stands on, or says that none exists yet and owes one.

## Why

An early plan invented "sills" at every river step. The owner asked how Skyrim does it; measuring Skyrim.esm's 80
stepped river edges gave a better rule in an hour: a sloped bed through the edge under a rapids chain, no sill.
Everything we had invented for that problem was worse than what was already in the data we own. The fix is to make
the question a habit, not a rescue.

## Consequences

- CLAUDE.md carries the rule as one line.
