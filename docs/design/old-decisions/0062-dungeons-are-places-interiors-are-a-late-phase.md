<!-- imported unchanged from elder-souls-argonia docs/decisions/0062-dungeons-are-places-interiors-are-a-late-phase.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0062 — Dungeons are places; assembled interiors come late, on demand

**Status** the phase queue is superseded by
[0134](0134-four-parts-de-risk-first.md): interiors are measured in 4.1c and
assembled on demand in 4.4; the rulings on dungeons as places, interior tiers
and promises stand.

## Evidence

- Dungeon-kind catalogue records already carry a typed interior block,
  entrance type, underwater access, purpose, slots and sockets;
  `worldgen.place_obligations` projects delivery-bearing fields into typed
  obligations with an owner and a manifest check.
- Mined plugin link records tie hundreds of shell models to furnished
  interior cells, most of them vanilla, about ninety from our mod kits; none
  of our own kit pieces has a matched interior, no Argonian interior ships
  anywhere, and the xanmeer tileset has no placed example
  ([0114](0114-the-plugin-data-is-the-interior-manifest.md)).
- `dungeon-root-v1` is BM&V's cave kit on 256 and 512 unit modules; vanilla
  cave shells are not used for structure.
- Bethesda authors interiors on a 3D grid of 128-unit modules with 90° yaw;
  furniture carries NPC-use markers; room bounds, lighting templates, locks
  and ownership are plugin data. Loot is authored and fixed, never levelled
  lists ([00-core](../world/00-core.md) rule 9).

## Rulings

1. **Dungeon places are authored with every other place**: site, identity,
   prose, purpose, quest links and typed promises of what must be inside
   (room functions, loops, traversal demands, combat-space intents, anchor
   sockets, slot locations, light regime, lock class). **Every family maps
   to a realisation recipe backed by a kit that exists**; a record whose
   family has none is re-typed, never promised.
2. **Interiors come in tiers.** Tier A, a furnished cell the plugin links to
   the shell, ships verbatim with its place, behind the door transition and
   the interior load contract
   ([0103](0103-tier-a-interiors-ship-in-16k-and-every-promise-is-a-placed-socket.md)).
   Tiers B and C, assembled interiors, are built late through an
   `interior-build` skill proven on exemplars: research first, the furnishing
   mine, a chamber-graph compiler, then hand-built exemplars until the skill
   runs unattended.
3. **Three preferences are relaxed to keep assembly small**: an interior need
   not match its shell's culture piece for piece (a retextured furnished
   vanilla cell behind an Argonian door is acceptable); assembled interiors
   are kit-bashed at chamber level from mined furnished chambers; the dungeon
   share of the density budget is a lever, so a delve may be re-typed to an
   exterior place.
4. **No throwaway experiment**: the kit data already answers whether a cave
   can be assembled; the first assembled exemplar is a modular root cavern.
5. **A wreck is a catalogue place**, built with the submerged band.
6. **The owner is hands-on for every major city and the opening-scene
   places**; no skill runs unattended on them
   ([world/96](../world/96-placement-playbook.md) §3).
