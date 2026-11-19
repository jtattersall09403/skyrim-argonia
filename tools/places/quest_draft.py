"""First spots for a place's quest things (docs/design/place-studio.md, "Quest things"; quests-on-a-world.md §4).

Every quest placement anchored at a new-world place with no row in its `quests.jsonl` gets a drafted row:
`{id, quest, ref, space, pos, rot, drafted: true, why}`. The drafter reads the placement's words (`need`, `room`),
resolves them against the place's own rows (its rooms by name, its pieces by the words of their `why`, its people by
name, the quest things already drafted by name, doors) and puts the thing on the place's walking mesh near what the
words name: a person or creature on a walkable triangle (never water unless the words ask for the shallows), a
thing on the mesh beside its anchor, a door on the door it names. Where the words name nothing the place holds, it
takes a sensible spot (the room's middle, the far end from the door for "back"/"far end", the place's middle
outside) and says so in `why`. A row without `drafted` is the owner's (set or finalised in the studio) and is never
changed; a drafted row stays as drafted until `--redraft`.

    python -m tools.places quest-draft <place_id> [--redraft] [--out out/places]

The walking mesh is the built place's (`navexport`, <out>/nav/<place>.json); a place not built yet uses its streets'
points and its people's spots."""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from tools.places import quest_spots as qs

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out" / "places"
STOP = set("""the a an of and or in on at by to from with its it his her their where who which that this these those
one two three some all any as is are be beside under over into out across near among a few steps step strides
stands stand standing sitting sits side place town camp quest quest's main mn01 mn02 mn03 mn04 mn05 mn06 mn
named showing shows door's from camp's town's place's city's record's""".split())
BACK = re.compile(r"\b(back|far end|farthest|behind|rear)\b")
WET = re.compile(r"\b(shallows|in the water|in the pool|wading|swims?)\b")
GAP = 70.0          # how far two drafted things stand apart at least
KIND_WORDS = {"light": "fire pit campfire hearth lantern", "container": "chest crate barrel sack pack",
              "furniture": "bench seat table bed", "marker": "spot"}
NEAR = (40.0, 220.0)  # a person stands this far from what the words name


def words(s: str) -> list[str]:
    return [w for w in re.findall(r"[a-z][a-z'-]+", str(s or "").lower()) if len(w) > 2 and w not in STOP]


class Mesh:
    """The walkable points of one space: triangle centroids with their kind (0 plain, 1 preferred, 2 water)."""

    def __init__(self, pts: list[tuple[float, float, float, int]], doors: list[tuple[float, float, float]]):
        self.pts, self.doors = pts, doors

    def snap(self, x: float, y: float, z: float | None, wet: bool, taken: list, lo: float = 0.0) -> tuple | None:
        best, bd = None, 1e18
        for p in self.pts:
            if p[3] == 2 and not wet:
                continue
            d = (p[0] - x) ** 2 + (p[1] - y) ** 2 + (0 if z is None else ((p[2] - z) * 0.5) ** 2)
            if d < lo * lo or any((p[0] - t[0]) ** 2 + (p[1] - t[1]) ** 2 < GAP * GAP for t in taken):
                continue
            if d < bd:
                best, bd = p, d
        return best

    def middle(self) -> tuple:
        n = len(self.pts) or 1
        return tuple(sum(p[i] for p in self.pts) / n for i in range(3))

    def far_from_door(self) -> tuple:
        if not self.doors:
            return self.middle()
        d0 = self.doors[0]
        return max(self.pts, key=lambda p: (p[0] - d0[0]) ** 2 + (p[1] - d0[1]) ** 2)[:3]


