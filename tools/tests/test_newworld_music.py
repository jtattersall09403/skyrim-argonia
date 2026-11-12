"""The soundtrack's data: every slot has its reference and feel, prompts name no source, and the music records'
data (records.json) names only real slots, covers every atmosphere class and fits its idspace row."""
import json
import re
from pathlib import Path

from tools.newworld import idspace

REPO = Path(__file__).resolve().parents[2]
MUSIC = REPO / "newworld/sources/music"
PIECES = json.loads((MUSIC / "pieces.json").read_text())
RECORDS = json.loads((MUSIC / "records.json").read_text())
CS = (REPO / "tools/ArgoniaPlugin/NewWorldMusic.cs").read_text()
SLOTS = [p["id"] for p in PIECES["pieces"]]


def test_every_piece_names_its_reference_and_feel():
    for p in PIECES["pieces"]:
        if "excerpt" in p:   # cut from another slot's file: that slot carries the reference
            assert len(p["feel"]) > 60, p["id"]
            continue
        assert p["reference"]["title"] and p["reference"]["length"], p["id"]
        assert len(p["feel"]) > 60, p["id"]


def test_prompts_never_name_the_reference():
    banned = {"morrowind", "soule", "vvardenfell", "vivec", "dunmer", "nerevar", "elder scrolls", "bethesda"}
    # a one-word title ("Ambush", "Triumphant") is an ordinary word a brief may use; longer titles never appear
    titles = {t for p in PIECES["pieces"] if "reference" in p and " " in (t := p["reference"]["title"].lower())}
    for p in PIECES["pieces"]:
        prompt = (p["axes"] + " " + PIECES["style"]).lower()
        assert not [w for w in banned | titles if w in prompt], p["id"]


def test_records_name_only_slots_and_cover_every_class():
    named = [s for k in ("night", "combat", "boss", "death", "levelup") for s in RECORDS[k]]
    assert "discovery" not in RECORDS and "discovery" not in CS.split("Defaults")[1].split("];")[0]   # Skyrim's own (owner, 2026-11-12)
    named += [s for v in RECORDS["day"].values() for s in v]
    assert set(named) <= set(SLOTS)
    classes = {v[0] for v in json.loads((REPO / "newworld/sources/atmosphere/regions.json").read_text())["regions"].values()}
    assert classes <= set(RECORDS["day"]) and RECORDS["world"] in RECORDS["day"]
    assert all(RECORDS["day"].values()) and RECORDS["night"] and RECORDS["combat"]


def test_ids_fit_the_music_row():
    lo, hi = idspace.SPAN["music"]
    const = {k: int(v, 16) for k, v in re.findall(r"(IdTrack|IdNight|IdType|IdEnd) = 0x([0-9A-F]+)", CS)}
    assert const["IdTrack"] == lo and const["IdEnd"] == hi
    assert const["IdTrack"] + len(SLOTS) <= const["IdNight"] and const["IdNight"] + len(SLOTS) <= const["IdType"]
    assert const["IdType"] + len(RECORDS["day"]) - 1 <= hi


def test_an_excerpt_is_cut_from_another_slot_with_clean_fades():
    import sys
    sys.path.insert(0, str(REPO / "tools/newworld/music"))
    import soundtrack
    for p in PIECES["pieces"]:
        for ex in [p["excerpt"], *p.get("excerpt_alternatives", [])] if "excerpt" in p else []:
            assert ex["of"] in SLOTS and ex["of"] != p["id"] and "excerpt" not in next(q for q in PIECES["pieces"] if q["id"] == ex["of"])
            assert 17.5 <= ex["end_s"] - ex["start_s"] <= 20.5 and 0.03 <= ex["fade_in_s"] <= 0.08 and 2 <= ex["fade_out_s"] <= 4.5  # Skyrim's: 18.7-19.3 s
    args = soundtrack.excerpt_filter({"of": "theme", "start_s": 119.6, "end_s": 138.6, "fade_in_s": 0.05, "fade_out_s": 3.5})
    assert args[:4] == ["-ss", "119.6", "-t", "19.0"]
    assert "afade=t=in:st=0:d=0.05" in args[5] and "afade=t=out:st=15.5:d=3.5" in args[5] and "loudnorm" in args[5]
