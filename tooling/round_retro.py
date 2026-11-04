#!/usr/bin/env python3
"""A round's retrospective (1.15-r6-fast-loop-2; owner 2026-11-04 #37: each round closes with where the time went).

    tooling/round_retro.py <log glob> [--since YYYY-MM-DD] [--append docs/research/<date>/round-N.md]

Reads ~/.argonia/jobs/<glob>.log (e.g. 'r6-*'), and prints the stage table (count, median, p90, total, share of the
summed stage time) from the lines each step prints: deploy's `== <step>` / `== N s`, `== <step>: N s` (LOD),
`ROUND|PREBATCH <step> OK|FAIL in N s`, `DEPLOY OK in N s`, the batch's `run N: PASS|FAIL in X s`, the LOD metrics
lines; then the waits: capacity (`up after N tries`, 60 s apart; `no spot capacity` lines), interrupts (`resumes`,
`interrupted`), locks (`queued for ... behind`); then the LOD halves (`LOD current`, `restore`, `no LOD archive`).
"""
from __future__ import annotations
import argparse, glob, os, re, statistics, sys, time
from collections import defaultdict

PAT = [
    (re.compile(r"^== ([^:]+): (\d+) s"), lambda m: ("lod: " + m[1], m[2])),
    (re.compile(r"DEPLOY OK in (\d+) s"), lambda m: ("deploy total", m[1])),
    (re.compile(r"^(ROUND|PREBATCH) (\S+) (?:OK|FAIL) in (\d+) s"), lambda m: (m[1].lower() + ": " + m[2], m[3])),
    (re.compile(r"^ROUND DONE \S+ in (\d+) s"), lambda m: ("round total", m[1])),
    (re.compile(r"run \d+: (?:PASS|FAIL) in ([\d.]+) s"), lambda m: ("batch: per journey run", m[1])),
    (re.compile(r'metrics: \{"step":"(\w+)","seconds":(\d+)'), lambda m: ("lod metrics: " + m[1], m[2])),
]
WAITS = {"capacity: no spot capacity lines": r"no spot capacity", "interrupts": r"interrupted|resumes\)|again \(resumes\)",
         "locks: queued behind": r"queued for .* behind", "lod: current": r"LOD current", "lod: restored": r"LOD restored|restore ",
         "lod: no archive (rebuild owed)": r"no LOD archive"}


def parse(files):
    S, W = defaultdict(list), defaultdict(int)
    for f in files:
        cur = None
        for ln in open(f, errors="replace"):
            ln = ln.rstrip()
            m = re.match(r"^== (\d+) s$", ln)
            if m:
                if cur: S["deploy: " + cur].append(float(m[1])); cur = None
                continue
            m = re.match(r"^up after (\d+) tries", ln)
            if m: S["capacity wait ((tries-1) x 60 s)"].append((int(m[1]) - 1) * 60.0)
            for p, g in PAT:
                m = p.search(ln)
                if m:
                    k, v = g(m); S[k].append(float(v)); break
            else:
                m = re.match(r"^== ([^:]+?)(?: \d\d:\d\d:\d\d.*)?$", ln)
                if m: cur = m[1]
            for k, p in WAITS.items():
                if re.search(p, ln): W[k] += 1
    return S, W


def table(S, W) -> str:
    leaf = {k: v for k, v in S.items() if "total" not in k and not k.startswith(("round: deploy", "round: batch", "lod metrics"))}
    tot = sum(sum(v) for v in leaf.values()) or 1
    out = ["| stage | n | median s | p90 s | total s | share |", "|---|---|---|---|---|---|"]
    for k, v in sorted(S.items(), key=lambda kv: -sum(kv[1])):
        v = sorted(v); p90 = v[min(len(v) - 1, round(0.9 * (len(v) - 1)))]
        sh = f"{100 * sum(v) / tot:.1f} %" if k in leaf else "(sum)"
        out.append(f"| {k} | {len(v)} | {statistics.median(v):.0f} | {p90:.0f} | {sum(v):.0f} | {sh} |")
    out += ["", "| wait or LOD half | lines |", "|---|---|"] + [f"| {k} | {n} |" for k, n in sorted(W.items())]
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("glob"); ap.add_argument("--since"); ap.add_argument("--append")
    ap.add_argument("--jobs", default=os.path.expanduser("~/.argonia/jobs"))
    a = ap.parse_args(argv)
    lo = time.mktime(time.strptime(a.since, "%Y-%m-%d")) if a.since else 0
    files = sorted(f for f in glob.glob(os.path.join(a.jobs, a.glob + ".log")) if os.path.getmtime(f) >= lo)
    if not files: print(f"round_retro: no logs match {a.glob}", file=sys.stderr); return 1
    t = f"{len(files)} logs ({a.glob}{', since ' + a.since if a.since else ''})\n\n" + table(*parse(files))
    print(t)
    if a.append:
        with open(a.append, "a") as fh: fh.write("\n## Where the time went (tooling/round_retro.py)\n\n" + t + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
