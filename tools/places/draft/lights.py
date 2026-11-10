"""A place's light: every light with its fixture, what we add lit as Skyrim lights it, each room's own lights.

- A light belongs to its fixture. A light has no body, so nothing ties it to the lantern, sconce, window or fire it
  was placed for but nearness: the nearest fixture within BIND units in the source is its fixture (`fixtures`). It
  shares that fixture's cluster, stands at its source offset from it turned with the cluster (`follow`), is seated
  `on` it (`seat`), and is left out when its fixture is.
- What we add is lit as Skyrim lights it (measured on Skyrim.esm's exteriors): a forge carries LightForgeFire01 (15 of
  24 placed forges, median offset FORGE_OFFSET in the forge's own frame); a smelter (0 of 21) and an alchemy lab (3 of
  16) carry none (`station_lights`).
- A copied room keeps the source's own lights as they are, shadow casters among them: there is no cap on
  shadow-casting lights in a room (the player's renderer settings decide how many it draws). A light of a room is
  never switched to another base for its shadows.
"""
from __future__ import annotations

import math
import re

from tools.places.draft import io

FIXTURE = re.compile(r"lantern|sconce|candle|torch|brazier|fire|window|light|lamp|chandel", re.I)
NOT_FIXTURE = {"light", "actor", "water", "marker", "tree", "plant", "groundcover", "rock"}
BIND = 128.0          # a light within this of a fixture in the source is that fixture's
OFFSET_TOL = 16.0     # how far a light may stand off its source offset from its fixture
FORGE_LIGHT = "Skyrim.esm:0B15EE"         # LightForgeFire01
FORGE_OFFSET = (-16.0, 167.0, 84.0)       # its median place in the forge's own frame, 15 vanilla forges
STATION_LIGHT = {"forge": (FORGE_LIGHT, FORGE_OFFSET)}


def is_fixture(r: dict, bases: dict) -> bool:
    b = bases.get(r.get("base")) or {}
    return r.get("kind") not in NOT_FIXTURE and bool(FIXTURE.search(f"{b.get('edid') or ''} {b.get('model') or ''}"))


