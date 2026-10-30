"""L1/L2: the core rules' generated tables (G11.2) and the rule sources that read them.

- the committed headers are what the tables generate, and a changed row makes them stale;
- no rule module source holds a numeric literal other than 0 or 1 (every formula constant is generated);
- every condition in the world fits its term's shape (arity and argument kinds), the C++ check's twin.
"""
from __future__ import annotations

import re

import pytest

from tools.argonia_world import core_tables, db

CORE = core_tables.REPO / "skse" / "core"
# The rule modules (native map §6.1). The co-save byte layer (cosave, families) is encoding, not formulas.
RULES = ["curve", "sheet", "effects", "carriers", "progression", "sitting", "rest", "death", "respawn", "conditions",
         "disposition", "journal", "items", "combat"]
LITERAL = re.compile(r"(?<![\w.])(\d+\.?\d*(?:[eE][-+]?\d+)?|\.\d+)(?![\w.])")
ALLOWED = {"0", "1", "0.0", "1.0"}


@pytest.fixture(scope="module")
def world():
    return db.open()


def test_headers_are_current(world):
    assert core_tables.stale(core_tables.render(world)) == []


def test_a_changed_row_makes_them_stale(world):
    world.update("core_constant", "k_exponent", value=1.7)  # in memory only; never saved
    try:
        diff = core_tables.stale(core_tables.render(world))
    finally:
        world.update("core_constant", "k_exponent", value=1.6)
    assert any("k_exponent = 1.7" in line for line in diff)


def strip(source: str) -> str:
    """C++ without comments and string or character literals."""
    source = re.sub(r"/\*.*?\*/", " ", source, flags=re.S)
    source = re.sub(r"//[^\n]*", " ", source)
    return re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '""', source)


def literals(path) -> list[str]:
    hits = []
    for n, line in enumerate(strip(path.read_text(encoding="utf-8")).splitlines(), 1):
        hits += [f"{path.relative_to(CORE)}:{n}: {m}" for m in LITERAL.findall(line) if m not in ALLOWED]
    return hits


def test_no_formula_constant_in_rule_sources():
    files = [CORE / "src" / f"{m}.cpp" for m in RULES] + [CORE / "include" / "argonia" / "core" / f"{m}.h"
                                                          for m in RULES]
    assert all(f.exists() for f in files)
    assert [h for f in files for h in literals(f)] == []


def test_the_literal_scan_sees_a_constant():
    text = (CORE / "src" / "curve.cpp").read_text(encoding="utf-8").replace("c::k_exponent", "1.6")
    text += '\n// 40 in a comment\nconst char* s = "x 7";\nstd::uint8_t u;\n'
    hits = [m for line in strip(text).splitlines() for m in LITERAL.findall(line) if m not in ALLOWED]
    assert hits == ["1.6"]  # the typed constant, not the comment, the string or the type name


def test_every_world_condition_fits_its_shape(world):
    specs = {}
    for r in world.query("SELECT term, ord, kind, optional FROM condition_shape_arg ORDER BY term, ord"):
        specs.setdefault(r["term"], []).append((r["kind"], bool(r["optional"])))
    values = {}
    for r in world.query("SELECT term, value FROM condition_shape_value"):
        values.setdefault(r["term"], set()).add(r["value"])
    ops = set(world.values("SELECT id FROM condition_op"))
    shape = {r["term"]: r["shape"] for r in world.query("SELECT term, shape FROM condition_shape")}
    args = {}
    for r in world.query("SELECT condition_id, ord, value FROM condition_arg ORDER BY condition_id, ord"):
        args.setdefault(r["condition_id"], []).append(r["value"])
    kids = {}
    for r in world.query("SELECT parent_id FROM condition WHERE parent_id IS NOT NULL"):
        kids[r["parent_id"]] = kids.get(r["parent_id"], 0) + 1
    bad = []
    for c in world.query("SELECT id, term FROM condition"):
        t, a = c["term"], args.get(c["id"], [])
        if shape[t] in ("all", "any", "not"):
            if a or (shape[t] == "not" and kids.get(c["id"], 0) != 1):
                bad.append(f"{c['id']}: {t} with {len(a)} args, {kids.get(c['id'], 0)} children")
            continue
        sp = specs.get(t, [])
        need = sum(1 for _, o in sp if not o)
        if not need <= len(a) <= len(sp):
            bad.append(f"{c['id']}: {t} takes {need}-{len(sp)} args, has {len(a)}")
            continue
        for (kind, _), v in zip(sp, a):
            ok = {"id": isinstance(v, str) and v != "", "int": isinstance(v, int) and not isinstance(v, bool),
                  "bool": v in (0, 1, True, False), "op": v in ops,
                  "enum": isinstance(v, str) and (t not in values or v in values[t])}[kind]
            if not ok:
                bad.append(f"{c['id']}: {t} argument {v!r} is not a {kind}")
    assert bad == []


def test_ident_escapes_keywords():
    assert core_tables.ident("not") == "not_"
    assert core_tables.ident("sap-speaker") == "sap_speaker"
    assert core_tables.num(5) == "5.0" and core_tables.num(0.0065) == "0.0065"
