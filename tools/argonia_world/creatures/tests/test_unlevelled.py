"""Decision 0035's L1 check fails on each thing it forbids (checks.unlevelled over records.document)."""
from tools.argonia_world.creatures import checks, records

SCALING = "000823:King of the Murkmire.esp"


class W:
    def query(self, sql, *a):
        if "danger_band_level" in sql:
            return [{"band": "D1", "level": 4}]
        return [{"form_key": SCALING}]


def _doc(entries, zone=(4, 4), level=4, actors=True):
    return {"lists": [{"edid": "L", "entries": entries}],
            "zones": [{"edid": "Z", "minLevel": zone[0], "maxLevel": zone[1]}],
            "templates": [{"edid": "T", "level": level}],
            "actors": [{"source": SCALING, "edid": "ARG_Cr_Wamasu01_D1"}] if actors else []}


def _run(monkeypatch, doc):
    monkeypatch.setattr(records, "document", lambda w: doc)
    monkeypatch.setattr(records, "fixed_forms", lambda w: [SCALING])
    return checks.unlevelled(W())["fail"]


def test_green(monkeypatch):
    assert _run(monkeypatch, _doc([["0D4000:ArgoniaWorld.esm", 1, 1]])) is None


def test_reds(monkeypatch):
    assert _run(monkeypatch, _doc([["0D4000:ArgoniaWorld.esm", 4, 1]]))  # an entry above level 1
    assert _run(monkeypatch, _doc([[SCALING, 1, 1]]))  # the scaling mod form itself
    assert _run(monkeypatch, _doc([], zone=(4, 8)))  # zone min <> max
    assert _run(monkeypatch, _doc([], level=7))  # a template off its band's level
    assert _run(monkeypatch, _doc([], actors=False))  # no fixed copy
