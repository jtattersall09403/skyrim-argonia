#!/usr/bin/env python3
"""Dev server: serves the studio web dir and a Studio API backed by make_fixture's output."""

import argparse
import datetime
import gzip
import hashlib
import json
import math
import re
import struct
import sys
import tempfile
import threading
import time
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

CELL, N, STEP = 4096.0, 33, 4096.0 / 32
KIND_COLOUR = {"building": (0.6, 0.45, 0.3), "tree": (0.2, 0.55, 0.2), "plant": (0.4, 0.7, 0.3),
               "groundcover": (0.35, 0.6, 0.3), "rock": (0.5, 0.5, 0.5), "furniture": (0.55, 0.35, 0.2),
               "clutter": (0.8, 0.7, 0.3), "light": (1.0, 0.85, 0.4), "door": (0.4, 0.25, 0.15),
               "actor": (0.8, 0.4, 0.4), "static": (0.55, 0.55, 0.5)}


REPO = Path(__file__).resolve().parents[5]
SAVE_ID = re.compile(r"[a-z0-9][a-z0-9._-]*")
NO_WATER = 3.0e38
LOCAL_TYPE = {"NPC_": "Npc"}


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def assets_module():
    """tools.places.assets when it is importable (real-data mode), else None."""
    try:
        sys.path.insert(0, str(REPO))
        from tools.places import assets
        return assets
    except Exception:
        return None


def jsonl_path(p):
    """The .jsonl, else its .gz, else None."""
    p = Path(p)
    if p.is_file():
        return p
    gz = p.with_name(p.name + ".gz")
    return gz if gz.is_file() else None


class State:
    def __init__(self, bundles, places, web, mismatch, saves, real):
        self.bdir, self.pdir, self.web, self.mismatch = Path(bundles), Path(places), Path(web), mismatch
        self.saves, self.real = Path(saves), real
        self.notes = {}
        self.assets = assets_module() if real else None
        self.lock = threading.Lock()
        self.seen_models, self.heartbeats, self.hb_started, self.runs = set(), 0, None, {}
        self.bases = {}  # bundle -> rows
        self.terrain_cache = {}
        for d in sorted(self.bdir.iterdir()):
            if d.is_dir():
                self.bases[d.name] = self.read_jsonl(d / "bases.jsonl")

    @staticmethod
    def read_jsonl(p):
        f = jsonl_path(p)
        if f is None:
            return []
        raw = gzip.open(f, "rt").read() if f.suffix == ".gz" else f.read_text()
        return [json.loads(x) for x in raw.splitlines() if x.strip()]

    def bundle_json(self, bid):
        p = self.bdir / bid / "bundle.json"
        return json.loads(p.read_text()) if p.is_file() else None

    def place_files(self):
        if self.real:
            return sorted(self.pdir.glob("*/place.json"))
        return [self.pdir / "place.json"]

    def load_terrain(self, bid):
        if bid in self.terrain_cache:
            return self.terrain_cache[bid]
        sp = self.bdir / bid / "spaces/exterior"
        out = None
        if (sp / "terrain.json").is_file() and (sp / "terrain.f32").is_file():
            meta = json.loads((sp / "terrain.json").read_text())
            raw = (sp / "terrain.f32").read_bytes()
            f = struct.unpack(f"<{len(raw) // 4}f", raw)
            out = ({tuple(c["cell"]): (c, f) for c in meta["cells"]}, meta.get("ltex", {}))
        self.terrain_cache[bid] = out
        return out

    def height(self, pid, x, y):
        t = self.load_terrain(f"ground.{pid}")
        cx, cy = math.floor(x / CELL), math.floor(y / CELL)
        if not t or (cx, cy) not in t[0]:
            return None, None
        c, f = t[0][(cx, cy)]
        fx, fy = (x - cx * CELL) / STEP, (y - cy * CELL) / STEP
        c0, r0 = min(int(fx), 31), min(int(fy), 31)
        tx, ty = fx - c0, fy - r0
        o = c["heights_index"] * N * N

        def g(r, cc):
            return f[o + r * N + cc]

        h = (g(r0, c0) * (1 - tx) + g(r0, c0 + 1) * tx) * (1 - ty) + (g(r0 + 1, c0) * (1 - tx) + g(r0 + 1, c0 + 1) * tx) * ty
        dzx = (g(r0, c0 + 1) - g(r0, c0)) / STEP
        dzy = (g(r0 + 1, c0) - g(r0, c0)) / STEP
        slope = math.degrees(math.atan(math.hypot(dzx, dzy)))
        w = (c.get("water") or {}).get("height")
        return h, (None if w is None or w >= NO_WATER else w, slope)

    def stamp(self, bid, fallback):
        b = self.bundle_json(bid)
        return (b["stamp"]["key"][:16] if b and b.get("stamp", {}).get("key") else fallback)

    def places(self):
        out = []
        for pf in self.place_files():
            if not pf.is_file():
                continue
            p = json.loads(pf.read_text())
            pid = p["place_id"]
            dk = p.get("draft_key") or hashlib.sha256(json.dumps((self.bundle_json(f"draft.{pid}") or {}).get("stamp", {}),
                                                                sort_keys=True).encode()).hexdigest()[:16]
            ent = {"place_id": pid, "title": p.get("title") or pid, "source_id": p["source_id"], "similar": p.get("similar", []),
                   "stamps": {"draft": self.stamp(f"draft.{pid}", dk) if self.bundle_json(f"draft.{pid}") else p.get("draft_key"),
                              "ground": self.stamp(f"ground.{pid}", (p.get("ground") or {}).get("stamp")),
                              "source": self.stamp(f"src.{p['source_id']}", (p.get("source") or {}).get("stamp"))},
                   "fit": p.get("fit")}
            out.append(ent)
        return out

    def ground_sha(self):
        for d in sorted(self.bdir.glob("ground.*")):
            b = self.bundle_json(d.name) or {}
            sha = (b.get("esm") or {}).get("sha256") or b.get("stamp", {}).get("sha")
            if sha:
                return sha
        return "0" * 64

    def find_base(self, model):
        return next((b for rows in self.bases.values() for b in rows if b["model"] == model), None)

    def land(self):
        """land.json shape from the ground terrains' ltex tables (the fallback when the asset module has none)."""
        out = {}
        for d in sorted(self.bdir.glob("ground.*")):
            t = self.load_terrain(d.name)
            for k, v in (t[1] if t else {}).items():
                col = tex_colour(v["diffuse"])
                out[k] = {"edid": v["edid"], "plugin": v["plugin"], "diffuse": v["diffuse"], "file": f"{v['edid']}.png",
                          "avg": "#%02x%02x%02x" % col, "w": 16, "h": 16}
        return out

    def save_path(self, pid, sid):
        return self.saves / re.sub(r"[^\w.-]", "_", pid) / (sid + ".json")


