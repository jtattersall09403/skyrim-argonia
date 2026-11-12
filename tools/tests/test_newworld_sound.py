"""The regions' ambient sound (tools/newworld/sound.py): every identity bed is real descriptors, neighbours differ, the
spec's sound entries are well formed and its copies sit in the atmosphere's id range."""
from __future__ import annotations

import json

from tools.newworld import identity, sound

SHEET = json.loads((sound.IDENT / "regions.json").read_text())


def test_every_bed_maps_to_descriptors():
    beds = sound.load_beds()["beds"]
    assert set(beds) == set(SHEET["sound_beds"])
    for bed, ents in beds.items():
        assert ents, bed
        for e in ents:
            plug, edid = e["sound"].split(":", 1)
            assert plug in sound.PLUGINS and edid, (bed, e)
            assert 0 < e["chance"] <= 1 and e["flags"] and e["source"], (bed, e)
    assert len({json.dumps(sorted(e["sound"] for e in ents)) for ents in beds.values()}) == len(beds)


def test_deep_hush_is_sparse_not_nothing():
    ents = sound.load_beds()["beds"]["deep-hush"]
    assert ents and max(e["chance"] for e in ents) < 0.1


def same_bed_pairs() -> list[str]:
    regs = SHEET["regions"]
    out = []
    for pair in identity.adjacency():
        a, b = pair if not isinstance(pair, str) else pair.split("|")
        sa, sb = regs[a]["sound"], regs[b]["sound"]
        if (sa["day"], sa["night"]) == (sb["day"], sb["night"]):
            out.append(f"{a}|{b}")
    return out


def test_neighbours_differ_in_day_or_night_bed():
    """Sound is one of six dimensions a pair must differ on three of (identity.py); most pairs differ in sound too."""
    same = same_bed_pairs()
    assert len(same) <= 0.15 * len(identity.adjacency()), same


def test_spec_sounds_well_formed():
    ents, copies = sound.sound_spec(SHEET["regions"])
    assert set(ents) == set(SHEET["regions"])
    edids = {c["edid"] for c in copies}
    ids = [c["formid"] for c in copies]
    assert len(ids) == len(set(ids)) and len(edids) == len(copies)
    assert all(sound.COPY_BASE <= i < sound.COPY_LIMIT for i in ids)
    assert all(c["gate"] in ("day", "night") and ":" in c["copy"] for c in copies)
    for rid, lst in ents.items():
        assert lst, rid
        for e in lst:
            assert e["sound"].startswith("ANW:") and e["sound"][4:] in edids or ":" in e["sound"] and not e["sound"].startswith("ANW:")
            assert e["flags"] and 0 < e["chance"] <= 1
    # an hourless descriptor is only ever used through our copy; a gated one keeps its own hours
    beds = sound.load_beds()["beds"]
    hourless = {e["sound"] for b in beds.values() for e in b if not e["hours"]}
    assert not hourless & {e["sound"] for lst in ents.values() for e in lst}
