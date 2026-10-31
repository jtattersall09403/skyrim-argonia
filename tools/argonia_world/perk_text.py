"""The skill-tree perks' own wording (1.12 §4; decision 0012): one PERK override per `perk_text` row.

Every perk a player can meet in a skill's tree (Wind UI's stats pane, the level-up menu) names and describes itself in
vanilla Skyrim's words; the rows hold ours: same meaning, every number unchanged. The override carries the master's
record whole (ArgoniaGen's PerkRecords.Override) with only the name and description replaced. Nothing here holds
vanilla text: a row's `formkey` is the master's FormKey and its words are ours.
"""
from __future__ import annotations

from tools.argonia_world.intermediate import Layer


def layer(world) -> Layer:
    recs = [{"type": "PERK", "override": True, "formKey": r.formkey, "edid": r.formkey, "name": r.name,
             "description": r.description} for r in world.rows("perk_text")]
    return Layer("patch:perk-text", recs)
