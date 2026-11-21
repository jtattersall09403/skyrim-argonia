"""What one place needs to be edited on a tablet with no connection (docs/design/place-studio.md, Offline).

`manifest` lists every URL the studio's front end asks for when it opens and edits the place, each with its size in
bytes, so the client downloads exactly that into the browser's own storage and never guesses: the app's files, the
place list and status, the place's bundles as served (the draft, our ground, the allocated source, the source rooms
its copied rooms are lit from), every mesh at the levels the views draw it, every texture those meshes name at the
sizes the views ask for, the thumbnails of every base the draft and the source hold, the land textures, and the
place's stock, needs, nav, notes and saves. Meshes, textures and thumbnails are converted here first, so each is
served from the cache when the tablet fetches it.

URLs are written exactly as the front end writes them (`encodeURIComponent` for a path part or a query value);
nothing of a game or mod file is written anywhere but the studio's own asset cache."""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlsplit

# Kinds the views draw with a model's light version (web/js/objects.js LIGHT), and kinds whose textures they ask
# for at no more than 256 pixels (objects.js SMALL_TEX).
LIGHT = {"tree", "plant", "groundcover", "rock"}
SMALL_TEX = {"tree", "plant", "groundcover", "rock", "clutter", "light", "marker", "other"}
SHELL_SKIP = ("test/", "dev/")
VERSION = 1   # the manifest's own shape


def enc(s: str) -> str:
    """JavaScript's encodeURIComponent."""
    return quote(str(s), safe="-_.!~*'()")


def shell_files(web: Path) -> list[Path]:
    """The app's own files: everything under web/ but its tests and dev tools."""
    out = []
    for p in sorted(web.rglob("*")):
        rel = p.relative_to(web).as_posix()
        if p.is_file() and not rel.startswith(SHELL_SKIP) and not p.name.startswith("."):
            out.append(p)
    return out


_ver: dict[str, tuple[tuple, str]] = {}


def web_version(web: Path) -> str:
    """A hash of the app's files (their paths and bytes): a new version of the studio has a new one."""
    files = shell_files(web)
    ident = tuple((p.relative_to(web).as_posix(), p.stat().st_size, p.stat().st_mtime_ns) for p in files)
    hit = _ver.get(str(web))
    if hit and hit[0] == ident:
        return hit[1]
    h = hashlib.sha256()
    for p in files:
        h.update(p.relative_to(web).as_posix().encode() + b"\0" + p.read_bytes() + b"\0")
    v = h.hexdigest()[:16]
    _ver[str(web)] = (ident, v)
    return v


def _jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()] if p.exists() else []


def glb_images(glb: Path) -> list[str]:
    """The texture URIs a GLB's materials draw with (base colour and emissive; the views never fetch a normal map)."""
    try:
        data = glb.read_bytes()
        if data[:4] != b"glTF":
            return []
        n, kind = struct.unpack_from("<II", data, 12)
        if kind != 0x4E4F534A:   # JSON
            return []
        g = json.loads(data[20:20 + n])
    except (OSError, ValueError, struct.error):
        return []
    used = set()
    for m in g.get("materials") or []:
        for t in ((m.get("pbrMetallicRoughness") or {}).get("baseColorTexture"), m.get("emissiveTexture")):
            if isinstance(t, dict) and isinstance(t.get("index"), int):
                used.add(t["index"])
    texs, imgs, out = g.get("textures") or [], g.get("images") or [], []
    for i in sorted(used):
        if i < len(texs) and isinstance(texs[i].get("source"), int) and texs[i]["source"] < len(imgs):
            uri = imgs[texs[i]["source"]].get("uri") or ""
            if uri and not uri.startswith("data:"):
                out.append(uri)
    return out


def sized(uri: str, kind: str) -> str:
    """objects.js `sized`: a small thing's texture asked for at no more than 256 pixels."""
    if kind not in SMALL_TEX:
        return uri
    parts = urlsplit(uri)
    q = parse_qsl(parts.query, keep_blank_values=True)
    if not any(k == "size" for k, _ in q):
        return uri
    import re
    return re.sub(r"([?&]size=)(\d+)", lambda m: m.group(1) + str(min(int(m.group(2)), 256)), uri, count=1)


