"""The travel menu: the pages of the "Argonia Travel" lesser power, newworld/sources/travel/menu.json.

The owner on a gamepad has no console. The power (ArgoniaNewWorld.esm, tools/ArgoniaPlugin/NewWorldTravel.cs) opens
a message box of at most 10 buttons a page, in one row that must fit the screen; a button opens another page or moves
the player to a named cell, the way `coc <cell>` does (`Debug.CenterOnCell`). The pages are data:

    {"root": "root", "pages": {"<id>": {"title": "...", "buttons": [{"label": "...", "page": "<id>"} |
                                                                     {"label": "...", "cell": "<coc name>"}]}}}

A page's title is the box's text: its name, then one line for each button whose short label stands for a longer
description ("<label>: <description>"); a button keeps that description as "about".

`generate` writes the pages the world makes (the start, the places by region, the walk-check waters and the ecology
walk's spots, each list paged with More... and Back) from teleports.json and the place database: a spot is a row of
`SPOTS` in tools/newworld/teleports.py (a named cell with its reason). `check` holds the file to the menu's rules (and,
given a teleports.json, to its cells):

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
MAX_BUTTONS = 10      # the engine's message box: at most 10 buttons (MESG menu buttons), More... and Back included
# The laid message box is the vanilla interface/messagebox.swf (no mod of the stack replaces it): it lays every button in
# one centred row that never wraps (MessageBox.InitButtons: each button its text's width plus SELECTION_INDICATOR_WIDTH),
# so a page whose row is wider than the screen loses its outer buttons, More... and Back first. On the 1280-wide stage
# of a 16:9 screen the row's safe width is about 1100 px, at about 12 px a character of the button font and about 40 px
# of indicator and spacing a button: a page's row holds ROW_CHARS characters, counting BUTTON_COST more a button.
# The pad moves along the row with left and right, A presses, B leaves the menu.
LABEL_MAX = 24        # a button's label; the page's text names each short label's whole description
ROW_CHARS = 96        # characters of one page's row of buttons, BUTTON_COST added a button
BUTTON_COST = 4
TEXT_LINES = 10       # lines of a page's text (its name and the descriptions)
MORE, BACK = "More...", "Back"
# the walk checks' own short labels, by teleport (tools/newworld/teleports.py WALK and SPOTS); others are cut by short()
SHORT = {
    "ANWSpotD1CapePercar": "D1 Cape Percar", "ANWSpotD5Murkwood": "D5 Murkwood", "ANWSpotFreshWater": "Fresh water",
    "ANWSpotSaltWater": "Salt water", "ANWSpotCanopy": "Canopy", "ANWSpotOpen": "Open ground",
    "ANWSpotDusk": "Dusk insects", "ANWSpotHostileNpcs": "Hostile band", "ANWSpotSwampHarvest": "Harvest plants",
    "ANWSpotDry": "Dry scrub", "ANWSpotSeaShore": "Sea shore", "ANWSpotLakeUlaish": "Lake shore",
    "ANWSpotBarsaebica": "Cool fen", "ANWSpotKotherra": "Red mangroves", "ANWSpotValleyOfStorms": "Storm light",
    "ANWWalkSwamp": "Black swamp", "ANWWalkMarsh": "Green marsh", "ANWWalkRiver": "River", "ANWWalkStream": "Stream",
    "ANWWalkPond": "Pond", "ANWWalkEstuary": "Estuary", "ANWWalkSea": "Open sea", "ANWWalkHelstromRiver": "Helstrom river",
}


def _row(labels: list[str]) -> int:
    return sum(len(x) for x in labels) + BUTTON_COST * len(labels)


def short(what: str) -> str:
    """A button's label for a description: the part after a colon (the spot "D1, the lowest danger: Cape Percar open
    coast" is "Cape Percar open coast"), cut at a word to LABEL_MAX."""
    s = what.split(": ", 1)[-1].strip()
    s = s[:1].upper() + s[1:]
    if len(s) > LABEL_MAX and s.startswith("Wreck of the "):
        s = s[len("Wreck of the "):] + " wreck"
    if len(s) <= LABEL_MAX:
        return s
    return s[:LABEL_MAX - 3].rsplit(" ", 1)[0].rstrip(",;:- ") + "..."


