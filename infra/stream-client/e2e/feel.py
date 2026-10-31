"""The stream-feel check's steps and estimate (chunk 1.8 item 8). feel.sh drives each device through drive.mjs; this
writes each device's steps and, after the runs, summary.json: per device its stills, the press-to-screen median
from the page's own marker samples, and owner_estimate_ms = that median - the agents' own round trip (a few ms on
the machine itself) + the owner's round trip and jitter from their logged real sessions.
  feel.py steps <kind> <first-wait-ms> <out.json>          kind: touch | pad | desktop
  feel.py summarize <run-dir> [--metrics <dir>]            default ~/.argonia/stream-metrics
"""
import glob
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# what the page knows at the end of a run: its paired marker samples and its per-second ticks
FEEL = ("({feel: argonia.metrics.probe.samples.map(s => [s.source, s.ms]), "
        "ticks: argonia.metrics.ticks.filter(t => t.transport).map(t => [t.rttMs, t.jitterMs, t.decodeMs, t.fps]), "
        "codec: (argonia.metrics.ticks.filter(t => t.codec).at(-1) || {}).codec || null, "
        "resolution: (argonia.metrics.ticks.filter(t => t.resolution).at(-1) || {}).resolution || null})")
# device -> drive.mjs profile, steps kind, the marker sources that are its input, the owner's network class
DEVICES = {
    "desktop": {"profile": "desktop", "kind": "desktop", "sources": ["keyboard", "mouse"], "net": "desktop"},
    "v5-folded": {"profile": "v5-folded", "kind": "touch", "sources": ["touch"], "net": "phone"},
    "v5-unfolded": {"profile": "v5-unfolded", "kind": "touch", "sources": ["touch"], "net": "phone"},
    "gamesir": {"profile": "v5-folded", "kind": "pad", "sources": ["gamepad"], "net": "phone", "fakepad": True},
}
AGENT_SETUPS = ("e2e-", "drive-")   # our own headless runs; every other setup is the owner on a real device


def med(values):
    v = [x for x in values if isinstance(x, (int, float))]
    return round(statistics.median(v), 1) if v else None


def steps(kind, first_wait, out):
    s = json.load(open(os.path.join(HERE, "steps", f"feel-{kind}.json")))
    s = [{"wait": first_wait}] + [{"probe": FEEL} if x.get("probe") == "FEEL" else x for x in s]
    json.dump(s, open(out, "w"), indent=0)


def page_result(log_text):
    """The FEEL probe's result from a drive log (drive.mjs logs `probe <expr> <json>`), or None."""
    for line in reversed(log_text.splitlines()):
        i = line.find('{"feel":')
        if i >= 0:
            return json.loads(line[i:])
    return None


def owner_network(metrics_dir):
    """The owner's round trip and jitter (medians of streaming ticks) per class, phone (touch points) or desktop,
    from sessions whose setup is not ours."""
    recs = []
    for f in sorted(glob.glob(os.path.join(metrics_dir, "*.jsonl"))):
        for line in open(f, encoding="utf-8"):
            try:
                recs.append(json.loads(line))
            except ValueError:
                continue
    cls = {}
    for r in recs:
        if r.get("kind") == "session" and not str(r.get("setup") or "").startswith(AGENT_SETUPS):
            cls[r.get("session")] = "phone" if ((r.get("device") or {}).get("touchPoints") or 0) > 0 else "desktop"
    out = {}
    for c in ("phone", "desktop"):
        ticks = [r for r in recs if r.get("kind") == "tick" and r.get("transport") and cls.get(r.get("session")) == c]
        out[c] = {"sessions": len({t["session"] for t in ticks}), "ticks": len(ticks),
                  "rttMs": med([t.get("rttMs") for t in ticks]), "jitterMs": med([t.get("jitterMs") for t in ticks])}
    return out


def device_summary(name, run_dir, net):
    d = os.path.join(run_dir, name)
    log = open(os.path.join(d, "drive.log"), encoding="utf-8", errors="replace").read() if os.path.exists(os.path.join(d, "drive.log")) else ""
    page = page_result(log) or {}
    want = DEVICES[name]["sources"]
    samples = [ms for src, ms in page.get("feel", []) if src in want]
    by_source = {s: med([ms for src, ms in page.get("feel", []) if src == s]) for s in want}
    ticks = page.get("ticks", [])
    agent_rtt = med([t[0] for t in ticks])
    p2s = med(samples)
    owner = net[DEVICES[name]["net"]]
    est = None
    if p2s is not None and owner["rttMs"] is not None:
        est = round(p2s - (agent_rtt or 0) + owner["rttMs"] + (owner["jitterMs"] or 0), 1)
    return {"profile": DEVICES[name]["profile"], "input": "+".join(want),
            "stills": sorted(os.path.basename(p) for p in glob.glob(os.path.join(d, "*.png"))),
            "p2s_n": len(samples), "p2s_median_ms": p2s, "p2s_by_source_ms": by_source,
            "agent_rtt_ms": agent_rtt, "decode_ms": med([t[2] for t in ticks]), "fps": med([t[3] for t in ticks]),
            "codec": page.get("codec"), "resolution": page.get("resolution"),
            "owner_net": DEVICES[name]["net"], "owner_estimate_ms": est,
            "drive_ok": "steps done" in log and "DRIVE FAILED" not in log}


def summarize(run_dir, metrics_dir):
    net = owner_network(metrics_dir)
    devs = {n: device_summary(n, run_dir, net) for n in DEVICES if os.path.isdir(os.path.join(run_dir, n))}
    s = {"run": os.path.basename(os.path.abspath(run_dir)), "owner_network": net, "devices": devs,
         "estimate": "owner_estimate_ms = p2s_median_ms - agent_rtt_ms + owner rttMs + owner jitterMs",
         "ok": bool(devs) and all(d["drive_ok"] and d["owner_estimate_ms"] is not None for d in devs.values())}
    json.dump(s, open(os.path.join(run_dir, "summary.json"), "w"), indent=1)
    return s


def main(argv):
    if argv[:1] == ["steps"]:
        steps(argv[1], int(argv[2]), argv[3])
    elif argv[:1] == ["summarize"]:
        m = argv[argv.index("--metrics") + 1] if "--metrics" in argv else os.path.expanduser("~/.argonia/stream-metrics")
        s = summarize(argv[1], m)
        for n, d in s["devices"].items():
            print(f"{n}: p2s {d['p2s_median_ms']} ms (n {d['p2s_n']}), decode {d['decode_ms']} ms, {d['codec']}, "
                  f"owner estimate {d['owner_estimate_ms']} ms, stills {len(d['stills'])}, drive {'ok' if d['drive_ok'] else 'FAILED'}")
        print("owner network:", json.dumps(s["owner_network"]))
        return 0 if s["ok"] else 1
    else:
        print(__doc__)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
