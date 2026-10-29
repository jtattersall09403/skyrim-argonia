"""The old project's ground-control raster (`ground-control.png`, the world studio's per-sample control image: red
the land-cover class, the other channels the region and wetness fields), fetched from the R2 vault into
`$ARGONIA_DATA/regions/`. Derived files of the old chain, never committed (0003); pinned by sha256 once fetched.

    python3 -m tools.argonia_world.regions.vault            locate and fetch what is missing
    python3 -m tools.argonia_world.regions.vault --list     print where each name sits in the vault
"""
from __future__ import annotations

import argparse
import io
import os
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

# local name -> the tail of its tar entry path (the vault's sidecars are searched for it)
WANT = {
    "ground-control.png": "public/province/refined/ground-control.png",
    "major-routes-report.json": "world-generation/output/major-routes-report.json",
    "route-grading-stretches.json": "world-generation/output/route-grading-stretches.json",
    **{f"road-{r}.json": f"world-generation/output/route-structures/road-{r}.json"
       for r in ("gideon-blackwood-road", "gideon-soulrest", "gideon-stormhold", "stormhold-thorn", "thorn-tear-road")},
}


def data_dir() -> Path:
    return Path(os.environ.get("ARGONIA_DATA", str(Path.home() / ".argonia" / "data"))) / "regions"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    import fetch_vault as fv

    s3 = fv.client(fv.secrets())
    found = fv.locate(s3, set(WANT))
    for part, entries in found.items():
        for e in entries:
            print(f"{part}\t{e}")
    if a.list:
        return 0
    d = data_dir()
    d.mkdir(parents=True, exist_ok=True)
    todo = {n for n in WANT if not (d / n).exists()}
    for part, entries in found.items():
        mine = {e: e.rsplit("/", 1)[-1] for e in entries
                if e.rsplit("/", 1)[-1] in todo and e.endswith(WANT[e.rsplit("/", 1)[-1]])}
        if not mine:
            continue
        stream = s3.get_object(Bucket=fv.BUCKET, Key=part)["Body"]
        with tarfile.open(fileobj=io.BufferedReader(stream, buffer_size=1 << 22), mode="r|") as tar:
            for m in tar:
                name = mine.get(m.name.lstrip("./")) or mine.get(m.name)
                if not name or name not in todo:
                    continue
                with tar.extractfile(m) as src, (d / name).open("wb") as dst:
                    for chunk in iter(lambda: src.read(1 << 20), b""):
                        dst.write(chunk)
                print(f"ok {name} ({(d / name).stat().st_size:,} bytes)")
                todo.discard(name)
                if not todo & set(mine.values()):
                    break
    for n in sorted(todo):
        print(f"NOT FETCHED {n}")
    return 1 if todo else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