def meshes(place_id: str, place_dir: Path, out: Path) -> dict[str, Mesh]:
    nav = out / "nav" / f"{place_id}.json"
    res: dict[str, Mesh] = {}
    if nav.exists():
        d = json.loads(nav.read_text())
        for sp, m in d["spaces"].items():
            v, t, k = m["verts"], m["tris"], m["kind"]
            pts = []
            for i in range(len(k)):
                a, b, c = t[3 * i], t[3 * i + 1], t[3 * i + 2]
                pts.append(tuple(sum(v[3 * j + q] for j in (a, b, c)) / 3 for q in range(3)) + (k[i],))
            doors = [pts[ti][:3] for ti, _r in m.get("doors") or [] if ti < len(pts)]
            res[sp] = Mesh(pts, doors)
    if "exterior" not in res:   # not built: its streets and its people's spots
        pts = []
        for p in qs_rows(place_dir / "paths.jsonl"):
            pts += [(q[0], q[1], q[2] if len(q) > 2 else 0.0, 0) for q in p.get("points") or []]
        res["exterior"] = Mesh(pts, [])
    return res


def qs_rows(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()] if p.exists() else []


def anchors(place_dir: Path) -> list[dict]:
    """What the words can name: the place's pieces (by the words of their why and kind), its people by name and
    trade, its rooms' doors by the room's name."""
    out = []
    spaces = {}
    for sj in sorted((place_dir / "spaces").glob("*/space.json")):
        spaces[sj.parent.name] = json.loads(sj.read_text())
    ext_refs = {}
    for sd in sorted((place_dir / "spaces").glob("*")):
        for r in qs_rows(sd / "refs.jsonl"):
            if len(r.get("pos") or []) == 3:
                ext_refs[r["id"]] = r
                out.append({"space": sd.name, "pos": r["pos"],
                            "text": f"{r.get('kind')} {KIND_WORDS.get(r.get('kind'), '')} {r.get('why') or ''}",
                            "what": f"{r.get('kind')} {r['id']}"})
    for sid, s in spaces.items():
        d = ext_refs.get(s.get("door_from"))
        if d and s.get("name"):
            src = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(s.get("copy_of") or "").split("/")[-1])
            out.append({"space": "exterior", "pos": d["pos"], "text": f"door {s['name']} house {src}", "door_of": sid,
                        "what": f"the door of {s['name']}"})
    for p in qs_rows(place_dir / "people.jsonl"):
        for slot in ("work", "bed"):
            at = p.get(slot) or {}
            r = ext_refs.get(at.get("ref"))
            pos = at.get("pos") or (r or {}).get("pos")
            if pos and len(pos) == 3:
                out.append({"space": at.get("space", "exterior"), "pos": pos,
                            "text": f"{p.get('name')} {p.get('role')} " + " ".join(s.get("detail", "") for s in p.get("services") or []),
                            "what": f"{p.get('name')}'s {slot} spot", "person": p.get("name")})
                break
    return out


def score(need: list[str], text: str) -> float:
    """The words the anchor shares with the placement's, the first words (what it stands at) counting most."""
    t = set(words(text))
    return sum(3.0 if i < 3 else 1.0 for i, w in enumerate(dict.fromkeys(need)) if w in t)


