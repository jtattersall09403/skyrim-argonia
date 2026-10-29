#!/usr/bin/env python3
"""The Argonia profile: every row of data/dependencies.json fetched, verified, staged and laid over a clean Data on
the game machine, with exact undo (chunk 0.2 §b; grew from 0.0's combat_test_stage.py).

  stack.py fetch [--record] [--only ID ...]   download each row to ~/.argonia/mods (Nexus API, GitHub, the private
                                              cache in S3, the old vault); check sha256; --record writes new hashes
  stack.py stage [--set GROUP=SET] [--dev]    unpack and place each row into ~/.argonia/stack/MO2/mods/<id>/, apply
                                              the recorded FOMOD choices and ini settings, write the profile
                                              (modlist, plugins.txt, loadorder.txt) and installed.json (every file's hash)
  stack.py push                               send changed mod folders and the profile to C:\\argonia\\MO2 on the machine
  stack.py install [--set ...] [--dev]        fetch, stage, push, then on the machine: stack.ps1 on (bare Data first),
                                              Pandora, and the main-menu check
  stack.py menu                               launch through SKSE, wait for the main menu, keep a still, list each DLL's load
  stack.py verify                             archives against the manifest; every laid file in Data against installed.json
  stack.py masters                            plugins (ESM/ESP/ESL) and mesh path lists to $ARGONIA_GAME_ROOT/Data (0.4)

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
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
MANIFEST = REPO / "data" / "dependencies.json"
HOME = pathlib.Path.home()
MODS = HOME / ".argonia" / "mods"
STACK = HOME / ".argonia" / "stack"
MO2 = STACK / "MO2"
PROFILE = "Argonia"
RUN = str(HERE / "run.sh")
API = "https://api.nexusmods.com/v1"
CACHE_BUCKET = "argonia-private-050977237313"
GAME_DATA = r"C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data" + "\\"
MAX_PATH = 259  # Skyrim's loose-file scan overruns a MAX_PATH buffer on any path of 260+ characters (0.0)
DATA_DIRS = {"meshes", "textures", "scripts", "skse", "interface", "sound", "music", "seq", "nemesis_engine",
             "pandora_engine", "mcm", "source", "strings", "video", "lodsettings", "grass", "shadersfx", "calientetools",
             "netscriptframework", "dyndolod", "materials", "platform"}
PLUGIN_EXT = (".esp", ".esm", ".esl")


# ---- manifest -----------------------------------------------------------------------------------------------------

def manifest():
    return json.loads(MANIFEST.read_text())


def save_manifest(doc):
    MANIFEST.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")


def chosen(doc, sets, dev):
    """The rows the profile lays, in load order: play rows (dev rows with --dev), one set per group."""
    pick = {g: names[0] for g, names in doc.get("sets", {}).items()}
    pick.update(sets)
    out = []
    for m in doc["mods"]:
        if m["profile"] == "pipeline" or (m["profile"] == "dev" and not dev):
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
    if "nexus" in s:
        link = json.load(urllib.request.urlopen(urllib.request.Request(
            f"{API}/games/{s['nexus']}/mods/{s['mod']}/files/{s['file']}/download_link.json",
            headers={"apikey": key, "User-Agent": "argonia-stack/0.2"}), timeout=60))[0]["URI"]
        download(urllib.parse.quote(link, safe=":/?&=%~+"), dest)
    elif "github" in s:
        download(f"https://github.com/{s['github']}/releases/download/{urllib.parse.quote(s['tag'], safe='')}/"
                 f"{urllib.parse.quote(s['asset'])}", dest)
    else:  # a manual download (ModDB): the private S3 cache first, then the old vault (R2)
        if s3("cp", f"s3://{CACHE_BUCKET}/mods/{dest.name}", str(dest)).returncode != 0:
            sys.path.insert(0, str(REPO / "tools"))
            import fetch_vault as fv  # noqa: E402 (needs boto3: the toolchain venv)
            body = fv.client(fv.secrets()).get_object(Bucket=fv.BUCKET, Key=f"{fv.PREFIX}{s['vault']}.tar")["Body"]
            tmp = dest.with_name(dest.name + ".part")
            with open(tmp, "wb") as f:
                while c := body.read(8 << 20):
                    f.write(c)
            tmp.rename(dest)
    return dest, "got"


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
        if "vault" in m["source"] and s3("ls", f"s3://{CACHE_BUCKET}/mods/{path.name}").returncode != 0:
            s3("cp", str(path), f"s3://{CACHE_BUCKET}/mods/{path.name}")  # the private cache (0.2 §b)
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
        if len(items) == 1 and dirs and dirs[0].name.lower() == "data":
            return dirs[0]
        if len(items) == 1 and dirs and dirs[0].name.lower() not in DATA_DIRS:
            root = dirs[0]
        else:
            return root


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
        for f in list(data.rglob("*")):
            if fnmatch.fnmatch(str(f.relative_to(data)).lower(), pat.lower()):
                shutil.rmtree(f) if f.is_dir() else f.unlink()
    for d in sorted((x for x in data.rglob("*") if x.is_dir()), key=lambda x: -len(x.parts)):
        if not any(d.iterdir()):
            d.rmdir()
    too_long = [f for f in data.rglob("*") if f.is_file() and len(GAME_DATA) + len(str(f.relative_to(data))) > MAX_PATH]
    if too_long:
        raise SystemExit(f"paths too long for Skyrim in {m['id']}: {too_long[0].relative_to(data)}")


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
    """The row's settings: {"file": glob under the mod, "section": name or null, "set": {key: value}}."""
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


