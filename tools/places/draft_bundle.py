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
import json
import math
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLACES = ROOT / "newworld" / "places"
BUNDLES = ROOT / "out" / "places" / "bundles"
ROOM_RADIUS = 1200.0  # the build's `room` rule: the source refs this near the room ref (Build, step 2)
FILES = ("people", "paths", "clear", "land")
TOOL = "tools/places/draft_bundle.py v1"


def jsonl(p: Path) -> list[dict]:
    p = Path(p)
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def write_jsonl(p: Path, rows) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def place_json(place_id: str, places: Path) -> dict:
    return json.loads((places / place_id / "place.json").read_text(encoding="utf-8"))


def key(place_id: str, places: Path = PLACES, bundles: Path = BUNDLES) -> str:
    """sha256 over every place file (saves excepted) and the source and ground bundles' bundle.json."""
    pdir = places / place_id
    h = hashlib.sha256(TOOL.encode())
    for p in sorted(pdir.rglob("*")):
        if p.is_file() and "edits" not in p.relative_to(pdir).parts:
            h.update(str(p.relative_to(pdir)).encode())
            h.update(p.read_bytes())
    src_id = place_json(place_id, places).get("source_id")
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
    """An interior: the source cell's refs (no actors; one room only when `room` or `keep_within` says), with our
    rows over them: a row with `src` changes that ref (or drops it when `removed`), ignored when its src is outside
    the kept room; a row without `src` is added."""
    copied_from = info["copy_of"].split("/", 1)[1]
    srows = [r for r in jsonl(src / "spaces" / copied_from / "refs.jsonl") if r.get("kind") != "actor"]
    keep = info.get("keep_within")
    if not keep and info.get("room"):
        rr = next((r for r in srows if r.get("id") == info["room"] and r.get("pos")), None)
        if rr:
            keep = {"pos": rr["pos"], "radius": ROOM_RADIUS}
    if keep:
        srows = [r for r in srows if r.get("pos") and math.dist(r["pos"], keep["pos"]) <= keep["radius"]]
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
    bases = {r["key"]: r for f in (ground / "bases.jsonl", src / "bases.jsonl") for r in jsonl(f)}
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
            "stamp": {"key": k, "draft_key": place.get("draft_key"), "inputs": stamp_in, "tool": TOOL,
                      "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}}
    (out / "bundle.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    final = bundles / f"draft.{place_id}"
    old = bundles / f".draft.{place_id}.{os.getpid()}.old"
    if final.exists():
        final.rename(old)
    out.rename(final)
    shutil.rmtree(old, ignore_errors=True)
    return {"bundle_id": f"draft.{place_id}", "key": k, "rebuilt": True, "refs": counts}


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
