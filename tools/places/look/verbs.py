"""The look verbs, run inside the daemon (daemon.py) against its warm page. Each returns a dict: `png` (a path) and/or
numbers. Hands make ops of the studio's own kinds (ref.move, ref.remove, ref.add), kept as strokes in the session."""
from __future__ import annotations

import copy
import json
import math
import time

import numpy as np

from tools.places.look import draw, geom
from tools.places.look.scene import LOOK_OUT

VIEWS = ("at", "orbit", "walk", "section", "overview")
HANDS = ("move", "turn", "sink", "delete", "duplicate")


def _opts(args: list[str], flags: dict) -> tuple[list[str], dict]:
    """Split positional words from --flags (flags: name -> takes a value)."""
    pos, o, i = [], {}, 0
    while i < len(args):
        a = args[i]
        if a.startswith("--") and a[2:] in flags:
            if flags[a[2:]]:
                o[a[2:]] = args[i + 1]
                i += 2
                continue
            o[a[2:]] = True
        else:
            pos.append(a)
        i += 1
    return pos, o


def _out(place: str, name: str) -> str:
    d = LOOK_OUT / place
    d.mkdir(parents=True, exist_ok=True)
    return str(d / f"{time.strftime('%H%M%S')}{int(time.time() * 1000) % 1000:03d}-{name}.png")   # two looks in one second keep both


def _save(img, path: str, cam: dict | None = None, extra: dict | None = None) -> str:
    img.convert("RGB").save(path, optimize=False, compress_level=3)
    if cam is not None:
        meta = {k: v for k, v in cam.items()} | (extra or {})
        open(path + ".json", "w").write(json.dumps(meta))
    return path


def run(d, place: str, sess: dict, verb: str, args: list[str]) -> dict:
    from tools.places.look.daemon import save_session
    if verb in VIEWS:
        return view(d, place, sess["strokes"], verb, args)
    if verb == "probe":
        sc = d.scene(place, sess["strokes"])
        pos, o = _opts(args, {"all": False, "mesh": False})
        if o.get("mesh"):
            return mesh_probe(sc, place, pos)
        if o.get("all") or not pos:
            f = sc.faults()
            by = {}
            for x in f:
                by[x["fault"]] = by.get(x["fault"], 0) + 1
            return {"place": place, "pieces": len(sc.pieces), "counts": by, "faults": f}
        th = sc.resolve(pos[0])
        boxes = {q["id"]: geom.aabb(q) for q in sc.everything()}
        rows = [geom.probe_piece(p, sc.ground, sc.everything(), boxes) for p in th["pieces"]]
        if len(rows) > 1:   # a structure: each piece short, its faults whole
            fl = {x["id"] for x in sc.faults()}
            rows = [{k: r[k] for k in ("id", "edid", "kind", "resolved", "box", "lowest_over_ground", "feet_over_ground",
                                       "held_by") if k in r} | ({"ends": r["ends"]} if "ends" in r else {})
                    | ({"fault": True} if r["id"] in fl else {}) for r in rows]
        return {"thing": th["name"], "kind": th["kind"], "box": [th["lo"], th["hi"]], "pieces": rows}
    if verb == "pick":
        return pick(d, place, sess["strokes"], args)
    if verb in HANDS:
        pos, o = _opts(args, {})
        if "--view" in args:
            i = args.index("--view")
            act, vw = args[:i], args[i + 1:]
        else:
            act, vw = args, []
        before = view(d, place, sess["strokes"], vw[0], vw[1:], keep=True) if vw else None
        sc = d.scene(place, sess["strokes"])
        ops = hand(sc, verb, act, sess)
        for op in ops:
            sess["n_op"] = op["n"] = sess.get("n_op", 0) + 1
        sess["strokes"].append(ops)
        save_session(place, sess)
        res = {"verb": verb, "ops": len(ops), "ids": [op.get("id") or op.get("ref", {}).get("id") for op in ops][:20]}
        if verb == "sink":
            res["dz"] = ops[0].get("_dz") if ops else 0
            for op in ops:
                op.pop("_dz", None)
            save_session(place, sess)
        if vw:
            after = view(d, place, sess["strokes"], vw[0], vw[1:], keep=True, cam=before["cam"])
            p = _out(place, f"{verb}-before-after")
            res["png"] = _save(draw.pair(before["img"], after["img"], "before", f"after {verb}"), p)
        return res
    if verb == "undo":
        if not sess["strokes"]:
            return {"undone": 0}
        last = sess["strokes"].pop()
        save_session(place, sess)
        return {"undone": len(last)}
    if verb == "snapshot":
        sess["snapshots"][args[0]] = copy.deepcopy(sess["strokes"])
        save_session(place, sess)
        return {"snapshot": args[0], "strokes": len(sess["strokes"])}
    if verb == "restore":
        sess["strokes"] = copy.deepcopy(sess["snapshots"][args[0]])
        save_session(place, sess)
        return {"restored": args[0], "strokes": len(sess["strokes"])}
    if verb == "commit":
        res = commit(place, sess, args)
        d.scenes.clear()
        d.place = None   # the page reloads the place files as now written
        return res
    if verb == "compare":
        a, b, vw = args[0], args[1], args[2:]
        sa = sess["snapshots"][a] if a != "now" else sess["strokes"]
        sb = sess["snapshots"][b] if b != "now" else sess["strokes"]
        va = view(d, place, sa, vw[0], vw[1:], keep=True)
        vb = view(d, place, sb, vw[0], vw[1:], keep=True, cam=va["cam"])
        p = _out(place, f"compare-{a}-{b}")
        return {"png": _save(draw.pair(va["img"], vb["img"], a, b), p)}
    if verb == "reset":
        sess["strokes"] = []
        save_session(place, sess)
        return {"reset": True}
    if verb == "status":
        return {"place": d.place, "strokes": len(sess["strokes"]), "snapshots": list(sess["snapshots"]), "timing": d.timing}
    raise ValueError(f"unknown verb {verb!r}")


