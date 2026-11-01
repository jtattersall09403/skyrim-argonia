<!-- imported unchanged from elder-souls-argonia docs/research/lore-facts-audit/README.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# The loading-fact audit

Every one of the 170 loading-screen facts (`world/sources/lore/loading-facts.json`)
read for what it implies in play, checked against what was built or
planned on 2026-10-23, and rated for value, effort and timing. The
owner's rulings on it are [0157](../../old-decisions/0157-the-marsh-does-what-the-lore-says.md);
where a rule landed is that record's last table.

| File | Topics |
|---|---|
| [group1.md](group1.md) | geography, cities |
| [group2.md](group2.md) | the Hist, history |
| [group3.md](group3.md) | creatures, flora |
| [group4.md](group4.md) | customs, foreign powers |
| [group5.md](group5.md) | religion, peoples |

Corrections to the group files, checked against the tree:

- Creatures already cast: `creatureCasters` in
  `packages/game-core/src/actors/data/hostile-loadouts.json` (the wisp's
  Absorb Health, 2.9x). What was missing is area effects, now 2.9c's
  hazard volumes.
- The marsh-born and lukiul choice at character creation (group 2's
  `marshBorn` field) is replaced by 0157's rule: every player is an
  outsider and earns Hist hearing by steps.
- Floods are out (0157), whatever a row rates them.
