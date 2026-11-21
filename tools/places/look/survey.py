"""`look <place> survey [<structure> ...] [--changed]`: one contact sheet per structure (and the whole place when none
is named): near and far from the four compass sides at eye level, two high obliques, a top view with the crowns
cut, sections on two axes with the ground line and a height scale, all in a neutral fill light, and one tile in the
place's own light (the viewer's, not the game's). Each tile is drawn at 1280x960 and saved as its own file
(`tiles/NN-<side>-<near|far|high|top|section-...|lit>.png`, with its id buffer for `pick`) carrying its side,
distance and capture score; a failed tile is retried once and else struck through. The contact sheet is the index:
the same tiles at 640x480, four across. Beside each sheet a table (JSON and plain text) of what each tile shows,
with each tile's file. `--changed` surveys only the structures whose rows changed since this checkout's last survey.

The tiles of a sheet are drawn in one page call on the warm scene. Pure parts (the tile plan, the row hashes, the
table) are tested in tools/tests/test_places_look.py."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from tools.places.look import capture, draw, verbs
from tools.places.look.scene import LOOK_OUT

TW, TH = 1280, 960         # a tile, as drawn and as saved
SW, SH = 640, 480           # a tile on the contact sheet
SCORE_W = 384               # the width of the id pass a tile is scored on (and picked from)
OWN_LIGHT = "viewer light, not the game's"
NEAR, FAR = 0.55, 1.3   # eye-level distances, as shares of the distance that frames the whole structure


def tile_file(i: int, t: dict) -> str:
    """The file name of tile `i` (counting from 1): NN-<side>-<near|far|high|top|lit>, or NN-section-<axis>."""
    if t.get("section"):
        return f"{i:02d}-section-{t['section']}.png"
    kind = "lit" if t.get("own_light") else t["name"].split()[-1] if t["name"].split()[-1] in ("near", "far", "high") else "top"
    return f"{i:02d}-{t['side']}-{kind}.png"


def plan() -> list[dict]:
    """The tiles of one sheet, in order."""
    t = [{"name": f"{s.upper()} {d}", "side": s, "height": "eye", "scale": k}
         for d, k in (("near", NEAR), ("far", FAR)) for s in ("n", "e", "s", "w")]
    t += [{"name": f"{s.upper()} high", "side": s, "height": "high", "scale": 1.0} for s in ("ne", "sw")]
    t += [{"name": "top, crowns cut", "side": "s", "height": "top", "scale": 1.0, "cut": True}]
    t += [{"name": f"section {a}", "section": a} for a in ("west-east", "south-north")]
    t += [{"name": OWN_LIGHT, "side": "se", "height": "oblique", "scale": 1.0, "own_light": True}]
    return t


def row_hash(rows: list[dict]) -> str:
    return hashlib.sha1(json.dumps(sorted(rows, key=lambda r: r.get("id", "")), sort_keys=True).encode()).hexdigest()[:16]


def structure_hashes(refs: list[dict]) -> dict[str, str]:
    """Each structure's rows (by cluster) hashed, and the whole place's as '_place'."""
    by: dict[str, list] = {}
    for r in refs:
        if r.get("cluster"):
            by.setdefault(r["cluster"], []).append(r)
    out = {c: row_hash(rs) for c, rs in by.items()}
    out["_place"] = row_hash(refs)
    return out


def changed(last: dict, now: dict) -> list[str]:
    """The structures whose rows differ from the last survey's (new ones too); the place when anything did."""
    got = [c for c in sorted(now) if c != "_place" and last.get(c) != now[c]]
    if got or last.get("_place") != now.get("_place"):
        got.append("_place")
    return got


