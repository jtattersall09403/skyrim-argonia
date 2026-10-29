<!-- imported unchanged from elder-souls-argonia docs/decisions/0085-kit-truth-is-mined-fixtures-ship-to-the-studio-only.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0085 — Kit truth is mined from placement evidence; composites are built, never expanded; fixtures ship to the studio and only the game target refuses them; sheets are judged flat

**Status:** accepted. **Extends:**
[0065](0065-the-compile-realises-the-graphs-classification.md) and
[0066](0066-downstream-stages-read-the-signed-record-never-re-solve-it.md)
(read the record, never re-solve it) to kit pieces. The mining protocol is
the `kit-mining` skill; composites are the `composite-author` skill.

## Decisions

1. **Anchor class and designed sink are placement evidence, decided once
   in the miner.** `mine_designed_sink.py` and `mine_mounts.py` read the
   plugins that placed each piece (exterior and interior cells; parents at
   any scale, the child's offset divided by the parent's scale) and write
   `world/sources/placement/kit-designed-sink.json` and
   `kit-mounts-mined.json`.
   - `anchorClass` (`ground` / `water` / `deck` / `wall` / `hanging`) is
     read from real mesh-to-mesh contact: the plugin gives every placed
     object's exact pose and the meshes give their surfaces. Where the
     child touches something (0.03 m or less) decides the class, and
     support from below wins: contact on its underside means it stands
     there (deck on a kit piece, else ground) whatever else it touches; only
     a child with nothing under it is wall (contact behind or beside) or
     hanging (contact on its top). Other contacts of a standing thing (a
     chair's back on a wall) are recorded as `abuts`, never as an anchor.
     Bounding boxes are only the candidate filter.
   - The class per asset is the majority over its placements (n of 3 or
     more, or "thin" when fewer all agree); the parents in contact are its
     pairs with exact offsets. `deck` is seated on a containing kit parent's
     top face, else on terrain; only `wall` and `hanging` need a mined pair
     (a `band` along a face, or a `points` set).
   - Refs whose base lives in a master are mined; the last land override
     wins and cells merge across the pool; the defining file's refs vote.
     A ref with no contact in a water column is water, as is contact from
     below on submerged ground; contacts decide before the column. The sink
     excludes static-supported refs; stilt and quay fits are seated by their
     deck; dug-in fits anchor on the lowest sample (world 97 C11a).
   - Policy rows in `placement-policies.json` are the fallback when no
     evidence exists, each with a written reason. The exporter reads
     `designedSinkM` and fails closed without one.
2. **Composites are baked by the kit build (`compose.parts`); the compile
   never expands a `composite:` ref.** Expanding would ship the geometry
   twice.
3. **`originOffsetM[0..1]` are footprint-corner offsets, not a runtime
   translation.**
4. **`reseat` is an override kind** (`plot_remedies.py`,
   `apply_sitings.py`): a committed record moves to a named point without a
   re-plot and without any stage applying a meso move to it (Blackrose's
   centre on its island; the wet villages' entrances on the bank).
5. **Fixtures ship to the studio, local and deployed alike; only the game
   target refuses them.** The proving ground (`fixture: true`,
   `world/sources/sites/proving-ground.json`, blueprint
   `place.fixture.proving-ground.json`) is the one fixture, published with
   `--fixtures-ok`, every building on cells under 2° of slope so the sink
   alone seats it. It is a regression fixture and is never walked.
6. **Mount exemplars follow vanilla's own pairings.** Skyrim hangs lights
   on walls (`impwallsconcecandle01` on Imperial walls) and signs on posts
   (`signwrpost01`); it never hangs a lantern on a post.
7. **Sheets are judged flat.** Kit sheets, templates and mount pairs are
   rendered `--flat` in one Blender session per kit: straight-on
   orthographic elevations with a labelled metre scale, the ground line a
   bright cut line, mount children magenta on a 40 percent parent. A reader
   UNSURE on legibility means re-render, never judge. A "wrong" from the
   owner becomes a rule in world 97 § C and a `blueprint_integration` check,
   never a per-piece fix.

## Why

Kit truth derived from geometry and labels gave mount pairs that were all
snap co-placements and no real hangs, and classed chairs, waterfall
effects, bridges and lilies as walls; the plugins already record where
every piece stood. Reading that record once is cheaper than any rule, and
every place is built from it.

## Consequences

- Places use `kit-designed-sink.json` and `kit-mounts-mined.json` as given;
  a piece with no evidence gets a policy row with a written reason.
- Evidence and the round numbers:
  [place-decision-rounds/0085](../research/archive/place-decision-rounds/0085-as-recorded.md)
  and the [16h ledger](../research/archive/phase16-evidence/16h-ledger.md).
