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


def state(place_id: str, places: Path | None = None) -> dict:
    """Which state of a place a look draws and measures: a hash of its place files as they stand in the working tree,
    the commit they sit on and whether they differ from it, and the source and ground bundles' stamps. Every look
    result carries it; a change to any of it reloads the page and the scene (daemon.py)."""
    import subprocess
    pdir = (places or PLACES) / place_id
    h = hashlib.sha256()
    for p in sorted(pdir.rglob("*")):
        if p.is_file() and "edits" not in p.relative_to(pdir).parts:
            h.update(str(p.relative_to(pdir)).encode() + b"\0" + p.read_bytes())

    def git(*a):
        return subprocess.run(["git", "-C", str(pdir), *a], capture_output=True, text=True, timeout=30)
    head = git("rev-parse", "--short=12", "HEAD")
    dirty = git("status", "--porcelain", "--", ".") if head.returncode == 0 else None
    out, bundles = data_out(), {}
    try:
        src = json.loads((pdir / "place.json").read_text()).get("source_id")
    except (OSError, ValueError):
        src = None
    for b in (f"src.{src}", f"ground.{place_id}"):
        bj = out / "bundles" / b / "bundle.json"
        try:
            bundles[b] = f"{(json.loads(bj.read_text()).get('stamp') or {}).get('key')}@{bj.stat().st_mtime_ns}"
        except (OSError, ValueError):
            bundles[b] = None
    return {"files": h.hexdigest()[:16], "commit": head.stdout.strip() if head.returncode == 0 else None,
            "working_tree": bool(dirty and dirty.stdout.strip()), "bundles": bundles}


def _jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


_STATIC: dict[str, dict] = {}


def fill_from_catalogue(bases: dict, keys, catalogue=None) -> list[str]:
    """Bases a row names that no bundle holds yet, taken from the asset catalogue: a piece of a new base placed and
    committed is known to the numbers before the daemon's own draft bundle is rebuilt (by the next page load).
    Returns the keys filled."""
    want = [k for k in keys if k and k not in bases]
    if not want:
        return []
    if catalogue is None:
        try:
            from tools.places.draft_bundle import catalogue as load
            catalogue = load()
        except Exception:  # noqa: BLE001  no catalogue on this machine: the bundles alone
            return []
    got = [k for k in want if k in catalogue]
    for k in got:
        bases[k] = catalogue[k]
    return got


def _static(place_id: str, source_id: str, out: Path) -> dict:
    """What does not change with an edit, read once per place: bases, the ground as built, the models' extents."""
    stamps = []
    for b in (f"src.{source_id}", f"ground.{place_id}"):   # a stage rerun (a new ground or source) is read again
        try:
            stamps.append((out / "bundles" / b / "bundle.json").stat().st_mtime_ns)
        except OSError:
            stamps.append(None)
    key = f"{place_id}|{source_id}|{stamps}"
    if key not in _STATIC:
        for k in [k for k in _STATIC if k.startswith(f"{place_id}|")]:
            del _STATIC[k]
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
        world = geom.world_rows(grd.exterior.refs if grd.exterior else [], bases)
        _STATIC[key] = {"world_refs": world,
                        "bases": bases | io.place_bases(src, grd, {"place_id": place_id, "source_id": source_id} | _place_json(place_id)),
                        "ground": Ground.load(bdir / f"ground.{place_id}"), "footprints": fp}
    return _STATIC[key]


def _place_json(place_id: str) -> dict:
    return json.loads((PLACES / place_id / "place.json").read_text())


_ROOM_BASES: dict[str, dict] = {}


def _room_bases(src_dir: Path) -> dict:
    """The bases of a source bundle a room is copied from (another place of our mods), read once."""
    k = str(src_dir)
    if k not in _ROOM_BASES:
        _ROOM_BASES[k] = {b["key"]: b for b in _jsonl(src_dir / "bases.jsonl")}
    return _ROOM_BASES[k]


