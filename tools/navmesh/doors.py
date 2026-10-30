"""Load doors on the navmesh (2.W4 §b; lane nav-walk): door triangles, Argonia.esm's NAVM/NAVI overlay, the L1 check.

The vanilla rule (Skyrim.esm, 426 of 426 door triangles): the triangle holding a load door's **arrival point** (the
position in its linked door's XTEL, where the traveller lands beside it) has flag Door (0x400) and an NVNM door
entry naming the door; the navmesh's NVMI lists the door among its door links. Our exterior doors are Argonia.esm
REFRs while the exterior NAVMs are ArgoniaWorld.esm's, which cannot master Argonia.esm. So the door cells' NAVMs are
overridden in Argonia.esm (geometry as built, plus the door data), with a NAVI override that carries only their
NVMI, as Dawnguard and King of the Murkmire override the NAVI with their own entries only.

    python -m tools.navmesh doors overlay --nav DIR --intermediate JSON --out doors.json
        the overlay ArgoniaGen writes into Argonia.esm (PlaceCells.cs, $ARGONIA_NAV_DOORS):
        {"schema": 1, "masters": [Skyrim.esm, ArgoniaWorld.esm], "self": "Argonia.esm",
         "navm": [{"x", "y", "worldspace", "formKey", "navm": base64 NAVM record}], "navi": base64 NAVI record,
         "doors": [{"door", "navm", "triangle"}]}
    python -m tools.navmesh doors check --nav DIR --intermediate JSON [--esm Argonia.esm] [--data DIR]
        L1: every built place's load door has its door triangle within DOOR_TRI_M of its arrival point on both
        sides, in the navmesh that wins (Argonia.esm's override, else ArgoniaWorld.esm's as built in DIR, else the
        borrowed interior's own plugin). Exit 1 when red.
    python -m tools.navmesh doors reach --nav DIR --intermediate JSON [--esm ...] [--data DIR]
        path queries: from the road to every exterior door's arrival, and inside each interior from the arrival to
        each of its beds (paths.py over the winning NVNMs)
"""
from __future__ import annotations

import argparse
import base64
import gzip
import json
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.navmesh import esm, nvnm, paths, stitch

MASTERS = ["Skyrim.esm", stitch.SELF_FILE]  # the overlay's FormIDs: index 1 is ArgoniaWorld.esm, as the built records
SELF_FILE = "Argonia.esm"
DOOR_TRI_M = 1.0  # the arrival point lies within this of its door triangle, in plan (vanilla: inside it)
DOOR_TRI_DZ = 128.0  # units: and within the agent's height of it
FIXTURES = "place:fixtures"  # the proving ground: a test room with no navmesh, not a place people walk


@dataclass
class Door:
    form_key: str  # the door REFR
    exterior: bool
    cell: str  # its CELL FormKey
    worldspace: str | None
    pos: tuple[float, float, float]
    arrival: tuple[float, float, float]  # where a traveller through the linked door lands, beside this door
    edid: str | None


def load_doors(intermediate: Path) -> list[Door]:
    """Every load door the built places lay (not the fixtures), with its arrival point from its partner's XTEL."""
    recs = json.loads(Path(intermediate).read_text(encoding="utf-8"))["records"]
    refs: dict[str, tuple[dict, dict]] = {}
    for r in recs:
        if r["type"] == "CELL" and r.get("layer", "").startswith("place:") and r["layer"] != FIXTURES:
            for x in r.get("refs", []):
                if "teleport" in x and not x.get("disabled"):
                    refs[x["formKey"]] = (r, x)
    out = []
    for fk, (cell, x) in sorted(refs.items()):
        partner = refs.get(x["teleport"]["door"])
        if partner is None:
            raise ValueError(f"door {fk}: its partner {x['teleport']['door']} is not a built door")
        out.append(Door(fk, bool(cell.get("worldspace")), cell["formKey"], cell.get("worldspace"),
                        tuple(x["pos"]), tuple(partner[1]["teleport"]["pos"]), x.get("edid")))
    return out


def form_id(form_key: str, masters: list[str], self_file: str) -> int:
    local, plugin = form_key.split(":", 1)
    names = [m.lower() for m in masters] + [self_file.lower()]
    return (names.index(plugin.lower()) << 24) | int(local, 16)


def form_key(fid: int, masters: list[str], self_file: str) -> str:
    i = fid >> 24
    return f"{fid & 0xFFFFFF:06X}:{masters[i] if i < len(masters) else self_file}"


# ---- navmeshes as the game resolves them: (key, Nvnm, doors as FormKeys) --------------------------------------
@dataclass
class Navm:
    key: str  # the NAVM's FormKey
    n: nvnm.Nvnm
    doors: list[tuple[int, str]]  # (triangle, door FormKey)
    cell: str | None = None  # an interior NAVM's CELL FormKey


