"""Summarise the client page's stream metrics (chunk 0.0 §c). Usage: summarize.py <dir> [--session <id>]"""
import collections
import glob
import json
import os
import sys


def q(values, p):
    s = sorted(v for v in values if isinstance(v, (int, float)))
    if not s:
        return None
    pos = (len(s) - 1) * p
    lo, hi = int(pos), min(int(pos) + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * (pos - lo), 1)


def cell(values):
    m, p = q(values, 0.5), q(values, 0.95)
    return "-" if m is None else f"{m:g}/{p:g}"


def main():
    root = sys.argv[1]
    only = sys.argv[sys.argv.index("--session") + 1] if "--session" in sys.argv else None
    recs = []
    for f in sorted(glob.glob(os.path.join(root, "*.jsonl"))):
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if only is None or r.get("session") == only:
                recs.append(r)
    sessions = {r["session"]: r for r in recs if r.get("kind") == "session"}
    groups = collections.defaultdict(lambda: {"ticks": [], "p2s": collections.defaultdict(list), "sessions": set()})
    for r in recs:
        s = sessions.get(r.get("session"), {})
        net = (r.get("net") or s.get("net") or {}) or {}
        shape = (r.get("device") or {}).get("shape") or (s.get("device") or {}).get("shape")
        key = (r.get("setup") or "?", shape or "?", net.get("type") or net.get("effectiveType") or "?")
        g = groups[key]
        g["sessions"].add(r.get("session"))
        if r.get("kind") == "tick" and r.get("transport"):
            g["ticks"].append(r)
        elif r.get("kind") == "p2s":
            g["p2s"][r.get("source")].append(r.get("ms"))
    cols = ["rttMs", "jitterMs", "lossPct", "bitrateKbps", "fps", "fpsPresented", "decodeMs", "framesDropped"]
    print(f"{len(recs)} records, {len(sessions)} sessions" + (f" (session {only})" if only else "") + "; cells are median/p95")
    print("setup | shape | net | sessions | ticks | " + " | ".join(cols) + " | press-to-screen ms by source (n median/p95)")
    for key, g in sorted(groups.items()):
        t = g["ticks"]
        p2s = ", ".join(f"{src} {len(v)} {cell(v)}" for src, v in sorted(g["p2s"].items())) or "-"
        print(" | ".join([*key, str(len(g["sessions"])), str(len(t)), *[cell([x.get(c) for x in t]) for c in cols], p2s]))
        last = next((x for x in reversed(t) if x.get("resolution")), None)
        if last:
            print(f"    last: {last.get('transport')} {last.get('resolution')} {last.get('codec')} candidate {json.dumps(last.get('candidate'))}")
    if only:
        ticks = [r for r in recs if r.get("kind") == "tick" and r.get("transport")]
        p2s = [r for r in recs if r.get("kind") == "p2s"]
        bad = []
        if len(ticks) < 10:
            bad.append(f"only {len(ticks)} streaming ticks")
        if not [r for r in ticks if isinstance(r.get("fps"), (int, float)) and r["fps"] > 1]:
            bad.append("no tick with a frame rate")
        if not [r for r in ticks if isinstance(r.get("rttMs"), (int, float))]:
            bad.append("no tick with a round trip")
        for src in ("keyboard", "touch"):
            v = [r["ms"] for r in p2s if r.get("source") == src]
            if not v:
                bad.append(f"no {src} press-to-screen samples")
            elif not 5 <= q(v, 0.5) <= 500:
                bad.append(f"{src} press-to-screen median {q(v, 0.5)} ms is implausible")
        if bad:
            print("CHECK FAILED: " + "; ".join(bad))
            sys.exit(1)
        print("CHECK PASSED: per-second ticks and press-to-screen samples present and plausible")


main()
