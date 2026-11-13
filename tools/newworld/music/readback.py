"""Read-back rows for what the player hears and is told where he is, judged from the world file's dump
(ArgoniaPlugin `nwverify dump`: header.json `regions`, `music_types`, `locations`, `world`; cells.tsv `region`,
`location`). Called by tools/newworld/verify.py (groups `music` and `location`).

Music (docs/design/music.md "In game"): a cell plays its region's music type (REGN RDMO), else the world's (WRLD
ZNAM); combat, death, level-up and discovery are Skyrim's default types (MUSCombat ...). A track plays only when its
file is laid and its conditions can hold. A music track has no subject: an actor condition on it holds only when run
on a reference (Skyrim runs its tracks' actor conditions on PlayerRef 000014); run on the subject it never holds.

Where the player is (Skyrim's way): a cell's location (XLCN) is what the map menu, the save list and the journal name
as "here"; a location's parent is the larger area (WhiterunLocation -> WhiterunHoldLocation "Whiterun Hold"). Each
region has a location of its name under the world's, set on every cell of the region."""
from __future__ import annotations

PLAYER = "000014:Skyrim.esm"
ACTOR_FNS = {"GetInWorldspace", "GetInCurrentLocation", "GetIsID", "HasKeyword", "GetInCell"}
DEFAULT_TYPES = ("MUSCombat", "MUSCombatBoss", "MUSSpecialDeath", "MUSSpecialSuccess", "MUSDiscoveryGeneric")


def music_key(path: str) -> str:
    """A track's file (`Data\\Music\\argonia\\x.wav`) as a data path (`music\\argonia\\x.wav`)."""
    p = path.replace("/", "\\").lower().lstrip("\\")
    return p[5:] if p.startswith("data\\") else p


def plays_in(track: dict, world: str, has) -> bool:
    """Whether a track can play in the world: its file is laid, every actor condition runs on the player, and its
    GetInWorldspace conditions (on the world) admit this world. OR-joined conditions are read as Skyrim's only use
    (GetCurrentTime spans), which never shut a world out."""
    if track.get("type") == "missing":
        return False
    if track.get("type") != "SingleTrack" or not track.get("file"):
        return False   # palettes and silent spacers do not count as a track that plays
    if not has(music_key(track["file"])):
        return False
    for c in track.get("conds") or []:
        if c["fn"] in ACTOR_FNS and not (c["runon"] == "Reference" and c.get("reference") == PLAYER):
            return False
        if c["fn"] == "GetInWorldspace" and c["op"] == "EqualTo" and not c["or"]:
            if (c["value"] == 1) != (c.get("world") == world):
                return False
    return True


def music_rows(H: dict, cells: dict, has) -> list[tuple]:
    """(requirement, value, ok, detail) rows."""
    types = H.get("music_types") or {}
    w = H.get("world") or {}
    world = w.get("form_key") or ""
    reg_music = {r["edid"]: r.get("music") for r in H.get("regions") or []}
    playable = {t: sum(plays_in(tr, world, has) for tr in v["tracks"]) for t, v in types.items()}
    silent, by = [], {}
    for k, c in cells.items():
        t = reg_music.get(c.get("region") or "") or w.get("music")
        by[t] = by.get(t, 0) + 1
        if not t or not playable.get(t):
            silent.append(k)
    rows = [("every exterior cell resolves to a music type with a track that plays (file laid, conditions can hold)",
             f"{len(cells) - len(silent)}/{len(cells)}", bool(cells) and not silent,
             f"silent e.g. {sorted(silent)[:4]}" if silent else ", ".join(f"{t} {n}" for t, n in sorted(by.items(), key=str)))]
    for t in DEFAULT_TYPES:
        tracks = (types.get(t) or {}).get("tracks") or []
        ours = [tr["edid"] for tr in tracks if plays_in(tr, world, has)]
        theirs = [tr["edid"] for tr in tracks if tr.get("edid") and not tr["edid"].startswith("ANW_") and plays_in(tr, world, has)]
        rows.append((f"{t} plays our pieces in the new world, none of Skyrim's", f"{len(ours) - len(theirs)} ours, {len(theirs)} Skyrim's",
                     bool(ours) and not theirs, f"Skyrim's playing: {theirs[:3]}" if theirs else ""))
    return rows


def location_rows(H: dict, cells: dict) -> list[tuple]:
    locs = {l["edid"]: l for l in H.get("locations") or []}
    names = {r["edid"]: r.get("map_name") for r in H.get("regions") or []}
    wrong = []
    for k, c in cells.items():
        loc = locs.get(c.get("location") or "")
        if not c.get("region"):
            continue
        if loc is None or not loc.get("name") or loc["name"] != names.get(c["region"]):
            wrong.append(k)
    top = {l["parent"] for l in locs.values() if l["edid"] != "ANW_Loc_World"}
    rows = [("every cell's location (XLCN) is named for its region", f"{len(cells) - len(wrong)}/{len(cells)}",
             bool(cells) and not wrong, f"e.g. {sorted(wrong)[:4]}" if wrong else ""),
            ("each region's location has the world's location as parent", sorted(top, key=str), top == {"ANW_Loc_World"}, "")]
    return rows