def cmd_stage(a):
    doc = manifest()
    rows = chosen(doc, dict(s.split("=", 1) for s in a.set), a.dev)
    mods, tools, root, work = MO2 / "mods", MO2 / "tools", MO2 / "root", STACK / "_unpacked"
    for d in (mods, tools, root):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
    names, record = [], {}
    for m in rows:
        src = work / m["id"]
        unpack(archive_path(m), src)
        data = mods / m["id"]
        data.mkdir()
        taken = place(m, src, data, tools, root)
        shutil.rmtree(src)
        prune(data, m)
        apply_ini(m, data)
        if any(data.iterdir()):
            names.append(m["id"])
        record[m["id"]] = {"fomod": taken} if taken else {}
        print(f"staged {m['id']}" + (f" ({'; '.join(taken)})" if taken else ""))
    shutil.rmtree(work, ignore_errors=True)
    names.append("pandora-output")  # filled when Pandora runs on the machine; highest priority
    (mods / "pandora-output").mkdir(exist_ok=True)
    prof = MO2 / "profiles" / PROFILE
    shutil.rmtree(prof, ignore_errors=True)
    prof.mkdir(parents=True)
    (prof / "modlist.txt").write_text("".join(f"+{n}\r\n" for n in reversed(names)))  # MO2 order: highest first
    plugins, have = [], {p.lower() for p in vanilla_plugins()}
    for n in names:
        for f in sorted((mods / n).iterdir()):
            if f.suffix.lower() in PLUGIN_EXT and f.name.lower() not in have:
                missing = [x for x in masters_of(f) if x.lower() not in have]
                if missing:
                    raise SystemExit(f"{n}: {f.name} needs masters not loaded before it: {missing}")
                plugins.append(f.name)
                have.add(f.name.lower())
    (prof / "plugins.txt").write_text("".join(f"*{p}\r\n" for p in plugins))
    (prof / "loadorder.txt").write_text("".join(f"{p}\r\n" for p in vanilla_plugins() + plugins))
    files = {}
    for n in names:
        for f in sorted((mods / n).rglob("*")):
            if f.is_file():
                files[str(f.relative_to(mods / n)).replace("/", "\\").lower()] = [n, sha256(f)]  # later mods win
    for f in sorted(root.rglob("*")):
        if f.is_file():
            files["..\\" + f.name.lower()] = ["skse", sha256(f)]
    (STACK / "installed.json").write_text(json.dumps({"rows": record, "plugins": plugins, "files": files}, indent=0))
    print(f"profile {PROFILE}: {len(names) - 1} mods, {len(plugins)} plugins, {len(files)} files")


# ---- the machine --------------------------------------------------------------------------------------------------

def run(*args, check=True, capture=False):
    r = subprocess.run([RUN, *args], text=True, capture_output=capture)
    if check and r.returncode != 0:
        raise SystemExit(f"run.sh {args[0]} failed: {(r.stderr or '')[-400:]}")
    return r.stdout if capture else ""


def cmd_push(a):
    """Tar each changed mod folder, copy it over and unpack it into C:\\argonia\\MO2\\mods\\<id>."""
    out = STACK / "push"
    out.mkdir(exist_ok=True)
    sent = json.loads((out / "sent.json").read_text()) if (out / "sent.json").exists() else {}
    names = [d.name for d in sorted((MO2 / "mods").iterdir())]
    digest = {}
    inst = json.loads((STACK / "installed.json").read_text())["files"]
    for n in names:
        digest[n] = hashlib.sha256("".join(sorted(f"{k}{v[1]}" for k, v in inst.items() if v[0] == n)).encode()).hexdigest()
    todo = [n for n in names if sent.get(n) != digest[n] and n != "pandora-output"]
    run("ps", r"New-Item -ItemType Directory -Force C:\argonia\MO2\mods, C:\argonia\MO2\push, C:\argonia\MO2\tools,"
              rf" C:\argonia\MO2\profiles\{PROFILE}, C:\argonia\MO2\root | Out-Null")
    batch = [todo[i:i + 12] for i in range(0, len(todo), 12)]
    for group in batch:
        for n in group:
            subprocess.run(["tar", "-cf", str(out / f"{n}.tar"), "-C", str(MO2 / "mods" / n), "."], check=True)
            run("put", str(out / f"{n}.tar"), f"C:/argonia/MO2/push/{n}.tar")
            (out / f"{n}.tar").unlink()
        script = "; ".join(rf"Remove-Item -Recurse -Force -LiteralPath 'C:\argonia\MO2\mods\{n}' -EA SilentlyContinue; "
                           rf"New-Item -ItemType Directory -Force 'C:\argonia\MO2\mods\{n}' | Out-Null; "
                           rf"tar -xf 'C:\argonia\MO2\push\{n}.tar' -C 'C:\argonia\MO2\mods\{n}'; "
                           rf"Remove-Item 'C:\argonia\MO2\push\{n}.tar'" for n in group)
        run("ps", script)
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
    for f in ("stack.ps1", "grab.ps1", "splash.ps1", "display.ps1"):
        run("put", str(HERE / f), f"C:/argonia/infra/{f}")
    print(f"pushed {len(todo)} changed of {len(names)} mods")


