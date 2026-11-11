"""The standing terrain build copied to its folder in the bucket.

    python3 -m tools.newworld.terrain_upload     # out/newworld/terrain/ and water_bodies.json; NW_UPLOAD=0 skips it

The folder is named for the build's id (`build.json`): s3://argonia-private-050977237313/nw/terrain/<id>/. The
rebuild runs this in its `upload` stage, after the read-back; a terrain build run by hand ends with it.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

from tools.newworld import frame as f

BUCKET = "s3://argonia-private-050977237313/nw/terrain"


def upload() -> str:
    out = f.OUT / "terrain"
    to = f"{BUCKET}/{json.loads((out / 'build.json').read_text())['id']}/"
    subprocess.run(["aws", "s3", "cp", "--recursive", "--quiet", str(out), to], check=True)
    subprocess.run(["aws", "s3", "cp", "--quiet", str(f.OUT / "water_bodies.json"), to], check=True)
    return to


def main() -> int:
    if os.environ.get("NW_UPLOAD", "1") != "1":
        print("upload skipped (NW_UPLOAD=0)")
        return 0
    print("uploaded", upload())
    return 0


if __name__ == "__main__":
    sys.exit(main())
