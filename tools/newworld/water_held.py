"""The owner's water, held: the water each of the owner's kind edits was made on, kept as drawn.

An edit made in the atlas names a body by a point inside it. The bodies are cut again on every run of water_kinds
(by shape, by what joins what), so a point alone finds whatever body holds it that day: when a rebuild joins a bit
of channel to its river, an edit made on the bit sets the whole river. So when an edit that sets a kind is taken
in, the water of the body it was made on is stamped into `newworld/sources/water_owner_bodies.png` (16-bit, map
pixels, 0 none, k the k-th held body) and the edit records `held` (that k) and `area_m2` (the body's area then).
water_kinds cuts every held body out first, whole and with the owner's kind, and classifies the rest round it; an
edit without a kind (a flow, a speed, a name) records only `area_m2` and is found by its point as before.

    python3 -m tools.newworld.water_held record [dir]   # stamp every edit that has no `area_m2` yet from the
                                                        # classification in dir (default out/newworld), in place
    python3 -m tools.newworld.water_held check          # each edit against the current classification

`record` is run by tools/newworld/water_overrides_pull.py on the edits it takes in, against the classification the
atlas was built from.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from tools.newworld import frame as f

SRC = f.ROOT / "sources"
OVERRIDES = SRC / "water_overrides.json"
PNG = SRC / "water_owner_bodies.png"
AREA_TOL, AREA_FLOOR_M2 = 0.10, 500.0     # an edit's body may differ from its recorded area by 10% or 500 m2


def point_of(key: str, o: dict):
    """An edit's point: its `point`, else the label point its body id spells."""
    if o.get("point"):
        return int(o["point"][0]), int(o["point"][1])
    if re.fullmatch(r"wb-\d+-\d+(-\d+)?", key):
        x, y = re.findall(r"\d+", key)[:2]
        return int(x), int(y)
    return None


def body_at(raster: np.ndarray, x: int, y: int) -> int:
    """The body index at a point, looking up to 12 px round it when the point itself is on land (0 if none)."""
    H, W = raster.shape
    for rr in (0, 2, 4, 8, 12):
        win = raster[max(0, y - rr):min(H, y + rr + 1), max(0, x - rr):min(W, x + rr + 1)]
        if (win > 0).any():
            vals, cnt = np.unique(win[win > 0], return_counts=True)
            return int(vals[cnt.argmax()])
    return 0


def load(shape) -> np.ndarray:
    """The held bodies at map pixels (zeros when nothing is held)."""
    if not PNG.exists():
        return np.zeros(shape, np.int32)
    held = np.asarray(Image.open(PNG)).astype(np.int32)
    if held.shape != tuple(shape):
        raise ValueError(f"{PNG.name} is {held.shape}, the water raster {tuple(shape)}: not the same map frame")
    return held


def kinds(ov: dict) -> dict:
    """held index -> the owner's kind on it: of the kind edits made on that body, the latest."""
    out = {}
    for _key, o in sorted(ov.items(), key=lambda kv: str(kv[1].get("at", ""))):
        if o.get("held") and o.get("water_kind_id"):
            out[int(o["held"])] = o["water_kind_id"]
    return out


def record(ov: dict, held: np.ndarray, raster: np.ndarray, rows: list) -> list:
    """Stamp every edit in `ov` that has no `area_m2` yet from a classification (`raster`, `rows`): the area of the
    body its point lands on, and for a kind edit that body's water into `held` (edits on one body share its index).
    Both are changed in place. Returns the keys of edits whose point found no body."""
    by_k = {r["raster_index"]: r for r in rows}
    index_of: dict = {}                       # classification body -> held index, for bodies already held
    for key, o in ov.items():
        if o.get("held") and o.get("area_m2") is not None and (pt := point_of(key, o)):
            k = body_at(raster, *pt)
            if k and (held[raster == k] == o["held"]).all():
                index_of[k] = int(o["held"])
    lost = []
    top = max([int(held.max())] + [int(o.get("held") or 0) for o in ov.values()])
    for key, o in sorted(ov.items(), key=lambda kv: str(kv[1].get("at", ""))):
        if o.get("area_m2") is not None:
            continue
        pt = point_of(key, o)
        k = body_at(raster, *pt) if pt else 0
        if not k:
            lost.append(key)
            continue
        o["area_m2"] = by_k[k]["area_m2"]
        if not o.get("water_kind_id"):
            continue
        if k not in index_of:
            m = raster == k
            inside = np.unique(held[m])
            if len(inside) == 1 and inside[0] > 0:        # exactly a body held already: the same water
                index_of[k] = int(inside[0])
            else:
                top += 1
                held[m] = top
                index_of[k] = top
        o["held"] = index_of[k]
    return lost


