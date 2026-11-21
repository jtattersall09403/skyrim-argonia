"""`look <place> versus <other place>`: two places on one source seen the same way, on one sheet: from straight above
and at eye level from the four sides, each place's middle (`place.json` `fit.anchor`) as the subject. The confirming
look at hand-over that the two do not feel like clones (skill place-check)."""
from __future__ import annotations

import json
from pathlib import Path

VIEWS = (("top", ["--top"]), ("north", ["--eye", "--from", "n"]), ("east", ["--eye", "--from", "e"]),
         ("south", ["--eye", "--from", "s"]), ("west", ["--eye", "--from", "w"]))
TILE = (480, 360)


def middle(place_id: str, places: Path | None = None) -> str:
    from tools.places.draft import io
    p = json.loads(((places or io.PLACES) / place_id / "place.json").read_text())
    a = (p.get("fit") or {}).get("anchor")
    if not a:
        raise SystemExit(f"versus: {place_id} has no fit.anchor (no baseline laid)")
    return f"{a[0]:.0f},{a[1]:.0f}"


def sheet(rows: list[tuple[str, list[tuple[str, str | None]]]], out: Path) -> Path:
    """One row per place, one tile per view, each labelled; a missing image is a grey tile saying so."""
    from PIL import Image, ImageDraw
    w, h = TILE
    img = Image.new("RGB", (w * len(VIEWS), (h + 24) * len(rows)), "white")
    d = ImageDraw.Draw(img)
    for r, (place, tiles) in enumerate(rows):
        for c, (name, png) in enumerate(tiles):
            x, y = c * w, r * (h + 24)
            d.text((x + 6, y + 4), f"{place}: {name}", fill="black")
            if png and Path(png).exists():
                img.paste(Image.open(png).convert("RGB").resize(TILE), (x, y + 24))
            else:
                d.rectangle([x, y + 24, x + w - 1, y + 24 + h - 1], fill="#ccc")
                d.text((x + 6, y + 40), "no capture", fill="black")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def run(place: str, other: str, call, places: Path | None = None, out_dir: Path | None = None) -> dict:
    """`call(place, verb, args)` -> the look reply; returns {"png": the sheet, "views": per place, per view}."""
    if out_dir is None:
        from tools.places.look import LOOK_OUT
        out_dir = Path(LOOK_OUT)
    rows, views = [], {}
    for p in (place, other):
        mid = middle(p, places)
        tiles = []
        for name, args in VIEWS:
            got = call(p, "at", [mid, *args])
            tiles.append((name, got.get("png")))
            views.setdefault(p, {})[name] = {"png": got.get("png"), "capture": got.get("capture")}
        rows.append((p, tiles))
    png = sheet(rows, out_dir / place / f"versus-{other}.png")
    return {"ok": True, "png": str(png), "views": views}
