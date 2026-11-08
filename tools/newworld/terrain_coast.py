"""The shoreline: the map's water mask (one pixel every 204.8 units, 2.93 m) turned into a smooth signed distance on
the heightmap's samples, so coasts and banks are natural curves rather than pixel staircases.

The recipe:
1. Signed distance at every map pixel centre, in pixels: positive on land, negative on water, the shore half way
   between a land and a water pixel (sd = +/- (EDT - 0.5)). Read between pixel centres it is already the sub-pixel
   contour (a staircase becomes its diagonal).
2. Smoothed: a Gaussian of 0.9 px everywhere; a Gaussian of 3.5 px where the mask has a straight axis-aligned run
   (a boundary straight for 7 px or more, the map's square notches and cell-aligned edges), faded in over 3 px.
3. Thin features kept: water or land narrower than 5 px (one- and two-pixel streams, spits, islets) keeps the raw
   distance less 0.3 px on its own side, so no stream is cut and no diagonal stream pinches at a corner.
4. Small-scale irregularity: fine noise (23 m and 9 m) added to the distance, and the field read at a domain-warped
   position (12 px wavelength), each scaled down near thin features, so a coast wanders by a metre or two between
   the map's pixels while its map-scale shape holds.
5. Read bilinearly at every sample (off the map: sea), in metres. Water is sd < 0.

`agreement` reports how far the samples' water follows the map: per pixel, and on 4 x 4 pixel blocks (majority).
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

M_PER_PX = 204.8 / 70.0
SIGMA_PX = 0.9
SIGMA_STRAIGHT_PX = 3.5
RUN_PX = 7
NOISE = ((8.0, 0.35), (3.0, 0.15))      # (wavelength px, amplitude px)
WARP = (12.0, 0.6)                     # (wavelength px, amplitude px)


def _noise(shape, wl, seed):
    from tools.newworld.terrain_relief import noise
    return noise(shape, wl, seed)


def straight_runs(water: np.ndarray, run: int = RUN_PX) -> np.ndarray:
    """Pixels on a boundary that is straight and axis-aligned for at least `run` px."""
    w = water.astype(np.int8)
    out = np.zeros(water.shape, bool)
    eh = (w[1:] != w[:-1]).astype(np.float32)            # edges between rows
    sh = ndi.uniform_filter1d(eh, run, axis=1) > 0.999
    out[1:] |= sh
    out[:-1] |= sh
    ev = (w[:, 1:] != w[:, :-1]).astype(np.float32)
    sv = ndi.uniform_filter1d(ev, run, axis=0) > 0.999
    out[:, 1:] |= sv
    out[:, :-1] |= sv
    return out


def signed_distance(water: np.ndarray, seed: int = 1952) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The smoothed signed distance at map pixel centres (px), the thin-feature weight (0..1), and the thin pixels
    (int8: -1 thin water, +1 thin land, 0 neither), which `sample` forces so no stream is cut."""
    sd = np.where(water, -(ndi.distance_transform_edt(water) - 0.5),
                  ndi.distance_transform_edt(~water) - 0.5).astype(np.float32)
    st = ndi.gaussian_filter(ndi.binary_dilation(straight_runs(water), iterations=3).astype(np.float32), 1.5)
    st = np.clip(st * 2.0, 0, 1)
    fine = ndi.gaussian_filter(sd, SIGMA_PX)
    broad = ndi.gaussian_filter(sd, SIGMA_STRAIGHT_PX)
    s = (1 - st) * fine + st * broad
    # thin = narrow: the widest inscribed distance within 2 px is under 2.5 px (a feature under 5 px across); a big
    # body's convex corner is not thin, so it is rounded like any other shore
    thin_w = water & (ndi.maximum_filter(np.where(water, -sd, 0), size=5) < 2.0)
    thin_l = ~water & (ndi.maximum_filter(np.where(water, 0, sd), size=5) < 2.0)
    near_w = ndi.binary_dilation(thin_w)
    near_l = ndi.binary_dilation(thin_l)
    near = (near_w | near_l).astype(np.float32)
    thin = np.maximum(near, np.clip(ndi.gaussian_filter(near, 2.0) * 3, 0, 1))
    free = 1 - thin
    for n, (wl, amp) in enumerate(NOISE):
        s += free * amp * _noise(water.shape, wl, seed + 50 + n)
    # thin features clamped last, so neither smoothing nor noise cuts a stream or drowns a spit
    s = np.where(near_w, np.minimum(s, sd - 0.3), s)
    s = np.where(near_l, np.maximum(s, sd + 0.3), s)
    force = np.where(thin_w, -1, np.where(thin_l, 1, 0)).astype(np.int8)
    return s.astype(np.float32), thin.astype(np.float32), force


