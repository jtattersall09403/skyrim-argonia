#!/usr/bin/env python3
"""Where do the Claude Code tokens and list-price dollars go? Reads this project's transcripts.

    session_tokens.py [--last N]   table per model for the last N days (default 7)
    session_tokens.py --brief      one line for the SessionStart hook
Prices are USD per million tokens: (input, output, cache read); a cache write costs 1.25x input.
A model id not in PRICES is shown as UNPRICED (tokens counted, dollars not).
"""
import argparse
import collections
import glob
import json
import os
import re
import sys
import time

# Placeholders carried over from the old project; check against the claude-api skill when they matter.
PRICES = {"claude-fable-5-1": (10.0, 50.0, 0.25), "claude-opus-5-5": (4.0, 20.0, 0.20),
          "claude-sonnet-5-5": (2.0, 10.0, 0.20), "claude-haiku-5-5": (0.10, 0.50, 0.01)}
WRITE = 1.25


def project_dir(root=None):
    root = root or os.getcwd()
    cfg = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    return os.path.join(cfg, "projects", re.sub(r"[^A-Za-z0-9]", "-", root))


def usage_by_model(directory, days=7, now=None):
    """{model: {input, output, cache_read, cache_write}} over every transcript touched in the last `days`."""
    cutoff = (now or time.time()) - days * 86400
    out = collections.defaultdict(lambda: collections.Counter())
    for path in glob.glob(os.path.join(directory, "**", "*.jsonl"), recursive=True):
        if os.path.getmtime(path) < cutoff:
            continue
        calls = {}  # one model call spans several records; the last carries the final usage
        for n, line in enumerate(open(path, errors="replace")):
            if '"usage"' not in line:
                continue
            try:
                m = json.loads(line).get("message") or {}
            except ValueError:
                continue
            if isinstance(m, dict) and m.get("usage") and m.get("model") != "<synthetic>":
                calls[m.get("id") or f"{path}:{n}"] = (m.get("model") or "unknown", m["usage"])
        for model, u in calls.values():
            c = out[model]
            c["input"] += u.get("input_tokens") or 0
            c["output"] += u.get("output_tokens") or 0
            c["cache_read"] += u.get("cache_read_input_tokens") or 0
            c["cache_write"] += u.get("cache_creation_input_tokens") or 0
    return out


def usd(model, c):
    """Dollars for a model's counters, None when the model has no price."""
    p = PRICES.get(model)
    if not p:
        return None
    return (c["input"] * p[0] + c["cache_write"] * p[0] * WRITE + c["output"] * p[1] + c["cache_read"] * p[2]) / 1e6


def total(by_model):
    return sum(usd(m, c) or 0 for m, c in by_model.items())


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--last", type=int, default=7, metavar="N")
    p.add_argument("--brief", action="store_true")
    p.add_argument("--dir", default=None)
    a = p.parse_args(argv)
    by = usage_by_model(a.dir or project_dir(), 1 if a.brief else a.last)
    if a.brief:
        unpriced = " (some UNPRICED)" if any(m not in PRICES for m in by) else ""
        print(f"Claude usage, last 24 h: ${total(by):.2f} list price{unpriced}")
        return 0
    print(f"{'model':<22}{'input M':>9}{'write M':>9}{'read M':>9}{'out M':>8}{'USD':>10}")
    for m, c in sorted(by.items()):
        d = usd(m, c)
        print(f"{m:<22}{c['input'] / 1e6:>9.2f}{c['cache_write'] / 1e6:>9.2f}{c['cache_read'] / 1e6:>9.2f}"
              f"{c['output'] / 1e6:>8.2f}{('UNPRICED' if d is None else f'{d:.2f}'):>10}")
    print(f"{'total (last %d d)' % a.last:<22}{'':>35}{total(by):>10.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
