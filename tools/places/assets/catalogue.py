"""The catalogue: every base form a place could use, across every source we hold, in out/places/catalogue/.

Sources, in load order (a later plugin's version of a record wins, its key stays the origin's):
the game's masters (Skyrim.esm, Update.esm, the three DLCs, the Creation Club files in Data), USSEP, Tropical Skyrim
(whose overrides of vanilla bases win), BM&V, then every new-world source and asset mod in mods/dependencies.json
(group newworld) in that file's order. A plugin is found in the game's Data, in its mod's folder, or else is
extracted from the mod's archive in ~/.argonia/mods into out/places/catalogue/plugins/<mod>/.

The reader is tools/places/assets/Catalogue (C#, Mutagen) writing bases.raw.jsonl and ltex.jsonl; this module adds
per base: `nordic` (decision 0006: Nordic architecture and Skyrim's cold-climate flora by the words of its editor id
and model path), `kind` (the studio's kinds), `source` (the mod id), `has_model` (the model resolves in the NewWorld
profile, so the converter can show it), and `text`, the plain-English descriptor lane V embeds for search.

bases.jsonl rows: {key, edid, type, name, model, bounds, plugin, keywords, value?, ench?, nordic, kind, source, has_model,
text}; `value` and `ench` (the enchantment's key or null) on item forms, so an item's stocking tier is known before
`stockdb items` measures it."""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from tools.places.assets import cache
from tools.places.assets.resolve import ASSET_MODS, DATA, STACK, default, norm

ROOT = Path(__file__).resolve().parents[3]
DOTNET = Path.home() / ".dotnet"
BIN = Path.home() / ".argonia" / "bin" / "places-catalogue"
ARCHIVES = Path.home() / ".argonia" / "mods"
MASTERS = ["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm"]
TYPE_KIND = {"STAT": "static", "MSTT": "static", "DOOR": "door", "CONT": "container", "FURN": "furniture",
             "LIGH": "light", "ACTI": "activator", "TACT": "activator", "TREE": "tree", "FLOR": "plant",
             "GRAS": "groundcover", "IDLM": "marker"}
TYPE_WORDS = {"STAT": "static object", "MSTT": "moving static object", "DOOR": "door", "CONT": "container",
              "FURN": "furniture", "LIGH": "light", "ACTI": "activator", "TACT": "talking activator", "TREE": "tree",
              "FLOR": "harvestable plant", "GRAS": "grass ground cover", "MISC": "clutter item", "BOOK": "book",
              "INGR": "ingredient", "ALCH": "potion or food", "KEYM": "key", "SCRL": "scroll", "SLGM": "soul gem",
              "WEAP": "weapon", "AMMO": "ammunition", "APPA": "alchemy apparatus", "IDLM": "idle marker",
              "ARMO": "armour"}
# Decision 0006: Nordic pieces stay visible in the wide search but are marked. Hold names of Skyrim's
# architecture sets and cold-climate flora (the flora study's snow/pine/aspen/reach/tundra/volcanic rule).
NORDIC = re.compile(r"(nord(?!ic\s*ruin)|nordic|whiterun|windhelm|solitude|markarth|riften|dawnstar|winterhold|falkreath|"
                    r"morthal|dragonsreach|skyhaven|farmhouse|stormcloak|draugr|snow|pine|aspen|reach|tundra|"
                    r"volcanic|wr(house|wall|gate|tower)|wh(house|wall)|sol(house|wall)|rift(house|wall)|"
                    r"mrk|winterhold|ice(?=[^a-z]|$)|frost|skyrim)")
# words that only look cold: taken out before the search (ice ends many an English word; pine sits in spine)
NORDIC_EXCEPT = re.compile(r"(icecream|spine|pineapple|porcupine|cutpine|apprentice|novice|chalice|lattice|device|"
                           r"office|justice|service|spice|juice|police|notice|practice|sacrifice|voice|choice|malice|"
                           r"orifice|edifice|precipice|cornice|crevice|poultice|advice|pumice|slice|price|twice)", re.I)
# an ice variant named in the middle of an editor id, which the lower-case search cannot see: ..01iceLt, ..IceBlend
ICE = re.compile(r"(?:(?<![A-Za-z])ice|(?<![A-Z])Ice)(?![a-z])")


