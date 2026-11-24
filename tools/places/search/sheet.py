"""A contact sheet: the top hits' thumbnails in one image, each captioned with its rank, key, editor id and which
half of the search matched (or why it could not be looked at), so an agent looks at 48 candidates in one read."""
from __future__ import annotations

import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from tools.places.search import look
from tools.places.search.index import Index

CELL = 256
CAP = 40
COLS = 8


def _font(size: int):
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


def hits_for_keys(keys: list[str]) -> list[dict]:
    ix = Index.open()
    by = {r["key"]: r for r in ix.rows}
    st = ix.look_status()
    out = []
    for k in keys:
        r = dict(by.get(k) or {"key": k, "edid": "(not in the index)"})
        if r.get("model"):
            mk = look.model_key(r["model"])
            p = look.thumb_path(mk)
            r["look"] = str(p) if p.exists() else None
            r["look_why"] = (st.get(mk) or {}).get("why")
        out.append(r)
    return out


def make(query: str | None, keys: list[str] | None, n: int = 48, out: str | None = None,
         kind: str | None = None) -> Path:
    hits = hits_for_keys(keys) if keys else Index.open().query(query or "", kind=kind, limit=n)
    hits = hits[:n]
    cols = min(COLS, max(len(hits), 1))
    rows = math.ceil(max(len(hits), 1) / cols)
    sheet = Image.new("RGB", (cols * CELL, rows * (CELL + CAP)), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    f = _font(12)
    for i, h in enumerate(hits):
        x, y = (i % cols) * CELL, (i // cols) * (CELL + CAP)
        p = h.get("look")
        if p and Path(p).exists():
            sheet.paste(Image.open(p).convert("RGB").resize((CELL, CELL)), (x, y))
        else:
            d.rectangle((x + 2, y + 2, x + CELL - 2, y + CELL - 2), outline=(200, 0, 0))
            d.text((x + 8, y + CELL // 2), "NO THUMBNAIL", fill=(200, 0, 0), font=f)
        why = h.get("look_why")
        if why:
            d.text((x + 4, y + 4), ("COULD NOT LOOK: " + why)[:40], fill=(200, 0, 0), font=f)
        d.text((x + 4, y + CELL + 2), f"{i + 1}. {(h.get('edid') or '')[:34]}", fill=(0, 0, 0), font=f)
        tag = f" [{h['matched']}]" if h.get("matched") else ""
        d.text((x + 4, y + CELL + 20), f"{h['key'].split(':')[-1]} {h['key'].split(':')[0][:18]}{tag}",
               fill=(90, 90, 90), font=f)
    if out is None:
        slug = re.sub(r"[^a-z0-9]+", "-", (query or "keys").lower()).strip("-")[:40] or "sheet"
        out = str(look.look_dir() / "sheets" / f"{slug}.webp")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=80) if out.endswith((".webp", ".jpg")) else sheet.save(out)
    return Path(out)


