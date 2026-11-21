"""`look <place> versus <other>`: the same five views of both places on one sheet."""
import json

from PIL import Image

from tools.places.look import versus


def test_versus_takes_the_same_views_of_both_places_onto_one_sheet(tmp_path):
    for pid, a in (("a", [100, 200]), ("b", [-300, 400])):
        (tmp_path / pid).mkdir()
        (tmp_path / pid / "place.json").write_text(json.dumps({"fit": {"anchor": a}}))
    img = tmp_path / "v.png"
    Image.new("RGB", (64, 48), "red").save(img)
    calls = []

    def call(p, verb, args):
        calls.append((p, verb, args))
        return {"png": str(img), "capture": "good"}
    out = versus.run("a", "b", call, places=tmp_path, out_dir=tmp_path / "out")
    assert [c[2][1:] for c in calls[:5]] == [c[2][1:] for c in calls[5:]]      # the same views for both
    assert calls[0][2][0] == "100,200" and calls[5][2][0] == "-300,400"
    w, h = Image.open(out["png"]).size
    assert w == versus.TILE[0] * 5 and h == (versus.TILE[1] + 24) * 2
