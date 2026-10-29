<!-- imported unchanged from elder-souls-argonia docs/decisions/0130-one-collider-part-per-placement.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0130 — One collider part per placement

Status: accepted.

## Context

The collider ceiling gate counts resident collision parts x 1.55 against 500
(`export_settlement_bundle.py`, decision 0052). A `mesh` or `convex` placement
built one trimesh per LOD0 primitive, so a building cost 3-11 parts. Helstrom
laid out at 854 parts (1324 with headroom) and could not reach the ceiling from
the layout alone.

## Decision

A `mesh` or `convex` placement collides as ONE trimesh: `trimeshParts`
(`packages/game-core/src/settlement/SettlementLayer.tsx`) bakes every LOD0
primitive through its local matrix and the placement scale, concatenates the
vertices and offsets the indices, and returns a single `trimesh` shape. The
exporter's `resident_collision_parts` counts 1 for every colliding `mesh` or
`convex` placement (a bound run of such pieces stays one joined part, 0101 rule
9). A box-kind piece still builds its measured parts, else one box per
primitive. The per-primitive trimesh path is deleted.

## Consequences

- Each bundle's `lod.colliderPartBudget` is `round(worst x 1.55)` of its own
  placements (settlementCollision test), so it falls on that place's next
  publish; a bundle carries its budget from its last publish.
- The runtime builds fewer, larger trimeshes: one broadphase entry per building.
  Triangle count per building is unchanged.
