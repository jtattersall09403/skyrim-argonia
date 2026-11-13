"""The studio server (docs/design/place-studio.md, Studio API): aiohttp on localhost, reached only through the
Cloudflare tunnel behind Access. Serves the API, the bundles and the front end (web/), compressed (brotli or
gzip, cached on disk), with ETags and range requests."""
from __future__ import annotations

import asyncio
import gzip
import hashlib
import json
import math
import mimetypes
import os
import time
import platform
import re
import subprocess
from pathlib import Path

import warnings

from aiohttp import web

from tools.places import navexport, needs, notes
from tools.places.studio import awake, links
from tools.places.studio.saves import AUTOSAVE, PLACE_ID, SAVE_ID, Conflict, Saves, atomic_write

ROOT = Path(__file__).resolve().parents[3]
WEB = Path(__file__).resolve().parent / "web"
NO_COMPRESS = {".webp", ".png", ".jpg", ".jpeg", ".gz", ".br", ".zip", ".woff2", ".mp4"}
RUN_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
warnings.filterwarnings("ignore", category=web.NotAppKeyWarning)
NOTE_BYTES = 512 * 1024   # a note: 4,000 characters of words and up to 200 things
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
        self.sources = Path(os.environ.get("NEWWORLD_SOURCES", ROOT / "newworld" / "sources"))


def jerr(status: int, msg: str, **extra) -> web.Response:
    return web.json_response({"error": msg} | extra, status=status)


def jok(data, status: int = 200, **kw) -> web.Response:
    r = web.json_response(data, status=status, dumps=lambda o: json.dumps(o, ensure_ascii=False), **kw)
    r.headers["Cache-Control"] = "no-store"
    return r


async def body_capped(req: web.Request, limit: int) -> bytes:
    """The request's body, refused with 413 once it runs past limit (the app's own cap is sized for a save)."""
    buf = bytearray()
    async for chunk in req.content.iter_chunked(65536):
        buf += chunk
        if len(buf) > limit:
            raise web.HTTPRequestEntityTooLarge(max_size=limit, actual_size=len(buf))
    return bytes(buf)


async def json_capped(req: web.Request, limit: int):
    try:
        return json.loads(await body_capped(req, limit))
    except ValueError:
        raise web.HTTPBadRequest(reason="body is not JSON") from None


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
        # the ETag names the source file's state, so a reload of an unchanged bundle costs a 304, not megabytes
        etag = f'"{key[:20]}-{enc}"'
        if etag in req.headers.get("If-None-Match", ""):
            return web.Response(status=304, headers={"ETag": etag, "Cache-Control": cache, "Vary": "Accept-Encoding"})
        headers["Content-Encoding"] = enc
        r = web.FileResponse(z, headers=headers)
        r.headers["ETag"] = etag
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


async def fresh_draft(app: web.Application, pid: str) -> str | None:
    """Rebuild draft.<pid> when its key is stale (off the event loop; concurrent callers wait on one build).
    Returns an error message, or None."""
    from tools.places import draft_bundle
    cfg: Config = app["cfg"]
    if not (cfg.places / pid / "spaces").exists():
        return None
    loop = asyncio.get_running_loop()
    async with app["draft_locks"].setdefault(pid, asyncio.Lock()):
        try:
            await loop.run_in_executor(None, draft_bundle.build, pid, cfg.places, cfg.out / "bundles")
        except Exception as e:  # a half-written redraft: show the last good bundle and say why
            print(f"draft bundle {pid}: {e!r}", flush=True)
            return f"the draft bundle could not be rebuilt: {e}"
    return None


