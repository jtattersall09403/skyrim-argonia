"""The season switch's tables for ArgoniaCore (2.W3 §a; native map G05.3): which season a day of the year falls in,
and what each `ARG_WChance_*` global holds in each season. The REGN weather lists read their chances from those
globals (RDWT's global), so setting them when the season turns is what makes the province's weather seasonal. Vanilla
uses no global (skyrim-does-it-this-way §7); seasons are new to it, so the seasonal shift is the one thing a global
carries, and no entry is gated by hour.

Each global is one weather of one weather group. The group's mist weather (its regions' regime, region_mist) takes the
regime's season chance (mist_regime_season); the synoptic weathers share the rest by state weight, times the
season's factor on that state (season_factor, 1 where unlisted), times the weather's share of the state, so a state a
season rules out (dry haze in the wet) gets 0. Each season's list sums to 100 (§7). The year runs the seasons in `season.year_ord` order from the first day, each taking its `share` of the
days. That order is a reversible design choice: the imported seasons have shares but no months.

    python3 -m tools.argonia_world.regions.season [--check]   write (or diff) skse/core/generated/.../tables_weather.h
"""
from __future__ import annotations

import difflib
import sys
from collections import defaultdict
from pathlib import Path

from tools.argonia_world import db
from tools.argonia_world import skyrim_units as su

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "skse" / "core" / "generated" / "argonia" / "core" / "tables_weather.h"
def order(w) -> list[str]:
    """The seasons in the year's order from day 0 (season.year_ord)."""
    return w.values("SELECT id FROM season ORDER BY year_ord")


def windows(w) -> list[tuple[str, int, int]]:
    """(season, first day, end day) over the year's days (0-based), in year order, covering the year once."""
    share = {r["id"]: r["share"] for r in w.query("SELECT id, share FROM season")}
    seasons = order(w)
    days = sum(su.MONTH_DAYS)
    out, acc, start = [], 0.0, 0
    for s in seasons:
        acc += share[s] / sum(share.values())
        end = days if s == seasons[-1] else round(acc * days)
        out.append((s, start, end))
        start = end
    return out


def hundred(raw: dict[str, float]) -> dict[str, int]:
    """Whole chances summing to exactly 100 by largest remainder (vanilla's lists all sum to 100,
    skyrim-does-it-this-way §7); all zero stays zero."""
    tot = sum(raw.values())
    if tot <= 0:
        return {k: 0 for k in raw}
    exact = {k: 100 * v / tot for k, v in raw.items()}
    out = {k: int(v) for k, v in exact.items()}
    for k in sorted(exact, key=lambda k: (out[k] - exact[k], k))[:100 - sum(out.values())]:
        out[k] += 1
    return out


def group_mist(w) -> dict[str, str]:
    """{weather group: its regions' mist weather} from region_mist; a group whose regions differ is refused (the
    chance globals are per group and weather)."""
    out: dict[str, set] = defaultdict(set)
    for r in w.query("SELECT e.weather_group_id g, mr.weather_id wid FROM land_region l JOIN eco_class e ON "
                     "e.id = l.eco_class_id JOIN region_mist m ON m.land_region_id = l.id JOIN mist_regime mr ON "
                     "mr.id = m.regime WHERE l.border = 0"):
        out[r["g"]].add(r["wid"])
    bad = {g: sorted(v) for g, v in out.items() if len(v) > 1}
    if bad:
        raise ValueError(f"weather groups with two mist regimes: {bad}")
    return {g: next(iter(v)) for g, v in sorted(out.items())}


