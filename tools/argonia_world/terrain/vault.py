"""The old project's derived terrain inputs that 2.W1 reads beside the frozen arrays, fetched from the R2 vault.

The five frozen arrays come through `tools/fetch_vault.py` against `freeze.json`. The land-cover raster, the
apron source (the Transbot9 All-Tamriel heightmap cropped and resampled 1:1 by the old chain's
`build_border_apron`, CC BY-NC 4.0, credited in the sourcing register) and the old chain's post-patch heightfield
(the oracle the patch applier is checked against) are derived files, not frozen ones, so they are pinned here by
sha256 as first fetched (2026-10-29) and land in `$ARGONIA_DATA/terrain/`. Nothing here is committed to git.

    python3 -m tools.argonia_world.terrain.vault            fetch what is missing or wrong
    python3 -m tools.argonia_world.terrain.vault --check    report only
    python3 -m tools.argonia_world.terrain.vault --pin      fetch and print the sha256 of each (first fetch)
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

_TW = "snapshot/v1/mod-sources/tamriel-worldspaces-118678.tar"
_HF = "elder-scrolls-asset-pipeline/skyrim-source/mod-sources/tamriel-worldspaces-118678/extracted/" \
      "Argonia Worldspace/argonia-heightfield/"
_ST = "snapshot/v1/repo-studio-public.tar"
_SP = "deploy-main/apps/world-studio/public/province/"

# local name -> (vault part, tar entry, sha256 of the file's bytes as first fetched)
FILES: dict[str, tuple[str, str, str]] = {
    "landcover-i16.npy": (_TW, _HF + "province-refined/landcover-i16.npy",
                          "10f20595069b49e96d8f0da59afcad942a044bb07fe71583078fc16da0c17b17"),
    "refined-height-f32.npy": (_TW, _HF + "province-refined/refined-height-f32.npy",
                               "b253c5ff89ddb6964227b5db1f7c9d92981c69c234e98501dbb43c7adeba71e8"),
    "apron-source-near.npy": (_TW, _HF + "province-refined/apron-source-near.npy",
                              "c85efe550401b0de2db0f440d0dc8579ea04e3fb2b24822ece6c45df3b9ad77a"),
    "apron-source-far.npz": (_TW, _HF + "province-refined/apron-source-far.npz",
                             "661eef14982ec1fb4afcc3c8d5e571fe586b0e09b1983e26ad13984d1a4d6b75"),
    "apron-source.json": (_TW, _HF + "province-refined/apron-source.json",
                          "02f904f6a841b9f76bb99d2195af572fa1fe70015156d670c3c09d0c9511df91"),
    "terrain-patches-applied.json": (_TW, _HF + "province-refined/terrain-patches-applied.json",
                                     "9b200feaab74bd3b265ff01fe5188addb1bbc84cf9647a1e3a7ff10e1b63cc79"),
    "route-grade-applied.json": (_TW, _HF + "province-refined/route-grade-applied.json",
                                 "f4c488ee57b3806ebb3c849d20ced0eb6f00c09766a8dbf1b7796ce52b5e6a30"),
    "settlement-pad-grades.json": (_TW, _HF + "province-refined/settlement-pad-grades.json",
                                   "018b0863f6c038d9d1862ade378665ef79255c93c96db458cf71169e129abee6"),
    "meta.json": (_TW, _HF + "meta.json", "51164558d7186ab0730f9465322201343950cc762d1e88a9565ce195d2ee91da"),
    "ground-tint.png": (_ST, _SP + "refined/ground-tint.png",
                        "637e903c8ea3e8428ff765a0e39a02926cf6dcb3cb76eb6ecb5f748585811259"),
}


def data_dir() -> Path:
    return Path(os.environ.get("ARGONIA_DATA", str(Path.home() / ".argonia" / "data"))) / "terrain"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def status(d: Path) -> dict[str, str]:
    return {n: "missing" if not (d / n).exists() else ("ok" if sha256(d / n) == s else "hash mismatch")
            for n, (_, _, s) in FILES.items()}


def fetch(names: set[str], d: Path, pin: bool) -> int:
    import fetch_vault as fv  # the 0.1 §e client and credentials

    env = fv.secrets()
    if not all(env.get(k) for k in ("ES_SNAPSHOT_ACCESS_KEY_ID", "ES_SNAPSHOT_SECRET_ACCESS_KEY", "ES_SNAPSHOT_ENDPOINT")):
        print("no R2 credentials in ~/.argonia/secrets.env (ES_SNAPSHOT_*): nothing fetched")
        return 2
    s3 = fv.client(env)
    d.mkdir(parents=True, exist_ok=True)
    bad = 0
    for part in sorted({FILES[n][0] for n in names}):
        want = {FILES[n][1]: n for n in names if FILES[n][0] == part}
        stream = s3.get_object(Bucket=fv.BUCKET, Key=part)["Body"]
        with tarfile.open(fileobj=io.BufferedReader(stream, buffer_size=1 << 22), mode="r|") as tar:
            for m in tar:  # streamed: the tar is never held, only the wanted entries are written
                name = want.pop(m.name.lstrip("./"), None) or want.pop(m.name, None)
                if not name:
                    continue
                target = d / name
                with tar.extractfile(m) as src, target.open("wb") as dst:
                    for chunk in iter(lambda: src.read(1 << 20), b""):
                        dst.write(chunk)
                got = sha256(target)
                if pin:
                    print(f'pin {name} {got}')
                elif got != FILES[name][2]:
                    target.unlink()
                    print(f"REFUSED {name}: sha256 {got} is not the pinned one")
                    bad += 1
                    continue
                print(f"ok {name} ({target.stat().st_size:,} bytes)")
                if not want:
                    break
        for entry, name in want.items():
            print(f"NOT IN VAULT {name} ({entry})")
            bad += 1
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--pin", action="store_true")
    a = ap.parse_args(argv)
    d = data_dir()
    st = status(d)
    for n, s in st.items():
        print(f"{s:14} {n}")
    todo = {n for n, s in st.items() if s != "ok"}
    if a.check or not todo:
        return 1 if todo else 0
    return fetch(todo, d, a.pin)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