def cmd_menu(a):
    """Launch through SKSE in the desktop session; main menu = SKSE's data-loaded message plus a still."""
    out = run("desktop", r"& C:\argonia\infra\stack.ps1 menu", capture=True)
    print(out)
    if "MAIN-MENU OK" not in out:
        raise SystemExit("main menu not reached")
    loaded = [l for l in out.splitlines() if "loaded correctly" in l]
    failed = [l for l in out.splitlines() if l.startswith("plugin ") and "loaded correctly" not in l
              and "no version data" not in l]
    print(f"{len(loaded)} DLLs loaded, {len(failed)} not")
    if failed:
        raise SystemExit("DLLs failed:\n" + "\n".join(failed))


def cmd_install(a):
    if not a.skip_fetch:
        cmd_fetch(argparse.Namespace(record=False, only=None))
    cmd_stage(a)
    cmd_push(a)
    print(run("ps", r"& C:\argonia\infra\stack.ps1 off", capture=True))  # bare Data first
    print(run("desktop", r"& C:\argonia\infra\stack.ps1 pandora", capture=True))
    cmd_menu(a)


def cmd_verify(a):
    doc, bad = manifest(), []
    for m in doc["mods"]:
        p = archive_path(m)
        if not p.exists():
            bad.append(f"{m['id']}: archive missing")
        elif m.get("sha256") != sha256(p):
            bad.append(f"{m['id']}: archive sha256 differs from the manifest")
    print(f"archives: {len(doc['mods']) - len(bad)} of {len(doc['mods'])} match")
    out = run("ps", r"& C:\argonia\infra\stack.ps1 verify", capture=True)
    print(out.strip()[-2000:])
    if "VERIFY OK" not in out:
        bad.append("installed files differ (above)")
    if bad:
        raise SystemExit("\n".join(bad))


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


def cmd_masters(a):
    """Plugins and mesh path lists to the build VM's game tree, so ArgoniaGen can master them (0.4)."""
    game = pathlib.Path(os.environ.get("ARGONIA_GAME_ROOT", HOME / "games" / "skyrimse"))
    data, lists = game / "Data", game / "Data" / "argonia-mesh-lists"
    lists.mkdir(parents=True, exist_ok=True)
    inst = json.loads((STACK / "installed.json").read_text())
    n = 0
    for mod in sorted((MO2 / "mods").iterdir()):
        meshes = [k for k, v in inst["files"].items() if v[0] == mod.name and k.startswith("meshes\\")]
        for f in mod.iterdir():
            if f.suffix.lower() in PLUGIN_EXT:
                shutil.copy2(f, data / f.name)
                n += 1
            elif f.suffix.lower() == ".bsa":
                meshes += [x.lower() for x in bsa_names(f) if x.lower().startswith("meshes")]
        if meshes:
            (lists / f"{mod.name}.txt").write_text("\n".join(sorted(set(meshes))) + "\n")
    (data / "argonia-plugins.txt").write_text("\n".join(inst["plugins"]) + "\n")
    print(f"{n} plugins and {len(list(lists.iterdir()))} mesh lists in {data}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--record", action="store_true")
    f.add_argument("--only", nargs="*")
    for name in ("stage", "install"):
        s = sub.add_parser(name)
        s.add_argument("--set", action="append", default=[], help="GROUP=SET, e.g. combat=souls-0.0")
        s.add_argument("--dev", action="store_true", help="lay the dev rows too (SkyLink AI, houseCARL)")
        if name == "install":
            s.add_argument("--skip-fetch", action="store_true")
    for name in ("push", "menu", "verify", "masters"):
        sub.add_parser(name)
    a = p.parse_args()
    {"fetch": cmd_fetch, "stage": cmd_stage, "push": cmd_push, "install": cmd_install, "menu": cmd_menu,
     "verify": cmd_verify, "masters": cmd_masters}[a.cmd](a)


if __name__ == "__main__":
    main()
