"""feel.py's estimate from a recorded metrics log and a recorded drive log (L2). python3 -m pytest test_feel.py"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feel  # noqa: E402


def jsonl(path, recs):
    path.write_text("\n".join(json.dumps(r) for r in recs) + "\nnot json\n")


def test_owner_network_uses_only_real_sessions_by_class(tmp_path):
    phone = {"touchPoints": 5, "shape": "unfolded"}
    jsonl(tmp_path / "2026-10-29.jsonl", [
        {"kind": "session", "session": "p", "setup": "mlw-webrtc", "device": phone},
        {"kind": "session", "session": "m", "setup": "mlw-none", "device": {"touchPoints": 0}},
        {"kind": "session", "session": "e", "setup": "e2e-headless-webrtc", "device": phone},
        {"kind": "session", "session": "d", "setup": "drive-headless-webrtc", "device": phone},
        *[{"kind": "tick", "session": "p", "transport": "webrtc", "rttMs": v, "jitterMs": 4} for v in (20, 30, 40)],
        {"kind": "tick", "session": "p", "transport": None, "rttMs": 999},
        {"kind": "tick", "session": "m", "transport": "webrtc", "rttMs": 12, "jitterMs": 1},
        {"kind": "tick", "session": "e", "transport": "webrtc", "rttMs": 1, "jitterMs": 0},
        {"kind": "tick", "session": "d", "transport": "webrtc", "rttMs": 1, "jitterMs": 0},
    ])
    net = feel.owner_network(str(tmp_path))
    assert net["phone"] == {"sessions": 1, "ticks": 3, "rttMs": 30, "jitterMs": 4}
    assert net["desktop"]["rttMs"] == 12 and net["desktop"]["sessions"] == 1


def test_summary_estimate_per_device(tmp_path):
    m = tmp_path / "m"; m.mkdir()
    jsonl(m / "a.jsonl", [{"kind": "session", "session": "p", "setup": "mlw-webrtc", "device": {"touchPoints": 5}},
                          {"kind": "tick", "session": "p", "transport": "webrtc", "rttMs": 30, "jitterMs": 5}])
    run = tmp_path / "run"
    d = run / "v5-folded"; d.mkdir(parents=True)
    (d / "drive-hud.png").write_bytes(b"")
    page = {"feel": [["touch", 50], ["touch", 60], ["touch", 70], ["keyboard", 5]], "ticks": [[2, 1, 1.5, 60]] * 3,
            "codec": "video/H265", "resolution": "1940x864"}
    (d / "drive.log").write_text(f"10:00:00 probe ({{feel: x}}) {json.dumps(page)}\n10:00:01 steps done\n")
    s = feel.summarize(str(run), str(m))
    v = s["devices"]["v5-folded"]
    assert v["p2s_median_ms"] == 60 and v["p2s_n"] == 3 and v["agent_rtt_ms"] == 2
    assert v["owner_estimate_ms"] == 60 - 2 + 30 + 5
    assert v["stills"] == ["drive-hud.png"] and v["codec"] == "video/H265" and s["ok"]
    assert json.load(open(run / "summary.json"))["devices"]["v5-folded"]["owner_estimate_ms"] == 93


def test_failed_drive_is_not_ok(tmp_path):
    d = tmp_path / "run" / "gamesir"; d.mkdir(parents=True)
    (d / "drive.log").write_text("DRIVE FAILED: no decoded video\n")
    s = feel.summarize(str(tmp_path / "run"), str(tmp_path))
    assert not s["ok"] and s["devices"]["gamesir"]["owner_estimate_ms"] is None


def test_steps_fill_the_probe_and_first_wait(tmp_path):
    for kind in ("touch", "pad", "desktop"):
        feel.steps(kind, 60000, str(tmp_path / f"{kind}.json"))
        s = json.load(open(tmp_path / f"{kind}.json"))
        assert s[0] == {"wait": 60000} and s[-1]["probe"] == feel.FEEL
        assert any("scene" in x for x in s) and sum("shot" in x for x in s) >= 4
