"""The built place's walking mesh for the studio: the navmesh records of the built plugin, decoded and joined per
space, so the studio draws people's routes on the mesh the game's people walk.

    python -m tools.places navexport <place_id> [--out out/places]

Writes <out>/nav/<place_id>.json: {esp_sha256, spaces: {<space>: {verts: [x, y, z, ...], tris: [a, b, c, ...],
nb: [n01, n12, n20, ...] (the triangle across each edge, -1 for none; cell seams joined), kind: [0 plain |
1 preferred | 2 water, ...], doors: [[triangle, ref id], ...]}}}. Outside is one mesh over the place's cells and the
world's round them; a room is its own. Positions are whole game units."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from tools.places import build as B
from tools.places import check as C

PREFERRED, WATER = 0x40, 0x200


def export(place_id: str, out: Path) -> Path:
    plan = json.loads((out / "shards" / place_id / "plan.json").read_text())
    esp = out / "plugin" / B.PLUGIN
    # with the world's own mesh round ours (the cells the plugin leaves as they are), as the build's checker loads it
    xs, ys = [c["x"] for c in plan["cells"]] or [0], [c["y"] for c in plan["cells"]] or [0]
    navs = C.load_navs(esp, C.world_nav_rows((min(xs) - B.NAV_RING, min(ys) - B.NAV_RING, max(xs) + B.NAV_RING, max(ys) + B.NAV_RING)))
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
    build = json.loads((out / "plugin" / "build.json").read_text())
    dst = out / "nav" / f"{place_id}.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".tmp")
    tmp.write_text(json.dumps({"esp_sha256": build.get("esp_sha256"), "spaces": spaces}, separators=(",", ":")))
    tmp.replace(dst)
    return dst


def current(place_id: str, out: Path) -> Path | None:
    """The export for the plugin as it stands (made again when the plugin was rebuilt); None when the place is not built."""
    bj, plan = out / "plugin" / "build.json", out / "shards" / place_id / "plan.json"
    if not (bj.exists() and plan.exists() and (out / "plugin" / B.PLUGIN).exists()):
        return None
    dst = out / "nav" / f"{place_id}.json"
    if dst.exists() and dst.stat().st_mtime >= max(bj.stat().st_mtime, plan.stat().st_mtime):
        return dst
    return export(place_id, out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places navexport")
    ap.add_argument("place_id")
    ap.add_argument("--out", default=str(B.OUT))
    a = ap.parse_args(argv)
    p = export(a.place_id, Path(a.out))
    d = json.loads(p.read_text())
    print(f"{p}: " + ", ".join(f"{s} {len(v['kind'])} triangles" for s, v in sorted(d["spaces"].items())))
    return 0
