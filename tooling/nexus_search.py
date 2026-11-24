"""Search Nexus Skyrim mods, Special Edition and the 2011 game both, by name and by description text.

    python3 tooling/nexus_search.py kagouti "sea lion" leech ...   # each term: name matches, then description-only matches
    python3 tooling/nexus_search.py --mod 27521 skyrim:19268 ...   # one mod's record: name, author, files, permission lines

A term is matched against mod names (wildcard) and against descriptions (whole words), in both game domains, most
endorsed first; translations dropped. A mod of the 2011 game (`skyrim:` ids) needs its meshes converted before
Special Edition can use them. The method this serves: docs/research/creature-mod-search.md. Key from
~/.argonia/secrets.env (NEXUS_API_KEY)."""
import json
import re
import sys
import urllib.request
from pathlib import Path

GAMES = ("skyrimspecialedition", "skyrim")
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


def search(term: str, count: int = 40) -> list[dict]:
    """Mods of both games whose name holds the term, then those whose description alone does."""
    q = ("query($f:ModsFilter,$n:Int){mods(filter:$f,count:$n,sort:[{endorsements:{direction:DESC}}])"
         "{nodes{modId name author endorsements summary game{domainName} modCategory{name}}}}")
    out, seen = [], set()
    for field, op in (("name", "WILDCARD"), ("description", "MATCHES")):
        for game in GAMES:
            f = {"gameDomainName": [{"value": game}], field: [{"value": term, "op": op}]}
            data = call("https://api.nexusmods.com/v2/graphql", {"query": q, "variables": {"f": f, "n": count}})
            for n in data["data"]["mods"]["nodes"]:
                k = (game, n["modId"])
                if k not in seen and not any(x in n["name"].lower() for x in DROP):
                    seen.add(k)
                    out.append({**n, "game": game, "by": field, "category": (n.get("modCategory") or {}).get("name") or ""})
    return out


def mod(ref: str) -> None:
    game, _, mid = ref.rpartition(":")
    game = game or GAMES[0]
    base = f"https://api.nexusmods.com/v1/games/{game}/mods/{mid}"
    d = call(f"{base}.json")
    print(f"## {game}:{mid} {d['name']} | {d['author']} {d['version']} | {d['summary'][:160]}")
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
            mod(a)
    else:
        for t in args:
            print(f"=== {t}")
            for n in search(t):
                tag = "" if n["game"] == GAMES[0] else "skyrim:"
                print(f"  {tag}{n['modId']} {n['name'][:60]} | {n['author']} {n['endorsements']} | {n['category'][:24]}"
                      f" | {n['by']} | {(n['summary'] or '')[:90]}")
