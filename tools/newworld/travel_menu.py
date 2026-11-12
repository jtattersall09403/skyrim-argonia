"""The travel menu: the pages of the "Argonia Travel" lesser power, newworld/sources/travel/menu.json.

The owner on a gamepad has no console. The power (ArgoniaNewWorld.esm, tools/ArgoniaPlugin/NewWorldTravel.cs) opens
a message menu of at most 10 buttons a page; a button opens another page or moves the player to a named cell, the way
`coc <cell>` does (`Debug.CenterOnCell`). The pages are data:

    {"root": "root", "pages": {"<id>": {"title": "...", "buttons": [{"label": "...", "page": "<id>"} |
                                                                     {"label": "...", "cell": "<coc name>"}]}}}

`generate` writes the pages the world makes (the start, the places by region in a pager, the walk checks) from
teleports.json and the place database, and keeps the page `spots` as it stands: a walk-check spot is one more row
there, `{"label": "...", "cell": "ANW..."}`. `check` holds the file to the menu's rules (and, given a teleports.json,
to its cells):

    python3 -m tools.newworld.travel_menu generate [--plugin out/newworld/plugin]
    python3 -m tools.newworld.travel_menu check [--plugin out/newworld/plugin]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MENU = REPO / "newworld/sources/travel/menu.json"
DB = REPO / "newworld/story/data/db"
MAX_BUTTONS = 10      # a message box's buttons, the Back and More buttons included
CHUNK = 8             # items a pager page holds: with Back and More, a full page


def _chunks(prefix: str, title: str, items: list[dict], back: str) -> dict:
    """Pages `prefix`, `prefix-2`, ... of CHUNK items each; each page ends with More (but the last) and Back."""
    pages = {}
    parts = [items[i:i + CHUNK] for i in range(0, len(items), CHUNK)] or [[]]
    for n, part in enumerate(parts, 1):
        pid = prefix if n == 1 else f"{prefix}-{n}"
        btn = list(part)
        if n < len(parts):
            btn.append({"label": "More", "page": f"{prefix}-{n + 1}"})
        btn.append({"label": "Back", "page": back if n == 1 else (prefix if n == 2 else f"{prefix}-{n - 1}")})
        pages[pid] = {"title": title + (f" ({n} of {len(parts)})" if len(parts) > 1 else ""), "buttons": btn}
    return pages


def generate(plugin: Path) -> dict:
    tele = json.loads((plugin / "map/teleports.json").read_text())["teleports"]
    rows = lambda n: [json.loads(ln) for ln in (DB / n).read_text().splitlines() if ln.strip()]
    regions = {r["id"]: r["name"] for r in rows("region.jsonl")}
    place = {p["id"]: p for p in rows("place.jsonl")}
    old = json.loads(MENU.read_text()) if MENU.exists() else {"pages": {}}
    pages: dict = {}
    by_region: dict[str, list[dict]] = {}
    walk = []
    for t in tele:
        if t["kind"] == "place":
            by_region.setdefault(place[t["id"]]["region_id"], []).append({"label": t["what"], "cell": t["coc"]})
        else:
            walk.append({"label": t["what"][:1].upper() + t["what"][1:], "cell": t["coc"]})
    region_items = []
    for rid in sorted(by_region, key=lambda r: regions[r]):
        items = sorted(by_region[rid], key=lambda b: b["label"])
        pages.update(_chunks(f"r-{rid}", regions[rid], items, "regions"))
        region_items.append({"label": regions[rid], "page": f"r-{rid}"})
    pages.update(_chunks("regions", "Places by region", region_items, "root"))
    pages["walk"] = {"title": "Walk checks", "buttons": walk[:MAX_BUTTONS - 1] + [{"label": "Back", "page": "root"}]}
    pages["spots"] = old["pages"].get("spots") or {"title": "Walk-check spots", "buttons": [{"label": "Back", "page": "root"}]}
    root = [{"label": "The start of the new world", "cell": "ArgoniaNWStart"},
            {"label": "Places by region", "page": "regions"},
            {"label": "Walk-check waters", "page": "walk"},
            {"label": "Walk-check spots", "page": "spots"}]
    pages["root"] = {"title": "Argonia Travel", "buttons": root}
    return {"root": "root", "pages": dict(sorted(pages.items(), key=lambda kv: (kv[0] != "root", kv[0])))}


def faults(doc: dict, cells: set[str] | None = None) -> list[str]:
    out = []
    pages = doc.get("pages", {})
    if doc.get("root") not in pages:
        out.append("the root page is not a page")
    for pid, p in pages.items():
        b = p.get("buttons", [])
        if not b or len(b) > MAX_BUTTONS:
            out.append(f"{pid}: {len(b)} buttons (1 to {MAX_BUTTONS})")
        if not p.get("title"):
            out.append(f"{pid}: no title")
        for x in b:
            if not x.get("label") or len(x["label"]) > 60:
                out.append(f"{pid}: a button label is empty or over 60 characters: {x.get('label')!r}")
            if ("page" in x) == ("cell" in x):
                out.append(f"{pid}/{x.get('label')}: a button names a page or a cell, one of them")
            elif "page" in x and x["page"] not in pages:
                out.append(f"{pid}/{x['label']}: page {x['page']} does not exist")
            elif "cell" in x and cells is not None and x["cell"] not in cells:
                out.append(f"{pid}/{x['label']}: no cell {x['cell']} in teleports.json")
    seen, todo = set(), [doc.get("root")]
    while todo:
        q = todo.pop()
        if q in seen or q not in pages:
            continue
        seen.add(q)
        todo += [x["page"] for x in pages[q].get("buttons", []) if "page" in x]
    out += [f"{pid}: not reachable from the root" for pid in pages if pid not in seen]
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("generate", "check"))
    ap.add_argument("--plugin", type=Path, default=REPO / "out/newworld/plugin")
    a = ap.parse_args(argv)
    tj = a.plugin / "map/teleports.json"
    if a.cmd == "generate":
        doc = generate(a.plugin)
        MENU.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
        print(f"travel menu: {len(doc['pages'])} pages written to {MENU.relative_to(REPO)}")
    else:
        doc = json.loads(MENU.read_text())
    cells = None
    if tj.exists():
        t = json.loads(tj.read_text())
        cells = {x["coc"] for x in t["teleports"]} | {c["coc"] for c in t["cells"]} | {"ArgoniaNWStart"}
    bad = faults(doc, cells)
    for f in bad:
        print("FAIL", f)
    if not bad:
        print(f"travel menu: {len(doc['pages'])} pages, every rule held" + ("" if cells else " (no teleports.json to hold cells to)"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
