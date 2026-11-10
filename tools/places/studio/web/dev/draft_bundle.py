#!/usr/bin/env python3
"""Resolve a place's files into the draft bundle the studio shows (out/places/bundles/draft.<place_id>/).

The contract's draft bundle is "the place files resolved for viewing": the exterior's refs as written, each
interior the source's copy with our changes over it (a row whose src names a source ref replaces it; `removed`
drops it), bases from the source and ground bundles, and the people, paths, clearance and land files as they are.
Derived, never committed; rerun after the draft or a finalise changes the place files.

    python3 draft_bundle.py <place_id> [--places newworld/places] [--bundles out/places/bundles]
"""
import argparse
import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]


def jsonl(p):
    p = Path(p)
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def write_jsonl(p, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def resolve(place_id, places, bundles):
    pdir = places / place_id
    place = json.loads((pdir / "place.json").read_text(encoding="utf-8"))
    src_id = place["source_id"]
    src, ground = bundles / f"src.{src_id}", bundles / f"ground.{place_id}"
    out = bundles / f"draft.{place_id}.tmp"
    if out.exists():
        shutil.rmtree(out)
    spaces = []
    for sdir in sorted((pdir / "spaces").iterdir()):
        sid, rows = sdir.name, jsonl(sdir / "refs.jsonl")
        info = json.loads((sdir / "space.json").read_text()) if (sdir / "space.json").exists() else {}
        if sid != "exterior" and info.get("copy_of"):
            copied_from = info["copy_of"].split("/", 1)[1]
            base = {r["id"]: dict(r, layer="place") for r in jsonl(src / "spaces" / copied_from / "refs.jsonl")}
            for r in rows:
                base.pop(r.get("src"), None)
                if not r.get("removed"):
                    base[r["id"]] = r
            rows = list(base.values())
            for r in rows:
                r.setdefault("seat", {"mode": "free"})
        info = {"space_id": sid, "type": "exterior" if sid == "exterior" else "interior", **info}
        (out / "spaces" / sid).mkdir(parents=True, exist_ok=True)
        (out / "spaces" / sid / "space.json").write_text(json.dumps(info, indent=1))
        write_jsonl(out / "spaces" / sid / "refs.jsonl", rows)
        spaces.append(sid)
    bases = {r["key"]: r for f in (src / "bases.jsonl", ground / "bases.jsonl") for r in jsonl(f)}
    write_jsonl(out / "bases.jsonl", list(bases.values()))
    write_jsonl(out / "npcs.jsonl", jsonl(src / "npcs.jsonl"))
    for name in ("people", "paths", "clear", "land"):
        write_jsonl(out / f"{name}.jsonl", jsonl(pdir / f"{name}.jsonl"))
    gmeta = json.loads((ground / "bundle.json").read_text())
    meta = {"bundle_id": f"draft.{place_id}", "kind": "draft", "title": f"{place_id} draft", "plugins": gmeta.get("plugins"),
            "worldspace": gmeta.get("worldspace"), "anchor": gmeta.get("anchor"), "cells": gmeta.get("cells"),
            "spaces": spaces, "stamp": {"key": place.get("draft_key"), "inputs": {}, "tool": "studio/web/dev/draft_bundle.py"}}
    (out / "bundle.json").write_text(json.dumps(meta, indent=1))
    final = bundles / f"draft.{place_id}"
    if final.exists():
        shutil.rmtree(final)
    out.rename(final)
    return final, {s: len(jsonl(final / "spaces" / s / "refs.jsonl")) for s in spaces}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("place_id")
    ap.add_argument("--places", default=str(REPO / "newworld" / "places"))
    ap.add_argument("--bundles", default=str(REPO / "out" / "places" / "bundles"))
    a = ap.parse_args()
    path, counts = resolve(a.place_id, Path(a.places), Path(a.bundles))
    print(path, sum(counts.values()), "refs in", len(counts), "spaces")
