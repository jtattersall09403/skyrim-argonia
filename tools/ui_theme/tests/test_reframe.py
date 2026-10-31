"""retheme.reframe (1.9): a frame painted into a sheet bitmap is replaced by the sheet's own margins and our line."""
import numpy as np

from tools.ui_theme import retheme


def sheet():
    rng = np.random.default_rng(1)
    rgba = np.zeros((720, 1280, 4), np.uint8)
    rgba[..., :3] = (226, 200, 150) + rng.integers(-6, 6, (720, 1280, 1))
    rgba[..., 3] = 255
    rgba[119:486, 298:980, 3] = 0           # the picture window
    rgba[40:100, 500:800, :3] = (60, 60, 60)  # a crest
    rgba[500:550, 260:300, :3] = (60, 60, 60)  # a corner knot
    return rgba


def test_the_ornaments_go_and_the_window_stays():
    before = sheet()
    after = retheme.reframe(before, (250, 25, 1035, 565))
    assert after[40:100, 500:800, :3].min() > 120      # crest gone (it was 60; parchment blue is ~150)
    assert after[500:550, 260:300, :3].min() > 120     # knot gone
    assert (after[119:486, 298:980, 3] == 0).all()     # window kept, still transparent
    assert (after[600:, :] == before[600:, :]).all()   # outside the ring untouched


def test_our_line_is_drawn_around_the_window():
    after = retheme.reframe(sheet(), (250, 25, 1035, 565))
    assert after[109, 640, :3].mean() < after[60, 640, :3].mean() - 20  # the ink line 10 px above the window
