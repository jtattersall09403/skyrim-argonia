"""The item, container, levelled-list and actor records stocking reads, from the plugins themselves (the bundles
carry models and keywords but no values, contents or enchantments).

    from tools.places.stock.records import Records
    r = Records.load(["Skyrim.esm", "Update.esm", ..., "Black Marsh North.esp"])   # load order, masters first
    r.item("Skyrim.esm:01397E")   -> {key, sig, edid, name, value, weight, keywords, ench, ...} or None
    r.cont(key) / r.lvli(key) / r.npc(key) / r.outfit(key)
    r.expand(key, level=1)        -> [(item_key, count, chance)]: what a base gives at a fixed level

Keys are the places' shape, "<Plugin>:<6 hex>". A later plugin's record wins, as in the game. Nothing read here is
written anywhere but derived values (keys, editor ids, names, numbers).
"""
from __future__ import annotations

import re
import struct
from functools import lru_cache
from pathlib import Path

from tools.argonia_world import esm

ITEM_SIGS = ("WEAP", "ARMO", "MISC", "BOOK", "ALCH", "INGR", "AMMO", "SLGM", "KEYM", "SCRL", "LIGH")
SIGS = set(ITEM_SIGS) | {"CONT", "LVLI", "NPC_", "OTFT", "KYWD", "FACT", "ENCH", "GLOB"}

# ALCH/INGR ENIT flags (UESP Skyrim Mod:Mod File Format/ALCH)
ALCH_FOOD, ALCH_MEDICINE, ALCH_POISON = 0x2, 0x10000, 0x20000
# BOOK DATA flags
BOOK_SKILL, BOOK_SPELL = 0x1, 0x4
# LVLI LVLF flags
LVL_ALL_LEVELS, LVL_EACH, LVL_USE_ALL = 0x1, 0x2, 0x4
# CONT DATA flags
CONT_RESPAWNS = 0x2
GOLD = "Skyrim.esm:00000F"


def place_key(form_key: str) -> str:
    """esm.py's "06X:Plugin" to the places' "Plugin:06X"."""
    hexid, plugin = form_key.split(":", 1)
    return f"{plugin}:{hexid}"


def _u32(d: bytes | None, off: int = 0) -> int | None:
    return struct.unpack_from("<I", d, off)[0] if d and len(d) >= off + 4 else None


def _i32(d: bytes | None, off: int = 0) -> int | None:
    return struct.unpack_from("<i", d, off)[0] if d and len(d) >= off + 4 else None


def _f32(d: bytes | None, off: int = 0) -> float | None:
    return round(struct.unpack_from("<f", d, off)[0], 3) if d and len(d) >= off + 4 else None