def check(ov: dict, raster: np.ndarray, rows: list) -> dict:
    """Every edit against a classification: the body its point lands on, that body's area against the area recorded
    when the edit was made, and its kind against the owner's kind on that held water (the latest kind edit made on
    it; an edit overtaken by a later one on the same water is counted apart).
    {"edits", "same", "overtaken", "no_record": [...], "off": [...], "lost": [...]}."""
    by_k = {r["raster_index"]: r for r in rows}
    owners = kinds(ov)
    out = {"edits": len(ov), "same": 0, "overtaken": 0, "no_record": [], "off": [], "lost": []}
    for key, o in sorted(ov.items()):
        pt = point_of(key, o)
        k = body_at(raster, *pt) if pt else 0
        if not k:
            out["lost"].append(key)
            continue
        r = by_k[k]
        kind = r.get("water_kind_id", r.get("kind"))
        if o.get("area_m2") is None or (o.get("water_kind_id") and not o.get("held")):
            out["no_record"].append(key)
            continue
        a0, a1 = float(o["area_m2"]), float(r["area_m2"])
        want = owners.get(int(o["held"])) if o.get("held") else None
        if abs(a1 - a0) > max(AREA_TOL * a0, AREA_FLOOR_M2):
            out["off"].append({"edit": key, "body": r["id"], "area_m2": a1, "recorded_m2": a0, "kind": kind})
        elif want and kind != want:
            out["off"].append({"edit": key, "body": r["id"], "area_m2": a1, "recorded_m2": a0, "kind": kind,
                               "wanted": want})
        elif want and o["water_kind_id"] != want:
            out["overtaken"] += 1
        else:
            out["same"] += 1
    return out


def rows(rep, path: Path) -> None:
    """The verify rows from water_kinds' own check (out/newworld/water_check.json)."""
    if not path.exists():
        rep.fail("water", "water kinds against the accepted classification", "water_check.json missing: run water_kinds")
        return
    c = json.loads(path.read_text())
    off = c["kinds_off"]
    rep.row("water", f"each water kind's bodies and area inside the picture within 2% of the accepted classification "
                     f"(build {c['accepted_build']})", f"{len(off)} kinds off" + (", waterline moved" if c["waterline_moved"] else ""),
            not off or c["waterline_moved"],
            "; ".join(f"{o['kind']}: {o['bodies']} bodies {o['area_m2'] / 1e4:.1f} ha, accepted "
                      f"{o['accepted_bodies']} and {o['accepted_area_m2'] / 1e4:.1f} ha" for o in off))
    e = c["edits"]
    bad = e["off"] + e["lost"] + e["no_record"]
    rep.row("water", "every owner water edit on the water it was made on (the body at its point within 10% of the "
                     "area recorded with the edit, with the edit's kind)",
            f"{e['same']} of {e['edits']} as made, {e['overtaken']} overtaken by a later edit on the same body",
            not bad, f"off {e['off'][:3]}, no body {e['lost'][:3]}, no recorded area {e['no_record'][:3]}" if bad else "")


def read(dirpath: Path) -> tuple[np.ndarray, list]:
    raster = np.asarray(Image.open(dirpath / "water_classified.png")).astype(np.int32)
    return raster, json.loads((dirpath / "water_classified.json").read_text())


def save(ov: dict, held: np.ndarray) -> None:
    OVERRIDES.write_text(json.dumps(ov, indent=1, sort_keys=True) + "\n")
    if held.any() or PNG.exists():
        Image.fromarray(held.astype(np.uint16)).save(PNG, optimize=True)


def main(argv: list) -> int:
    cmd = argv[0] if argv else ""
    ov = json.loads(OVERRIDES.read_text()) if OVERRIDES.exists() else {}
    raster, rows = read(Path(argv[1]) if len(argv) > 1 else f.OUT)
    if cmd == "record":
        held = load(raster.shape)
        lost = record(ov, held, raster, rows)
        save(ov, held)
        print(json.dumps({"edits": len(ov), "held_bodies": len(kinds(ov)),
                          "with_area": sum(o.get("area_m2") is not None for o in ov.values()), "lost": lost}))
        return 1 if lost else 0
    if cmd == "check":
        res = check(ov, raster, rows)
        print(json.dumps(res, indent=1))
        return 1 if res["off"] or res["lost"] else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