async def places(req: web.Request) -> web.Response:
    cfg: Config = req.app["cfg"]
    titles = place_titles()
    out = []
    for pj in sorted(cfg.places.glob("*/place.json")):
        pid = pj.parent.name
        draft_error = await fresh_draft(req.app, pid)
        draft = bundle_stamp(cfg, f"draft.{pid}")
        draft_error = ([{"error": draft_error}] if draft_error else []) + list((draft or {}).get("missing_bases") or [])
        if draft is None and not (pj.parent / "spaces").exists():
            continue
        pl = json.loads(pj.read_text(encoding="utf-8"))
        out.append({"place_id": pid, "title": titles.get(pid) or pl.get("title") or pid,
                    "source_id": pl.get("source_id"), "similar": pl.get("similar") or [],
                    "stamps": {"draft": draft, "ground": bundle_stamp(cfg, f"ground.{pid}"),
                               "source": bundle_stamp(cfg, f"src.{pl.get('source_id')}")},
                    "fit": pl.get("fit"),
                    **({"draft_error": draft_error} if draft_error else {})})
    return jok(out)


async def bundle_file(req: web.Request) -> web.StreamResponse:
    cfg: Config = req.app["cfg"]
    bid = req.match_info["bundle_id"]
    if not RUN_ID.match(bid):
        return jerr(400, "bad bundle id")
    if bid.startswith("draft.") and req.match_info["path"] == "bundle.json":
        await fresh_draft(req.app, bid[len("draft."):])
    p = inside(cfg.out / "bundles" / bid, req.match_info["path"])
    return await send_file(req, p) if p else jerr(404, "no such bundle file")


# ---- assets and search -----------------------------------------------------------------------------------------

def assets_retry() -> str:
    from tools.places import assets
    return assets.RETRY


async def asset(req: web.Request, kind: str, args: tuple, cache: str = "public, max-age=86400"):
    """Lane A converts synchronously (a cold mesh is under a second), off the event loop."""
    try:
        p = await asyncio.get_running_loop().run_in_executor(None, links.asset, kind, *args)
    except FileNotFoundError as e:
        return jerr(404, str(e))
    if p is None or not p.exists():
        return jerr(404, f"no such {kind}")
    if f".{assets_retry()}." in p.name:   # a stand-in for a conversion that will be tried again: never kept
        cache = "no-store"
    return await send_file(req, p, cache=cache)


async def asset_mesh(req: web.Request):
    m, lv = req.query.get("model"), req.query.get("level", "0")
    if not m:
        return jerr(400, "model= is required")
    if lv not in ("0", "1"):
        return jerr(400, "level is 0 or 1")
    return await asset(req, "mesh", (m, int(lv)))


MISSING_TEX: dict = {}


def missing_tex() -> bytes:
    """A 4x4 neutral grey WebP for a texture the profile lacks."""
    if "b" not in MISSING_TEX:
        import io

        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (4, 4), (128, 128, 128)).save(buf, "WEBP", lossless=True)
        MISSING_TEX["b"] = buf.getvalue()
    return MISSING_TEX["b"]


async def asset_tex(req: web.Request):
    p = req.query.get("path")
    if not p:
        return jerr(400, "path= is required")
    try:
        size = int(req.query.get("size", "512"))
    except ValueError:
        return jerr(400, "size must be a number")
    cache = "public, max-age=2592000, immutable"
    try:
        f = await asyncio.get_running_loop().run_in_executor(None, links.asset, "tex", p, size)
    except FileNotFoundError:
        f = None
    except Exception as e:  # a texture the converter cannot read is logged here and drawn as the stand-in
        print(f"texture {p}: {type(e).__name__}: {e}"[:300], flush=True)
        f = None
    if f is None or not f.exists():  # the profile lacks it: a neutral stand-in, marked, so the console stays clean
        return web.Response(body=missing_tex(), content_type="image/webp",
                            headers={"Cache-Control": "public, max-age=86400", "X-Argonia-Missing": "1"})
    return await send_file(req, f, cache=cache)


async def asset_thumb(req: web.Request):
    m = req.query.get("model")
    return await asset(req, "thumb", (m,)) if m else jerr(400, "model= is required")


async def asset_land(req: web.Request):
    return await asset(req, "land", (), cache="no-cache")


