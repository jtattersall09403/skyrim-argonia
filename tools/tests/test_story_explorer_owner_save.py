"""The owner's studio save commits though the story explorer is behind (its republish owed to the next agent turn);
any other commit is still refused until it is republished."""
from tools.newworld import story_explorer as SE


def test_owner_save_passes_and_an_agents_commit_does_not(monkeypatch, capsys):
    monkeypatch.setattr(SE, "check", lambda *a, **k: "story explorer behind: republish it")
    monkeypatch.delenv("STUDIO_OWNER_SAVE", raising=False)
    assert SE.main(["check"]) == 1
    monkeypatch.setenv("STUDIO_OWNER_SAVE", "1")
    assert SE.main(["check"]) == 0
    assert "owed" in capsys.readouterr().out
