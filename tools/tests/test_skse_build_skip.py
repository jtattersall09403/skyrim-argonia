import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skse_stamp import DLLS, can_skip, make_stamp, parse_probe

S = make_stamp("abc123\n", "windows-dev")
BOTH = list(DLLS)


def test_match_skips():
    assert S == "abc123:windows-dev"
    assert can_skip(S, S, BOTH, False)


def test_mismatch_builds():
    assert not can_skip(S, make_stamp("def456", "windows-dev"), BOTH, False)
    assert not can_skip(S, make_stamp("abc123", "windows-release"), BOTH, False)


def test_missing_stamp_builds():
    assert not can_skip(S, None, BOTH, False)
    assert not can_skip(S, "", BOTH, False)


def test_missing_dll_builds():
    assert not can_skip(S, S, ["ArgoniaCore.dll"], False)
    assert not can_skip(S, S, [], False)


def test_dirty_never_skips():
    assert not can_skip(S, S, BOTH, True)


def test_probe_parse():
    stamp, dlls = parse_probe("stamp=abc123:windows-dev\r\ndll=ArgoniaCore.dll\r\ndll=ArgoniaBridge.dll\r\n")
    assert can_skip(S, stamp, dlls, False)
    assert not can_skip(S, *parse_probe("dll=ArgoniaCore.dll\n"), False)
