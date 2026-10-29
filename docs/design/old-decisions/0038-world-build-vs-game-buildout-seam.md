<!-- imported unchanged from elder-souls-argonia docs/decisions/0038-world-build-vs-game-buildout-seam.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0038 — The package rule, and how game systems were seamed from the world build

**Status** the seam policy is superseded by
[0134](0134-four-parts-de-risk-first.md): the build-out register is archived
and game systems belong to Part 2; the package rule below stands as a
[CLAUDE.md](../../CLAUDE.md) rule.

## The package rule

Everything the shipped game needs is written package-shaped from the start,
rendering included. Apps hold only scene composition, app-only tooling and
debug UI. No new cross-system module-level singletons or `__STUDIO_*`
globals. Existing app-private runtime code is recorded debt, paid down when
touched substantially, never grown.

## What the seam settled that still holds

- The world build shipped contracts, thin slices and calibration data for
  game systems (capability profiles, the thin stat hook, semantic authoring,
  the quest condition vocabulary); full systems are Part 2's.
- The stats, items and loot boundary needs no separate decision: `gear.json`
  is the single source ([module 76](../world/76-stats-progression.md) §129)
  and the semantic compiler covers loot and traps.
- Training is priced as Morrowind prices it, 10 × the current skill level per
  rank ([0033](0033-workstream-s-design-and-numbers.md) call 14).
- Evidence: the
  [build-out systems audit](../research/combat-and-systems/game-buildout-systems-audit.md)
  and the archived
  [register](../research/archive/plan-2026-10-pre-derisk/buildout-register.md).