# ---------- views ----------
def view(d, place, strokes, verb, args, keep=False, cam=None) -> dict:
    t0 = time.time()
    d.open(place)
    d.sync(strokes)
    sc = d.scene(place, strokes)
    pos, o = _opts(args, {"from": True, "eye": False, "high": False, "top": False, "plain": False, "size": True,
                          "slab": True, "axis": False, "grass": False, "n": True, "helpers": False,
                          "mesh": False})
    d.helpers = bool(o.get("helpers"))
    w, h = (int(v) for v in o.get("size", f"{draw_w()}x{draw_h()}").split("x"))
    faults = {x["id"] for x in sc.faults()}
    plain = bool(o.get("plain"))
    height = "eye" if o.get("eye") else "high" if o.get("high") else "top" if o.get("top") else "oblique"
    side = o.get("from", "se")
    timing = {"scene_s": round(time.time() - t0, 2)}
    mesh_facts: dict = {}
    M = marks = None
    if o.get("mesh"):
        M, mesh_facts = built_mesh(place)
        marks = mesh_marks(sc, M) if M is not None else None
    raw_shot = d.shot

    def shot(c):   # each frame with the built mesh over it when asked (a section keeps its slab's triangles)
        img_, r_ = raw_shot(c)
        if M is not None:
            keep_ = None
            if c.get("line"):
                a_, b_ = np.asarray(c["line"][0][:2], float), np.asarray(c["line"][1][:2], float)
                t_ = (b_ - a_) / max(float(np.linalg.norm(b_ - a_)), 1e-9)
                rel = M.C[:, :2] - a_
                keep_ = np.abs(rel[:, 0] * t_[1] - rel[:, 1] * t_[0]) <= float(o.get("slab", 96))
            img_ = draw.mesh_overlay(img_, c, M, *marks, keep=keep_)
        return img_, r_
    if verb == "at":
        th = sc.resolve(pos[0])
        cam = cam or geom.frame(th["lo"], th["hi"], side, height, w, h, ground_z=sc.ground_under(th["lo"], th["hi"]))
        cam = cam | {"grass": bool(o.get("grass"))}
        img, r = shot(cam)
        timing |= {k: r.get(k) for k in ("ms", "draw_ms", "render_ms", "calls", "triangles")}
        if not plain:
            img, labels = draw.annotate(img, cam, sc, th, faults, f"{th['name']} from {side.upper()}, {height}")
        res = {"cam": cam, "img": img}
        if not keep:
            res = {"png": _save(img, _out(place, f"at-{_slug(th['name'])}-{side}"), cam), "thing": th["name"], "kind": th["kind"]}
    elif verb == "orbit":
        th = sc.resolve(pos[0])
        tw, thh = w // 2 * 2 // 2, h // 2 * 2 // 2
        tiles, caps, rms = [], [], []
        for s in ("n", "e", "s", "w"):
            c = geom.frame(th["lo"], th["hi"], s, height, tw, thh, ground_z=sc.ground_under(th["lo"], th["hi"]))
            img, r = shot(c)
            rms.append(r["ms"])
            if not plain:
                img, _ = draw.annotate(img, c, sc, th, faults, f"from {s.upper()}")
            tiles.append(img)
            caps.append(f"{th['name']} from {s.upper()}")
        img = draw.sheet(tiles, 2)
        timing |= {"shot_ms": rms}
        res = {"cam": None, "img": img}
        if not keep:
            res = {"png": _save(img, _out(place, f"orbit-{_slug(th['name'])}")), "thing": th["name"]}
    elif verb == "walk":
        a, b = sc.resolve(pos[0]), sc.resolve(pos[1])
        pa, pb = _point(a), _point(b)
        lines = [p["points"] for p in sc.files.get("paths") or [] if p.get("points")]
        way = geom.route(lines, pa, pb)
        n = int(o.get("n", 6)) if "n" in o else 6
        tw, thh = w // 2, h // 2
        tiles, caps, rms = [], [], []
        for i, (p, dv) in enumerate(geom.stations(way, n)):
            g = sc.ground.height(*p) or 0.0
            sup = geom.support_under(sc.pieces, p[0], p[1], g + 400, 400)
            z = max(g, geom.aabb(sc.by_id[sup])[1][2] if sup else g)
            c = {"pos": [p[0] - dv[0] * 60, p[1] - dv[1] * 60, z + geom.EYE], "target": [p[0] + dv[0] * 800, p[1] + dv[1] * 800, z + geom.EYE * 0.7],
                 "up": [0, 0, 1], "fov": 70, "w": tw, "h": thh, "near": 8, "far": 7000}
            img, r = shot(c)
            rms.append(r["ms"])
            heading = (math.degrees(math.atan2(dv[0], dv[1])) + 360) % 360
            if not plain:
                img, _ = draw.annotate(img, c, sc, None, faults, f"{i + 1}/{n} heading {heading:.0f}", grid=False)
            tiles.append(img)
        img = draw.sheet(tiles, 3)
        timing |= {"shot_ms": rms}
        res = {"cam": None, "img": img}
        if not keep:
            res = {"png": _save(img, _out(place, f"walk-{_slug(a['name'])}-{_slug(b['name'])}")), "route_len": round(_len(way)),
                   "route": [[round(v) for v in q] for q in way]}
    elif verb == "section":
        slab = float(o.get("slab", 96))
        if o.get("axis") or len(pos) == 1:
            th = sc.resolve(pos[0])
            if len(th["pieces"]) == 1:
                A, B = geom.long_axis(th["pieces"][0])
            else:
                lo, hi = th["lo"], th["hi"]
                if hi[0] - lo[0] >= hi[1] - lo[1]:
                    A, B = [lo[0] - 300, (lo[1] + hi[1]) / 2], [hi[0] + 300, (lo[1] + hi[1]) / 2]
                else:
                    A, B = [(lo[0] + hi[0]) / 2, lo[1] - 300], [(lo[0] + hi[0]) / 2, hi[1] + 300]
            title = f"section along {th['name']}"
        else:
            A, B = [_xy(sc, pos[0]), _xy(sc, pos[1])]
            title = f"section {pos[0]} to {pos[1]}"
        cam, crossed, prof = section_setup(sc, A, B, slab, w, h)
        img, r = shot(cam)
        timing |= {"shot_ms": r["ms"], "draw_ms": r["draw_ms"]}
        if not plain:
            img = draw.annotate_section(img, cam, sc, prof, crossed, faults, title + f" (slab {slab:.0f} u each side, looking {_facing(cam)})")
        res = {"cam": cam, "img": img}
        if not keep:
            res = {"png": _save(img, _out(place, "section"), cam), "line": [A, B], "crossed": crossed}
    elif verb == "overview":
        cl = sc.clusters()
        keep_c = [c for c, ps in cl.items() if not c.startswith("w")] or list(cl)
        allp = [p for c in keep_c for p in cl[c]]
        th = sc._of(place, "place", allp)
        c1 = geom.frame(th["lo"], th["hi"], side, "oblique", w, h, ground_z=sc.ground_under(th["lo"], th["hi"]), fill=0.95)
        c2 = geom.frame(th["lo"], th["hi"], "s", "top", w, h, fill=0.95)
        i1, r1 = shot(c1)
        i2, r2 = shot(c2)
        if not plain:
            i1, _ = draw.annotate(i1, c1, sc, th, faults, f"{place} from {side.upper()}")
            i2, _ = draw.annotate(i2, c2, sc, th, faults, f"{place} from above")
        img = draw.sheet([i1, i2], 2)
        timing |= {"shot_ms": [r1["ms"], r2["ms"]]}
        res = {"cam": None, "img": img}
        if not keep:
            res = {"png": _save(img, _out(place, "overview"), c1 | {"tiles": [c1, c2]})}
    else:
        raise ValueError(verb)
    if mesh_facts and not keep:
        res["mesh"] = {k: v for k, v in mesh_facts.items() if k != "built"}
    if not keep:
        res["timing"] = timing | {"total_s": round(time.time() - t0, 2)}
        res["size"] = list(img.size)
    return res


