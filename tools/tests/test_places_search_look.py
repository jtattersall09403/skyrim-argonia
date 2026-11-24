"""The looked-at index (tools/places/search/look.py): failed pictures are named not dropped, an interrupted status
file resumes, a query adds the look score and says which half matched with exact names still first, and the
contact sheet draws each hit or says why it could not look."""
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

FIX = Path(__file__).parent / "fixtures" / "places"
BGE = Path.home() / ".argonia" / "models" / "bge-small-en-v1.5" / "model_quantized.onnx"


@pytest.fixture
def out(tmp_path, monkeypatch):
    monkeypatch.setenv("PLACES_OUT", str(tmp_path))
    return tmp_path


def test_judge_names_empty_and_black():
    from tools.places.search import look
    bg = Image.new("RGB", (64, 64), tuple(int(x) for x in look.BG))
    assert look.judge(bg).startswith("empty")
    black = bg.copy()
    black.paste((2, 2, 2), (10, 10, 50, 50))
    assert look.judge(black).startswith("black")
    seen = bg.copy()
    seen.paste((120, 90, 40), (10, 10, 50, 50))
    assert look.judge(seen) is None


def test_status_survives_a_cut_line_and_failed_rows_are_not_looked(out):
    from tools.places.search import look
    d = look.look_dir()
    d.mkdir(parents=True)
    (d / "status.jsonl").write_text(
        json.dumps({"k": "a", "model": "m/a.nif", "ok": True, "why": None}) + "\n" +
        json.dumps({"k": "b", "model": "m/b.nif", "ok": False, "why": "unresolved texture: t.dds"}) + "\n" +
        json.dumps({"k": "c", "model": "m/c.nif", "ok": False, "why": "not found: x"}) + "\n" + '{"k": "d", "mo')
    st = look.status()
    assert set(st) == {"a", "b", "c"}
    assert look.lookable(st["a"]) and look.lookable(st["b"]) and not look.lookable(st["c"])
    assert look.model_key("M\\A.nif") == look.model_key("m/a.nif")


@pytest.fixture
def index(out):
    if not BGE.exists():
        pytest.skip("text search model not fetched")
    from tools.places.search import look
    from tools.places.search.clip import DIM
    from tools.places.search.index import Index
    Index._open.clear()
    ix = Index.open(out / "search")
    ix.update(FIX / "bases.jsonl")
    rows = [r for r in ix.rows if r.get("model")]
    target = next(r for r in rows if r["edid"] == "FxRopeCoil01")
    q = np.zeros(DIM, np.float32)
    q[0] = 1
    keys, vecs = [], []
    for r in rows:
        k = look.model_key(r["model"])
        v = np.zeros(DIM, np.float32)
        v[0], v[1 + len(keys) % (DIM - 1)] = (0.6, 0.8) if r is target else (0.2, 0.98)
        keys.append(k)
        vecs.append(v)
        p = look.thumb_path(k)
        p.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (256, 256), (100, 80, 60)).save(p)
    d = look.look_dir()
    np.save(d / "vectors.npy", np.stack(vecs).astype(np.float16))
    (d / "keys.jsonl").write_text("".join(json.dumps(k) + "\n" for k in keys))
    (d / "status.jsonl").write_text(json.dumps({"k": look.model_key(rows[0]["model"]), "model": rows[0]["model"],
                                                "ok": False, "why": "black: the model draws black"}) + "\n")
    ix.embed_look = lambda text: q
    return ix


def test_query_adds_the_look_score_and_names_the_half(index):
    hits = index.query("thing in a pile", limit=5)
    assert hits[0]["edid"] == "FxRopeCoil01" and hits[0]["matched"] == "look", hits[0]
    assert hits[0]["look"] and hits[0]["look_score"] > 0.5
    exact = index.query("FxBarrel01", limit=3)
    assert exact[0]["edid"] == "FxBarrel01" and exact[0]["matched"] == "name"


def test_sheet_draws_hits_and_says_why_not(index, out):
    from tools.places.search import sheet
    first = index.rows[0]["key"]
    p = sheet.make(None, [first, "Fixture.esm:000811", "Nope.esp:000001"], out=str(out / "s.png"))
    img = Image.open(p)
    assert img.size == (3 * sheet.CELL, sheet.CELL + sheet.CAP)
    assert img.getpixel((sheet.CELL + 128, 128)) == (100, 80, 60)
    assert img.getpixel((2 * sheet.CELL + 2, 2))[0] == 200 or img.getpixel((2 * sheet.CELL + 3, 3))[0] == 200
