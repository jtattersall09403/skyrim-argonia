#!/usr/bin/env python3
"""The Argonia profile: every row of mods/dependencies.json fetched, verified, staged and laid over a clean Data on
the game machine, with exact undo.

  stack.py fetch [--record] [--only ID ...]   download each row to ~/.argonia/mods (local, then the private cache in S3,
                                              then the Nexus API or GitHub); check sha256; --record writes new hashes
  stack.py stage [--dev] [--into DIR]         unpack and place each row into ~/.argonia/stack/MO2/mods/<id>/, apply
                                              the recorded FOMOD choices and ini settings, write the profile
                                              (modlist, plugins.txt, loadorder.txt) and installed.json (every file's hash)
  stack.py plan [--dev]                       what stage would unpack and the room it needs (JSON)
  stack.py push                               send changed mod folders and the profile to C:\\argonia\\MO2 on the machine
  stack.py install [--dev] [--skip-fetch]     fetch, stage, push, then on the machine: stack.ps1 off (bare Data), Pandora,
                                              the animation-data patch (no game launch: agents never run it)
  stack.py animdata                           after Pandora: the root motion its animation data lacks (animdata.py)
  stack.py menu                               launch through SKSE, wait for the main menu, list each DLL's load
  stack.py verify [--full]                    archives against the manifest; every laid file in Data against installed.json
  stack.py prune | evict                      cut a verified big row to its plugins | delete local archives once cached

Machine: `stack.py --machine NAME <cmd>` (or ARGONIA_PLAY) drives that game machine; the default is argonia-play.
`stack.ps1 on` always starts from bare Data, which is the exact undo. Nothing staged here is committed (decision 0003).
"""
import argparse
import fnmatch
import hashlib
import json
import os
import pathlib
import re
import shutil
import struct
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
MANIFEST = REPO / "mods" / "dependencies.json"
HOME = pathlib.Path.home()
MODS = HOME / ".argonia" / "mods"
STACK = HOME / ".argonia" / "stack"
MO2 = STACK / "MO2"
PROFILE = "Argonia"  # the BM&V world: every play row
NEWWORLD = "NewWorld"  # the new world (phase nw-02): every play row, then the newworld rows


def installed_name(profile):
    return "installed.json" if profile == PROFILE else f"installed-{profile}.json"
RUN = str(HERE / "run.sh")


def per_machine(path: pathlib.Path) -> pathlib.Path:
    """argonia-play keeps the old path; another machine (ARGONIA_PLAY) gets <name>-<machine> beside it."""
    m = os.environ.get("ARGONIA_PLAY", "argonia-play")
    return path if m == "argonia-play" else path.with_name(f"{path.name}-{m}")
API = "https://api.nexusmods.com/v1"
CACHE_BUCKET = "argonia-private-050977237313"
GAME_DATA = r"C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data" + "\\"
MAX_PATH = 259  # Skyrim's loose-file scan overruns a MAX_PATH buffer on any path of 260+ characters (0.0)
DATA_DIRS = {"meshes", "textures", "scripts", "skse", "interface", "sound", "music", "seq", "nemesis_engine",
             "pandora_engine", "mcm", "source", "strings", "video", "lodsettings", "grass", "shadersfx", "calientetools",
             "netscriptframework", "dyndolod", "materials", "platform"}
PLUGIN_EXT = (".esp", ".esm", ".esl")
RESERVE = 10 << 30  # the build VM's disk is shared by every lane: no write over 2 GB may leave less than this free


def room(need, what):
    """Refuse a write of `need` bytes that would leave under RESERVE free on the build VM (planner, 2026-10-29)."""
    free = shutil.disk_usage(HOME).free
    if need > (2 << 30) and free - need < RESERVE:
        raise SystemExit(f"{what}: needs {need >> 30} GB, {free >> 30} GB free; would leave under {RESERVE >> 30} GB")


# ---- manifest -----------------------------------------------------------------------------------------------------

def manifest():
    return json.loads(MANIFEST.read_text())


def save_manifest(doc):
    MANIFEST.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")


def chosen(doc, dev):
    """The rows stage places, in load order: play and newworld rows (dev rows with --dev). The Argonia profile lays
    all but the newworld rows; the NewWorld profile lays them all (profile_rows)."""
    return [m for m in doc["mods"] if m["profile"] in ("play", NEWWORLD.lower()) or (m["profile"] == "dev" and dev)]


def profile_rows(rows, profile):
    return [m for m in rows if profile == NEWWORLD or m["profile"] != NEWWORLD.lower()]


# ---- fetch --------------------------------------------------------------------------------------------------------

def secret(name):
    for line in (HOME / ".argonia" / "secrets.env").read_text().splitlines():
        m = re.match(rf"\s*(?:export\s+)?{name}=(.+)", line)
        if m:
            return m.group(1).strip().strip('"')
    raise SystemExit(f"{name} missing from ~/.argonia/secrets.env")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while c := f.read(1 << 22):
            h.update(c)
    return h.hexdigest()


def archive_path(m):
    s = m["source"]
    if "nexus" in s:
        have = [f for f in MODS.glob(f"{s['mod']}-{s['file']}-*") if f.stat().st_size > 0 and not f.name.endswith(".part")]
        return have[0] if have else MODS / f"{s['mod']}-{s['file']}-{m['archive']}"
    if "github" in s:
        return MODS / f"gh-{s['github'].replace('/', '_')}-{s['asset']}"
    if "built" in s:  # our own build (skse_build.sh pack): a tar of the plugin and its ini
        return MODS / f"built-{s['built']}.tar"
    return MODS / f"vault-{s['vault']}.tar"


def download(url, dest, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "argonia-stack/0.2", **(headers or {})})
    tmp = dest.with_name(dest.name + ".part")
    with urllib.request.urlopen(req, timeout=600) as r, open(tmp, "wb") as f:
        while c := r.read(1 << 20):
            f.write(c)
    tmp.rename(dest)


def s3(*args):
    return subprocess.run(["aws", "s3", *args, "--region", "eu-west-2", "--only-show-errors"], capture_output=True, text=True)


def fetch_one(m, key):
    dest = archive_path(m)
    if dest.exists() and dest.stat().st_size > 0:
        return dest, "have"
    s = m["source"]
    room(m.get("size_kb", 0) * 1024, f"fetch {m['id']}")
    if s3("cp", f"s3://{CACHE_BUCKET}/mods/{dest.name}", str(dest)).returncode == 0:
        return dest, "cache"  # the private cache holds every archive once fetched (evict deletes local copies)
    if "nexus" in s:
        link = json.load(urllib.request.urlopen(urllib.request.Request(
            f"{API}/games/{s['nexus']}/mods/{s['mod']}/files/{s['file']}/download_link.json",
            headers={"apikey": key, "User-Agent": "argonia-stack/0.2"}), timeout=60))[0]["URI"]
        download(urllib.parse.quote(link, safe=":/?&=%~+"), dest)
    elif "github" in s:
        download(f"https://github.com/{s['github']}/releases/download/{urllib.parse.quote(s['tag'], safe='')}/"
                 f"{urllib.parse.quote(s['asset'])}", dest)
    elif "built" in s:  # our own SKSE plugin: made by `skse_build.sh build` then `pack`, never downloaded
        raise OSError(f"{dest.name} is not built here or cached: run infra/gpu-box/skse_build.sh build, then pack")
    else:  # a manual download (ModDB): only the private cache holds it
        raise OSError(f"{dest.name} is not in s3://{CACHE_BUCKET}/mods/ (a manual download: upload it there)")
    return dest, "got"


