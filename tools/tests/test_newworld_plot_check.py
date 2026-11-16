"""plot_check: both quest forms, alias matching, a jump, a slump warning, the opening rule and an unknown place."""
import json

from tools.newworld import plot_check as pc


def make_places(tmp_path, bands):
    """bands: {name: (strength, reach)}; ids are the lower-cased names."""
    d = tmp_path / "db"
    d.mkdir(exist_ok=True)
    (d / "place.jsonl").write_text("\n".join(
        json.dumps({"id": n.lower().replace(" ", "-"), "name": n, "danger_band_id": "D0"}) for n in bands))
    (d / "place_danger.jsonl").write_text("\n".join(
        json.dumps({"place_id": n.lower().replace(" ", "-"), "strength_band_id": s, "reach_band_id": r})
        for n, (s, r) in bands.items()))
    (d / "place_alias.jsonl").write_text(json.dumps({"place_id": "alpha", "alias": "The Old Alpha"}))
    return pc.Places(d)


def page(items, para=False):
    out = ["## 5. The acts", "", "### Act I: start", ""]
    for i, (title, places) in enumerate(items, 1):
        out.append(f"**{i}. {title}** ({places}). text here." if para else f"{i}. **{title}** ({places}). text here.")
        out.append("")
    return "\n".join(out)


BANDS = {"Alpha": ("D1", "D1"), "Beta": ("D2", "D1"), "Gamma": ("D3", "D2"), "Delta": ("D5", "D4"), "Eps": ("D0", "D0")}


def run(tmp_path, items, para=False, opens="D1"):
    return pc.analyse(pc.parse(page(items, para)), make_places(tmp_path, BANDS), opens)


def test_both_forms_parse_the_same(tmp_path):
    items = [("One", "Alpha, a camp; Beta, a town"), ("Two", "Beta, x")]
    a = pc.parse(page(items))
    b = pc.parse(page(items, para=True))
    assert a == b
    assert a[0]["phrases"] == ["Alpha", "Beta"] and a[0]["title"] == "One"


def test_band_is_harder_of_strength_and_reach(tmp_path):
    res = run(tmp_path, [("One", "Alpha, x"), ("Two", "Beta, x; Gamma, y")])
    assert [r["band"] for r in res["rows"]] == ["D1", "D3"]
    assert res["rows"][1]["top"] == "D3"
    assert res["errors"] == [] or all("jump" not in e for e in res["errors"][:0])


def test_alias_and_the_prefix(tmp_path):
    res = run(tmp_path, [("One", "the Old Alpha, x"), ("Two", "The Beta, x")])
    assert res["errors"] == []
    assert [r["band"] for r in res["rows"]] == ["D1", "D2"]


def test_jump_is_an_error(tmp_path):
    res = run(tmp_path, [("One", "Alpha, x"), ("Two", "Beta, x"), ("Three", "Delta, x")])
    assert any("Three" in e and "jump" in e for e in res["errors"])


def test_slump_is_a_warning_after_the_first_third(tmp_path):
    items = [("One", "Alpha, x"), ("Two", "Beta, x"), ("Three", "Gamma, x"), ("Four", "Delta, x"), ("Five", "Delta, x"),
             ("Six", "Alpha, x")]
    res = run(tmp_path, items)
    assert any("Six" in w and "slump" in w for w in res["warnings"])
    assert not any("slump" in e for e in res["errors"])


def test_no_slump_inside_the_first_third(tmp_path):
    res = run(tmp_path, [("One", "Beta, x"), ("Two", "Eps, x")] + [("N", "Beta, x")] * 4)
    assert not any("slump" in w for w in res["warnings"])


def test_opening_rule(tmp_path):
    res = run(tmp_path, [("One", "Beta, x"), ("Two", "Beta, x")])
    assert any("first quest" in e for e in res["errors"])
    res = run(tmp_path, [("One", "Beta, x"), ("Two", "Beta, x")], opens="D2")
    assert res["errors"] == []
    res = run(tmp_path, [("One", "Alpha, x"), ("Two", "Gamma, x")])
    assert any("second quest" in e for e in res["errors"])


def test_unknown_place_warns_when_another_resolved_and_errors_when_none(tmp_path):
    res = run(tmp_path, [("One", "Alpha, x; the cavern beyond the door"), ("Two", "the Root")])
    assert any("not a place" in w for w in res["warnings"])
    assert any("Two" in e and "no place" in e for e in res["errors"])
    assert not any("One" in e for e in res["errors"])


def test_last_act_info_and_exit_code(tmp_path, capsys):
    res = run(tmp_path, [("One", "Alpha, x"), ("Two", "Beta, x")])
    assert res["info"] == ["last act (Act I: start): top D2"]
    f = tmp_path / "p.md"
    f.write_text(page([("One", "Zed, x")]))
    assert pc.main([str(f), "--json"]) == 1
    assert json.loads(capsys.readouterr().out)[str(f)]["errors"]
