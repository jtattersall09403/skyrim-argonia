"""A placed ref's position, angles and scale as a matrix, and back (docs/design/place-studio.md, "Units and axes").

Skyrim's convention, proven on real data by `python -m tools.places xform prove <bundle_id>`:
- game units, Z up, +Y north, +X east;
- the record's three angles are radians, each a clockwise turn about its axis seen from the axis' positive end
  (so a Z angle is a compass heading: 0 faces +Y, pi/2 faces +X);
- R = Rx(-x) . Ry(-y) . Rz(-z), Rk the usual right-handed (counter-clockwise) rotations: the Z turn is applied
  first, then Y, then X, each about the world's fixed axes (Gamebryo's XYZ Euler matrix);
- world = pos + scale * R . local.

`matrix` gives a 4x4 row-major list for column vectors; `decompose` inverts it. The JavaScript mirror
(`tools/places/studio/web/xform.js`) is tested against `xform_vectors.json`; nothing else does this maths.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

VECTORS = Path(__file__).with_name("xform_vectors.json")


def _rx(a: float) -> list[list[float]]:
    c, s = math.cos(a), math.sin(a)
    return [[1, 0, 0], [0, c, -s], [0, s, c]]


def _ry(a: float) -> list[list[float]]:
    c, s = math.cos(a), math.sin(a)
    return [[c, 0, s], [0, 1, 0], [-s, 0, c]]


def _rz(a: float) -> list[list[float]]:
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def _mul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def rotation(rot: list[float]) -> list[list[float]]:
    """The 3x3 rotation of a record's angles [x, y, z] (radians)."""
    rx, ry, rz = rot
    return _mul(_rx(-rx), _mul(_ry(-ry), _rz(-rz)))


def matrix(pos: list[float], rot: list[float], scale: float = 1.0) -> list[list[float]]:
    """4x4 row-major matrix taking a point in the ref's model space to world space (column vectors)."""
    r = rotation(rot)
    return [[r[i][0] * scale, r[i][1] * scale, r[i][2] * scale, pos[i]] for i in range(3)] + [[0.0, 0.0, 0.0, 1.0]]


def apply(m: list[list[float]], p: list[float]) -> list[float]:
    """A model-space point through the matrix."""
    return [m[i][0] * p[0] + m[i][1] * p[1] + m[i][2] * p[2] + m[i][3] for i in range(3)]


def decompose(m: list[list[float]]) -> tuple[list[float], list[float], float]:
    """pos, rot (radians, each in (-pi, pi]; the record stores them in [0, 2pi) and both are the same turn), scale."""
    pos = [m[0][3], m[1][3], m[2][3]]
    scale = math.sqrt(m[0][0] ** 2 + m[1][0] ** 2 + m[2][0] ** 2)
    r = [[m[i][j] / scale for j in range(3)] for i in range(3)]
    # R = Rx(a) Ry(b) Rz(c) with a=-x, b=-y, c=-z: r[0][2] = sin b
    sb = max(-1.0, min(1.0, r[0][2]))
    b = math.asin(sb)
    if abs(sb) < 1 - 1e-9:
        a = math.atan2(-r[1][2], r[2][2])
        c = math.atan2(-r[0][1], r[0][0])
    else:  # gimbal lock: put the whole turn about X
        c = 0.0
        a = math.atan2(r[2][1], r[1][1])
    return pos, [_wrap(-a), _wrap(-b), _wrap(-c)], scale


def _wrap(a: float) -> float:
    a = math.fmod(a, 2 * math.pi)
    if a <= -math.pi:
        a += 2 * math.pi
    elif a > math.pi:
        a -= 2 * math.pi
    return 0.0 if abs(a) < 1e-12 else a


def up(rot: list[float]) -> list[float]:
    """The ref's model +Z in world space."""
    r = rotation(rot)
    return [r[0][2], r[1][2], r[2][2]]


def forward(rot: list[float]) -> list[float]:
    """The ref's model +Y (its facing) in world space."""
    r = rotation(rot)
    return [r[0][1], r[1][1], r[2][1]]


# ---- the proof on real data -----------------------------------------------------------------------------------------

CONVENTION = "Rx(-x)Ry(-y)Rz(-z)"
CANDIDATES = {  # every plausible reading of the record's angles; the proof must pick the one `rotation` uses
    "Rz(-z)Ry(-y)Rx(-x)": lambda x, y, z: _mul(_rz(-z), _mul(_ry(-y), _rx(-x))),
    "Rx(-x)Ry(-y)Rz(-z)": lambda x, y, z: _mul(_rx(-x), _mul(_ry(-y), _rz(-z))),
    "Rz(z)Ry(y)Rx(x)": lambda x, y, z: _mul(_rz(z), _mul(_ry(y), _rx(x))),
    "Rx(x)Ry(y)Rz(z)": lambda x, y, z: _mul(_rx(x), _mul(_ry(y), _rz(z))),
    "Rz(-z)Rx(-x)Ry(-y)": lambda x, y, z: _mul(_rz(-z), _mul(_rx(-x), _ry(-y))),
    "Ry(-y)Rx(-x)Rz(-z)": lambda x, y, z: _mul(_ry(-y), _mul(_rx(-x), _rz(-z))),
}