def cached_sha(name):
    """The sha256 the private cache recorded for an archive (object metadata), or None if it is not cached."""
    r = subprocess.run(["aws", "s3api", "head-object", "--bucket", CACHE_BUCKET, "--key", f"mods/{name}", "--region",
                        "eu-west-2", "--query", "Metadata.sha256", "--output", "text"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() not in ("", "None") else None


def cache(path, h):
    """The archive into s3://<cache>/mods/ with its sha256, unless it is already there with that hash."""
    if cached_sha(path.name) != h:
        r = s3("cp", str(path), f"s3://{CACHE_BUCKET}/mods/{path.name}", "--metadata", f"sha256={h}")
        if r.returncode != 0:
            raise SystemExit(f"cache {path.name}: {r.stderr[-300:]}")


def cmd_evict(a):
    """Delete each local archive once the private cache holds it with the manifest's sha256 (stage refetches)."""
    freed = 0
    for m in manifest()["mods"]:
        p = archive_path(m)
        if p.exists():
            cache(p, m["sha256"])
            freed += p.stat().st_size
            p.unlink()
    print(f"evicted {freed >> 20} MB of archives; s3://{CACHE_BUCKET}/mods/ holds them")


def cmd_fetch(a):
    doc = manifest()
    MODS.mkdir(parents=True, exist_ok=True)
    key, bad, changed = secret("NEXUS_API_KEY"), [], False
    for m in doc["mods"]:
        if a.only and m["id"] not in a.only:
            continue
        try:
            path, how = fetch_one(m, key)
        except (urllib.error.URLError, OSError) as e:
            print(f"FAIL  {m['id']}: {e}")
            bad.append(m["id"])
            continue
        h = sha256(path)
        if m.get("sha256") in (None, "") or (a.record and m["sha256"] != h):
            m["sha256"], changed = h, True
            print(f"{how:5} {m['id']}: recorded {h[:12]}")
        elif m["sha256"] != h:
            print(f"BAD   {m['id']}: sha256 {h[:12]} != manifest {m['sha256'][:12]}")
            bad.append(m["id"])
        else:
            print(f"{how:5} {m['id']}: ok")
        if m["sha256"] == h:
            cache(path, h)
    if changed:
        save_manifest(doc)
    if bad:
        raise SystemExit(f"{len(bad)} failed: {', '.join(bad)}")


# ---- stage --------------------------------------------------------------------------------------------------------

def unpack(archive, dest):
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    head = open(archive, "rb").read(8)
    if head.startswith(b"Rar!"):  # RAR5: p7zip cannot decode it
        subprocess.run(["unrar", "x", "-o+", "-inul", str(archive), str(dest) + "/"], check=True, capture_output=True)
    elif archive.suffix == ".tar":
        subprocess.run(["tar", "-xf", str(archive), "-C", str(dest)], check=True)
    else:
        subprocess.run(["7z", "x", "-y", f"-o{dest}", str(archive)], check=True, capture_output=True)
    # Some zips store Windows paths ("Interface\\x.txt") as flat names; turn them into folders.
    for f in sorted(dest.rglob("*"), key=lambda x: -len(x.parts)):
        if "\\" in f.name:
            target = f.parent.joinpath(*[s for s in f.name.split("\\") if s])
            target.parent.mkdir(parents=True, exist_ok=True)
            if f.is_dir():
                shutil.copytree(f, target, dirs_exist_ok=True)
                shutil.rmtree(f)
            else:
                f.rename(target)


class Resume:
    """A row's stage progress on disk (decision 0037): steps done under one stage key, so a build VM killed
    mid-unpack (spot reclaim) resumes at the step it was on. A different key, or no file, is a fresh start."""

    def __init__(self, path, key):
        self.path, self.key, self.steps = pathlib.Path(path), key, []
        try:
            doc = json.loads(self.path.read_text())
            if doc["key"] == key:
                self.steps = list(doc["steps"])
        except (OSError, ValueError, KeyError):
            pass
        self.fresh = not self.steps

    def done(self, step):
        return step in self.steps

    def mark(self, step):
        self.steps.append(step)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"key": self.key, "steps": self.steps}))
        tmp.replace(self.path)  # atomic: a kill leaves the old or the new list, never half

    def clear(self):
        self.path.unlink(missing_ok=True)


def unrar_into(inner, data, names=None):
    """Lay a rar into Data; with `names`, only those members (an @listfile, one exact name a line)."""
    if names is None:
        subprocess.run(["unrar", "x", "-o+", "-inul", str(inner), str(data) + "/"], check=True)
        return
    lst = pathlib.Path(str(inner) + ".extract.lst")
    lst.write_text("\n".join(names) + "\n")
    subprocess.run(["unrar", "x", "-o+", "-inul", str(inner), "@" + str(lst), str(data) + "/"], check=True)
    lst.unlink()


def list_rar(inner):
    """Member names of a rar, as stored (case kept)."""
    out = subprocess.run(["unrar", "lb", str(inner)], check=True, capture_output=True, text=True).stdout
    return [n for n in out.splitlines() if n and not n.endswith("/")]


def keep_select(listings, m):
    """The members of the row's rars that its `keep` (and `drop`) leave in Data: {rar: [names]}. The extraction list is
    built from the keep list, so BM&V's 21 GB is never laid, only its few hundred files. A keep glob that matches no
    member is a red (a stale entry or a case/prefix slip), never skipped quietly."""
    globs, drops = m["keep"], m.get("drop", [])
    sel, hit = {}, set()
    for rar, names in listings.items():
        sel[rar] = []
        for n in names:
            r = n.lower().replace("\\", "/")
            if any(fnmatch.fnmatch(r, d.lower()) for d in drops):
                continue
            g = [x for x in globs if fnmatch.fnmatch(r, x)]
            if g or (r.count("/") == 0 and pathlib.Path(r).suffix in PLUGIN_EXT):
                sel[rar].append(n)
                hit.update(g)
    missing = [x for x in globs if x not in hit]
    if missing:
        raise SystemExit(f"{m['id']}: keep entries matching nothing in {', '.join(listings)}: {missing}")
    return sel


KEPT_HEADROOM = 1 << 30  # what a keep-listed row lays beyond its archive's own unpack (BM&V: measured 191 MB)


def stage_need(m, size):
    """Bytes a row's stage needs free: the archive unpacked plus the staged copy (x3). A nested row with a keep list
    lays only its keep list: its archive's members (x1) plus the kept files, never the full 21 GB."""
    if m.get("nested") and m.get("keep"):
        return size + KEPT_HEADROOM
    return size * 3


def stage_nested(m, key, archive, src, data, progress, unpack_fn=None, unrar_fn=unrar_into, list_fn=list_rar):
    """A row whose archive holds archives (BM&V: a 9 GB tar of Data1.rar, Data2.rar, 21 GB laid). Each step is marked
    on disk when done; a rerun after a kill skips the done steps, and a step cut half-way (no mark) is redone over its
    partial files (unrar -o+ overwrites). A changed stage key (or no mark) clears the partial copy first.
    A row with a `keep` list lays only the members its keep list names, plus the textures those meshes name (a second
    pass), instead of the whole 21 GB that prune would then delete."""
    unpack_fn = unpack_fn or unpack
    r = Resume(progress, key)
    if r.fresh:
        shutil.rmtree(data, ignore_errors=True)
        shutil.rmtree(src, ignore_errors=True)
    todo = [name for name in m["nested"] if not r.done(f"rar:{name}")]
    need = bool(todo) or bool(m.get("keep") and not r.done("textures"))  # the archive's rars are still read
    # the unpacked tar is removed once every inner rar is laid, before the checks that follow; a rerun after one of
    # those failed (2026-11-08: the completeness check) has nothing left to unpack, and one with a rar still to lay
    # unpacks again if the tar's copy is gone
    if need and (not r.done("unpack") or not src.exists()):
        unpack_fn(archive, src)
        r.mark("unpack")
        print(f"  {m['id']}: unpacked the archive", flush=True)
    data.mkdir(parents=True, exist_ok=True)
    inners = {}
    for name in (m["nested"] if need else []):
        inner = ci(data_root(src), name)
        if inner is None:
            raise SystemExit(f"{m['id']}: {name} not in the archive")
        inners[name] = inner
    sel = None
    if m.get("keep") and need:
        listings = {name: list_fn(inner) for name, inner in inners.items()}
        sel = keep_select(listings, m)
        print(f"  {m['id']}: extraction list {sum(len(v) for v in sel.values())} of "
              f"{sum(len(v) for v in listings.values())} members", flush=True)
    for name, inner in inners.items():
        if r.done(f"rar:{name}"):
            print(f"  {m['id']}: {name} already laid (resumed)", flush=True)
            continue
        if sel is None:
            unrar_fn(inner, data)
        elif sel[name]:
            unrar_fn(inner, data, sel[name])
        r.mark(f"rar:{name}")
        print(f"  {m['id']}: laid {name}", flush=True)
    if sel is not None and not r.done("textures"):
        have = {str(f.relative_to(data)).lower().replace("\\", "/") for f in data.rglob("*") if f.is_file()}
        wanted = {}
        for f in data.rglob("*.nif"):
            for t in nif_textures(f.read_bytes()):
                wanted[t] = None
        for name in inners:
            more = [n for n in listings[name] if n.lower().replace("\\", "/") in wanted and n.lower() not in have]
            if more:
                unrar_fn(inners[name], data, more)
        r.mark("textures")
        print(f"  {m['id']}: laid the meshes' textures", flush=True)
    return r