class Records:
    def __init__(self):
        self.raw: dict[str, esm.Record] = {}
        self.kw: dict[str, str] = {}

    @classmethod
    def load(cls, plugins: list[str | Path], dirs: list[str] | None = None) -> "Records":
        from tools.places.extract import find_plugin, search_dirs
        dirs = dirs or search_dirs()
        self = cls()
        for name in plugins:
            path = Path(name) if Path(name).is_absolute() else find_plugin(str(name), dirs)
            p = esm.Plugin.read(path, SIGS)
            for rec in p.records():
                self.raw[place_key(rec.key)] = rec
        self.kw = {k: r.edid or k for k, r in self.raw.items() if r.sig == "KYWD"}
        return self

    def _ref(self, rec: esm.Record, d: bytes | None, off: int = 0) -> str | None:
        v = _u32(d, off)
        return place_key(rec.plugin.form_key(v)) if v else None

    def sig(self, key: str) -> str | None:
        r = self.raw.get(key)
        return r.sig if r else None

    def edid(self, key: str) -> str | None:
        r = self.raw.get(key)
        return r.edid if r else None

    @lru_cache(maxsize=None)
    def item(self, key: str) -> dict | None:
        rec = self.raw.get(key)
        if rec is None or rec.sig not in ITEM_SIGS:
            return None
        kws = []
        d = rec.sub("KWDA")
        if d:
            kws = [self.kw.get(place_key(rec.plugin.form_key(v)), place_key(rec.plugin.form_key(v)))
                   for v in struct.unpack_from(f"<{len(d) // 4}I", d)]
        out = {"key": key, "sig": rec.sig, "edid": rec.edid, "name": rec.name, "keywords": kws,
               "ench": self._ref(rec, rec.sub("EITM")), "value": 0, "weight": 0.0}
        g = re.search(r"(\d\d)$", self.edid(out["ench"]) or "") if out["ench"] else None
        if g:   # the enchantment's grade, by vanilla's naming of its enchantments (EnchWeaponShockDamage03 is 3)
            out["ench_grade"] = int(g.group(1))
        data = rec.sub("DATA")
        if rec.sig in ("WEAP", "ARMO", "MISC", "SLGM", "KEYM", "SCRL"):
            out["value"], out["weight"] = _i32(data) or 0, _f32(data, 4) or 0.0
            if rec.sig == "WEAP" and data and len(data) >= 10:
                out["damage"] = struct.unpack_from("<H", data, 8)[0]
            if rec.sig == "ARMO":
                out["rating"] = (_i32(rec.sub("DNAM")) or 0) / 100
                out["slots"] = _u32(rec.sub("BOD2") or rec.sub("BODT")) or 0   # biped slot flags
            if rec.sig == "SLGM":
                out["soul"] = (rec.sub("SOUL") or b"\0")[0]
                out["capacity"] = (rec.sub("SLCP") or b"\0")[0]
        elif rec.sig == "BOOK" and data and len(data) >= 16:
            flags = data[0]
            out["value"], out["weight"] = _u32(data, 8) or 0, _f32(data, 12) or 0.0
            if flags & BOOK_SPELL:
                out["teaches"] = {"spell": self._ref(rec, data, 4)}
            elif flags & BOOK_SKILL:
                out["teaches"] = {"skill": _i32(data, 4)}
        elif rec.sig in ("ALCH", "INGR"):
            enit = rec.sub("ENIT")
            if rec.sig == "ALCH":          # DATA is the weight; ENIT starts with the value
                out["value"], out["weight"] = _i32(enit) or 0, _f32(data) or 0.0
            else:                          # DATA is value and weight; ENIT the effects' own value and flags
                out["value"], out["weight"] = _i32(data) or 0, _f32(data, 4) or 0.0
            f = _u32(enit, 4) or 0
            out["food"] = bool(f & ALCH_FOOD) if rec.sig == "ALCH" else False
            out["poison"] = bool(f & ALCH_POISON)
        elif rec.sig == "AMMO":
            out["value"] = _u32(data, 12) or 0
            out["weight"] = _f32(data, 16) or 0.0
        elif rec.sig == "LIGH":
            out["value"], out["weight"] = (_u32(data, 40) or 0, _f32(data, 44) or 0.0) if data and len(data) >= 48 else (0, 0.0)
            out["carried"] = bool(data and len(data) >= 16 and (_u32(data, 12) or 0) & 0x2)
        return out

    def _cnto(self, rec: esm.Record) -> list[tuple[str, int]]:
        out = []
        for d in rec.all("CNTO"):
            k = self._ref(rec, d)
            if k:
                out.append((k, _i32(d, 4) or 1))
        return out

    @lru_cache(maxsize=None)
    def cont(self, key: str) -> dict | None:
        rec = self.raw.get(key)
        if rec is None or rec.sig != "CONT":
            return None
        data = rec.sub("DATA")
        return {"key": key, "edid": rec.edid, "name": rec.name, "model": (rec.zstr("MODL") or "").lower(),
                "items": self._cnto(rec), "respawns": bool(data and data[0] & CONT_RESPAWNS)}

    @lru_cache(maxsize=None)
    def lvli(self, key: str) -> dict | None:
        rec = self.raw.get(key)
        if rec is None or rec.sig != "LVLI":
            return None
        entries = []
        for d in rec.all("LVLO"):
            if len(d) >= 10:
                lvl = struct.unpack_from("<H", d, 0)[0]
                entries.append((lvl, self._ref(rec, d, 4), struct.unpack_from("<H", d, 8)[0]))
        chance = (rec.sub("LVLD") or b"\0")[0]
        glob = self._ref(rec, rec.sub("LVLG"))
        if glob and glob in self.raw:
            v = _f32(self.raw[glob].sub("FLTV"))
            chance = int(v) if v is not None else chance
        return {"key": key, "edid": rec.edid, "flags": (rec.sub("LVLF") or b"\0")[0], "chance_none": chance,
                "entries": entries}

    @lru_cache(maxsize=None)
    def npc(self, key: str) -> dict | None:
        rec = self.raw.get(key)
        if rec is None or rec.sig != "NPC_":
            return None
        acbs = rec.sub("ACBS")
        facts = []
        for d in rec.all("SNAM"):
            f = self._ref(rec, d)
            facts.append({"faction": f, "edid": self.edid(f) if f else None, "rank": d[4] if len(d) > 4 else 0})
        return {"key": key, "edid": rec.edid, "name": rec.name, "items": self._cnto(rec),
                "outfit": self._ref(rec, rec.sub("DOFT")), "template": self._ref(rec, rec.sub("TPLT")),
                "death_item": self._ref(rec, rec.sub("INAM")),
                "level": struct.unpack_from("<h", acbs, 8)[0] if acbs and len(acbs) >= 10 else None,
                "pc_level_mult": bool(acbs and _u32(acbs) & 0x80),
                "class": self._ref(rec, rec.sub("CNAM")), "factions": facts}

    @lru_cache(maxsize=None)
    def outfit(self, key: str) -> list[str]:
        rec = self.raw.get(key)
        if rec is None or rec.sig != "OTFT":
            return []
        d = rec.sub("INAM") or b""
        return [place_key(rec.plugin.form_key(v)) for v in struct.unpack_from(f"<{len(d) // 4}I", d) if v]

    def fixed(self, key: str, _depth: int = 0) -> list[tuple[str, int]]:
        """What the build makes of a base at level 1, the one pick the writer takes (ArgoniaPlaces People.Fixed): a
        levelled list's level-1 entries (its lowest entry when none is level 1), every one when it gives all, else the
        first; nested lists the same way. Not a list: the base itself."""
        lv = self.lvli(key)
        if lv is None:
            return [(key, 1)]
        if _depth > 8:
            return []
        entries = [e for e in lv["entries"] if e[1]]
        low = [e for e in entries if e[0] <= 1] or sorted(entries, key=lambda e: e[0])[:1]
        if not lv["flags"] & LVL_USE_ALL:
            low = low[:1]
        out: list[tuple[str, int]] = []
        for _lvl, k, n in low:
            out += [(x, c * max(1, n)) for x, c in self.fixed(k, _depth + 1)]
        return out

    def expand(self, key: str, level: int = 1, count: float = 1.0, chance: float = 1.0,
               _depth: int = 0) -> list[tuple[str, float, float]]:
        """Every item a base can give at `level`: (item key, count, chance of it). A levelled list yields each
        entry it can pick at that level with its share of the pick (use-all lists every entry at full chance)."""
        if _depth > 12:
            return []
        lv = self.lvli(key)
        if lv is None:
            return [(key, count, chance)]
        ok = [e for e in lv["entries"] if e[1] and e[0] <= level]
        if not lv["flags"] & LVL_ALL_LEVELS and ok:
            top = max(e[0] for e in ok)
            ok = [e for e in ok if e[0] == top]
        if not ok:
            return []
        live = chance * (1 - lv["chance_none"] / 100)
        share = 1.0 if lv["flags"] & LVL_USE_ALL else 1.0 / len(ok)
        out = []
        for _lvl, k, n in ok:
            out += self.expand(k, level, count * n, live * share, _depth + 1)
        return out
