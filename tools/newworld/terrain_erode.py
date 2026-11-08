"""Weathering: the natural ground (terrain_relief's output, metres above the water) eroded and detailed so it reads like
Skyrim's, before water, places and roads shape it. Runs between relief and compose in terrain.build, so everything
downstream (shores, beds, pads, roads, entrances, the water guarantee) is laid on the weathered ground exactly as
before: the water mask, the water level and every shore are untouched by construction, and no water is added.

The recipe (each step measured against Skyrim's Tamriel and BM&V's Black Marsh in terrain_quality):
1. Drainage (stream power, implicit, Braun and Willett 2013) on a grid eight samples apart (14.6 m): depressions on
   land are filled, every land sample drains by steepest descent to the water (the map's water and the grid's edge
   are the only outlets; routed on a copy jittered by up to 0.25 m each step so filled flats never drain down
   dead-straight lines), and the ground is lowered by K A^0.5 S each step, with hillslope diffusion between. This
   cuts the dendritic ridge-and-valley structure value noise lacks, and removes its closed hollows. The valleys are
   dry: the eroded ground is held at least DRY_M above the water, so no water course is added.
2. Erodibility K follows each region's relief span (summit - floor): about none under 15 m (marsh, bayou, basin stay
   flat and hummocky), full over 60 m (uplands, ridges and mesas carve the most). Mesa tops keep their flats: K is cut
   where the ground is a plateau.
3. Valleys, not trenches: the coarse cut is spread over two widths (VALLEY_SIGMA, mixed by VALLEY_MIX), so a
   valley's width and depth grow with its drainage and its floor is rounded; no cut is deeper than MAX_CUT_SHARE of
   the ground's height over its lowest point within 400 m. Then resampled (cubic) onto the full-resolution ground.
4. Detail: slope-weighted fine relief at 20 to 45 m (ridged noise, strongest on slopes, none on flats and valley
   floors), sized from the region's roughness, so hillsides carry Skyrim's 20 m texture.
5. Thermal weathering at full resolution: wherever two neighbours differ by more than the talus slope (TALUS_DEG,
   unless the slope is a cliff by design, over CLIFF_KEEP_DEG), a share of the difference moves downhill. This
   rounds noise spikes into scree without touching the cliffs FreeClimb climbs.
6. Low ground: where the region's relief span is under 40 m, fine relief under 15 m is cut to a sixth (fading in
   from 15 m span), so marsh lies flat between softer hummocks, as BM&V's does.
7. Hollows: every closed hollow on land is filled to its spill height (the water and the grid's edge are the
   outlets), so all ground drains and low ground lies flat between its hummocks, as BM&V's marsh does.
8. Room to build (settle_places): each large built place (settlement tier town and up) gets a buildable core:
   within the radius BUILD_R_M[tier] the ground is eased toward its own broad shape (a 60 m Gaussian) until no slope
   exceeds BUILD_MAX_SLOPE; the remaining natural relief is kept at BUILD_KEEP of its amplitude, and the ease fades
   out over a skirt as wide as the radius, round an irregular edge, so the place sits in the land, neither bulldozed nor perched.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from skimage.morphology import reconstruction

M = 128.0 / 70.0          # metres a sample
C = 8                     # drainage grid: one node every C samples (14.6 m)
DRY_M = 0.8               # eroded land stays this far above the water: valleys are dry
K0 = 4.5e-3               # stream-power erodibility (per step, A in m^2, S dimensionless)
STEPS = 30
VALLEY_SIGMA = (1.0, 3.0)  # the incision spread over two widths (drainage nodes): swales and broad valleys
VALLEY_MIX = (0.6, 1.2)
MAX_CUT_SHARE = 0.4        # no valley deeper than this share of the ground's height over its lowest point in 400 m
DIFFUSE = 0.12            # hillslope diffusion per step (share of the Laplacian)
TALUS_DEG = 42.0
CLIFF_KEEP_DEG = 55.0
# Room to build: the buildable core's radius (metres) by settlement tier, the steepest slope left in it, and how much
# of the natural relief inside it survives.
BUILD_R_M = {"megalopolis": 450.0, "metropolis": 300.0, "large-city": 220.0, "small-city": 160.0, "town": 110.0}
BUILD_MAX_SLOPE_DEG = 8.0
BUILD_KEEP = 0.35

_NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def _down(a: np.ndarray, c: int) -> np.ndarray:
    r, k = a.shape[0] // c, a.shape[1] // c
    return a[:r * c, :k * c].reshape(r, c, k, c).mean((1, 3))


def _up(a: np.ndarray, shape, c: int) -> np.ndarray:
    z = ndi.zoom(a, c, order=3, mode="nearest", grid_mode=True)
    out = np.zeros(shape, np.float32)
    r, k = min(shape[0], z.shape[0]), min(shape[1], z.shape[1])
    out[:r, :k] = z[:r, :k]
    out[r:, :k] = out[r - 1:r, :k]
    out[:, k:] = out[:, k - 1:k]
    return out


def fill(h: np.ndarray, outlet: np.ndarray) -> np.ndarray:
    """Depressions filled to their spill height, outlets fixed, plus a tiny tilt toward the spill so flats drain."""
    seed = np.where(outlet, h, h.max() + 1.0)
    filled = reconstruction(seed, h, method="erosion")
    flat = filled > h + 1e-6
    tilt = ndi.distance_transform_edt(flat) * 1e-4
    return filled + tilt


def receivers(h: np.ndarray, outlet: np.ndarray, dx: float) -> tuple[np.ndarray, np.ndarray]:
    """D8 steepest-descent receiver of every node (itself for an outlet or a sink) and the drop distance."""
    R, K = h.shape
    idx = np.arange(R * K).reshape(R, K)
    best = np.zeros(h.shape)
    rcv = idx.copy()
    dist = np.full(h.shape, dx)
    hp = np.pad(h, 1, mode="edge")
    ip = np.pad(idx, 1, mode="edge")
    for di, dj in _NB:
        d = dx * (1.4142 if di and dj else 1.0)
        nb = hp[1 + di:1 + di + R, 1 + dj:1 + dj + K]
        s = (h - nb) / d
        better = s > best
        best = np.where(better, s, best)
        rcv = np.where(better, ip[1 + di:1 + di + R, 1 + dj:1 + dj + K], rcv)
        dist = np.where(better, d, dist)
    rcv[outlet] = idx[outlet]
    return rcv.ravel(), dist.ravel()


def stream_power(h: np.ndarray, outlet: np.ndarray, k: np.ndarray, floor: np.ndarray, steps: int = STEPS,
                 dx: float = C * M) -> np.ndarray:
    """Implicit stream-power erosion with diffusion; outlets fixed; land never below `floor`."""
    h = h.astype(np.float64).copy()
    rng = np.random.default_rng(29)
    kf = k.ravel().astype(np.float64)
    fl = floor.ravel()
    area0 = dx * dx
    for _ in range(steps):
        hf = fill(h, outlet)
        # routing on a jittered copy: filled flats would otherwise drain down dead-straight D8 lines
        jit = hf + np.where(outlet, 0, rng.uniform(0, 0.25, h.shape))
        rcv, dist = receivers(jit, outlet, dx)
        order = np.argsort(jit.ravel(), kind="stable")           # low to high: every receiver before its donors
        acc = np.full(rcv.size, area0)
        rv = rcv.tolist()
        al = acc.tolist()
        for n in order[::-1].tolist():                          # high to low: pass area downstream
            r = rv[n]
            if r != n:
                al[r] += al[n]
        acc = np.asarray(al)
        f = kf * np.sqrt(acc) / dist                            # m = 0.5, n = 1
        z = jit.ravel().copy()
        fl_ = f.tolist()
        zl = z.tolist()
        for n in order.tolist():                                # low to high: implicit update
            r = rv[n]
            if r != n:
                zl[n] = (zl[n] + fl_[n] * zl[r]) / (1 + fl_[n])
        z = np.maximum(np.asarray(zl), fl).reshape(h.shape)
        z = np.where(outlet, h, np.minimum(z, hf))
        z += DIFFUSE * np.where(outlet, 0, ndi.laplace(z))
        h = np.maximum(z, floor)
    return h.astype(np.float32)


def ridged(shape, wl_samples: float, seed: int) -> np.ndarray:
    from tools.newworld.terrain_relief import noise
    return 1 - 2 * np.abs(noise(shape, wl_samples, seed)) / 1.6


def thermal(h: np.ndarray, iters: int = 6, talus_deg: float = TALUS_DEG, keep_deg: float = CLIFF_KEEP_DEG,
            frozen: np.ndarray | None = None) -> np.ndarray:
    """Talus weathering: drops between neighbours steeper than the talus slope (and gentler than a cliff kept by
    design) shed a quarter of their excess downhill."""
    t = np.tan(np.radians(talus_deg)) * M
    kmax = np.tan(np.radians(keep_deg)) * M
    h = h.astype(np.float32).copy()
    for _ in range(iters):
        for ax in (0, 1):
            d = np.diff(h, axis=ax)
            ex = np.where((np.abs(d) > t) & (np.abs(d) < kmax), (np.abs(d) - t) * np.sign(d) * 0.25, 0)
            mv = np.zeros_like(h)
            if ax == 0:
                mv[:-1] += ex
                mv[1:] -= ex
            else:
                mv[:, :-1] += ex
                mv[:, 1:] -= ex
            if frozen is not None:
                mv[frozen] = 0
            h += mv
    return h


def weather(relief_m: np.ndarray, water_s: np.ndarray, F: dict, seed: int = 1952) -> np.ndarray:
    """The weathered natural ground (metres). F: the full-resolution region fields (floor, summit, rough, w_mesa)."""
    shape = relief_m.shape
    span = np.maximum(F["summit"] - F["floor"], 0)
    kfac = np.clip((span - 15.0) / 45.0, 0, 1)
    plateau = F["w_mesa"] * (ndi.gaussian_filter(relief_m, 2) - ndi.gaussian_filter(relief_m, 12) > -0.5)
    kfac = kfac * (1 - 0.8 * np.clip(plateau, 0, 1))
    hc = _down(relief_m, C)
    oc = _down(water_s.astype(np.float32), C) > 0
    oc[0, :] = oc[-1, :] = oc[:, 0] = oc[:, -1] = True
    hc = np.where(oc, 0.0, hc)
    kc = _down(kfac, C) * K0
    floorc = np.where(oc, 0.0, np.maximum(DRY_M, _down(F["floor"], C) * 0.3))
    floorc = np.minimum(floorc, hc)
    ec = stream_power(hc, oc, kc, floorc)
    # valleys, not trenches: the incision spread over two widths, so a valley's width and depth grow with its
    # drainage (a big channel's cut spreads wide and U-shaped, a rill's stays a shallow swale), capped by the relief
    cut = np.minimum(ec - hc, 0)
    cut = sum(m * ndi.gaussian_filter(cut, sg) for m, sg in zip(VALLEY_MIX, VALLEY_SIGMA))
    base = ndi.minimum_filter(hc, size=int(400 / (C * M)) | 1)
    cut = np.maximum(cut, -MAX_CUT_SHARE * np.maximum(hc - base, 0))
    # weighted by the full-resolution erodibility (a cubic resample of a near-zero field rings, and a hard mask of
    # it flips in drainage-grid blocks)
    out = relief_m + _up(cut, shape, C) * np.clip(kfac / 0.05, 0, 1)
    # detail: ridged fine relief on slopes, sized by the region's roughness
    gy, gx = np.gradient(ndi.gaussian_filter(out, 3), M)
    sl = np.clip(np.hypot(gx, gy) / 0.35, 0, 1)
    det = 0.6 * ridged(shape, 45 / M, seed + 11) + 0.4 * ridged(shape, 20 / M, seed + 12)
    out = out + (0.1 + 0.3 * kfac) * F["rough"] * sl * det
    out = thermal(out)
    # low ground (little relief span) keeps only a third of its fine relief under 15 m: marsh lies flat between
    # rarer, softer hummocks
    lw = np.clip(1 - kfac, 0, 1) * np.clip((40.0 - span) / 25.0, 0, 1)
    broad = ndi.gaussian_filter(out, 15 / M / 2)
    out = broad + (1 - 0.85 * lw) * (out - broad)
    # closed hollows on land filled to their spill height: ground drains to the water, marsh lies flat between
    # its hummocks (BM&V's marsh is flat ground about 1.7 m up, with few hollows)
    outlet = water_s.copy()
    outlet[0, :] = outlet[-1, :] = outlet[:, 0] = outlet[:, -1] = True
    seed = np.where(outlet, out, out.max() + 1.0)
    out = reconstruction(seed.astype(np.float32), out.astype(np.float32), method="erosion")
    return np.maximum(out, np.minimum(relief_m, DRY_M)).astype(np.float32)


def settle_places(relief_m: np.ndarray, centres_ij: list[tuple[float, float, str]], m: float = M) -> list[dict]:
    """Ease the ground around each large built place into a buildable core (see the module recipe). Mutates
    `relief_m`; returns what was done per place."""
    done = []
    for i0, j0, tier in centres_ij:
        r = BUILD_R_M.get(tier)
        if r is None:
            continue
        skirt = r
        rr = int((1.3 * r + skirt) / m) + 40
        a, b = max(0, int(i0) - rr), min(relief_m.shape[0], int(i0) + rr + 1)
        c, d = max(0, int(j0) - rr), min(relief_m.shape[1], int(j0) + rr + 1)
        win = relief_m[a:b, c:d].astype(np.float64)
        ii, jj = np.mgrid[a:b, c:d]
        dist = np.hypot(ii - i0, jj - j0) * m
        from tools.newworld.terrain_shape import wobble
        dist = dist / wobble(i0, j0, np.arctan2(ii - i0, jj - j0))   # an irregular core, not a circle
        broad = ndi.gaussian_filter(win, 60 / m / 2, mode="nearest")
        fine = win - broad
        keep = BUILD_KEEP
        for _ in range(12):
            cand = broad + keep * fine
            # the broad shape itself is flattened toward its mean until the core is under the slope limit
            gy, gx = np.gradient(cand, m)
            s = np.degrees(np.arctan(np.hypot(gx, gy)))[dist <= r]
            if s.size == 0 or np.percentile(s, 98) <= BUILD_MAX_SLOPE_DEG:
                break
            core_mean = broad[dist <= r].mean()
            broad = core_mean + 0.75 * (broad - core_mean)
            keep *= 0.85
        x = np.clip((dist - r) / skirt, 0, 1)
        w = 1 - x * x * x * (x * (6 * x - 15) + 10)
        relief_m[a:b, c:d] = (win * (1 - w) + cand * w).astype(np.float32)
        gy, gx = np.gradient(relief_m[a:b, c:d].astype(np.float64), m)
        s = np.degrees(np.arctan(np.hypot(gx, gy)))[dist <= r]
        done.append({"tier": tier, "radius_m": r, "slope_p98_deg": round(float(np.percentile(s, 98)), 2),
                     "relief_m": round(float(np.ptp(relief_m[a:b, c:d][dist <= r])), 2), "keep": round(keep, 3)})
    return done