def prove_slopes(b, kinds=("plant", "rock", "tree", "groundcover", "clutter", "static"), min_tilt=0.1) -> dict:
    """Ground-conformed refs (tilted plants, rocks, scatter) have their model +Z on the land's normal: score each
    candidate reading by the mean angle between the two over every tilted ref on sloped land."""
    terr = b.space("exterior").terrain
    scores = {k: [] for k in CANDIDATES}
    for r in b.space("exterior").refs:
        if r["kind"] not in kinds:
            continue
        x, y, z = r["rot"]
        if math.hypot(_wrap(x), _wrap(y)) < min_tilt:
            continue
        n = terr.normal_at(r["pos"][0], r["pos"][1]) if terr else None
        if n is None or n[2] > 0.995:
            continue
        for k, f in CANDIDATES.items():
            m = f(x, y, z)
            d = max(-1.0, min(1.0, m[0][2] * n[0] + m[1][2] * n[1] + m[2][2] * n[2]))
            scores[k].append(math.degrees(math.acos(d)))
    out = {k: {"n": len(v), "mean_deg": round(sum(v) / len(v), 2) if v else None,
               "within_5deg": round(sum(1 for d in v if d < 5) / len(v), 3) if v else None} for k, v in scores.items()}
    best = min((k for k in out if out[k]["n"]), key=lambda k: out[k]["mean_deg"], default=None)
    return {"best": best, "candidates": out}


def prove_doors(b) -> dict:
    """A door's teleport marker stands in front of the door it lands at and faces away from it: the marker's
    forward (its Z angle read as a clockwise heading) points from that door to the marker."""
    refs = {r["id"]: r for s in b.space_ids for r in b.space(s).refs}
    cw, ccw = [], []
    for r in refs.values():
        d = r.get("door")
        if not d or d.get("to_ref") not in refs:
            continue
        tgt = refs[d["to_ref"]]["pos"]
        vx, vy = d["to_pos"][0] - tgt[0], d["to_pos"][1] - tgt[1]
        if math.hypot(vx, vy) < 16:
            continue
        h = math.atan2(vx, vy)  # the clockwise-from-north heading of door -> marker
        z = d["to_rot"][2]
        cw.append(abs(math.degrees(_wrap(h - z))))
        ccw.append(abs(math.degrees(_wrap(h + z))))
    med = lambda v: round(sorted(v)[len(v) // 2], 1) if v else None  # noqa: E731
    return {"pairs": len(cw), "median_deg_clockwise": med(cw), "median_deg_counter_clockwise": med(ccw),
            "within_30deg_clockwise": round(sum(1 for a in cw if a < 30) / len(cw), 3) if cw else None}


def prove(bundle_id: str) -> dict:
    from tools.places.bundle import Bundle

    b = Bundle(bundle_id)
    slopes, doors = prove_slopes(b), prove_doors(b)
    ok = slopes["best"] == CONVENTION and (doors["pairs"] == 0 or doors["median_deg_clockwise"] < doors["median_deg_counter_clockwise"])
    return {"bundle": b.id, "convention": CONVENTION, "proven": ok, "slopes": slopes, "doors": doors}


def make_vectors() -> dict:
    """The shared test vectors: hand-checkable turns first, then mixed angles in the record's [0, 2pi) range."""
    cases = [
        ([0, 0, 0], [0, 0, 0], 1.0),
        ([100, 200, 300], [0, 0, math.pi / 2], 1.0),     # heading east: model +Y -> world +X
        ([0, 0, 0], [0, 0, math.pi], 2.0),               # heading south, doubled
        ([0, 0, 0], [math.pi / 2, 0, 0], 1.0),           # pitch: model +Y -> world -Z (nose down)
        ([0, 0, 0], [0, math.pi / 2, 0], 1.0),           # roll: model +X -> world +Z
        ([-26781.5, 89701.25, 12.5], [0.1, 0.2, 5.5], 1.3),
        ([4096, -8192, -50], [6.1, 0.35, 2.4], 0.7),
        ([10, 20, 30], [0.4, 6.0, 3.9], 1.0),
        ([-1, -2, -3], [3.0, 0.5, 1.0], 1.05),
    ]
    pts = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], [10, -20, 30]]
    out = []
    for pos, rot, sc in cases:
        m = matrix(pos, rot, sc)
        p2, r2, s2 = decompose(m)
        out.append({"pos": pos, "rot": rot, "scale": sc, "matrix": [[round(v, 9) for v in row] for row in m],
                    "points": [{"local": p, "world": [round(v, 9) for v in apply(m, p)]} for p in pts],
                    "decomposed": {"pos": [round(v, 9) for v in p2], "rot": [round(v, 9) for v in r2], "scale": round(s2, 9)}})
    return {"convention": CONVENTION, "units": "game units, Z up, +Y north; angles radians, clockwise",
            "matrix": "4x4 row-major, column vectors: world = M . [local, 1]",
            "decompose": "rot wrapped to (-pi, pi]; same turn as the record's [0, 2pi) angles", "cases": out}


def main(argv: list[str]) -> int:
    if argv[:1] == ["vectors"]:
        VECTORS.write_text(json.dumps(make_vectors(), indent=1) + "\n")
        print(f"wrote {VECTORS}")
        return 0
    if len(argv) >= 2 and argv[0] == "prove":
        res = prove(argv[1])
        print(json.dumps(res, indent=2))
        return 0 if res["proven"] else 1
    print("usage: python -m tools.places xform prove <bundle_id> | vectors", file=sys.stderr)
    return 2
