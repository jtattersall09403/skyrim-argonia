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
    return M.Material(src, M.OldWater(None, None, PAD), M.Regions.uniform(eco, PAD, N), roads=False)


def test_texture_set_is_bmv_and_never_nordic():
    for t in M.TEXTURES:
        assert t.bmv.startswith("TEXTUREPACK\\landscape\\") and t.form_key.endswith(":Skyrim.esm")
        assert not any(k in t.edid.lower() for k in ("snow", "glacier", "ice", "volcanic"))
    for c, stops in M.STOPS.items():
        assert 4 <= len({s.ltex for s in stops}) <= 6, c
        assert all(s.ltex in M.TEX and s.why for s in stops), c


def test_water_gradient_runs_bed_edge_land():
    src = sources(shore())
    win = mat(src).window(PAD, PAD + N + 1, PAD, PAD + N + 1)
    row = win.weights[N // 2]
    dom = [M.TEXTURES[i].edid for i in row.argmax(axis=1)]
    first = {e: dom.index(e) for e in dict.fromkeys(dom)}
    assert first["LRiverBottom01"] < first["LRiverbedEdge01"] < first["LPineForest03"]
    assert "LRiverMud01" in first  # the exposed wet mud between


def test_blend_spans_many_vertices_never_one():
    src = sources(shore())
    w = mat(src).window(PAD, PAD + N + 1, PAD, PAD + N + 1).weights
    step = max(np.abs(np.diff(w, axis=0)).max(), np.abs(np.diff(w, axis=1)).max())
    assert step < 0.35  # a one-vertex blend jumps by ~1


def test_class_border_blends():
    src = sources(np.full((N + 1, N + 1), 10.0))
    reg = M.Regions.uniform("flooded-forest", PAD, N)
    reg.grid[:, 2:] = M.CLASSES.index("northern-transition")
    m = M.Material(src, M.OldWater(None, None, PAD), reg, roads=False)
    w = m.window(PAD, PAD + N + 1, PAD, PAD + N + 1).weights
    assert np.abs(np.diff(w, axis=1)).max() < 0.2


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
        if (x + 1, y) in cells:  # this cell's BottomRight east edge = the neighbour's BottomLeft west edge
            assert np.abs(comp(c, 1)[:, -1] - comp(cells[(x + 1, y)], 0)[:, 0]).max() < 0.03


def test_noise_is_position_seeded():
    a = M.value_noise(100, 140, 200, 260, 48, 1)
    b = M.value_noise(110, 140, 230, 260, 48, 1)
    assert np.array_equal(a[10:, 30:], b)