async def asset_land_file(req: web.Request):
    t = await asyncio.get_running_loop().run_in_executor(None, links.asset, "land")
    p = inside(t.parent, req.match_info["file"]) if t else None
    return await send_file(req, p, cache="public, max-age=86400") if p else jerr(404, "no such land texture")


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


# ---- what a place holds and who its people are (Stock) -------------------------------------------------------------

def _stock_args(req: web.Request):
    from tools.places.studio import stock
    cfg: Config = req.app["cfg"]
    return stock, stock.Sources(cfg.sources), cfg.out / "catalogue" / "bases.jsonl"


async def stock_get(req: web.Request) -> web.Response:
    """The place's identities and stock from the database's sources, with the items' facts and the scale."""
    pid = req.match_info["place_id"]
    if not PLACE_ID.match(pid):
        return jerr(400, "bad place id")
    stock, src, cat = _stock_args(req)
    out = await asyncio.get_running_loop().run_in_executor(
        None, lambda: stock.payload(pid, src, stock.Catalogue.open(cat)))
    return jok(out)


async def items_get(req: web.Request) -> web.Response:
    """Item search for adding to a holder: each result says whether this place may hold it, and why not."""
    pid = req.match_info["place_id"]
    if not PLACE_ID.match(pid):
        return jerr(400, "bad place id")
    try:
        limit = max(1, min(60, int(req.query.get("limit", "30"))))
    except ValueError:
        return jerr(400, "limit must be a number")
    stock, src, cat = _stock_args(req)
    q, kind = req.query.get("q", ""), req.query.get("kind") or None
    out = await asyncio.get_running_loop().run_in_executor(
        None, lambda: stock.search(pid, q, kind, limit, src, stock.Catalogue.open(cat)))
    return jok(out)


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
        if finalising(req.app, pid, sid):
            return jerr(409, "this save is being finalised, so it can no longer change; save under a new name",
                        current={"final": True})
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


async def nav_get(req: web.Request) -> web.StreamResponse:
    """The built place's walking mesh (tools/places/navexport.py), exported again when the plugin was rebuilt (one
    export at a time for a place: tabs that ask together wait on the same one)."""
    pid = req.match_info["place_id"]
    if not PLACE_ID.match(pid):
        return jerr(400, "bad place id")
    async with req.app["nav_locks"].setdefault(pid, asyncio.Lock()):
        p = await asyncio.get_running_loop().run_in_executor(None, navexport.current, pid, req.app["cfg"].out)
    return await send_file(req, p) if p else jerr(404, "this place has not been built")


async def notes_get(req: web.Request) -> web.Response:
    """The owner's notes on a place (tools/places/notes.py), oldest first."""
    try:
        return jok(notes.read(req.match_info["place_id"], req.app["cfg"].places))
    except ValueError as e:
        return jerr(400, str(e))


async def notes_post(req: web.Request) -> web.Response:
    """Add a note ({text, things, view, save}), or close or reopen one ({id, done})."""
    pid, cfg = req.match_info["place_id"], req.app["cfg"]
    body = await json_capped(req, NOTE_BYTES)
    try:
        if not isinstance(body, dict):
            raise ValueError("body must be a note")
        async with req.app["locks"].setdefault(pid, asyncio.Lock()):
            note = (notes.done(pid, str(body["id"]), places=cfg.places, undo=not body.get("done", True)) if body.get("id")
                    else notes.add(pid, body, cfg.places))
    except (ValueError, TypeError) as e:
        return jerr(400, str(e))
    p = notes.path(pid, cfg.places)
    if cfg.commit and p.is_relative_to(ROOT):
        rel = str(p.relative_to(ROOT))
        req.app["pending"][rel] = True
        await req.app["commit_q"].put((rel, f"places: the owner's studio note {pid}/{note['id']}"))
    return jok(note)


