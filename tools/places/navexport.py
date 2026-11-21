"""The built place's walking mesh for the studio: the navmesh records of the built plugin, decoded and joined per
space, so the studio draws people's routes on the mesh the game's people walk.

    python -m tools.places navexport <place_id> [--out out/places]

Writes <out>/nav/<place_id>.json: {esp_sha256, from: "build", built_at, spaces: {<space>: {verts: [x, y, z, ...],
tris: [a, b, c, ...], nb: [n01, n12, n20, ...] (the triangle across each edge, -1 for none; cell seams joined),
kind: [0 plain | 1 preferred | 2 water, ...], doors: [[triangle, ref id], ...]}}}. Outside is one mesh over the
place's cells and the world's round them; a room is its own. Positions are whole game units. A preview build of the
walking mesh alone (walkpreview) writes the same shape from its plan, `from: "preview"`."""
import argparse
import json
import os
import threading
from collections import defaultdict
from pathlib import Path

from tools.places import build as B
from tools.places import check as C

PREFERRED, WATER = 0x40, 0x200


def _world_round(plan: dict) -> dict:
    """The world's own mesh round ours (the cells the plugin leaves as they are), as the build's checker loads it."""
    xs, ys = [c["x"] for c in plan["cells"]] or [0], [c["y"] for c in plan["cells"]] or [0]
    return C.world_nav_rows((min(xs) - B.NAV_RING, min(ys) - B.NAV_RING, max(xs) + B.NAV_RING, max(ys) + B.NAV_RING))


def export(place_id: str, out: Path) -> Path:
    plan = json.loads((out / "shards" / place_id / "plan.json").read_text())
    esp = out / "plugin" / B.PLUGIN
    navs = C.load_navs(esp, _world_round(plan), plan)
    build = json.loads((out / "plugin" / "build.json").read_text())
    bj = out / "plugin" / "build.json"
    built = max(bj.stat().st_mtime, (out / "shards" / place_id / "plan.json").stat().st_mtime)
    return _write(out / "nav" / f"{place_id}.json", {"esp_sha256": build.get("esp_sha256"), "from": "build", "built_at": _iso(built),
                                                     "spaces": spaces_of(navs, plan)})


def plan_navs(plan: dict) -> dict:
    """The navmeshes a plan wrote (its `navmesh.navm` records, before any plugin is written) with the world's round
    them, as load_navs reads them out of the plugin: the walking mesh of a preview build (walkpreview)."""
    import base64
    import struct

    from tools.navmesh import esm, nvnm
    names = list(plan["navmesh"]["masters"]) + [plan["navmesh"]["self"]]

    def key_of_raw(raw: int) -> str:
        i = raw >> 24
        return B.key_of(names[i] if i < len(names) else "?", raw & 0xFFFFFF)
    out = {}
    for e in plan["navmesh"]["navm"]:
        rec = base64.b64decode(e["record"])
        fid = struct.unpack_from("<I", rec, 12)[0]
        nv = nvnm.decode(next(p for s, p in esm.subrecords(rec[24:]) if s == b"NVNM"))
        fk = key_of_raw(fid)
        out[fk] = C.Nav(fk, "exterior" if nv.world else key_of_raw(nv.cell), nv.grid_xy, nv, key_of_raw)
    world = _world_round(plan)
    wn = ["Skyrim.esm", B.WORLD]
    for (x, y), e in world.items():
        rec = base64.b64decode(e["navm"])
        fid = struct.unpack_from("<I", rec, 12)[0]
        fk = B.key_of(B.WORLD, fid & 0xFFFFFF)
        if fk in out or (x, y) in {tuple(n.cell) for n in out.values() if n.space == "exterior"}:
            continue
        nv = nvnm.decode(next(p for s, p in esm.subrecords(rec[24:]) if s == b"NVNM"))
        out[fk] = C.Nav(fk, "exterior", (x, y), nv, lambda r, wn=wn: B.key_of(wn[r >> 24] if (r >> 24) < 2 else "?", r & 0xFFFFFF))
        out[fk].world = True
    return out


