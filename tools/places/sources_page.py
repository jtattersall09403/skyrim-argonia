"""python -m tools.places sources-page

The owner's sense check of the source-place match, one self-contained page: out/newworld/sources/index.html. Reads
the committed match (newworld/sources/source_match/), the places (newworld/story/data/db/place.jsonl, the research's
population from git HEAD's version when the working copy already holds the new one) and the mining status.
"""
from __future__ import annotations

import html
import json
import statistics
from collections import Counter, defaultdict

from tools.places.bundle import REPO
from tools.places.sources_match import FAMILY, MATCH, RANKED
from tools.places.sources_mine import GROUPS, OUT as MINED

OUT = REPO / "out" / "newworld" / "sources" / "index.html"
DB = REPO / "newworld" / "story" / "data" / "db"


def e(s) -> str:
    return html.escape(str(s if s is not None else ""))


def jl(p):
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def fam(k: str) -> str:
    if k.startswith("ruin") or k.endswith("-ruin"):
        return "ruin"
    return FAMILY.get(k, k)


CSS = """
:root{--bg:#f7f5f0;--card:#fff;--ink:#1d2321;--muted:#5d6763;--line:#dcd8cf;--accent:#2f6b5a;--warn:#a2512b;--bar:#6f9f8f;--bar2:#c7a15a}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#141816;--card:#1c2220;--ink:#e6ebe8;--muted:#9aa6a1;--line:#2e3633;--accent:#7cc4ad;--warn:#e39a74;--bar:#4f8d7a;--bar2:#b08c47}}
:root[data-theme="dark"]{--bg:#141816;--card:#1c2220;--ink:#e6ebe8;--muted:#9aa6a1;--line:#2e3633;--accent:#7cc4ad;--warn:#e39a74;--bar:#4f8d7a;--bar2:#b08c47}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:980px;margin:0 auto;padding:16px}h1{font-size:1.5rem;margin:.2em 0}h2{font-size:1.15rem;margin:1.6em 0 .5em;border-bottom:1px solid var(--line);padding-bottom:.2em}
p.lead{color:var(--muted)}.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px}.tile b{display:block;font-size:1.35rem}.tile span{color:var(--muted);font-size:.85rem}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}table{border-collapse:collapse;width:100%;font-size:.88rem;background:var(--card)}
th,td{border-bottom:1px solid var(--line);padding:5px 6px;text-align:left;vertical-align:top}th{color:var(--muted);font-weight:600}
td.n{text-align:right;font-variant-numeric:tabular-nums}.bar{display:inline-block;height:9px;background:var(--bar);border-radius:2px;vertical-align:middle}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin:8px 0}.card h3{margin:0 0 4px;font-size:1rem}
.muted{color:var(--muted)}.warn{color:var(--warn)}.k{font-family:ui-monospace,Menlo,monospace;font-size:.8rem;color:var(--muted);word-break:break-all}
ol.alts{margin:4px 0 0;padding-left:20px}.chip{display:inline-block;border:1px solid var(--line);border-radius:10px;padding:0 6px;font-size:.78rem;margin:1px}
"""


