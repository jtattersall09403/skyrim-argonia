"""The draft bundle: a place's files resolved for viewing, `out/places/bundles/draft.<place_id>/`, to the bundle
contract (docs/design/place-studio.md, Bundles). The exterior's refs as written; each interior the source's copy
with our changes over it, keeping only the room the build keeps (Build, recipe step 2); people, paths, cleared
plants and land patches as written; bases from the source and ground bundles; actor bases from the source.
Stamped with a key over the place files and the source and ground bundles' stamps; an unchanged key is not rebuilt.
Unknown fields are carried through untouched.

  python -m tools.places draft_bundle <place_id> [--force]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLACES = ROOT / "newworld" / "places"
BUNDLES = ROOT / "out" / "places" / "bundles"
# A bundle ref's kind as the record type the build's room rule reads (tools.places.build.kind_of, inverted)
BASE_TYPE = {"static": "STAT", "door": "DOOR", "furniture": "FURN", "container": "CONT", "light": "LIGH",
             "activator": "ACTI", "plant": "FLOR", "tree": "TREE", "marker": "IDLM", "actor": "NPC_"}
FILES = ("people", "paths", "clear", "land")
TOOL = "tools/places/draft_bundle.py v4"
CATALOGUE = ROOT / "out" / "places" / "catalogue" / "bases.jsonl"
_catalogue: dict = {}


def catalogue(path: Path | None = None) -> dict:
    """The asset catalogue indexed by key, read once per file change (39,280 rows)."""
    p = Path(path or os.environ.get("PLACES_CATALOGUE") or CATALOGUE)
    m = p.stat().st_mtime_ns if p.exists() else None
    if _catalogue.get("at") != (str(p), m):
        _catalogue.clear()
        _catalogue.update(at=(str(p), m), rows={r["key"]: r for r in jsonl(p)})
    return _catalogue["rows"]


def jsonl(p: Path) -> list[dict]:
    p = Path(p)
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def write_jsonl(p: Path, rows) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def place_json(place_id: str, places: Path) -> dict:
    return json.loads((places / place_id / "place.json").read_text(encoding="utf-8"))


def git(cwd: Path, *args, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, timeout=120, **kw)


def committed(place_id: str, places: Path = PLACES, bundles: Path = BUNDLES) -> tuple[Path, str]:
    """The place files as committed: (a places root holding <place_id>/, its id). Inside a git work tree that is
    a snapshot of HEAD:<places>/<place_id> under out/places/snapshots/, keyed by the path's tree sha, so a redraft
    in the working tree is never seen until it is committed. Outside git (tests), the folder itself and a hash of
    its files."""
    top = git(places, "rev-parse", "--show-toplevel", text=True)
    if top.returncode == 0:
        rel = (places / place_id).resolve().relative_to(Path(top.stdout.strip()).resolve()).as_posix()
        t = git(places, "rev-parse", f"HEAD:{rel}", text=True)
        if t.returncode != 0:
            raise FileNotFoundError(f"{rel} is not committed")
        tree = t.stdout.strip()
        snaps = bundles.parent / "snapshots"
        root = snaps / f"{place_id}.{tree[:16]}"
        if not (root / place_id / "place.json").exists():  # a failed or empty snapshot is redone
            tmp = snaps / f".{place_id}.{tree[:16]}.{os.getpid()}.tmp"
            shutil.rmtree(tmp, ignore_errors=True)
            (tmp / place_id).mkdir(parents=True)
            arc = git(Path(top.stdout.strip()), "archive", "--format=tar", tree)  # from the top: a subdir limits it
            if arc.returncode != 0:
                raise RuntimeError(arc.stderr.decode()[-300:])
            with tarfile.open(fileobj=io.BytesIO(arc.stdout)) as tf:
                tf.extractall(tmp / place_id, filter="data")
            shutil.rmtree(root, ignore_errors=True)
            tmp.rename(root)
            for old in snaps.glob(f"{place_id}.*"):  # one snapshot per place is enough
                if old != root:
                    shutil.rmtree(old, ignore_errors=True)
        return root, tree
    pdir = places / place_id
    h = hashlib.sha256()
    for p in sorted(pdir.rglob("*")):
        if p.is_file() and "edits" not in p.relative_to(pdir).parts:
            h.update(str(p.relative_to(pdir)).encode())
            h.update(p.read_bytes())
    return places, h.hexdigest()


def key(place_id: str, places: Path = PLACES, bundles: Path = BUNDLES) -> str:
    """sha256 over the committed place's tree id and the source and ground bundles' bundle.json."""
    root, tree = committed(place_id, places, bundles)
    h = hashlib.sha256(TOOL.encode() + tree.encode())
    src_id = place_json(place_id, root).get("source_id")
    for b in (f"src.{src_id}", f"ground.{place_id}"):
        bj = bundles / b / "bundle.json"
        h.update(b.encode() + (bj.read_bytes() if bj.exists() else b"-"))
    return h.hexdigest()


def current_key(place_id: str, bundles: Path = BUNDLES) -> str | None:
    bj = bundles / f"draft.{place_id}" / "bundle.json"
    try:
        return json.loads(bj.read_text())["stamp"]["key"]
    except (OSError, ValueError, KeyError, TypeError):
        return None


def stale(place_id: str, places: Path = PLACES, bundles: Path = BUNDLES) -> bool:
    return current_key(place_id, bundles) != key(place_id, places, bundles)


def copy_space(info: dict, rows: list[dict], src: Path) -> list[dict]:
    """An interior: the source cell's refs (no actors; one room only when `room` names it, by the build's room_partition), with our
    rows over them: a row with `src` changes that ref (or drops it when `removed`), ignored when its src is outside
    the kept room; a row without `src` is added."""
    copied_from = info["copy_of"].split("/", 1)[1]
    srows = [r for r in jsonl(src / "spaces" / copied_from / "refs.jsonl") if r.get("kind") != "actor"]
    if info.get("room"):  # one room of a shared cell: exactly the room the build makes (Build, the room rule)
        from tools.places.build import room_partition
        rows_b = [{"fk": r["id"], "base": r["base"], "pos": r["pos"], "rot": r.get("rot"), "scale": r.get("scale"),
                   "door": r.get("door"), "base_type": BASE_TYPE.get(r.get("kind"), "MISC")}
                  for r in srows if r.get("pos")]
        work = BUNDLES.parent / "work" / "draft_bundle"
        work.mkdir(parents=True, exist_ok=True)
        room = room_partition(info["copy_of"], rows_b, work)["rooms"].get(info["room"])
        keep = room["refs"] if room else set()
        srows = [r for r in srows if r["id"] in keep]
    out = {r["id"]: dict(r, layer="place", src=r["id"], seat={"mode": "free"}) for r in srows}
    for r in rows:
        s = r.get("src")
        if s:
            if s not in out:
                continue
            if r.get("removed"):
                out.pop(s)
                continue
            out[s] = out[s] | r
            out[r["id"]] = out.pop(s) if r["id"] != s else out[s]
        elif not r.get("removed"):
            out[r["id"]] = r
    return list(out.values())


def build(place_id: str, places: Path = PLACES, bundles: Path = BUNDLES, force: bool = False) -> dict:
    k = key(place_id, places, bundles)
    if not force and current_key(place_id, bundles) == k:
        return {"bundle_id": f"draft.{place_id}", "key": k, "rebuilt": False}
    places, _ = committed(place_id, places, bundles)
    pdir = places / place_id
    place = place_json(place_id, places)
    src, ground = bundles / f"src.{place['source_id']}", bundles / f"ground.{place_id}"
    out = bundles / f".draft.{place_id}.{os.getpid()}.tmp"
    shutil.rmtree(out, ignore_errors=True)
    spaces, counts = [], {}
    for sdir in sorted(p for p in (pdir / "spaces").iterdir() if p.is_dir()):
        sid, rows = sdir.name, jsonl(sdir / "refs.jsonl")
        info = json.loads((sdir / "space.json").read_text(encoding="utf-8")) if (sdir / "space.json").exists() else {}
        if sid != "exterior" and info.get("copy_of"):
            rows = copy_space(info, rows, src)
        info = {"space_id": sid, "type": "exterior" if sid == "exterior" else "interior"} | info
        if sid == "exterior" and (ground / "spaces" / "exterior" / "space.json").exists():
            info = json.loads((ground / "spaces" / "exterior" / "space.json").read_text()) | info
        (out / "spaces" / sid).mkdir(parents=True, exist_ok=True)
        (out / "spaces" / sid / "space.json").write_text(json.dumps(info, indent=1, ensure_ascii=False))
        write_jsonl(out / "spaces" / sid / "refs.jsonl", rows)
        spaces.append(sid)
        counts[sid] = len(rows)
    # every base a ref uses: the source bundle first (then the ground's), else the catalogue; none: reported
    bases = {r["key"]: r for f in (ground / "bases.jsonl", src / "bases.jsonl") for r in jsonl(f)}
    used: dict[str, int] = {}
    for sid in spaces:
        for r in jsonl(out / "spaces" / sid / "refs.jsonl"):
            if r.get("base"):
                used[r["base"]] = used.get(r["base"], 0) + 1
    cat, missing = None, []
    for bk, n in sorted(used.items()):
        if bk not in bases:
            cat = cat if cat is not None else catalogue()
            if bk in cat:
                bases[bk] = cat[bk]
            else:
                missing.append({"missing_base": bk, "refs": n})
    write_jsonl(out / "bases.jsonl", bases.values())
    write_jsonl(out / "npcs.jsonl", jsonl(src / "npcs.jsonl"))
    for name in FILES:
        write_jsonl(out / f"{name}.jsonl", jsonl(pdir / f"{name}.jsonl"))
    gmeta = json.loads((ground / "bundle.json").read_text()) if (ground / "bundle.json").exists() else {}
    stamp_in = {f"src.{place['source_id']}": (json.loads((src / "bundle.json").read_text()).get("stamp") or {})
                .get("inputs") if (src / "bundle.json").exists() else None,
                f"ground.{place_id}": (gmeta.get("stamp") or {}).get("inputs")}
    meta = {"bundle_id": f"draft.{place_id}", "kind": "draft", "title": f"{place_id} (draft)",
            "plugins": gmeta.get("plugins"), "worldspace": gmeta.get("worldspace"), "anchor": gmeta.get("anchor"),
            "cells": gmeta.get("cells"), "spaces": spaces,
            "stamp": {"key": k, "draft_key": place.get("draft_key"), "inputs": stamp_in, "tool": TOOL, "missing_bases": missing,
                      "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}}
    (out / "bundle.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    # draft.<id> is a symlink to a finished folder, swapped in one atomic rename: no request sees a half bundle
    final = bundles / f"draft.{place_id}"
    ver = bundles / f".draft.{place_id}.{k[:16]}"
    shutil.rmtree(ver, ignore_errors=True)
    out.rename(ver)
    link = bundles / f".draft.{place_id}.{os.getpid()}.link"
    link.unlink(missing_ok=True)
    link.symlink_to(ver.name)
    if final.exists() and not final.is_symlink():
        shutil.rmtree(final)
    os.replace(link, final)
    for old in bundles.glob(f".draft.{place_id}.*"):
        if old != ver and not old.name.endswith((".tmp", ".link")):
            shutil.rmtree(old, ignore_errors=True)
    return {"bundle_id": f"draft.{place_id}", "key": k, "rebuilt": True, "refs": counts, "missing_bases": missing}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places draft_bundle")
    ap.add_argument("place_id")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    r = build(a.place_id, force=a.force)
    print(json.dumps(r))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
