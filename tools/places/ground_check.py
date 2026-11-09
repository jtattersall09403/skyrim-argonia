"""python -m tools.places ground-check <place_id> [--json]

Passes only when the ground bundle `ground.<place_id>` was extracted from exactly the world file the play machine
has: the bundle's stamped ESM sha256 equals out/newworld/verify/play-esm.sha256 (the play machine's copy, hashed
back by `infra/gpu-box/lod.sh send`). It also says when the bundle is behind the ESM built here. Never a silent pass:
an absent or stale record fails with what to run. `check()` is the same test for the studio's status.
"""
from __future__ import annotations

import argparse
import json
import time

from tools.places.bundle import BUNDLES, REPO, sha256_file

ESM = REPO / "out" / "newworld" / "plugin" / "ArgoniaNewWorld.esm"
PLAY_SHA = REPO / "out" / "newworld" / "verify" / "play-esm.sha256"


def _iso(t: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def check(place_id: str) -> dict:
    """{ok, reason, ground_sha, built_sha, play_sha, play_recorded_at, built_at}; ok only on a proven match."""
    res = {"place_id": place_id, "ok": False, "ground_sha": None, "built_sha": None, "play_sha": None,
           "play_recorded_at": None, "built_at": None, "reason": ""}
    meta_f = BUNDLES / f"ground.{place_id}" / "bundle.json"
    if not meta_f.exists():
        res["reason"] = f"no ground bundle: run `python -m tools.places extract --ground {place_id}`"
        return res
    meta = json.loads(meta_f.read_text())
    ground = (meta.get("esm") or {}).get("sha256")
    res["ground_sha"] = ground
    if not ground:
        res["reason"] = "the ground bundle carries no ESM stamp: re-extract it"
        return res
    if ESM.exists():
        res["built_sha"] = sha256_file(ESM)
        res["built_at"] = _iso(ESM.stat().st_mtime)
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
    if ground == play:
        res["ok"] = True
        res["reason"] = "the ground is the play machine's world file"
        if res["built_sha"] and res["built_sha"] != ground:
            res["reason"] += f" (a newer build {res['built_sha'][:12]} is here, not yet sent)"
        return res
    stale = ESM.exists() and PLAY_SHA.stat().st_mtime < ESM.stat().st_mtime
    if res["built_sha"] and res["built_sha"] != ground:
        res["reason"] = (f"the ground bundle ({ground[:12]}) is behind the built world file ({res['built_sha'][:12]}): "
                         f"run `python -m tools.places extract --ground {place_id}`")
    elif stale:
        res["reason"] = (f"the play machine's record ({play[:12]}, {res['play_recorded_at']}) predates the build "
                         f"({res['built_at']}): deploy with `infra/gpu-box/lod.sh send`")
    else:
        res["reason"] = f"the play machine has {play[:12]}, the ground was read from {ground[:12]}: deploy or re-extract"
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