def _item(what: str, **target) -> dict:
    full = what[:1].upper() + what[1:]
    b = {"label": SHORT.get(target.get("cell", ""), short(full)), **target}
    if b["label"] != full:
        b["about"] = full
    return b


def _text(title: str, btn: list[dict]) -> str:
    return "\n".join([title, *(f"{b['label']}: {b['about']}" for b in btn if b.get("about"))])


def _chunks(prefix: str, title: str, items: list[dict], back: str) -> dict:
    """Pages `prefix`, `prefix-2`, ...: each holds as many items as fit its row beside its More... and Back buttons."""
    parts: list[list[dict]] = [[]]
    for it in items:
        cur = parts[-1] + [it]
        fits = (len(cur) + 2 <= MAX_BUTTONS and _row([b["label"] for b in cur] + [MORE, BACK]) <= ROW_CHARS
                and 1 + sum(1 for b in cur if b.get("about")) <= TEXT_LINES)
        if parts[-1] and not fits:
            parts.append([])
        parts[-1].append(it)
    pages = {}
    for n, part in enumerate(parts, 1):
        pid = prefix if n == 1 else f"{prefix}-{n}"
        btn = list(part)
        if n < len(parts):
            btn.append({"label": MORE, "page": f"{prefix}-{n + 1}"})
        btn.append({"label": BACK, "page": back if n == 1 else (prefix if n == 2 else f"{prefix}-{n - 1}")})
        pages[pid] = {"title": _text(title + (f" ({n} of {len(parts)})" if len(parts) > 1 else ""), btn), "buttons": btn}
    return pages


def generate(plugin: Path, tele: list[dict] | None = None) -> dict:
    tele = tele if tele is not None else json.loads((plugin / "map/teleports.json").read_text())["teleports"]
    rows = lambda n: [json.loads(ln) for ln in (DB / n).read_text().splitlines() if ln.strip()]
    regions = {r["id"]: r["name"] for r in rows("region.jsonl")}
    place = {p["id"]: p for p in rows("place.jsonl")}
    pages: dict = {}
    by_region: dict[str, list[dict]] = {}
    walk, spots = [], []
    for t in tele:
        if t["kind"] == "place":
            by_region.setdefault(place[t["id"]]["region_id"], []).append(_item(t["what"], cell=t["coc"]))
        else:
            (spots if t["kind"] == "spot" else walk).append(_item(t["what"], cell=t["coc"]))
    region_items = []
    for rid in sorted(by_region, key=lambda r: regions[r]):
        items = sorted(by_region[rid], key=lambda b: b["label"])
        pages.update(_chunks(f"r-{rid}", regions[rid], items, "regions"))
        region_items.append(_item(regions[rid], page=f"r-{rid}"))
    pages.update(_chunks("regions", "Places by region", region_items, "root"))
    pages.update(_chunks("walk", "Walk-check waters", walk, "root"))
    pages.update(_chunks("spots", "Walk-check spots", spots, "root"))
    root = [{"label": "The start", "cell": "ArgoniaNWStart"},
            {"label": "Places", "page": "regions"},
            {"label": "Waters", "page": "walk"},
            {"label": "Walk spots", "page": "spots"}]
    pages["root"] = {"title": "Argonia Travel\nThe start: where a new game of the new world begins\n"
                              "Places: every place, by region\nWaters: the walk checks' waters\n"
                              "Walk spots: the walk checks' spots", "buttons": root}
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
        elif len(p["title"].split("\n")) > TEXT_LINES:
            out.append(f"{pid}: {len(p['title'].split(chr(10)))} lines of text (at most {TEXT_LINES})")
        width = _row([x.get("label") or "" for x in b])
        if width > ROW_CHARS:
            out.append(f"{pid}: its row of buttons is {width} characters wide (at most {ROW_CHARS}): off the screen")
        if len({x.get("label") for x in b}) < len(b):
            out.append(f"{pid}: two buttons share a label")
        if pid != doc.get("root") and not any(x.get("label") == BACK and "page" in x for x in b):
            out.append(f"{pid}: no {BACK} button")
        for x in b:
            if not x.get("label") or len(x["label"]) > LABEL_MAX:
                out.append(f"{pid}: a button label is empty or over {LABEL_MAX} characters: {x.get('label')!r}")
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