def words(s: str | None) -> list[str]:
    if not s:
        return []
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    return [w for w in re.split(r"[^a-z]+", s.lower()) if len(w) > 1]


def is_nordic(b: dict) -> bool:
    text = NORDIC_EXCEPT.sub("", f"{b.get('edid') or ''} {b.get('model') or ''}")
    return bool(NORDIC.search(text.lower()) or ICE.search(text))


def kind(b: dict) -> str:
    t = b["type"]
    if t in TYPE_KIND:
        k = TYPE_KIND[t]
        if k == "static":
            m = (b.get("model") or "") + " " + (b.get("edid") or "").lower()
            if re.search(r"rock|boulder|cliff|stone(?!wall)", m):
                return "rock"
            if re.search(r"tree|stump|log\b|trunk", m):
                return "tree"
            if re.search(r"plant|fern|shrub|bush|flower|reed|moss|grass|vine|mushroom|shroom|lily", m):
                return "plant"
            if re.search(r"architecture|house|hut|tower|wall|bridge|dock|pier|walkway|building|shack|stilt|ruin", m):
                return "building"
            if "clutter" in m:
                return "clutter"
        return k
    return "clutter"


def size_words(bounds) -> str:
    if not bounds:
        return ""
    d = [abs(bounds[1][i] - bounds[0][i]) / 70.0 for i in range(3)]  # 70 units a metre (roughly)
    big = max(d)
    tag = "tiny" if big < 0.3 else "small" if big < 1.5 else "medium" if big < 5 else "large" if big < 20 else "huge"
    return f"{tag}, about {d[0]:.1f} by {d[1]:.1f} m and {d[2]:.1f} m tall"


def descriptor(b: dict, source_name: str) -> str:
    model = (b.get("model") or "").rsplit(".", 1)[0]
    parts = [b.get("name") or "", " ".join(words(b.get("edid"))), TYPE_WORDS.get(b["type"], b["type"]),
             "model " + " ".join(words(model.replace("/", " "))), f"from {source_name}", size_words(b.get("bounds"))]
    if b.get("nordic"):
        parts.append("Nordic (Skyrim) style")
    return ". ".join(p for p in parts if p)


def deps() -> dict:
    return json.loads((ROOT / "mods" / "dependencies.json").read_text())


def plugin_list(out: Path) -> list[tuple[str, Path, str, str]]:
    """[(file, path, mod id, mod name)] in load order; extracts a plugin from its archive when not on disk."""
    d = deps()
    rows = {r["id"]: r for r in d["mods"]}
    want: list[tuple[str, str]] = [(f, "skyrim") for f in MASTERS]
    want += [(p.name, "skyrim") for p in sorted(DATA.glob("cc*.es[ml]"))] + [("_ResourcePack.esl", "skyrim")]
    want += [(f, "ussep") for f in rows["ussep"]["plugins"]] + [(f, "tropical-skyrim-sse") for f in rows["tropical-skyrim-sse"]["plugins"]]
    want += [(f, "bmv") for f in rows["bmv"]["plugins"]]
    want += [(f, r["id"]) for r in d["mods"] if r.get("group") == "newworld" and r["id"] != "tropical-skyrim-sse" for f in r.get("plugins") or []]
    found, seen = [], set()
    for f, mod in want:
        if f.lower() in seen:
            continue
        seen.add(f.lower())
        p = _locate(f, mod, rows.get(mod), out)
        name = rows[mod]["name"] if mod in rows else "Skyrim" if mod == "skyrim" else mod
        if p:
            found.append((f, p, mod, name))
        else:
            print(f"catalogue: {f} ({mod}) not held: skipped")
    return found


def _ci(d: Path, name: str) -> Path | None:
    if not d.is_dir():
        return None
    for n in os.listdir(d):
        if n.lower() == name.lower():
            return d / n
    return None


