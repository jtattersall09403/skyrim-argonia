"""python -m tools.places ground-check <place_id> [--json]

Passes only when the ground bundle `ground.<place_id>` stands on the world records the world file holds, here and
on the play machine: the bundle's stamp of them (its cells' LAND and placed references, the bases they name, the
worldspace, the land textures: tools/places/worldparts.py) is read again from the world file built here, and the
play machine's copy (out/newworld/verify/play-esm.sha256, hashed back by `infra/gpu-box/lod.sh send`) is a file that
holds the same. A world file rewritten with none of them changed leaves the bundle current; one that changes any
names which. Never a silent pass: an absent record fails with what to run. `check()` is the same test for the
studio's status.
"""
from __future__ import annotations

import argparse
import json
import time

from tools.places import worldparts
from tools.places.bundle import BUNDLES, REPO, sha256_file

ESM = REPO / "out" / "newworld" / "plugin" / "ArgoniaNewWorld.esm"
PLAY_SHA = REPO / "out" / "newworld" / "verify" / "play-esm.sha256"


def _iso(t: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def check(place_id: str) -> dict:
    """{ok, reason, ground_sha, built_sha, play_sha, play_recorded_at, built_at, changed}; ok only on a proven
    match. `ground_sha` is the world file the bundle was read from, `changed` what of the world moved under it."""
    res = {"place_id": place_id, "ok": False, "ground_sha": None, "built_sha": None, "play_sha": None,
           "play_recorded_at": None, "built_at": None, "changed": [], "reason": ""}
    extract = f"run `python -m tools.places extract --ground {place_id}`"
    meta_f = BUNDLES / f"ground.{place_id}" / "bundle.json"
    if not meta_f.exists():
        res["reason"] = f"no ground bundle: {extract}"
        return res
    meta = json.loads(meta_f.read_text())
    st = meta.get("world")
    res["ground_sha"] = (meta.get("esm") or {}).get("sha256")
    if not st:
        res["reason"] = f"the ground bundle names no world records it stands on: {extract}"
        return res
    if not ESM.exists():
        res["reason"] = f"no world file here ({ESM.relative_to(REPO)}): build the world"
        return res
    res["built_sha"] = sha256_file(ESM)
    res["built_at"] = _iso(ESM.stat().st_mtime)
    res["changed"] = worldparts.changed(st, ESM)
    if res["changed"]:
        res["reason"] = f"under the ground bundle the world changed: {'; '.join(res['changed'])}: {extract}"
        return res
    if not PLAY_SHA.exists():
        res["reason"] = (f"no record of the play machine's world file ({PLAY_SHA.relative_to(REPO)} is absent): "
                         "deploy with `infra/gpu-box/lod.sh send`, which hashes the machine's copy back")
        return res
    play = PLAY_SHA.read_text().strip().lower()
    res["play_sha"] = play or None
    res["play_recorded_at"] = _iso(PLAY_SHA.stat().st_mtime)
    if len(play) != 64:
        res["reason"] = f"{PLAY_SHA.relative_to(REPO)} holds no sha256 ({play[:20]!r}): resend with `infra/gpu-box/lod.sh send`"
        return res
    holds = True if play == res["built_sha"] else worldparts.file_holds(st, play)
    if holds:
        res["ok"] = True
        res["reason"] = "the ground stands on the world records the play machine's world file holds"
        if play != res["built_sha"]:
            res["reason"] += f" (a newer build {res['built_sha'][:12]} is here, not yet sent; it changes none of them)"
    elif holds is None:
        res["reason"] = (f"the play machine's world file ({play[:12]}, {res['play_recorded_at']}) was never read here: "
                         "deploy with `infra/gpu-box/lod.sh send`")
    else:
        res["reason"] = (f"the play machine's world file ({play[:12]}) holds other records under this ground than the "
                         "build here: deploy with `infra/gpu-box/lod.sh send`")
    return res


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places ground-check")
    ap.add_argument("place_id")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    res = check(a.place_id)
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(("PASS" if res["ok"] else "FAIL") + f" ground.{a.place_id}: {res['reason']}")
    return 0 if res["ok"] else 1


def status(place_id: str | None = None) -> dict:
    """The studio's view: {ground_sha, deployed_sha, match, reason, ...check()}; with no place, the newest ground
    bundle on disk."""
    if place_id is None:
        grounds = sorted(BUNDLES.glob("ground.*/bundle.json"), key=lambda p: p.stat().st_mtime)
        if not grounds:
            return {"ground_sha": None, "deployed_sha": None, "match": False, "ok": False,
                    "reason": "no ground bundle: run `python -m tools.places extract --ground <place_id>`"}
        place_id = grounds[-1].parent.name.removeprefix("ground.")
    res = check(place_id)
    return dict(res, deployed_sha=res["play_sha"], match=res["ok"])
