"""The ground's texture sets (1.15 materials): BM&V's look reaches the ground only through TXST records that point at
its landscape pack (`textures\\TEXTUREPACK\\landscape\\`), because Black Marsh.esm overrides none of the vanilla TXST
(0 of its 144) and paints vanilla LTEX (lane report 2026-11-01). So Argonia.esm carries one new TXST per LTEX the
material paints (`material.TEXTURES`) and an LTEX override naming it, with the grass list the plan gives
(`terrain/grass.py`; the winner's where the plan has no row). BM&V ships no normal maps, and a landscape TXST with
no TX01 shades from the engine's default normal; the landscape shader reads specular from the normal's alpha, so the
ground shone (owner, play test 3, findings 16-17). Each TXST names Skyrim.esm's own normal of the same name
(`Tex.normal`, `landscape\\<name>_n.dds`, in the player's Skyrim - Textures BSA): vanilla's landscape normals carry
alpha p50 ~20/255 (50 files, measured 2026-11-02, terrain/texcheck.py), Tropical Skyrim's DXT1 copies at the same
paths carry 255 on 18 of our 19, so dependencies.json drops those 19 TS files and the vanilla ones resolve.
`python -m tools.argonia_world.terrain check-materials` proves the laid set.

The records go to ArgoniaGen `generate` (TextureSets.cs, LandTextures.cs); `grass.layer` leaves these LTEX to us.
"""
from __future__ import annotations

from tools.argonia_world.intermediate import Layer
from tools.argonia_world.terrain import material as M

PREFIX = "ARG_GroundTxst"  # formids.EDID: every new Argonia EditorID is ARG_


def form_keys() -> set[str]:
    return {t.form_key for t in M.TEXTURES}


def records(alloc, scan: dict, intended: dict[str, list[str]]) -> list[dict]:
    ltex = {l["formKey"]: l for l in scan["ltex"]}
    out = []
    for t in M.TEXTURES:
        edid = PREFIX + t.edid[1:]
        txst = alloc.form_key(edid, "TXST", f"ground.txst.{t.edid}")
        out.append({"type": "TXST", "edid": edid, "formKey": txst, "diffuse": t.bmv, "normal": t.normal})
        w = ltex[t.form_key]
        out.append({"type": "LTEX", "override": True, "formKey": t.form_key, "edid": w["edid"], "textureSet": txst,
                    "materialType": w["materialType"], "friction": w["friction"], "restitution": w["restitution"],
                    "specular": w["specular"], "flags": w["flags"],
                    "grasses": intended.get(t.form_key, w["grasses"])})
    return out


def layer(alloc, scan: dict) -> Layer:
    from tools.argonia_world.terrain import grass
    return Layer("patch:ground-textures", records(alloc, scan, grass.plan(alloc.world)[1]))
