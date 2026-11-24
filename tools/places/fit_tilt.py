"""A tilted source piece carried under a turned fit keeps its tilt in the world (draft/wholesale.py, srcnav.py,
xform.turn_rot): the fit turns the source about the up axis, so a piece's rotation is Rz(-fit) . R(source), which for a
level piece is its Z angle plus the fit's turn and for a tilted one is not. This tool finds the committed rows the
earlier composition (the fit's turn added to the Z angle alone) left wrong, proves each on its mesh's real vertices,
and puts them right.

For each row of a wholesale place whose source ref is tilted and whose fit turns: `true` is the source's pose carried
by the fit (Rz(-fit) . R(source)); `old` the rotation the draft wrote; `new` turn_rot's. The probe is the largest
distance between the mesh's vertices placed by each and by `true`. A row whose rotation is no longer `old` was set by a
hand (the agent's or the owner's) and stays as it stands; so does a row named in place.json `draft.fit_tilt_kept`
[{id, why}]: one whose true pose breaks what a hand laid round its older one (a street, a patrol, a pair of rocks
leaning together), found by building the place with the change and running its checks.

    python -m tools.places fit_tilt [<place_id> ...]            the rows, their probes, what would change
    python -m tools.places fit_tilt <place_id> ... --apply       change them in the place files
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

from tools.places import xform
from tools.places.draft import io


def _M(rot) -> np.ndarray:
    return np.array(xform.rotation([float(v) for v in rot]))


def _same(a, b, tol=2e-4) -> bool:
    return all(abs(math.remainder(float(x) - float(y), 2 * math.pi)) <= tol for x, y in zip(a, b))


def rows_of(place_id: str, places: Path, bundles: Path, verts_of) -> list[dict]:
    files = json.loads((places / place_id / "place.json").read_text())
    fit = files.get("fit") or {}
    turn = math.radians(float(fit.get("rot_deg", 0.0)))
    if "wholesale" not in files or not math.remainder(turn, 2 * math.pi):
        return []
    src = io.load(f"src.{files['source_id']}", bundles)
    by_src = {r["id"]: r for r in src.exterior.refs}
    out = []
    rows = [json.loads(ln) for ln in (places / place_id / "spaces" / "exterior" / "refs.jsonl").read_text().splitlines() if ln.strip()]
    kept = {k["id"] for k in (files.get("draft") or {}).get("fit_tilt_kept") or []}
    for r in rows:
        s = by_src.get(r.get("src"))
        if s is None or r["id"] in kept:   # kept in its older pose: what a hand laid round it needs it there
            continue
        sr = [float(v) for v in (s.get("rot") or [0, 0, 0])]
        if abs(math.remainder(sr[0], 2 * math.pi)) < 1e-6 and abs(math.remainder(sr[1], 2 * math.pi)) < 1e-6:
            continue
        old = [sr[0], sr[1], round(sr[2] + turn, 5)]
        new = [round(v % (2 * math.pi), 5) for v in xform.turn_rot(sr, turn)]
        true = np.array(xform._rz(-turn)) @ _M(sr)
        hand = not _same(r.get("rot") or [0, 0, 0], old)
        p = verts_of(s.get("base"), (src.bases.get(s.get("base")) or {}).get("model"))
        if p is None:     # a light or a marker: no mesh, its own axes a hundred units long stand for it
            p = np.eye(3) * 100.0
        dev = lambda rot: None if p is None else round(float(np.abs(p @ (_M(rot) - true).T * float(r.get("scale", 1.0))).max()), 1)
        now = dev(r.get("rot") or [0, 0, 0])
        if now <= 0.5:       # already the source's pose carried (a level-equivalent tilt, or put right before)
            continue
        out.append({"id": r["id"], "src": s["id"], "base": s.get("base"), "hand": hand, "old": old, "new": new,
                    "dev_old": dev(old), "dev_new": dev(new), "dev_now": now})
    return out


def apply(place_id: str, places: Path, found: list[dict]) -> int:
    p = places / place_id / "spaces" / "exterior" / "refs.jsonl"
    want = {f["id"]: f["new"] for f in found if not f["hand"]}
    lines, n = [], 0
    for ln in p.read_text().splitlines():
        if ln.strip():
            r = json.loads(ln)
            if r["id"] in want:
                r["rot"] = want[r["id"]]
                ln = json.dumps(r, ensure_ascii=False, separators=(",", ":")) if '":' in ln and ', "' not in ln else json.dumps(r, ensure_ascii=False)
                n += 1
        lines.append(ln)
    p.write_text("\n".join(lines) + "\n")
    return n


def verts_loader():
    from tools.places.draft import io as dio
    from tools.newworld.place.seat import mesh_points
    cat = {}

    def verts(base, model=None):
        if base not in cat:
            model = model or (dio.catalogue_bases({base}).get(base) or {}).get("model")
            pts = mesh_points(model) if model else None
            cat[base] = None if pts is None else np.asarray(pts, float).reshape(-1, 3)
        return cat[base]
    return verts


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places fit_tilt")
    ap.add_argument("places", nargs="*")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--places-dir", type=Path, default=io.PLACES)
    a = ap.parse_args(argv)
    ids = a.places or sorted(d.name for d in a.places_dir.iterdir() if (d / "place.json").exists())
    verts = verts_loader()
    for pid in ids:
        found = rows_of(pid, a.places_dir, io.BUNDLES, verts)
        fix = [f for f in found if not f["hand"]]
        print(f"{pid}: {len(found)} tilted source rows under a turned fit, {len(fix)} to change, {len(found) - len(fix)} set by hand")
        for f in found:
            print(f"  {f['id']} ({f['base']}): {'hand, left' if f['hand'] else 'change'}; mesh off the source's pose by "
                  f"{f['dev_now']} now, {f['dev_new']} after")
        if a.apply and fix:
            print(f"  changed {apply(pid, a.places_dir, found)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