def draw_w():
    return 768


def draw_h():
    return 576


def section_setup(sc, A, B, slab, w, h):
    prof = geom.profile(sc.ground, A, B)
    boxes = {p["id"]: geom.aabb(p) for p in sc.pieces}
    crossed = []
    for p in sc.pieces:
        if not p.get("model") or p.get("kind") in ("light", "marker", "groundcover"):
            continue
        if geom.crosses(p, A, B, slab, boxes[p["id"]]):
            lo, hi = boxes[p["id"]]
            g = [sc.ground.height(x, y) for x, y, _ in geom.bottom_points(p)]
            g = [v for v in g if v is not None]
            crossed.append({"id": p["id"], "edid": p.get("edid"), "kind": p.get("kind"), "z": [round(float(lo[2])), round(float(hi[2]))],
                            "over": round(float(lo[2]) - max(g), 1) if g else None,
                            "label": p.get("kind") in ("building", "static", "door", "furniture") and (hi[0] - lo[0]) * (hi[1] - lo[1]) > 20000})
    zs = [v for _, g, wz in prof for v in (g, wz) if v is not None]
    zs += [z for c in crossed for z in c["z"] if c.get("label") or c["kind"] in ("building", "static")]
    zlo, zhi = min(zs) - 60, max(zs) + 60
    cam = geom.section_camera(A, B, zlo, zhi, w, h, slab)
    # the ground and water drawn across the whole frame, past A and B
    t = (np.asarray(B, float) - np.asarray(A, float)) / max(float(np.linalg.norm(np.subtract(B, A))), 1e-9)
    mid, hw = (np.asarray(A, float) + np.asarray(B, float)) / 2, cam["upp"] * w / 2
    cam["prof_line"] = [(mid - t * hw).tolist(), (mid + t * hw).tolist()]
    prof = geom.profile(sc.ground, *cam["prof_line"])
    crossed.sort(key=lambda c: -(c["over"] or 0))
    return cam, crossed, prof


