"""The navmesh's L1 checks, over a built box (`<out>/in` the inputs, `<out>/navm` and `navi.json` the records).

    heights   every vertex within TOLERANCE_Z of the ground under it (the LAND's two triangulations of the quad
              bound it), or of the water surface; the triangles' centroids measured the same way (reported)
    degenerate  no triangle with zero area in plan (a repeated corner, or three corners on one line): the engine
              locates actors on the navmesh in plan, and a zero-area triangle has no inside and no normal
    links     every edge link has its reverse (the neighbour's triangle links back to this one), lands on a
              triangle that exists, and its two edges share both ends in plan
    islands   the walkable components across cells (triangle neighbours and edge links): every one apart from the
              largest is an island; the count, and each larger than ISLAND_REPORT_M2, are listed
    navi      the NAVI lists every NAVM once and nothing else; each entry's edge links are its NVNM's neighbour
              navmeshes, its location the vertex mean, its pathing cell the NVNM's
    road      the painted road samples inside the box (dry ones) that lie on a triangle: the share (measured)
    coverage  the same for every dry sample whose ground slope is within the walkable angle (measured)
"""
from __future__ import annotations

import base64
import json
import math
import struct
from collections import defaultdict
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.navmesh import nvnm, params, stitch
from tools.navmesh.esm import subrecords


class Rasters:
    def __init__(self, d: Path):
        g = json.loads((d / "grid.json").read_text())
        self.g = g
        shape = (g["rows"], g["cols"])
        self.h = np.memmap(d / "height.f32", np.float32, "r", shape=shape)
        self.w = np.memmap(d / "water.f32", np.float32, "r", shape=shape)
        self.f = np.memmap(d / "flags.u8", np.uint8, "r", shape=shape)
        obj = d / "objects.f32"  # the placed objects' boxes (inputs.py), 8 corners each
        self.boxes = np.fromfile(obj, np.float32).reshape(-1, 8, 3).astype(np.float64) if obj.exists() else None

    def top_dist(self, x, y, z, margin: float):
        """|z - the box top| at (x, y) for the highest placed box whose footprint (grown by `margin`) holds the point,
        else inf: a vertex on an object stands on that object, not the ground."""
        d = np.full(np.shape(x), np.inf)
        if self.boxes is None:
            return d
        p = np.stack([x, y], axis=1)
        for b in self.boxes:
            o, u, v = b[0, :2], b[1, :2] - b[0, :2], b[2, :2] - b[0, :2]
            lu, lv = np.linalg.norm(u), np.linalg.norm(v)
            a, c = (p - o) @ (u / lu), (p - o) @ (v / lv)
            m = (a >= -margin) & (a <= lu + margin) & (c >= -margin) & (c <= lv + margin)
            if m.any():
                d[m] = np.minimum(d[m], np.abs(np.asarray(z)[m] - b[4, 2]))
        return d

    def frac(self, x, y):
        g = self.g
        return (np.asarray(x, float) - g["x0"]) / g["step"], (g["ytop"] - np.asarray(y, float)) / g["step"]

    def ground_band(self, x, y):
        """(low, high) of the ground at (x, y) over the quad's two diagonal triangulations."""
        c, r = self.frac(x, y)
        c0 = np.clip(np.floor(c).astype(int), 0, self.g["cols"] - 2)
        r0 = np.clip(np.floor(r).astype(int), 0, self.g["rows"] - 2)
        u, v = c - c0, r - r0
        h = self.h
        a, b, cc, d = h[r0, c0], h[r0, c0 + 1], h[r0 + 1, c0], h[r0 + 1, c0 + 1]  # NW NE SW SE
        # diagonal NW-SE
        z1 = np.where(u >= v, a + u * (b - a) + v * (d - b), a + v * (cc - a) + u * (d - cc))
        # diagonal NE-SW
        z2 = np.where(u + v <= 1, a + u * (b - a) + v * (cc - a), d + (1 - u) * (cc - d) + (1 - v) * (b - d))
        return np.minimum(z1, z2), np.maximum(z1, z2)

    def water_at(self, x, y):
        c, r = self.frac(x, y)
        return self.w[np.clip(np.rint(r).astype(int), 0, self.g["rows"] - 1), np.clip(np.rint(c).astype(int), 0, self.g["cols"] - 1)]


def _dist_band(z, lo, hi):
    return np.maximum(np.maximum(lo - z, z - hi), 0.0)


