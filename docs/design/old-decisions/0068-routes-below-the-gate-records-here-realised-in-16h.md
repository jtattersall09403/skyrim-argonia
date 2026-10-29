<!-- imported unchanged from elder-souls-argonia docs/decisions/0068-routes-below-the-gate-records-here-realised-in-16h.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0068 — Roads are solved on the frozen ground, graded by patches, drawn from records; one travel-service graph

**Status** accepted · **Evidence** the
[routes ledger](../research/archive/phase16-evidence/16e-ledger.md)

## Roads

1. **Major roads are solved below the freeze gate, on the frozen ground**,
   by `solve_major_routes`. Nothing above the gate runs again; the frozen
   danger and culture fields stand. The router avoids steep ground, river
   beds (a reach polygon is a wall except at a recorded crossing) and marsh
   (deep marsh costs 16× dry ground), and zigzags up long slopes on its own.
   Typed junction records fix where named roads meet. Minor routes use the
   same gradient cost and are **never graded**.
2. **Roads attract roads.** Roads are solved longest first, and a built
   road's cells cost 0.35 of the ground to the roads after it, so a shared
   corridor is one road that splits later. An owner steer on a line is a
   `pin` in `junctions.json` (one road, a measured dry gentle point, a
   `why`), never a hand-drawn line; a long bridge over dry ground is answered
   with a pin, not a structure.
3. **Grading is a patch author.** One pass finds every choke point on the
   solved majors, decides patch or structure from the measured shape, emits
   all `route-grade` patches and hands structure windows to the span author.
   A span longer than vanilla's longest whole bridge (52 m) is a routing
   failure.
4. **Two height arrays**, so grading never feeds back into routing:
   `refined-height-natural-f32.npy` (frozen base plus place patches; read by
   the water compile, router and grader) and `refined-height-f32.npy`
   (natural plus route-grade patches; read downstream). Route-grade patches
   live in their own file, applied after every place patch; where two roads
   share a corridor the first patch wins. A walkable channel bank or marsh
   edge (at most 30°) stays natural.
5. **Crossings**: a crossing's band is decided by width and depth (a ford is
   never deeper than the small-draft line); a marsh is never a ferry
   crossing: the road is carried on a boardwalk deck or kept out.
6. **Paint follows the record**: the land-cover bake paints only lines the
   ladder produced, and a test keeps road texels within 5 m of a published
   line. The lane re-liner runs once, after the water compile.

## Records, then drawing

Span records, placed pieces, ferry landings, berths and operator sockets are
data; the 3D layer draws a placed piece only where its record puts it (a
`water` anchor class for hulls). A ferry berth is where the hull floats,
found by walking from the landing into the water; that walk is the jetty
length; a landing that never floats its hull demotes the service. Ferries
and landing ties are built with each place.

## One travel-service graph

`travel-services.json` is the province's Morrowind-style service record:
ferry, boat, rootworm and canoe, with guide, cart and porter in the
vocabulary. A minimal talk-pay-arrive contract lives in `packages/`. The
rootworm network is authored at the hero Hist nodes, its quest ties in the
co-design loop.

**Canoe services** carry paid passage on minor waterways: one station run per
connected chain of published minor channels, hull `canoe`, fare 2 gold. A
chain earns a service when at least two of the places it ends at are live and
sited and none is a harbour city. Each run joins the web at an existing
station on the run or by a transfer walk of 800 m or less, suited to the
province's scale; a chain that joins nowhere within that walk gets no
service.
