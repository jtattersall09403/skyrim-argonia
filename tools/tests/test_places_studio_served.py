"""tools/places/studio/served.py: the studio levels its tree before serving, says which place is behind when it cannot,
and restarts for landed code only when nothing of the owner's is in flight."""
import asyncio
import time

from tools.places.studio import served


class Cfg:
    level = True


def app_with(res):
    app = {"cfg": Cfg(), "commit_q": asyncio.Queue(), "pending": {}, "finalising": {}, "draft_locks": {}}
    served.setup(app)
    calls = []
    served.run_level = lambda root=served.ROOT: calls.append(1) or res
    return app, calls


def test_ensure_levels_at_most_once_a_throttle_and_names_the_places_behind(monkeypatch):
    orig = served.run_level
    try:
        app, calls = app_with({"code": 1, "places_behind": ["helstrom"]})
        asyncio.run(served.ensure(app))
        asyncio.run(served.ensure(app))
        assert len(calls) == 1 and served.places_behind(app) == {"helstrom"}
        asyncio.run(served.ensure(app, force=True))
        assert len(calls) == 2
        app["served"]["res"] = {"code": 0, "places_behind": ["helstrom"]}   # levelled: nothing is behind
        assert served.places_behind(app) == set()
        assert "Your saves and unsaved work are safe" in served.behind_message("Helstrom")
    finally:
        served.run_level = orig


def test_a_restart_waits_for_every_write_of_the_owners():
    app, _ = app_with({"code": 0})
    assert served.idle(app) is None
    app["served"]["inflight"] = 1
    assert served.idle(app) == "a request is in flight"
    app["served"]["inflight"] = 0
    app["commit_q"].put_nowait(("x", "m"))
    assert served.idle(app) == "a save waits to be committed"
    app["commit_q"].get_nowait()
    app["served"]["last_write"] = time.time()
    assert "last minute" in served.idle(app)
    app["served"]["last_write"] = 0
    app["draft_locks"]["p"] = type("L", (), {"locked": lambda self: True})()
    assert served.idle(app) == "a draft is being rebuilt"


def test_a_changed_module_file_is_seen(tmp_path, monkeypatch):
    f = tmp_path / "m.py"
    f.write_text("x = 1\n")
    snap = {str(f): __import__("hashlib").sha256(f.read_bytes()).hexdigest()}
    assert served.code_changed(snap) == []
    f.write_text("x = 2\n")
    assert served.code_changed(snap) == [str(f)]
    monkeypatch.delenv("INVOCATION_ID", raising=False)
    assert served.restart() is False   # never outside systemd