def ci(base, rel):
    """Resolve an archive-relative path case-insensitively (FOMODs are written on Windows)."""
    cur = base
    for part in re.split(r"[\\/]+", rel.strip("\\/")):
        if not part:
            continue
        hit = [c for c in cur.iterdir() if c.name.lower() == part.lower()] if cur.is_dir() else []
        if not hit:
            return None
        cur = hit[0]
    return cur


def copy_into(src, dst):
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def data_root(src):
    """Descend through single wrapper folders to the data root."""
    root = src
    while True:
        items = [f for f in root.iterdir() if not f.name.startswith(".")]
        dirs = [f for f in items if f.is_dir()]
        loose = [f for f in items if f.is_file() and f.suffix.lower() in DOC_EXT]  # an example config, a readme
        if len(dirs) == 1 and len(items) - len(loose) == 1 and dirs[0].name.lower() == "data":
            return dirs[0]  # SkyLink AI: Data/ beside claude_desktop_config_example.json
        if len(items) == 1 and dirs and dirs[0].name.lower() not in DATA_DIRS:
            root = dirs[0]
        else:
            return root


DOC_EXT = (".txt", ".md", ".pdf", ".jpg", ".png", ".url", ".json", ".docx")
SKIP_TOP = ("docs", "fomod", "meta.ini", "readme", "license", "licence", "copying", "changes", "exceptions", "credits",
            "changelog")


def place_plain(src, data):
    root = data_root(src)
    for f in root.iterdir():
        if not f.name.lower().startswith(SKIP_TOP) and not (f.is_file() and f.suffix.lower() in (".txt", ".md", ".pdf",
                                                                                                   ".jpg", ".png", ".url")):
            copy_into(f, data / f.name)


def fomod(src, data, choices):
    """A FOMOD installer: required files, then per group the options named in the row's "fomod" (group name ->
    option names), else the group's Required and Recommended options (the first option for a select-exactly-one
    group with none), condition flags and the conditional installs. Returns the options taken, for the record."""
    cfg = next((p for p in src.rglob("*") if p.name.lower() == "moduleconfig.xml"), None)
    base = cfg.parent.parent
    raw = cfg.read_bytes()
    text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig", errors="replace")
    root = ET.fromstring(re.sub(r"^<\?xml[^>]*\?>", "", text.strip()))
    files, flags, taken = [], {}, []

    def add(node):
        for el in node:
            if el.tag in ("file", "folder"):
                files.append((int(el.get("priority", 0)), el.tag, el.get("source", ""), el.get("destination")))

    def holds(dep):
        op = dep.get("operator", "And")
        res = []
        for d in dep:
            if d.tag == "flagDependency":
                res.append(flags.get(d.get("flag")) == d.get("value"))
            elif d.tag == "dependencies":
                res.append(holds(d))
            else:  # file or game dependencies: assume met (we install the files the profile names)
                res.append(True)
        return all(res) if op == "And" else any(res)

    req = root.find("requiredInstallFiles")
    if req is not None:
        add(req)
    for step in root.iter("installStep"):
        vis = step.find("visible")
        if vis is not None and not holds(vis):
            continue
        for group in step.iter("group"):
            gname, gtype = group.get("name", ""), group.get("type", "")
            plugins = list(group.iter("plugin"))

            def ptype(p):
                t = p.find("typeDescriptor/type")
                if t is not None:
                    return t.get("name")
                d = p.find("typeDescriptor/dependencyType/defaultType")
                return d.get("name") if d is not None else "Optional"
            if gname in choices:
                pick = [p for p in plugins if p.get("name") in choices[gname]]
                missing = set(choices[gname]) - {p.get("name") for p in pick}
                if missing:
                    raise SystemExit(f"FOMOD group {gname!r} has no option {sorted(missing)}")
            else:
                pick = [p for p in plugins if ptype(p) in ("Required", "Recommended")]
                if gtype in ("SelectExactlyOne", "SelectAtLeastOne") and not pick:
                    pick = [p for p in plugins if ptype(p) != "NotUsable"][:1]
                if gtype == "SelectExactlyOne":
                    pick = pick[:1]
            for p in pick:
                taken.append(f"{gname}: {p.get('name')}")
                fl = p.find("files")
                if fl is not None:
                    add(fl)
                for f in p.iter("flag"):
                    flags[f.get("name")] = (f.text or "").strip()
    cond = root.find("conditionalFileInstalls")
    if cond is not None:
        for pat in cond.iter("pattern"):
            dep = pat.find("dependencies")
            if dep is None or holds(dep):
                add(pat.find("files"))
    for _, kind, source, dest in sorted(files, key=lambda x: x[0]):
        s = ci(base, source)
        if s is None:
            raise SystemExit(f"FOMOD source missing: {source}")
        d = data / dest.replace("\\", "/").strip("/") if dest else (data if kind == "folder" else data / s.name)
        copy_into(s, d)
    return taken


def place(m, src, data, tools, root):
    how = m.get("install")
    if how == "root":  # SKSE: loader and DLLs beside the game, its scripts into Data
        (base,) = [d for d in src.iterdir() if d.is_dir()]
        for f in base.iterdir():
            if f.suffix.lower() in (".exe", ".dll"):
                copy_into(f, root / f.name)
        copy_into(base / "Data", data)
        return []
    if how == "tool":
        copy_into(src, tools / m["id"])
        return []
    if m.get("nested"):  # archives inside the archive (the vault's BM&V part: Data1.rar, Data2.rar), unpacked into Data
        base = data_root(src)
        for name in m["nested"]:
            inner = ci(base, name)
            if inner is None:
                raise SystemExit(f"{m['id']}: {name} not in the archive")
            subprocess.run(["unrar", "x", "-o+", "-inul", str(inner), str(data) + "/"], check=True)
            inner.unlink()
        return []
    if m.get("pick"):  # archive-relative paths, "x/*" copies x's contents; fixed choices from 0.0
        for part in m["pick"]:
            p = ci(src, part[:-2] if part.endswith("/*") else part)
            if p is None:
                raise SystemExit(f"{m['id']}: {part} not in the archive")
            if part.endswith("/*"):
                for f in p.iterdir():
                    copy_into(f, data / f.name)
            else:
                copy_into(p, data / (m.get("pick_to", {}).get(part) or p.name))
        return []
    if any(p.name.lower() == "moduleconfig.xml" for p in src.rglob("*")):
        return fomod(src, data, m.get("fomod", {}))
    place_plain(src, data)
    return []


def left_out_on_purpose(p, m):
    """An archive path (lower case, '/') that prune removes on purpose: tool leftovers, or the row's own `drop` list
    (BM&V's ELFX-edited meshes, 2026-11-08: the completeness check failed the stage on all 62)."""
    if p.endswith((".bat", ".pdb")) or (pathlib.PurePath(p).name.startswith("put your ") and p.endswith(".txt")):
        return True
    return any(fnmatch.fnmatch(p, d.lower()) or p.startswith(d.lower().rstrip("/") + "/") for d in m.get("drop", []))