class Scene:
    ring: dict | None = None  # a source view's footprint ring: {centre, radius_m}
    info: dict = {}           # a room's space.json (the exterior: none)
    plan_box: list | None = None   # a room's plan box: its cut, else its shell's

    def __init__(self, place_id: str, ops: list[dict] | None = None, places: Path = PLACES, space: str = "exterior",
                 state: str | None = None):
        self.place_id, self.space = place_id, space
        out = data_out()
        self.files = edits.load_place(places / place_id)
        if ops:
            self.files = edits.apply(self.files, ops, edits.bundle_source(out / "bundles"))
        # a quest state (states.jsonl): the refs it switches off are not in the scene, as the game shows it then
        from tools.places import states as quest_states
        st = quest_states.find(quest_states.load(places / place_id), state) if (places / place_id / "states.jsonl").exists() else None
        if st is not None:
            for sp in self.files["spaces"].values():
                sp["refs"] = [r for r in sp["refs"] if quest_states.enabled(r, st)]
        self.state = (st or {}).get("id")
        st = _static(place_id, self.files["place"]["source_id"], out)
        self.bases, self.footprints = st["bases"], st["footprints"]
        if space != "exterior":
            self._room(place_id, space, out)
            return
        self.ring = self.files["place"].get("look_ring")   # a source view's footprint ring (look/srcview.py)
        g = st["ground"]
        self.ground = Ground({k: list(v) for k, v in g.cells.items()}, g.water_by_cell, g.default_water, g.sha)
        self.ground.apply_patches(self.files.get("land") or [])
        refs = [r for r in copy.deepcopy(self.files["spaces"]["exterior"]["refs"]) if not r.get("removed")]
        fill_from_catalogue(self.bases, {r["base"] for r in refs})
        seat_all(refs, self.ground)
        self.refs = {r["id"]: r for r in refs}
        self.pieces = [p for p in (self.piece(r) for r in refs) if p]
        self.by_id = {p["id"]: p for p in self.pieces}
        # the world's own trees and rocks about the place: they hold up what hangs on them or rests on them
        if "world" not in st:
            st["world"] = [dict(p, world=True) for p in (self.piece(r) for r in st["world_refs"]) if p and p.get("resolved")]
        self.world = st["world"]

    def _room(self, place_id: str, sid: str, out: Path):
        """A room: its pieces as the draft bundle composes them (the source cell's copy with our rows over it, kept to
        its room and cut), its floor (the source cell's walkable mesh) as its ground, no world about it."""
        from tools.places import draft_bundle
        from tools.places.look import room
        sp = self.files["spaces"].get(sid)
        if sp is None:
            raise KeyError(f"{place_id} has no room {sid}")
        info = sp.get("space") or {}
        rows = copy.deepcopy(sp["refs"])
        src = out / "bundles" / f"src.{self.files['place']['source_id']}"
        floor = None
        if info.get("copy_of"):
            csrc = draft_bundle.copy_src(info, src)
            rows = draft_bundle.copy_space(info, rows, csrc)
            if csrc != src:
                self.bases = _room_bases(csrc) | self.bases
            floor = (csrc, info["copy_of"].split("/", 1)[1])
        refs = [r for r in rows if not r.get("removed") and r.get("pos")]
        self.info = info
        self.refs = {r["id"]: r for r in refs}
        self.pieces = [p for p in (self.piece(r) for r in refs) if p]
        self.by_id = {p["id"]: p for p in self.pieces}
        self.world = []
        boxes = [geom.aabb(p) for p in self.pieces if p.get("kind") in ("building", "static") and p.get("model")] or \
            [geom.aabb(p) for p in self.pieces] or [(np.zeros(3), np.zeros(3))]
        lo = np.min([b[0] for b in boxes], axis=0)
        hi = np.max([b[1] for b in boxes], axis=0)
        cut = info.get("cut")
        self.plan_box = [float(lo[0]), float(lo[1]), float(hi[0]), float(hi[1])]
        if cut and cut.get("box"):   # the cut, as far as the room's shell reaches
            x1, y1, x2, y2 = cut["box"]
            self.plan_box = [max(min(x1, x2), self.plan_box[0]), max(min(y1, y2), self.plan_box[1]),
                             min(max(x1, x2), self.plan_box[2]), min(max(y1, y2), self.plan_box[3])]
        if floor:
            self.ground = room.floor_of(floor[0] / "spaces" / floor[1] / "navmesh.jsonl", cut, self.plan_box)
        else:
            self.ground = room.flat_floor(float(lo[2]))
        if not len(self.ground.T):
            self.ground = room.flat_floor(float(lo[2]))

    def faults(self) -> list[dict]:
        """The open faults: every fault the probe finds less those the drafter accepted (`accepted_faults`)."""
        if ((getattr(self, "files", None) or {}).get("place") or {}).get("view_only"):   # a source seen as it stands (look/srcview.py): nothing to mend
            self._accepted = []
            return []
        if getattr(self, "_faults", None) is None:
            found = geom.faults(self.pieces, self.ground, self.world)
            if self.space != "exterior":
                from tools.places.look import room
                found = room.held_by_shell(found, self.pieces)
            self._faults, self._accepted = split_accepted(found, getattr(self, "files", None))
        return self._faults

    def accepted_faults(self) -> list[dict]:
        """The faults the drafter accepted (place.json `draft.accepted_faults`: [{id, fault, why}]), each with its
        why: drawn and counted apart from the open ones, never in red."""
        self.faults()
        return self._accepted

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
                self.footprints[m] = info.get("bounds") if info.get("tris") and not info.get("placeholder") else None
            except Exception:
                self.footprints[m] = None
        b = self.footprints.get(m)
        return (b or base.get("bounds") or [[-32, -32, 0], [32, 32, 64]]), b is not None

    def piece(self, r: dict) -> dict | None:
        base = self.bases.get(r["base"])
        if base is None:   # a base a hand placed from the whole pool (look place): the catalogue's row
            from tools.places.draft_bundle import catalogue
            base = catalogue().get(r["base"])
            if base is not None:
                self.bases[r["base"]] = base
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
            g = self.ground.height(v[0], v[1])
            g = getattr(self.ground, "floor", 0.0) if g is None else g
            z = v[2] if len(v) > 2 else g
            return {"name": n, "kind": "point", "pieces": [], "lo": [v[0] - 400, v[1] - 400, z], "hi": [v[0] + 400, v[1] + 400, z + 300],
                    "point": [v[0], v[1], z]}
        if self.space != "exterior" and n.lower() in ("door", "the door"):   # a room's way out to where it opens from
            out = [p for p in self.pieces if p.get("kind") == "door" and (p.get("door") or {}).get("to_space") == (self.info.get("parent") or "exterior")]
            if out:   # standing where the way in lands inside (the outer door's to_pos)
                ext = {r["id"]: r for r in self.files["spaces"].get(self.info.get("parent") or "exterior", {}).get("refs") or []}
                land = ((ext.get(self.info.get("door_from")) or {}).get("door") or {}).get("to_pos")
                return self._of(n, "door", out[:1]) | ({"point": list(land)} if land else {})
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


def split_accepted(found: list[dict], files: dict | None) -> tuple[list[dict], list[dict]]:
    """Split probe faults into (open, accepted) by place.json `draft.accepted_faults` rows {id, fault, why}: a row
    accepts that piece's fault of that kind (any kind when `fault` is absent)."""
    rows = (((files or {}).get("place") or {}).get("draft") or {}).get("accepted_faults") or []
    acc = {}
    for r in rows:
        acc.setdefault(r.get("id"), []).append(r)
    open_, accepted = [], []
    for f in found:
        a = next((r for r in acc.get(f["id"], ()) if r.get("fault") in (None, f["fault"])), None)
        (open_ if a is None else accepted).append(f if a is None else {**f, "accepted": a.get("why", "")})
    return open_, accepted