def glb_box(bounds, colour):
    (x0, y0, z0), (x1, y1, z1) = bounds
    # glTF is Y up; the front end converts axes, so write game axes as-is (x, y, z).
    c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [((0, 3, 2, 1), (0, 0, -1)), ((4, 5, 6, 7), (0, 0, 1)), ((0, 1, 5, 4), (0, -1, 0)),
             ((2, 3, 7, 6), (0, 1, 0)), ((1, 2, 6, 5), (1, 0, 0)), ((3, 0, 4, 7), (-1, 0, 0))]
    pos, nor, idx = [], [], []
    for quad, n in faces:
        b = len(pos)
        for i in quad:
            pos.append(c[i])
            nor.append(n)
        idx += [b, b + 1, b + 2, b, b + 2, b + 3]
    pb = b"".join(struct.pack("<3f", *p) for p in pos)
    nb = b"".join(struct.pack("<3f", *p) for p in nor)
    ib = struct.pack(f"<{len(idx)}H", *idx)
    ib += b"\0" * (-len(ib) % 4)
    blob = pb + nb + ib
    mn = [min(p[i] for p in pos) for i in range(3)]
    mx = [max(p[i] for p in pos) for i in range(3)]
    js = {"asset": {"version": "2.0", "generator": "devserver"}, "scene": 0, "scenes": [{"nodes": [0]}],
          "nodes": [{"mesh": 0}],
          "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1}, "indices": 2, "material": 0}]}],
          "materials": [{"pbrMetallicRoughness": {"baseColorFactor": [*colour, 1.0], "metallicFactor": 0.0,
                                                  "roughnessFactor": 0.9}}],
          "buffers": [{"byteLength": len(blob)}],
          "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pb), "target": 34962},
                          {"buffer": 0, "byteOffset": len(pb), "byteLength": len(nb), "target": 34962},
                          {"buffer": 0, "byteOffset": len(pb) + len(nb), "byteLength": len(idx) * 2, "target": 34963}],
          "accessors": [{"bufferView": 0, "componentType": 5126, "count": 24, "type": "VEC3", "min": mn, "max": mx},
                        {"bufferView": 1, "componentType": 5126, "count": 24, "type": "VEC3"},
                        {"bufferView": 2, "componentType": 5123, "count": len(idx), "type": "SCALAR"}]}
    jb = json.dumps(js, separators=(",", ":")).encode()
    jb += b" " * (-len(jb) % 4)
    total = 12 + 8 + len(jb) + 8 + len(blob)
    return (struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<I4s", len(jb), b"JSON") + jb
            + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def png(rgb, size=16):
    row = b"\0" + bytes(rgb) * size
    raw = row * size

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def tex_colour(path):
    h = hashlib.md5(path.encode()).digest()
    return (60 + h[0] % 150, 60 + h[1] % 150, 60 + h[2] % 150)


def score(b, tokens, q):
    hay = f"{b.get('name') or ''} {b.get('edid') or ''} {b.get('model') or ''} {' '.join(b.get('keywords', []))} {b.get('kind', '')}".lower()
    if not tokens:
        return 1.0
    s = sum(1.0 for t in tokens if t in hay)
    if s == 0:
        return 0.0
    if q in (b.get("edid") or "").lower():
        s += 1.0
    return round(s / (len(tokens) + 1), 3)


def run_state(run):
    steps = ["record", "build", "learn", "report"]
    t = time.time() - run["t0"]
    k = int(t / 1.0)
    if k >= 4:
        run.update(state="done", step="report", rc=0)
        run["report"] = ("# Finalise report\n\n## Built\n\n- fixplace: 40 refs, 2 interiors, 2 people, 1 path\n\n"
                         "## Failed checks\n\n- door FixHouse02 faces a wall (synthetic)\n\n"
                         "## Recipe changes\n\n- Seat doors before furniture.\n- Level a pad under each building.\n")
    else:
        run.update(state="starting" if k == 0 and t < 0.4 else "running", step=steps[k] if k else "record", rc=None)
    done = steps[:min(k, 4)]
    run["log"] = "".join(f"[{s}] ok\n" for s in done) + (f"[{steps[k]}] running\n" if k < 4 else "")
    return {x: run[x] for x in ("run_id", "save_id", "state", "step", "rc", "log", *(["report"] if k >= 4 else []))}


class H(BaseHTTPRequestHandler):
    st: State

    def log_message(self, *a):
        pass

    def send(self, code, body=b"", ctype="application/json", headers=None):
        if not isinstance(body, bytes):
            body = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def converting(self):
        self.send(202, {"state": "converting"}, headers={"Retry-After": "1"})

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def do_HEAD(self):  # the page asks whether the Atlas is there before offering it
        p = unquote(urlparse(self.path).path)
        return self.atlas(p[len("/atlas/"):] or "index.html") if p.startswith("/atlas/") else self.send(405, b"", "text/plain")

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        p = unquote(u.path)
        st = self.st
        if p.startswith("/atlas/"):
            return self.atlas(p[len("/atlas/"):] or "index.html")
        if not p.startswith("/api/"):
            return self.static(p)
        if p == "/api/places":
            return self.send(200, st.places())
        m = re.fullmatch(r"/api/bundle/([^/]+)/(.+)", p)
        if m:
            return self.bundle_file(m[1], m[2])
        if p == "/api/asset/mesh":
            return self.mesh(q.get("model", ""), q.get("level", "0"))
        if p == "/api/asset/tex":
            return self.tex(q.get("path", ""), q.get("size", "512"))
        if p == "/api/asset/thumb":
            return self.thumb(q.get("model", ""))
        if p == "/api/asset/land":
            return self.land()
        m = re.fullmatch(r"/api/asset/land/(.+)", p)
        if m:
            return self.land_file(m[1])
        if p == "/api/search":
            return self.search(q)
        if p == "/api/status":
            g = st.ground_sha()
            dep = ("0" * 8 + g[8:]) if st.mismatch else g
            return self.send(200, {"ground_sha": g, "deployed_sha": dep, "match": g == dep,
                                   "versions": {"studio": "devserver", "repo_head": "dev", "python": sys.version.split()[0],
                                                "aiohttp": None, "search_model": "devserver-substring",
                                                "search_rows": sum(len(r) for r in st.bases.values())},
                                   "awake": {"job_alive": st.hb_started is not None}})
        if p == "/api/_heartbeats":
            return self.send(200, {"count": st.heartbeats})
        m = re.fullmatch(r"/api/place/([^/]+)/notes", p)
        if m:
            return self.send(200, st.notes.get(m[1], []))
        m = re.fullmatch(r"/api/place/([^/]+)/(saves|seat|runs)(?:/([^/]+))?", p)
        if m:
            pid, what, arg = m.groups()
            if what == "saves":
                return self.saves_get(pid, arg)
            if what == "seat":
                try:
                    x, y = float(q["x"]), float(q["y"])
                except (KeyError, ValueError):
                    return self.send(400, {"error": "x and y required"})
                h, rest = st.height(pid, x, y)
                if h is None:
                    return self.send(404, {"error": "outside ground cells"})
                return self.send(200, {"ground": round(h, 2), "water": rest[0], "slope": round(rest[1], 2)})
            if what == "runs" and arg:
                with st.lock:
                    run = st.runs.get(arg)
                    if not run:
                        return self.send(404, {"error": "no such run"})
                    return self.send(200, run_state(run))
        self.send(404, {"error": "not found"})

    def bundle_file(self, bid, rel):
        root = (self.st.bdir / bid).resolve()
        f = (root / rel).resolve()
        if root not in f.parents:
            return self.send(404, {"error": "no such file"})
        if not f.is_file() and f.suffix == ".jsonl" and f.with_name(f.name + ".gz").is_file():
            data = gzip.open(f.with_name(f.name + ".gz")).read()
        elif f.is_file():
            data = f.read_bytes()
        else:
            return self.send(404, {"error": "no such file"})
        ct = "application/json" if f.suffix == ".json" else "application/octet-stream" if f.suffix == ".f32" else "application/x-ndjson"
        self.send(200, data, ct)

    def saves_get(self, pid, sid):
        base = self.st.save_path(pid, "x").parent
        if sid is None:
            rows = [dict(json.loads(f.read_text()), save_id=f.stem) for f in base.glob("*.json")] if base.exists() else []
            rows = [{k: (len(v) if k == "ops" else v) for k, v in r.items() if k != "base"} for r in rows]  # as the server lists them
            rows.sort(key=lambda r: r["at"], reverse=True)
            return self.send(200, rows)
        f = self.st.save_path(pid, re.sub(r"[^\w.-]", "_", sid))
        return self.send(200, f.read_bytes()) if f.exists() else self.send(404, {"error": "no such save"})

    def do_PUT(self):
        m = re.fullmatch(r"/api/place/([^/]+)/saves/([^/]+)", urlparse(self.path).path)
        if not m:
            return self.send(404, {"error": "not found"})
        pid, sid = m[1], unquote(m[2])
        if not SAVE_ID.fullmatch(sid):
            return self.send(400, {"error": "save_id must match [a-z0-9][a-z0-9._-]*"})
        try:
            data = json.loads(self.body())
            rev = data["rev"]
            name, base, ops = data["name"], data.get("base"), data["ops"]
        except (ValueError, KeyError, TypeError):
            return self.send(400, {"error": "body needs name, base, ops and rev"})
        f = self.st.save_path(pid, sid)
        with self.st.lock:
            cur = json.loads(f.read_text()) if f.exists() else None
            if cur and cur.get("final"):
                return self.send(409, {"error": "this save is final", "current": {"rev": cur["rev"], "at": cur["at"], "name": cur["name"]}})
            if rev != (cur["rev"] if cur else 0):
                c = {"rev": cur["rev"], "at": cur["at"], "name": cur["name"]} if cur else {"rev": 0, "at": None, "name": None}
                return self.send(409, {"error": "this save changed since you last read it", "current": c})
            at = now()
            row = {"save_id": sid, "place_id": pid, "name": name, "at": at, "rev": rev + 1, "final": False, "base": base,
                   "ops": ops, "kept": "disk"}
            f.parent.mkdir(parents=True, exist_ok=True)
            tmp = f.with_suffix(".tmp")
            tmp.write_text(json.dumps(row))
            tmp.replace(f)
        self.send(200, {"save_id": sid, "rev": rev + 1, "at": at, "kept": "disk"})

    def do_POST(self):
        p = urlparse(self.path).path
        if p == "/api/heartbeat":
            self.body()
            with self.st.lock:
                self.st.heartbeats += 1
                self.st.hb_started = self.st.hb_started or now()
                started = self.st.hb_started
            return self.send(200, {"held": True, "started": started, "release_after_s": 300})
        m = re.fullmatch(r"/api/place/([^/]+)/notes", p)
        if m:
            b = json.loads(self.body() or b"{}")
            with self.st.lock:
                rows = self.st.notes.setdefault(m[1], [])
                if b.get("id"):
                    note = next(r for r in rows if r["id"] == b["id"])
                    note["done"] = bool(b.get("done", True))
                else:
                    note = {"id": f"n{len(rows) + 1}", "at": now(), "text": b.get("text", ""), "things": b.get("things", []),
                            "view": b.get("view"), "done": False}
                    rows.append(note)
            return self.send(200, note)
        m = re.fullmatch(r"/api/place/([^/]+)/finalise", p)
        if m:
            try:
                sid = json.loads(self.body() or b"{}").get("save_id")
            except ValueError:
                return self.send(400, {"error": "bad json"})
            f = self.st.save_path(m[1], str(sid))
            with self.st.lock:
                if not sid or not f.exists():
                    return self.send(404, {"error": "no such save"})
                row = json.loads(f.read_text())
                row.update(final=True, rev=row["rev"] + 1)
                f.write_text(json.dumps(row))
                rid = f"{m[1]}.{sid}"
                self.st.runs[rid] = {"run_id": rid, "save_id": sid, "state": "starting", "step": "record", "rc": None,
                                     "t0": time.time(), "log": ""}
            return self.send(202, {"run_id": rid})
        self.send(404, {"error": "not found"})

    def mesh(self, model, level):
        st = self.st
        if level not in ("0", "1"):
            return self.send(400, {"error": "level must be 0 or 1"})
        base = st.find_base(model)
        if not base and model.startswith("landscape/grass/"):  # a land texture's grass: no base of its own
            base = {"bounds": [[-30, -30, 0], [30, 30, 60]], "kind": "groundcover"}
        if st.assets:
            pth = st.assets.mesh(model, int(level), base["bounds"] if base else None)
            return self.file(pth, "model/gltf-binary")
        if not base and not st.real:
            return self.send(404, {"error": "unknown model"})
        with st.lock:
            first = (model, level) not in st.seen_models
            st.seen_models.add((model, level))
        if first and not st.real:
            return self.converting()
        bounds = base["bounds"] if base else [[-50, -50, 0], [50, 50, 100]]
        col = KIND_COLOUR.get((base or {}).get("kind", ""), (0.6, 0.6, 0.6))
        self.send(200, glb_box(bounds, col), "model/gltf-binary")

    def file(self, pth, ctype=None):
        if pth is None:
            return self.converting()
        pth = Path(pth)
        ct = ctype or {".webp": "image/webp", ".png": "image/png", ".json": "application/json"}.get(pth.suffix, "application/octet-stream")
        self.send(200, pth.read_bytes(), ct)

    def tex(self, path, size):
        if self.st.assets:
            try:
                n = int(size)
            except ValueError:
                return self.send(400, {"error": "size must be a number"})
            return self.file(self.st.assets.tex(path, n))
        self.send(200, png(tex_colour(path), 16), "image/png")

    def thumb(self, model):
        st = self.st
        if st.assets:
            return self.file(st.assets.thumb(model))
        base = st.find_base(model)
        if not base and not st.real:
            return self.send(404, {"error": "unknown model"})
        self.send(200, png(tex_colour(model), 64), "image/png")

    def land(self):
        if self.st.assets:
            return self.file(self.st.assets.land_table(), "application/json")
        self.send(200, self.st.land())

    def land_file(self, name):
        if self.st.assets:
            t = self.st.assets.land_table()
            if t is None:
                return self.converting()
            f = (Path(t).parent / name).resolve()
            if Path(t).parent.resolve() not in f.parents or not f.is_file():
                return self.send(404, {"error": "no such land texture"})
            return self.file(f)
        row = next((v for v in self.st.land().values() if v["file"] == name), None)
        if not row:
            return self.send(404, {"error": "no such land texture"})
        self.send(200, png(tex_colour(row["diffuse"]), 16), "image/png")

    def search(self, q):
        st = self.st
        text = q.get("q", "").lower().strip()
        tokens = text.split()
        scope, sid = q.get("scope", "all"), q.get("source_id")
        kinds = set(filter(None, (q.get("kind") or "").split(",")))
        limit = int(q.get("limit") or 50)
        bundles = [f"src.{sid}"] if scope == "source" and sid else list(st.bases)
        res, seen = [], set()
        for bid in bundles:
            for b in st.bases.get(bid, []):
                if kinds and b.get("kind") not in kinds:
                    continue
                s = score(b, tokens, text)
                if s <= 0 or b["key"] in seen:
                    continue
                seen.add(b["key"])
                res.append({"key": b["key"], "edid": b.get("edid"), "name": b.get("name"), "model": b.get("model"),
                            "type": b.get("type"), "kind": b.get("kind"), "nordic": b.get("nordic", False),
                            "plugin": b.get("plugin"), "score": s, "thumb": None})
        res.sort(key=lambda r: -r["score"])
        self.send(200, {"q": q.get("q", ""), "scope": scope, "results": res[:limit]})

    def atlas(self, rel):
        """The world map: --atlas DIR when given (the built Atlas), else a stub page that shows the place it was asked
        to open; --no-atlas answers 404, as the studio server does when the Atlas has not been built."""
        if self.st.atlas is False:
            return self.send(404, b"the Atlas has not been built", "text/plain")
        if self.st.atlas:
            root = Path(self.st.atlas).resolve(); f = (root / rel).resolve()
            if root not in f.parents or not f.is_file():
                return self.send(404, b"not found", "text/plain")
            ct = {".html": "text/html", ".json": "application/json", ".png": "image/png", ".webp": "image/webp"}.get(f.suffix, "application/octet-stream")
            return self.send(200, f.read_bytes(), ct)
        if rel != "index.html":
            return self.send(404, b"not found", "text/plain")
        stub = ("<!doctype html><meta charset=utf-8><title>Atlas stub</title><body><h1>Atlas</h1><p id=place></p>"
                "<script>const s = () => { document.getElementById('place').textContent = "
                "(/place=([^&]+)/.exec(location.hash) || [])[1] || ''; }; s(); addEventListener('hashchange', s);</script>")
        self.send(200, stub.encode(), "text/html")

    def static(self, p):
        root = self.st.web.resolve()
        f = (root / p.lstrip("/")).resolve()
        if f.is_dir():
            f = f / "index.html"
        if root not in f.parents and f != root or not f.is_file():
            return self.send(404, b"not found", "text/plain")
        ct = {".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
              ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png"}.get(f.suffix, "application/octet-stream")
        self.send(200, f.read_bytes(), ct)


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8790)
    ap.add_argument("--fixture", default=str(here / "fixture-out"), help="fixture mode (default): make_fixture's output dir")
    ap.add_argument("--bundles", help="real-data mode: the bundles dir (e.g. out/places/bundles)")
    ap.add_argument("--places", help="real-data mode: dir holding <place_id>/place.json")
    ap.add_argument("--saves", help="where saves go (default: fixture-out/saves, or a temp dir in real mode)")
    ap.add_argument("--web", default=str(here.parent))
    ap.add_argument("--mismatch", action="store_true")
    ap.add_argument("--atlas", help="the built Atlas dir (out/newworld/map); default: a stub page")
    ap.add_argument("--no-atlas", action="store_true", help="answer the Atlas with 404, as when it is not built")
    a = ap.parse_args()
    real = bool(a.bundles)
    if real:
        if not a.places:
            ap.error("--bundles needs --places")
        saves = a.saves or tempfile.mkdtemp(prefix="devserver-saves-")
        H.st = State(a.bundles, a.places, a.web, a.mismatch, saves, True)
    else:
        saves = a.saves or str(Path(a.fixture) / "saves")
        H.st = State(Path(a.fixture) / "bundles", a.fixture, a.web, a.mismatch, saves, False)
    H.st.atlas = False if a.no_atlas else a.atlas
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), H)
    print(f"serving {a.web} + API ({'real' if real else 'fixture'} data, assets "
          f"{'tools.places.assets' if H.st.assets else 'generated'}) on :{a.port}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
