"""The tree-seat journey (lane 1.15-r4-trees; owner play test 3, findings 4 and 32): six placed trees of different
forms, the ones their mod sinks deepest first (the erut, palm and jungle trees whose roots hung in the air), a
first-person still each aimed at the trunk base; then one still per region class from a placed tree's spot, level at
the play camera, for the variety between classes. Generated from the placer's shards like the rock booth (booth.py).

    python3 -m tools.argonia_world.vegetation tree-booth --out <shards>

Reader checklist per tree still: the trunk base meets the ground (no gap under it, roots into the ground, not
standing on root tips); natural bark and leaf colour (no neon blue-green, no washed-out pale). Per class still: name
the trees and plants seen; the six classes' stills should not read as one forest.
"""
from __future__ import annotations

import math
from pathlib import Path

from tools.argonia_world.vegetation import booth, build, lists

ROOT = Path(__file__).resolve().parents[3]
STAND_U, EYE_U = 450.0, 120.0  # 450 units off the trunk, eye 120 up: the base and the lower trunk in frame
CLASSES = ("coastal-lagoon", "tidal-delta", "flooded-forest", "interior-swamp", "rootland", "northern-transition")


def pick(out: Path, w) -> tuple[list[dict], list[dict]]:
    meta = {r["form_key"]: r for r in w.query(
        "SELECT f.form_key, f.edid, f.role_id, v.seat_units FROM vegetation_form v JOIN object_form f USING (form_key)")}
    eco = {r["id"]: r["eco_class_id"] for r in w.query("SELECT id, eco_class_id FROM land_region")}
    trees, per_class = [], {}
    for c in build.read_cells(out):
        for r in c["refs"]:
            m = meta.get(c["bases"][r[1]])
            if not m or m["role_id"] not in lists.SEATED_ROLES:
                continue
            d = {"form_key": m["form_key"], "edid": m["edid"], "fid": r[0], "cell": (c["x"], c["y"]), "x": r[2],
                 "y": r[3], "z": r[4], "scale": r[8], "seat": m["seat_units"], "eco": eco.get(c["region"])}
            trees.append(d)
            if d["eco"] in CLASSES and len(c["refs"]) > per_class.get(d["eco"], {}).get("n", -1):
                per_class[d["eco"]] = {**d, "n": len(c["refs"])}  # the class's fullest cell
    trees.sort(key=lambda d: (-d["seat"] * d["scale"], d["fid"]))
    seen, six = set(), []
    for d in trees:
        if d["form_key"] not in seen and len(six) < 6:
            seen.add(d["form_key"])
            six.append(d)
    return six, [per_class[e] for e in CLASSES if e in per_class]


def _steps(name: str, note: str, d: dict, x: float, y: float, z: float, h: float, pitch: float, wx: str) -> list[str]:
    cx, cy = d["cell"]
    subj = [f"  # subject: {d['x']:.0f} {d['y']:.0f} {d['z'] + d['seat'] * d['scale']:.0f}"] if pitch else []
    return [f"- name: {name}", f"  # {note}", *subj, "  do:", "  - console:", f"      line: cow {booth.WORLD} {cx} {cy}",
            "      settle: 60", "  - wait: 8", "  - console:",
            "      line: set gamehour to 12", "  - console:", f"      line: player.setpos x {x:.0f}", "  - console:",
            f"      line: player.setpos y {y:.0f}", "  - console:", f"      line: player.setpos z {z:.0f}",
            "  - console:", f"      line: player.setangle z {h:.0f}", "  - console:",
            f"      line: player.setangle x {pitch:.0f}", "  - console:", "      line: player.setangle y 0", "  - wait: 6",
            "  - console:", f"      line: fw {wx}"]   # AFTER the teleport and its settle (the region weather replaces an earlier force)


def journey(six: list[dict], classes: list[dict], src, weather: dict) -> str:
    lines = [ln if ln else "#" for ln in ("# " + __doc__.replace("\n", "\n# ")).splitlines()]
    lines += ["id: tree-seat", "runner: 1", "crash_risk: low", "scene: rock-booth", "camera: first", "steps:"]
    for n, d in enumerate(six, 1):
        x, y = d["x"], d["y"] - STAND_U  # stand south of the trunk, looking north at its base
        z = booth._ground_units(src, x, y) + EYE_U
        base = d["z"] + d["seat"] * d["scale"]
        pitch = max(-60.0, min(60.0, math.degrees(math.atan2(z - base, STAND_U))))
        lines += _steps(f"tree-{n}-{d['edid'].lower()}", f"{d['form_key']} ref {d['fid']:06X}, seat {d['seat']:.0f} u x "
                        f"scale {d['scale']:.2f}; aim at the trunk base", d, x, y, z, 0.0, pitch, weather[d["cell"]])
    for d in classes:
        z = booth._ground_units(src, d["x"], d["y"] - 200.0) + EYE_U
        lines += _steps(f"class-{d['eco']}", f"the class's fullest cell ({d['n']} refs), level view north",
                        d, d["x"], d["y"] - 200.0, z, 0.0, 0.0, weather[d["cell"]])
    return "\n".join(lines) + "\n"


def write(out: Path, w) -> tuple[list[dict], list[dict]]:
    from tools.argonia_world.terrain.grid import Sources
    six, classes = pick(out, w)
    src = Sources.load(apron=False)
    wx = booth.region_weather(w, {d["cell"] for d in six + classes})
    (ROOT / "tests" / "journeys" / "tree-seat.yaml").write_text(journey(six, classes, src, wx))
    return six, classes