def _locate(f: str, mod: str, row: dict | None, out: Path) -> Path | None:
    for d in (DATA, STACK / "MO2" / "mods" / mod, ASSET_MODS / mod, out / "plugins" / mod):
        p = _ci(d, f)
        if p and p.is_file() and p.stat().st_size:
            return p
    if not row or not row.get("archive"):
        return None
    arcs = [a for a in ARCHIVES.glob("*") if a.name.endswith(row["archive"])]
    if not arcs:
        return None
    dest = out / "plugins" / mod
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        if arcs[0].suffix.lower() == ".rar":  # 7z here cannot unpack RAR5
            subprocess.run(["unrar", "e", "-o+", "-r", str(arcs[0]), "*.esp", "*.esm", "*.esl", tmp + "/"], capture_output=True, check=False)
        else:
            subprocess.run(["7z", "e", "-y", "-r", f"-o{tmp}", str(arcs[0]), "*.esp", "*.esm", "*.esl"], capture_output=True, check=False)
        for p in Path(tmp).iterdir():
            if p.is_file() and p.stat().st_size and not (dest / p.name).exists():
                os.replace(p, dest / p.name)
    p = _ci(dest, f)
    return p if p and p.is_file() else None


def strings(out: Path, plugins: list[str]) -> Path:
    """The English string files of the localized masters, unpacked from the game's archives (names for the rows),
    named as Mutagen looks for them on a case-sensitive disk: <Plugin stem>_English.STRINGS."""
    from tools.places.assets.resolve import _decompress
    d = out / "strings"
    d.mkdir(parents=True, exist_ok=True)
    stems = {Path(p).stem.lower(): Path(p).stem for p in plugins}
    for _, a in default().archives():
        for k in a.files:
            m = re.match(r"strings/(.+)_english\.(strings|dlstrings|ilstrings)$", k)
            if m and m.group(1) in stems:
                f = d / f"{stems[m.group(1)]}_English.{m.group(2).upper()}"
                if not f.exists():
                    f.write_bytes(_decompress(a, k))
    return d


def build_tool() -> None:
    env = dict(os.environ, DOTNET_ROOT=str(DOTNET), DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1",
               PATH=f"{DOTNET}:{os.environ['PATH']}")
    subprocess.run(["dotnet", "build", "-c", "Release", "-o", str(BIN), str(Path(__file__).parent / "Catalogue"), "-v", "q", "-nologo"],
                   check=True, env=env, capture_output=True)


def run(out: Path | None = None) -> dict:
    out = out or cache.root().parent / "catalogue"
    out.mkdir(parents=True, exist_ok=True)
    build_tool()
    plugins = plugin_list(out)
    env = dict(os.environ, DOTNET_ROOT=str(DOTNET), DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1",
               ARGONIA_STRINGS=str(strings(out, [f for f, *_ in plugins])))
    subprocess.run(["nice", str(DOTNET / "dotnet"), str(BIN / "Catalogue.dll"), str(out)] + [str(p) for _, p, _, _ in plugins],
                   check=True, env=env)
    src = {f.lower(): (mod, name) for f, _, mod, name in plugins}
    r = default()
    by_source, by_type, n = Counter(), Counter(), 0
    tmp = out / "bases.jsonl.tmp"
    with (out / "bases.raw.jsonl").open(encoding="utf-8") as fin, tmp.open("w", encoding="utf-8") as fo:
        for line in fin:
            b = json.loads(line)
            origin = b["key"].rsplit(":", 1)[0].lower()
            mod, name = src.get(origin, src.get(b["plugin"].lower(), ("unknown", "unknown")))
            b["nordic"] = is_nordic(b)
            b["kind"] = kind(b)
            b["source"] = mod
            k = norm(b["model"], "meshes")
            b["has_model"] = bool(r.loose_file(k)) or any(k.replace("\\", "/") in a.files for _, a in r.archives())
            b["text"] = descriptor(b, name)
            fo.write(json.dumps(b, ensure_ascii=False) + "\n")
            by_source[mod] += 1
            by_type[b["type"]] += 1
            n += 1
    os.replace(tmp, out / "bases.jsonl")
    (out / "bases.raw.jsonl").unlink()
    summary = {"bases": n, "plugins": [f for f, *_ in plugins], "by_source": dict(by_source.most_common()),
               "by_type": dict(by_type.most_common())}
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    return summary
