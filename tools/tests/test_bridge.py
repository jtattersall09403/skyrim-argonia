"""L2: tools/bridge.py against a fake plugin on a local socket and a fake machine (0.3 §a). The fail-on-purpose
cases: a refusal raises BridgeError, a closed connection with a dead game raises GameDown, a crash log seen
while a call waits raises GameDown within one health interval, a stale token is refreshed once."""
import json
import socket
import threading
import time

import pytest

from tools import bridge as B


class FakeMachine:
    def __init__(self, token="t" * 32, alive=True, crash=""):
        self.token, self.alive, self.crash, self.calls = token, alive, crash, []

    def helper(self, cmd, *args, timeout=0):
        self.calls.append(cmd)
        if cmd == "token":
            return {"token": self.token}
        if cmd == "health":
            return {"alive": self.alive, "pid": 7, "responding": True, "crash_log": self.crash,
                    "crash_head": "EXCEPTION_ACCESS_VIOLATION" if self.crash else ""}
        raise AssertionError(cmd)


def serve(reply_for, n=8):
    """A one-thread fake plugin: each connection gets reply_for(line) (None = close without a reply)."""
    ls = socket.socket()
    ls.bind(("127.0.0.1", 0))
    ls.listen(4)

    def loop():
        for _ in range(n):
            try:
                c, _ = ls.accept()
            except OSError:
                return
            with c:
                line = c.makefile().readline().strip()
                r = reply_for(line)
                if r == "hang":
                    time.sleep(1.5)
                    continue
                if r is not None:
                    c.sendall((json.dumps(r) + "\n").encode())

    threading.Thread(target=loop, daemon=True).start()
    return ls, ls.getsockname()[1]


@pytest.fixture(autouse=True)
def no_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(B, "STATE", tmp_path)


def make(port, machine):
    b = B.Bridge(machine=machine, port=port)
    b.tunnel = lambda: None
    return b


def test_ok_returns_the_result_and_sends_the_token():
    seen = []

    def reply(line):
        seen.append(line)
        return {"ok": True, "cmd": "player", "result": {"pos": {"z": 12.5}}}

    ls, port = serve(reply)
    assert make(port, FakeMachine()).call("player")["pos"]["z"] == 12.5
    assert seen == ["t" * 32 + " player"]
    ls.close()


def test_args_are_joined_with_single_spaces():
    seen = []
    ls, port = serve(lambda line: seen.append(line) or {"ok": True, "result": {}})
    make(port, FakeMachine()).call("console", "player.getav", "health")
    assert seen[0].endswith(" console player.getav health")
    ls.close()


def test_a_refusal_raises_bridge_error():
    ls, port = serve(lambda line: {"ok": False, "cmd": "load", "error": "no save x"})
    with pytest.raises(B.BridgeError, match="no save x") as e:
        make(port, FakeMachine()).call("load", "x")
    assert not isinstance(e.value, B.GameDown)
    ls.close()


def test_a_stale_token_is_refreshed_once(tmp_path):
    (tmp_path / "token").write_text("old" + "0" * 29)
    m = FakeMachine(token="n" * 32)
    ls, port = serve(lambda line: {"ok": True, "result": 1} if line.startswith("n" * 32) else
                     {"ok": False, "error": "bad token"})
    assert make(port, m).call("ping") == 1
    assert m.calls == ["token"]
    ls.close()


def test_a_closed_connection_with_a_dead_game_is_game_down():
    ls, port = serve(lambda line: None)
    with pytest.raises(B.GameDown, match="not running; crash log crash-1.log"):
        make(port, FakeMachine(alive=False, crash="crash-1.log")).call("player")
    ls.close()


def test_a_crash_log_while_waiting_is_game_down_within_one_interval(monkeypatch):
    monkeypatch.setattr(B, "HEALTH_EVERY", 0.3)
    ls, port = serve(lambda line: "hang")
    t0 = time.monotonic()
    with pytest.raises(B.GameDown, match="zombie"):
        make(port, FakeMachine(crash="crash-2.log")).call("load", "x")
    assert time.monotonic() - t0 < 1.0
    ls.close()


def test_no_reply_from_a_live_game_is_no_reply(monkeypatch):
    monkeypatch.setattr(B, "HEALTH_EVERY", 0.2)
    ls, port = serve(lambda line: "hang")
    with pytest.raises(B.NoReply):
        make(port, FakeMachine()).call("player", timeout=0.5)
    ls.close()


def test_frame_difference(tmp_path):
    PIL = pytest.importorskip("PIL.Image")
    a, b, c = tmp_path / "a.png", tmp_path / "b.png", tmp_path / "c.png"
    PIL.new("RGB", (10, 10), (0, 0, 0)).save(a)
    PIL.new("RGB", (10, 10), (0, 0, 0)).save(b)
    img = PIL.new("RGB", (10, 10), (0, 0, 0))
    img.putpixel((0, 0), (255, 255, 255))
    img.save(c)
    assert B.frame_difference(a, b) == 0.0  # the fail-on-purpose case: a frozen capture is not live
    assert B.frame_difference(a, c) == pytest.approx(0.01)


def test_pad_sequences_are_capped_at_three_seconds():
    assert B.pad_duration_ms("LY=1:800 B:150 wait:900") == 1850
    with pytest.raises(B.BridgeError, match="over the 3000 ms"):
        B.pad_duration_ms("LY=1:2500 B:600")  # the fail-on-purpose case
    with pytest.raises(B.BridgeError):
        B.pad_duration_ms("B")
    with pytest.raises(B.BridgeError):
        B.pad_duration_ms("")


def test_a_release_build_refuses_the_bridge():
    """The dev-only guard (decision 0003): ArgoniaBridge's CMake stops a release configure before any target."""
    import shutil
    import subprocess
    from pathlib import Path

    cmake = shutil.which("cmake") or str(Path.home() / ".argonia/buildtools/bin/cmake")
    if not Path(cmake).exists():
        pytest.skip("no cmake")
    lists = B.REPO / "skse" / "ArgoniaBridge" / "CMakeLists.txt"
    p = subprocess.run([cmake, "-DARGONIA_RELEASE=ON", "-P", str(lists)], capture_output=True, text=True)
    assert p.returncode != 0 and "dev-only and cannot be part of a release build" in p.stderr
    assert "ArgoniaBridge.dll" in (B.REPO / "skse" / "dev-only.txt").read_text()
    top = (B.REPO / "skse" / "CMakeLists.txt").read_text()
    assert "if(NOT ARGONIA_RELEASE)\n    add_subdirectory(ArgoniaBridge)" in top