def built_navms(nav: Path, cells: set[tuple[int, int]]) -> dict[str, Navm]:
    """ArgoniaWorld.esm's NAVMs of these grid cells, as built under nav/navm (stitch.py; byte for byte the plugin's)."""
    out = {}
    for cy in sorted({c[1] for c in cells}):
        p = nav / "navm" / f"cy{cy:+04d}.jsonl.gz"
        if not p.exists():
            continue
        with gzip.open(p, "rt", encoding="ascii") as f:
            for line in f:
                d = json.loads(line)
                if (d["x"], d["y"]) in cells:
                    rec = base64.b64decode(d["navm"])
                    n = nvnm.decode(dict(esm.subrecords(rec[24:]))[b"NVNM"])
                    out[d["formKey"]] = Navm(d["formKey"], n, [(int(t), form_key(int(dr), stitch.MASTERS, stitch.SELF_FILE))
                                                               for t, _, dr in n.doors])
    return out


def plugin_navms(path: Path, want=None) -> dict[str, Navm]:
    """A plugin's NAVMs (all, or those `want(fk, cell_fk, nvnm)` keeps), their FormIDs read through its masters."""
    masters = esm.masters(path)
    own = path.name
    out = {}
    for r in esm.records(path, {b"NAVM"}, groups={b"CELL", b"WRLD"}):
        n = nvnm.decode(dict(esm.subrecords(r.data))[b"NVNM"])
        fk = form_key(r.fid, masters, own)
        cell = form_key(r.cell, masters, own) if r.cell else None
        if want is None or want(fk, cell, n):
            out[fk] = Navm(fk, n, [(int(t), form_key(int(d), masters, own)) for t, _, d in n.doors], cell)
    return out


def _plan_dist(p, tri: np.ndarray) -> float:
    """Distance in plan from p to the triangle (0 inside)."""
    a, b, c = tri[:, :2]
    q = np.asarray(p[:2], float)

    def seg(u, v):
        d = v - u
        t = float(np.clip(np.dot(q - u, d) / (np.dot(d, d) or 1.0), 0, 1))
        return float(np.linalg.norm(q - (u + t * d)))
    cr = [(v[0] - u[0]) * (q[1] - u[1]) - (v[1] - u[1]) * (q[0] - u[0]) for u, v in ((a, b), (b, c), (c, a))]
    if all(x >= 0 for x in cr) or all(x <= 0 for x in cr):
        return 0.0
    return min(seg(a, b), seg(b, c), seg(c, a))


def door_triangle_near(navms: list[Navm], door: str, p) -> tuple[str, int, float] | None:
    """The door triangle of `door` nearest p in plan, within DOOR_TRI_M and DOOR_TRI_DZ, or None."""
    best = None
    lim = DOOR_TRI_M * su.UNITS_PER_METRE
    for m in navms:
        for t, d in m.doors:
            if d.lower() != door.lower() or not int(m.n.tris["flags"][t]) & nvnm.DOOR:
                continue
            tri = m.n.verts[m.n.tris["v"][t].astype(int)].astype(float)
            dist = _plan_dist(p, tri)
            if dist <= lim and abs(float(tri[:, 2].mean()) - p[2]) <= DOOR_TRI_DZ and (best is None or dist < best[2]):
                best = (m.key, t, dist)
    return best


