"""Place records keep their researched population (decision 0040); record_check is the consistency checker's
internal and ground families, never a second set of rules."""
import glob
import json
from pathlib import Path

from tools.newworld import build_db
from tools.newworld import consistency as C
from tools.newworld import record_check as rc
from tools.tests.test_newworld_consistency import ctx

ROOT = Path(__file__).resolve().parents[2]


def test_water_pixel_is_the_pixel_the_point_lies_in():
    assert build_db.water_pixel(1789.9, 2124.2) == (1789, 2124)


def test_the_database_keeps_each_record_s_population():
    """build_db writes the research estimate; a source's people count never replaces it."""
    research = {r["id"]: r["population"] for fn in glob.glob(str(ROOT / "newworld/sources/research/places/*.json"))
                for r in json.loads(Path(fn).read_text())["records"]}
    built = {p["id"]: p["population"] for p in
             (json.loads(line) for line in (ROOT / "newworld/story/data/db/place.jsonl").read_text().splitlines()
              if line.strip())}
    assert {k: v for k, v in built.items() if research.get(k) != v} == {}
    assert not hasattr(build_db, "source_match_population")


def test_record_check_finds_what_the_consistency_checker_finds():
    c = ctx()
    c["danger"]["a"]["disposition_id"] = "hostile"
    c["places"]["b"]["population"] = 15
    want = C.Report()
    for fam in rc.FAMILIES:
        C.FAMILIES[fam](c, want)
    got = rc.faults(c)
    assert got and [(f.place, f.cause) for f in got] == [(f.place, f.cause) for f in want.items]
    assert {f.place for f in rc.faults(c, ["a"])} == {"a"}
    assert rc.faults(ctx()) == []