class Bundles:
    """The bundles one place opens with, as the front end reads them (web/js/bundle.js loadBundle)."""

    def __init__(self, out: Path, places: Path, place_id: str):
        self.out, self.places, self.pid = out, places, place_id
        pj = places / place_id / "place.json"
        self.place = json.loads(pj.read_text(encoding="utf-8")) if pj.exists() else {}
        self.source_id = self.place.get("source_id")

    def dir(self, bid: str) -> Path:
        from tools.places import variant
        return self.out / "bundles" / variant.bundle(bid)   # a variant stands on its place's ground

    def ids(self) -> list[str]:
        out = [f"ground.{self.pid}", f"draft.{self.pid}"]
        if self.source_id:
            out.append(f"src.{self.source_id}")
        return [b for b in out if (self.dir(b) / "bundle.json").exists()]

    def files(self, bid: str) -> list[str]:
        """Every file of a bundle the front end asks for, as its path under /api/bundle/<bid>/."""
        d = self.dir(bid)
        meta = json.loads((d / "bundle.json").read_text(encoding="utf-8"))
        rel = ["bundle.json", "bases.jsonl", "npcs.jsonl"]
        for sid in meta.get("spaces") or ["exterior"]:
            s = f"spaces/{enc(sid)}/"
            rel += [s + "space.json", s + "refs.jsonl"]
            if (d / "spaces" / sid / "terrain.json").exists():
                rel += [s + "terrain.json", s + "terrain.f32"]
        if bid.startswith("draft."):
            rel += [f"{f}.jsonl" for f in ("people", "paths", "clear", "land", "walk")]
        return [r for r in rel if (d / _unenc(r)).is_file()]

    def rooms(self) -> list[tuple[str, str]]:
        """The source rooms the draft's copied rooms are lit from (main.js roomInfo): (bundle id, space id)."""
        d, out = self.dir(f"draft.{self.pid}"), []
        if not (d / "bundle.json").exists():
            return out
        for sj in sorted((d / "spaces").glob("*/space.json")):
            copy_of = (json.loads(sj.read_text(encoding="utf-8")) or {}).get("copy_of") or ""
            if "/" in copy_of:
                src, cell = copy_of.rsplit("/", 1)
                if (self.dir(f"src.{src}") / "spaces" / cell / "space.json").exists():
                    out.append((f"src.{src}", cell))
        return sorted(set(out))

    def models(self) -> dict[tuple[str, int], set[str]]:
        """(model, level) -> the kinds that draw it: every placed ref's base, every base of the source (what can be
        added from it), and the grass the land textures grow."""
        out: dict[tuple[str, int], set[str]] = {}

        def want(model, kind):
            if model:
                kind = kind or "other"
                out.setdefault((model, 1 if kind in LIGHT else 0), set()).add(kind)
        for bid in self.ids():
            d = self.dir(bid)
            bases = {b["key"]: b for b in _jsonl(d / "bases.jsonl")}
            for refs in d.glob("spaces/*/refs.jsonl"):
                for r in _jsonl(refs):
                    b = bases.get(r.get("base"))
                    if b:
                        want(b.get("model"), r.get("kind") or b.get("kind"))
            if bid.startswith(("src.", "draft.")):
                for b in bases.values():
                    want(b.get("model"), b.get("kind"))
            for t in d.glob("spaces/*/terrain.json"):
                for lt in (json.loads(t.read_text(encoding="utf-8")).get("ltex") or {}).values():
                    for g in lt.get("grasses") or []:
                        want(g.get("model"), "groundcover")
        return out

    def thumbs(self) -> list[str]:
        """Models whose thumbnail the panels show: the draft's and the source's bases."""
        out = set()
        for bid in self.ids():
            if bid.startswith(("src.", "draft.")):
                out |= {b["model"] for b in _jsonl(self.dir(bid) / "bases.jsonl") if b.get("model")}
        return sorted(out)

    def ltex(self) -> dict[str, dict]:
        out = {}
        for bid in self.ids():
            for t in self.dir(bid).glob("spaces/*/terrain.json"):
                out |= json.loads(t.read_text(encoding="utf-8")).get("ltex") or {}
        return out

    def stamps(self) -> dict:
        out = {}
        for bid in self.ids():
            meta = json.loads((self.dir(bid) / "bundle.json").read_text(encoding="utf-8"))
            out[bid.split(".", 1)[0]] = (meta.get("stamp") or {}).get("key")
        return out