def group_lists(w) -> dict[str, dict[str, dict[str, int]]]:
    """{group: {weather: {season: chance}}}: the group's mist weather at its regime's season chance
    (mist_regime_season), the synoptic weathers (state weight x season factor x share) sharing the rest; each
    season's list sums to 100 (skyrim-does-it-this-way §7)."""
    fac = {(r["season_id"], r["weather_state_id"]): r["factor"] for r in w.query("SELECT * FROM season_factor")}
    mist_w = group_mist(w)
    mist_ch = {(r["weather_id"], r["season_id"]): r["chance"] for r in w.query(
        "SELECT mr.weather_id, s.season_id, s.chance FROM mist_regime mr JOIN mist_regime_season s "
        "ON s.regime_id = mr.id")}
    out: dict[str, dict[str, dict[str, int]]] = {}
    for g in w.values("SELECT DISTINCT weather_group_id FROM weather_realisation ORDER BY 1"):
        rows = w.query("SELECT r.weather_state_id st, r.weather_id wid, r.share, gw.weight FROM weather_realisation r "
                       "JOIN weather_group_weight gw ON gw.weather_group_id = r.weather_group_id AND "
                       "gw.weather_state_id = r.weather_state_id WHERE r.weather_group_id = ? ORDER BY r.weather_id", g)
        per: dict[str, dict[str, int]] = defaultdict(dict)
        for s in order(w):
            raw = defaultdict(float)
            for r in rows:
                raw[r["wid"]] += r["weight"] * fac.get((s, r["st"]), 1.0) * r["share"]
            m = mist_ch.get((mist_w.get(g), s), 0) if g in mist_w else 0
            tot = sum(raw.values()) or 1.0
            scaled = {k: v * (100 - m) / tot for k, v in raw.items()}
            if g in mist_w:
                scaled[mist_w[g]] = m
            for wid, c in hundred(scaled).items():
                per[wid][s] = c
        out[g] = dict(sorted(per.items()))
    return out


def global_name(group: str, weather: str) -> str:
    from tools.argonia_world.regions.classify import slug
    return f"ARG_WChance_{slug(group)}_{slug(weather)}"


def region_list(w, group: str) -> list[tuple[str, int, str]]:
    """(weather, chance, season global) for a group's region list: the chance the year's mean over the seasons'
    shares, summing to 100, which the global replaces season by season."""
    share = {r["id"]: r["share"] for r in w.query("SELECT id, share FROM season")}
    per = group_lists(w).get(group, {})
    mean = hundred({wid: sum(share[s] * c for s, c in v.items()) for wid, v in per.items()})
    return [(wid, mean[wid], global_name(group, wid)) for wid in sorted(per)]


def chances(w) -> dict[str, dict[str, int]]:
    """{global EditorID: {season: chance 0..100}} for every global a region list names."""
    used = set(w.values("SELECT DISTINCT season_global FROM land_region_weather WHERE season_global LIKE "
                        "'ARG_WChance_%'"))
    out = {global_name(g, wid): v for g, lst in group_lists(w).items() for wid, v in lst.items()}
    missing = used - set(out)
    if missing:
        raise ValueError(f"globals with no realisation: {sorted(missing)}")
    return {k: out[k] for k in sorted(used)}


def render(w) -> str:
    win, ch = windows(w), chances(w)
    lines = ["// tables_weather.h: GENERATED by tools/argonia_world/regions/season.py from the world database",
             "// (decision 0030). Data only. Do not edit: change the rows through db.py and regenerate.",
             "#pragma once", "#include <array>", "#include <cstdint>", "#include <string_view>", "",
             "namespace argonia::core::gen {", "",
             f"enum class Season : std::uint8_t {{ {', '.join(s.replace('-', '_') for s in order(w))} }};",
             f"inline constexpr std::size_t kSeasons = {len(order(w))};",
             f"inline constexpr std::array<std::uint8_t, 12> kMonthDays{{{', '.join(map(str, su.MONTH_DAYS))}}};",
             "struct SeasonWindow { Season season; std::uint16_t first_day, end_day; };",
             f"inline constexpr std::array<SeasonWindow, {len(win)}> kSeasonWindows{{{{",
             *[f"    {{Season::{s}, {a}, {b}}}," for s, a, b in win], "}};",
             "struct WeatherChance { std::string_view global; std::array<std::uint8_t, kSeasons> chance; };",
             f"inline constexpr std::array<WeatherChance, {len(ch)}> kWeatherChances{{{{",
             *[f"    {{\"{g}\", {{{', '.join(str(v[s]) for s in order(w))}}}}}," for g, v in ch.items()],
             "}};", "", "}  // namespace argonia::core::gen", ""]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    text = render(db.open())
    if "--check" in argv:
        cur = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if cur != text:
            sys.stderr.write("".join(difflib.unified_diff(cur.splitlines(True), text.splitlines(True), str(OUT),
                                                          "regenerated", n=1)))
            print("tables_weather.h is stale; run `python3 -m tools.argonia_world.regions.season`", file=sys.stderr)
            return 1
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"season: {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
