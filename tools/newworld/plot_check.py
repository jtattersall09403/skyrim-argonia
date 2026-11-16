"""Check the danger ladder of a story line's plot page against the place database.

    python3 -m tools.newworld.plot_check story/design/quests/lines/main-plot.md [more.md] [--opens-at D2] [--json]

Under the "## ... The acts" heading each quest is a numbered item ``6. **Title** (place, kind; place, kind). text`` or a
paragraph ``**6. Title** (place, kind; ...). text``. A place's band is the harder of its strength and reach bands
(``place_danger``), else its ``danger_band_id``; a quest's band is its hardest place. Errors (exit 1): a jump of more
than one band over the hardest earlier quest (a line may climb from towns to its opening band), a first quest above the opening band (D1, or D2 with --opens-at D2), a
second quest above D2, a quest with no place of the database. Warnings: a slump (two or more bands under the running
top after the line's first third), a phrase that is not a place when another place resolved. Info: the last act's top.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "newworld" / "story" / "data" / "db"
NUMBERED = re.compile(r"^\s*(\d+)\.\s+\*\*(.+?)\*\*\s*(.*)$")
PARA = re.compile(r"^\s*\*\*(\d+)\.\s+(.+?)\*\*\s*(.*)$")
ACT = re.compile(r"^###\s+Act\b")


def _jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def norm(name: str) -> str:
    s = re.sub(r"\s+", " ", name.strip().lower().replace("’", "'"))
    for p in ("the wreck of the ", "wreck of the ", "the "):
        if s.startswith(p):
            return s[len(p):]
    return s


def band_rank(b: str | None) -> int | None:
    m = re.fullmatch(r"D(\d)", b or "")
    return int(m.group(1)) if m else None


class Places:
    def __init__(self, data: Path = DATA):
        self.by_name: dict[str, str] = {}
        self.band: dict[str, int | None] = {}
        for r in _jsonl(data / "place.jsonl"):
            self.band[r["id"]] = band_rank(r.get("danger_band_id"))
            self._add(r["name"], r["id"])
        for r in _jsonl(data / "place_alias.jsonl"):
            if r["place_id"] in self.band:
                self._add(r["alias"], r["place_id"])
        for r in _jsonl(data / "place_danger.jsonl"):
            ranks = [x for x in (band_rank(r.get("strength_band_id")), band_rank(r.get("reach_band_id"))) if x is not None]
            if ranks and r["place_id"] in self.band:
                self.band[r["place_id"]] = max(ranks)

    def _add(self, name: str, pid: str) -> None:
        self.by_name.setdefault(norm(name), pid)

    def find(self, phrase: str) -> tuple[str, int | None] | None:
        pid = self.by_name.get(norm(phrase))
        return None if pid is None else (pid, self.band[pid])


def _first_paren(text: str) -> str | None:
    i = text.find("(")
    if i < 0:
        return None
    depth = 0
    for j in range(i, len(text)):
        depth += text[j] == "("
        depth -= text[j] == ")"
        if depth == 0:
            return text[i + 1:j]
    return None


def parse(text: str) -> list[dict]:
    """Quests of the acts section: {number, title, phrases, act}."""
    quests: list[dict] = []
    in_acts, act, cur = False, None, None
    for line in text.splitlines():
        if line.startswith("## "):
            in_acts = "The acts" in line
            cur = None
            continue
        if not in_acts:
            continue
        if ACT.match(line):
            act, cur = line.lstrip("# ").strip(), None
            continue
        m = NUMBERED.match(line) or PARA.match(line)
        if m:
            cur = {"number": int(m.group(1)), "title": m.group(2).strip().rstrip("."), "act": act, "raw": m.group(3)}
            quests.append(cur)
        elif cur is not None and line.strip() and not line.startswith("#"):
            cur["raw"] += " " + line.strip()
    for q in quests:
        raw = q.pop("raw").strip()
        inner = _first_paren(raw) if raw.startswith("(") else None
        q["phrases"] = [p.split(",")[0].strip() for p in (inner or "").split(";") if p.strip()]
    return quests


def analyse(quests: list[dict], places: Places, opens_at: str = "D1") -> dict:
    n = len(quests)
    open_rank = band_rank(opens_at) or 1
    first_third = math.ceil(n / 3)
    errors: list[str] = []
    warnings: list[str] = []
    rows = []
    top = None
    for i, q in enumerate(quests):
        found, missing = [], []
        for ph in q["phrases"]:
            hit = places.find(ph)
            if hit and hit[1] is not None:
                found.append((ph, hit))
            else:
                missing.append(ph)
        resolved = [(ph, h[0], h[1]) for ph, h in found]
        band = max((b for _, _, b in resolved), default=None)
        label = f"{q['number']} {q['title']}"
        if band is None:
            errors.append(f"{label}: no place of the database ({', '.join(q['phrases']) or 'none named'})")
        else:
            for ph in missing:
                warnings.append(f"{label}: '{ph}' is not a place")
            # a line may climb to its opening band from towns (D0) without a jump
            if top is not None and band > max(top, open_rank - 1) + 1:
                errors.append(f"{label}: D{band} is a jump over the top so far D{top}")
            if i == 0 and band > open_rank:
                errors.append(f"{label}: the first quest is D{band}, above D{open_rank}")
            if i == 1 and band > 2:
                errors.append(f"{label}: the second quest is D{band}, above D2")
            if top is not None and i >= first_third and band <= top - 2:
                warnings.append(f"{label}: D{band} is a slump under the top D{top}")
            top = band if top is None else max(top, band)
        rows.append({
            "number": q["number"], "title": q["title"], "act": q["act"],
            "places": [{"name": ph, "place": pid, "band": f"D{b}"} for ph, pid, b in resolved]
            + [{"name": ph, "place": None, "band": None} for ph in missing],
            "band": None if band is None else f"D{band}",
            "top": None if top is None else f"D{top}",
        })
    info = []
    if quests:
        last = quests[-1]["act"]
        bands = [band_rank(r["band"]) for r in rows if r["act"] == last and r["band"]]
        if bands:
            info.append(f"last act ({last}): top D{max(bands)}")
    return {"rows": rows, "errors": errors, "warnings": warnings, "info": info}


def render(path: str, res: dict) -> str:
    out = [f"== {path}", f"{'#':>3}  {'quest':<28} {'places':<70} {'band':<5} top"]
    for r in res["rows"]:
        pl = "; ".join(f"{p['name']} {p['band'] or '?'}" for p in r["places"])
        out.append(f"{r['number']:>3}  {r['title'][:28]:<28} {pl[:70]:<70} {r['band'] or '-':<5} {r['top'] or '-'}")
    out += [f"ERROR: {e}" for e in res["errors"]] + [f"warning: {w}" for w in res["warnings"]]
    out += [f"info: {i}" for i in res["info"]]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="plot_check")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--opens-at", default="D1", choices=["D1", "D2"])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    places = Places()
    results = {f: analyse(parse(Path(f).read_text()), places, a.opens_at) for f in a.files}
    if a.json:
        print(json.dumps(results, indent=1))
    else:
        print("\n\n".join(render(f, r) for f, r in results.items()))
    return 1 if any(r["errors"] for r in results.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
