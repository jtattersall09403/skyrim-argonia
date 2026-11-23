"""The places build writes the plugin again only when what the writer reads changed (tools/places/build.py
write_key): a shard's plan, the items, the world file or the tool itself; a heavy-lock wait is counted."""
from pathlib import Path

from tools.places import build, heavy_lock


def test_write_key_follows_every_input(tmp_path, monkeypatch):
    tool = tmp_path / "tool.dll"
    tool.write_bytes(b"tool v1")
    monkeypatch.setattr(build, "TOOL", tool)
    esp = tmp_path / "plugin" / "X.esp"
    esp.parent.mkdir()
    (esp.parent / "items.json").write_text("[]")
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text('{"refs": [1]}')
    b.write_text('{"refs": [2]}')
    k0 = build.write_key(esp, [str(a), str(b)], "w1")
    assert build.write_key(esp, [str(a), str(b)], "w1") == k0                  # nothing changed: the same key
    a.write_text('{"refs": [1, 3]}')
    k1 = build.write_key(esp, [str(a), str(b)], "w1")
    assert k1 != k0                                                              # a plan changed
    assert build.write_key(esp, [str(a), str(b)], "w2") != k1                   # the world file changed
    assert build.write_key(esp, [str(a)], "w1") != k1                           # a shard went
    (esp.parent / "items.json").write_text("[1]")
    k2 = build.write_key(esp, [str(a), str(b)], "w1")
    assert k2 != k1                                                              # the items changed
    tool.write_bytes(b"tool v2")
    assert build.write_key(esp, [str(a), str(b)], "w1") != k2                   # the tool changed
    (tmp_path / "other").mkdir()
    (tmp_path / "other" / "items.json").write_text("[1]")
    k3 = build.write_key(esp, [str(a), str(b)], "w1")
    assert build.write_key(tmp_path / "other" / "X.esp", [str(a), str(b)], "w1") != k3   # another plugin path


def test_a_lock_wait_is_counted(tmp_path, monkeypatch):
    import fcntl
    import os
    import threading
    monkeypatch.setenv("ARGONIA_PLACES_LOCK_FILE", str(tmp_path / "lock"))
    monkeypatch.delenv("ARGONIA_PLACES_NO_LOCK", raising=False)
    fd = os.open(tmp_path / "lock", os.O_RDWR | os.O_CREAT)
    fcntl.flock(fd, fcntl.LOCK_EX)
    threading.Timer(0.4, lambda: os.close(fd)).start()
    was = heavy_lock.WAITED
    with heavy_lock.heavy_lock():
        pass
    assert heavy_lock.WAITED - was >= 0.3
