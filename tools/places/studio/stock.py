"""What a place holds and who its people are, for the studio (docs/design/place-studio.md, Stock: the studio).

Read from the database's own sources (`newworld/sources/`), the shape the studio's edit ops carry and finalise writes
back: the people source, the place's stock source, the measured item catalogue (`items.json`), the scale and the
place's wealth. Item names come from the asset catalogue (`out/places/catalogue/bases.jsonl`). Pure Python, no
server: the studio server and the dev server both call it.

    payload(place_id, sources, catalogue)            -> GET /api/place/<id>/stock
    search(place_id, q, kind, limit, sources, catalogue) -> GET /api/place/<id>/items
"""
from __future__ import annotations

import json
import re
import threading
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ITEM_SIGS = ("WEAP", "ARMO", "AMMO", "ALCH", "BOOK", "SCRL", "SLGM", "KEYM", "INGR", "MISC", "LIGH")
GOLD = "Skyrim.esm:00000F"   # coin is a holder's `gold`, never an item row
ITEM_LINE = re.compile(r'"type":\s*"(' + "|".join(ITEM_SIGS) + ')"')


def _json(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


class Sources:
    """newworld/sources (or a fixture's copy of its layout)."""

    def __init__(self, root: Path | None = None):
        self.root = Path(root or REPO / "newworld" / "sources")

    def people(self, pid: str) -> dict:
        return _json(self.root / "people" / f"{pid}.json") or {"place_id": pid, "households": [], "people": []}

    def lookups(self) -> dict:
        return _json(self.root / "people" / "lookups.json") or {}

    def stock(self, pid: str) -> dict:
        return _json(self.root / "stock" / "places" / f"{pid}.json") or {
            "place_id": pid, "goods": [], "containers": [], "loose": [], "possessions": [], "traders": [],
            "deliveries": []}

    def scale(self) -> dict:
        return _json(self.root / "stock" / "scale.json") or {}

    def measured(self) -> dict:
        return {i["id"]: i for i in (_json(self.root / "stock" / "items.json") or {}).get("items", [])}

    def wealth(self, pid: str) -> dict | None:
        rows = (_json(self.root / "stock" / "place_wealth.json") or {}).get("places", [])
        return next((r for r in rows if r.get("id") == pid), None)


class Catalogue:
    """The asset catalogue's item rows by key, read once and again when the file changes (off the event loop)."""
    _open: dict[str, "Catalogue"] = {}
    _lock = threading.Lock()

    def __init__(self, path: Path):
        self.path, self.rows, self.mtime = Path(path), {}, None

    @classmethod
    def open(cls, path: Path) -> "Catalogue":
        with cls._lock:
            c = cls._open.setdefault(str(path), cls(path))
            try:
                m = c.path.stat().st_mtime
            except OSError:
                m = None
            if m != c.mtime:
                rows = {}
                if m is not None:
                    with c.path.open(encoding="utf-8") as f:
                        for line in f:
                            if not ITEM_LINE.search(line):   # a cheap look before the parse: 12k of 39k rows
                                continue
                            r = json.loads(line)
                            if r.get("type") in ITEM_SIGS:
                                rows[r["key"]] = {k: r.get(k) for k in ("key", "edid", "name", "type", "keywords", "plugin")}
                c.rows, c.mtime = rows, m
            return c


# ---------- what the scale says of an item ----------

def tier_rank(scale: dict) -> dict:
    return {t["id"]: t.get("rank", i + 1) for i, t in enumerate(scale.get("tiers", []))}


def _listed_tier(row: dict, scale: dict) -> tuple[str | None, str]:
    """The lowest tier whose lists name the item's material or the item itself, with how it was found."""
    kws, edid = set(row.get("keywords") or []), row.get("edid") or ""
    for t in scale.get("tiers", []):
        mat = next((k for k in t.get("weapon", []) + t.get("armour", []) if k in kws), None)
        if mat:
            return t["id"], f"its material ({mat})"
        if edid and (edid == t.get("soul_gem") or edid in t.get("gem", []) or edid in t.get("jewellery", [])):
            return t["id"], "the scale's list for that tier"
    return None, ""


def never_of(row: dict, scale: dict) -> str | None:
    """Why the item may not be used (decision 0006), or None."""
    nv = scale.get("never") or {}
    mat = next((k for k in row.get("keywords") or [] if k in set(nv.get("materials", []))), None)
    if mat:
        return f"{mat} is Skyrim's own gear, which has no road into Black Marsh (decision 0006)"
    edid = (row.get("edid") or "").lower()
    word = next((w for w in nv.get("edid_words", []) if w.lower() in edid), None)
    if word:
        return f"it is {word} gear, Skyrim's own, which has no road into Black Marsh (decision 0006)"
    return None


def item_facts(key: str, measured: dict | None, cat: dict | None, scale: dict) -> dict:
    """{id, edid, name, kind, record, value, tier, significant, never, measured, why_tier}: measured by `stockdb
    items` when it has run on the item; else read from the catalogue row (no value there: the tier from the item's
    material or the scale's lists, else unknown until finalise measures it)."""
    cat = cat or {}
    if measured:
        nv = never_of(cat or {"edid": measured.get("edid"), "keywords": [measured.get("material")] if measured.get("material") else []}, scale)
        return {"id": key, "edid": measured.get("edid"), "name": cat.get("name") or measured.get("name") or measured.get("edid"),
                "kind": measured.get("item_kind_id"), "record": measured.get("record"), "value": measured.get("value"),
                "tier": measured.get("stock_tier_id"), "significant": bool(measured.get("significant")),
                "never": nv or ("on the scale's never list (decision 0006)" if measured.get("never") else None),
                "measured": True, "why_tier": "measured from the plugins"}
    from tools.places.stock import split
    it = {"key": key, "sig": cat.get("type") or "MISC", "edid": cat.get("edid"), "name": cat.get("name"),
          "keywords": cat.get("keywords") or [], "value": 0, "ench": None}
    try:
        kind, sig, _ = split.item_class(it, scale.get("split") or split.rules())
    except (KeyError, TypeError):
        kind, sig = "clutter", False
    tier, how = _listed_tier(cat, scale)
    return {"id": key, "edid": cat.get("edid"), "name": cat.get("name") or cat.get("edid") or key, "kind": kind,
            "record": cat.get("type"), "value": None, "tier": tier, "significant": sig, "never": never_of(cat, scale),
            "measured": False, "why_tier": (f"from {how}" if tier else "not measured yet: finalise measures it")}


def allowed(facts: dict, ceiling: str | None, scale: dict) -> tuple[bool, str]:
    """May the place hold this item? Never-list items and items above the place's ceiling are refused, each with
    its reason. A tier not yet known is allowed and said so. The words are js/stock.js allowedItem's."""
    if facts.get("never"):
        return False, f"Not allowed: {facts['never']}."
    rank = tier_rank(scale)
    t = facts.get("tier")
    tl = lambda x: f"{x} {_label(scale, x)}"   # noqa: E731
    if t and ceiling and rank.get(t, 0) > rank.get(ceiling, 99):
        return False, f"Not allowed: it is {tl(t)}, above this place's ceiling {tl(ceiling)}."
    if not t:
        return True, "Allowed; its tier is not measured yet."
    return True, f"Allowed: {tl(t)}, within this place's ceiling {ceiling or 'none'}."


def wealth_facts(row: dict | None, scale: dict) -> dict | None:
    """The place's wealth as the database loads it (tools/newworld/wealth.py load): the owner's overrule first."""
    if not row:
        return None
    rank = {t["id"]: t.get("rank", 0) for t in scale.get("tiers", [])}
    band_ceiling = {b["id"]: b.get("ceiling_tier") for b in scale.get("place_wealth_bands", [])}
    o = row.get("owner") or {}
    band = o.get("band", row.get("band"))
    if o.get("ceiling_tier"):
        ceiling = o["ceiling_tier"]
    elif "band" in o:
        ceiling = max(row.get("danger_tier") or "T1", band_ceiling.get(band) or "T1", key=lambda t: rank.get(t, 0))
    else:
        ceiling = row.get("ceiling_tier")
    label = next((b.get("label") for b in scale.get("place_wealth_bands", []) if b["id"] == band), None)
    return {"place_id": row.get("id"), "name": row.get("name"), "band": band, "band_label": label,
            "open_tier": row.get("open_tier"), "ceiling_tier": ceiling, "ceiling_label": _label(scale, ceiling) if ceiling else None,
            "why": f"owner: {o['why']} (derived: {row.get('why')})" if o else row.get("why"), "by": "owner" if o else "derived"}


def _label(scale: dict, t: str) -> str:
    return next((x.get("label", t) for x in scale.get("tiers", []) if x["id"] == t), t)


# ---------- the payload ----------

def item_keys(stock: dict) -> set[str]:
    keys = {i["item"] for c in stock.get("containers", []) for i in c.get("items", [])}
    keys |= {lo["item"] for lo in stock.get("loose", [])}
    for h in stock.get("possessions", []) + stock.get("traders", []):
        keys |= {i["item"] for i in h.get("items", [])}
    return keys


def scale_view(scale: dict) -> dict:
    """What the studio shows of the scale: tiers, bands, security, locks, kinds (no long lists)."""
    keep = lambda rows, ks: [{k: r.get(k) for k in ks if k in r} for r in rows]   # noqa: E731
    split = scale.get("split") or {}
    return {"tiers": keep(scale.get("tiers", []), ("id", "rank", "label", "lock", "gold", "value_max", "about")),
            "place_wealth_bands": keep(scale.get("place_wealth_bands", []), ("id", "rank", "label", "ceiling_tier", "about")),
            "person_wealth_bands": keep(scale.get("person_wealth_bands", []), ("id", "rank", "label", "carried", "home", "top_tier", "about")),
            "security": keep(scale.get("security", []), ("id", "label", "means", "holds_up_to")),
            "lock_levels": list((scale.get("lock_level") or {}).keys()),
            "effort": keep(scale.get("effort", []), ("id", "means", "tier")),
            "container_kinds": [[k, ws] for k, ws in split.get("container_kinds", [])],
            "always_significant_containers": split.get("always_significant_containers", []),
            "never_why": (scale.get("never") or {}).get("why")}


def payload(pid: str, sources: Sources, catalogue: Catalogue | None = None) -> dict:
    scale, stock = sources.scale(), sources.stock(pid)
    measured, cat = sources.measured(), (catalogue.rows if catalogue else {})
    items = {k: item_facts(k, measured.get(k), cat.get(k), scale) for k in sorted(item_keys(stock))}
    lk = sources.lookups()
    return {"place_id": pid, "facts": wealth_facts(sources.wealth(pid), scale), "identities": sources.people(pid), "stock": stock,
            "items": items, "scale": scale_view(scale),
            "lookups": {k: lk.get(k, []) for k in ("race", "person_role", "household_role", "relation_kind")}}


def _squash(s) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s or "").lower())


