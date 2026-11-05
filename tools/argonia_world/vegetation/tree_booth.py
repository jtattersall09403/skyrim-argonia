"""The tree-seat journey (lane 1.15-r4-trees; owner play test 3, findings 4 and 32): six placed trees of different
forms, the ones their mod sinks deepest first (the erut, palm and jungle trees whose roots hung in the air), a
first-person still each aimed at the trunk base from 6-10 m with nothing over 1 m within 3 m of the eye line (the stand
rule, BAND_M); then one still per region class from a clearing's edge in the class's fullest cell (no plant over 1 m
within 4 m of the eye), level into the most trunks, for the variety between classes. Generated from the placer's shards like the rock booth (booth.py).

    python3 -m tools.argonia_world.vegetation tree-booth --out <shards>

Reader checklist per tree still: the trunk base meets the ground (no gap under it, roots into the ground, not
standing on root tips); natural bark and leaf colour (no neon blue-green, no washed-out pale). Per class still: name
the trees and plants seen; the six classes' stills should not read as one forest.
"""
from __future__ import annotations

import functools
import math
from pathlib import Path

import tools.journeys as J
from tools.argonia_world import skyrim_units as su
from tools.argonia_world.vegetation import booth, build, lists

ROOT = Path(__file__).resolve().parents[3]
# The stand rule (lane 1.15-r6-tree-look: round 6's stands were 2.4-4.4 m off the trunk, inside the root flare and the
# crown, so the bark filled the lens as a smeared slab and the base was never in frame): a tree stop stands BAND_M off
# the trunk, aimed at its base (the base in the frame's middle), with nothing taller than TALL_M within AIM_OFF_M of the
# eye line; a class stop stands where no plant over TALL_M comes within CURTAIN_M of the eye (no leaf curtain on the
# lens) and looks level into the most trunks CONE_M out. The eye is the engine's (SEAT_U + EYE_HEIGHT_UNITS, 1.6 m).
BAND_M = (6.0, 10.0)
AIM_OFF_M, TALL_M, CURTAIN_M = 3.0, 1.0, 4.0
CONE_M, CONE_DEG = (8.0, 30.0), 30.0
BEARING_STEP = 15
TRIES = 8  # trees of one form tried for a clear stand before the next form
CLASSES = ("coastal-lagoon", "tidal-delta", "flooded-forest", "interior-swamp", "rootland", "northern-transition")


def pick(out: Path, w) -> tuple[list[dict], list[dict]]:
    meta = {r["form_key"]: r for r in w.query(
        "SELECT f.form_key, f.edid, f.role_id, f.mod, f.model, v.seat_units FROM vegetation_form v JOIN object_form f USING (form_key)")}
    eco = {r["id"]: r["eco_class_id"] for r in w.query("SELECT id, eco_class_id FROM land_region")}
    trees, per_class = [], {}
    for c in build.read_cells(out):
        for r in c["refs"]:
            m = meta.get(c["bases"][r[1]])
            if not m or m["role_id"] not in lists.SEATED_ROLES:
                continue
            d = {"form_key": m["form_key"], "edid": m["edid"], "fid": r[0], "cell": (c["x"], c["y"]), "x": r[2],
                 "y": r[3], "z": r[4], "scale": r[8], "seat": m["seat_units"], "eco": eco.get(c["region"]),
                 "mod": m["mod"], "model": m["model"]}
            trees.append(d)
            if d["eco"] in CLASSES and len(c["refs"]) > per_class.get(d["eco"], {}).get("n", -1):
                per_class[d["eco"]] = {**d, "n": len(c["refs"])}  # the class's fullest cell
    trees.sort(key=lambda d: (-d["seat"] * d["scale"], d["fid"]))
    forms = []
    for d in trees:
        if d["form_key"] not in forms and len(forms) < 6:
            forms.append(d["form_key"])
    return [d for d in trees if d["form_key"] in forms], [per_class[e] for e in CLASSES if e in per_class]


def _parts(f: tuple, trunked: bool) -> list[tuple]:
    """A plant as one cylinder (a shrub, a fern) or a trunk under a crown, as the journeys' blockers measure it:
    [(radius, z low, z high)] units."""
    fx, fy, fz, fr, fh = f[:5]
    if not trunked:
        return [(fr, fz, fz + fh)]
    return [(min(fr, J.TRUNK_U), fz, fz + J.CROWN_FROM * fh), (fr, fz + J.CROWN_FROM * fh, fz + fh)]


def _tall(b, f) -> bool:
    return f[2] + (f[6] if len(f) > 6 else 0.0) + f[4] - b.ground_u(f[0], f[1]) > TALL_M * su.UNITS_PER_METRE


