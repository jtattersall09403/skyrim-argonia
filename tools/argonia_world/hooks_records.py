"""The generated records of the native hooks (native map P3, docs/research/native-map.md §2): the dialogue intercept.

A player perk whose Activate entry point (Run Immediately + Replace Default) runs the one-line Papyrus fragment
`ARG_PRKF_DialogueIntercept` on every Argonia speaker, marked by the keyword `ARG_Speaker` that each speaker's NPC_
record carries (2.W5). Every field is plain and resolved; ArgoniaGen's PerkRecords.cs makes no choices.
"""
from __future__ import annotations

from tools.argonia_world.formids import Allocator
from tools.argonia_world.intermediate import Layer

SPEAKER_EDID = "ARG_Speaker"
PERK_EDID = "ARG_Perk_DialogueIntercept"
FRAGMENT_SCRIPT = "ARG_PRKF_DialogueIntercept"


def layer(alloc: Allocator) -> Layer:
    kw = alloc.form_key(SPEAKER_EDID, "KYWD", "hook.speaker")
    perk = {
        "type": "PERK", "edid": PERK_EDID, "formKey": alloc.form_key(PERK_EDID, "PERK", "hook.dialogue-intercept"),
        "hidden": True, "playable": False, "trait": False, "level": 0, "ranks": 1, "name": "", "description": "",
        "effects": [{
            "entryPoint": "Activate", "function": "AddActivateChoice", "rank": 0, "priority": 0, "tabCount": 2,
            "conditions": [{"tab": 1, "function": "HasKeyword", "keyword": kw, "op": "EqualTo", "value": 1}],
            "buttonLabel": "Speak", "flags": ["RunImmediately", "ReplaceDefault"], "fragment": 0,
        }],
        "fragments": {"script": FRAGMENT_SCRIPT, "entries": [{"index": 0, "name": "Fragment_0"}]},
    }
    return Layer("base:hooks", [{"type": "KYWD", "edid": SPEAKER_EDID, "formKey": kw}, perk])
