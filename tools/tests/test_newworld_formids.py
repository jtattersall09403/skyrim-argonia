"""The world plugin's form id registry (newworld/sources/world_formids.json, ArgoniaPlugin FormIds.cs): the committed
file is whole and in its one form, its blocks stand clear of the ids placed by formula, and the registry's rules hold
(`formids selftest`: a re-place, a land texture or a blend more, a full block, the file's bytes)."""
import json
import os
import re
import subprocess
from pathlib import Path

import pytest

from tools.newworld import idspace

REPO = Path(__file__).resolve().parents[2]
FILE = REPO / "newworld/sources/world_formids.json"
DOTNET = Path.home() / ".dotnet"
# ids placed by formula (tools/newworld/idspace.py: every allocator's range): no block may reach into them
FORMULA = {k: v for k, v in idspace.SPAN.items() if k not in idspace.REGISTRY and k != "seeded"}
NAME = re.compile(r"(copy:[0-9A-F]{6}:.+\.es[pml]|alttex:[0-9A-F]{6}:.+\.es[pml]:\d+|ltex:\S+|watr:\S+|blend:[^|]+\|[^|]*\|[\d,]+|region:[\w-]+)")


def span(s: str) -> tuple[int, int]:
    a, b = s.split("-")
    return int(a, 16), int(b, 16)


def test_the_committed_registry_is_in_its_one_form():
    text = FILE.read_text(encoding="utf-8")
    doc = json.loads(text)
    assert text == json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"   # sorted, one entry a line
    assert set(doc) == {"blocks", "ids", "seeded"}


def test_every_name_holds_one_id_in_its_kinds_block_or_the_seeded_range():
    doc = json.loads(FILE.read_text(encoding="utf-8"))
    seeded, held, names = span(doc["seeded"]), {}, set()
    for kind, rows in doc["ids"].items():
        lo, hi = span(doc["blocks"][kind])
        for name, hx in rows.items():
            assert re.fullmatch(r"0x[0-9A-F]{6}", hx) and NAME.fullmatch(name), (name, hx)
            i = int(hx, 16)
            assert lo <= i <= hi or seeded[0] <= i <= seeded[1], (kind, name, hx)
            assert i not in held and name not in names, f"{hx} is held by {held.get(i)} and {name}"
            held[i] = name
            names.add(name)
    assert len(held) > 7000   # the world's ground, water, bases and regions as first registered


def test_no_block_reaches_into_another_or_into_the_ids_placed_by_formula():
    doc = json.loads(FILE.read_text(encoding="utf-8"))
    spans = {**{k: span(v) for k, v in doc["blocks"].items()}, "seeded": span(doc["seeded"]), **FORMULA}
    order = sorted(spans.items(), key=lambda kv: kv[1])
    for (a, (_, a1)), (b, (b0, _)) in zip(order, order[1:]):
        assert a1 < b0, f"{a} and {b} overlap"
    assert max(hi for _, hi in spans.values()) <= 0xFFFFFF


def _env():
    return {**os.environ, "DOTNET_ROOT": str(DOTNET), "PATH": f"{DOTNET}:{os.environ['PATH']}",
            "DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_NOLOGO": "1"}


@pytest.fixture(scope="module")
def tool():
    if not DOTNET.exists():
        pytest.skip("~/.dotnet is absent")
    out = REPO / "out" / "tools" / "ArgoniaPlugin"
    b = subprocess.run(["dotnet", "build", "-c", "Release", "-o", str(out), "tools/ArgoniaPlugin"], cwd=REPO, env=_env(),
                       capture_output=True, text=True)
    assert b.returncode == 0, b.stdout[-2000:]
    return out / "ArgoniaPlugin.dll"


def test_selftest_a_re_place_or_a_new_record_moves_no_id_and_a_full_block_stops(tool, tmp_path):
    r = subprocess.run(["dotnet", str(tool), "formids", "selftest", str(tmp_path)], cwd=REPO, env=_env(), capture_output=True, text=True)
    assert r.returncode == 0 and "PASS" in r.stdout, r.stdout + r.stderr
    made = (tmp_path / "one.json").read_text()          # the writer's own bytes are the committed file's form
    assert made == json.dumps(json.loads(made), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
