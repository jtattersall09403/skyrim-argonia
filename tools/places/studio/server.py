"""The studio server (docs/design/place-studio.md, Studio API): aiohttp on localhost, reached only through the
Cloudflare tunnel behind Access. Serves the API, the bundles and the front end (web/), compressed (brotli or
gzip, cached on disk), with ETags and range requests."""
from __future__ import annotations

import asyncio
import gzip
import hashlib
import json
import mimetypes
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import warnings

from aiohttp import web

from tools.places.studio import awake, links
from tools.places.studio.saves import AUTOSAVE, PLACE_ID, SAVE_ID, Conflict, Saves, atomic_write

ROOT = Path(__file__).resolve().parents[3]
WEB = Path(__file__).resolve().parent / "web"
NO_COMPRESS = {".webp", ".png", ".jpg", ".jpeg", ".gz", ".br", ".zip", ".woff2", ".mp4"}
RUN_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
warnings.filterwarnings("ignore", category=web.NotAppKeyWarning)
BUCKET = os.environ.get("STUDIO_BUCKET", "s3://argonia-private-050977237313/places/autosave")


class Config:
    def __init__(self) -> None:
        self.out = Path(os.environ.get("PLACES_OUT", ROOT / "out" / "places"))
        self.places = Path(os.environ.get("PLACES_DIR", ROOT / "newworld" / "places"))
        self.web = Path(os.environ.get("STUDIO_WEB", WEB))
        self.commit = os.environ.get("STUDIO_COMMIT", "1") == "1"
        self.bucket = os.environ.get("STUDIO_BUCKET_SYNC", "1") == "1"
        self.awake = os.environ.get("STUDIO_AWAKE", "1") == "1"
        self.jobs = Path(os.environ.get("JOBS_DIR", Path.home() / ".argonia" / "jobs"))
        self.zcache = Path(os.environ.get("STUDIO_ZCACHE", Path.home() / ".argonia" / "cache" / "studio-z"))


def jerr(status: int, msg: str, **extra) -> web.Response:
    return web.json_response({"error": msg} | extra, status=status)


def jok(data, status: int = 200, **kw) -> web.Response:
    r = web.json_response(data, status=status, dumps=lambda o: json.dumps(o, ensure_ascii=False), **kw)
    r.headers["Cache-Control"] = "no-store"
    return r


def inside(base: Path, rel: str) -> Path | None:
    p = (base / rel).resolve()
    return p if p.is_file() and p.is_relative_to(base.resolve()) else None


# ---- files: compression, ETag, range -------------------------------------------------------------------------

def _compress(src: Path, dst: Path, enc: str) -> None:
    data = src.read_bytes()
    if enc == "br":
        import brotli
        out = brotli.compress(data, quality=5)
    else:
        out = gzip.compress(data, 6)
    atomic_write(dst, out)


async def send_file(req: web.Request, p: Path, cache: str = "no-cache") -> web.StreamResponse:
    """A file with its ETag; compressed when the client accepts it and no range is asked (a range is served from
    the plain file). Compressed copies are cached under the zcache, keyed by path, size and mtime."""
    cfg: Config = req.app["cfg"]
    st = p.stat()
    ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    if p.suffix in (".jsonl", ".f32", ".glb"):
        ctype = {".jsonl": "application/x-ndjson", ".f32": "application/octet-stream",
                 ".glb": "model/gltf-binary"}[p.suffix]
    headers = {"Cache-Control": cache, "Content-Type": ctype, "Vary": "Accept-Encoding"}
    ae = req.headers.get("Accept-Encoding", "")
    enc = "br" if "br" in ae else "gzip" if "gzip" in ae else None
    if enc and "Range" not in req.headers and st.st_size > 1024 and p.suffix.lower() not in NO_COMPRESS:
        key = hashlib.sha1(f"{p}|{st.st_size}|{st.st_mtime_ns}".encode()).hexdigest()
        z = cfg.zcache / f"{key}.{enc}"
        if not z.exists():
            await asyncio.get_running_loop().run_in_executor(None, _compress, p, z, enc)
        headers["Content-Encoding"] = enc
        r = web.FileResponse(z, headers=headers)
        r.headers["ETag"] = f'"{key[:20]}-{enc}"'
        return r
    return web.FileResponse(p, headers=headers)