async def needs_get(req: web.Request) -> web.Response:
    """What the stories need of the place and what they use its people for (tools/places/needs.py), in plain words."""
    pid, cfg = req.match_info["place_id"], req.app["cfg"]
    if not PLACE_ID.match(pid):
        return jerr(400, "bad place id")
    out = await asyncio.get_running_loop().run_in_executor(
        None, lambda: needs.payload(pid, cfg.sources / "needs", cfg.sources / "people"))
    return jok(out)


async def needs_changed_post(req: web.Request) -> web.Response:
    """The owner carried on past a need's warning ({need | person, change, what, save}): the edit stands as any other,
    and the need is marked changed by the owner, for the story to be changed to fit the place."""
    pid, cfg = req.match_info["place_id"], req.app["cfg"]
    body = await json_capped(req, NOTE_BYTES)
    try:
        if not isinstance(body, dict):
            raise ValueError("body must be a change")
        row = await asyncio.get_running_loop().run_in_executor(
            None, lambda: needs.record_change(pid, body, cfg.sources / "needs"))
    except (ValueError, TypeError) as e:
        return jerr(400, str(e))
    p = needs.changes_path(pid, cfg.sources / "needs")
    if cfg.commit and p.is_relative_to(ROOT):
        rel = str(p.relative_to(ROOT))
        req.app["pending"][rel] = True
        await req.app["commit_q"].put((rel, f"places: the owner changed what a story needs, {pid}"))
    return jok(row)


COMMIT_TRIES, COMMIT_WAIT_S = 6, 5.0


async def commit_worker(app: web.Application) -> None:
    """Commit and push each named save and the notes by path, one at a time. A commit that fails (the finalise
    chain or an agent committing in the same tree at that moment, the network) is tried again after a wait, a few
    times, then left for the next write of that file; a file another commit already carried is done."""
    q: asyncio.Queue = app["commit_q"]
    tries: dict[str, int] = {}
    loop = asyncio.get_running_loop()
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
            if proc.returncode == 0 or b"nothing to commit" in out:
                app["pending"].pop(path, None)
                tries.pop(path, None)
            elif tries.get(path, 0) + 1 < COMMIT_TRIES:
                tries[path] = tries.get(path, 0) + 1
                loop.call_later(COMMIT_WAIT_S * tries[path], q.put_nowait, (path, m))
            else:
                tries.pop(path, None)


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

def finalising(app: web.Application, pid: str, sid: str) -> bool:
    """True from the moment a save's finalise is accepted until its chain ends: the chain reads the save and writes
    it back final, so a write in between would be lost. A chain that failed leaves the save open to change again."""
    t = app["finalising"].get((pid, sid))
    if t is None:
        return False
    job = app["cfg"].jobs / f"finalise.{pid}.{sid}"

    def since(suffix: str) -> bool:   # the job's file of this run (an earlier run of the same save leaves older ones)
        try:
            return Path(f"{job}.{suffix}").stat().st_mtime >= t
        except OSError:
            return False
    over = since("rc") or (time.time() - t > 120 and not since("pid"))   # ended, or never started
    if over:
        del app["finalising"][(pid, sid)]
    return not over


async def finalise(req: web.Request) -> web.Response:
    pid = req.match_info["place_id"]
    body = await json_capped(req, 4096)
    sid = body.get("save_id", "") if isinstance(body, dict) else ""
    if not isinstance(sid, str) or not PLACE_ID.match(pid) or not SAVE_ID.match(sid) or sid == AUTOSAVE:
        return jerr(400, "finalise needs the save_id of a named save")
    if not req.app["saves"].read(pid, sid):
        return jerr(404, "no such save")
    async with req.app["locks"].setdefault(pid, asyncio.Lock()):   # after any write of the save now in hand
        req.app["finalising"][(pid, sid)] = time.time()
    # the save's own commit lands first: the chain commits the same file, and two commits of it at once collide
    rel = str(req.app["saves"].path(pid, sid).relative_to(ROOT)) if req.app["cfg"].commit else None
    for _ in range(120):
        if not rel or not req.app["pending"].get(rel):
            break
        await asyncio.sleep(0.5)
    run_id = await asyncio.get_running_loop().run_in_executor(None, links.run_start, pid, sid)
    return jok({"run_id": run_id}, status=202)


