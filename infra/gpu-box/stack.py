#!/usr/bin/env python3
"""The Argonia profile: every row of data/dependencies.json fetched, verified, staged and laid over a clean Data on
the game machine, with exact undo (chunk 0.2 §b; grew from 0.0's combat_test_stage.py).

  stack.py fetch [--record] [--only ID ...]   download each row to ~/.argonia/mods (Nexus API, GitHub, the private
                                              cache in S3, the old vault); check sha256; --record writes new hashes
  stack.py stage [--set G=S] [--dev] [--through CHUNK]  unpack and place each row into ~/.argonia/stack/MO2/mods/<id>/, apply
                                              the recorded FOMOD choices and ini settings, write the profile
                                              (modlist, plugins.txt, loadorder.txt) and installed.json (every file's hash)
  stack.py push                               send changed mod folders and the profile to C:\\argonia\\MO2 on the machine
  stack.py install [--set ...] [--dev]        fetch, stage, push, then on the machine: stack.ps1 on (bare Data first),
                                              Pandora, the animation-data patch, and the main-menu check
  stack.py animdata                           after Pandora: the root motion its animation data lacks (animdata.py), in
                                              pandora-output and Data alike
  stack.py menu                               launch through SKSE, wait for the main menu, keep a still, list each DLL's load
  stack.py verify [--full]                    archives against the manifest; every laid file in Data against installed.json
                                              (hashes cached by size and mtime on the machine; --full rehashes all)
  stack.py masters                            plugins (ESM/ESP/ESL) and mesh path lists to $ARGONIA_GAME_ROOT/Data (0.4)
  stack.py combat A|B|B2 [--dry DIR]          the combat group's set (souls-0.0, dsc-b, dsc-b2) installed, then Pandora's
                                              DSC check; --dry stages only the combat group of each named set into DIR
                                              (build VM only), checks the switch is idempotent and exactly undone, and
                                              writes each set's file list
  stack.py pandora-check                      on the machine: Pandora's log and output hold DSC's FNIS animations

Machine: `stack.py --machine argonia-play-2 <cmd>` (or ARGONIA_PLAY=argonia-play-2) drives that game machine; the
default is argonia-play. Each machine keeps its own push record and menu still.

Sets: a group may hold alternative sets (row "set"); the profile takes one per group (default: the manifest's first),
so a second combat stack is a set of rows and `--set combat=<name>` swaps it; `stack.ps1 on` always starts from bare
Data, which is the exact undo. Nothing staged here is committed (decision 0003).
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
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
MANIFEST = REPO / "data" / "dependencies.json"
HOME = pathlib.Path.home()
MODS = HOME / ".argonia" / "mods"
STACK = HOME / ".argonia" / "stack"
MO2 = STACK / "MO2"
PROFILE = "Argonia"
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


THEME = "argonia-theme"  # 1.2 §a's derived UI theme overlay (tools/ui_theme)
MAP = "argonia-map"  # 1.2 §e's derived world map overlay over FWMF (tools/chart/fwmf.py, installer/steps/world-map.md)
VIEWS = "argonia-views"  # 1.2 §0's view bundle (tools/ui_harness/build.py: out/ui/views) under PrismaUI/views/argonia
LOD = "Argonia LOD (generated)"  # 2.W4 §c: filled on the machine by lod.ps1 (decision 0014 §4), never staged or pushed
CURRENT_PART = "0"  # stack.py --through's default: the rows of every chunk of the part being built


def started(chunk, through):
    """Has `chunk` (a row's `from`, e.g. "2.W5" or "2.7") started by `through` (a part "1" or a chunk "2.7")? A
    chunk of an earlier part has; within the part, a whole part takes all, else the same track (main or W) up to
    `through`'s number (0027: the world track runs beside the main one)."""
    def key(c):
        part, _, rest = c.partition(".")
        track = "W" if rest.startswith("W") else ""
        return int(part), track, float(rest.lstrip("W") or "inf")
    (p, t, n), (tp, tt, tn) = key(chunk), key(through)
    return p < tp or (p == tp and (tn == float("inf") or (t == tt and n <= tn)))


def picks(doc, sets):
    """The set each group lays: the manifest's first, unless --set names another. An unknown name is refused (it
    would silently lay none of the group's set rows)."""
    known = doc.get("sets", {})
    for g, s in sets.items():
        if s not in known.get(g, []):
            raise SystemExit(f"--set {g}={s}: the manifest's sets for {g!r} are {known.get(g)}")
    return {**{g: names[0] for g, names in known.items()}, **sets}


def chosen(doc, sets, dev, through=CURRENT_PART, need=()):
    """The rows the profile lays, in load order: play rows (dev rows with --dev), one set per group, and only the
    rows whose `from` chunk has started by `through` (deferred rows arrive with their first-use chunk), or whose
    plugin is in `need` (a master of our built plugins: Argonia.esm cannot load without it)."""
    pick = picks(doc, sets)
    out = []
    for m in doc["mods"]:
        if m["profile"] == "pipeline" or (m["profile"] == "dev" and not dev) or m.get("dropped"):
            continue
        if m.get("from") and not started(m["from"], through) and not set(m.get("plugins") or []) & set(need):
            continue
        sets = m.get("set")  # one name or a list: a row shared by several sets stays one row
        if sets and pick.get(m["group"]) not in ([sets] if isinstance(sets, str) else sets):
            continue
        out.append(m)
    return out


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
    else:  # a manual download (ModDB): the old vault (R2)
        sys.path.insert(0, str(REPO / "tools"))
        import fetch_vault as fv  # noqa: E402 (needs boto3: the toolchain venv)
        body = fv.client(fv.secrets()).get_object(Bucket=fv.BUCKET, Key=f"{fv.PREFIX}{s['vault']}.tar")["Body"]
        tmp = dest.with_name(dest.name + ".part")
        with open(tmp, "wb") as f:
            while c := body.read(8 << 20):
                f.write(c)
        tmp.rename(dest)
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


def prune(data, m):
    for f in list(data.rglob("*")):
        if f.is_file() and (f.name.lower().startswith("put your ") and f.suffix.lower() == ".txt"
                            or f.suffix.lower() in (".bat", ".pdb")):
            f.unlink()
    for d in sorted((x for x in data.rglob("*") if x.is_dir() and (x.name in ("BEIFEN",) or not x.name.isascii())),
                    key=lambda x: -len(x.parts)):
        shutil.rmtree(d, ignore_errors=True)  # Rim Parry's unused sound backups
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


def keep_subset(data, globs):
    """A row's `keep`: only the Data paths the world references (globs, lower case), the row's plugins, and every
    texture a kept mesh names (read from the nif's strings) stay; the rest of the row is removed (BM&V, 9.6 GB, of
    which the world references 24 meshes: dependency audit 2026-10-29)."""
    files = {str(f.relative_to(data)).lower().replace("\\", "/"): f for f in data.rglob("*") if f.is_file()}
    kept = {r for r in files if any(fnmatch.fnmatch(r, g) for g in globs)
            or (r.count("/") == 0 and pathlib.Path(r).suffix in PLUGIN_EXT)}
    for r in [r for r in kept if r.endswith(".nif")]:
        for t in DDS.findall(files[r].read_bytes()):
            t = t.decode().lower().replace("\\", "/")
            t = t[t.find("textures/"):] if "textures/" in t else t.lstrip("/")  # a length byte may precede it
            t = t if t.startswith("textures/") else "textures/" + t
            if t in files:
                kept.add(t)
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


_COMBAT = None


def combat_settings(mod_id):
    """The world database's combat settings for one mod (`combat_mod_setting`, the 1.6 wiring: decision 0030 makes
    the db the home of every tuned value; bindings and install toggles stay in the manifest's `ini`), grouped as the
    manifest's ini edits are."""
    global _COMBAT
    if _COMBAT is None:
        sys.path.insert(0, str(REPO))
        from tools.argonia_world import db
        _COMBAT = {}
        for r in db.open().rows("combat_mod_setting"):
            _COMBAT.setdefault(r.mod, {}).setdefault((r.file, r.section), {})[r.key] = r.value
    return [{"file": f, "section": sec, "set": kv} for (f, sec), kv in sorted(_COMBAT.get(mod_id, {}).items(),
                                                                                key=lambda x: (x[0][0], x[0][1] or ""))]


def apply_ini(m, data):
    """The row's settings: {"file": glob under the mod, "section": name or null, "set": {key: value}}, the manifest's
    then the world database's combat settings for the row."""
    for edit in m.get("ini", []) + combat_settings(m["id"]):
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


def plugin_values(m, data, pick):
    """The row's `plugin_values` for the chosen set (decision 0014: a mod's setting made at install, never shipped):
    a GLOB's value and a quest script's int property, written into the staged plugin. For a mod with no ini whose
    settings are records (Dark Souls Combat's crits global and roll key)."""
    for e in m.get("plugin_values", []):
        if e["set"] != pick.get(m["group"]):
            continue
        f = ci(data, e["plugin"])
        if f is None:
            raise SystemExit(f"{m['id']}: no {e['plugin']} to set")
        q = e.get("quest_script_int") or {}
        f.write_bytes(edit_plugin(f.read_bytes(), e.get("glob", {}), q.get("quest"), q.get("script"),
                                  q.get("values", {})))
        print(f"  {m['id']}: set {', '.join([*e.get('glob', {}), *q.get('values', {})])} in {e['plugin']} ({e['set']})")


def _wstr(b, i):
    n = struct.unpack_from("<H", b, i)[0]
    return b[i + 2:i + 2 + n].decode("latin-1"), i + 2 + n


def _skip_value(b, i, typ, fmt):
    one = {1: 8, 3: 4, 4: 4, 5: 1}
    if typ in one:
        return i + one[typ]
    if typ == 2:
        return _wstr(b, i)[1]
    if typ in (11, 12, 13, 14, 15):
        n, i = struct.unpack_from("<I", b, i)[0], i + 4
        for _ in range(n):
            i = _skip_value(b, i, typ - 10, fmt)
        return i
    raise SystemExit(f"VMAD property type {typ} not handled")


def set_script_ints(vmad, script, values):
    """A VMAD with `script`'s int properties set to `values` (added when the CK left the default), the rest kept."""
    version, fmt, count = struct.unpack_from("<hhH", vmad, 0)
    out, i, found = bytearray(vmad[:6]), 6, False
    for _ in range(count):
        start = i
        name, i = _wstr(vmad, i)
        status, nprops = vmad[i], struct.unpack_from("<H", vmad, i + 1)[0]
        i += 3
        props = []
        for _ in range(nprops):
            p0 = i
            pname, i = _wstr(vmad, i)
            typ = vmad[i]
            i = _skip_value(vmad, i + (2 if version >= 4 else 1), typ, fmt)
            props.append((pname, vmad[p0:i]))
        if name.lower() != script.lower():
            out += vmad[start:i]
            continue
        found, left = True, dict(values)
        kept = []
        for pname, raw in props:
            if pname in left:
                raw = struct.pack("<H", len(pname)) + pname.encode() + bytes([3, 1]) + struct.pack("<i", left.pop(pname))
            kept.append(raw)
        kept += [struct.pack("<H", len(k)) + k.encode() + bytes([3, 1]) + struct.pack("<i", v) for k, v in left.items()]
        out += struct.pack("<H", len(name)) + name.encode() + bytes([status]) + struct.pack("<H", len(kept)) + b"".join(kept)
    if not found:
        raise SystemExit(f"no script {script} in the VMAD")
    return bytes(out + vmad[i:])  # the quest's fragments and aliases, as they were


def edit_plugin(buf, globs, quest=None, script=None, values=None):
    """The plugin with each named GLOB's FLTV set and `quest`'s `script` ints set; GRUP and record sizes follow."""
    left_g, left_q = {k.lower(): v for k, v in globs.items()}, bool(quest)

    def subs(body):
        i = 0
        while i < len(body):
            t, n = body[i:i + 4], struct.unpack_from("<H", body, i + 4)[0]
            yield t, body[i + 6:i + 6 + n]
            i += 6 + n

    def record(head, body):
        nonlocal left_q
        typ, flags = head[:4], struct.unpack_from("<I", head, 8)[0]
        if typ not in (b"GLOB", b"QUST"):
            return head + body
        if flags & 0x40000:
            return head + body  # compressed: neither record kind DSC needs is
        parts = list(subs(body))
        edid = next((v for t, v in parts if t == b"EDID"), b"").rstrip(b"\0").decode("latin-1").lower()
        if typ == b"GLOB" and edid in left_g:
            parts = [(t, struct.pack("<f", float(left_g.pop(edid))) if t == b"FLTV" else v) for t, v in parts]
        elif typ == b"QUST" and quest and edid == quest.lower():
            parts = [(t, set_script_ints(v, script, values) if t == b"VMAD" else v) for t, v in parts]
            left_q = False
        else:
            return head + body
        body = b"".join(t + struct.pack("<H", len(v)) + v for t, v in parts)
        return head[:4] + struct.pack("<I", len(body)) + head[8:] + body

    def walk(b, i, end):
        out = bytearray()
        while i < end:
            typ, size = b[i:i + 4], struct.unpack_from("<I", b, i + 4)[0]
            if typ == b"GRUP":
                inner = walk(b, i + 24, i + size)
                out += b[i:i + 4] + struct.pack("<I", 24 + len(inner)) + b[i + 8:i + 24] + inner
                i += size
            else:
                out += record(b[i:i + 24], b[i + 24:i + 24 + size])
                i += 24 + size
        return bytes(out)

    out = walk(buf, 0, len(buf))
    if left_g or left_q:
        raise SystemExit(f"not in the plugin: {sorted(left_g) + ([quest] if left_q else [])}")
    return out


def our_masters():
    """The masters of our built plugins in out/ (make plugin), which make deploy lays."""
    need = set()
    for f in ("Argonia.esm", "ArgoniaWorld.esm"):
        if (REPO / "out" / f).exists():
            need |= set(masters_of(REPO / "out" / f))
    return need


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


def cmd_stage(a):
    doc = manifest()
    sets = dict(s.split("=", 1) for s in a.set)
    rows, pick = chosen(doc, sets, a.dev, a.through, need=our_masters()), picks(doc, sets)
    STACK, MO2 = stack_dirs(a)  # noqa: N806 (a scratch stage for a dry run, else the build VM's stack)
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
    prev = json.loads((STACK / "installed.json").read_text())["files"] if (STACK / "installed.json").exists() else {}
    for d in list(mods.iterdir()):
        if d.name not in ids and d.name not in ("pandora-output", THEME, MAP, VIEWS, LOD):
            shutil.rmtree(d)
    for d in list(tools.iterdir()):  # a tool of another set too (game-12: B2's Nemesis stayed, and A's Pandora ran it)
        if d.is_dir() and d.name not in ids:
            shutil.rmtree(d)
    for m in rows:
        laid = {k: v for k, v in m.items() if k not in DOC_FIELDS}  # a permission or note edit does not re-stage
        if combat_settings(m["id"]):  # a changed db setting re-stages its row (and only rows that have some)
            laid["combat_settings"] = combat_settings(m["id"])
        if m.get("plugin_values"):  # a row shared by sets whose values differ re-stages when the set changes
            laid["chosen_set"] = pick.get(m["group"])
        data, key = mods / m["id"], hashlib.sha256(json.dumps(laid, sort_keys=True).encode()).hexdigest()
        kf = keys / f"{m['id']}.json"
        laid_ok = (tools / m["id"]).exists() if m.get("install") == "tool" else (data.exists() or m.get("install"))
        if kf.exists() and json.loads(kf.read_text())["key"] == key and laid_ok:
            taken = json.loads(kf.read_text())["fomod"]
            if json.loads(kf.read_text()).get("pruned"):
                pruned.add(m["id"])
        else:
            src = work / m["id"]
            if not archive_path(m).exists():
                fetch_one(m, secret("NEXUS_API_KEY"))
            shutil.rmtree(data, ignore_errors=True)  # the old staged copy first: BM&V's is 21 GB on a 116 GB disk
            room(archive_path(m).stat().st_size * 3, f"unpack {m['id']}")  # unpacked plus staged copy
            unpack(archive_path(m), src)
            data.mkdir()
            if m.get("install") == "tool":  # a tool is never a mod: nothing of it reaches Data
                shutil.rmtree(tools / m["id"], ignore_errors=True)
            taken = place(m, src, data, tools, root)
            shutil.rmtree(src)
            prune(data, m)
            apply_ini(m, data)
            plugin_values(m, data, pick)
            kf.write_text(json.dumps({"key": key, "fomod": taken}))
            restaged.add(m["id"])
            print(f"staged {m['id']}" + (f" ({'; '.join(taken)})" if taken else ""))
        if m["id"] in pruned or (data.exists() and any(data.iterdir())):
            names.append(m["id"])
        record[m["id"]] = {"fomod": taken} if taken else {}
    shutil.rmtree(work, ignore_errors=True)
    theme = REPO / "out" / "ui_theme" / THEME  # derived on the build VM (installer/steps/ui-theme.md), never committed
    if theme.exists():  # above dear-diary, wood-and-paper and oblivion-loading-menu, so its fontconfig.txt wins
        shutil.rmtree(mods / THEME, ignore_errors=True)
        shutil.copytree(theme, mods / THEME)
        names.append(THEME)
        restaged.add(THEME)
        print(f"staged {THEME} from {theme}")
    names.append(LOD)  # filled by lod.ps1 on the machine; it overrides nothing of the mods
    (mods / LOD).mkdir(exist_ok=True)
    chart = REPO / "out" / "argonia_map" / MAP  # derived on the build VM (installer/steps/world-map.md), never committed
    if chart.exists():  # above the LOD and flat-world-map: its level-32 block 0,0 is the map's paper
        shutil.rmtree(mods / MAP, ignore_errors=True)
        shutil.copytree(chart, mods / MAP)
        names.append(MAP)
        restaged.add(MAP)
        print(f"staged {MAP} from {chart}")
    views = REPO / "out" / "ui" / "views"  # made on the build VM by tools/ui_harness/build.py (the installer's step)
    if (views / "dialogue" / "index.html").exists():  # PrismaUI loads file:///views/<path> from Data/PrismaUI/views
        shutil.rmtree(mods / VIEWS, ignore_errors=True)
        shutil.copytree(views, mods / VIEWS / "PrismaUI" / "views" / "argonia")
        names.append(VIEWS)
        restaged.add(VIEWS)
        print(f"staged {VIEWS} from {views}")
    names.append("pandora-output")  # filled when Pandora runs on the machine; highest priority
    (mods / "pandora-output").mkdir(exist_ok=True)
    prof = MO2 / "profiles" / PROFILE
    shutil.rmtree(prof, ignore_errors=True)
    prof.mkdir(parents=True)
    (prof / "modlist.txt").write_text("".join(f"+{n}\r\n" for n in reversed(names)))  # MO2 order: highest first
    plugins, have, unmet = [], {p.lower() for p in vanilla_plugins()}, []
    for n in names:
        for f in sorted((mods / n).iterdir()):
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
            if n in pruned:  # pushed, verified on the machine and cut to its plugins here: its record stands
                own = {k: v[1] for k, v in prev.items() if v[0] == n}
            else:
                own = {str(f.relative_to(mods / n)).replace("/", "\\").lower(): sha256(f)
                       for f in sorted((mods / n).rglob("*")) if f.is_file()}
            hf.write_text(json.dumps(own, indent=0))
        files.update((k, [n, h]) for k, h in json.loads(hf.read_text()).items())
    for f in sorted(root.rglob("*")):
        if f.is_file():
            files["..\\" + f.name.lower()] = ["skse", sha256(f)]
    (STACK / "installed.json").write_text(json.dumps({"rows": record, "plugins": plugins, "files": files}, indent=0))
    print(f"profile {PROFILE}: {len(names) - 1} mods, {len(plugins)} plugins, {len(files)} files")
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


def send_tar(src, out, n):
    """tar `src` as C:/argonia/MO2/push/<n>.tar.NNN parts, never the whole tar on the build VM's disk; the files
    with non-ASCII paths (wide_names) go as C:/argonia/MO2/push/<n>.wide.zip. Returns that zip's file count."""
    # three tries: one scp of a 1 GB part dropped with exit 255 while the machine was busy (2026-10-29)
    put = (f"for i in 1 2 3; do {RUN} put \"$FILE\" C:/argonia/MO2/push/ >/dev/null && break; [ $i = 3 ] && exit 1; "
           f"done && rm \"$FILE\"")
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


def cmd_push(a):
    """Tar each changed mod folder, copy it over and unpack it into C:\\argonia\\MO2\\mods\\<id>."""
    out = per_machine(STACK / "push")
    out.mkdir(exist_ok=True)
    sent = json.loads((out / "sent.json").read_text()) if (out / "sent.json").exists() else {}
    names = [d.name for d in sorted((MO2 / "mods").iterdir())]
    digest = {}
    inst = json.loads((STACK / "installed.json").read_text())["files"]
    for n in names:
        digest[n] = hashlib.sha256("".join(sorted(f"{k}{v[1]}" for k, v in inst.items() if v[0] == n)).encode()).hexdigest()
    todo = [n for n in names if sent.get(n) != digest[n] and n not in ("pandora-output", LOD)]
    run("ps", r"New-Item -ItemType Directory -Force C:\argonia\MO2\mods, C:\argonia\MO2\push, C:\argonia\MO2\tools,"
              rf" C:\argonia\MO2\profiles\{PROFILE}, C:\argonia\MO2\root | Out-Null")
    batch = [todo[i:i + 12] for i in range(0, len(todo), 12)]
    for group in batch:
        for n in group:
            send_tar(MO2 / "mods" / n, out, n)
        script = "; ".join(unpack_script(n) for n in group)
        out_ps = run("ps", script + "; 'UNPACKED'", check=False, capture=True)  # absent after any failure
        if "UNPACKED" not in out_ps.splitlines()[-1:]:
            raise SystemExit("push: unpack failed: " + out_ps.strip()[-600:])
        for n in group:
            sent[n] = digest[n]
        (out / "sent.json").write_text(json.dumps(sent))
        print("pushed", ", ".join(group))
    for d in ("tools", "root"):
        subprocess.run(["tar", "-cf", str(out / f"{d}.tar"), "-C", str(MO2 / d), "."], check=True)
        run("put", str(out / f"{d}.tar"), f"C:/argonia/MO2/push/{d}.tar")
        run("ps", rf"Remove-Item -Recurse -Force C:\argonia\MO2\{d} -EA SilentlyContinue; New-Item -ItemType Directory"
                  rf" C:\argonia\MO2\{d} | Out-Null; tar -xf C:\argonia\MO2\push\{d}.tar -C C:\argonia\MO2\{d}")
    run("put", str(MO2 / "profiles" / PROFILE) + "/.", f"C:/argonia/MO2/profiles/{PROFILE}/")
    stale = [n for n in sent if n not in names]
    if stale:  # rows no longer in the profile (a set swapped out)
        run("ps", "; ".join(rf"Remove-Item -Recurse -Force -LiteralPath 'C:\argonia\MO2\mods\{n}' -EA SilentlyContinue"
                            for n in stale))
        for n in stale:
            sent.pop(n)
        (out / "sent.json").write_text(json.dumps(sent))
    run("put", str(STACK / "installed.json"), "C:/argonia/MO2/installed.json")
    # a portable MO2 instance description, so houseCARL (which reads MO2 instances) sees this profile
    ini = out / "ModOrganizer.ini"
    ini.write_text("[General]\r\ngameName=Skyrim Special Edition\r\ngamePath=@ByteArray(C:\\\\Program Files (x86)"
                   "\\\\Steam\\\\steamapps\\\\common\\\\Skyrim Special Edition)\r\n"
                   f"selected_profile=@ByteArray({PROFILE})\r\n[Settings]\r\n")
    run("put", str(ini), "C:/argonia/MO2/ModOrganizer.ini")
    (out / "portable.txt").write_text("")
    run("put", str(out / "portable.txt"), "C:/argonia/MO2/portable.txt")
    for f in ("housecarl.ps1", "skylink.ps1", "pad.ps1"):
        run("put", str(HERE / f), f"C:/argonia/infra/{f}")
    for f in ("stack.ps1", "grab.ps1", "splash.ps1", "display.ps1"):
        run("put", str(HERE / f), f"C:/argonia/infra/{f}")
    print(f"pushed {len(todo)} changed of {len(names)} mods")


def cmd_menu(a):
    """Launch through SKSE in the desktop session; main menu = SKSE's data-loaded message plus a still."""
    os.environ.setdefault("DESKTOP_WAIT", "600")
    keep = "$env:ARGONIA_KEEP = '1'; " if os.environ.get("ARGONIA_KEEP") else ""  # leave the game running after
    out = run("desktop", keep + r"& C:\argonia\infra\stack.ps1 menu", capture=True)
    print(out)
    stills = per_machine(STACK / "stills")
    stills.mkdir(exist_ok=True)
    run("get", "C:/argonia/logs/menu.png", str(stills / "menu.png"), check=False)
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
    cmd_masters(a)  # the build VM's Data follows the staged set: the gate reads this profile (game-10: DSC listed, absent)
    # the game quit before the push: a running game holds its DLLs, so a mod the new set drops cannot be removed
    # (game-11: B2's push failed on ModernStaggerLock.dll); a bridge launch keeps it running
    run("ps", r"Get-Process SkyrimSE,skse64_loader -EA SilentlyContinue | Stop-Process -Force; Start-Sleep 3")
    cmd_push(a)
    print(run("ps", r"& C:\argonia\infra\stack.ps1 off", capture=True))  # bare Data first
    os.environ["DESKTOP_WAIT"] = "2000"  # Pandora, or Nemesis (update then generate, 900 s each at most)
    print(run("desktop", r"& C:\argonia\infra\stack.ps1 pandora", capture=True))
    cmd_animdata(a)
    cmd_menu(a)


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
    """After the machine's verify passes: masters first, then each staged mod cut to its plugins (the build VM
    keeps only what ArgoniaGen masters; the machine holds the mod, installed.json its hashes)."""
    out = run("ps", r"& C:\argonia\infra\stack.ps1 on | Out-Null; & C:\argonia\infra\stack.ps1 verify", capture=True)
    print(out.strip()[-600:])
    if "VERIFY OK" not in out:
        raise SystemExit("the machine does not match installed.json: nothing pruned")
    cmd_masters(a)
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


def bsa_names(path):
    """File paths inside a v104/v105 BSA (names only; nothing extracted)."""
    with open(path, "rb") as f:
        magic, version, _, flags, folders, files, _, names_len, _ = struct.unpack("<4sIIIIIIIH2x", f.read(36))
        if magic != b"BSA\0" or version not in (104, 105):
            return []
        rec = 24 if version == 105 else 16
        counts = [struct.unpack("<QII" if version == 104 else "<QIIQ", f.read(rec))[1] for _ in range(folders)]
        dirs = []
        for c in counts:
            dirs.append((f.read(f.read(1)[0])[:-1].decode("latin-1"), c))
            f.seek(16 * c, 1)
        names = f.read(names_len).split(b"\0")
    out, i = [], 0
    for d, c in dirs:
        for _ in range(c):
            out.append(f"{d}\\{names[i].decode('latin-1')}")
            i += 1
    return out


MASTERS_COPIED = "argonia-masters-copied.txt"  # what masters laid in the build VM's Data, so a set switch can undo it


def cmd_masters(a):
    """Plugins and mesh path lists to the build VM's game tree, so ArgoniaGen can master them (0.4). Only the staged
    (active) set's: a plugin an earlier set laid here and this one does not stage is taken out again, with its mesh
    list, so Data, the profile's plugins.txt and argonia-plugins.txt name the same set (game-10: combat B left
    Dark Souls Combat.esp in the profile the gate reads, absent from Data)."""
    game = pathlib.Path(os.environ.get("ARGONIA_GAME_ROOT", HOME / "games" / "skyrimse"))
    data, lists = game / "Data", game / "Data" / "argonia-mesh-lists"
    lists.mkdir(parents=True, exist_ok=True)
    inst = json.loads((STACK / "installed.json").read_text())
    keys = STACK / "staged"
    copied, mods = [], sorted((MO2 / "mods").iterdir())
    for mod in mods:
        kf = keys / f"{mod.name}.json"
        pruned = kf.exists() and json.loads(kf.read_text()).get("pruned")
        meshes = [] if pruned else [k for k, v in inst["files"].items() if v[0] == mod.name and k.startswith("meshes\\")]
        for f in mod.iterdir():
            if f.suffix.lower() in PLUGIN_EXT:
                shutil.copy2(f, data / f.name)
                copied.append(f.name)
            elif f.suffix.lower() == ".bsa" and not pruned:
                meshes += [x.lower() for x in bsa_names(f) if x.lower().startswith("meshes")]
        if meshes:  # a pruned mod's list was written before the prune
            (lists / f"{mod.name}.txt").write_text("\n".join(sorted(set(meshes))) + "\n")
    record = data / MASTERS_COPIED
    now = {c.lower() for c in copied}
    gone = [x for x in (record.read_text().split("\n") if record.exists() else []) if x and x.lower() not in now]
    for x in gone:
        (data / x).unlink(missing_ok=True)
    staged = {m.name for m in mods}
    for f in lists.iterdir():
        if f.stem not in staged:
            f.unlink()
    record.write_text("\n".join(sorted(copied)) + "\n")
    (data / "argonia-plugins.txt").write_text("\n".join(inst["plugins"]) + "\n")
    print(f"{len(copied)} plugins ({len(gone)} of another set taken out) and {len(list(lists.iterdir()))} mesh lists "
          f"in {data}")


COMBAT = {"A": "souls-0.0", "B": "dsc-b", "B2": "dsc-b2"}  # the owner's names for the combat sets
DSC_EVENTS = ["BB_DSC_ForwardRoll_Fast", "BB_DSC_Backstep_Med", "BB_DSC_RightRoll_Fat_MAG",
              "BB_DSC_pa_1HMKillMoveBleedOutKill", "BB_DSC_pa_KillMoveH2HComboA"]  # FNIS b, b, b (MAG), pa, pa


def cmd_combat(a):
    """`combat A|B|B2`: install that set (stack.ps1 on starts from bare Data: the exact undo), then the Pandora check
    when DSC is laid. With --dry DIR: each named set's combat group staged in turn into DIR on the build VM, then
    the first again; the switch must restage only what differs, a second stage of the same set must restage
    nothing, and the first set's files must come back byte for byte. Each set's list is DIR/files-<name>.txt."""
    if not a.dry:
        if len(a.which) != 1:
            raise SystemExit("combat installs one set: A, B or B2")
        a.set = [f"combat={COMBAT[a.which[0]]}"]
        cmd_install(a)
        if a.which[0] != "A":
            cmd_pandora_check(a)
        return
    out, lists = pathlib.Path(a.dry), {}
    out.mkdir(parents=True, exist_ok=True)
    stage = argparse.Namespace(dev=False, through=a.through, into=str(out), group="combat")

    def one(name):
        stage.set = [f"combat={COMBAT[name]}"]
        print(f"== combat {name} ({COMBAT[name]})")
        restaged = cmd_stage(stage) - {THEME, MAP, VIEWS}  # derived overlays, copied afresh by every stage
        inst = json.loads((out / "installed.json").read_text())
        return restaged, inst

    order = list(a.which) + [a.which[0]]
    first = None
    for n, name in enumerate(order):
        restaged, inst = one(name)
        files = {k: v for k, v in inst["files"].items() if not v[0].startswith(("argonia-", "Argonia LOD"))}
        if n == len(order) - 1:
            if files != first:
                raise SystemExit(f"combat {name} again: {len(set(files) ^ set(first))} files differ from its first stage")
            again, _ = one(name)
            if again:
                raise SystemExit(f"combat {name} a second time restaged {sorted(again)}: not idempotent")
            print(f"undo exact: combat {name} again = its first stage ({len(files)} files); a second stage restaged nothing")
            break
        first = first or files
        lists[name] = files
        (out / f"files-{name}.txt").write_text("".join(f"{v[0]}\t{k}\t{v[1]}\n" for k, v in sorted(files.items())))
        rows = sorted({v[0] for v in files.values()})
        dsc = [k for k, v in files.items() if v[0] == "dark-souls-combat"]
        rips = [k for k in dsc if k.startswith("sound\\")]
        if rips:
            raise SystemExit(f"combat {name}: DSC's sound rips are laid: {rips[:3]}")
        print(f"combat {name}: {len(rows)} rows, {len(files)} files, plugins {inst['plugins']}; "
              f"DSC {len(dsc)} files, 0 under sound\\; restaged {len(restaged)}")
    names = list(lists)
    for x, y in zip(names, names[1:]):
        rx, ry = {v[0] for v in lists[x].values()}, {v[0] for v in lists[y].values()}
        print(f"{x} -> {y}: rows out {sorted(rx - ry)}; rows in {sorted(ry - rx)}")


def cmd_pandora_check(a):
    """Pandora read DSC's FNIS list (combat-mod-28567.md §6.1): its engine log names the mod, the generated behaviours
    hold DSC's animation events (the paired killmoves are the open risk) and the animation data its clips. Run on
    the machine after `stack.ps1 pandora`; DSC loads its rolls by these events, so a miss means B is dead."""
    events = ",".join(f"'{e}'" for e in DSC_EVENTS)
    out = run("ps", rf"""
$out = 'C:\argonia\MO2\mods\pandora-output'; $log = 'C:\argonia\logs\pandora-engine.log'
if (Test-Path $log) {{ $l = Select-String -Path $log -Pattern 'BBDarkSoulsCombat|FNIS' | Select -First 20
  "log: $(@(Select-String -Path $log -Pattern 'BBDarkSoulsCombat').Count) DSC lines; $(@(Select-String -Path $log -Pattern 'error|fail' ).Count) error/fail lines"
  $l | % {{ '  ' + $_.Line }} }} else {{ 'log: none (run stack.ps1 pandora first)' }}
$beh = Get-ChildItem "$out\meshes" -Recurse -File -Filter *.hkx -EA SilentlyContinue
foreach ($e in @({events})) {{
  $hit = @($beh | ? {{ [Text.Encoding]::ASCII.GetString([IO.File]::ReadAllBytes($_.FullName)).Contains($e) }} | % Name)
  "event ${{e}}: " + $(if ($hit) {{ $hit -join ' ' }} else {{ 'MISSING' }}) }}
$ad = "$out\meshes\animationdatasinglefile.txt"
"animdata: " + $(if (Test-Path $ad) {{ @(Select-String -Path $ad -Pattern 'BBDarkSoulsCombat' -SimpleMatch).Count }} else {{ 'no file' }}) + ' DSC clip lines'
""", capture=True)
    print(out.strip())
    missing = [ln for ln in out.splitlines() if ln.endswith("MISSING") and "_pa_" not in ln]
    if missing or "log: none" in out:
        raise SystemExit("pandora-check: DSC's FNIS animations did not reach the behaviours (B is dead): " + "; ".join(missing))
    print("PANDORA-DSC OK" + (" (paired killmoves missing: B's own riposte and backstab cannot play)"
                              if "MISSING" in out else ""))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--machine", help="game machine (default $ARGONIA_PLAY, else argonia-play)")
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--record", action="store_true")
    f.add_argument("--only", nargs="*")
    for name in ("stage", "install"):
        s = sub.add_parser(name)
        s.add_argument("--set", action="append", default=[], help="GROUP=SET, e.g. combat=souls-0.0")
        s.add_argument("--dev", action="store_true", help="lay the dev rows too (SkyLink AI, houseCARL)")
        s.add_argument("--through", default=CURRENT_PART,
                       help="lay deferred rows whose `from` chunk has started by this part or chunk (default: the current part)")
        if name == "install":
            s.add_argument("--skip-fetch", action="store_true")
        else:
            s.add_argument("--into", help="stage into this dir instead of ~/.argonia/stack (a dry run)")
            s.add_argument("--group", help="with --into: only this group's rows")
    c = sub.add_parser("combat", help="install combat set A (souls-0.0), B (dsc-b) or B2 (dsc-b2)")
    c.add_argument("which", nargs="+", choices=sorted(COMBAT))
    c.add_argument("--dry", help="stage the combat group of each named set into this scratch dir; check the switch")
    c.add_argument("--dev", action="store_true")
    c.add_argument("--through", default=CURRENT_PART)
    c.add_argument("--skip-fetch", action="store_true")
    for name in ("push", "menu", "masters", "prune", "evict", "animdata", "pandora-check"):
        sub.add_parser(name)
    sub.add_parser("verify").add_argument("--full", action="store_true", help="rehash every file (no cache)")
    a = p.parse_args()
    if a.machine:
        os.environ["ARGONIA_PLAY"] = a.machine  # run.sh reads it
    {"fetch": cmd_fetch, "stage": cmd_stage, "push": cmd_push, "install": cmd_install, "menu": cmd_menu,
     "verify": cmd_verify, "masters": cmd_masters, "prune": cmd_prune, "evict": cmd_evict,
     "animdata": cmd_animdata, "combat": cmd_combat, "pandora-check": cmd_pandora_check}[a.cmd](a)


if __name__ == "__main__":
    main()