def _words(s) -> set[str]:
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(s or ""))
    return {w for w in re.split(r"[^a-z0-9]+", s.lower()) if w}


def search(pid: str, q: str, kind: str | None, limit: int, sources: Sources, catalogue: Catalogue | None) -> dict:
    """Items by name or editor id, best first, each with its tier and whether this place may hold it (a refused
    item is listed with its reason, never hidden). Capped at `limit`."""
    scale, measured = sources.scale(), sources.measured()
    rows = dict(catalogue.rows if catalogue else {})
    for k, m in measured.items():   # an item stocking names that the catalogue lacks is still found
        rows.setdefault(k, {"key": k, "edid": m.get("edid"), "name": m.get("name"), "type": m.get("record"),
                            "keywords": [m["material"]] if m.get("material") else [], "plugin": m.get("plugin")})
    ceiling = (wealth_facts(sources.wealth(pid), scale) or {}).get("ceiling_tier")
    sq, qw = _squash(q), _words(q)
    kinds = set(filter(None, (kind or "").split(",")))
    hits = []
    if sq:
        for k, r in rows.items():
            if k == GOLD or not (r.get("name") or r.get("edid")):
                continue
            n, e = _squash(r.get("name")), _squash(r.get("edid"))
            if sq in (n, e):
                s = 3.0
            elif n.startswith(sq) or e.startswith(sq):
                s = 2.0
            elif qw and qw <= (_words(r.get("name")) | _words(r.get("edid"))):
                s = 1.0
            elif sq in n or sq in e:
                s = 0.5
            else:
                continue
            hits.append((s + (0.25 if r.get("name") else 0), k, r))
    hits.sort(key=lambda h: (-h[0], str(h[2].get("name") or h[2].get("edid")), h[1]))
    out = []
    for s, k, r in hits:
        f = item_facts(k, measured.get(k), r, scale)
        if kinds and f["kind"] not in kinds:
            continue
        ok, why = allowed(f, ceiling, scale)
        out.append(f | {"allowed": ok, "why": why, "score": s})
        if len(out) >= limit:
            break
    return {"q": q, "ceiling": ceiling, "results": out}