def _unenc(rel: str) -> str:
    from urllib.parse import unquote
    return unquote(rel)


def _size(p) -> int:
    try:
        return Path(p).stat().st_size if p else 0
    except OSError:
        return 0


def manifest(place_id: str, out: Path, places: Path, web: Path, asset, saves: list[str]) -> dict:
    """Every URL the place needs offline with its size: {place_id, version, web, stamps, files: [{url, bytes, kind}],
    bytes, counts}. `asset(kind, *args)` is links.asset (converts on demand); `saves` the place's save ids."""
    B = Bundles(out, places, place_id)
    if not B.ids():
        raise FileNotFoundError(f"no bundle for {place_id}")
    files: list[dict] = []

    def add(url, size, kind):
        files.append({"url": url, "bytes": int(size or 0), "kind": kind})

    for p in shell_files(web):
        add("/" + p.relative_to(web).as_posix(), p.stat().st_size, "app")
    add("/", (web / "index.html").stat().st_size if (web / "index.html").exists() else 0, "app")
    for u in ("/api/places", "/api/status"):
        add(u, 0, "api")
    for u in ("stock", "needs", "quests", "nav", "notes", "saves"):
        add(f"/api/place/{place_id}/{u}", 0, "api")
    for sid in saves:
        add(f"/api/place/{place_id}/saves/{enc(sid)}", 0, "api")
    for bid in B.ids():
        for rel in B.files(bid):
            add(f"/api/bundle/{bid}/{rel}", _size(B.dir(bid) / _unenc(rel)), "bundle")
    for bid, cell in B.rooms():
        u = f"/api/bundle/{bid}/spaces/{enc(cell)}/space.json"
        if not any(f["url"] == u for f in files):
            add(u, _size(B.dir(bid) / "spaces" / cell / "space.json"), "bundle")
    # meshes at the levels the views draw them, then the textures they name at the sizes the views ask for
    tex_kinds: dict[str, set[str]] = {}
    for (model, level), kinds in sorted(B.models().items()):
        glb = asset("mesh", model, level)
        add(f"/api/asset/mesh?model={enc(model)}&level={level}", _size(glb), "mesh")
        for uri in glb_images(Path(glb)) if glb else []:
            tex_kinds.setdefault(uri, set()).update(kinds)
    tex_urls = sorted({sized(u, k) for u, ks in tex_kinds.items() for k in ks})
    for u in tex_urls:
        q = dict(parse_qsl(urlsplit(u).query))
        try:
            p = asset("tex", q.get("path", ""), int(q.get("size", "512")))
        except (FileNotFoundError, ValueError):
            p = None
        except Exception:   # noqa: BLE001  a texture the converter cannot read is served as the grey stand-in
            p = None
        add(u, _size(p) or 64, "texture")
    for model in B.thumbs():
        add(f"/api/asset/thumb?model={enc(model)}", _size(asset("thumb", model)), "thumb")
    land = asset("land")
    if land:
        add("/api/asset/land", _size(land), "land")
        table = json.loads(Path(land).read_text(encoding="utf-8"))
        for key, lt in sorted(B.ltex().items()):
            row = table.get(key) or {}
            if row.get("file"):
                add(f"/api/asset/land/{enc(row['file'])}", _size(Path(land).parent / row["file"]), "land")
            elif lt.get("diffuse"):   # terrain_mesh.js: no converted land texture, the diffuse at 256
                add(f"/api/asset/tex?path={enc(lt['diffuse'])}&size=256", 0, "land")
    seen, uniq = set(), []
    for f in files:
        if f["url"] not in seen:
            seen.add(f["url"])
            uniq.append(f)
    counts: dict[str, int] = {}
    for f in uniq:
        counts[f["kind"]] = counts.get(f["kind"], 0) + 1
    return {"version": VERSION, "place_id": place_id, "web": web_version(web), "stamps": B.stamps(),
            "files": uniq, "bytes": sum(f["bytes"] for f in uniq), "counts": counts}