def table_text(name: str, rows: list[dict]) -> str:
    """The plain-text table of what each tile shows."""
    out = [f"survey of {name}: {sum(r['capture'] == 'failed' for r in rows)} of {len(rows)} tiles failed",
           f"{'tile':24} {'capture':8} {'seen':>5} {'fills':>5} {'land':>5} {'sky':>5}  file; covered by / why"]
    for r in rows:
        occ = ", ".join(f"{o.get('edid') or o['piece'][-8:]} {o['share']:.0%}" for o in r.get("occluders", [])[:3])
        out.append(f"{r['tile']:24} {r['capture']:8} {r.get('subject_seen', 0):5.0%} {r.get('subject_fills', 0):5.0%} "
                   f"{r.get('land', 0):5.0%} {r.get('sky', 0):5.0%}  {r.get('file', '')}; {occ}{'; FAILED: ' + r['why'] if r.get('why') else ''}")
    return "\n".join(out) + "\n"


def _cam(sc, place, th, t, gz, retry=False):
    if t.get("section"):
        lo, hi = th["lo"], th["hi"]
        my, mx = (lo[1] + hi[1]) / 2, (lo[0] + hi[0]) / 2
        A, B = ([lo[0] - 300, my], [hi[0] + 300, my]) if t["section"] == "west-east" else ([mx, lo[1] - 300], [mx, hi[1] + 300])
        cam, crossed, prof = verbs.section_setup(sc, A, B, 96.0, TW, TH)
        return cam | {"_section": (crossed, prof)}
    # a retry: the next side round, nearer at the eye (past what stood in the way), further from high
    scale = t["scale"] * ((0.7 if t["height"] == "eye" else 1.4) if retry else 1.0)
    side = verbs.framing.by_turn(t["side"])[1] if retry else t["side"]
    c = verbs.make_cam(sc, place, th, side, t["height"], TW, TH, {}, False, scale, gz)
    if c is None:
        return None
    if t.get("scale", 1) < 1:   # a near look shows part of the structure: judged on the part in its frame
        c["part"] = True
    if t.get("cut") or retry:
        from tools.places.look import canopy
        c["canopy"] = {"z": canopy.cut_height(gz)}
    return c


