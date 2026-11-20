"""A place as the look tool sees it: the committed place files with the session's ops applied (tools/places/edits.py,
the studio's own edit operations, in memory only), its bases, its ground, and every piece as a box (geom.py).
Names an agent can use for a thing: a structure (cluster id), a piece id or its tail, a door (its id or the room it
leads to), a person (id or name), a quest thing (its spot id or ref), or "x,y"."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path

import numpy as np

from tools.places import edits, xform
from tools.places.look import geom
from tools.places.seat import PLACES, ROOT, Ground, seat_all


def data_out() -> Path:
    """Where the bundles are: PLACES_OUT, else this tree's out/places, else the main tree's (a lane's worktree has none)."""
    env = os.environ.get("PLACES_OUT")
    if env:
        return Path(env)
    for r in (ROOT, *ROOT.parents):
        p = r / "out" / "places"
        if (p / "bundles").is_dir():
            return p
    return ROOT / "out" / "places"


# Each checkout (the main tree, a lane's worktree) has its own daemon, session and port: `out` is one shared
# directory across worktrees, and a daemon serves the place files of the tree that started it.
TREE = "main" if (ROOT / ".git").is_dir() else hashlib.sha1(str(ROOT).encode()).hexdigest()[:8]
LOOK_OUT = Path(os.environ.get("LOOK_OUT", ROOT / "out" / "places" / "look" / TREE))
LOOK_PORT = 8791 if TREE == "main" else 8800 + int(TREE, 16) % 180


def _jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


_STATIC: dict[str, dict] = {}


def _static(place_id: str, source_id: str, out: Path) -> dict:
    """What does not change with an edit, read once per place: bases, the ground as built, the models' extents."""
    key = f"{place_id}|{source_id}"
    if key not in _STATIC:
        bdir = out / "bundles"
        from tools.places.draft import io   # the draft's own bases: the source's, the ground's and the catalogue's
        src = io.load(f"src.{source_id}", bdir)
        grd = io.load(f"ground.{place_id}", bdir)
        bases: dict[str, dict] = {}
        for bid in (f"ground.{place_id}", f"draft.{place_id}"):
            for b in _jsonl(bdir / bid / "bases.jsonl"):
                bases[b["key"]] = b
        try:
            fp = json.loads((out / "footprints.json").read_text())
        except (OSError, ValueError):
            fp = {}
        world = [r for r in (grd.exterior.refs if grd.exterior else []) if r.get("layer") != "place"
                 and (r.get("kind") or (bases.get(r["base"]) or {}).get("kind")) not in geom.NO_SOLID]
        _STATIC[key] = {"world_refs": world,
                        "bases": bases | io.place_bases(src, grd, {"place_id": place_id, "source_id": source_id} | _place_json(place_id)),
                        "ground": Ground.load(bdir / f"ground.{place_id}"), "footprints": fp}
    return _STATIC[key]


def _place_json(place_id: str) -> dict:
    return json.loads((PLACES / place_id / "place.json").read_text())


class Scene:
    def __init__(self, place_id: str, ops: list[dict] | None = None, places: Path = PLACES):
        self.place_id = place_id
        out = data_out()
        self.files = edits.load_place(places / place_id)
        if ops:
            self.files = edits.apply(self.files, ops)
        st = _static(place_id, self.files["place"]["source_id"], out)
        self.bases, self.footprints = st["bases"], st["footprints"]
        g = st["ground"]
        self.ground = Ground({k: list(v) for k, v in g.cells.items()}, g.water_by_cell, g.default_water, g.sha)
        self.ground.apply_patches(self.files.get("land") or [])
        refs = [r for r in copy.deepcopy(self.files["spaces"]["exterior"]["refs"]) if not r.get("removed")]
        seat_all(refs, self.ground)
        self.refs = {r["id"]: r for r in refs}
        self.pieces = [p for p in (self.piece(r) for r in refs) if p]
        self.by_id = {p["id"]: p for p in self.pieces}
        # the world's own trees and rocks about the place: they hold up what hangs on them or rests on them
        if "world" not in st:
            st["world"] = [dict(p, world=True) for p in (self.piece(r) for r in st["world_refs"]) if p and p.get("resolved")]
        self.world = st["world"]

    def faults(self) -> list[dict]:
        if getattr(self, "_faults", None) is None:
            self._faults = geom.faults(self.pieces, self.ground, self.world)
        return self._faults

    def everything(self) -> list[dict]:
        """The place's pieces and the world's solid things about it."""
        return self.pieces + self.world

    def bounds_of(self, base: dict) -> tuple[list, bool]:
        """The model's own extent and whether its model resolves (a stand-in box when it does not)."""
        m = str(base.get("model") or "").lower()
        if not m:
            return base.get("bounds") or [[-32, -32, 0], [32, 32, 64]], False
        if m not in self.footprints:
            try:   # the studio's own converter: no triangles is the stand-in box
                from tools.places import assets
                info = assets.mesh_info(m, bounds=base.get("bounds"))
                self.footprints[m] = info.get("bounds") if info.get("tris") else None
            except Exception:
                self.footprints[m] = None
        b = self.footprints.get(m)
        return (b or base.get("bounds") or [[-32, -32, 0], [32, 32, 64]]), b is not None

    def piece(self, r: dict) -> dict | None:
        base = self.bases.get(r["base"])
        if base is None:
            return {"id": r["id"], "base": r["base"], "kind": r.get("kind"), "cluster": r.get("cluster"), "edid": None,
                    "model": None, "missing": True, "resolved": False, "m": xform.matrix(r["pos"], r.get("rot") or [0, 0, 0], r.get("scale", 1)),
                    "lo": [-32, -32, 0], "hi": [32, 32, 64], "door": r.get("door")}
        b, ok = self.bounds_of(base)
        return {"id": r["id"], "base": r["base"], "kind": r.get("kind") or base.get("kind"), "cluster": r.get("cluster"),
                "edid": base.get("edid"), "model": base.get("model"), "resolved": ok,
                "m": xform.matrix(r["pos"], r.get("rot") or [0, 0, 0], r.get("scale", 1)),
                "lo": list(b[0]), "hi": list(b[1]), "door": r.get("door")}

    # ---------- names ----------
    def clusters(self) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        for p in self.pieces:
            if p.get("cluster"):
                out.setdefault(p["cluster"], []).append(p)
        return out

    def resolve(self, name: str) -> dict:
        """A thing by name: {name, kind, pieces, lo, hi, point?}. Raises KeyError with the nearest names."""
        n = name.strip()
        if "+" in n:   # several things as one: a+b+c
            got, seen = [], set()
            for part in n.split("+"):
                for p in self.resolve(part)["pieces"]:
                    if p["id"] not in seen:
                        seen.add(p["id"])
                        got.append(p)
            return self._of(n, "group", got)
        if "@" in n:   # a thing's pieces whose origin lies in a plan box: b04@x1,y1,x2,y2
            what, box = n.split("@", 1)
            x1, y1, x2, y2 = (float(v) for v in box.split(","))
            inside = [p for p in self.resolve(what)["pieces"]
                      if min(x1, x2) <= p["m"][0][3] <= max(x1, x2) and min(y1, y2) <= p["m"][1][3] <= max(y1, y2)]
            if not inside:
                raise KeyError(f"no piece of {what!r} lies in {box}")
            return self._of(n, "group", inside)
        if "," in n and all(_num(v) for v in n.split(",")):
            v = [float(x) for x in n.split(",")]
            g = self.ground.height(v[0], v[1]) or 0.0
            z = v[2] if len(v) > 2 else g
            return {"name": n, "kind": "point", "pieces": [], "lo": [v[0] - 400, v[1] - 400, z], "hi": [v[0] + 400, v[1] + 400, z + 300],
                    "point": [v[0], v[1], z]}
        cl = self.clusters()
        if n in cl:
            return self._of(n, "structure", cl[n])
        if n in self.by_id:
            return self._of(n, "piece", [self.by_id[n]])
        tail = [p for p in self.pieces if p["id"].lower().endswith(n.lower()) or p["id"].split(".")[-1].lower().startswith(n.lower())]
        if len(tail) == 1:
            return self._of(tail[0]["id"], "piece", tail)
        doors = [p for p in self.pieces if p.get("kind") == "door" and (p.get("door") or {}).get("to_space", "").lower() == n.lower()]
        if doors:
            return self._of(n, "door", doors[:1])
        for who in self.files.get("people") or []:
            if n.lower() in (who.get("id", "").lower(), (who.get("name") or "").lower()):
                pos = (who.get("work") or {}).get("pos") or (who.get("pos"))
                if pos:
                    return self.resolve(",".join(str(v) for v in pos[:2])) | {"name": who.get("name") or n, "kind": "person"}
        for q in self.files.get("quests") or []:
            if n.lower() in (q.get("id", "").lower(), (q.get("ref") or "").lower()) and q.get("space", "exterior") == "exterior":
                return self.resolve(",".join(str(v) for v in q["pos"][:3])) | {"name": n, "kind": "quest thing"}
        near = sorted(list(cl)[:40]) + [p["id"].split(".")[-1][:8] for p in tail[:5]]
        raise KeyError(f"no thing named {name!r}" + (f" ({len(tail)} pieces match; give more of the id)" if tail else "")
                       + f"; structures: {' '.join(near)}")

    def _of(self, name, kind, pieces) -> dict:
        # what is built sets the frame: the trees, rocks and plants of a structure only when it has nothing else
        core = [p for p in pieces if p.get("kind") in geom.STRUCTURAL and p.get("model")] or pieces
        if len(core) > 1:   # a piece lost deep in the ground does not set the frame either
            under = {f["id"] for f in self.faults() if f["fault"] == "buried"}
            core = [p for p in core if p["id"] not in under] or core
        boxes = [geom.aabb(p) for p in core]
        lo = np.min([b[0] for b in boxes], axis=0)
        hi = np.max([b[1] for b in boxes], axis=0)
        # the outer twentieth of a big structure's pieces does not set its frame (a stray plant far off)
        if len(core) > 20:
            cs = np.array([(b[0] + b[1]) / 2 for b in boxes])
            q0, q1 = np.percentile(cs, 3, axis=0), np.percentile(cs, 97, axis=0)
            keep = [b for b, c in zip(boxes, cs) if np.all(c >= q0) and np.all(c <= q1)]
            if keep:
                lo, hi = np.min([b[0] for b in keep], axis=0), np.max([b[1] for b in keep], axis=0)
        return {"name": name, "kind": kind, "pieces": pieces, "lo": lo.tolist(), "hi": hi.tolist()}

    def ground_under(self, lo, hi) -> float:
        hs = [self.ground.height(x, y) for x in np.linspace(lo[0], hi[0], 5) for y in np.linspace(lo[1], hi[1], 5)]
        hs = [h for h in hs if h is not None]
        return min(hs) if hs else float(lo[2])


def _num(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False
