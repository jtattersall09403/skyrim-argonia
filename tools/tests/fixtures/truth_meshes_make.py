"""Writes truth_meshes.json: the golden place's tiny meshes, built from boxes and rings (no game asset), each with
the numbers shape.py must read from it. Run: python tools/tests/fixtures/truth_meshes_make.py"""
import json
import math
from pathlib import Path


def box(x0, y0, z0, x1, y1, z1):
    v = [[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    t = [(0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3), (0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5),
         (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6)]
    return v, t


def join(*parts):
    V, T = [], []
    for v, t in parts:
        o = len(V)
        V += v
        T += [[a + o, b + o, c + o] for a, b, c in t]
    return {"v": V, "t": T}


def ring_stack(rings, n=12):
    """A closed tube through rings [(cx, cy, z, r)], capped at both ends, outward faces."""
    V, T = [], []
    for cx, cy, z, r in rings:
        V += [[cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n), z] for k in range(n)]
    for i in range(len(rings) - 1):
        for k in range(n):
            a, b = i * n + k, i * n + (k + 1) % n
            T += [[a, b, b + n], [a, b + n, a + n]]
    for i, flip in ((0, True), (len(rings) - 1, False)):
        cx, cy, z, _ = rings[i]
        c = len(V)
        V.append([cx, cy, z])
        for k in range(n):
            a, b = i * n + k, i * n + (k + 1) % n
            T.append([c, b, a] if flip else [c, a, b])
    return {"v": V, "t": T}


def post(cx, cy, z0, z1, w=20):
    return box(cx - w / 2, cy - w / 2, z0, cx + w / 2, cy + w / 2, z1)


M = {}
# an L-shaped deck on three inset posts: deck top 0, posts down to -260
M["fx/ldeck.nif"] = join(box(0, 0, -20, 400, 100, 0), box(0, 100, -20, 100, 400, 0),
                         post(50, 50, -260, -20), post(350, 50, -260, -20), post(50, 350, -260, -20))
# a house body on four legs: floor 10, walls to 250, roof 250..270 overhanging by 50 (eaves 250)
M["fx/legshouse.nif"] = join(post(-90, -90, -100, 0), post(90, -90, -100, 0), post(-90, 90, -100, 0), post(90, 90, -100, 0),
                             box(-100, -100, 0, 100, 100, 10),
                             box(-100, -100, 10, -90, 100, 250), box(90, -100, 10, 100, 100, 250),
                             box(-90, -100, 10, 90, -90, 250), box(-90, 90, 10, 90, 100, 250),
                             box(-150, -150, 250, 150, 150, 270))
# a leaning tree: root flare from radius 90 at -40 shrinking to the trunk's 20 at 0 (the collar), then a trunk
# leaning 0.2 in x per unit up to 400
M["fx/leantree.nif"] = ring_stack([(0, 0, -40, 90), (0, 0, -32, 70), (0, 0, -24, 50), (0, 0, -16, 34), (0, 0, -8, 24),
                                   (0, 0, 0, 20)] + [(0.2 * z, 0, z, 20) for z in range(40, 401, 40)])
# a cliff with an overhang: a block 0..200 in x to 600 high, and an overhang 200..350 from 400 up
M["fx/cliff.nif"] = join(box(0, 0, 0, 200, 400, 600), box(200, 0, 400, 350, 400, 600))
M["fx/egg.nif"] = join(box(-10, -10, 0, 10, 10, 20))
M["fx/root.nif"] = join(box(-200, -8, -16, 200, 8, 0))
# a stair: five treads 40 deep rising 32 each, solid under each tread to its foot
M["fx/stair.nif"] = join(*[box(40 * k, -50, 0, 40 * (k + 1), 50, 32 * (k + 1)) for k in range(5)])
# a bridge plank 400 long, deck top 10
M["fx/plank.nif"] = join(box(0, -40, 0, 400, 40, 10))
# a deck slab 200 square, top 0
M["fx/slab.nif"] = join(box(-100, -100, -20, 100, 100, 0))
# a boardwalk 600 long, top 0, and a small house body standing on it
M["fx/boardwalk.nif"] = join(box(0, -60, -20, 600, 60, 0))
M["fx/hut.nif"] = join(box(-50, -50, 0, 50, 50, 200))


def sag(x):
    """A hanging bridge's deck: 60 lower mid-span than at its ends (x 0 and 480)."""
    return -60 * (1 - ((x - 240) / 240) ** 2)


# a rope bridge 480 long: 15 planks (2 apart) on a deck sagging 60 mid-span, each plank's top at the deck's height at
# its outer edge; rope rails 50 over the deck; at each end, beyond the last plank, two posts to 60 and an end frame
# whose top (60) is a walked face standing above and beyond the deck's end
planks = []
for k in range(15):
    x0, x1 = 32 * k + 1, 32 * k + 31
    zt = sag(x0 if x0 < 240 else x1)
    planks += [box(x0, -50, zt - 6, x1, 50, zt), box(x0, -58, zt + 46, x1, -54, zt + 50), box(x0, 54, zt + 46, x1, 58, zt + 50)]
M["fx/ropebridge.nif"] = join(*planks, *[post(x, y, -100, 60, 12) for x in (-6, 486) for y in (-56, 56)],
                              box(-12, -62, 50, 0, 62, 60), box(480, -62, 50, 492, 62, 60))
# a small deck (top 0) on four posts 600 long that rise 80 over it (rail posts)
M["fx/stiltdeck.nif"] = join(box(0, 0, -10, 200, 100, 0), *[post(x, y, -600, 80, 12) for x in (16, 184) for y in (16, 84)])
# a rock: a block 400 by 300, top 0
M["fx/rock.nif"] = join(box(-100, -100, -300, 300, 200, 0))
# a hut 600 by 200 whose floor (top 8) lies on its deck and whose walls reach 16 under the floor
M["fx/hutfloor.nif"] = join(box(-300, -100, 0, 300, 100, 8), box(-300, -100, -16, -290, 100, 200), box(290, -100, -16, 300, 100, 200),
                            box(-290, -100, -16, 290, -90, 200), box(-290, 90, -16, 290, 100, 200), box(-330, -130, 200, 330, 130, 220))
# a wall 20 thick and 200 long, from 40 under to 200
M["fx/wall.nif"] = join(box(-10, -100, -40, 10, 100, 200))
# a boardwalk 600 long and 200 wide, top 0
M["fx/wideboard.nif"] = join(box(0, -100, -20, 600, 100, 0))

CASES = {
    "ldeck": {"model": "fx/ldeck.nif", "feet": 3, "feet_z": -260, "walk_cells_min": 250, "low": -260,
              "plan_cells_lt_box": True},
    "legshouse": {"model": "fx/legshouse.nif", "eaves": 250, "floor": 10, "feet": 4, "feet_z": -100},
    "leantree": {"model": "fx/leantree.nif", "collar": 0, "collar_tol": 8, "lean": 11.3, "lean_tol": 1.5, "low": -40},
    "cliff_egg": {"cliff": "fx/cliff.nif", "egg_under_overhang": [275, 200, 10], "egg_inside": [100, 200, 10],
                  "egg_beside": [420, 200, 10]},
    "stairs": {"model": "fx/stair.nif", "foot_z": 32, "head_z": 160, "midair": 40},
    "bridge": {"plank": "fx/plank.nif", "slab": "fx/slab.nif", "short": 30},
    "ropebridge": {"model": "fx/ropebridge.nif", "slab": "fx/slab.nif", "length": 480, "gap": 4},
    "legs": {"model": "fx/stiltdeck.nif", "rock": "fx/rock.nif", "legs": 600, "short": 100},
    "floor": {"hut": "fx/hutfloor.nif", "slab": "fx/slab.nif"},
    "walls": {"wall": "fx/wall.nif", "boardwalk": "fx/boardwalk.nif", "wide": "fx/wideboard.nif", "stair": "fx/stair.nif",
              "clear": 100},
}

out = Path(__file__).with_name("truth_meshes.json")
out.write_text(json.dumps({"about": __doc__.split("\n")[0], "meshes": M, "cases": CASES}, separators=(",", ":")) + "\n")
print(out, sum(len(m["t"]) for m in M.values()), "triangles")