# ---- places and bundles -------------------------------------------------------------------------------------

def place_titles() -> dict:
    p = ROOT / "newworld" / "story" / "data" / "db" / "place.jsonl"
    out = {}
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                out[r["id"]] = r.get("name")
    return out


def bundle_stamp(cfg: Config, bundle_id: str) -> dict | None:
    bj = cfg.out / "bundles" / bundle_id / "bundle.json"
    if not bj.exists():
        return None
    return json.loads(bj.read_text(encoding="utf-8")).get("stamp")


async def places(req: web.Request) -> web.Response:
    cfg: Config = req.app["cfg"]
    titles = place_titles()
    out = []
    for pj in sorted(cfg.places.glob("*/place.json")):
        pid = pj.parent.name
        draft = bundle_stamp(cfg, f"draft.{pid}")
        if draft is None and not (pj.parent / "spaces").exists():
            continue
        pl = json.loads(pj.read_text(encoding="utf-8"))
        out.append({"place_id": pid, "title": titles.get(pid) or pl.get("title") or pid,
                    "source_id": pl.get("source_id"), "similar": pl.get("similar") or [],
                    "stamps": {"draft": draft, "ground": bundle_stamp(cfg, f"ground.{pid}"),
                               "source": bundle_stamp(cfg, f"src.{pl.get('source_id')}")}})
    return jok(out)


async def bundle_file(req: web.Request) -> web.StreamResponse:
    cfg: Config = req.app["cfg"]
    bid = req.match_info["bundle_id"]
    if not RUN_ID.match(bid):
        return jerr(400, "bad bundle id")
    p = inside(cfg.out / "bundles" / bid, req.match_info["path"])
    return await send_file(req, p) if p else jerr(404, "no such bundle file")


# ---- assets and search -----------------------------------------------------------------------------------------

async def asset(req: web.Request, kind: str, args: tuple) -> web.StreamResponse:
    try:
        p = await asyncio.get_running_loop().run_in_executor(None, links.asset, kind, *args)
    except links.Missing as e:
        return jerr(503, f"the asset converter is not built yet ({e})")
    except FileNotFoundError as e:
        return jerr(404, str(e))
    if p is None:
        return jok({"state": "converting"}, status=202, headers={"Retry-After": "2"})
    return await send_file(req, p, cache="public, max-age=86400")


async def asset_mesh(req: web.Request):
    m = req.query.get("model")
    return await asset(req, "mesh", (m,)) if m else jerr(400, "model= is required")


async def asset_tex(req: web.Request):
    p = req.query.get("path")
    if not p:
        return jerr(400, "path= is required")
    try:
        size = int(req.query.get("size", "512"))
    except ValueError:
        return jerr(400, "size must be a number")
    return await asset(req, "tex", (p, size))


async def asset_thumb(req: web.Request):
    m = req.query.get("model")
    return await asset(req, "thumb", (m,)) if m else jerr(400, "model= is required")


async def search(req: web.Request) -> web.Response:
    from urllib.parse import quote

    from tools.places.search.index import Index
    q = req.query
    scope = q.get("scope", "all")
    if scope not in ("all", "source"):
        return jerr(400, "scope is source or all")
    if scope == "source" and not q.get("source_id"):
        return jerr(400, "scope=source needs source_id")
    try:
        limit = max(1, min(200, int(q.get("limit", "40"))))
    except ValueError:
        return jerr(400, "limit must be a number")

    def run():
        ix = Index.open(req.app["cfg"].out / "search")
        return ix.query(q.get("q", ""), scope=scope, source_id=q.get("source_id"), kind=q.get("kind") or None,
                        limit=limit)
    hits = await asyncio.get_running_loop().run_in_executor(None, run)
    for h in hits:
        h["thumb"] = f"/api/asset/thumb?model={quote(h['model'])}" if h.get("model") else None
    return jok({"q": q.get("q", ""), "scope": scope, "results": hits})