def sample(sd_px: np.ndarray, thin: np.ndarray, grid, seed: int = 1952, band: int = 256,
           force: np.ndarray | None = None) -> np.ndarray:
    """The signed distance (metres) at every sample of `grid` (terrain_shape.Grid), domain-warped; off the map: sea.
    A sample whose nearest map pixel is thin water (force -1) reads water, thin land (+1) land: the blur and the warp
    never cut a stream or drown a spit."""
    H, W = sd_px.shape
    out = np.empty((grid.rows, grid.cols), np.float32)
    wl = WARP[0] / grid.k
    wi = _noise((grid.rows, grid.cols), wl, seed + 60)
    wj = _noise((grid.rows, grid.cols), wl, seed + 61)
    pad = 8
    big = np.pad(sd_px, pad, mode="constant", constant_values=-pad)
    tpad = np.pad(thin, pad, mode="constant", constant_values=0)
    jx = grid.p0x + np.arange(grid.cols) * grid.k - 0.5 + pad
    for i0 in range(0, grid.rows, band):
        rows = np.arange(i0, min(grid.rows, i0 + band))
        iy = grid.p0y + rows * grid.k - 0.5 + pad
        I, J = np.meshgrid(iy, jx, indexing="ij")
        th = ndi.map_coordinates(tpad, [I, J], order=1, mode="nearest")
        amp = WARP[1] * (1 - th)
        I2, J2 = I + amp * wi[rows], J + amp * wj[rows]
        v = ndi.map_coordinates(big, [I2, J2], order=1, mode="nearest")
        outside = (I2 < pad - 0.5) | (J2 < pad - 0.5) | (I2 > H + pad - 0.5) | (J2 > W + pad - 0.5)
        v[outside] = np.minimum(v[outside], -1.0)
        if force is not None:
            fy = np.clip(np.floor(I - pad + 0.5).astype(int), 0, H - 1)
            fx = np.clip(np.floor(J - pad + 0.5).astype(int), 0, W - 1)
            fc = force[fy, fx]
            v = np.where(fc < 0, np.minimum(v, -0.15), np.where(fc > 0, np.maximum(v, 0.15), v))
        out[rows] = v * M_PER_PX
    return out


def agreement(water_samples: np.ndarray, grid, water: np.ndarray) -> dict:
    """How the samples' water matches the map: at pixel centres (nearest sample), and on 4 x 4 pixel blocks."""
    H, W = water.shape
    py, px = np.mgrid[0:H, 0:W].astype(np.float32) + 0.5
    i = np.round((py - grid.p0y) / grid.k).astype(int)
    j = np.round((px - grid.p0x) / grid.k).astype(int)
    ok = (i >= 0) & (j >= 0) & (i < grid.rows) & (j < grid.cols)
    got = np.zeros(water.shape, bool)
    got[ok] = water_samples[i[ok], j[ok]]
    px_ok = float((got == water)[ok].mean())
    edge = ok & (ndi.binary_dilation(water) & ndi.binary_dilation(~water))
    r, c = (H // 4) * 4, (W // 4) * 4

    def blocks(a):
        return a[:r, :c].reshape(r // 4, 4, c // 4, 4).mean((1, 3))
    okb = blocks(ok.astype(np.float32)) == 1
    bw, bg = blocks(water.astype(np.float32)), blocks(got.astype(np.float32))
    decided = okb & (np.abs(bw - 0.5) > 0.2)
    return {"px": round(px_ok, 5), "shore_px": round(float((got == water)[edge].mean()), 4),
            "blocks4": round(float(((bw > 0.5) == (bg > 0.5))[decided].mean()), 5),
            "water_px_kept": round(float(got[ok & water].mean()), 5),
            "land_px_kept": round(float(1 - got[ok & ~water].mean()), 5),
            "bodies_split": bodies_split(water_samples, i, j, ok, water)}


def bodies_split(water_samples: np.ndarray, i, j, ok, water: np.ndarray) -> int:
    """Map water bodies (8-connected) whose samples fall into more than one 4-connected sample body: cut streams."""
    lab_m, n = ndi.label(water, np.ones((3, 3), bool))
    lab_s, _ = ndi.label(water_samples)
    sel = ok & water
    ls = lab_s[i[sel], j[sel]]
    lm = lab_m[sel]
    keep = ls > 0
    pairs = np.unique(np.stack([lm[keep], ls[keep]], 1), axis=0)
    per = np.bincount(pairs[:, 0], minlength=n + 1)
    return int((per > 1).sum())


def repair(sd_m: np.ndarray, grid, water: np.ndarray, rounds: int = 3) -> int:
    """Rejoin cut bodies: for every map body whose samples split where the nearest-pixel sampling did not, the
    nearest-pixel water is restored on that body's land samples (its banks take the map's pixel line again, so the
    neck is open). Mutates sd_m; returns the bodies repaired."""
    from tools.newworld.terrain_shape import sample_classes
    old = sample_classes(grid, water)
    H, W = water.shape
    py, px = np.mgrid[0:H, 0:W].astype(np.float32) + 0.5
    i = np.round((py - grid.p0y) / grid.k).astype(int)
    j = np.round((px - grid.p0x) / grid.k).astype(int)
    ok = (i >= 0) & (j >= 0) & (i < grid.rows) & (j < grid.cols)
    lab_m, n = ndi.label(water, np.ones((3, 3), bool))
    sel = ok & water
    body_of_sample = np.zeros(sd_m.shape, np.int32)
    body_of_sample[i[sel], j[sel]] = lab_m[sel]

    def split_bodies(ws):
        lab_s, _ = ndi.label(ws)
        ls, lm = lab_s[i[sel], j[sel]], lab_m[sel]
        keep = ls > 0
        pairs = np.unique(np.stack([lm[keep], ls[keep]], 1), axis=0)
        return np.bincount(pairs[:, 0], minlength=n + 1) > 1

    base = split_bodies(old)
    fixed = np.zeros(n + 1, bool)
    for _ in range(rounds):
        bad = split_bodies(sd_m < 0) & ~base
        if not bad.any():
            break
        fixed |= bad
        # the body's own samples and their neighbours (a neck's land samples carry no body label)
        zone = ndi.binary_dilation(bad[body_of_sample], iterations=2)
        put = zone & old & (sd_m >= 0)
        sd_m[put] = -0.15 * M_PER_PX
    return int(fixed.sum())
