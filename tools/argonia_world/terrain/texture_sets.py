"""The ground's texture sets (1.15 materials): BM&V's look reaches the ground only through TXST records that point at
its landscape pack (`textures\\TEXTUREPACK\\landscape\\`), because Black Marsh.esm overrides none of the vanilla TXST
(0 of its 144) and paints vanilla LTEX (lane report 2026-11-01). So Argonia.esm carries one new TXST per LTEX the
material paints (`material.TEXTURES`) and an LTEX override naming it, with the grass list the plan gives
(`terrain/grass.py`; the winner's where the plan has no row). BM&V ships no normal maps, so the TXST names none (TX01 empty), by evidence
(2026-11-01): Black Marsh.esm's own landscape TXSTs leave TX01 empty on 8 of its 11, and the other 3 name the
diffuse itself, never a vanilla or Tropical Skyrim `_n`; Tropical Skyrim ships an `_n` for all 19 of our slots,
but each is authored to its own diffuse's stones and tufts, so on BM&V's diffuse it would light relief that is not
there. The in-game look (flat against TS's `_n`) is the planner's batch check.

The records go to ArgoniaGen `generate` (TextureSets.cs, LandTextures.cs); `grass.layer` leaves these LTEX to us.
"""
from __future__ import annotations

from tools.argonia_world.intermediate import Layer
from tools.argonia_world.terrain import material as M

PREFIX = "ArgGroundTxst"


def form_keys() -> set[str]:
    return {t.form_key for t in M.TEXTURES}


def records(alloc, scan: dict, intended: dict[str, list[str]]) -> list[dict]:
    ltex = {l["formKey"]: l for l in scan["ltex"]}
    out = []
    for t in M.TEXTURES:
        edid = PREFIX + t.edid[1:]
        txst = alloc.form_key(edid, "TXST", f"ground.txst.{t.edid}")
        out.append({"type": "TXST", "edid": edid, "formKey": txst, "diffuse": t.bmv})
        w = ltex[t.form_key]
        out.append({"type": "LTEX", "override": True, "formKey": t.form_key, "edid": w["edid"], "textureSet": txst,
                    "materialType": w["materialType"], "friction": w["friction"], "restitution": w["restitution"],
                    "specular": w["specular"], "flags": w["flags"],
                    "grasses": intended.get(t.form_key, w["grasses"])})
    return out


def layer(alloc, scan: dict) -> Layer:
    from tools.argonia_world.terrain import grass
    return Layer("patch:ground-textures", records(alloc, scan, grass.plan(alloc.world)[1]))
