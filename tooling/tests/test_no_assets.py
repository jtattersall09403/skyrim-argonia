import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "guards"))
import no_assets as g  # noqa: E402


def refused(rel, data, allow=()):
    return g.check_file(rel, data, set(allow))


def test_one_byte_nif_refused():
    assert refused("x.nif", b"x")


@pytest.mark.parametrize("head", [b"TES4....", b"BSA\0xx", b"DDS xx", b"\x57\xe0\xe0\x57", b"FSB5xx",
                                  b"BND4xx", b"DCX\0xx", b"RIFF\0\0\0\0XWMA", b"Gamebryo File Format, V"])
def test_magic_refused_under_a_harmless_name(head):
    assert refused("notes.txt", head)


def test_wav_riff_without_xwma_is_only_an_extension_case():
    assert not refused("a.txt", b"RIFF\0\0\0\0WAVE")


def test_big_file_needs_allowlist():
    big = b"a" * 1_000_001
    assert refused("data.json", big)
    assert not refused("data.json", big, ["data.json"])


@pytest.mark.parametrize("text", ["undefined8 x;", "call __thiscall", "FUN_140abcdef()", "DAT_1234abcd", "IDA Pro"])
def test_decompiler_text_refused(text):
    assert refused("a.md", text.encode())


def test_plain_text_passes():
    assert not refused("README.md", b"hello FUN_12 world")


def test_staged_and_tree_modes_in_a_real_repo(tmp_path):
    def run(*a):
        subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)
    run("init", "-q")
    (tmp_path / "TES4_plugin.txt").write_bytes(b"TES4 header")
    (tmp_path / "ok.md").write_text("fine")
    run("add", "-A")
    assert any("TES4_plugin.txt" in b for b in g.scan("staged", tmp_path))
    assert not any("ok.md" in b for b in g.scan("tree", tmp_path))
    assert any("TES4_plugin.txt" in b for b in g.scan("tree", tmp_path))


def test_markdown_may_name_signatures_in_inline_code_only():
    assert not refused("a.md", b"we refuse `undefined8` and `FUN_140abcdef`")
    assert refused("a.md", b"```\nundefined8 x;\n```")
