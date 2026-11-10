"""A built place's stock in numbers, read back from the plugin (tools/places/stock/verify.py `summary`).

    python -m tools.places stock report <place_id> [--out DIR] [--json PATH]

Prints containers authored and built, items placed, the containers' significant value against their budgets, the
people's and the loose things' value, the gold, the significant source things taken out (the shard plan's count), and
the ten most valuable things with who or what holds them.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv: list[str]) -> int:
    from tools.places import build as B
    from tools.places.stock import verify
    ap = argparse.ArgumentParser(prog="stock report")
    ap.add_argument("place")
    ap.add_argument("--out", default=str(B.OUT), help="the places output folder holding shards/ and plugin/")
    ap.add_argument("--json", help="also write the numbers here")
    a = ap.parse_args(argv)
    out = Path(a.out)
    plan = json.loads((out / "shards" / a.place / "plan.json").read_text())
    esp = out / "plugin" / B.PLUGIN
    tmp = out / "tmp" / f"stock_report_{a.place}.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    B.build_tool()
    B.tool("dump", str(esp), str(B.WORLD_ESM), str(tmp))
    dump = json.loads(tmp.read_text())
    tmp.unlink()
    X = verify.load(a.place, plan, dump, esp)
    if X is None:
        print(f"{a.place}: no stock source")
        return 1
    s = verify.summary(X)
    s["taken_out"] = ((plan.get("stock") or {}).get("counts") or {}).get("taken_out")
    for k, v in s.items():
        if k != "top":
            print(f"{k}: {v}")
    print("most valuable:")
    for t in s["top"]:
        print(f"  {t['value']:>6}  {t['item']} x{t['count']}  {t['held_by']}")
    if a.json:
        Path(a.json).write_text(json.dumps(s, indent=1) + "\n")
    return 0
