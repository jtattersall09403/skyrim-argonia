"""PathIndex.within answers as dist_to_paths does (tools/places/draft/paths.py), for every point and every distance up
to its reach: the draft check's street tests over thousands of world plants read only the streets near each."""
import random

from tools.places.draft.paths import PathIndex, dist_to_paths


def test_within_is_dist_to_paths():
    rnd = random.Random(11)
    paths = []
    for _ in range(12):
        x, y = rnd.uniform(0, 8000), rnd.uniform(0, 8000)
        pts = [(x, y)]
        for _ in range(rnd.randint(1, 6)):
            x, y = x + rnd.uniform(-900, 900), y + rnd.uniform(-900, 900)
            pts.append((x, y))
        row = {"points": pts}
        if rnd.random() < 0.5:
            row["width"] = rnd.choice([96.0, 192.0, 384.0])
        paths.append(row)
    idx = PathIndex(paths, 300.0)
    hits = 0
    for _ in range(4000):
        p = (rnd.uniform(-500, 8500), rnd.uniform(-500, 8500))
        for d in (0.0, 40.0, 300.0):
            want = dist_to_paths(p, paths) <= d
            assert idx.within(p, d) == want
            hits += want
    assert hits > 100