async def run_get(req: web.Request) -> web.Response:
    """The contract's {run_id, save_id, state, step, rc, log, report} over lane F's read_run (kept whole beside)."""
    cfg: Config = req.app["cfg"]
    rid, pid = req.match_info["run_id"], req.match_info["place_id"]
    if not RUN_ID.match(rid) or not rid.startswith(pid + "."):
        return jerr(404, "no such run for this place")
    rdir = cfg.out / "runs" / rid
    job = cfg.jobs / f"finalise.{rid}"
    pidf, rcf = Path(f"{job}.pid"), Path(f"{job}.rc")
    if not rdir.exists() and not pidf.exists():
        return jerr(404, "no such run")
    st = await asyncio.get_running_loop().run_in_executor(None, links.run_read, rdir)
    rc = rcf.read_text().strip() if rcf.exists() else None
    state = st.get("state")
    if state in (None, "queued"):
        state = "starting" if rc is None else ("done" if rc == "0" else "failed")
    elif state == "running" and rc is not None:
        state = "done" if rc == "0" else "failed"
    return jok(st | {"run_id": rid, "save_id": st.get("save_id") or rid[len(pid) + 1:], "state": state,
                     "step": st.get("step"), "rc": rc, "log": "\n".join(st.get("log_tail") or []),
                     "report": st.get("report_md")})


# ---- seat, heartbeat, status --------------------------------------------------------------------------------------

async def seat(req: web.Request) -> web.Response:
    cfg: Config = req.app["cfg"]
    pid = req.match_info["place_id"]
    if not PLACE_ID.match(pid):
        return jerr(400, "bad place id")
    try:
        x, y = float(req.query["x"]), float(req.query["y"])
    except (KeyError, ValueError):
        return jerr(400, "x= and y= are required numbers")
    if not (math.isfinite(x) and math.isfinite(y)):
        return jerr(400, "x= and y= are required numbers")
    try:
        r = await asyncio.get_running_loop().run_in_executor(None, links.seat_at, pid, x, y, cfg.out / "bundles",
                                                             cfg.places)
    except FileNotFoundError as e:
        return jerr(404, str(e))
    return jok(r)


async def heartbeat(req: web.Request) -> web.Response:
    if not req.app["cfg"].awake:
        return jok({"held": False, "disabled": True})
    r = await asyncio.get_running_loop().run_in_executor(None, awake.beat)
    return jok(r)


async def client_log(req: web.Request) -> web.Response:
    """What the studio page reports about itself (load stages, errors, the device's graphics): one line each in
    out/places/studio-client.log, so a fault on the owner's tablet can be read here."""
    try:   # the first 4,000 bytes; the rest is never read
        head = await req.content.readexactly(4000)
    except asyncio.IncompleteReadError as e:
        head = e.partial
    body = head.decode("utf-8", "replace")
    line = json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "ua": req.headers.get("User-Agent", "")[:200],
                       "body": body}, ensure_ascii=False)
    log = req.app["cfg"].out / "studio-client.log"
    if log.exists() and log.stat().st_size > 2_000_000:
        log.write_text("")
    with open(log, "a") as f:
        f.write(line + "\n")
    return web.Response(status=204)


