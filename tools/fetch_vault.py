#!/usr/bin/env python3
"""Fetch the frozen terrain arrays from the old project's R2 vault (0.1 §e, decision 0009 §5).

The vault is the old project's snapshot bucket (`elder-souls-vault`, prefix `snapshot/v1/`): each part is one
uncompressed tar of paths relative to the old dev root, with a `.files` sidecar listing its entries. This
script reads `world/sources/terrain/freeze.json` for the file names and hashes it needs, finds which part
holds each (from the sidecars), streams only those parts, extracts only those entries into `$ARGONIA_DATA`
(default `~/.argonia/data`), and refuses any file whose sha256 differs from the freeze record.

Credentials come from `~/.argonia/secrets.env` (never printed): ES_SNAPSHOT_ACCESS_KEY_ID,
ES_SNAPSHOT_SECRET_ACCESS_KEY, ES_SNAPSHOT_ENDPOINT (the R2 endpoint without a bucket suffix). With no
credentials it exits 2 and says which owner step provides them.

  python3 tools/fetch_vault.py            fetch what is missing or wrong
  python3 tools/fetch_vault.py --check    only report what is present and verified
"""
import argparse
import hashlib
import io
import json
import os
import sys
import tarfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FREEZE = REPO / "world" / "sources" / "terrain" / "freeze.json"
BUCKET, PREFIX = "elder-souls-vault", "snapshot/v1/"
# the parts that can hold world-generation output, searched in this order (the sidecars decide)
CANDIDATE_PARTS = ("repo-wg-products", "vault-output", "vault-extra")


def secrets() -> dict:
    env = {}
    path = Path.home() / ".argonia" / "secrets.env"
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip().removeprefix("export ")] = v.strip().strip('"').strip("'")
    env.update({k: v for k, v in os.environ.items() if k.startswith("ES_SNAPSHOT_")})
    return env


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def wanted() -> dict[str, str]:
    return {name: row["sha256"] for name, row in json.loads(FREEZE.read_text())["frozen"].items()}


def status(data: Path, want: dict[str, str]) -> dict[str, str]:
    out = {}
    for name, sha in want.items():
        p = data / name
        out[name] = "missing" if not p.exists() else ("ok" if sha256_of(p) == sha else "hash mismatch")
    return out


def client(env):
    import boto3  # in the toolchain venv

    return boto3.client("s3", endpoint_url=env["ES_SNAPSHOT_ENDPOINT"],
                        aws_access_key_id=env["ES_SNAPSHOT_ACCESS_KEY_ID"],
                        aws_secret_access_key=env["ES_SNAPSHOT_SECRET_ACCESS_KEY"], region_name="auto")


def locate(s3, names: set[str]) -> dict[str, list[str]]:
    """part id -> the tar entry names (full paths inside the tar) that end in a wanted file name."""
    found: dict[str, list[str]] = {}
    for part in CANDIDATE_PARTS:
        try:
            body = s3.get_object(Bucket=BUCKET, Key=f"{PREFIX}{part}.files")["Body"].read().decode()
        except Exception:  # a part this snapshot does not have
            continue
        hits = [e for e in body.splitlines() if e.rsplit("/", 1)[-1] in names]
        if hits:
            found[part] = hits
            names -= {e.rsplit("/", 1)[-1] for e in hits}
        if not names:
            break
    return found


def fetch(s3, part: str, entries: list[str], data: Path, want: dict[str, str]) -> list[str]:
    """Stream one part's tar and extract only the listed entries; return the names verified."""
    stream = s3.get_object(Bucket=BUCKET, Key=f"{PREFIX}{part}.tar")["Body"]
    done = []
    with tarfile.open(fileobj=io.BufferedReader(stream, buffer_size=1 << 22), mode="r|") as tar:
        for member in tar:
            if member.name.lstrip("./") not in entries and member.name not in entries:
                continue
            name = member.name.rsplit("/", 1)[-1]
            target = data / name
            with tar.extractfile(member) as src, target.open("wb") as dst:
                for chunk in iter(lambda: src.read(1 << 20), b""):
                    dst.write(chunk)
            if sha256_of(target) != want[name]:
                target.unlink()
                print(f"REFUSED {name}: sha256 differs from freeze.json (the vault moved on?)")
            else:
                done.append(name)
                print(f"ok {name} ({target.stat().st_size:,} bytes)")
            if len(done) == len(entries):
                break
    return done


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--data", default=os.environ.get("ARGONIA_DATA", str(Path.home() / ".argonia" / "data")))
    a = ap.parse_args()
    data = Path(a.data)
    data.mkdir(parents=True, exist_ok=True)
    want = wanted()
    st = status(data, want)
    for n, s in st.items():
        print(f"{s:14} {n}")
    todo = {n for n, s in st.items() if s != "ok"}
    if a.check or not todo:
        return 0 if not todo else 1
    env = secrets()
    if not all(env.get(k) for k in ("ES_SNAPSHOT_ACCESS_KEY_ID", "ES_SNAPSHOT_SECRET_ACCESS_KEY", "ES_SNAPSHOT_ENDPOINT")):
        print("no R2 credentials in ~/.argonia/secrets.env (ES_SNAPSHOT_*): owner step, 0.1 §e; nothing fetched")
        return 2
    s3 = client(env)
    where = locate(s3, set(todo))
    missing = todo - {e.rsplit("/", 1)[-1] for es in where.values() for e in es}
    for n in sorted(missing):
        print(f"NOT IN VAULT {n}: no snapshot part lists it (owner call: re-derive or find the old disk)")
    got = []
    for part, entries in where.items():
        print(f"fetching {len(entries)} file(s) from {part}.tar")
        got += fetch(s3, part, entries, data, want)
    left = todo - set(got)
    return 0 if not left else 1


if __name__ == "__main__":
    sys.exit(main())
