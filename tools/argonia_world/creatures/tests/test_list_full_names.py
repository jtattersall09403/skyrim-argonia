"""A journey's `among` is the FULL names of a list's forms, as the game reports them, not our kind names."""
from tools.argonia_world.creatures import journey, levelled


class FakeW:
    def query(self, sql, *args):
        assert args == ("lvln.x.D1.shore",)
        return [{"kind": "Poison Frog", "form_key": "000001:A.esp"}, {"kind": "Poison Frog", "form_key": "000002:A.esp"},
                {"kind": "Bird", "form_key": "000003:A.esp"}]


def test_among_is_the_forms_full_names(monkeypatch):
    names = {"000001:A.esp": "Blue Poison Frog", "000002:A.esp": "Red Poison Frog", "000003:A.esp": ""}
    monkeypatch.setattr(levelled, "full_name", names.__getitem__)
    assert journey.list_kinds(FakeW(), "lvln.x.D1.shore") == ["Bird", "Blue Poison Frog", "Red Poison Frog"]  # empty FULL keeps our kind
    assert journey.list_forms(FakeW(), "lvln.x.D1.shore")[-1] == ("Bird", "Bird")