def git_sha() -> str:
    r = subprocess.run(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip()


async def status(req: web.Request) -> web.Response:
    from importlib.metadata import version

    from tools.places.search.embed import MODEL
    from tools.places.search.index import Index
    try:
        g = await asyncio.get_running_loop().run_in_executor(None, links.ground_status)
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


async def atlas_file(req: web.Request) -> web.StreamResponse:
    """The Atlas (the world map page built by `python3 -m tools.newworld.map_page`), served read-only as it was
    built, so the studio can show it without a copy of its code; 404 when it has not been built."""
    base = Path(os.environ.get("STUDIO_ATLAS", ROOT / "out" / "newworld" / "map"))
    p = inside(base, req.match_info.get("path") or "index.html")
    return await send_file(req, p) if p else web.Response(status=404, text="the Atlas has not been built")


def access(req: web.Request, status: int) -> None:
    """One line per request for the page and its scripts in out/places/studio-access.log (not the bundles, assets
    or heartbeats): which device asked for what and what it got, so a page that will not start on one device can
    be traced here."""
    if req.path.startswith(("/api/asset/", "/api/bundle/", "/api/heartbeat", "/api/clientlog", "/vendor/")):
        return
    log = req.app["cfg"].out / "studio-access.log"
    try:
        if log.exists() and log.stat().st_size > 2_000_000:
            log.write_text("")
        with open(log, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {status} {req.method} {req.path_qs[:200]} "
                    f"| {req.headers.get('User-Agent', '')[:160]}\n")
    except OSError:
        pass


@web.middleware
async def errors(req: web.Request, handler):
    try:
        r = await handler(req)
        access(req, r.status)
        return r
    except web.HTTPException as e:
        access(req, e.status)
        if req.path.startswith("/api/"):
            return jerr(e.status, e.reason)
        raise


def warm_search(out: Path) -> None:
    """Load the index and the model at start, so the first query is as fast as the rest."""
    from tools.places.search.index import Index
    ix = Index.open(out / "search")
    if ix.rows:
        ix.embed(["warm"])


async def on_start(app: web.Application) -> None:
    asyncio.get_running_loop().run_in_executor(None, warm_search, app["cfg"].out)
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
    app["draft_locks"], app["nav_locks"], app["finalising"] = {}, {}, {}
    app["locks"], app["pending"], app["bucket_q"] = {}, {}, {}
    app["commit_q"] = asyncio.Queue()
    app["sha"] = git_sha()
    r = app.router
    r.add_get("/api/places", places)
    r.add_get("/api/bundle/{bundle_id}/{path:.+}", bundle_file)
    r.add_get("/api/asset/mesh", asset_mesh)
    r.add_get("/api/asset/tex", asset_tex)
    r.add_get("/api/asset/thumb", asset_thumb)
    r.add_get("/api/asset/land", asset_land)
    r.add_get("/api/asset/land/{file:.+}", asset_land_file)
    r.add_get("/api/search", search)
    r.add_get("/api/place/{place_id}/saves", saves_list)
    r.add_get("/api/place/{place_id}/saves/{save_id}", save_get)
    r.add_put("/api/place/{place_id}/saves/{save_id}", save_put)
    r.add_post("/api/place/{place_id}/finalise", finalise)
    r.add_get("/api/place/{place_id}/nav", nav_get)
    r.add_get("/api/place/{place_id}/notes", notes_get)
    r.add_get("/api/place/{place_id}/stock", stock_get)
    r.add_get("/api/place/{place_id}/items", items_get)
    r.add_post("/api/place/{place_id}/notes", notes_post)
    r.add_get("/api/place/{place_id}/needs", needs_get)
    r.add_post("/api/place/{place_id}/needs/changed", needs_changed_post)
    r.add_get("/api/place/{place_id}/runs/{run_id}", run_get)
    r.add_get("/api/place/{place_id}/seat", seat)
    r.add_post("/api/heartbeat", heartbeat)
    r.add_post("/api/clientlog", client_log)
    r.add_get("/api/status", status)
    r.add_get("/atlas/{path:.*}", atlas_file)
    r.add_get("/", web_file)
    r.add_get("/{path:(?!api/).+}", web_file)
    app.on_startup.append(on_start)
    app.on_cleanup.append(on_stop)
    return app
