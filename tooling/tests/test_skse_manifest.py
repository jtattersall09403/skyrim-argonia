import importlib.util, os, pathlib

spec = importlib.util.spec_from_file_location('skse_manifest', pathlib.Path(__file__).parents[2] / 'infra/gpu-box/skse_manifest.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def put(tree, rel, text, t):
    p = tree / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text); os.utime(p, (t, t))


def test_touch_only_changed_new_and_save_drops_deleted(tmp_path):
    tree, man = tmp_path / 't', str(tmp_path / 'man')
    put(tree, 'a.cpp', 'a', 1000); put(tree, 'b.cpp', 'b', 1000)
    files = ['a.cpp', 'b.cpp']
    assert sorted(m.touch(str(tree), files, man, now=5000)) == files   # no manifest: all new
    m.save(str(tree), files, man)
    os.utime(tree / 'b.cpp', (1000, 1000))
    put(tree, 'a.cpp', 'a // comment', 1000)       # edited, but with an old time (the bug)
    put(tree, 'c.cpp', 'c', 1000)                  # new
    files = ['a.cpp', 'b.cpp', 'c.cpp']
    assert sorted(m.touch(str(tree), files, man, now=5000)) == ['a.cpp', 'c.cpp']
    assert (tree / 'a.cpp').stat().st_mtime == 5000 and (tree / 'c.cpp').stat().st_mtime == 5000
    assert (tree / 'b.cpp').stat().st_mtime == 1000   # unchanged keeps its time
    # a failed build never saves: the edit is still pending
    assert 'a.cpp' in m.changed(str(tree), files, man)
    m.save(str(tree), files, man)
    assert m.changed(str(tree), files, man) == []
    m.save(str(tree), ['a.cpp'], man)              # b and c deleted
    assert set(m.load(man)) == {'a.cpp'}
