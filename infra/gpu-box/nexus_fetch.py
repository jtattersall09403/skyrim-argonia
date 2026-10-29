#!/usr/bin/env python3
"""Download the files named in a mod list: Nexus files through the API (Premium key in ~/.argonia/secrets.env),
and GitHub release assets for entries with github/tag/asset.

  nexus_fetch.py infra/gpu-box/combat-test-mods.json [--out ~/.argonia/mods]

Files land outside the repo and are never committed (decision 0003). Already-downloaded files are skipped.
"""
import argparse
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.nexusmods.com/v1"


def key():
    for line in (pathlib.Path.home() / ".argonia" / "secrets.env").read_text().splitlines():
        m = re.match(r"\s*(?:export\s+)?NEXUS_API_KEY=(.+)", line)
        if m:
            return m.group(1).strip().strip('"')
    raise SystemExit("NEXUS_API_KEY missing from ~/.argonia/secrets.env")


def get(url, apikey):
    req = urllib.request.Request(url, headers={"apikey": apikey, "User-Agent": "argonia-nexus-fetch/0.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("list")
    p.add_argument("--out", default=str(pathlib.Path.home() / ".argonia" / "mods"))
    a = p.parse_args()
    spec = json.loads(pathlib.Path(a.list).read_text())
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    apikey, game = key(), spec["game"]
    failed = []
    for m in spec["mods"]:
        if "github" in m:  # a GitHub release asset (mods not on Nexus)
            tag = urllib.parse.quote(m["tag"], safe="")
            dest = out / f"gh-{m['github'].replace('/', '_')}-{m['asset']}"
            if dest.exists() and dest.stat().st_size > 0:
                print(f"have  {m['name']}: {dest.name}")
                continue
            url = f"https://github.com/{m['github']}/releases/download/{tag}/{urllib.parse.quote(m['asset'])}"
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "argonia-nexus-fetch/0.0"}), timeout=300) as r, open(dest, "wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            print(f"got   {m['name']}: {dest.name} ({dest.stat().st_size // 1024} KiB)")
            continue
        have = [f for f in out.glob(f"{m['mod']}-{m['file']}-*") if f.stat().st_size > 0]
        if have:  # already downloaded: no API call (a file can later vanish from Nexus)
            print(f"have  {m['name']}: {have[0].name}")
            continue
        try:
            info = get(f"{API}/games/{game}/mods/{m['mod']}/files/{m['file']}.json", apikey)
        except urllib.error.HTTPError as e:
            print(f"FAIL  {m['name']} ({m['mod']}/{m['file']}): HTTP {e.code}")
            failed.append(m["name"])
            continue
        dest = out / f"{m['mod']}-{m['file']}-{info['file_name']}"
        if dest.exists() and dest.stat().st_size > 0:
            print(f"have  {m['name']}: {dest.name}")
            continue
        link = get(f"{API}/games/{game}/mods/{m['mod']}/files/{m['file']}/download_link.json", apikey)[0]["URI"]
        link = urllib.parse.quote(link, safe=":/?&=%~+")
        req = urllib.request.Request(link, headers={"User-Agent": "argonia-nexus-fetch/0.0"})
        with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
        print(f"got   {m['name']}: {dest.name} ({dest.stat().st_size // 1024} KiB)")

    if failed:
        raise SystemExit(f"{len(failed)} failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