def sheet(d, place, strokes, sc, th, faults, out_dir: Path) -> dict:
    """One structure's sheet: every tile in one page call, failed tiles retried once in a second."""
    t0 = time.time()
    gz = sc.ground_under(th["lo"], th["hi"])
    tiles = plan()
    cams = [_cam(sc, place, th, t, gz) for t in tiles]
    subj = [p["id"] for p in th["pieces"]][:400]
    rows: list[dict] = [{} for _ in tiles]
    imgs: list = [None] * len(tiles)
    ids_keep: list = [None] * len(tiles)
    calls = []

    def run(idx):
        page = [dict(_page(cams[i]), ids=True, ref_w=SCORE_W, subject=subj, fill=not tiles[i].get("own_light"), grass=False)
                for i in idx]
        tc = time.time()
        got = d.page.evaluate("(cs) => agent.shots(cs)", page)
        calls.append(round(time.time() - tc, 2))
        for i, r in zip(idx, got):
            c = cams[i]
            img = draw.from_data_url(r["png"])
            s, ids = verbs.judge(sc, c, r, th, False)
            img = capture.hatch(img, ids, r["table"], r["id0"], verbs.helper_label(sc))
            title = f"{th['name']} {tiles[i]['name']}"
            if c.get("_section"):
                img = draw.annotate_section(img, c, sc, c["_section"][1], c["_section"][0], faults, title)
            else:
                img, _ = draw.annotate(img, c, sc, th, faults, title)
            imgs[i], ids_keep[i] = img, {"ids": ids, "table": r["table"], "id0": r["id0"]}
            rows[i] = {"tile": tiles[i]["name"], "side": tiles[i].get("side"), "height": tiles[i].get("height"),
                       "distance": tiles[i].get("scale")} | s

    d.open(place)
    d.sync(strokes)
    d.go("exterior")
    first = [i for i, c in enumerate(cams) if c is not None]
    for i, c in enumerate(cams):
        if c is None:
            rows[i] = {"tile": tiles[i]["name"], "capture": "failed", "why": "no spot a person can stand there"}
    run(first)
    again = [i for i in first if rows[i]["capture"] == "failed" and not tiles[i].get("section")]
    if again:
        for i in again:
            c = _cam(sc, place, th, tiles[i], gz, retry=True)
            if c is not None:
                cams[i], rows[i]["retried"] = c, True
        run([i for i in again if cams[i] is not None])
    for i, r in enumerate(rows):
        if imgs[i] is None:
            from PIL import Image
            imgs[i] = Image.new("RGBA", (TW, TH), (60, 60, 60, 255))
        if r.get("capture") == "failed":
            imgs[i] = capture.strike(verbs.mark(imgs[i], r))
        cap = r["tile"] + (f"  seen {r.get('subject_seen', 0):.0%}" if "subject_seen" in r else "")
        if tiles[i].get("own_light"):
            cap = f"{th['name']}: {OWN_LIGHT}"
        from PIL import ImageDraw
        dd = ImageDraw.Draw(imgs[i])
        draw.tag(dd, (TW // 2, TH - 10), cap, size=12, fill=(255, 255, 160, 240))
    out_dir.mkdir(parents=True, exist_ok=True)
    tdir = out_dir / "tiles"
    tdir.mkdir(exist_ok=True)
    for old in tdir.glob("*"):   # the tiles of the last survey of this structure
        old.unlink()
    png = out_dir / "sheet.png"
    from PIL import Image
    small, metas = [], []
    for i, (im, c) in enumerate(zip(imgs, cams)):
        f = tdir / tile_file(i + 1, tiles[i])
        verbs._save(im, str(f), {k: v for k, v in (c or {"w": TW, "h": TH}).items() if k != "_section"})
        if ids_keep[i]:
            verbs.save_ids(str(f), [ids_keep[i]])
        rows[i]["file"] = str(f)
        small.append(im.convert("RGB").resize((SW, SH), Image.LANCZOS))
        metas.append(dict({k: v for k, v in (c or {"w": TW, "h": TH}).items() if k != "_section"},
                          ox=(i % 4) * SW, oy=(i // 4) * SH, sw=SW, sh=SH, file=str(f)))
    verbs._save(draw.sheet(small, 4), str(png))
    (Path(str(png) + ".json")).write_text(json.dumps({"tiles": metas, "cols": 4}))
    (out_dir / "table.json").write_text(json.dumps(rows, indent=1))
    (out_dir / "table.txt").write_text(table_text(th["name"], rows))
    return {"structure": th["name"], "sheet": str(png), "failed": sum(r.get("capture") == "failed" for r in rows),
            "tiles": len(rows), "tiles_dir": str(tdir), "files": [r["file"] for r in rows], "s": round(time.time() - t0, 1), "page_calls_s": calls}


def _page(c: dict) -> dict:
    return {k: v for k, v in c.items() if not k.startswith("_")}


def run(d, place: str, strokes, args: list[str]) -> dict:
    t0 = time.time()
    pos, o = verbs._opts(args, {"changed": False})
    sc = d.scene(place, strokes, "exterior")
    faults = {x["id"] for x in sc.faults()}
    root = LOOK_OUT / place / "survey"
    state_p = root / "state.json"
    now = structure_hashes(sc.files["spaces"]["exterior"]["refs"])
    names = pos
    if o.get("changed"):
        last = json.loads(state_p.read_text()) if state_p.exists() else {}
        names = changed(last, now)
    elif not names:
        names = ["_place"]
    out = []
    for n in names:
        if n == "_place":
            cl = sc.clusters()
            allp = [p for c, ps in cl.items() if not c.startswith("w") and c != "outside" for p in ps] or sc.pieces
            th = sc._of(place, "place", allp)
        else:
            th = sc.resolve(n)
        out.append(sheet(d, place, strokes, sc, th, faults, root / ("place" if n == "_place" else n)))
    last = json.loads(state_p.read_text()) if state_p.exists() else {}
    last |= {n: now[n] for n in names if n in now}
    root.mkdir(parents=True, exist_ok=True)
    state_p.write_text(json.dumps(last, indent=1))
    return {"surveyed": out, "lines": [f"{r['sheet']}  failed tiles: {r['failed']}/{r['tiles']}  tiles in {r['tiles_dir']}  ({r['s']} s; page {r['page_calls_s']} s)" for r in out],
            "total_s": round(time.time() - t0, 1)}
