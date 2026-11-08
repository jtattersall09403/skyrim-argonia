"""Off-game read of the ground paint: the edge, swathe and share metrics, and crops rendered as the game blends them.

    python3 -m tools.newworld.world.texcheck [--out out/newworld/plugin] [--crops]

Reads `<out>/tex/` shards (texture.py) as the engine stacks them (base, then each alpha layer replaces (1 - o) of
what is under it) and the landcover flags (land/water). Writes `<out>/tex/check.json` and, with --crops,
`<out>/crops/tex_*.png`: close crops at vertex resolution (each vertex's composite of the materials' real diffuse
textures, 6 repeats per cell edge, bilinear between vertices) plus `tex_overview.png` (1 px per vertex / 4).
Metrics (PASS limits):
  hard edge: per material, the step in composite weight between neighbouring vertices inside every quadrant
    (quadrant and cell border vertices are in both quadrants, so steps across borders are counted): p99 <= 0.41
    (BM&V's p99), max <= 0.75 (a ramp of at least two vertices: the 1-vertex blends vanilla uses at p50 stay
    below a full 0 -> 1 jump); seam: the same vertex read from each quadrant sharing it differs by <= 3/255 (8-bit
    opacities compounded over up to 7 layers).
  textures per land quadrant (weight >= 0.02 somewhere) mean >= 2.5; no material over 0.40 of any land 1 km
    window (17 x 17 cells, land >= 50%); GRAS share of land = the weight on materials with a grass list.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from tools.newworld.world import texture as tx

REPO = tx.REPO
DIFFUSE = {
    "forest_floor": "Landscape\\PineForest03.dds", "moss": "TEXTUREPACK\\landscape\\tundramoss01.dds",
    "wet_rock_moss": "TEXTUREPACK\\landscape\\grass\\rocksgrasswater01.dds", "swamp_mud": "TEXTUREPACK\\landscape\\rivermud.dds",
    "mud_reeds": "argonia\\landscape\\rivermud.dds", "marsh_grass": "argonia\\landscape\\CTQ_Grass_Lush01.dds",
    "rainforest": "argonia\\landscape\\CTQ_Undergrowth_01.dds", "rainforest_low": "argonia\\landscape\\CTQ_JungleGrass01_d.dds",
    "dirt_grass": "TEXTUREPACK\\landscape\\fielddirtgrass01.dds", "dark_grass_rocks": "landscape\\darklandgrassrocks.dds",
    "meadow": "Landscape\\FieldGrass02.dds", "sand": "landscape\\sand\\Sand03.dds",
    "wet_sand": "_ResourcePack\\Landscape\\SandWet01_d.dds", "rock": "landscape\\Apel_lh_rock_02.dds",
    "rock2": "vvardenfell\\rm\\rm_rock02.dds", "rock_grass": "Landscape\\TundraRocks01.dds", "dirt_road": "dirtroad01.dds",
    "road_skirt": "Landscape\\Dirt02.dds", "marsh_mud": "_ResourcePack\\Landscape\\MarshMud02_d.dds",
    "riverbed_edge": "Landscape\\RiverbedEdge.dds", "river_bottom": "Landscape\\RiverBottom.dds",
    "river_mud": "Landscape\\RiverMud.dds", "beach": "Landscape\\CoastBeach01.dds",
    "ocean_floor": "Landscape\\CoastOceanFloor01.dds", "dirt_slopes": "Landscape\\FrozenMarshDirtSlopes01.dds",
    "silt": "argonia\\landscape\\dirt02.dds",
}
FLAT = {"mud_reeds": (52, 44, 34), "marsh_grass": (88, 104, 52), "rainforest": (62, 74, 38),
        "rainforest_low": (74, 92, 44), "silt": (104, 92, 72)}  # KoTM's own textures are not on this machine
LOOSE = [Path.home() / ".argonia/stack/MO2/mods/bmv/textures"]
BSAS = [Path.home() / "games/skyrimse/Data" / n for n in
        ["_ResourcePack.bsa"] + [f"Skyrim - Textures{i}.bsa" for i in range(9)]]


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def read_rows(out: Path):
    man = json.loads((out / "tex/manifest.json").read_text())
    g = json.loads((out / "land/manifest.json").read_text())["grid"]
    return man, g


def cell_quads(data: bytes, i: int):
    base = i * 4 * tx.QBYTES
    return [tx.decode_quad(data, base + q * tx.QBYTES) for q in range(4)]


def check(out: Path) -> dict:
    man, g = read_rows(out)
    flags = np.load(tx.LC / "flags.npy", mmap_mode="r")
    nx, ny = g["cells_x"], g["cells_y"]
    cell_w = np.zeros((ny, nx, tx.NM), np.float64)
    cell_land = np.zeros((ny, nx), np.float64)
    hist = np.zeros(102, np.int64)  # steps in 0.01 bins, all materials, pairs with any weight
    maxstep = 0.0
    max_at = None
    prev_rows = None
    seam_max = 0.0
    nlayers, ntex_land = [], []
    for k, name in enumerate(man["shards"]):
        cy = int(name[2:-4])
        data = (out / "tex" / name).read_bytes()
        north = (g["cy_top"] - cy) * 32
        fl = np.asarray(flags[north:north + 33])[::-1]  # y from the south
        cur_rows = []
        for i in range(nx):
            qs = cell_quads(data, i)
            full = []
            for q, (mats, w) in enumerate(qs):
                dense = np.zeros((tx.Q, tx.Q, tx.NM), np.float32)
                for j, m in enumerate(mats):
                    dense[..., m] += w[:, j].reshape(tx.Q, tx.Q)
                full.append(dense)
                dx = np.abs(np.diff(dense, axis=1)); dy = np.abs(np.diff(dense, axis=0))
                st = np.concatenate([dx[dx > 0], dy[dy > 0]])
                if st.size:
                    hist += np.bincount(np.minimum((st * 100).astype(int), 101), minlength=102)
                    mx = float(st.max())
                    if mx > maxstep:
                        maxstep, max_at = mx, (g["cx0"] + i, cy, q)
                qy, qx = divmod(q, 2)
                land = (fl[qy * 16:qy * 16 + 17, i * 32 + qx * 16:i * 32 + qx * 16 + 17] & 1) == 0
                nlayers.append(len(mats))
                if land.any():
                    ntex_land.append(int(((dense * land[..., None]).max((0, 1)) >= 0.02).sum()))
                lw = (fl[qy * 16:qy * 16 + 17, i * 32 + qx * 16:i * 32 + qx * 16 + 17] & 1) == 0
                cell_w[ny - 1 - (cy - g["cy_bottom"]), i] += (dense * lw[..., None]).sum((0, 1))
                cell_land[ny - 1 - (cy - g["cy_bottom"]), i] += lw.sum()
            # seams inside the cell: BL|BR column, TL|TR column, BL/TL row, BR/TR row
            bl, br, tl, tr = full
            for a, b in ((bl[:, 16], br[:, 0]), (tl[:, 16], tr[:, 0]), (bl[16], tl[0]), (br[16], tr[0])):
                seam_max = max(seam_max, float(np.abs(a - b).max()))
            if i:
                for a, b in ((cur_rows[i - 1][1][:, 16], bl[:, 0]), (cur_rows[i - 1][3][:, 16], tl[:, 0])):
                    seam_max = max(seam_max, float(np.abs(a - b).max()))
            if prev_rows is not None:
                pa = prev_rows[i]  # the cell to the north: its bottom row is this cell's top row
                for a, b in ((pa[0][0], tl[16]), (pa[1][0], tr[16])):
                    seam_max = max(seam_max, float(np.abs(a - b).max()))
            cur_rows.append(full)
        prev_rows = cur_rows
        if k % 20 == 0:
            log(f"  check row {cy}")
    cdf = np.cumsum(hist) / hist.sum()
    p99 = float(np.searchsorted(cdf, 0.99) / 100)
    p90 = float(np.searchsorted(cdf, 0.90) / 100)
    # 1 km windows (17 x 17 cells)
    from scipy.ndimage import uniform_filter
    W = 17
    lw = uniform_filter(cell_land, W, mode="constant")
    landmask = lw >= 0.5 * 4 * tx.Q * tx.Q  # land >= 50% (vertices counted once per quadrant)
    sw = np.stack([uniform_filter(cell_w[..., m], W, mode="constant") for m in range(tx.NM)], -1)
    share = sw / np.maximum(lw[..., None], 1e-9)
    win = share[landmask]
    worst = float(win.max()) if win.size else 0.0
    worst_mat = tx.MAT[int(np.unravel_index(np.argmax(win), win.shape)[1])] if win.size else None
    wy, wx = np.unravel_index(np.argmax(np.where(landmask[..., None], share, 0).max(-1)), landmask.shape)
    worst_at = [int(g["cx0"] + wx), int(g["cy_top"] - wy)]
    tot = cell_w.sum((0, 1)); land_tot = cell_land.sum()
    table = {m: round(float(tot[j] / land_tot), 4) for j, m in enumerate(tx.MAT)}
    gras = sum(v for m, v in table.items() if tx.MATERIALS[m][1])
    res = {"step_p90": p90, "step_p99": p99, "step_max": round(maxstep, 3), "step_max_at": max_at,
           "seam_max": round(seam_max, 4), "layers_per_quadrant_mean": round(float(np.mean(nlayers)), 2),
           "textures_per_land_quadrant_mean": round(float(np.mean(ntex_land)), 2),
           "swathe_max_1km_land": round(worst, 3), "swathe_material": worst_mat, "swathe_at_cell": worst_at,
           "gras_share_of_land": round(gras, 3), "share_of_land": dict(sorted(table.items(), key=lambda x: -x[1]))}
    res["pass"] = bool(p99 <= 0.41 and maxstep <= 0.75 and seam_max <= 3 / 255 + 1e-6
                       and res["textures_per_land_quadrant_mean"] >= 2.5 and worst <= 0.40)
    (out / "tex/check.json").write_text(json.dumps(res, indent=1))
    return res


# --- rendering ----------------------------------------------------------------------------------------------------

class Tex:
    def __init__(self):
        self.bsas = None
        self.cache = {}

    def _bsa(self):
        if self.bsas is None:
            sys.path.insert(0, str(REPO / "out/newworld/research/flora_scripts"))
            from bsa import BSA  # noqa: E402  (the flora study's BSA reader)
            self.bsas = [BSA(p) for p in BSAS if p.exists()]
        return self.bsas

    def get(self, m: str) -> np.ndarray:
        if m in self.cache:
            return self.cache[m]
        img = None
        rel = DIFFUSE[m]
        for root in LOOSE:
            p = root / rel.replace("\\", "/")
            cands = [p] + list(p.parent.glob(p.name, case_sensitive=False)) if p.parent.exists() else []
            for c in cands:
                if c.exists():
                    img = Image.open(c)
                    break
            if img is not None:
                break
        if img is None and m not in FLAT:
            for b in self._bsa():
                key = ("textures\\" + rel).lower()
                if key in b.files:
                    img = Image.open(io.BytesIO(b.read(key)))
                    break
        if img is None:
            a = np.zeros((256, 256, 3), np.float32) + np.array(FLAT.get(m, (255, 0, 255)), np.float32)
        else:
            a = np.asarray(img.convert("RGB").resize((256, 256)), np.float32)
        self.cache[m] = a
        return a


def composite(out: Path, cx0: int, cy0: int, ncx: int, ncy: int, px_per_vertex: int = 8) -> np.ndarray:
    """RGB of cells [cx0, cx0+ncx) x [cy0, cy0+ncy) as the game blends: weights bilinear between vertices."""
    man, g = read_rows(out)
    V = 32 * ncx + 1, 32 * ncy + 1
    w = np.zeros((V[1], V[0], tx.NM), np.float32)  # y from the south
    for cy in range(cy0, cy0 + ncy):
        data = (out / "tex" / f"cy{cy:+04d}.bin").read_bytes()
        for cx in range(cx0, cx0 + ncx):
            qs = cell_quads(data, cx - g["cx0"])
            for q, (mats, ww) in enumerate(qs):
                qy, qx = divmod(q, 2)
                y0 = (cy - cy0) * 32 + qy * 16; x0 = (cx - cx0) * 32 + qx * 16
                d = np.zeros((tx.Q, tx.Q, tx.NM), np.float32)
                for j, m in enumerate(mats):
                    d[..., m] += ww[:, j].reshape(tx.Q, tx.Q)
                w[y0:y0 + 17, x0:x0 + 17] = d
    w = w[::-1]  # north up
    from scipy.ndimage import zoom
    H, W = (V[1] - 1) * px_per_vertex, (V[0] - 1) * px_per_vertex
    img = np.zeros((H, W, 3), np.float32)
    T = Tex()
    yy, xx = np.mgrid[0:H, 0:W]
    rep = 256 * 6 / (32 * px_per_vertex)  # texture px per image px: 6 repeats a cell
    u = ((xx * rep) % 256).astype(int); v = ((yy * rep) % 256).astype(int)
    for j, m in enumerate(tx.MAT):
        if w[..., j].max() < 1e-3:
            continue
        wj = zoom(w[..., j], ((H) / (V[1] - 1), (W) / (V[0] - 1)), order=1)[:H, :W]
        img += wj[..., None] * T.get(m)[v, u]
    return np.clip(img, 0, 255).astype(np.uint8)


def overview(out: Path, step: int = 4) -> None:
    man, g = read_rows(out)
    T = Tex()
    mean = np.stack([T.get(m).reshape(-1, 3).mean(0) for m in tx.MAT])
    rows = []
    for name in man["shards"]:
        data = (out / "tex" / name).read_bytes()
        band = np.zeros((32 // step, g["cells_x"] * 32 // step, 3), np.float32)
        for i in range(g["cells_x"]):
            for q, (mats, w) in enumerate(cell_quads(data, i)):
                qy, qx = divmod(q, 2)
                c = (w @ mean[mats]).reshape(tx.Q, tx.Q, 3)[:16:step, :16:step]
                band[(1 - qy) * 16 // step:(2 - qy) * 16 // step, (i * 32 + qx * 16) // step:(i * 32 + qx * 16 + 16) // step] = c[::-1]
        rows.append(band)
    Image.fromarray(np.clip(np.concatenate(rows), 0, 255).astype(np.uint8)).save(out / "crops/tex_overview.png")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=REPO / "out/newworld/plugin")
    ap.add_argument("--crops", nargs="*", help="name:cx,cy,ncx,ncy ...")
    ap.add_argument("--overview", action="store_true")
    ap.add_argument("--no-metrics", action="store_true")
    a = ap.parse_args(argv)
    (a.out / "crops").mkdir(parents=True, exist_ok=True)
    ok = True
    if not a.no_metrics:
        r = check(a.out)
        print(json.dumps({k: v for k, v in r.items() if k != "share_of_land"}, indent=1))
        print("texcheck", "PASS" if r["pass"] else "FAIL")
        ok = r["pass"]
    for spec in a.crops or []:
        name, box = spec.split(":")
        cx, cy, nx, ny = map(int, box.split(","))
        Image.fromarray(composite(a.out, cx, cy, nx, ny)).save(a.out / f"crops/tex_{name}.png")
    if a.overview:
        overview(a.out)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