class UF:
    def __init__(self):
        self.p = {}

    def find(self, a):
        p = self.p
        p.setdefault(a, a)
        while p[a] != a:
            p[a] = p[p[a]]
            a = p[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def local_components(n: nvnm.Nvnm) -> np.ndarray:
    t = len(n.tris)
    lab = np.arange(t)

    def f(i):
        while lab[i] != i:
            lab[i] = lab[lab[i]]
            i = lab[i]
        return i
    for ti in range(t):
        fl = int(n.tris["flags"][ti])
        for k in range(3):
            e = int(n.tris["e"][ti][k])
            if e >= 0 and not fl & nvnm.EDGE_LINK[k]:
                a, b = f(ti), f(e)
                if a != b:
                    lab[max(a, b)] = min(a, b)
    return np.array([f(i) for i in range(t)])


def plan_area_m2(v: np.ndarray, tv: np.ndarray) -> np.ndarray:
    a, b, c = v[tv[:, 0]], v[tv[:, 1]], v[tv[:, 2]]
    cr = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    return np.abs(cr) / 2 / su.UNITS_PER_METRE ** 2


def degenerate_mask(v: np.ndarray, tv: np.ndarray) -> np.ndarray:
    """Triangles with zero area in plan: a corner repeated, or the three corners on one line."""
    a, b, c = v[tv[:, 0]], v[tv[:, 1]], v[tv[:, 2]]
    cr = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    return (tv[:, 0] == tv[:, 1]) | (tv[:, 1] == tv[:, 2]) | (tv[:, 0] == tv[:, 2]) | (cr == 0)


def covered(points: np.ndarray, v: np.ndarray, tv: np.ndarray) -> np.ndarray:
    """Which plan points lie in some triangle (edges included, 0.5 unit slack)."""
    if len(points) == 0 or len(tv) == 0:
        return np.zeros(len(points), bool)
    a, b, c = v[tv[:, 0], :2], v[tv[:, 1], :2], v[tv[:, 2], :2]
    out = np.zeros(len(points), bool)
    for s in range(0, len(points), 256):
        p = points[s:s + 256, None, :]

        def side(u, w):
            return (w[None, :, 0] - u[None, :, 0]) * (p[..., 1] - u[None, :, 1]) - (w[None, :, 1] - u[None, :, 1]) * (p[..., 0] - u[None, :, 0])
        e = -0.5 * 128
        out[s:s + 256] = ((side(a, b) >= e) & (side(b, c) >= e) & (side(c, a) >= e)).any(axis=1)
    return out


def run(out: Path) -> dict:
    ras = Rasters(out / "in")
    box = ras.g["cells"]
    cos_max = math.cos(math.radians(params.MAX_SLOPE_DEG))
    vdev, cdev = [], []
    over = 0
    links = set()
    tri_count = {}
    seam_xy = {}
    comp_area: dict = defaultdict(float)
    uf = UF()
    navm_meta = {}
    road_n = road_in = 0
    walk = {"under_30": [0, 0], "30_to_40": [0, 0], "40_to_45": [0, 0]}
    max_slope_ground, steep_ground = 0.0, 0
    degenerate, degenerate_at = 0, []
    for x, y, fk, n in stitch.read_navm(out):
        local = int(fk.split(":")[0], 16)
        v = n.verts.astype(np.float64)
        tv = n.tris["v"].astype(int)
        tri_count[local] = len(tv)
        bad = degenerate_mask(v, tv)
        degenerate += int(bad.sum())
        degenerate_at += [[x, y, int(ti)] for ti in np.nonzero(bad)[0][:10 - len(degenerate_at)]]
        lo, hi = ras.ground_band(v[:, 0], v[:, 1])
        dg = _dist_band(v[:, 2], lo, hi)
        wl = ras.water_at(v[:, 0], v[:, 1])
        dw = np.where(np.isfinite(wl), np.abs(v[:, 2] - wl), np.inf)
        d = np.minimum(np.minimum(dg, dw), ras.top_dist(v[:, 0], v[:, 1], v[:, 2], params.TOLERANCE_Z))
        vdev.append(d)
        over += int((d > params.TOLERANCE_Z).sum())
        cen = v[tv].mean(axis=1)
        clo, chi = ras.ground_band(cen[:, 0], cen[:, 1])
        cdev.append(_dist_band(cen[:, 2], clo, chi))
        # slope of the ground triangles (neither water nor road)
        g = ((n.tris["flags"] & (nvnm.WATER | nvnm.PREFERRED)) == 0) & ~bad
        if g.any():
            a, b, c = v[tv[g, 0]], v[tv[g, 1]], v[tv[g, 2]]
            nrm = np.cross(b - a, c - a)
            cosz = np.abs(nrm[:, 2]) / np.linalg.norm(nrm, axis=1)
            max_slope_ground = max(max_slope_ground, float(np.degrees(np.arccos(np.clip(cosz.min(), -1, 1)))))
            steep_ground += int((cosz < cos_max).sum())
        # links
        for ti in range(len(tv)):
            fl = int(n.tris["flags"][ti])
            for k in range(3):
                if fl & nvnm.EDGE_LINK[k]:
                    lk = n.links[int(n.tris["e"][ti][k])]
                    other = int(lk["navm"]) & 0xFFFFFF
                    links.add((local, ti, other, int(lk["tri"])))
                    p, q = v[tv[ti, k], :2], v[tv[ti, (k + 1) % 3], :2]
                    seam_xy[(local, ti, other, int(lk["tri"]))] = tuple(sorted([tuple(p), tuple(q)]))
        # components
        lab = local_components(n)
        ar = plan_area_m2(v, tv)
        for ti, l in enumerate(lab):
            comp_area[(local, int(l))] += float(ar[ti])
        navm_meta[local] = (n, lab)
        # road and walkable coverage over the cell's own samples (dry)
        gx0, gy0 = su.cell_origin(x, y)
        c0 = int(round((gx0 - ras.g["x0"]) / ras.g["step"]))
        r0 = int(round((ras.g["ytop"] - gy0 - su.CELL_UNITS) / ras.g["step"]))
        Q = su.LAND_VERTS
        hh = np.asarray(ras.h[r0:r0 + Q, c0:c0 + Q], np.float64)
        ww = np.asarray(ras.w[r0:r0 + Q, c0:c0 + Q])
        ff = np.asarray(ras.f[r0:r0 + Q, c0:c0 + Q])
        gr, gc = np.gradient(hh, su.VERTEX_SPACING_UNITS)
        cosg = 1 / np.sqrt(1 + gr * gr + gc * gc)
        jj, ii = np.mgrid[0:Q, 0:Q]
        px, py = gx0 + ii * su.VERTEX_SPACING_UNITS, gy0 + su.CELL_UNITS - jj * su.VERTEX_SPACING_UNITS
        dry = ~np.isfinite(ww)
        inner = (ii >= 1) & (ii <= Q - 2) & (jj >= 1) & (jj <= Q - 2)  # away from the seams' half-voxel slack
        rm = (ff & 1).astype(bool) & dry & inner
        pts = np.stack([px[rm], py[rm]], axis=1).astype(np.float64)
        road_n += len(pts)
        road_in += int(covered(pts, v, tv).sum())
        deg = np.degrees(np.arccos(np.clip(cosg, -1, 1)))
        for name, lo_, hi_ in (("under_30", -1, 30), ("30_to_40", 30, 40), ("40_to_45", 40, params.MAX_SLOPE_DEG)):
            wm = dry & inner & (deg > lo_) & (deg <= hi_)
            pts = np.stack([px[wm], py[wm]], axis=1).astype(np.float64)
            walk[name][0] += len(pts)
            walk[name][1] += int(covered(pts, v, tv).sum())
    # symmetry
    asym = [lk for lk in links if (lk[2], lk[3], lk[0], lk[1]) not in links]
    bad_target = [lk for lk in links if lk[2] not in tri_count or not 0 <= lk[3] < tri_count[lk[2]]]
    bad_geom = [lk for lk in links if (lk[2], lk[3], lk[0], lk[1]) in seam_xy
                and seam_xy[lk] != seam_xy[(lk[2], lk[3], lk[0], lk[1])]]
    # islands across cells
    for (a_, ti, b_, tj) in links:
        if b_ in navm_meta:
            uf.union((a_, int(navm_meta[a_][1][ti])), (b_, int(navm_meta[b_][1][tj])))
    area = defaultdict(float)
    for k, ar in comp_area.items():
        area[uf.find(k)] += ar
    comps = sorted(area.values(), reverse=True)
    islands = comps[1:]
    big = sorted([a for a in islands if a > params.ISLAND_REPORT_M2], reverse=True)
    # the NAVI
    navi = json.loads((out / "navi.json").read_text())
    rec = base64.b64decode(navi["navi"])
    nv = [p for s, p in subrecords(rec[24:]) if s == b"NVMI"]
    seen, navi_err = set(), []
    for b in nv:
        f = struct.unpack_from("<I", b)[0] & 0xFFFFFF
        cx, cy, cz = struct.unpack_from("<3f", b, 8)
        o = 24
        k = struct.unpack_from("<I", b, o)[0]
        el = {e & 0xFFFFFF for e in struct.unpack_from(f"<{k}I", b, o + 4)}
        if f in seen:
            navi_err.append(f"{f:06X} twice")
        seen.add(f)
        if f not in navm_meta:
            navi_err.append(f"{f:06X} has no NAVM")
            continue
        n = navm_meta[f][0]
        if el != {int(lk["navm"]) & 0xFFFFFF for lk in n.links}:
            navi_err.append(f"{f:06X}: edge links differ from its NVNM's")
        if not np.allclose(n.verts.mean(axis=0), [cx, cy, cz], atol=0.01):
            navi_err.append(f"{f:06X}: location is not the vertex mean")
        gy, gx = struct.unpack_from("<hh", b, len(b) - 4)
        if (gx, gy) != n.grid_xy:
            navi_err.append(f"{f:06X}: pathing cell {gx},{gy} is not the NVNM's {n.grid_xy}")
    missing = sorted(set(navm_meta) - seen)
    vd = np.concatenate(vdev) if vdev else np.zeros(0)
    cd = np.concatenate(cdev) if cdev else np.zeros(0)
    res = {
        "box": box, "navm": len(navm_meta), "triangles": int(sum(tri_count.values())), "vertices": int(len(vd)),
        "objects": 0 if ras.boxes is None else len(ras.boxes),
        "heights": {"tolerance": params.TOLERANCE_Z, "over": over, "vertex_max": round(float(vd.max()), 2) if len(vd) else 0,
                    "vertex_p99": round(float(np.percentile(vd, 99)), 2) if len(vd) else 0,
                    "centroid_p99": round(float(np.percentile(cd, 99)), 2) if len(cd) else 0,
                    "centroid_max": round(float(cd.max()), 2) if len(cd) else 0},
        "degenerate": {"count": degenerate, "first": degenerate_at},
        "links": {"count": len(links), "asymmetric": len(asym), "bad_target": len(bad_target), "bad_geometry": len(bad_geom)},
        "islands": {"components": len(comps), "main_m2": round(comps[0], 1) if comps else 0,
                    "islands": len(islands), "islands_m2": round(sum(islands), 1),
                    f"over_{params.ISLAND_REPORT_M2:g}_m2": len(big), "largest_m2": [round(a, 1) for a in big[:10]]},
        "navi": {"entries": len(nv), "missing": len(missing), "errors": navi_err[:10], "error_count": len(navi_err)},
        "road": {"samples": road_n, "on_navmesh": road_in, "share": round(road_in / road_n, 4) if road_n else None},
        "coverage": {k: {"samples": a, "on_navmesh": b, "share": round(b / a, 4) if a else None}
                     for k, (a, b) in walk.items()},
        "ground_triangles_steeper_than_walkable": steep_ground,
        "max_ground_slope_deg": round(max_slope_ground, 1),
    }
    res["green"] = (over == 0 and degenerate == 0 and not asym and not bad_target and not bad_geom and not missing and not navi_err)
    return res


def verify_esm(esm_path: Path, out: Path) -> dict:
    """The written plugin against the built records: every NAVM present once, its NVNM byte for byte as built once
    Mutagen's FormID mapping is undone (the plugin's own index replaces the contract's), and the NAVI's entries."""
    from tools.navmesh import esm as esm_mod
    masters = esm_mod.masters(esm_path)
    own = len(masters)  # the plugin's own index in its FormIDs

    def remap(b: bytes) -> bytes:
        n = nvnm.decode(b)
        if n.world >> 24 == stitch.SELF:
            n.world = (own << 24) | (n.world & 0xFFFFFF)
        for i in range(len(n.links)):
            f = int(n.links["navm"][i])
            if f >> 24 == stitch.SELF:
                n.links["navm"][i] = (own << 24) | (f & 0xFFFFFF)
        return nvnm.encode(n)

    want = {}
    for x, y, fk, n in stitch.read_navm(out):
        want[int(fk.split(":")[0], 16)] = remap(nvnm.encode(n))
    got, same, extra = set(), 0, 0
    navi_entries = 0
    for r in esm_mod.records(esm_path, {b"NAVM", b"NAVI"}):
        if r.sig == b"NAVI":
            navi_entries += sum(1 for s, _ in esm_mod.subrecords(r.data) if s == b"NVMI")
            continue
        local = r.fid & 0xFFFFFF
        if local not in want or local in got:
            extra += 1
            continue
        got.add(local)
        same += dict(esm_mod.subrecords(r.data))[b"NVNM"] == want[local]
    return {"masters": masters, "built": len(want), "in_esm": len(got), "identical": same, "extra": extra,
            "navi_entries": navi_entries, "green": same == len(want) == len(got) == navi_entries and not extra}
