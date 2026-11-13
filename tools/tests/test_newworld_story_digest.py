"""The story digest (tools/newworld/story_digest.py): it runs on the real database, covers every place, region and
culture, cites the rows it rests on, and the committed digest is the generator's current output."""
import re

import pytest

from tools.argonia_world import db
from tools.newworld import frame as f
from tools.newworld import story_digest as sd

COMMITTED = sd.OUT


@pytest.fixture(scope="module")
def made(tmp_path_factory):
    out = tmp_path_factory.mktemp("world")
    counts = sd.generate(out, today="2000-01-01")
    return out, counts


def rows(sql):
    return [dict(r) for r in db.open(f.ROOT).query(sql)]


def test_every_place_region_and_culture_appears(made):
    out, counts = made
    places = rows("SELECT id, name, region_id FROM place")
    regions = rows("SELECT id, name FROM region")
    cultures = rows("SELECT id, name FROM culture")
    assert counts["places"] == len(places) and counts["regions"] == len(regions)
    assert counts["cultures"] == len(cultures)
    province = (out / "province.md").read_text()
    for r in regions:
        assert (out / "regions" / f"{r['id']}.md").exists(), r["id"]
        assert r["name"] in province
    for c in cultures:
        assert f"culture:{c['id']}" in province, c["id"]
    for p in places:
        assert f"<!-- place:{p['id']} -->" in (out / "regions" / f"{p['region_id']}.md").read_text(), p["id"]
        assert f"| {p['name'].replace('|', '/')} |" in province, p["id"]


def test_every_place_says_what_it_promises_is_built_from_and_whether_built(made):
    out, _ = made
    for p in rows("SELECT id, region_id FROM place"):
        text = (out / "regions" / f"{p['region_id']}.md").read_text()
        sec = text.split(f"<!-- place:{p['id']} -->", 1)[1].split("\n### ", 1)[0]
        assert "It promises the player" in sec, p["id"]
        assert "to be built from" in sec or "will be built from" in sec, p["id"]
    assert "It is drafted" in (out / "regions" / "murkwood.md").read_text()


def test_every_cited_place_note_exists(made):
    out, _ = made
    notes = {(r["place_id"], r["aspect_id"]) for r in rows("SELECT place_id, aspect_id FROM place_note")}
    cited = set()
    for fp in (out / "regions").glob("*.md"):
        cited |= set(re.findall(r"place_note:([\w-]+)/(\w+)", fp.read_text()))
    assert cited and cited <= notes


def test_hooks_quote_the_hooks_notes_whole(made):
    out, counts = made
    assert counts["hooks"] >= len(rows("SELECT 1 FROM place_note WHERE aspect_id = 'hooks'"))
    text = (out / "regions" / "murkwood.md").read_text()
    assert "The assembly will not speak of its sour spring in open session." in text


def test_no_em_dashes_in_what_the_generator_writes(made):
    out, _ = made
    for fp in [*out.glob("*.md"), *(out / "regions").glob("*.md")]:
        assert "—" not in fp.read_text(), fp.name


def test_the_committed_digest_is_current(made):
    out, _ = made
    if not (COMMITTED / "index.md").exists():
        pytest.skip("no committed digest")
    for fp in [*out.glob("*.md"), *(out / "regions").glob("*.md")]:
        rel = fp.relative_to(out)
        want = fp.read_text()
        have = (COMMITTED / rel).read_text()
        if rel.name == "index.md":       # the date and the revision move with every regeneration
            want, have = (re.sub(r"Made \S+ from database revision `\w+`", "", t) for t in (want, have))
        assert have == want, f"{rel} is stale: rerun python3 -m tools.newworld.story_digest"
