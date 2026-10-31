"""Custom Skills Framework data for the 13 skills with no vanilla actor value (chunk 1.12 §4; 1.3 §a's table).

The 14 skills on a vanilla actor value (skyrim_units.PLAYER_SKILL_AV) keep their vanilla perk trees and are listed
by name; the other 13 are CSF skills. CSF makes each skill's ActorValueInfo itself at load (Settings::ReadSkillDef
calls the AVIF factory), so Argonia.esm carries no AVIF: it carries what the JSON points at, per skill
  - five GLOBs (float): level, ratio, legendary, color, showLevelup, which ArgoniaCore writes and CSF reads;
  - one placeholder PERK ("No perks yet"), the one node the tree requires even for a skill with no perks.
`SKILLS.json` (CSF's group file whose stem is SKILLS: the vanilla skills menu) lists all 27 and names those forms as
"Argonia.esm|<local id>". Schema: github.com/Exit-9B/CustomSkills docs/schema (CustomSkill.json, skill.json,
defs.json); what was used: docs/research/2026-10-31/csf-config.md.

    python3 -m tools.argonia_world.csf_records            # allocate FormIDs if new, write data/csf/.../SKILLS.json
    python3 -m tools.argonia_world.csf_records --check    # exit 1 when the committed JSON is stale
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.intermediate import Layer

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "data" / "csf" / "SKSE" / "Plugins" / "CustomSkills" / "SKILLS.json"
MOD = "Argonia.esm"
WHITE = 0xFFFFFF  # CSF's colour global: white 0xFFFFFF
PLACEHOLDER_NAME = "No perks yet"
PLACEHOLDER_TEXT = "This skill has no perks yet."
GLOBALS = ("level", "ratio", "legendary", "color", "showLevelup")  # CSF's skill.json global keys, in file order

# The sheet's names for the CSF skills (sentence case; the DB skill table holds ids only).
LABELS = {
    "acrobatics": "Acrobatics", "athletics": "Athletics", "axe": "Axe", "blunt": "Blunt weapon",
    "handToHand": "Hand-to-hand", "longBlade": "Long blade", "marksman": "Marksman", "mediumArmor": "Medium armor",
    "mercantile": "Mercantile", "mysticism": "Mysticism", "shortBlade": "Short blade", "spear": "Spear",
    "unarmored": "Unarmored",
}


def skill_ids(world) -> list[str]:
    """All the skill table's ids, which must be exactly the units module's 27."""
    ids = world.values("SELECT id FROM skill ORDER BY id")
    if set(ids) != set(su.PLAYER_SKILL_AV):
        raise ValueError(f"PLAYER_SKILL_AV differs from the skill table: {sorted(set(ids) ^ set(su.PLAYER_SKILL_AV))}")
    return ids


def csf_ids(world) -> list[str]:
    """The skills that live on CSF: no vanilla actor value."""
    ids = [i for i in skill_ids(world) if su.PLAYER_SKILL_AV[i] is None]
    if set(ids) != set(LABELS):
        raise ValueError(f"LABELS differs from the CSF skills: {sorted(set(ids) ^ set(LABELS))}")
    return ids


def vanilla_ids(world) -> list[str]:
    return [i for i in skill_ids(world) if su.PLAYER_SKILL_AV[i] is not None]


def _pascal(skill: str) -> str:
    return skill[0].upper() + skill[1:]


def global_edid(skill: str, which: str) -> str:
    return f"ARG_CSF_{_pascal(skill)}_{_pascal(which)}"


def perk_edid(skill: str) -> str:
    return f"ARG_CSF_{_pascal(skill)}_Perk"


def layer(alloc, world) -> Layer:
    recs = []
    for s in csf_ids(world):
        for g in GLOBALS:
            e = global_edid(s, g)
            recs.append({"type": "GLOB", "edid": e, "formKey": alloc.form_key(e, "GLOB", f"csf.{s}.{g}"),
                         "value": WHITE if g == "color" else 0, "valueType": "float"})
        e = perk_edid(s)
        recs.append({"type": "PERK", "edid": e, "formKey": alloc.form_key(e, "PERK", f"csf.{s}.perk"),
                     "hidden": False, "playable": True, "trait": False, "level": 100, "ranks": 1,
                     "name": PLACEHOLDER_NAME, "description": PLACEHOLDER_TEXT, "effects": []})
    return Layer("base:csf", recs)


def _form(alloc, edid: str) -> str:
    return f"{MOD}|{alloc.get(edid):06X}"


def config(alloc, world) -> dict:
    """CSF's SKILLS.json: the 14 vanilla skills by name, the 13 CSF skills as objects with a one-node tree."""
    entries = []
    for s in skill_ids(world):
        if su.PLAYER_SKILL_AV[s] is not None:
            entries.append(su.PLAYER_SKILL_AV[s])
            continue
        entry = {"id": f"argonia_{s}", "name": LABELS[s], "description": f"Your skill in {LABELS[s].lower()}."}
        entry.update({g: _form(alloc, global_edid(s, g)) for g in GLOBALS})
        entry["nodes"] = [{"perk": _form(alloc, perk_edid(s)), "x": 0, "y": 1}]
        entries.append(entry)
    return {"version": 1, "skills": entries}


def render(alloc, world) -> str:
    return json.dumps(config(alloc, world), indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> int:
    from tools.argonia_world import db
    from tools.argonia_world.formids import Allocator
    check = "--check" in argv
    world = db.open()
    alloc = Allocator(world, frozen=check)
    layer(alloc, world)  # allocates the FormIDs a new skill needs (appended; the plugin build reuses them)
    text = render(alloc, world)
    if check:
        if not CONFIG.exists() or CONFIG.read_text(encoding="utf-8") != text:
            print(f"{CONFIG.relative_to(REPO)} is stale; run `python3 -m tools.argonia_world.csf_records`",
                  file=sys.stderr)
            return 1
        print("csf: SKILLS.json current")
        return 0
    alloc.save()
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(text, encoding="utf-8")
    print(f"csf: wrote {CONFIG.relative_to(REPO)} ({len(csf_ids(world))} CSF skills, {len(vanilla_ids(world))} vanilla)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