def _facing(cam):
    v = np.asarray(cam["target"]) - np.asarray(cam["pos"])
    names = ["east", "north-east", "north", "north-west", "west", "south-west", "south", "south-east"]
    return names[int(round(math.degrees(math.atan2(v[1], v[0])) / 45)) % 8]


def _xy(sc, s):
    th = sc.resolve(s)
    return _point(th)[:2]


def _point(th):
    if th.get("point"):
        return th["point"]
    if th["kind"] == "door":
        arr = (th["pieces"][0].get("door") or {}).get("arrival")
        if arr:
            return arr
    lo, hi = th["lo"], th["hi"]
    return [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]]


def _len(way):
    return float(np.sum(np.linalg.norm(np.diff(np.asarray(way, float), axis=0), axis=1)))


def _slug(s):
    return "".join(c if c.isalnum() else "-" for c in str(s).split(".")[-1])[:24]


# ---------- pick ----------
def pick(d, place, strokes, args) -> dict:
    png, px, py = args[0], float(args[1]), float(args[2])
    cam = json.loads(open(png + ".json").read())
    if cam.get("tiles"):
        tw = cam["tiles"][0]["w"]
        k = int(px // tw)
        cam, px = cam["tiles"][k], px - k * tw
    sc = d.scene(place, strokes)
    hits = geom.pick(cam, px, py, sc.pieces, cam.get("clip"))
    out = []
    for t, p in hits[:5]:
        lo, hi = geom.aabb(p)
        g = [sc.ground.height(x, y) for x, y, _ in geom.bottom_points(p)]
        g = [v for v in g if v is not None]
        out.append({"id": p["id"], "base": p["base"], "edid": p.get("edid"), "model": p.get("model"), "kind": p.get("kind"),
                    "structure": p.get("cluster"), "dist": round(t), "lowest_over_ground": round(float(lo[2]) - max(g), 1) if g else None})
    o, dv = geom.ray(cam, px, py)
    ground = None
    for s in np.arange(0, 60000, 16.0):
        q = o + dv * s
        gz = sc.ground.height(q[0], q[1])
        if gz is not None and q[2] <= gz:
            ground = [round(float(q[0]), 1), round(float(q[1]), 1), round(float(gz), 1)]
            break
    return {"hits": out, "ground": ground}


# ---------- commit: the session into the place files ----------
def commit(place: str, sess: dict, args: list[str], places=None, bundles=None) -> dict:
    """`commit -m "<why>"`: the session's strokes written into the committed place files by the studio's own apply
    (edits.apply_agent_save), as the agent's draft edits: the save kept at <place>/agent-edits/<save_id>.json and
    listed in place.json `agent_saves_applied`; a stroke on a row the owner's finalised saves touched is left out and
    reported. The session is then emptied (its snapshots too: they name the old files)."""
    from tools.places import edits
    from tools.places.draft.stages import owner_rows
    from tools.places.look.daemon import save_session
    from tools.places.look.scene import data_out
    from tools.places.seat import PLACES
    why = " ".join(a for a in args if a not in ("-m", "--m")).strip()
    if not why:
        raise ValueError('commit needs -m "<why>"')
    if not sess["strokes"]:
        return {"committed": 0, "why": "the session has no strokes"}
    pdir = (places or PLACES) / place
    at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    sid = "agent-" + time.strftime("%Y%m%dT%H%M%S", time.gmtime())
    ops, n = [], 0
    for k, stroke in enumerate(sess["strokes"], 1):
        for op in stroke:
            n += 1
            ops.append({kk: v for kk, v in op.items() if not kk.startswith("_")} | {"n": n, "stroke": k, "at": at})
    save = {"save_id": sid, "place_id": place, "name": why, "at": at, "by": "agent", "final": False, "ops": ops}
    files = edits.load_place(pdir)
    out, left = edits.apply_agent_save(files, save, owner_rows(pdir),
                                       edits.bundle_source(bundles or (data_out() / "bundles")))
    edits.write_place(pdir, out)
    ad = pdir / "agent-edits"
    ad.mkdir(exist_ok=True)
    (ad / f"{sid}.json").write_text(json.dumps(save, indent=1) + "\n")
    sess["strokes"], sess["snapshots"] = [], {}
    save_session(place, sess)
    return {"save": str(ad / f"{sid}.json"), "ops": n, "strokes": len({op["stroke"] for op in ops}),
            "left_for_owner": left}


# ---------- hands ----------
def _rows(sc, th):
    rows = {r["id"]: r for r in sc.files["spaces"]["exterior"]["refs"]}
    return [rows[p["id"]] for p in th["pieces"] if p["id"] in rows]


def _pose(r):
    return copy.deepcopy({"pos": r["pos"], "rot": r.get("rot") or [0, 0, 0], "scale": r.get("scale", 1), "seat": r.get("seat")})


def _move_op(r, after):
    before = _pose(r)
    keys = [k for k in ("pos", "rot", "scale", "seat") if k in r or k in ("pos", "rot")]
    return {"op": "ref.move", "space": "exterior", "id": r["id"], "call": "fault",
            "before": {k: before[k] for k in keys}, "after": {k: after[k] for k in keys}}


def _shift(r, dx, dy, dz, rot=None, moved=frozenset()):
    """r moved by dx dy dz (and turned); its seat's dz moves with it, unless it sits `on` a piece moved with it."""
    a = _pose(r)
    a["pos"] = [round(a["pos"][0] + dx, 3), round(a["pos"][1] + dy, 3), round(a["pos"][2] + dz, 3)]
    if a.get("seat") and a["seat"].get("mode", "free") != "free" and a["seat"].get("on") not in moved:
        a["seat"] = dict(a["seat"], dz=round(float(a["seat"].get("dz", 0)) + dz, 3))
    if rot is not None:
        a["rot"] = [a["rot"][0], a["rot"][1], round((a["rot"][2] + rot) % (2 * math.pi), 5)]
    return a


def hand(sc, verb, args, sess) -> list[dict]:
    pos, o = _opts(args, {"until-feet-buried": False})
    th = sc.resolve(pos[0])
    rows = _rows(sc, th)
    if not rows:
        raise ValueError(f"{pos[0]} has no pieces to act on")
    ids = {r["id"] for r in rows}   # a piece seated on one of these moves with it: its own dz stays
    if verb == "move":
        dx, dy, dz = (float(v) for v in pos[1:4])
        return [_move_op(r, _shift(r, dx, dy, dz, moved=ids)) for r in rows]
    if verb == "turn":
        deg = float(pos[1])
        a = math.radians(deg)
        cx, cy = (th["lo"][0] + th["hi"][0]) / 2, (th["lo"][1] + th["hi"][1]) / 2
        if len(rows) == 1:
            cx, cy = rows[0]["pos"][0], rows[0]["pos"][1]
        ops = []
        for r in rows:
            ox, oy = r["pos"][0] - cx, r["pos"][1] - cy
            nx, ny = cx + ox * math.cos(a) + oy * math.sin(a), cy - ox * math.sin(a) + oy * math.cos(a)   # clockwise, as the game's yaw
            ops.append(_move_op(r, _shift(r, nx - r["pos"][0], ny - r["pos"][1], 0.0, rot=a, moved=ids)))
        return ops
    if verb == "sink":
        if len(pos) > 1 and not o.get("until-feet-buried"):
            dz = -abs(float(pos[1]))
        else:   # until every foot is in the ground: the highest foot of the lowest-standing solid piece goes 8 under
            boxes = {q["id"]: geom.aabb(q) for q in sc.everything()}
            feet = []
            for p in th["pieces"]:
                if not geom.solid(p):
                    continue
                r = geom.probe_piece(p, sc.ground, sc.everything(), boxes)
                if r["feet_over_ground"]:
                    feet.append(r["feet_over_ground"][1])
            dz = -(min(feet) + 8.0) if feet else 0.0
            dz = min(dz, 0.0)
        ops = [_move_op(r, _shift(r, 0, 0, dz, moved=ids)) for r in rows]
        if ops:
            ops[0]["_dz"] = round(dz, 1)
        return ops
    if verb == "delete":
        return [{"op": "ref.remove", "space": "exterior", "id": r["id"], "call": "fault", "before": copy.deepcopy(r)} for r in rows]
    if verb == "duplicate":
        dx, dy = (float(pos[1]), float(pos[2])) if len(pos) > 2 else (256.0, 0.0)
        sess["n"] = sess.get("n", 0) + 1
        ids = {r["id"]: f"{sc.place_id}.LOOK{sess['n']:03d}{i:04d}" for i, r in enumerate(rows)}
        ops = []
        for r in rows:
            nr = copy.deepcopy(r)
            nr["id"] = ids[r["id"]]
            nr["pos"] = [round(r["pos"][0] + dx, 3), round(r["pos"][1] + dy, 3), r["pos"][2]]
            nr.pop("src", None)
            if (nr.get("seat") or {}).get("on") in ids:
                nr["seat"] = dict(nr["seat"], on=ids[nr["seat"]["on"]])
            ops.append({"op": "ref.add", "space": "exterior", "call": "fault", "ref": nr})
        return ops
    raise ValueError(verb)


# ---------- the built walkable mesh ----------
_MESH: dict = {}


def built_mesh(place: str, space: str = "exterior"):
    """(Mesh, facts) of the place's built navmesh in `space`, cached per export; facts say which build and whether
    the place files are newer than it (stale)."""
    from tools.places.look import mesh
    from tools.places.look.scene import data_out
    from tools.places.seat import PLACES
    path, build = mesh.find(place, data_out())
    if path is None:
        return None, {"mesh": None, "why": f"{place} has no build with a navmesh (draft check or the place build makes one)"}
    key = (str(path), path.stat().st_mtime, space)
    if key not in _MESH:
        _MESH.clear()
        _MESH[key] = mesh.load(path, space)
    facts = {"navmesh": str(path), **mesh.stale(PLACES / place, build, place)}
    if facts["stale"]:
        facts["warning"] = "STALE: the place files are newer than the build this mesh is of; rebuild before trusting it"
    return _MESH[key], facts


def mesh_marks(sc, M) -> tuple[list, list]:
    """Door arrivals [(name, xyz, on the main network)] and street points [(xyz, on)] for the overlay and the numbers."""
    di = M.door_islands()
    doors = []
    for p in sc.pieces:
        dd = p.get("door") or {}
        if p.get("kind") != "door" or not dd.get("to_space"):
            continue
        at = dd.get("arrival") or [p["m"][0][3], p["m"][1][3], p["m"][2][3]]
        isl = di.get(p["id"], M.island_of(at[0], at[1], at[2]))
        doors.append((dd["to_space"], list(at), isl == M.main))
    pts = []
    for line in sc.files.get("paths") or []:
        for q in line.get("points") or []:
            t, z = street_point(sc, M, q)
            pts.append(([q[0], q[1], z], bool(t >= 0 and M.lab[t] == M.main)))
    return doors, pts


def street_point(sc, M, q) -> tuple[int, float]:
    """The triangle a street point stands on: the main network's under it if any, else the one nearest the ground."""
    g = sc.ground.height(q[0], q[1]) or 0.0
    t, z = M.tri_at(q[0], q[1], g + 200, tol=400)
    if t >= 0 and M.lab[t] != M.main:
        for zz in (g, g + 100, g + 300):
            t2, z2 = M.tri_at(q[0], q[1], zz, tol=60)
            if t2 >= 0 and M.lab[t2] == M.main:
                return t2, z2
    return (t, z) if t >= 0 else (-1, g)


def mesh_probe(sc, place: str, names: list[str]) -> dict:
    """`probe --mesh [a b]`: the islands and what stands on each; with two things, whether a walk joins them and,
    where it does not, where and how the mesh breaks between them."""
    M, facts = built_mesh(place)
    if M is None:
        return facts
    doors, pts = mesh_marks(sc, M)
    di = M.door_islands()
    by_isl: dict[int, dict] = {}
    for p in sc.pieces:
        if p["id"] in di:
            by_isl.setdefault(di[p["id"]], {"doors": [], "points": 0})["doors"].append((p.get("door") or {}).get("to_space"))
    for q, _ in pts:
        t, _z = M.tri_at(q[0], q[1], q[2], tol=8)
        if t >= 0:
            by_isl.setdefault(int(M.lab[t]), {"doors": [], "points": 0})["points"] += 1
    rows = [{"island": int(i), "triangles": int(M.count[i]), **({"main": True} if i == M.main else {}),
             "doors": by_isl.get(i, {}).get("doors", []), "street_points": by_isl.get(i, {}).get("points", 0)}
            for i in sorted(set(by_isl) | {M.main}, key=lambda i: -M.count[i])]
    res = {**facts, "islands": len(M.count), "triangles": int(len(M.T)), "listed": rows,
           "doors_off_main": [n for n, _, on in doors if not on],
           "street_points_off_main": sum(1 for _, on in pts if not on)}
    if len(names) >= 2:
        ends = []
        for n in names[:2]:
            th = sc.resolve(n)
            at = _point(th)
            pid = th["pieces"][0]["id"] if th["kind"] == "door" else None
            isl = di.get(pid, -1) if pid else -1
            if isl < 0:
                isl = M.island_of(at[0], at[1], at[2] if len(at) > 2 else None)
            ends.append({"thing": th["name"], "at": [round(v) for v in at], "island": int(isl)})
        res["join"] = {"from": ends[0], "to": ends[1], "joined": ends[0]["island"] == ends[1]["island"] >= 0}
        if not res["join"]["joined"] and min(e["island"] for e in ends) >= 0:
            g = M.gap(ends[0]["island"], ends[1]["island"])
            if g:
                g["pieces_at_gap"] = [
                    {"id": p["id"], "edid": p.get("edid")} for p in sc.pieces
                    if p.get("kind") not in ("light", "marker", "plant", "groundcover") and _box_has(p, g["at"], 48)][:8]
            res["join"]["gap"] = g
    return res


def _box_has(p, at, pad):
    lo, hi = geom.aabb(p)
    return all(lo[k] - pad <= at[k] <= hi[k] + pad for k in range(3))
