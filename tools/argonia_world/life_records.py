"""The generated records of the life hooks (native map P3, P4; docs/research/native-map.md §2, §3.4-3.5): the rest
spot and the Vastei pile, the keywords ArgoniaCore reads by world id, the rest-intercept perk and the game-setting
overrides of the engine's own XP and cell respawn.

Every field is plain and resolved; ArgoniaGen's ActivatorRecords.cs, GameSettingRecords.cs and PerkRecords.cs make no
choices. The two models, picked from out/pieces-index.json by the asset route (Black Marsh mods, then Tropical Skyrim
SSE, then vanilla; the index holds no Black Marsh or Tropical Skyrim bedroll or soul marker, so vanilla's, as a path
only, never a file):
  - ARG_CampSpot: furniture/bedroll/bedroll01.nif, vanilla's ground bedroll (a stitched hide with a fur pillow, no
    Nordic element; a camp is a bedroll). Not bedrollground.nif: that file is only the furniture marker and an
    editor marker, with no visible geometry and no collision (quarantine verdict 00085F, core-wiring 2026-10-30).
  - ARG_VasteiPile: effects/ashpileghost01.nif, the mesh of vanilla's DefaultAshPileGhost (101048:Skyrim.esm), the
    soft pale glowing heap a slain ghost leaves and the player activates to loot: a pile you walk to and take, with no
    Nordic ornament (owner 2026-10-30: native, nice-looking, from magic; ranking in
    docs/research/2026-10-30/respawn-rulings.md §4). ArgoniaCore plays VASTEI_FX_ART on it, vanilla's Soul Trap
    target art (violet soul wisps), so it reads as souls. Both are referenced by path and FormKey, never shipped.
"""
from __future__ import annotations

from tools.argonia_world.formids import Allocator
from tools.argonia_world.intermediate import Layer

REST_SPOT = ("ARG_RestSpot", "hook.rest-spot")
VASTEI_PILE = ("ARG_VasteiPile", "hook.vastei-pile")
LOC_SETTLEMENT = ("ARG_LocType_Settlement", "hook.loc-settlement")
LOC_DUNGEON = ("ARG_LocType_Dungeon", "hook.loc-dungeon")
LOC_CLEARABLE = ("ARG_LocType_Clearable", "hook.loc-clearable")
PERK_EDID = "ARG_Perk_RestIntercept"
FRAGMENT_SCRIPT = "ARG_PRKF_RestIntercept"
CAMP_MODEL = "Furniture\\Bedroll\\Bedroll01.nif"
VASTEI_MODEL = "Effects\\AshPileGhost01.nif"
VASTEI_FX_ART = "0506D6:Skyrim.esm"  # ARTO SoulTrapTargetEffects (magic/soultraptargeteffects.nif); 1.5 runtime


def location_edid(place_id: str) -> str:
    return "ARG_Loc_" + "".join(w[:1].upper() + w[1:] for w in place_id.rsplit(".", 1)[1].split("-"))


def location_key(alloc, place_id: str) -> str:
    """The LCTN of a clearable place (owner 2026-10-30): the engine's own cleared state lives on it."""
    return alloc.form_key(location_edid(place_id), "LCTN", f"loc.{place_id}")


def clearable_places(world) -> list[str]:
    return sorted(h.place_id for h in world.rows("place_build_hostility") if h.clearable)


def _choice(kw: str, label: str, fragment: int) -> dict:
    return {
        "entryPoint": "Activate", "function": "AddActivateChoice", "rank": 0, "priority": 0, "tabCount": 2,
        "conditions": [{"tab": 1, "function": "HasKeyword", "keyword": kw, "op": "EqualTo", "value": 1}],
        "buttonLabel": label, "flags": ["RunImmediately", "ReplaceDefault"], "fragment": fragment,
    }


def game_settings(alloc: Allocator, world, scan: dict) -> list[dict]:
    """One GMST per game_setting row. A setting the master defines is an override with the master's FormKey, read
    from the vanilla scan. A setting the engine has built in but no master record carries (fXPPerSkillRank is one)
    is a new record of ours: the engine reads a GMST by its EditorID."""
    found = scan.get("gameSettings", {})
    out = []
    for r in world.rows("game_setting", order="edid"):
        m = found.get(r.edid)
        if m is not None and m["kind"] != r.kind:
            raise ValueError(f"{r.edid}: the master's setting is {m['kind']}, the row says {r.kind}")
        value = int(r.value) if r.kind in ("int", "bool") else float(r.value)
        rec = {"type": "GMST", "edid": r.edid, "kind": r.kind, "value": value}
        if m is not None:
            rec.update(override=True, formKey=m["formKey"])
        else:
            rec["formKey"] = alloc.form_key(r.edid, "GMST", f"setting.{r.edid}")
        out.append(rec)
    return out


def layer(alloc: Allocator, world, scan: dict) -> Layer:
    fk = alloc.form_key
    keys = {}
    recs: list[dict] = []
    kws = [REST_SPOT, VASTEI_PILE, LOC_SETTLEMENT, LOC_DUNGEON, LOC_CLEARABLE]
    for edid, wid in kws:
        keys[edid] = fk(edid, "KYWD", wid)
        recs.append({"type": "KYWD", "edid": edid, "formKey": keys[edid]})
    # One LCTN per clearable place, keyworded clearable: its persistent actors carry it as their editor location
    # (place_build), and ArgoniaCore sets its native cleared flag once every untilCleared actor there is dead at once.
    for pid in clearable_places(world):
        recs.append({"type": "LCTN", "edid": location_edid(pid), "formKey": location_key(alloc, pid),
                     "name": world.get("place", pid).name, "keywords": [keys[LOC_CLEARABLE[0]]]})
    recs.append({"type": "ACTI", "edid": "ARG_CampSpot", "formKey": fk("ARG_CampSpot", "ACTI", "rest.camp-spot"),
                 "name": "Camp", "model": CAMP_MODEL, "keywords": [keys[REST_SPOT[0]]], "activateTextOverride": "Rest"})
    recs.append({"type": "ACTI", "edid": "ARG_VasteiPileActivator",
                 "formKey": fk("ARG_VasteiPileActivator", "ACTI", "death.vastei-pile"),
                 "name": "Vastei", "model": VASTEI_MODEL, "keywords": [keys[VASTEI_PILE[0]]],
                 "activateTextOverride": "Take"})
    recs.append({
        "type": "PERK", "edid": PERK_EDID, "formKey": fk(PERK_EDID, "PERK", "hook.rest-intercept"),
        "hidden": True, "playable": False, "trait": False, "level": 0, "ranks": 1, "name": "", "description": "",
        "effects": [_choice(keys[REST_SPOT[0]], "Rest", 0), _choice(keys[VASTEI_PILE[0]], "Take Vastei", 1)],
        "fragments": {"script": FRAGMENT_SCRIPT, "entries": [{"index": 0, "name": "Fragment_0"},
                                                             {"index": 1, "name": "Fragment_1"}]},
    })
    recs += game_settings(alloc, world, scan)
    return Layer("base:life", recs)