def complete_nested(m, archive, data):
    """Every file of a nested row's inner archives is laid (owner, 2026-11-05: 100% of BM&V, nothing missing): list each
    inner rar's files with `unrar lt` and fail on any not in the staged copy, bar what prune removes on purpose."""
    with tempfile.TemporaryDirectory() as t:
        subprocess.run(["tar", "-xf", str(archive), "-C", t, "--wildcards", *[f"*/{n}" for n in m["nested"]]], check=True)
        want = set()
        for n in m["nested"]:
            inner = next(pathlib.Path(t).rglob(n))
            out = subprocess.run(["unrar", "lt", str(inner)], check=True, capture_output=True, text=True).stdout
            name = None
            for line in out.splitlines():
                line = line.strip()
                if line.startswith("Name: "):
                    name = line[6:]
                elif line.startswith("Type: ") and line[6:] == "File" and name:
                    want.add(name.replace("\\", "/").lower())
    have = {str(f.relative_to(data)).lower() for f in data.rglob("*") if f.is_file()}
    missing = sorted(p for p in want - have if not left_out_on_purpose(p, m))
    if missing:
        raise SystemExit(f"{m['id']}: {len(missing)} archive files not laid, e.g. {missing[:3]}")
    print(f"  {m['id']}: complete: {len(want)} archive files, all laid")


def assets_only(data):
    """An asset-only row (owner, 2026-11-08): its plugins are never active, and a BSA loads only beside an active
    plugin of its name, so each BSA is extracted loose (a loose file the mod already ships wins, as in game) and
    the BSAs and plugins leave the staged folder."""
    import sys
    sys.path.insert(0, str(REPO / "tools"))
    from navmesh import bsa
    n = 0
    for arc in sorted(data.glob("*.bsa")):
        a = bsa.Archive(bsa.local(arc))
        room(sum(v[1] for v in a.files.values()) * 2, f"extract {arc.name}")
        for key in a.files:
            dst = data / key
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(a.get(key))
                n += 1
        arc.unlink()
    for f in data.iterdir():
        if f.suffix.lower() in PLUGIN_EXT:
            f.unlink()
    print(f"  asset-only: {n} files extracted from BSAs; plugins and BSAs removed")


def prune(data, m):
    for f in list(data.rglob("*")):
        if f.is_file() and (f.name.lower().startswith("put your ") and f.suffix.lower() == ".txt"
                            or f.suffix.lower() in (".bat", ".pdb")):
            f.unlink()
    # Only a row that asks drops its non-ASCII folders (Rim Parry's sound backups did): a blanket rule deleted BM&V's
    # meshes/clutter/Oaristys/Forge/Linen° and its 42 meshes (2026-11-05).
    for d in sorted((x for x in data.rglob("*") if x.is_dir() and (x.name in ("BEIFEN",) or
                     (m.get("drop_nonascii") and not x.name.isascii()))), key=lambda x: -len(x.parts)):
        shutil.rmtree(d, ignore_errors=True)
    for pat in m.get("drop", []):
        gone = 0
        for f in list(data.rglob("*")):
            if f.exists() and fnmatch.fnmatch(str(f.relative_to(data)).lower(), pat.lower()):
                gone += sum(1 for x in f.rglob("*") if x.is_file()) if f.is_dir() else 1
                shutil.rmtree(f) if f.is_dir() else f.unlink()
        print(f"  {m['id']}: drop {pat}: {gone} files" + ("" if gone else " (matched nothing: a stale drop list?)"))
    if m.get("keep"):
        keep_subset(data, m["keep"])
    for d in sorted((x for x in data.rglob("*") if x.is_dir()), key=lambda x: -len(x.parts)):
        if not any(d.iterdir()):
            d.rmdir()
    too_long = [f for f in data.rglob("*") if f.is_file() and len(GAME_DATA) + len(str(f.relative_to(data))) > MAX_PATH]
    if too_long:
        raise SystemExit(f"paths too long for Skyrim in {m['id']}: {too_long[0].relative_to(data)}")


DDS = re.compile(rb"[\x20-\x7e]{3,200}?\.dds", re.I)


def nif_textures(raw):
    """Texture paths (lower case, under textures/) a nif's strings name."""
    out = set()
    for t in DDS.findall(raw):
        t = t.decode().lower().replace("\\", "/")
        t = t[t.find("textures/"):] if "textures/" in t else t.lstrip("/")  # a length byte may precede it
        out.add(t if t.startswith("textures/") else "textures/" + t)
    return out


def keep_subset(data, globs):
    """A row's `keep`: only the Data paths the world references (globs, lower case), the row's plugins, and every
    texture a kept mesh names (read from the nif's strings) stay; the rest of the row is removed (BM&V, 9.6 GB, of
    which the world references 24 meshes: dependency audit 2026-10-29)."""
    files = {str(f.relative_to(data)).lower().replace("\\", "/"): f for f in data.rglob("*") if f.is_file()}
    kept = {r for r in files if any(fnmatch.fnmatch(r, g) for g in globs)
            or (r.count("/") == 0 and pathlib.Path(r).suffix in PLUGIN_EXT)}
    for r in [r for r in kept if r.endswith(".nif")]:
        kept.update(t for t in nif_textures(files[r].read_bytes()) if t in files)
    for r, f in files.items():
        if r not in kept:
            f.unlink()
    print(f"  keep: {len(kept)} of {len(files)} files")


def set_ini(text, section, key, value):
    """Set key=value inside [section] (any section when None), adding it when absent; keeps the file's spacing."""
    lines, sec, done, insert_at = text.splitlines(), None, False, None
    for i, line in enumerate(lines):
        s = re.match(r"\s*\[([^\]]+)\]", line)
        if s:
            if sec is not None and section and sec.lower() == section.lower() and insert_at is None:
                insert_at = i
            sec = s.group(1)
            continue
        k = re.match(rf"(\s*{re.escape(key)}\s*=\s*)([^;#\r\n]*?)(\s*([;#].*)?)$", line)
        if k and (section is None or (sec or "").lower() == section.lower()):
            lines[i], done = f"{k.group(1)}{value}{k.group(3)}", True
            break
    if not done:
        if section and insert_at is None and not any(re.match(rf"\s*\[{re.escape(section)}\]", x, re.I) for x in lines):
            lines += [f"[{section}]", f"{key} = {value}"]
        else:
            lines.insert(insert_at if insert_at is not None else len(lines), f"{key} = {value}")
    return "\n".join(lines) + "\n"


def apply_ini(m, data):
    """The row's settings: {"file": glob under the mod, "section": name or null, "set": {key: value}}, the manifest's
    """
    for edit in m.get("ini", []):
        hits = [f for f in data.rglob("*") if f.is_file()
                and fnmatch.fnmatch(str(f.relative_to(data)).replace("\\", "/").lower(), edit["file"].lower())]
        if not hits:
            raise SystemExit(f"{m['id']}: no {edit['file']} to set")
        for f in hits:
            text = f.read_text(errors="ignore")
            for k, v in edit["set"].items():
                text = set_ini(text, edit.get("section"), k, v)
            f.write_text(text)
        print(f"  {m['id']}: set {', '.join(edit['set'])} in {edit['file']}")


