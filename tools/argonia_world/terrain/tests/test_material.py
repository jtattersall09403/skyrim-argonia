"""L2: the material gradient on synthetic cells (1.15 §c): layer count, blend width, the seam fix, the water
gradient, and the texture set's own rules."""
import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain import build, material as M
from tools.argonia_world.terrain.grid import Sources

N, PAD = 4 * 32, 32


def sources(ground):
    return Sources(ground=ground.astype(np.float32), apron=np.full((N + 1 + 2 * PAD,) * 2, -10.0, np.float32),
                   cover=np.zeros((N + 1,) * 2, np.int16), tint=None, pad=PAD)


def shore():
    """A ramp from 6 m under the sea (west) to 40 m (east), with a steep bank in the east."""
    xx = np.mgrid[0:N + 1, 0:N + 1][1].astype(np.float32)
    g = -6.0 + xx * 0.25
    g[:, 100:] += (xx[:, 100:] - 100) * 1.5
    return g


def mat(src, eco="flooded-forest"):
    return M.Material(src, M.Water.sea(PAD, N), M.Regions.uniform(eco, PAD, N), roads=False)


def test_texture_set_is_bmv_and_never_nordic():
    for t in M.TEXTURES:
        assert t.bmv.startswith("TEXTUREPACK\\landscape\\") and t.form_key.endswith(":Skyrim.esm")
        assert not any(k in t.edid.lower() for k in ("snow", "glacier", "ice", "volcanic"))
    for c, stops in M.STOPS.items():
        land = {s.ltex for s in stops} - {M.BED.ltex, M.MUD.ltex, M.EDGE.ltex}  # the water family is shared
        assert (2 if c == "border" else 2) <= len(land) <= 6, c  # the apron is bare (audit §9)
        assert all(s.ltex in M.TEX and s.why for s in stops), c


