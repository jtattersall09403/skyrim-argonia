"""Search Nexus Skyrim SE mods by name (GraphQL v2 wildcard, most endorsed first); translations dropped.

    python3 tooling/nexus_search.py kagouti "sea lion" leech ...
    python3 tooling/nexus_search.py --mod 27521 ...     # one mod's record: name, author, files, permission lines

The method this serves: docs/research/creature-mod-search.md. Key from ~/.argonia/secrets.env (NEXUS_API_KEY)."""
import json
import re
import sys
import urllib.request
from pathlib import Path

GAME = "skyrimspecialedition"
DROP = ("traduc", "espa", "german", "deutsch", "french", "russian", "translation", "tradu", "patch")


def key() -> str:
    for line in (Path.home() / ".argonia/secrets.env").read_text().splitlines():
        m = re.match(r"\s*(?:export\s+)?NEXUS_API_KEY=(.+)", line)
        if m:
            return m.group(1).strip().strip('"')
    raise SystemExit("NEXUS_API_KEY missing")


def call(url: str, body: dict | None = None):
    h = {"apikey": key(), "User-Agent": "argonia-stack/0.2", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=h)
    return json.load(urllib.request.urlopen(req, timeout=60))


def search(term: str) -> list[dict]:
    q = ("query($f:ModsFilter){mods(filter:$f,count:40,sort:[{endorsements:{direction:DESC}}])"
         "{nodes{modId name author endorsements}}}")
    f = {"gameDomainName": [{"value": GAME}], "name": [{"value": term, "op": "WILDCARD"}]}
    nodes = call("https://api.nexusmods.com/v2/graphql", {"query": q, "variables": {"f": f}})["data"]["mods"]["nodes"]
    return [n for n in nodes if not any(x in n["name"].lower() for x in DROP)]


def mod(mid: int) -> None:
    base = f"https://api.nexusmods.com/v1/games/{GAME}/mods/{mid}"
    d = call(f"{base}.json")
    print(f"## {mid} {d['name']} | {d['author']} {d['version']} | {d['summary'][:160]}")
    text = re.sub(r"<[^>]+>|\[[^\]]*\]", " ", d.get("description") or "")
    for s in re.findall(r"(?i)[^.\n]{0,100}(?:permission|requir|resource|credit|allow)[^.\n]{0,120}", text)[:6]:
        print("  ", s.strip())
    for f in call(f"{base}/files.json")["files"]:
        if f["category_name"] in ("MAIN", "OPTIONAL"):
            print(f"  file {f['file_id']} {f['category_name']} {f['name']} {f['size_kb']} KB")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--mod"]:
        for a in args[1:]:
            mod(int(a))
    else:
        for t in args:
            print(f"=== {t}")
            for n in search(t):
                print(f"  {n['modId']} {n['name'][:70]} | {n['author']} {n['endorsements']}")