def apply_files(m, data):
    """The row's own setting files: {"path": under the mod, "text": contents}, written beside the mod's files (1.12:
    Wind UI's settings.json and vanilla.txt; its licence allows installers to lay "your own setting files")."""
    for f in m.get("files", []):
        out = data / f["path"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(f["text"])
        print(f"  {m['id']}: wrote {f['path']}")


def game_data():
    """The player's own game Data on the build VM (the owner's licensed copy; plugin.sh reads the same)."""
    return pathlib.Path(os.environ.get("ARGONIA_GAME_ROOT", HOME / "games" / "skyrimse")) / "Data"


def apply_vanilla(m, data):
    """The row's `vanilla_files`: {path under the mod: [archive, path inside]}, each a file of the player's own game
    copied out of its archive (bsa.py) and laid there, e.g. Skyrim's own DodgeBack.hkx as the standing backstep
    (owner walk 4, 2026-11-08). Derived at stage time from the player's copy (decision 0003); never committed."""
    import bsa
    for rel, (archive, inner) in m.get("vanilla_files", {}).items():
        out = data / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(bsa.read_file(str(game_data() / archive), inner))
        print(f"  {m['id']}: {rel} <- {archive}:{inner} ({sha256(out)[:16]})")


def masters_of(plugin):
    """The MAST entries of a plugin's TES4 header."""
    with open(plugin, "rb") as f:
        head = f.read(24)
        if head[:4] != b"TES4":
            return []
        body = f.read(struct.unpack("<I", head[4:8])[0])
    out, i = [], 0
    while i + 6 <= len(body):
        typ, size = body[i:i + 4], struct.unpack("<H", body[i + 4:i + 6])[0]
        if typ == b"MAST":
            out.append(body[i + 6:i + 6 + size].rstrip(b"\0").decode("latin-1"))
        i += 6 + size
    return out


def vanilla_plugins():
    return [n for n in (HERE / "vanilla-data-files.txt").read_text().split() if n.endswith(PLUGIN_EXT)]


# manifest fields that describe a row without changing what is laid
DOC_FIELDS = {"licence", "permission_summary", "ai_clause", "permission_ask", "permission_evidence", "runtime",
              "conflicts", "linked_or_forked_by", "plugins"}


def stage_key(m) -> str:
    """A row's stage stamp: its manifest entry (not the permission or note fields): a row is re-staged (unpacked
    again) only when this changes."""
    laid = {k: v for k, v in m.items() if k not in DOC_FIELDS}  # a permission or note edit does not re-stage
    return hashlib.sha256(json.dumps(laid, sort_keys=True).encode()).hexdigest()


def staged_ok(m, key, keys, mods, tools) -> bool:
    """The row is staged under `key` and its files are there: the stage leaves it alone."""
    kf = keys / f"{m['id']}.json"
    laid_ok = (tools / m["id"]).exists() if m.get("install") == "tool" else ((mods / m["id"]).exists() or m.get("install"))
    try:
        return bool(laid_ok) and json.loads(kf.read_text())["key"] == key
    except (OSError, ValueError, KeyError):
        return False


def cmd_plan(a):
    """What `stage` would unpack (rows whose stage key changed) and the room it needs. Prints JSON."""
    rows = chosen(manifest(), a.dev)
    STACK, MO2 = stack_dirs(a)  # noqa: N806
    todo = [m for m in rows if not staged_ok(m, stage_key(m), STACK / "staged", MO2 / "mods", MO2 / "tools")]
    need = sum(stage_need(m, archive_path(m).stat().st_size) if archive_path(m).exists() else 0 for m in todo)
    print(json.dumps({"restage": [m["id"] for m in todo], "need_bytes": need}))
    return todo, need


STAGE_INPUTS = ("mods/dependencies.json", "infra/gpu-box")


def behind_main(repo=REPO):
    """Paths of STAGE_INPUTS that origin/main changed in commits this tree lacks. The real stack is shared by every
    lane: a stage from a tree behind main lays an older manifest over main's and pushes it to the machine."""
    g = ["git", "-C", str(repo)]
    subprocess.run(g + ["fetch", "-q", "origin", "main"], check=False, capture_output=True)
    out = subprocess.run(g + ["log", "--format=", "--name-only", "HEAD..origin/main", "--", *STAGE_INPUTS],
                         capture_output=True, text=True)
    return sorted({x for x in out.stdout.split() if x}) if out.returncode == 0 else []


def cmd_stage(a):
    rows = chosen(manifest(), a.dev)
    STACK, MO2 = stack_dirs(a)  # noqa: N806 (a scratch stage for a dry run, else the build VM's stack)
    if not getattr(a, "into", None):
        stale = behind_main()
        if stale:
            raise SystemExit(f"stage: this tree is behind origin/main on {', '.join(stale)}; merge main first (the "
                             "stack is shared: an older manifest would be laid over main's and pushed)")
    group = getattr(a, "group", None)
    if group:  # one group alone: a dry run's file lists, never the real stack (it would remove every other row)
        if not getattr(a, "into", None):
            raise SystemExit("--group stages into a scratch dir only (--into DIR)")
        rows = [m for m in rows if m["group"] == group]
    mods, tools, root, work = MO2 / "mods", MO2 / "tools", MO2 / "root", STACK / "_unpacked"
    keys = STACK / "staged"  # a row is re-staged only when its archive or its manifest entry changed
    for d in (mods, tools, root, keys):
        d.mkdir(parents=True, exist_ok=True)
    names, record, ids, pruned, restaged = [], {}, {m["id"] for m in rows}, set(), {"pandora-output"}
    prev = {}
    for profile in (NEWWORLD, PROFILE):
        if (STACK / installed_name(profile)).exists():
            prev.update(json.loads((STACK / installed_name(profile)).read_text())["files"])
    for d in list(mods.iterdir()):
        if d.name not in ids and d.name not in ("pandora-output", LODS):
            shutil.rmtree(d)
    for d in list(tools.iterdir()):  # a tool no row names any more
        if d.is_dir() and d.name not in ids:
            shutil.rmtree(d)
    for m in rows:
        data, key = mods / m["id"], stage_key(m)
        kf = keys / f"{m['id']}.json"
        if staged_ok(m, key, keys, mods, tools):
            taken = json.loads(kf.read_text())["fomod"]
            if json.loads(kf.read_text()).get("pruned"):
                pruned.add(m["id"])
        else:
            src = work / m["id"]
            if not archive_path(m).exists():
                fetch_one(m, secret("NEXUS_API_KEY"))
            prog = STACK / "progress" / f"{m['id']}.json"
            resume = Resume(prog, key) if m.get("nested") else None
            if resume is None or resume.fresh:  # a resumed row keeps the partial copy it is part-way through
                shutil.rmtree(data, ignore_errors=True)  # the old staged copy first: BM&V's is 21 GB on a 116 GB disk
                room(stage_need(m, archive_path(m).stat().st_size), f"unpack {m['id']}")  # unpacked plus staged copy
            if resume is not None:
                resume = stage_nested(m, key, archive_path(m), src, data, prog)
                taken = []
            else:
                unpack(archive_path(m), src)
                data.mkdir()
                if m.get("install") == "tool":  # a tool is never a mod: nothing of it reaches Data
                    shutil.rmtree(tools / m["id"], ignore_errors=True)
                taken = place(m, src, data, tools, root)
            shutil.rmtree(src, ignore_errors=True)
            if m.get("asset_only"):
                assets_only(data)
            prune(data, m)
            if m.get("nested") and not m.get("keep"):
                complete_nested(m, archive_path(m), data)
            apply_ini(m, data)
            apply_files(m, data)
            apply_vanilla(m, data)
            kf.write_text(json.dumps({"key": key, "fomod": taken}))
            if resume is not None:
                resume.clear()
            restaged.add(m["id"])
            print(f"staged {m['id']}" + (f" ({'; '.join(taken)})" if taken else ""))
        if m["id"] in pruned or (data.exists() and any(data.iterdir())):
            names.append(m["id"])
        record[m["id"]] = {"fomod": taken} if taken else {}
    shutil.rmtree(work, ignore_errors=True)
    # LODSettings for the worlds whose terrain LOD ships without one (lodsettings.py; the world map needs them),
    # derived from the staged mods; kept as made when a pruned row no longer holds its .btr files
    import lodsettings
    tmp = mods / f"{LODS}.new"
    shutil.rmtree(tmp, ignore_errors=True)
    if lodsettings.derive(mods, tmp):
        shutil.rmtree(mods / LODS, ignore_errors=True)
        tmp.rename(mods / LODS)
        restaged.add(LODS)
    shutil.rmtree(tmp, ignore_errors=True)
    if (mods / LODS).exists():
        names.append(LODS)
    names.append("pandora-output")  # filled when Pandora runs on the machine; highest priority
    (mods / "pandora-output").mkdir(exist_ok=True)
    all_names = names
    for profile in (PROFILE, NEWWORLD):
        prows = profile_rows(rows, profile)
        pids = {m["id"] for m in prows}
        names = [n for n in all_names if n in pids or n not in ids]  # derived folders (LODs, Pandora) in both
        prof = MO2 / "profiles" / profile
        shutil.rmtree(prof, ignore_errors=True)
        prof.mkdir(parents=True)
        (prof / "modlist.txt").write_text("".join(f"+{n}\r\n" for n in reversed(names)))  # MO2 order: highest first
        plugins, have, unmet = [], {p.lower() for p in vanilla_plugins()}, []
        order = {m["id"]: [x.lower() for x in m.get("plugins", [])] for m in prows}

        def plugin_key(n, f):
            """A row's own `plugins` list is its load order; else masters (.esm, .esl) before .esp, then by name
            (alphabetical alone put "Black Marsh North.esp" before its master "Black Marsh.esm", 2026-11-05)."""
            want = order.get(n, [])
            if f.name.lower() in want:
                return (0, want.index(f.name.lower()), "")
            return (1, 0 if f.suffix.lower() in (".esm", ".esl") else 1, f.name.lower())

        for n in names:
            for f in sorted((mods / n).iterdir(), key=lambda f: plugin_key(n, f)):
                if f.suffix.lower() in PLUGIN_EXT and f.name.lower() not in have:
                    missing = [x for x in masters_of(f) if x.lower() not in have]
                    if missing:
                        unmet.append(f"{n}: {f.name} needs masters not loaded before it: {missing}")
                    plugins.append(f.name)
                    have.add(f.name.lower())
        if unmet and not group:
            raise SystemExit("\n".join(unmet))
        print("\n".join(f"  (one group: {u})" for u in unmet))
        (prof / "plugins.txt").write_text("".join(f"*{p}\r\n" for p in plugins))
        (prof / "loadorder.txt").write_text("".join(f"{p}\r\n" for p in vanilla_plugins() + plugins))
        files = {}
        for n in names:  # later mods win
            hf = keys / f"{n}.files.json"  # the row's own file hashes, kept with its key: a skipped row is not re-hashed
            if n in restaged or not hf.exists():
                # a row restaged now is hashed from disk even if it was pruned before: the pruned record is its old
                # content (BM&V's trimmed keep list stood in for the whole mod, 2026-11-05)
                if n in pruned and n not in restaged:  # pushed, verified on the machine and cut to its plugins here
                    own = {k: v[1] for k, v in prev.items() if v[0] == n}
                else:
                    own = {str(f.relative_to(mods / n)).replace("/", "\\").lower(): sha256(f)
                           for f in sorted((mods / n).rglob("*")) if f.is_file()}
                hf.write_text(json.dumps(own, indent=0))
            files.update((k, [n, h]) for k, h in json.loads(hf.read_text()).items())
        for f in sorted(root.rglob("*")):
            if f.is_file():
                files["..\\" + f.name.lower()] = ["skse", sha256(f)]
        (STACK / installed_name(profile)).write_text(json.dumps({"rows": record, "plugins": plugins, "files": files}, indent=0))
        print(f"profile {profile}: {len(names) - 1} mods, {len(plugins)} plugins, {len(files)} files")
    return restaged - {"pandora-output"}


def stack_dirs(a):
    """The stage's home: --into DIR (a scratch dry run) or ~/.argonia/stack."""
    into = getattr(a, "into", None)
    return (pathlib.Path(into), pathlib.Path(into) / "MO2") if into else (STACK, MO2)


# ---- the machine --------------------------------------------------------------------------------------------------

def run(*args, check=True, capture=False):
    r = subprocess.run([RUN, *args], text=True, capture_output=capture, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise SystemExit(f"run.sh {args[0]} failed ({' '.join(args[1:])[:160]}): {(r.stderr or '')[-400:]} {(r.stdout or '')[-400:]}")
    return r.stdout if capture else ""


def stream(*args):
    """run.sh with its output printed line by line as it comes (a long machine job stays visible); returns it."""
    r = subprocess.Popen([RUN, *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         encoding="utf-8", errors="replace")
    lines = []
    for line in r.stdout:
        print(line, end="", flush=True)
        lines.append(line)
    r.wait()
    return "".join(lines)


PART = 1 << 30  # a mod's tar goes over in 1 GB parts, one on the build VM's disk at a time (BM&V is 21 GB)


def wide_names(src):
    """Files under `src` whose path is not plain ASCII, relative and '/'-separated. Windows tar converts each name
    through the ANSI code page (1252) and skips one it cannot convert with "empty or unreadable filename" (game-10's
    A restore: Rim Parry's and Modern Stagger Lock's `- 副本` copies and OAR's `RP弹反开启时间.xlsm`, 20 files
    missing from Data); these go in a zip instead, whose UTF-8 names .NET reads exactly."""
    return sorted(str(f.relative_to(src)).replace(os.sep, "/") for f in src.rglob("*")
                  if f.is_file() and not str(f.relative_to(src)).isascii())


def part_markers(done_dir, machine_sizes):
    """Parts a killed push already put on the machine: {part name: size} markers in `done_dir` that the machine still
    holds at that size stay; any other marker goes (the part is sent again)."""
    kept = {}
    for f in done_dir.glob("*") if done_dir.exists() else []:
        try:
            size = int(f.read_text())
        except ValueError:
            size = -1
        if machine_sizes.get(f.name) == size:
            kept[f.name] = size
        else:
            f.unlink()
    return kept


def machine_part_sizes(n):
    """{part name: bytes} of <n>.tar.NNN already in the machine's push dir (empty when none or the call fails)."""
    out = run("ps", rf"Get-ChildItem -LiteralPath C:\argonia\MO2\push -Filter '{n}.tar.*' -EA SilentlyContinue | "
                    r"% { $_.Name + ' ' + $_.Length }", check=False, capture=True) or ""
    sizes = {}
    for ln in out.splitlines():
        parts = ln.split()
        if len(parts) == 2 and parts[1].isdigit():
            sizes[parts[0]] = int(parts[1])
    return sizes


def send_tar(src, out, n, digest=""):
    """tar `src` as C:/argonia/MO2/push/<n>.tar.NNN parts, never the whole tar on the build VM's disk; the files
    with non-ASCII paths (wide_names) go as C:/argonia/MO2/push/<n>.wide.zip. Returns that zip's file count."""
    # three tries: one scp of a 1 GB part dropped with exit 255 while the machine was busy (2026-10-29)
    # resume (0037): a part put and size-checked on the machine leaves a marker under parts/<n>-<digest>/; a rerun after
    # a kill cuts the same parts again (the tar of an unchanged folder is the same bytes) and sends only the unmarked
    done_dir = out / "parts" / f"{n}-{digest[:16]}"
    for old in (out / "parts").glob(f"{n}-*") if (out / "parts").exists() else []:
        if old != done_dir:
            shutil.rmtree(old, ignore_errors=True)  # another content: its parts are not ours
    done_dir.mkdir(parents=True, exist_ok=True)
    have = machine_part_sizes(n)
    kept = part_markers(done_dir, have)
    stale = [k for k in have if k not in kept]  # a part cut mid-put, or another content's: the join would take it
    if stale:
        run("ps", "; ".join(rf"Remove-Item -LiteralPath 'C:\argonia\MO2\push\{k}' -EA SilentlyContinue" for k in stale))
    put = (f"B=$(basename \"$FILE\"); if [ ! -e \"{done_dir}/$B\" ]; then "
           f"for i in 1 2 3; do {RUN} put \"$FILE\" C:/argonia/MO2/push/ >/dev/null && break; [ $i = 3 ] && exit 1; "
           f"done && stat -c %s \"$FILE\" > \"{done_dir}/$B\"; fi && rm \"$FILE\"")
    wide = set(wide_names(src))
    names = sorted(str(f.relative_to(src)).replace(os.sep, "/") for f in src.rglob("*") if f.is_file())
    listing = "".join(f"./{x}\0" for x in names if x not in wide)
    # pax: names go as UTF-8 in pax headers; in GNU format Windows tar reads the raw bytes as cp437 and lays
    # `°` as `┬░` (2026-10-29: 64 files of BM&V, Rim Parry and Modern Stagger Lock)
    tar = subprocess.Popen(["tar", "--format=pax", "--null", "--no-recursion", "-cf", "-", "-C", str(src), "-T", "-"],
                           stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    split = subprocess.Popen(["split", "-b", str(PART), "-d", "-a", "3", f"--filter=cat > \"$FILE\" && {put}", "-",
                              str(out / f"{n}.tar.")], stdin=tar.stdout)
    tar.stdout.close()
    tar.stdin.write(listing.encode("utf-8", "surrogateescape"))
    tar.stdin.close()
    if tar.wait() or split.wait():
        raise SystemExit(f"tar of {src} failed")
    if wide:
        z = out / f"{n}.wide.zip"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_STORED) as zf:  # non-ASCII names carry the UTF-8 flag (bit 11)
            for x in sorted(wide):
                zf.write(src / x, x)
        run("put", str(z), f"C:/argonia/MO2/push/{n}.wide.zip")
        z.unlink()
    return len(wide)


def unpack_script(n):
    """PowerShell that lays the pushed <n>: the parts joined, tar unpacked (its exit code checked: a skipped entry
    is a failed push), then <n>.wide.zip unpacked by .NET, which honours the zip's UTF-8 names."""
    d, push = rf"C:\argonia\MO2\mods\{n}", r"C:\argonia\MO2\push"
    return (rf"Remove-Item -Recurse -Force -LiteralPath '{d}' -EA SilentlyContinue; "
            rf"New-Item -ItemType Directory -Force '{d}' | Out-Null; "
            + join_parts(n) +
            rf"tar -xf '{push}\{n}.tar' -C '{d}'; if ($LASTEXITCODE) {{ 'UNPACK FAILED: {n} (tar)'; exit 1 }}; "
            rf"Remove-Item '{push}\{n}.tar'; "
            rf"if (Test-Path -LiteralPath '{push}\{n}.wide.zip') {{ Add-Type -AssemblyName System.IO.Compression.FileSystem; "
            rf"[IO.Compression.ZipFile]::ExtractToDirectory('{push}\{n}.wide.zip', '{d}'); "
            rf"Remove-Item -LiteralPath '{push}\{n}.wide.zip' }}")


def join_parts(n):
    """PowerShell that joins <n>.tar.NNN (in name order) into <n>.tar and removes the parts."""
    p = rf"C:\argonia\MO2\push\{n}.tar"
    return (rf"$o = [IO.File]::Create('{p}'); Get-ChildItem -LiteralPath C:\argonia\MO2\push -Filter '{n}.tar.*' | "
            rf"? {{ $_.Name -ne '{n}.tar' }} | Sort-Object Name | % {{ $i = [IO.File]::OpenRead($_.FullName); $i.CopyTo($o); $i.Close(); "
            rf"Remove-Item -LiteralPath $_.FullName }}; $o.Close(); ")


def row_digest(keys, n):
    """A mod folder's push digest: every file the row itself laid (staged/<row>.files.json, written by stage), so a
    file another row overrides in a profile record still counts toward its own row (a newworld row's override at a
    play row's path must not hide an edit to the play row's copy)."""
    hf = keys / f"{n}.files.json"
    own = json.loads(hf.read_text()) if hf.exists() else {}
    return hashlib.sha256("".join(sorted(f"{k}{h}" for k, h in own.items())).encode()).hexdigest()


def cmd_push(a):
    """Tar each changed mod folder, copy it over and unpack it into C:\\argonia\\MO2\\mods\\<id>."""
    out = per_machine(STACK / "push")
    out.mkdir(exist_ok=True)
    sent = json.loads((out / "sent.json").read_text()) if (out / "sent.json").exists() else {}
    names = [d.name for d in sorted((MO2 / "mods").iterdir())]
    digest = {n: row_digest(STACK / "staged", n) for n in names}
    todo = [n for n in names if sent.get(n) != digest[n] and n != "pandora-output"]
    only = getattr(a, "only", None)
    if only:  # these rows alone: every other mod, and its record on the machine, stays as the machine has it
        todo = [n for n in todo if n in only]
    print(f"push: {len(todo)} mods to send: {', '.join(todo)}", flush=True)
    run("ps", r"New-Item -ItemType Directory -Force C:\argonia\MO2\mods, C:\argonia\MO2\push, C:\argonia\MO2\tools,"
              rf" C:\argonia\MO2\profiles\{PROFILE}, C:\argonia\MO2\profiles\{NEWWORLD}, C:\argonia\MO2\root | Out-Null")
    batch = [todo[i:i + 12] for i in range(0, len(todo), 12)]
    for group in batch:
        for n in group:
            print(f"sending {n}", flush=True)
            send_tar(MO2 / "mods" / n, out, n, digest[n])
        script = "; ".join(unpack_script(n) for n in group)
        out_ps = run("ps", script + "; 'UNPACKED'", check=False, capture=True)  # absent after any failure
        if "UNPACKED" not in out_ps.splitlines()[-1:]:
            raise SystemExit("push: unpack failed: " + out_ps.strip()[-600:])
        for n in group:
            sent[n] = digest[n]
            shutil.rmtree(out / "parts" / f"{n}-{digest[n][:16]}", ignore_errors=True)
        (out / "sent.json").write_text(json.dumps(sent))
        print("pushed", ", ".join(group))
    for d in () if only else ("tools", "root"):  # --only: the machine's tools and root stand
        subprocess.run(["tar", "-cf", str(out / f"{d}.tar"), "-C", str(MO2 / d), "."], check=True)
        run("put", str(out / f"{d}.tar"), f"C:/argonia/MO2/push/{d}.tar")
        run("ps", rf"Remove-Item -Recurse -Force C:\argonia\MO2\{d} -EA SilentlyContinue; New-Item -ItemType Directory"
                  rf" C:\argonia\MO2\{d} | Out-Null; tar -xf C:\argonia\MO2\push\{d}.tar -C C:\argonia\MO2\{d}")
    for profile in (PROFILE, NEWWORLD):
        if only and not (set(read_profile_mods(profile)) - set(read_profile_mods(PROFILE))) & set(only):
            continue  # --only: a profile none of the pushed rows belong to alone stays as on the machine
        run("put", str(MO2 / "profiles" / profile) + "/.", f"C:/argonia/MO2/profiles/{profile}/")
    stale = [] if only else [n for n in sent if n not in names]
    if stale:  # rows no longer in the profile (a set swapped out)
        run("ps", "; ".join(rf"Remove-Item -Recurse -Force -LiteralPath 'C:\argonia\MO2\mods\{n}' -EA SilentlyContinue"
                            for n in stale))
        for n in stale:
            sent.pop(n)
        (out / "sent.json").write_text(json.dumps(sent))
    for profile in (PROFILE, NEWWORLD):
        src = STACK / installed_name(profile)
        if only:  # the machine's record, with only the pushed rows' files taken from here (later rows win)
            with tempfile.TemporaryDirectory() as t:
                run("get", f"C:/argonia/MO2/{installed_name(profile)}", f"{t}/m.json")  # this profile's own record
                rec = json.loads(pathlib.Path(f"{t}/m.json").read_text(encoding="utf-8-sig"))
            local = json.loads(src.read_text())
            prof_mods = set(read_profile_mods(profile))
            if profile == PROFILE and not (prof_mods & set(only)):
                continue  # nothing of this profile was pushed: its record on the machine stands
            rec["files"].update((k, v) for k, v in local["files"].items() if v[0] in only)
            rec["plugins"] = local["plugins"]
            src = out / installed_name(profile)
            src.write_text(json.dumps(rec, indent=0))
        run("put", str(src), f"C:/argonia/MO2/{installed_name(profile)}")
    # a portable MO2 instance description, so houseCARL (which reads MO2 instances) sees this profile
    ini = out / "ModOrganizer.ini"
    ini.write_text("[General]\r\ngameName=Skyrim Special Edition\r\ngamePath=@ByteArray(C:\\\\Program Files (x86)"
                   "\\\\Steam\\\\steamapps\\\\common\\\\Skyrim Special Edition)\r\n"
                   f"selected_profile=@ByteArray({PROFILE})\r\n[Settings]\r\n")
    run("put", str(ini), "C:/argonia/MO2/ModOrganizer.ini")
    (out / "portable.txt").write_text("")
    run("put", str(out / "portable.txt"), "C:/argonia/MO2/portable.txt")
    for f in ("stack.ps1", "splash.ps1", "display.ps1", "sunshine-apps.json", "make-cards.ps1"):
        run("put", str(HERE / f), f"C:/argonia/infra/{f}")
    if todo:  # what changed is laid into Data at once when the profile is on
        run("ps", r"if (Test-Path C:\argonia\stack-state\mode-on) { & C:\argonia\infra\stack.ps1 on | Out-Null }")
    print(f"pushed {len(todo)} changed of {len(names)} mods")


def read_profile_mods(profile):
    return [x[1:].strip() for x in (MO2 / "profiles" / profile / "modlist.txt").read_text().splitlines() if x.startswith("+")]


def cmd_menu(a):
    """Launch through SKSE in the desktop session; main menu = SKSE's data-loaded message."""
    os.environ.setdefault("DESKTOP_WAIT", "600")
    keep = "$env:ARGONIA_KEEP = '1'; " if os.environ.get("ARGONIA_KEEP") else ""  # leave the game running after
    out = run("desktop", keep + r"& C:\argonia\infra\stack.ps1 menu", capture=True)
    print(out)
    if "MAIN-MENU OK" not in out:
        raise SystemExit("main menu not reached")
    loaded = [l for l in out.splitlines() if "loaded correctly" in l]
    # SKSE logs one "plugin <name>.dll (...)" line per DLL it finds; msdia140.dll (Crash Logger's helper) is no plugin
    failed = [l for l in out.splitlines() if re.match(r"plugin \S.*\.dll \(", l, re.I) and "loaded correctly" not in l
              and "no version data" not in l]
    print(f"{len(loaded)} DLLs loaded, {len(failed)} not")
    if failed:
        raise SystemExit("DLLs failed:\n" + "\n".join(failed))


def cmd_install(a):
    if not a.skip_fetch:
        cmd_fetch(argparse.Namespace(record=False, only=None))
    cmd_stage(a)
    # the game quits before the push: a running game holds its DLLs, so a mod the profile drops cannot be removed
    run("ps", r"Get-Process SkyrimSE,skse64_loader -EA SilentlyContinue | Stop-Process -Force; Start-Sleep 3")
    cmd_push(a)
    print(run("ps", r"& C:\argonia\infra\stack.ps1 off", capture=True))  # bare Data first
    # Pandora runs over SSH with --auto_run --auto_close: no desktop session needed (a freshly booted machine has no
    # signed-in user, and the desktop job never started, 2026-11-06)
    print(run("ps", r"& C:\argonia\infra\stack.ps1 pandora", capture=True))
    cmd_animdata(a)
    # No main-menu launch here: agents never run the game (owner, 2026-11-05); the laid files are checked by reading.


LODS = "argonia-lodsettings"  # derived in cmd_stage, never a row
ANIMDATA = r"meshes\animationdatasinglefile.txt"


def cmd_animdata(a):
    """Pandora's animation data lacks the root motion of TK Dodge's clips (animdata.py): patched on the build VM
    and written over pandora-output's file and Data's (a copy may break the hard link), both then hashed."""
    import animdata
    mod = rf"C:\argonia\MO2\mods\pandora-output\{ANIMDATA}"
    data = rf"C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data\{ANIMDATA}"
    with tempfile.TemporaryDirectory() as t:
        src, out = pathlib.Path(t) / "in.txt", pathlib.Path(t) / "out.txt"
        run("get", mod.replace("\\", "/"), str(src))
        text, added = animdata.patch(open(src, newline="").read())
        print("\n".join(added) or "animdata: nothing missing")
        if not added:
            return
        open(out, "w", newline="").write(text)
        run("put", str(out), r"C:/argonia/animdata.tmp")
        got = run("ps", rf"Copy-Item C:\argonia\animdata.tmp '{mod}' -Force; "
                        rf"Copy-Item C:\argonia\animdata.tmp '{data}' -Force; "
                        rf"(Get-FileHash '{mod}').Hash + ' ' + (Get-FileHash '{data}').Hash", capture=True).split()
    want = hashlib.sha256(text.encode()).hexdigest().upper()
    if got != [want, want]:
        raise SystemExit(f"animdata: the machine's files hash {got}, not {want}")
    print(f"animdata: {len(added)} clips added, pandora-output and Data match")


def cmd_verify(a):
    doc, bad = manifest(), []
    for m in doc["mods"]:
        p = archive_path(m)
        if not p.exists():
            if cached_sha(p.name) != m.get("sha256"):
                bad.append(f"{m['id']}: archive neither here nor in the cache with the manifest's sha256")
        elif m.get("sha256") != sha256(p):
            bad.append(f"{m['id']}: archive sha256 differs from the manifest")
    print(f"archives: {len(doc['mods']) - len(bad)} of {len(doc['mods'])} match")
    run("put", str(HERE / "stack.ps1"), "C:/argonia/infra/stack.ps1")
    out = stream("ps", r"& C:\argonia\infra\stack.ps1 verify" + (" -Full" if getattr(a, "full", False) else ""))
    if "VERIFY OK" not in out:
        bad.append("installed files differ (above)")
    if bad:
        raise SystemExit("\n".join(bad))


def cmd_prune(a):
    """After the machine's verify passes: each staged mod cut to its plugins (the machine holds the mod,
    installed.json its hashes)."""
    out = run("ps", r"& C:\argonia\infra\stack.ps1 on | Out-Null; & C:\argonia\infra\stack.ps1 verify", capture=True)
    print(out.strip()[-600:])
    if "VERIFY OK" not in out:
        raise SystemExit("the machine does not match installed.json: nothing pruned")
    freed = 0
    for mod in sorted((MO2 / "mods").iterdir()):
        for f in sorted(mod.rglob("*"), key=lambda x: -len(x.parts)):
            if f.is_file() and not (f.parent == mod and f.suffix.lower() in PLUGIN_EXT):
                freed += f.stat().st_size
                f.unlink()
            elif f.is_dir() and not any(f.iterdir()):
                f.rmdir()
        kf = STACK / "staged" / f"{mod.name}.json"
        if kf.exists():
            kf.write_text(json.dumps({**json.loads(kf.read_text()), "pruned": True}))
    print(f"pruned {freed >> 20} MB of staged files")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--machine", help="game machine (default $ARGONIA_PLAY, else argonia-play)")
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--record", action="store_true")
    f.add_argument("--only", nargs="*")
    for name in ("stage", "install", "plan"):
        s = sub.add_parser(name)
        s.add_argument("--dev", action="store_true", help="lay the dev rows too (houseCARL)")
        s.set_defaults(into=None, group=None)
        if name == "install":
            s.add_argument("--skip-fetch", action="store_true")
        elif name == "stage":
            s.add_argument("--into", help="stage into this dir instead of ~/.argonia/stack (a dry run)")
            s.add_argument("--group", help="with --into: only this group's rows")
    sub.add_parser("push").add_argument("--only", nargs="*", help="send these mods alone (the rest stay as on the machine)")
    for name in ("menu", "prune", "evict", "animdata"):
        sub.add_parser(name)
    sub.add_parser("verify").add_argument("--full", action="store_true", help="rehash every file (no cache)")
    a = p.parse_args()
    if a.machine:
        os.environ["ARGONIA_PLAY"] = a.machine  # run.sh reads it
    {"fetch": cmd_fetch, "stage": cmd_stage, "plan": cmd_plan, "push": cmd_push, "install": cmd_install, "menu": cmd_menu,
     "verify": cmd_verify, "prune": cmd_prune, "evict": cmd_evict, "animdata": cmd_animdata}[a.cmd](a)


if __name__ == "__main__":
    main()