def test_water_gradient_runs_bed_edge_land():
    src = sources(shore())
    win = mat(src).window(PAD, PAD + N + 1, PAD, PAD + N + 1)
    row = win.weights[N // 2]
    dom = [M.TEXTURES[i].edid for i in row.argmax(axis=1)]
    first = {e: dom.index(e) for e in dict.fromkeys(dom)}
    assert first["LRiverBottom01"] < first["LRiverbedEdge01"] < first["LPineForest03"]
    # vanilla's sequence (audit §4): the edge carries on to +128 u above the line, and no mud lies above the water
    i, e = (M.TEXTURES.index(M.TEX[t]) for t in ("LRiverMud01", "LRiverbedEdge01"))
    dh = win.dh[N // 2]
    assert row[(dh > 0.3) & (dh < M.EDGE_TOP_M - 0.3), e].min() > 0.5
    assert row[dh > 0.3, i].max() < 0.1
    assert row[dh > M.EDGE_TOP_M + 0.4, e].max() < 0.1


def test_blends_are_vanilla_brush_widths():
    """Skyrim.esm's blends run 1 vertex at p50 and 5 at p90 (audit §4); ours ran 6-17."""
    src = sources(shore())
    runs = M.blend_runs(mat(src).window(PAD, PAD + N + 1, PAD, PAD + N + 1).weights)
    assert len(runs) and np.percentile(runs, 50) <= 2 and np.percentile(runs, 90) <= 5


def test_class_border_blends():
    src = sources(np.full((N + 1, N + 1), 10.0))
    reg = M.Regions.uniform("flooded-forest", PAD, N)
    reg.grid[:, 2:] = M.CLASSES.index("northern-transition")
    m = M.Material(src, M.Water.sea(PAD, N), reg, roads=False)
    w = m.window(PAD, PAD + N + 1, PAD, PAD + N + 1).weights
    runs = M.blend_runs(w)
    assert len(runs) and np.percentile(runs, 90) <= 5  # blended where classes change, over a few vertices (audit §4)


def test_seam_fix_and_layer_count():
    rng = np.random.default_rng(3)
    w = rng.random((2 * M.QS + 1, 2 * M.QS + 1, 12)) ** 6  # many textures: drop-outs must happen
    w /= w.sum(axis=2, keepdims=True)
    wr, keep = M.quadrant_sets(w)
    assert all(len(k) <= M.MAX_ALPHA + 1 for row in keep for k in row)
    comp = {}
    for i in range(2):
        for j in range(2):
            q = wr[i * M.QS:i * M.QS + M.QV, j * M.QS:j * M.QS + M.QV]
            base, layers = M.quadrant_layers(q, keep[i][j])
            assert len(layers) <= su.LAND_QUADRANT_LAYERS
            comp[i, j] = M.composite(base, layers, 12)
    # the shared edges composite the same weights on both sides (to the byte rounding)
    assert np.abs(comp[0, 0][:, -1] - comp[0, 1][:, 0]).max() < 0.03
    assert np.abs(comp[0, 0][-1] - comp[1, 0][0]).max() < 0.03


def test_build_writes_at_most_six_layers_and_matching_seams(tmp_path):
    src = sources(shore())
    st = build.build(src, None, tmp_path, cells=(-63, -63, -60, -60))
    assert max(st.layers_hist) <= M.MAX_ALPHA
    n = len(M.TEXTURES)
    cells = {(c["x"], c["y"]): c for c in build.read_cells(tmp_path)}
    fk = {t.form_key: i for i, t in enumerate(M.TEXTURES)}

    def comp(c, q):
        qd = c["quads"][q]
        import base64
        layers = [(fk[l["ltex"]], np.frombuffer(base64.b64decode(l["alpha"]), np.uint8).reshape(17, 17))
                  for l in qd["layers"]]
        return M.composite(fk[qd["base"]], layers, n)
    for (x, y), c in cells.items():
        # this cell's BottomRight east edge = the neighbour's BottomLeft west edge; the apron's bare quadrants (base
        # alone, audit §9) meet edge to edge as vanilla's far ground does
        if (x + 1, y) in cells and src.in_province(x, y) and src.in_province(x + 1, y):
            assert np.abs(comp(c, 1)[:, -1] - comp(cells[(x + 1, y)], 0)[:, 0]).max() < 0.03


def test_noise_is_position_seeded():
    a = M.value_noise(100, 140, 200, 260, 48, 1)
    b = M.value_noise(110, 140, 230, 260, 48, 1)
    assert np.array_equal(a[10:, 30:], b)


def test_material_gradient_table_matches_the_stops():
    from tools.argonia_world import db
    cols = ("eco_class_id", "stop", "ltex_form_key", "dh_lo", "dh_hi", "slope_lo", "slope_hi", "wet_lo", "wet_hi",
            "noise_lo", "noise_hi", "weight", "north", "why")
    rows = sorted(tuple(r) for r in db.open().query(f"SELECT {', '.join(cols)} FROM material_gradient"))
    want = sorted(tuple(r[c] for c in cols) for r in M.gradient_rows())
    assert rows == want  # run `terrain gradient` after a STOPS edit


def test_nearest_wet_level_and_distance():
    lev = np.full((40, 50), np.nan, np.float32)
    lev[5, 5], lev[30, 45] = 1.0, 3.0
    near, d = M.nearest_wet(lev)
    yy, xx = np.mgrid[0:40, 0:50]
    d1, d2 = np.hypot(yy - 5, xx - 5), np.hypot(yy - 30, xx - 45)
    assert np.allclose(d, np.minimum(d1, d2), atol=1e-4)
    assert (near[d1 < d2 - 0.5] == 1.0).all() and (near[d2 < d1 - 0.5] == 3.0).all()


def test_vclr_draws_no_ring_at_the_waterline():
    """The wet darkening falls monotonically from the water outward: no darker line on the shore than in it."""
    n = 64
    wet = np.clip(1.0 - np.arange(n) / 30.0, 0, 1)[None, :].repeat(8, 0).astype(np.float32)
    dh = (np.arange(n) - 20.0)[None, :].repeat(8, 0).astype(np.float32) * 0.2
    z = np.zeros_like(wet)
    d = np.clip(np.arange(n) - 20.0, 0, None)[None, :].repeat(8, 0).astype(np.float32)
    v = M.vclr(M.Window(np.zeros(wet.shape + (1,)), dh, z, z, wet, d))[..., 0].astype(int)
    assert (np.diff(v[0]) >= 0).all()
    assert v[0, 20] < 160 and (v[0, 27:] == 255).all()  # dark at the line, white 7 vertices out (fitted to §4)


def test_steep_ground_is_not_darker():
    """Vanilla's steep ground is not darker (audit §4: p10 198 against 165 flat): no slope or aspect shade."""
    s = np.full((4, 4), 60.0, np.float32)
    far = np.full((4, 4), 99.0, np.float32)
    v = M.vclr(M.Window(np.zeros((4, 4, 1)), far, s, np.ones_like(s), np.zeros_like(s), far))
    assert (v[..., 0] == 255).all()


def test_apron_is_bare():
    """Beyond the border polygon: the border class alone and one base texture per quadrant (audit §9)."""
    src = sources(shore())
    m = mat(src)
    w = m.window(0, 2 * M.QS + 1, 0, 2 * M.QS + 1).weights
    _, keep = M.quadrant_sets(w, bare=m.apron(0, 2 * M.QS + 1, 0, 2 * M.QS + 1))
    assert all(len(k) == 1 for row in keep for k in row)


def test_rain_lifts_dry_ground_wetness():
    m = mat(sources(shore()))
    box = (PAD, PAD + N + 1, PAD, PAD + N + 1)
    dry = m.window(*box).wet[:, 110:].mean()
    m.water.rain[:] = 1.0
    assert m.window(*box).wet[:, 110:].mean() > dry + 0.1


def test_open_shallow_bed_takes_the_bed_not_mud():
    """Mud and the edge lie only in the band under the edge; a wide shallow bed is the bed texture (r1 mud blobs)."""
    g = np.full((N + 1, N + 1), -2.0, np.float32)  # 2 m deep: above -384 u, so by depth alone all mud and edge
    g[:, :20] = 3.0
    win = mat(sources(g)).window(PAD, PAD + N + 1, PAD, PAD + N + 1)
    dom = win.weights.argmax(axis=2)
    bed, sea, mud = (M.TEXTURES.index(M.TEX[t]) for t in ("LRiverBottom01", "LCoastOceanFloor01", "LRiverMud01"))
    assert np.isin(dom[:, 40:], (bed, sea)).mean() > 0.95  # the synthetic rim's warped border class is sea floor
    assert (dom[:, 40:] == mud).sum() == 0


def test_steep_ground_is_rock_in_patches_not_a_swathe():
    """Skyrim.esm: rock dominates ~25 % of slopes over 34° (options §8): ours is patches, not the whole face."""
    xx = np.mgrid[0:N + 1, 0:N + 1][1].astype(np.float32)
    g = 20.0 + xx * 1.6  # ~42° everywhere
    w = M.Material(sources(g), M.Water.sea(PAD, N), M.Regions.uniform("western-frontier", PAD, N), roads=False)
    dom = w.window(PAD, PAD + N + 1, PAD, PAD + N + 1).weights.argmax(axis=2)
    rocks = [M.TEXTURES.index(M.TEX[t]) for t in ("LReachMossyRocks01", "LRocks01", "LTundraRocks01")]
    share = np.isin(dom, rocks).mean()
    assert 0.1 < share < 0.6, share
    assert len(np.unique(dom)) >= 2


def test_render_draws_the_quadrant_bases_the_build_writes():
    src = sources(shore())
    m = mat(src)
    w = M.built_weights(m, 3, 2 * M.QS + 3, 0, 2 * M.QS)  # not on a quadrant corner: widened and cut back
    assert w.shape[:2] == (2 * M.QS, 2 * M.QS)
    assert ((w > 0).sum(axis=2) == 1).all()  # the apron's quadrants: one base, no blend


def _longest_seam_on_cell_lines(dom, pad):
    """The longest run of vertices along any cell line (index - pad = 32k) where the dominant texture changes
    across it."""
    best = 0
    for f in (dom, dom.T):
        for i in range(1, f.shape[0] - 1):
            if (i - pad) % su.QUADS_PER_CELL:
                continue
            d = (f[i - 1] != f[i]) | (f[i] != f[i + 1])
            p = np.diff(np.r_[0, d.astype(int), 0])
            best = max(best, int((np.nonzero(p == -1)[0] - np.nonzero(p == 1)[0]).max(initial=0)))
    return best


def test_no_texture_boundary_runs_along_a_cell_edge():
    """Ground piecewise linear between samples 16 vertices apart (as the source is) steps the raw slope along
    straight lines; the slope keys read it smoothed, so no zone boundary follows a cell edge (-38_25, 2026-11-01)."""
    yy, xx = np.mgrid[0:N + 1, 0:N + 1].astype(np.float32)
    k = np.sin(xx[::16, ::16] / 9.0) * np.cos(yy[::16, ::16] / 7.0) * 18 + 30  # coarse samples
    i, f = np.divmod(np.arange(N + 1), 16)
    i1 = np.minimum(i + 1, k.shape[0] - 1)
    t = (f / 16.0)
    rows = k[i] * (1 - t)[:, None] + k[i1] * t[:, None]
    g = rows[:, i] * (1 - t)[None, :] + rows[:, i1] * t[None, :]
    win = mat(sources(g), "western-frontier").window(PAD, PAD + N + 1, PAD, PAD + N + 1)
    assert _longest_seam_on_cell_lines(win.weights.argmax(axis=2), 0) <= 8


def test_flooded_forest_floor_is_patches_not_a_swathe():
    yy, xx = np.mgrid[0:N + 1, 0:N + 1].astype(np.float32)
    g = 4.0 + 0.5 * np.sin(xx / 11.0) * np.cos(yy / 13.0)  # a low wooded flat
    dom = mat(sources(g)).window(PAD, PAD + N + 1, PAD, PAD + N + 1).weights.argmax(axis=2)
    _, n = np.unique(dom, return_counts=True)
    assert len(n) >= 4 and n.max() / n.sum() <= 0.5, n


def test_dry_ground_is_never_a_bed():
    """A dry hollow below a nearby water's level takes land, not the riverbed (-38_25, 2026-11-01)."""
    src = sources(np.full((N + 1, N + 1), 5.0, np.float32))
    water = M.Water(np.zeros((4, 4)), np.full((4, 4), 20.0), PAD)
    win = M.Material(src, water, M.Regions.uniform("flooded-forest", PAD, N), roads=False).window(
        PAD, PAD + N + 1, PAD, PAD + N + 1)
    assert (win.dh >= 0).all()


def test_dry_ground_with_no_water_in_reach_is_land():
    """Ground at 36 m, 'near' level 35 m read through the raster, no cell carrying a level in the window: no
    bed/edge/mud band (0_0_1_1, 2026-11-01)."""
    src = sources(np.full((N + 1, N + 1), 36.0, np.float32))
    water = M.Water(np.full((4, 4), np.nan), np.full((4, 4), 35.0), PAD)
    win = M.Material(src, water, M.Regions.uniform("flooded-forest", PAD, N), roads=False).window(
        PAD, PAD + N + 1, PAD, PAD + N + 1)
    assert (win.dh >= M.FAR_DH).all()
