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
        assert p["reference"]["title"] and p["reference"]["length"], p["id"]
        assert len(p["feel"]) > 60, p["id"]


def test_prompts_never_name_the_reference():
    banned = {"morrowind", "soule", "vvardenfell", "vivec", "dunmer", "nerevar", "elder scrolls", "bethesda"}
    # a one-word title ("Ambush", "Triumphant") is an ordinary word a brief may use; longer titles never appear
    titles = {t for p in PIECES["pieces"] if " " in (t := p["reference"]["title"].lower())}
    for p in PIECES["pieces"]:
        prompt = (p["axes"] + " " + PIECES["style"]).lower()
        assert not [w for w in banned | titles if w in prompt], p["id"]


def test_records_name_only_slots_and_cover_every_class():
    named = [s for k in ("night", "combat", "boss", "death", "levelup", "discovery") for s in RECORDS[k]]
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