def _around(p) -> set[tuple[int, int]]:
    cx, cy = su.cell_of(p[0], p[1])
    return {(cx + dx, cy + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}


# ---- the overlay ---------------------------------------------------------------------------------------------
def nvmi_with_doors(b: bytes, doors: list[int]) -> bytes:
    """An NVMI (nvnm.nvmi's layout) with its door links replaced by `doors` (raw FormIDs), sorted."""
    o = 24
    for _ in range(2):  # edge links, preferred edge links
        o += 4 + 4 * struct.unpack_from("<I", b, o)[0]
    nd = struct.unpack_from("<I", b, o)[0]
    ds = sorted(set(doors))
    mid = struct.pack("<I", len(ds)) + b"".join(struct.pack("<II", nvnm.PATHING_DOOR, d) for d in ds)
    return b[:o] + mid + b[o + 4 + 8 * nd:]


def overlay(nav: Path, intermediate: Path) -> dict:
    """The door cells' NAVMs with their door triangles marked, and the NAVI entries for them alone."""
    doors = [d for d in load_doors(intermediate) if d.exterior]
    cells = set().union(*(_around(d.arrival) for d in doors)) if doors else set()
    navms = built_navms(nav, cells)
    keyed = {int(k.split(":")[0], 16): m for k, m in navms.items()}
    g = paths.Graph([(k, m.n) for k, m in keyed.items()])
    marked: dict[int, list[tuple[int, int]]] = {}
    summary = []
    worlds = {}
    for d in doors:
        hit = g.locate(d.arrival, DOOR_TRI_DZ)
        if hit is None:  # left for the check to report red (the navmesh may predate the door: `make navmesh`)
            summary.append({"door": d.form_key, "navm": None, "triangle": None})
            print(f"doors: WARNING {d.form_key} ({d.edid}): its arrival {d.arrival} is on no navmesh", file=sys.stderr)
            continue
        k, t = hit
        marked.setdefault(k, []).append((t, form_id(d.form_key, MASTERS, SELF_FILE)))
        worlds[k] = d.worldspace
        summary.append({"door": d.form_key, "navm": keyed[k].key, "triangle": t})
    navi = json.loads((nav / "navi.json").read_text())
    nvmis = {struct.unpack_from("<I", p)[0]: p for s, p in esm.subrecords(base64.b64decode(navi["navi"])[24:]) if s == b"NVMI"}
    lines, entries = [], []
    for k in sorted(marked):
        n = keyed[k].n
        for t, _ in marked[k]:
            n.tris["flags"][t] |= nvnm.DOOR
        rows = sorted(set(map(tuple, n.doors.tolist())) | {(t, nvnm.PATHING_DOOR, f) for t, f in marked[k]})
        n.doors = np.array(rows, nvnm.DOOR_TRI)
        fid = stitch.fid(k)
        rec = stitch.record(b"NAVM", fid, esm.pack_subrecord(b"NVNM", nvnm.encode(n)))
        x, y = n.grid_xy
        lines.append({"x": x, "y": y, "worldspace": worlds[k], "formKey": keyed[k].key,
                      "navm": base64.b64encode(rec).decode("ascii")})
        entries.append(nvmi_with_doors(nvmis[fid], [int(f) for _, _, f in rows]))
    return {"schema": 1, "masters": MASTERS, "self": SELF_FILE, "navm": lines,
            "navi": base64.b64encode(stitch.navi_record(entries)).decode("ascii") if entries else None,
            "doors": summary}


# ---- the L1 check and the path queries -------------------------------------------------------------------------
class Winning:
    """The NAVMs the game resolves: Argonia.esm's overrides over ArgoniaWorld.esm's as built and the borrowed
    interiors' own plugins."""

    def __init__(self, nav: Path, doors: list[Door], ours: Path | None, data: Path, overlay_json: dict | None = None):
        self.nav, self.data = nav, data
        self.over: dict[str, Navm] = {}
        if ours is not None and ours.exists():
            self.over = plugin_navms(ours)
        elif overlay_json:  # the overlay before it is written: its records read with its own masters
            for line in overlay_json["navm"]:
                n = nvnm.decode(dict(esm.subrecords(base64.b64decode(line["navm"])[24:]))[b"NVNM"])
                self.over[line["formKey"]] = Navm(line["formKey"], n, [(int(t), form_key(int(d), overlay_json["masters"],
                                                                                        overlay_json["self"])) for t, _, d in n.doors])
        ext = [d for d in doors if d.exterior]
        self.ext = built_navms(nav, set().union(*(_around(d.arrival) for d in ext))) if ext else {}
        self.int: dict[str, Navm] = {}
        by_plugin: dict[str, set[str]] = {}
        for d in doors:
            if not d.exterior:
                by_plugin.setdefault(d.cell.split(":", 1)[1], set()).add(d.cell.lower())
        for plugin, cells in by_plugin.items():
            p = data / plugin
            if p.exists():
                self.int.update(plugin_navms(p, lambda fk, cell, n, cells=cells: (cell or "").lower() in cells))

    def side(self, d: Door) -> list[Navm]:
        """The NAVMs on the door's arrival side: the cells around an exterior arrival, else the door's interior."""
        if d.exterior:
            near = _around(d.arrival)
            base = {k: m for k, m in self.ext.items() if m.n.grid_xy in near}
            base.update({k: m for k, m in self.over.items() if m.n.world and m.n.grid_xy in near})
        else:
            here = d.cell.lower()
            base = {k: m for k, m in self.int.items() if (m.cell or "").lower() == here}
            base.update({k: m for k, m in self.over.items() if (m.cell or "").lower() == here})
        return list(base.values())


def check(doors: list[Door], win: Winning) -> dict:
    rows, red = [], []
    for d in doors:
        side = win.side(d)
        hit = door_triangle_near(side, d.form_key, d.arrival)
        row = {"door": d.form_key, "edid": d.edid, "side": "exterior" if d.exterior else "interior",
               "navms": len(side), "door_triangle": None if hit is None else {"navm": hit[0], "triangle": hit[1],
                                                                               "plan_dist": round(hit[2], 1)}}
        rows.append(row)
        if hit is None:
            red.append(f"{d.form_key} ({d.edid or d.cell}, {row['side']}): no door triangle within "
                       f"{DOOR_TRI_M:g} m of its arrival {tuple(round(v, 1) for v in d.arrival)} ({len(side)} NAVMs)")
    return {"doors": len(doors), "with_door_triangle": len(doors) - len(red), "rows": rows, "red": red, "green": not red}


def reach(doors: list[Door], win: Winning, start, intermediate: Path, bed_bases: set[str]) -> dict:
    """From `start` (the road) to every exterior door's arrival; inside, from the arrival to each bed."""
    out = {}
    ext = [d for d in doors if d.exterior]
    if ext:
        cells = set().union(*(_around(d.arrival) for d in ext)) | _around(start)
        navms = built_navms(win.nav, cells)
        navms.update({k: m for k, m in win.over.items() if m.n.world and m.n.grid_xy in cells})
        g = paths.Graph([(int(k.split(":")[0], 16), m.n) for k, m in navms.items()])
        a = g.locate(start)
        for d in ext:
            p = g.path(a, g.locate(d.arrival))
            out[d.form_key] = {"edid": d.edid, "from": "road", "path_tris": None if p is None else len(p)}
    recs = json.loads(Path(intermediate).read_text(encoding="utf-8"))["records"]
    beds = {r["formKey"].lower(): [x for x in r.get("refs", []) if x["base"] in bed_bases] for r in recs if r["type"] == "CELL"}
    for d in doors:
        if d.exterior:
            continue
        side = win.side(d)
        g = paths.Graph([(int(m.key.split(":")[0], 16), m.n) for m in side])
        a = g.locate(d.arrival)
        if a is None:  # a traveller off the mesh's edge walks from the door's own triangle, as the engine routes
            hit = door_triangle_near(side, d.form_key, d.arrival)
            a = (int(hit[0].split(":")[0], 16), hit[1]) if hit else None
        for b in beds.get(d.cell.lower(), []):
            goal = _nearest(g, b["pos"])
            p = g.path(a, goal[:2]) if goal else None
            out[f"{d.form_key} -> bed {b['formKey']}"] = {"from": "arrival", "path_tris": None if p is None else len(p),
                                                          "bed_to_navmesh_units": None if goal is None else round(goal[2], 1)}
    return out


def _nearest(g: paths.Graph, p, reach_units: float = 150.0):
    """The triangle whose centroid is nearest p in plan within reach_units (a bed stands over no navmesh: its
    users walk to its side)."""
    best = None
    for k, c in g.cent.items():
        d = np.hypot(c[:, 0] - p[0], c[:, 1] - p[1])
        d[np.abs(c[:, 2] - p[2]) > DOOR_TRI_DZ] = np.inf
        i = int(np.argmin(d))
        if d[i] <= reach_units and (best is None or d[i] < best[2]):
            best = (k, i, float(d[i]))
    return best


def main(argv=None) -> int:
    from tools.navmesh.__main__ import game_data
    ap = argparse.ArgumentParser(prog="python -m tools.navmesh doors")
    ap.add_argument("cmd", choices=["overlay", "check", "reach"])
    ap.add_argument("--nav", required=True)
    ap.add_argument("--intermediate", required=True)
    ap.add_argument("--out")
    ap.add_argument("--esm", help="the generated Argonia.esm, whose NAVM overrides win")
    ap.add_argument("--overlay", help="an overlay (doors.json) standing in for Argonia.esm's NAVMs, before it is written")
    ap.add_argument("--data", help="the Data folder holding the borrowed interiors' plugins")
    ap.add_argument("--start", default="-229120.07,43306.46,2594.6", help="reach: the road point (x,y,z units; Claywater: ARG_Ref_ClaywaterStationRoadIn)")
    ap.add_argument("--beds", default="0259DF:King of the Murkmire.esp", help="reach: the bed bases, comma-separated")
    a = ap.parse_args(argv)
    nav, inter = Path(a.nav), Path(a.intermediate)
    if a.cmd == "overlay":
        ov = overlay(nav, inter)
        Path(a.out).write_text(json.dumps(ov, sort_keys=True) + "\n")
        print(json.dumps({"overlay": a.out, "navm": len(ov["navm"]), "doors": ov["doors"]}))
        return 0
    doors = load_doors(inter)
    ov = json.loads(Path(a.overlay).read_text()) if a.overlay else None
    win = Winning(nav, doors, Path(a.esm) if a.esm else None, Path(a.data) if a.data else game_data(), ov)
    if a.cmd == "check":
        res = check(doors, win)
        print(json.dumps({k: res[k] for k in ("doors", "with_door_triangle", "red", "green")}))
        return 0 if res["green"] else 1
    res = reach(doors, win, tuple(float(v) for v in a.start.split(",")), inter, set(a.beds.split(",")))
    print(json.dumps(res, indent=1))
    return 0 if all(v["path_tris"] for v in res.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
