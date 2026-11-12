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
    # level-up: the UI sound plays our sting; the level-up music type adds nothing in the new world
    assert RECORDS["levelup"] == [] and RECORDS["levelup_sound"] in SLOTS and "057B44" in CS
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
            # Skyrim's level-up: the UI sound about 4 s + 4 s, the music 18.7-19.3 s
            length = (7, 9) if p["id"] == "sting-levelup" else (17.5, 20.5)
            assert length[0] <= ex["end_s"] - ex["start_s"] <= length[1], p["id"]
            assert 0.03 <= ex["fade_in_s"] <= 0.08 and 3 <= ex["fade_out_s"] <= 5
    args = soundtrack.excerpt_filter({"of": "theme", "start_s": 129.5, "end_s": 137.5, "fade_in_s": 0.05, "fade_out_s": 4.0})
    assert args[1] .startswith("afade=t=in:st=0:d=0.05,afade=t=out:st=4.0:d=4.0,loudnorm")
    assert soundtrack.excerpt_input({"start_s": 129.5, "end_s": 137.5}) == ["-ss", "129.5", "-t", "8.0"]


def test_a_cut_excerpt_is_audible_and_silence_is_refused(tmp_path):
    """The seek is on the input, so the fades run on the cut's own clock; an output-side seek came out silent."""
    import shutil
    import subprocess
    import sys
    import pytest
    sys.path.insert(0, str(REPO / "tools/newworld/music"))
    import soundtrack
    if not shutil.which(soundtrack.FFMPEG):
        pytest.skip("no ffmpeg")
    src = tmp_path / "src.wav"
    subprocess.run([soundtrack.FFMPEG, "-v", "error", "-f", "lavfi", "-i", "anoisesrc=color=pink:duration=30",
                    str(src)], check=True)
    out = tmp_path / "cut.wav"
    soundtrack.convert(src, out, None, {"start_s": 20, "end_s": 28, "fade_in_s": 0.05, "fade_out_s": 4})
    assert soundtrack.audible(*soundtrack.loudness(out))
    assert not soundtrack.audible(-70.0, -200.0)
