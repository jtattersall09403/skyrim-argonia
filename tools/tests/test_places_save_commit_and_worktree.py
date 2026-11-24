"""A named save that carries needs changes commits the story digest with them (studio server flush_needs), and a
look daemon in a lane's worktree reads the enclosing tree's asset catalogue (draft_bundle._catalogue_path)."""
from types import SimpleNamespace

import pytest

pytest.importorskip("aiohttp")
from tools.places.studio import server  # noqa: E402


def test_flush_needs_carries_the_regenerated_digest(tmp_path, monkeypatch):
    from tools.argonia_world import db
    from tools.newworld import needsdb, story_digest

    root = tmp_path
    needs_dir = root / "newworld" / "sources" / "needs"
    needs_dir.mkdir(parents=True)
    (needs_dir / "p1.changed.jsonl").write_text("{}\n")
    tables = root / db.DB_DIR
    tables.mkdir(parents=True)
    for t in needsdb.TABLES:
        (tables / f"{t}.jsonl").write_text("")
    out = root / "story" / "design" / "world"
    generated = []

    def fake_generate(*a, **k):
        (out / "regions").mkdir(parents=True, exist_ok=True)
        for f in ("index.md", "province.md", "people.md", "regions/r1.md"):
            (out / f).write_text("x\n")
        (out / "01-lore-note.md").write_text("by hand\n")
        generated.append(True)

    monkeypatch.setattr(server, "ROOT", root)
    monkeypatch.setattr(server, "record", lambda pid: pid)
    monkeypatch.setattr(server.needs, "flush_held", lambda *a, **k: True)
    monkeypatch.setattr(needsdb, "reload", lambda: SimpleNamespace(root=str(root)))
    monkeypatch.setattr(story_digest, "OUT", out)
    monkeypatch.setattr(story_digest, "generate", fake_generate)
    cfg = SimpleNamespace(sources=root / "newworld" / "sources", out=tmp_path / "saves")

    paths = server.flush_needs(cfg, "p1", "named")

    assert generated
    assert "newworld/sources/needs/p1.changed.jsonl" in paths
    for f in ("index.md", "province.md", "people.md", "regions/r1.md"):
        assert f"story/design/world/{f}" in paths
    assert "story/design/world/01-lore-note.md" not in paths


def test_a_worktree_reads_the_enclosing_trees_catalogue(tmp_path):
    from tools.places import draft_bundle
    main = tmp_path / "main"
    cat = main / "out" / "places" / "catalogue" / "bases.jsonl"
    cat.parent.mkdir(parents=True)
    cat.write_text("")
    lane = main / ".claude" / "worktrees" / "lane"
    lane.mkdir(parents=True)
    assert draft_bundle._catalogue_path(lane) == cat
    own = lane / "out" / "places" / "catalogue" / "bases.jsonl"
    own.parent.mkdir(parents=True)
    own.write_text("")
    assert draft_bundle._catalogue_path(lane) == own


def test_a_worktree_reads_source_bundles_from_the_enclosing_tree(tmp_path):
    """A lane's worktree has no bundles of its own: promises and the draft rules read the main tree's source bundles
    (a carried room's own refs are evidence there too), never an empty folder."""
    from tools.places import draft_bundle
    b = tmp_path / "main" / "out" / "places" / "bundles"
    b.mkdir(parents=True)
    lane = tmp_path / "main" / ".claude" / "worktrees" / "lane"
    lane.mkdir(parents=True)
    assert draft_bundle.read_bundles(lane) == b