def main(argv: list[str]) -> int:
    places = {p["id"]: p for p in jl(DB / "place.jsonl")}
    match = jl(MATCH / "place_source.jsonl")
    src = {s["id"]: s for s in jl(MATCH / "source_place.jsonl")}
    ranked = json.loads(RANKED.read_text())
    status = json.loads((MINED / "status.json").read_text())
    by = defaultdict(dict)
    for r in match:
        by[r["place_id"]][r["rank"]] = r
    a0 = [by[p][0] for p in places]
    imp = {p: places[p]["importance"] for p in places}
    out = []
    w = out.append

    w(f"<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
      f"<title>Source Place Matches</title><style>{CSS}</style></head><body><main>")
    w("<p class=lead><strong>Approved by the owner on 2026-11-12; population now matches each source's residents.</strong></p>")
    w("<h1>Source places for our 258 places</h1><p class=lead>Each of our places has been given one source place out of "
      "a game or mod plugin we hold: its layout, buildings and interiors are what the place will be drafted from. "
      "No two places share a source. Below are the numbers, the major places one by one, and the matches most worth a "
      "second look, so that not every match needs checking.</p>")
    scores = [r["score"] for r in a0]
    mism = [r for r in a0 if fam(places[r["place_id"]]["place_kind_id"]) != fam(src[r["source_place_id"]]["kind"])]
    pb = sum((r.get("population_before") or 0) for r in a0)
    pa = sum((r.get("population_after") or 0) for r in a0)
    mined_n = sum(s.get("rows", 0) for s in status.values() if s.get("mined"))
    tiles = [(len(places), "our places, each with a source"), (ranked["candidates"], f"usable candidates (of {mined_n} mined)"),
             (sum(1 for s in status.values() if s.get("mined")), "plugin groups mined"),
             (f"{statistics.mean(scores):.2f}", "mean similarity (0-1) of the allocated source"),
             (f"{statistics.mean(r['score'] for r in a0 if imp[r['place_id']] >= 4):.2f}", "mean for the 21 major places"),
             (len(mism), "places whose source is another family of place"),
             (f"{pb} → {pa}", "total population, before → after")]
    w("<div class=tiles>" + "".join(f"<div class=tile><b>{e(v)}</b><span>{e(t)}</span></div>" for v, t in tiles) + "</div>")

    from tools.places.sources_match import KIND_FIT
    gap_kinds = ("village", "hamlet", "abandoned-village", "outpost", "kothringi-ruin", "velothi-ruin", "imperial-ruin",
                 "lilmothiit-ruin", "quarry", "estate", "lighthouse")
    gap = {k: [0, 0] for k in gap_kinds}
    for r in a0:
        k = places[r["place_id"]]["place_kind_id"]
        if k in gap:
            gap[k][0] += 1
            gap[k][1] += KIND_FIT.get(k, {}).get(src[r["source_place_id"]]["kind"], 0) >= 0.85
    w("<h2>What changed since the first version</h2><p>You kept Skyrim's towns as layouts, so that call is gone. The miner "
      "now finds small places in the mods we hold: hamlets of a few huts, camps of tents and ruins by their tileset, "
      "each counted apart even when two share a cell. Kothringi ruins now take an abandoned village or an Imperial "
      "ruin, as the lore describes them, never a cave or a Dwemer city. Ten more mods were mined and kept where "
      "they won places: Wyrmstooth, Nyhus (Cyrodiil's border: Imperial forts and villages), Skyrim Trading Posts "
      "(roadside posts for outposts), Caves of Morrowind, Bloodmoon Dungeons Restored and Solstheim Dungeonpack "
      "(Velothi tombs), Underwater Skyrim (sunken ruins), Northwatch Coast, Explore Skyrim and Moonpath to Elsweyr. "
      "Each is a download you make yourself, as the others are; nothing of theirs is shipped.</p>")
    w("<h2>Gaps that remain</h2><p class=muted>Places of each kind whose source is the same kind of place. No mod on "
      "Nexus places Argonian tribal camps, toll posts or quarries; those kinds take the nearest kind we hold.</p><div class=scroll><table><tr><th>Our kind</th><th class=n>Places</th><th class=n>Same kind</th></tr>"
      + "".join(f"<tr><td>{e(k)}</td><td class=n>{n}</td><td class=n>{f}</td></tr>" for k, (n, f) in gap.items())
      + "</table></div>")
    w("<h2>How similar, by importance</h2><p class=muted>Importance 5 shapes the province, 1 is local colour. The "
      "allocation weighs a major place six times a minor one, so the major places should score highest.</p>")
    w("<div class=scroll><table><tr><th>Importance</th><th class=n>Places</th><th class=n>Mean</th><th class=n>Lowest</th>"
      "<th class=n>Median</th><th>Spread (tenths, 0 to 1)</th></tr>")
    for i in (5, 4, 3, 2, 1):
        s = sorted(r["score"] for r in a0 if imp[r["place_id"]] == i)
        bins = [0] * 10
        for x in s:
            bins[min(9, int(x * 10))] += 1
        top = max(bins)
        bars = ("<svg viewBox='0 0 100 24' width=150 height=24 role=img aria-label='scores 0 to 1 in tenths'>"
                + "".join(f"<rect x={b * 10 + 1} y={24 - 22 * n / top:.1f} width=8 height={22 * n / top:.1f} fill='var(--bar)'/>"
                          for b, n in enumerate(bins) if n) + "</svg>")
        w(f"<tr><td>{i}</td><td class=n>{len(s)}</td><td class=n>{statistics.mean(s):.2f}</td><td class=n>{s[0]:.2f}</td>"
          f"<td class=n>{statistics.median(s):.2f}</td><td style='white-space:nowrap'>{bars}</td></tr>")
    w("</table></div>")

    w("<h2>What kinds of source each kind of place got</h2><div class=scroll><table><tr><th>Our kind</th><th class=n>Places</th>"
      "<th class=n>Mean</th><th>Source kinds used (count)</th><th>From</th></tr>")
    kinds = defaultdict(list)
    for r in a0:
        kinds[places[r["place_id"]]["place_kind_id"]].append(r)
    for k, rs in sorted(kinds.items(), key=lambda x: -len(x[1])):
        sk = Counter(src[r["source_place_id"]]["kind"] for r in rs)
        gp = Counter(src[r["source_place_id"]]["mined_group"] for r in rs)
        w(f"<tr><td>{e(k)}</td><td class=n>{len(rs)}</td><td class=n>{statistics.mean(r['score'] for r in rs):.2f}</td>"
          f"<td>{', '.join(f'{e(a)} {b}' for a, b in sk.most_common())}</td><td class=muted>{', '.join(f'{e(a)} {b}' for a, b in gp.most_common())}</td></tr>")
    w("</table></div>")

    def srcline(r):
        s = src[r["source_place_id"]]
        return (f"<b>{e(s['name'])}</b> <span class=chip>{e(s['kind'])}</span> <span class=chip>{e(s['plugin'])}</span> "
                f"score {r['score']:.2f} · {s['residents']} residents, {s['buildings']} buildings, {s['interiors']} interiors "
                f"<div class=k>{e(s['id'])}</div>")

    w("<h2>The 21 major places</h2><p class=muted>Allocated source first, then the three next most similar (these may be "
      "shared with other places). “Why” names the kind of place the source is and its strongest score parts.</p>")
    for p in sorted(places.values(), key=lambda p: (-p["importance"], p["name"])):
        if p["importance"] < 4:
            continue
        r0 = by[p["id"]][0]
        w(f"<div class=card><h3>{e(p['name'])} <span class=muted>· {e(p['place_kind_id'])} · importance {p['importance']}</span></h3>"
          f"<div>{srcline(r0)}</div><div class=muted>Why: {e(r0['why'])}</div>"
          f"<div class=muted>Population {r0.get('population_before')} → {r0.get('population_after')}: {e(r0.get('population_why'))}</div>"
          f"<ol class=alts>" + "".join(f"<li>{srcline(by[p['id']][k])}</li>" for k in (1, 2, 3) if k in by[p["id"]]) + "</ol></div>")

    def table(rows, title, note, why=True):
        w(f"<h2>{title}</h2><p class=muted>{note}</p><div class=scroll><table><tr><th>Our place</th><th>Kind</th><th class=n>Imp.</th>"
          "<th>Source</th><th>Source kind</th><th class=n>Score</th>" + ("<th>Why</th>" if why else "") + "</tr>")
        for r in rows:
            p, s = places[r["place_id"]], src[r["source_place_id"]]
            w(f"<tr><td>{e(p['name'])}</td><td>{e(p['place_kind_id'])}</td><td class=n>{p['importance']}</td>"
              f"<td>{e(s['name'])} <span class=muted>({e(s['plugin'])})</span></td><td>{e(s['kind'])}</td>"
              f"<td class=n>{r['score']:.2f}</td>" + (f"<td class=muted>{e(r['why'])}</td>" if why else "") + "</tr>")
        w("</table></div>")

    table(sorted(a0, key=lambda r: r["score"])[:25], "The 25 weakest matches",
          "Where the best unique source we hold is still a poor fit; a better source would need a plugin we do not mine.")
    table(sorted(mism, key=lambda r: (-imp[r["place_id"]], r["score"])), f"Source of another family ({len(mism)})",
          "Our place is one family (settlement, camp, military, ruin, underground, water, landmark) and its source another.",
          why=False)

    w("<h2>Population</h2>")
    try:
        import subprocess
        head = subprocess.run(["git", "show", "HEAD:newworld/sources/source_match/place_source.jsonl"], cwd=REPO,
                              capture_output=True, text=True, check=True).stdout
        prev = sum((json.loads(x).get("population_after") or 0) for x in head.splitlines() if x.strip() and json.loads(x)["rank"] == 0)
    except Exception:
        prev = None
    w(f"<p>A lived place's population is now its source's residents: the people the source's layout was built for, "
      "with hostile and levelled enemies left out. Nothing is blended toward the record's estimate or held to a kind's "
      "range. Ruined, abandoned and sunken places the record leaves empty stay at 0; no place has fewer people than "
      "its record names (traders, trainers, followers); a source whose miner counted nobody keeps the record's "
      f"estimate.</p><p>Total: research estimate {pb}"
      + (f", the cut-down version you saw {prev}" if prev is not None and prev != pa else "") + f", now {pa}.</p>")
    big = sorted(a0, key=lambda r: -(r.get("population_after") or 0))[:20]
    w("<h3>The 20 biggest</h3><div class=scroll><table><tr><th>Place</th><th>Kind</th><th>Source</th>"
      "<th class=n>Estimate</th><th class=n>Now</th></tr>")
    for r in big:
        p = places[r["place_id"]]
        w(f"<tr><td>{e(p['name'])}</td><td>{e(p['place_kind_id'])}</td><td>{e(src.get(r['source_place_id'], {}).get('title', r['source_place_id']))}</td>"
          f"<td class=n>{r.get('population_before')}</td><td class=n>{r.get('population_after')}</td></tr>")
    w("</table></div>")
    kept = [r for r in a0 if "fallback" in (r.get("population_why") or "") or "raised" in (r.get("population_why") or "")
            or ((r.get("population_after") or 0) == 0)]
    w(f"<h3>Kept at the estimate, raised, or at 0 ({len(kept)})</h3><div class=scroll><table><tr><th>Place</th><th>Kind</th>"
      "<th class=n>Now</th><th>Why</th></tr>")
    for r in sorted(kept, key=lambda r: (r.get("population_after") or 0) == 0):
        p = places[r["place_id"]]
        w(f"<tr><td>{e(p['name'])}</td><td>{e(p['place_kind_id'])}</td><td class=n>{r.get('population_after')}</td>"
          f"<td class=muted>{e(r.get('population_why'))}</td></tr>")
    w("</table></div>")

    w("<h2>Plugins mined</h2><div class=scroll><table><tr><th>Group</th><th>Plugins</th><th>Mod</th><th class=n>Mined</th>"
      "<th class=n>Usable</th><th class=n>Allocated</th></tr>")
    usable = ranked["by_group"]
    alloc = Counter(src[r["source_place_id"]]["mined_group"] for r in a0)
    for g, (_l, mine, credit) in GROUPS.items():
        s = status.get(g, {})
        mined = s.get("rows", 0) if s.get("mined") else f"not mined: {s.get('why', 'not run')}"
        w(f"<tr><td>{e(g)}</td><td>{e(', '.join(mine))}</td><td>{e(credit)}</td><td class=n>{e(mined)}</td>"
          f"<td class=n>{usable.get(g, 0)}</td><td class=n>{alloc.get(g, 0)}</td></tr>")
    w("</table></div><p class=muted>A plugin that only carries building pieces (Xanmeer, the Ayleid resources, the "
      "Hist tree) places no town of its own, so it yields no candidate; its pieces still reach us through the places "
      f"that use them. Dropped before matching: {e(', '.join(f'{k} {v}' for k, v in ranked['dropped'].items()))}; "
      "BM&amp;V's Lilmoth is left out entirely, as asked.</p>")
    w("</main></body></html>")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(out))
    print(OUT)
    return 0