# ---- saves ---------------------------------------------------------------------------------------------------------

def git_dirty(paths: list[Path]) -> set[str]:
    if not paths:
        return set()
    r = subprocess.run(["git", "status", "--porcelain", "--", *map(str, paths)], cwd=ROOT, capture_output=True,
                       text=True, timeout=30)
    return {line[3:].strip() for line in r.stdout.splitlines()}


async def saves_list(req: web.Request) -> web.Response:
    cfg: Config = req.app["cfg"]
    pid = req.match_info["place_id"]
    if not PLACE_ID.match(pid):
        return jerr(400, "bad place id")
    rows = req.app["saves"].list(pid)
    named = [Path(r["path"]) for r in rows if r["save_id"] != AUTOSAVE]
    dirty = git_dirty(named) if cfg.commit else set()
    for r in rows:
        p = Path(r.pop("path"))
        if r["save_id"] == AUTOSAVE:
            r["kept"] = "disk+bucket"
        else:
            rel = str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)
            r["kept"] = "pending" if (rel in dirty or req.app["pending"].get(rel)) else "committed"
    return jok(rows)


async def save_get(req: web.Request) -> web.Response:
    try:
        s = req.app["saves"].read(req.match_info["place_id"], req.match_info["save_id"])
    except ValueError as e:
        return jerr(400, str(e))
    return jok(s) if s else jerr(404, "no such save")


async def save_put(req: web.Request) -> web.Response:
    pid, sid = req.match_info["place_id"], req.match_info["save_id"]
    if not PLACE_ID.match(pid) or not SAVE_ID.match(sid):
        return jerr(400, "bad place or save id (lower case letters, digits, dot, dash, underscore)")
    try:
        body = await req.json()
    except ValueError:
        return jerr(400, "body is not JSON")
    if not isinstance(body, dict):
        return jerr(400, "body must be a save object")
    locks = req.app["locks"]
    async with locks.setdefault(pid, asyncio.Lock()):
        try:
            save = req.app["saves"].write(pid, sid, body)
        except Conflict as c:
            return jerr(409, "this save was written by another tab or session since you loaded it; "
                             "reload it, or save under a new name", current=c.current)
        except ValueError as e:
            return jerr(400, str(e))
    p = req.app["saves"].path(pid, sid)
    if sid == AUTOSAVE:
        req.app["bucket_q"][pid] = p
        kept = "disk+bucket"
    else:
        kept = "pending" if req.app["cfg"].commit else "disk"
        if req.app["cfg"].commit:
            rel = str(p.relative_to(ROOT))
            req.app["pending"][rel] = True
            await req.app["commit_q"].put((rel, f"places: studio save {pid}/{sid} (rev {save['rev']})"))
    return jok({"save_id": sid, "rev": save["rev"], "at": save["at"], "kept": kept})