def aim_hits(b, eye: tuple, subj: tuple, skip_u: float = 100.0) -> int:
    """The plants over TALL_M whose body comes within AIM_OFF_M of the eye -> subject segment at a height between the
    ground and the line (+ 1 m), the subject's own (within skip_u of it) excepted."""
    u = su.UNITS_PER_METRE
    ex, ey, ez = eye
    sx, sy, sz = subj
    dx, dy = sx - ex, sy - ey
    L2 = max(dx * dx + dy * dy, 1.0)
    n = 0
    for f in b.foliage_near((ex + sx) / 2, (ey + sy) / 2, math.sqrt(L2) / 2 + AIM_OFF_M * u):
        if math.hypot(f[0] - sx, f[1] - sy) <= skip_u or not _tall(b, f):
            continue
        t = min(max(((f[0] - ex) * dx + (f[1] - ey) * dy) / L2, 0.0), 1.0)
        d = math.hypot(ex + t * dx - f[0], ey + t * dy - f[1])
        zl = ez + t * (sz - ez)
        if any(d - r < AIM_OFF_M * u and lo <= zl + u for r, lo, hi in _parts(f, not f[5])):
            n += 1
    return n


def curtain(b, eye: tuple) -> int:
    """The plants over TALL_M with a part within CURTAIN_M of the eye (horizontally) spanning the eye's height."""
    u = su.UNITS_PER_METRE
    ex, ey, ez = eye
    n = 0
    for f in b.foliage_near(ex, ey, CURTAIN_M * u):
        if not _tall(b, f):
            continue
        d = math.hypot(f[0] - ex, f[1] - ey)
        if any(d - r < CURTAIN_M * u and lo - u <= ez <= hi + u for r, lo, hi in _parts(f, not f[5])):
            n += 1
    return n


BASE_SLICE_U = 150.0  # the mesh's body from its seat (the ground) to 2 m up


@functools.lru_cache(maxsize=None)
def base_radius_u(mod: str, model: str, seat_u: float) -> float:
    """The trunk's footprint at the ground: the 90th-percentile horizontal reach of the mesh's vertices between its
    seat and BASE_SLICE_U above it (mesh units; round 6: PalmokeTree02Single 744, ErutTree01Tall 350, HistTreeTrunk01
    1210, so stands 2.4-4.4 m off the pivot stood inside the roots). The trunk radius when the mesh cannot be read."""
    import numpy as np
    from tools.argonia_world.meshes import nif, patch
    try:
        n = nif.Nif(patch.find([patch.MODS], {"mod": mod, "mesh": "meshes/" + model.replace("\\", "/").lower()}))
    except (FileNotFoundError, OSError, ValueError):
        return J.TRUNK_U
    ps = [s.positions() for s in n.shapes() if s.nv]
    if not ps:
        return J.TRUNK_U
    p = np.concatenate(ps)
    m = (p[:, 2] >= seat_u) & (p[:, 2] <= seat_u + BASE_SLICE_U)
    return float(np.percentile(np.hypot(p[m, 0], p[m, 1]), 90)) if m.any() else J.TRUNK_U


def tree_stand(b, d: dict) -> dict:
    """The stand BAND_M off the tree aimed at its base: dry footing, the fewest aim-line hits then the fewest at the eye,
    the band's middle and the south first (Skyrim's 0 = north: the still looks north, the sun behind)."""
    u = su.UNITS_PER_METRE
    base = (d["x"], d["y"], d["z"] + d["seat"] * d["scale"])
    off_m = base_radius_u(d.get("mod") or "", d.get("model") or "", d["seat"]) * d["scale"] / u if d.get("model") else 0.0
    mid = sum(BAND_M) / 2
    dists = sorted({float(k) for k in range(int(BAND_M[0]), int(BAND_M[1]) + 1)}, key=lambda k: (abs(k - mid), k))
    best = None
    brgs = [180] + [(180 + sg * k) % 360 for k in range(BEARING_STEP, 181, BEARING_STEP) for sg in (1, -1)][:-1]
    for brg in brgs:
        for dm in dists:
            x = base[0] + math.sin(math.radians(brg)) * (off_m + dm) * u
            y = base[1] + math.cos(math.radians(brg)) * (off_m + dm) * u
            if b.soaked(x, y):
                continue
            eye = J.eye_of(b, x, y)
            key = (aim_hits(b, eye, base, skip_u=max(100.0, off_m * u)), curtain(b, eye))
            if best is None or key < best["key"]:
                h, p = J.aim(eye, base)
                best = {"x": x, "y": y, "z": b.ground_u(x, y) + J.SEAT_U, "h": h, "p": p, "key": key, "d_m": dm,
                        "subj": base, "base_m": off_m}
            if key == (0, 0):
                return best
    return best