def fixtures(refs: list[dict], bases: dict) -> dict[str, str]:
    """{light ref id: its fixture's ref id} over one space's source refs."""
    fx = [r for r in refs if is_fixture(r, bases)]
    grid: dict[tuple, list] = {}
    for f in fx:
        grid.setdefault((int(f["pos"][0] // BIND), int(f["pos"][1] // BIND)), []).append(f)
    out = {}
    for r in refs:
        if r.get("kind") != "light":
            continue
        gx, gy = int(r["pos"][0] // BIND), int(r["pos"][1] // BIND)
        near = [(math.dist(r["pos"], f["pos"]), f["id"]) for i in (-1, 0, 1) for j in (-1, 0, 1)
                for f in grid.get((gx + i, gy + j), ())]
        best = min(near, default=None)
        if best and best[0] <= BIND:
            out[r["id"]] = best[1]
    return out


def seat(light: dict, fixture: dict) -> dict:
    """A light's seat rule: `on` its fixture, at its source height over the fixture's origin."""
    return {"mode": "on", "on": fixture["id"], "dz": round(light["pos"][2] - fixture["pos"][2], 2)}


def offset(light: dict, fixture: dict, turn: float) -> tuple[float, float]:
    """The light's source offset from its fixture in plan, turned by the cluster's turn (clockwise, radians)."""
    dx, dy = light["pos"][0] - fixture["pos"][0], light["pos"][1] - fixture["pos"][1]
    c, s = math.cos(turn), math.sin(turn)
    return dx * c + dy * s, -dx * s + dy * c


def plan_shift(row: dict) -> tuple[float, float]:
    """How far a replaced piece was shifted to line its plane up with the original's: its light keeps the offset
    from where the original stood."""
    sh = (row.get("align") or {}).get("shift") or (0.0, 0.0)
    return float(sh[0]), float(sh[1])


def follow(rows: list[dict], by_src: dict[str, dict], bound: dict[str, str], turn_of) -> int:
    """Put every bound light of ours at its source offset from its fixture as the fixture now stands. `rows` are our
    exterior rows; `turn_of(cluster id)` is that cluster's turn. Returns the lights moved."""
    ours = {r["src"]: r for r in rows if r.get("src")}
    n = 0
    for lid, fid in sorted(bound.items()):
        row, f = ours.get(lid), ours.get(fid)
        if row is None or f is None:
            continue
        ox, oy = offset(by_src[lid], by_src[fid], turn_of(f.get("cluster")))
        sx, sy = plan_shift(f)
        x, y = round(f["pos"][0] - sx + ox, 2), round(f["pos"][1] - sy + oy, 2)
        if abs(x - row["pos"][0]) > 0.011 or abs(y - row["pos"][1]) > 0.011:
            row["pos"][0], row["pos"][1] = x, y
            n += 1
    return n


def off_fixture(rows: list[dict], by_src: dict[str, dict], bound: dict[str, str], turn_of) -> list[str]:
    """The check: every bound light of ours stands within OFFSET_TOL of its source offset from its fixture."""
    ours = {r["src"]: r for r in rows if r.get("src")}
    bad = []
    for lid, fid in sorted(bound.items()):
        row, f = ours.get(lid), ours.get(fid)
        if row is None:
            continue
        if f is None:
            bad.append(f"light {row['id']} stands without its fixture {fid}, which is left out")
            continue
        ox, oy = offset(by_src[lid], by_src[fid], turn_of(f.get("cluster")))
        sx, sy = plan_shift(f)
        want = (f["pos"][0] - sx + ox, f["pos"][1] - sy + oy, f["pos"][2] + by_src[lid]["pos"][2] - by_src[fid]["pos"][2])
        d = math.dist(want, row["pos"])
        if d > OFFSET_TOL:
            bad.append(f"light {row['id']} stands {d:.0f} units off its place by its fixture {f['id']}")
    return bad


# --- what we add ---
def station_lights(place_id: str, rows: list[dict], stations: dict) -> list[dict]:
    """The light rows our added stations carry: one per added exterior station whose kind Skyrim lights, at the
    vanilla offset in the station's own frame, seated `on` it."""
    by_id = {r["id"]: r for r in rows}
    out = []
    for a in (stations or {}).get("added") or []:
        lit, st = STATION_LIGHT.get(a.get("station")), by_id.get(a.get("id"))
        if not lit or st is None or a.get("space", "exterior") != "exterior":
            continue
        base, (u, v, w) = lit
        rz = st["rot"][2]
        c, s = math.cos(rz), math.sin(rz)
        out.append({"id": io.mint(place_id, "light", a["id"]), "base": base, "kind": "light",
                    "pos": [round(st["pos"][0] + u * c + v * s, 2), round(st["pos"][1] - u * s + v * c, 2),
                            round(st["pos"][2] + w, 2)],
                    "rot": [0.0, 0.0, 0.0], "scale": 1.0, "layer": "place", "flags": [], "src": None,
                    "seat": {"mode": "on", "on": st["id"], "dz": w}, "cluster": st.get("cluster"),
                    "why": f"the {a['station']}'s fire light, as Skyrim's forges carry it"})
    return [{k: v for k, v in r.items() if v is not None or k == "src"} for r in out]


# --- the load order's lights ---
_lights: dict | None = None


def light_bases(path=None) -> dict[str, dict]:
    """Every light base of the load order (the catalogue's lights.jsonl), by key."""
    global _lights
    p = path or io.CATALOGUE.with_name("lights.jsonl")
    if path is not None:
        return {r["key"]: r for r in io.read_jsonl(p)} if p.exists() else {}
    if _lights is None:
        _lights = {r["key"]: r for r in io.read_jsonl(p)} if p.exists() else {}
    return _lights


def casts(base: dict | None) -> bool:
    return "Shadow" in str(((base or {}).get("light") or {}).get("flags") or "")