async def commit_worker(app: web.Application) -> None:
    """Commit and push each named save by path, one at a time; a failure is logged and retried on the next save."""
    q: asyncio.Queue = app["commit_q"]
    while True:
        rel, msg = await q.get()
        latest = {rel: msg}
        while not q.empty():
            r2, m2 = q.get_nowait()
            latest[r2] = m2
        for path, m in latest.items():
            proc = await asyncio.create_subprocess_exec(
                str(ROOT / "tooling" / "lane_commit.sh"), "-m", m, "--", path, cwd=ROOT,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
            out, _ = await proc.communicate()
            print(f"commit {path}: rc={proc.returncode} {out.decode(errors='replace')[-300:]}", flush=True)
            if proc.returncode == 0:
                app["pending"].pop(path, None)


async def bucket_worker(app: web.Application) -> None:
    """Copy each place's autosave to the private bucket at most once a minute."""
    while True:
        await asyncio.sleep(60)
        todo, app["bucket_q"] = app["bucket_q"], {}
        for pid, p in todo.items():
            proc = await asyncio.create_subprocess_exec("aws", "s3", "cp", "--only-show-errors", str(p),
                                                        f"{BUCKET}/{pid}.json", stdout=asyncio.subprocess.DEVNULL,
                                                        stderr=asyncio.subprocess.PIPE)
            _, err = await proc.communicate()
            if proc.returncode:
                print(f"bucket {pid}: {err.decode(errors='replace')[-200:]}", flush=True)


# ---- finalise and runs -----------------------------------------------------------------------------------------

async def finalise(req: web.Request) -> web.Response:
    cfg: Config = req.app["cfg"]
    pid = req.match_info["place_id"]
    try:
        body = await req.json()
    except ValueError:
        return jerr(400, "body is not JSON")
    sid = (body or {}).get("save_id", "")
    if not PLACE_ID.match(pid) or not SAVE_ID.match(sid or "") or sid == AUTOSAVE:
        return jerr(400, "finalise needs the save_id of a named save")
    if not req.app["saves"].read(pid, sid):
        return jerr(404, "no such save")
    run_id = f"{pid}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    rdir = cfg.out / "runs" / run_id
    if rdir.exists():
        return jerr(409, "a finalise started this second; try again")
    job = f"places-finalise-{run_id}"
    atomic_write(rdir / "run.json", json.dumps({"run_id": run_id, "place_id": pid, "save_id": sid, "job": job,
                                                "at": datetime.now(timezone.utc).isoformat()}).encode())
    cmd = [str(ROOT / "tooling" / "job_guard.sh"), "run", job, "--", "env", f"ARGONIA_RUN_ID={run_id}",
           sys.executable, "-m", "tools.places", "finalise", pid, sid]
    r = await asyncio.create_subprocess_exec(*cmd, cwd=ROOT, stdout=asyncio.subprocess.PIPE,
                                             stderr=asyncio.subprocess.STDOUT)
    out, _ = await r.communicate()
    if r.returncode:
        return jerr(500, "could not start the finalise job", log=out.decode(errors="replace")[-500:])
    return jok({"run_id": run_id}, status=202)


def tail(p: Path, n: int = 40) -> str:
    if not p.exists():
        return ""
    with p.open("rb") as f:
        f.seek(max(0, p.stat().st_size - 16384))
        return b"\n".join(f.read().splitlines()[-n:]).decode(errors="replace")


async def run_get(req: web.Request) -> web.Response:
    cfg: Config = req.app["cfg"]
    rid = req.match_info["run_id"]
    if not RUN_ID.match(rid):
        return jerr(400, "bad run id")
    rdir = cfg.out / "runs" / rid
    if not (rdir / "run.json").exists():
        return jerr(404, "no such run")
    run = json.loads((rdir / "run.json").read_text())
    if run.get("place_id") != req.match_info["place_id"]:
        return jerr(404, "no such run for this place")
    job = run["job"]
    st = json.loads((rdir / "state.json").read_text()) if (rdir / "state.json").exists() else {}
    alive = False
    try:
        os.kill(int((cfg.jobs / f"{job}.pid").read_text().strip()), 0)
        alive = True
    except (OSError, ValueError):
        pass
    rc = (cfg.jobs / f"{job}.rc").read_text().strip() if (cfg.jobs / f"{job}.rc").exists() else None
    state = st.get("state") or ("running" if alive else "done" if rc == "0" else "failed" if rc else "starting")
    if not alive and rc is not None and state == "running":
        state = "done" if rc == "0" else "failed"
    report = rdir / "report.md"
    return jok({"run_id": rid, "save_id": run["save_id"], "state": state, "step": st.get("step"), "rc": rc,
                "log": tail(cfg.jobs / f"{job}.log"),
                "report": report.read_text(encoding="utf-8") if report.exists() else None})


# ---- seat, heartbeat, status --------------------------------------------------------------------------------------

async def seat(req: web.Request) -> web.Response:
    cfg: Config = req.app["cfg"]
    pid = req.match_info["place_id"]
    try:
        x, y = float(req.query["x"]), float(req.query["y"])
    except (KeyError, ValueError):
        return jerr(400, "x= and y= are required numbers")
    try:
        r = await asyncio.get_running_loop().run_in_executor(None, links.seat_at, pid, x, y, cfg.out / "bundles",
                                                             cfg.places)
    except links.Missing as e:
        return jerr(503, f"seating is not built yet ({e})")
    except FileNotFoundError as e:
        return jerr(404, str(e))
    return jok(r)


async def heartbeat(req: web.Request) -> web.Response:
    if not req.app["cfg"].awake:
        return jok({"held": False, "disabled": True})
    r = await asyncio.get_running_loop().run_in_executor(None, awake.beat)
    return jok(r)


def git_sha() -> str:
    r = subprocess.run(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip()


async def status(req: web.Request) -> web.Response:
    from importlib.metadata import version

    from tools.places.search.embed import MODEL
    from tools.places.search.index import Index
    try:
        g = await asyncio.get_running_loop().run_in_executor(None, links.ground_status)
    except links.Missing as e:
        g = {"ground_sha": None, "deployed_sha": None, "match": None, "error": f"not built yet ({e})"}
    except Exception as e:  # the check failing is itself the answer the studio shows
        g = {"ground_sha": None, "deployed_sha": None, "match": False, "error": str(e)[:300]}
    ix = Index.open(req.app["cfg"].out / "search")
    return jok(g | {"versions": {"studio": req.app["sha"], "repo_head": git_sha(), "python": platform.python_version(),
                                 "aiohttp": version("aiohttp"), "search_model": MODEL, "search_rows": len(ix.rows)},
                    "awake": {"job_alive": awake.job_alive(), "release_after_s": awake.HOLD}})


# ---- the front end ----------------------------------------------------------------------------------------------

async def web_file(req: web.Request) -> web.StreamResponse:
    cfg: Config = req.app["cfg"]
    rel = req.match_info.get("path") or "index.html"
    p = inside(cfg.web, rel)
    if p is None and (cfg.web / rel).is_dir():
        p = inside(cfg.web, rel.rstrip("/") + "/index.html")
    return await send_file(req, p) if p else web.Response(status=404, text="not found")


@web.middleware
async def errors(req: web.Request, handler):
    try:
        return await handler(req)
    except web.HTTPException as e:
        if req.path.startswith("/api/"):
            return jerr(e.status, e.reason)
        raise


async def on_start(app: web.Application) -> None:
    app["tasks"] = [asyncio.create_task(commit_worker(app))]
    if app["cfg"].bucket:
        app["tasks"].append(asyncio.create_task(bucket_worker(app)))


async def on_stop(app: web.Application) -> None:
    for t in app["tasks"]:
        t.cancel()


def make_app(cfg: Config | None = None) -> web.Application:
    cfg = cfg or Config()
    app = web.Application(middlewares=[errors], client_max_size=64 * 1024 * 1024)
    app["cfg"], app["saves"] = cfg, Saves(cfg.places, cfg.out)
    app["locks"], app["pending"], app["bucket_q"] = {}, {}, {}
    app["commit_q"] = asyncio.Queue()
    app["sha"] = git_sha()
    r = app.router
    r.add_get("/api/places", places)
    r.add_get("/api/bundle/{bundle_id}/{path:.+}", bundle_file)
    r.add_get("/api/asset/mesh", asset_mesh)
    r.add_get("/api/asset/tex", asset_tex)
    r.add_get("/api/asset/thumb", asset_thumb)
    r.add_get("/api/search", search)
    r.add_get("/api/place/{place_id}/saves", saves_list)
    r.add_get("/api/place/{place_id}/saves/{save_id}", save_get)
    r.add_put("/api/place/{place_id}/saves/{save_id}", save_put)
    r.add_post("/api/place/{place_id}/finalise", finalise)
    r.add_get("/api/place/{place_id}/runs/{run_id}", run_get)
    r.add_get("/api/place/{place_id}/seat", seat)
    r.add_post("/api/heartbeat", heartbeat)
    r.add_get("/api/status", status)
    r.add_get("/", web_file)
    r.add_get("/{path:(?!api/).+}", web_file)
    app.on_startup.append(on_start)
    app.on_cleanup.append(on_stop)
    return app