def into_stand(b, x: float, y: float) -> tuple[int, float]:
    """(trunks, heading): the bearing (of 8) that holds the most trunks CONE_M out within +-CONE_DEG."""
    u = su.UNITS_PER_METRE
    fs = [f for f in b.foliage_near(x, y, CONE_M[1] * u) if not f[5]]
    best = (-1, 0.0)
    for h in range(0, 360, 45):
        n = 0
        for f in fs:
            dd = math.hypot(f[0] - x, f[1] - y) / u
            a = (math.degrees(math.atan2(f[0] - x, f[1] - y)) - h + 180) % 360 - 180
            n += CONE_M[0] <= dd <= CONE_M[1] and abs(a) <= CONE_DEG
        best = max(best, (n, float(h)), key=lambda t: t[0])
    return best


def class_stand(b, d: dict, step_m: float = 8.0) -> dict:
    """In the class's fullest cell: a dry stand with no leaf curtain within CURTAIN_M of the eye (a clearing's edge),
    looking level at the most trunks; the curtain count, then the trunks, rank."""
    u = su.UNITS_PER_METRE
    ox, oy = su.cell_origin(*d["cell"])
    n = int(su.CELL_UNITS / (step_m * u))
    best = None
    for i in range(n + 1):
        for j in range(n + 1):
            x, y = ox + i * step_m * u, oy + j * step_m * u
            if b.soaked(x, y):
                continue
            c = curtain(b, J.eye_of(b, x, y))
            if best is not None and c > best["curtain"]:
                continue
            trunks, h = into_stand(b, x, y)
            key = (c, -trunks)
            if best is None or key < (best["curtain"], -best["trunks"]):
                best = {"x": x, "y": y, "z": b.ground_u(x, y) + J.SEAT_U, "h": h, "p": 0.0, "curtain": c,
                        "trunks": trunks}
    return best


def _steps(name: str, note: str, d: dict, s: dict, wx: str) -> list[str]:
    cx, cy = su.cell_of(s["x"], s["y"])
    subj = [f"  # subject: {s['subj'][0]:.0f} {s['subj'][1]:.0f} {s['subj'][2]:.0f}"] if "subj" in s else []
    return [f"- name: {name}", f"  # {note}", *subj, "  do:", "  - console:", f"      line: cow {booth.WORLD} {cx} {cy}",
            "      settle: 60", "  - wait: 8", "  - console:",
            "      line: set gamehour to 12", "  - console:", f"      line: player.setpos x {s['x']:.0f}", "  - console:",
            f"      line: player.setpos y {s['y']:.0f}", "  - console:", f"      line: player.setpos z {s['z']:.0f}",
            "  - console:", f"      line: player.setangle z {s['h']:.0f}", "  - console:",
            f"      line: player.setangle x {s['p']:.0f}", "  - console:", "      line: player.setangle y 0", "  - wait: 6",
            "  - console:", f"      line: fw {wx}"]   # AFTER the teleport and its settle (the region weather replaces an earlier force)


def journey(six: list[dict], classes: list[dict], weather: dict) -> str:
    lines = [ln if ln else "#" for ln in ("# " + __doc__.replace("\n", "\n# ")).splitlines()]
    lines += ["id: tree-seat", "runner: 1", "crash_risk: low", "scene: rock-booth", "camera: first", "steps:"]
    for n, d in enumerate(six, 1):
        s = d["stand"]
        lines += _steps(f"tree-{n}-{d['edid'].lower()}", f"{d['form_key']} ref {d['fid']:06X}, seat {d['seat']:.0f} u x "
                        f"scale {d['scale']:.2f}; aim at the trunk base {s['d_m']:.0f} m off its {s['base_m']:.1f} m footprint, {s['key'][0]} on the aim "
                        f"line, {s['key'][1]} at the eye", d, s, weather[d["cell"]])
    for d in classes:
        s = d["stand"]
        lines += _steps(f"class-{d['eco']}", f"the class's fullest cell ({d['n']} refs), level view into {s['trunks']} "
                        f"trunks, {s['curtain']} plants within {CURTAIN_M:.0f} m of the eye", d, s, weather[d["cell"]])
    return "\n".join(lines) + "\n"


def stood(b, six_pool: list[dict], classes: list[dict]) -> tuple[list[dict], list[dict]]:
    """Each form's first tree (of TRIES) with a fully clear stand, else its best; each class's stand."""
    by: dict[str, list] = {}
    for d in six_pool:
        by.setdefault(d["form_key"], []).append(d)
    six = []
    for fk, ds in by.items():
        best = None
        for d in ds[:TRIES]:
            s = tree_stand(b, d)
            if s and (best is None or s["key"] < best[1]["key"]):
                best = (d, s)
            if best and best[1]["key"] == (0, 0):
                break
        if best:
            six.append({**best[0], "stand": best[1]})
    return six, [{**d, "stand": class_stand(b, d)} for d in classes]


def write(out: Path, w, b=None) -> tuple[list[dict], list[dict]]:
    pool, classes = pick(out, w)
    six, classes = stood(b or J.Build(), pool, classes)
    wx = booth.region_weather(w, {d["cell"] for d in six + classes})
    (ROOT / "tests" / "journeys" / "tree-seat.yaml").write_text(journey(six, classes, wx))
    return six, classes