def draft(place_id: str, places: Path = qs.PLACES, quests: Path = qs.QUESTS, out: Path = OUT, sources: Path = qs.SOURCES,
          redraft: bool = False, write: bool = True) -> dict:
    place_dir = places / place_id
    d = qs.payload(place_id, places, quests, sources, url="")
    rows = {r["id"]: r for r in qs.read(place_dir)}
    if redraft:
        rows = {k: r for k, r in rows.items() if not r.get("drafted")}
    M = meshes(place_id, place_dir, out)
    A = anchors(place_dir)
    rooms = {s.get("name", "").lower(): sp for sp, s in
             ((sj.parent.name, json.loads(sj.read_text())) for sj in sorted((place_dir / "spaces").glob("*/space.json")))
             if s.get("name")}
    by_ref = {}
    for r in rows.values():
        by_ref.setdefault(r.get("ref"), r)
    made, unresolved = [], []
    for it in d["items"]:
        if it.get("orphan") or it.get("place_person") or it["id"] in rows:
            continue
        need = it.get("need") or ""
        if it["ref"] in by_ref:   # the same thing another quest already stands at the place
            r = dict(by_ref[it["ref"]], id=it["id"], quest=it["quest"], drafted=True,
                     why=f"where {by_ref[it['ref']]['quest']} stands it (the same {it['ref']})")
            rows[it["id"]] = r
            made.append(r)
            continue
        space = it.get("space") or "exterior"
        low = need.lower()
        if space == "exterior" and it["kind"] != "door":
            for name, sp in rooms.items():
                if name and name in low and re.search(r"\b(inside|in|back of|at the back)\b", low):
                    space = sp
        mesh = M.get(space) or M.get("exterior")
        taken = [r["pos"] for r in rows.values() if r.get("space") == space]
        nw = words(need)
        # quest things already drafted, by name
        cands = [a for a in A if a["space"] == space]
        for r in rows.values():
            other = next((x for x in d["items"] if x["id"] == r["id"]), None)
            if other and r.get("space") == space:
                cands.append({"space": space, "pos": r["pos"], "text": f"{other['name']} {other['ref']}", "what": other["name"]})
        best = max(cands, key=lambda a: score(nw, a["text"]), default=None)
        sc = score(nw, best["text"]) if best else 0
        wet = bool(WET.search(low))
        lo = 0.0
        if it["kind"] == "door":
            door = next((a for a in A if a.get("door_of") and a["what"].lower()[len("the door of "):] in low), None)
            if door:
                best, sc = door, 99
        if best and sc >= 2:
            ax, ay, az = best["pos"]
            why = f"by {best['what']} (the words: {', '.join(w for w in nw if w in set(words(best['text'])))})"
            lo = NEAR[0] if it["kind"] == "person" else 0.0
        elif space != "exterior" and BACK.search(low):
            ax, ay, az = mesh.far_from_door()
            why = "the far end of the room from its door (the words name nothing the room's rows hold)"
        else:
            ax, ay, az = mesh.middle()
            why = ("the middle of the room" if space != "exterior" else "the middle of the place's walking mesh") + \
                  " (the words name nothing the place's rows hold: move it)"
            unresolved.append(it["id"])
        if it["kind"] == "door" and sc == 99:
            pos = (ax, ay, az)
        else:
            p = mesh.snap(ax, ay, az, wet, taken, lo) or mesh.snap(ax, ay, az, True, [], 0) or (ax, ay, az, 0)
            pos = p[:3]
            if it["kind"] == "person":
                why += "; on a walkable triangle" + (" in the shallows" if wet and len(p) > 3 and p[3] == 2 else "")
            elif it["kind"] != "marker":
                why += "; on the walking mesh beside it (seated on the ground by the build)"
        head = math.atan2(ax - pos[0], ay - pos[1]) % (2 * math.pi) if (ax, ay) != tuple(pos[:2]) else 0.0
        r = {"id": it["id"], "quest": it["quest"], "ref": it["ref"], "space": space,
             "pos": [round(float(v), 2) for v in pos], "rot": [0, 0, round(head, 2)], "drafted": True, "why": why}
        rows[it["id"]] = r
        by_ref.setdefault(it["ref"], r)
        made.append(r)
    if write and made:
        from tools.places import edits   # the studio's writer: one text for the file, whoever writes it
        edits._write_jsonl(place_dir / qs.FILE, sorted(rows.values(), key=lambda r: r["id"]))
    return {"place": place_id, "drafted": made, "unresolved": unresolved,
            "items": sum(1 for it in d["items"] if not it.get("orphan")),
            "place_people": sum(1 for it in d["items"] if it.get("place_person"))}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places quest-draft")
    ap.add_argument("place_id", nargs="+")
    ap.add_argument("--redraft", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    for pid in a.place_id:
        r = draft(pid, out=Path(a.out), redraft=a.redraft)
        print(f"{pid}: {r['items']} quest things, {len(r['drafted'])} drafted, {r['place_people']} the place's own people, "
              f"{len(r['unresolved'])} unresolved {r['unresolved']}")
    return 0