def export_plan(plan: dict, dst: Path, built_at: float, extra: dict | None = None) -> Path:
    """A preview build's walking mesh (from its plan, no plugin) in the export's shape, `from: "preview"`."""
    return _write(dst, {"esp_sha256": None, "from": "preview", "built_at": _iso(built_at), **(extra or {}),
                        "spaces": spaces_of(plan_navs(plan), plan)})


def _iso(t: float) -> str:
    import datetime
    return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(dst: Path, doc: dict) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(f".{dst.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(doc, separators=(",", ":")))
    tmp.replace(dst)
    return dst


def spaces_of(navs: dict, plan: dict) -> dict:
    room = {i["fk"]: i["space"] for i in plan["interiors"]}
    ref_id = {r["fk"]: r["id"] for r in plan["refs"]}
    by_space = defaultdict(list)
    for n in navs.values():
        space = "exterior" if n.space == "exterior" else room.get(n.space)
        if space:
            by_space[space].append(n)
    spaces = {}
    for space, group in by_space.items():
        group.sort(key=lambda n: n.fk)
        v0, t0 = {}, {}
        nv = nt = 0
        for n in group:
            v0[n.fk], t0[n.fk] = nv, nt
            nv, nt = nv + len(n.verts), nt + len(n.tri)
        verts, tris, nb, kind, doors = [], [], [], [], []
        for n in group:
            verts += [int(round(c)) for v in n.verts for c in v]
            for i, t in enumerate(n.tri):
                tris += [int(t[0]) + v0[n.fk], int(t[1]) + v0[n.fk], int(t[2]) + v0[n.fk]]
                f = int(n.flags[i])
                kind.append(2 if f & WATER else 1 if f & PREFERRED else 0)
                for k in range(3):
                    e, other = int(n.edge[i][k]), -1
                    if f & (1 << k):
                        if 0 <= e < len(n.links) and n.links[e][1] in t0:
                            other = t0[n.links[e][1]] + n.links[e][2]
                    elif e >= 0:
                        other = t0[n.fk] + e
                    nb.append(other)
            doors += [[t0[n.fk] + ti, ref_id[d]] for ti, d in n.doors if d in ref_id]
        spaces[space] = {"verts": verts, "tris": tris, "nb": nb, "kind": kind, "doors": doors}
    return spaces


_failed: dict[tuple[str, str], float] = {}   # (out, place) -> the build time whose export failed


def current(place_id: str, out: Path) -> Path | None:
    """The export for the plugin as it stands (made again when the plugin was rebuilt); None when the place is not
    built, or when this build's export failed (said once on stdout, and not tried again until the build changes)."""
    bj, plan = out / "plugin" / "build.json", out / "shards" / place_id / "plan.json"
    if not (bj.exists() and plan.exists() and (out / "plugin" / B.PLUGIN).exists()):
        return None
    dst = out / "nav" / f"{place_id}.json"
    built = max(bj.stat().st_mtime, plan.stat().st_mtime)
    if dst.exists() and dst.stat().st_mtime >= built:
        return dst
    if _failed.get((str(out), place_id)) == built:
        return None
    try:
        return export(place_id, out)
    except Exception as e:  # noqa: BLE001  the studio then draws routes on our ground; the reason is on the log
        print(f"navexport {place_id}: {type(e).__name__}: {e}"[:400], flush=True)
        _failed[(str(out), place_id)] = built
        return None


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places navexport")
    ap.add_argument("place_id")
    ap.add_argument("--out", default=str(B.OUT))
    a = ap.parse_args(argv)
    p = export(a.place_id, Path(a.out))
    d = json.loads(p.read_text())
    print(f"{p}: " + ", ".join(f"{s} {len(v['kind'])} triangles" for s, v in sorted(d["spaces"].items())))
    return 0
