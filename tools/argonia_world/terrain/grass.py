"""The grass the painted ground grows (2.W1; decision 0006: no Nordic grass in the marsh).

Every LTEX the land cover paints (`land_cover_ltex`) carries a grass list, and the game grows that list wherever the
texture lies. The winning copy of a list comes from the load order: Tropical Skyrim's override, Depths of
Skyrim's underwater one, or vanilla's. The intended list per painted LTEX is world data: `ltex_grass_plan` lists
every painted LTEX (one with no `ltex_grass` rows is bare on purpose), `ltex_grass` its forms in order, and
`grass_source` the plugins a grass form may come from (it must be defined or overridden there). Where the
winning list is not the intended one, Argonia.esm overrides the LTEX: every field is the winner's, and only the
grass list is ours.

The L1 check (`check`): every painted LTEX's list, after Argonia.esm's overrides, is made only of GRAS from a
grass source, or is empty where the plan says bare. The scan is ArgoniaGen `ltex` (out/ltex-scan.json).
"""
from __future__ import annotations

import json
from pathlib import Path

from tools.argonia_world.intermediate import Layer

ROOT = Path(__file__).resolve().parents[3]
SCAN = ROOT / "out" / "ltex-scan.json"
SOURCES = {  # the seed of `grass_source`
    "Tropical Skyrim.esp": "the base-Skyrim replacer (decision 0006 §8): its tropical grass forms and overrides",
    "DepthsOfSkyrim.esp": "underwater flora only (seabed, river bottom and mud): kelp, algae, seaweed, coral",
}
ADD = {  # an LTEX that would be bare once filtered, but should grow grass: its forms (seed of `ltex_grass`)
    "LFallForestDirt01": ["TropicalGrassPlant01"],
}


def load_scan(path: Path = SCAN) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def allowed(scan: dict, sources) -> set[str]:
    src = set(sources)
    return {g["formKey"] for g in scan["grass"] if src & set(g["plugins"])}


def seed_plan(scan: dict, painted: dict[str, str]) -> tuple[list[dict], list[dict], list[dict]]:
    """The first plan from the scan: each painted LTEX (form key -> EditorID) keeps its winning list filtered to the
    grass sources, plus ADD; returns (grass_source, ltex_grass_plan, ltex_grass) rows."""
    ok = allowed(scan, SOURCES)
    ltex = {l["formKey"]: l for l in scan["ltex"]}
    by_edid = {g["edid"]: g["formKey"] for g in scan["grass"] if g["formKey"] in ok}
    plans, rows = [], []
    for fk, edid in sorted(painted.items()):
        keep = [g for g in ltex[fk]["grasses"] if g in ok] + [by_edid[e] for e in ADD.get(edid, [])]
        dropped = [g for g in ltex[fk]["grasses"] if g not in ok]
        why = ("the winning list, filtered to the grass sources" + (f" ({len(dropped)} vanilla forms dropped)" if dropped else "")
               + ("; plus tropical grass" if edid in ADD else "") if keep else "bare on purpose (no grass source grows here)")
        plans.append({"ltex_form_key": fk, "ltex_edid": edid, "why": why})
        rows += [{"ltex_form_key": fk, "ord": i, "grass_form_key": g} for i, g in enumerate(keep)]
    return [{"plugin": p, "why": w} for p, w in SOURCES.items()], plans, rows


def plan(world) -> tuple[set[str], dict[str, list[str]]]:
    """(the grass source plugins, painted LTEX form key -> intended grass list) from the database."""
    sources = {r[0] for r in world.query("SELECT plugin FROM grass_source")}
    out = {r[0]: [] for r in world.query("SELECT ltex_form_key FROM ltex_grass_plan")}
    for fk, g in world.query("SELECT ltex_form_key, grass_form_key FROM ltex_grass ORDER BY ltex_form_key, ord"):
        out[fk].append(g)
    return sources, out


def overrides(scan: dict, intended: dict[str, list[str]]) -> list[dict]:
    """The LTEX override records Argonia.esm needs: every field the winner's, the grass list the plan's."""
    ltex = {l["formKey"]: l for l in scan["ltex"]}
    out = []
    for fk, want in sorted(intended.items()):
        w = ltex[fk]
        if w["grasses"] != want:
            out.append({"type": "LTEX", "override": True, "formKey": fk, "edid": w["edid"],
                        "textureSet": w["textureSet"], "materialType": w["materialType"], "friction": w["friction"],
                        "restitution": w["restitution"], "specular": w["specular"], "flags": w["flags"],
                        "grasses": want})
    return out


def layer(world, scan: dict) -> Layer:
    return Layer("patch:ltex-grass", overrides(scan, plan(world)[1]))


def check(scan: dict, world, records: list[dict]) -> list[str]:
    """Every painted LTEX's effective list (Argonia.esm's override if any, else the winner's) is only grass-source
    GRAS, and empty exactly where the plan says bare. Returns the failures."""
    sources, intended = plan(world)
    ok = allowed(scan, sources)
    names = {g["formKey"]: g["edid"] for g in scan["grass"]}
    ltex = {l["formKey"]: l for l in scan["ltex"]}
    ours = {r["formKey"]: r["grasses"] for r in records if r.get("type") == "LTEX"}
    painted = {r[0]: r[1] for r in world.query("SELECT ltex_form_key, ltex_edid FROM land_cover_ltex")}
    errs = []
    for fk, edid in sorted(painted.items()):
        if fk not in intended:
            errs.append(f"{edid}: painted but has no ltex_grass_plan row")
            continue
        eff = ours.get(fk, ltex[fk]["grasses"])
        bad = [names.get(g, g) for g in eff if g not in ok]
        if bad:
            errs.append(f"{edid}: grass not from a grass source: {', '.join(bad)}")
        if bool(eff) != bool(intended[fk]):
            errs.append(f"{edid}: {'grows grass' if eff else 'bare'}, the plan says {'grass' if intended[fk] else 'bare'}")
    return errs
