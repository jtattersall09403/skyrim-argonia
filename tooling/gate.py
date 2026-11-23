"""The scoped gate: run only the checks a change can reach.

`make check` runs this and runs only what the change reaches; a landing runs `make check GATE_BASE=origin/main`.
`make check-all WHY=deploy|phase-close` runs every stage and every test, and only for those two occasions: it, and
`gate.py run --all`, refuse without one of them (FULL_WHY).

    python tooling/gate.py run              # the working tree and index against HEAD (before a commit)
    python tooling/gate.py run --base origin/main   # everything on this branch since main (a lane landing)
    python tooling/gate.py plan [--base REF] [paths...]   # print what would run, run nothing
    python tooling/gate.py run --all --why deploy|phase-close   # the whole gate

How a change picks its checks (the map is tooling/gate_map.toml, one comment per rule):
  - the no-assets guard and ruff always run (seconds);
  - a pytest file runs when a changed path is in its import closure inside the repo (tools.*, tooling.*), or is a
    repo path its code names: a string such as "story/data/x.json" or "tools.places.studio", or a chain such as
    REPO / "newworld" / "sources" (a named directory covers everything under it). The closure follows names, not
    whole files: `from m import f` reaches what m runs on import and what f's body reaches (so a lazy import inside
    one function reaches only that function's callers), `import m` used as `m.f` reaches f the same way, and a path
    held in a module-level name (DB = REPO / "x" / "db") reaches only the code that uses the name;
  - a slow suite listed in the map's `per_test_reach` (the studio's browser tests) runs test by test: its reach
    module declares the core every test stands on and each test's own files (`per_test`);
  - the make stages adaptation, questtext, questform, reach, storyexplorer, atlas and consistency run the same way from their module;
  - the map's rules add stages and tests for path globs (story markdown -> the explorer and story tests, skse/** ->
    the C++ tests, and so on);
  - a path of a map rule marked `only` (a place's edits/, the owner's saves; the place skills' text) picks that rule's
    stages and nothing else;
  - a folder of independent members (the map's `trees`: newworld/places) named by a tool is reached by a root file of
    it, never by a file inside one member: one place's files run that place's data checks, not the tools that read any
    place;
  - a path in the map's `full` list, or a path nothing above picks up, runs the whole gate; so does any error in
    the picker itself;
  - an edit to the map is scoped like any other change: the map at the base ref against the map now, and only the
    entries added, removed or altered count as changed (their stages, their tests, their named paths); an edit to the
    map's structural parts (`full`, `named_direct`, `trees`, `per_test_reach`, the `[stages]` table) runs the whole
    gate.
It prints one line saying what it ran and what it skipped, and why.
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import os
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAP = REPO / "tooling" / "gate_map.toml"
TEST_DIRS = ("tooling/tests", "tools/tests")
STAGES = ("adaptation", "questtext", "questform", "reach", "storyexplorer", "atlas", "consistency", "skse", "editsvalid")
TOP = None  # top-level repo entries, filled lazily
PATH_RE = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.*-]+)+/?$")
MOD_RE = re.compile(r"^(tools|tooling)(\.[A-Za-z_][A-Za-z0-9_]*)+$")


@dataclass
class Plan:
    full: bool = False
    reason: str = ""
    tests: set[str] = field(default_factory=set)
    stages: set[str] = field(default_factory=set)
    why: dict[str, str] = field(default_factory=dict)
    inert: list[str] = field(default_factory=list)   # paths of an `only` rule: checked by their own stage, nothing else


# ---- the dependency index -------------------------------------------------------------------------------------

def _top(repo: Path) -> set[str]:
    return {p.name for p in repo.iterdir() if not p.name.startswith(".git")}


def _mod_file(repo: Path, mod: str) -> Path | None:
    base = repo.joinpath(*mod.split("."))
    for cand in (base.with_suffix(".py"), base / "__init__.py"):
        if cand.is_file():
            return cand
    return None


def _chain(node: ast.AST) -> list[str] | None:
    """`a / "x" / "y"` -> ["x", "y"] (the string parts of a / chain), else None."""
    parts: list[str] = []
    while isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        if isinstance(node.right, ast.Constant) and isinstance(node.right.value, str):
            parts.append(node.right.value)
        else:
            parts.clear()
        node = node.left
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        parts.append(node.value)
    return list(reversed(parts)) if parts else None


@dataclass
class Scope:
    """What one part of a file reaches: its imports as (module, name or None), the repo paths it names, and the
    bare names it uses (to follow calls to the file's own functions)."""
    imports: set[tuple[str, str | None, str | None]] = field(default_factory=set)   # (module, name, bound as)
    paths: set[str] = field(default_factory=set)
    names: set[str] = field(default_factory=set)       # bare names used (not as the base of an attribute)
    attrs: set[tuple[str, str]] = field(default_factory=set)   # `x.y` uses: (x, y)


def _visit(node: ast.AST, pkg: str, tops: set[str], s: Scope, inner: bool = False) -> None:
    """`inner`: the node is the left part of a longer `a / "x"` chain, whose whole path the outer node records (a
    prefix such as REPO / "newworld" alone would name a whole tree)."""
    n = node
    if isinstance(n, ast.Import):
        s.imports.update((a.name, None, a.asname if a.asname or "." in a.name else a.name) for a in n.names)
    elif isinstance(n, ast.ImportFrom):
        base = n.module or ""
        if n.level:
            up = pkg.split(".")[: len(pkg.split(".")) - (n.level - 1)]
            base = ".".join([*up, base] if base else up)
        s.imports.update((base, a.name, a.asname or a.name) for a in n.names)
    elif isinstance(n, ast.Constant) and isinstance(n.value, str):
        v = n.value.strip()
        if MOD_RE.match(v):
            s.imports.add((v, None, None))
        elif PATH_RE.match(v) and v.split("/")[0] in tops:
            s.paths.add(v.rstrip("/").split("*")[0].rstrip("/"))
    elif isinstance(n, ast.BinOp) and not inner:
        parts = _chain(n)
        if parts:
            joined = "/".join(p.strip("/") for p in parts if p)
            if joined.split("/")[0] in tops:
                s.paths.add(joined.split("*")[0].rstrip("/"))
    elif isinstance(n, ast.Name):
        s.names.add(n.id)
    elif isinstance(n, ast.Attribute):
        s.names.add(n.attr)
        if isinstance(n.value, ast.Name):
            s.attrs.add((n.value.id, n.attr))


def _is_div(n: ast.AST) -> bool:
    return isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div)


def _is_main(t: ast.AST) -> bool:
    return (isinstance(t, ast.Compare) and isinstance(t.left, ast.Name) and t.left.id == "__name__"
            and any(isinstance(c, ast.Constant) and c.value == "__main__" for c in t.comparators))


def _walk(node: ast.AST, pkg: str, tops: set[str], s: Scope, skip_defs: bool) -> None:
    for c in ast.iter_child_nodes(node):
        if isinstance(node, ast.Attribute) and isinstance(c, ast.Name):
            continue                                  # the base of `x.y` is recorded in attrs, not as a bare use
        if skip_defs and isinstance(c, ast.If) and _is_main(c.test):
            continue                                  # `if __name__ == "__main__":` never runs on import
        if skip_defs and isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in [*c.decorator_list, *c.args.defaults, *c.args.kw_defaults]:   # these run at import
                if d is not None:
                    _visit(d, pkg, tops, s); _walk(d, pkg, tops, s, False)
            continue
        _visit(c, pkg, tops, s, _is_div(node) and c is node.left and _is_div(c))
        _walk(c, pkg, tops, s, skip_defs)


_CLOSURES: dict = {}
_SCANS: dict[tuple[str, int, frozenset[str]], tuple[Scope, dict[str, Scope]]] = {}


def scan(repo: Path, f: Path, tops: set[str]) -> tuple[Scope, dict[str, Scope]]:
    """One file in parts: what runs on import (`top`: everything outside a function body, class bodies included) and,
    for each function or class defined at module level, what its body reaches. Kept per file and mtime."""
    try:
        key = (str(f), f.stat().st_mtime_ns, frozenset(tops))
    except OSError:
        return Scope(), {}
    if key not in _SCANS:
        _SCANS[key] = _scan(repo, f, tops)
    return _SCANS[key]


def _scan(repo: Path, f: Path, tops: set[str]) -> tuple[Scope, dict[str, Scope]]:
    top, defs = Scope(), {}
    try:
        tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return top, defs
    pkg = ".".join(f.relative_to(repo).with_suffix("").parts[:-1])
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            s = defs[n.name] = Scope()
            _walk(n, pkg, tops, s, False)
        targets = _const_targets(n)
        if targets:            # `DB = REPO / "x" / "db"`: a path held in a name reaches only the code that uses it
            for t in targets:
                _walk(n, pkg, tops, defs.setdefault(t, Scope()), False)
            continue
        holder = ast.Module(body=[n], type_ignores=[])
        _walk(holder, pkg, tops, top, True)
    return top, defs


# calls that only build a value (a path, a set) and read nothing: a module-level name assigned with only these holds
# a path for its users rather than reading it on import
PURE_CALLS = {"Path", "PurePath", "resolve", "parent", "joinpath", "expanduser", "absolute", "home", "get", "getenv",
              "str", "int", "float", "frozenset", "set", "tuple", "list", "dict", "compile", "with_suffix", "with_name",
              "relative_to", "as_posix", "cwd", "gethostname"}


def _const_targets(n: ast.stmt) -> list[str]:
    if isinstance(n, ast.Assign):
        tg, value = n.targets, n.value
    elif isinstance(n, ast.AnnAssign) and n.value is not None:
        tg, value = [n.target], n.value
    else:
        return []
    if not all(isinstance(t, ast.Name) for t in tg):
        return []
    for c in ast.walk(value):
        if isinstance(c, ast.Call):
            f = c.func
            name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
            if name not in PURE_CALLS:
                return []
        elif isinstance(c, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            return []
    return [t.id for t in tg]


class Index:
    """Each test file's and each stage's closure: the repo files it imports and the repo paths it names.

    The closure follows names, not just files: `from m import f` reaches what m runs on import plus what f's body
    reaches (and the functions of m that f uses, in turn); `import m`, a module named as a string, a test file and a
    stage's module reach the whole file. So a function-local import (a command dispatcher's lazy `from x import
    main`) reaches only the callers of that function, not every importer of its module."""

    def __init__(self, repo: Path):
        self.repo = repo
        self.tops = _top(repo)
        self._scan: dict[str, tuple[Scope, dict[str, Scope]]] = {}
        self._mods: dict[str, str | None] = {}
        self._deps_cache: dict[tuple[str, str | None], tuple[set[tuple[str, str | None]], set[str]]] = {}

    def _modfile(self, key: str) -> str | None:
        if key not in self._mods:
            mf = _mod_file(self.repo, key)
            self._mods[key] = mf.relative_to(self.repo).as_posix() if mf else None
        return self._mods[key]

    def _resolve(self, rel: str, imports, named: set[str], bare: set[str], attrs: set[tuple[str, str]]
                 ) -> set[tuple[str, str | None]]:
        """Imports as nodes (file, name): name None is the whole file, "" what it runs on import. A module bound to
        a name the scope uses only as `alias.f` reaches what it runs on import plus each such f."""
        out: set[tuple[str, str | None]] = set()
        here = (self.repo / rel).parent

        def whole(f: str, alias: str | None) -> None:
            if alias is None or alias in bare:
                out.add((f, None))
                return
            out.add((f, ""))
            out.update((f, a) for b, a in attrs if b == alias)

        for mod, name, alias in imports:
            if not mod:
                continue
            if mod.split(".")[0] not in ("tools", "tooling"):
                # a bare import from a folder the file put on sys.path: its own folder, its parent, or one it names
                for cand in ([f"{mod}.{name}", mod] if name else [mod]):
                    for d in (here, here.parent, *(self.repo / n for n in named)):
                        mf = _mod_file(d, cand)
                        if mf and mf.is_relative_to(self.repo):
                            out.add((mf.relative_to(self.repo).as_posix(), None))
                            break
                    else:
                        continue
                    break
                continue
            parts = mod.split(".")
            for i in range(1, len(parts)):       # a package's __init__ runs on import of its children
                if self._modfile(".".join(parts[:i])):
                    out.add((self._modfile(".".join(parts[:i])), ""))
            mf = self._modfile(mod)
            sub = self._modfile(f"{mod}.{name}") if name and name != "*" else None
            if sub:                               # `from pkg import submodule`
                if mf:
                    out.add((mf, ""))
                whole(sub, alias)
            elif mf and name is None:
                whole(mf, alias)
            elif mf:
                out.add((mf, None if name == "*" else name))
        return out

    def _deps(self, rel: str, sym: str | None = None) -> tuple[set[tuple[str, str | None]], set[str]]:
        """One node's direct in-repo dependencies (nodes) and the paths it names."""
        key = (rel, sym)
        if key in self._deps_cache:
            return self._deps_cache[key]
        if rel not in self._scan:
            self._scan[rel] = scan(self.repo, self.repo / rel, self.tops)
        top, defs = self._scan[rel]
        scopes = [top]
        if sym is None:
            scopes += list(defs.values())
        else:
            todo = [sym, *top.names] if sym else list(top.names)
            seen: set[str] = set()
            while todo:
                d = todo.pop()
                if d in seen or d not in defs:
                    continue
                seen.add(d)
                scopes.append(defs[d])
                todo.extend(defs[d].names)
        imports = set().union(*(s.imports for s in scopes))
        named = set().union(*(s.paths for s in scopes))
        bare = set().union(*(s.names for s in scopes))
        attrs = set().union(*(s.attrs for s in scopes))
        out = (self._resolve(rel, imports, named, bare, attrs), named)
        self._deps_cache[key] = out
        return out

    def closure(self, start: Path, direct_only: frozenset[str] = frozenset()) -> tuple[set[str], set[str]]:
        """The files `start` reaches and the paths they name; the paths a `direct_only` module names count only when
        `start` itself imports that module (not through another module)."""
        key = (str(self.repo), str(start), direct_only)
        if key not in _CLOSURES:     # one process (the gate, its tests) sees one tree: a closure is worked out once
            _CLOSURES[key] = self._closure(start, direct_only)
        return _CLOSURES[key]

    def _closure(self, start: Path, direct_only: frozenset[str]) -> tuple[set[str], set[str]]:
        first = start.relative_to(self.repo).as_posix()
        direct = {f for f, _ in self._deps(first)[0]}
        seen: set[tuple[str, str | None]] = set()
        files: set[str] = set()
        paths: set[str] = set()
        todo: list[tuple[str, str | None]] = [(first, None)]
        while todo:
            node = todo.pop()
            if node in seen:
                continue
            seen.add(node)
            rel = node[0]
            files.add(rel)
            deps, named = self._deps(*node)
            if rel not in direct_only or rel == first or rel in direct:
                paths |= named
            todo.extend(deps - seen)
        return files, paths

    def tests(self) -> list[str]:
        out = []
        for d in TEST_DIRS:
            out += sorted(p.relative_to(self.repo).as_posix() for p in (self.repo / d).glob("test_*.py"))
        return out


def _named(path: str, named: set[str], trees: frozenset[str] = frozenset()) -> bool:
    """A named file, or anything under a named directory of two or more parts (a bare top-level directory such as
    REPO / "docs" / name is too coarse to pick by; the map's rules cover those trees). A named `tree` (the map's
    `trees`: a folder of many independent folders, newworld/places) covers a path only directly under it or in a
    place's folder the code names itself (newworld/places/<id>), never a path inside any other member: a tool that
    names the whole tree reads whichever member it is given, and a change to one member does not reach it."""
    for n in named:
        if path == n:
            return True
        if n.count("/") >= 1 and path.startswith(n + "/"):
            if n in trees and "/" in path[len(n) + 1:]:
                continue
            return True
    return False


def _glob(path: str, globs) -> bool:
    return any(fnmatch.fnmatchcase(path, g) for g in globs)


def _rule_hit(path: str, rule: dict) -> bool:
    """A rule's `globs` minus its `not` globs (a more exact rule's paths, which the broader rule leaves to it)."""
    return _glob(path, rule["globs"]) and not _glob(path, rule.get("not", []))


# ---- the picker ---------------------------------------------------------------------------------------------

MAP_REL = "tooling/gate_map.toml"


def _rule_key(r: dict) -> str:
    return repr((sorted(r["globs"]), sorted(r.get("not", [])), sorted(r.get("stages", [])), sorted(r.get("tests", []))))


def map_delta(old: dict, new: dict) -> tuple[list[dict], list[str]] | None:
    """The rules added, removed or altered between two maps, and a line naming them; None when a structural part
    (`full`, `named_direct`, `[stages]`) differs, which the caller runs whole."""
    for part in ("full", "named_direct", "trees", "stages", "per_test_reach"):
        if old.get(part) != new.get(part):
            return None
    a = {_rule_key(r): r for r in old.get("rule", [])}
    b = {_rule_key(r): r for r in new.get("rule", [])}
    rules = [r for k, r in {**a, **b}.items() if (k in a) != (k in b)]
    return rules, [", ".join(r["globs"][:2]) + ("..." if len(r["globs"]) > 2 else "") for r in rules]


def pick(changed: list[str], repo: Path = REPO, mapfile: Path = MAP, base_map: str | None = None) -> Plan:
    """`base_map` is the map's text at the base ref; with it an edit to the map is scoped to its changed entries."""
    gate = tomllib.loads(mapfile.read_text())
    plan = Plan()
    changed = sorted({c for c in changed if c})
    extra: set[str] = set()      # paths the map's changed entries name: picked, never "unmatched"
    delta_rules: list[dict] = []
    notes: list[str] = []
    if MAP_REL in changed:
        d = map_delta(tomllib.loads(base_map), gate) if base_map is not None else None
        if d is None:
            return Plan(full=True, reason=f"{MAP_REL}: a structural part changed (or no base map to compare with)")
        changed.remove(MAP_REL)
        delta_rules, notes = d
        for r in delta_rules:
            extra |= {g for g in r["globs"] if "*" not in g}
    for c in changed:
        if _glob(c, gate.get("full", [])):
            return Plan(full=True, reason=f"{c} is shared by every check")
    if not changed and not delta_rules:
        return plan
    changed = sorted(set(changed) | extra)
    for r in delta_rules:     # a changed entry's own stages and tests run (a removed entry's, if they still exist)
        for s in r.get("stages", []):
            if s not in STAGES:
                raise ValueError(f"unknown stage {s}")
            plan.stages.add(s); plan.why.setdefault(s, "gate_map.toml entry " + r["globs"][0])
        for t in r.get("tests", []):
            if (repo / t).exists():
                plan.tests.add(t); plan.why.setdefault(t, "gate_map.toml entry " + r["globs"][0])
    if notes:
        plan.reason = "gate_map.toml entries treated as changed: " + "; ".join(notes)
    # a path of an `only` rule (the owner's saves under a place's edits/) reaches nothing but that rule's own checks
    only = [r for r in gate.get("rule", []) if r.get("only")]
    plan.inert = [c for c in changed if _glob(c, [g for r in only for g in r["globs"]])]
    for r in only:
        for c in plan.inert:
            if _glob(c, r["globs"]):
                for st in r.get("stages", []):
                    plan.stages.add(st); plan.why.setdefault(st, c)
    changed = [c for c in changed if c not in plan.inert]
    if not changed and not delta_rules:
        return plan
    idx = Index(repo)
    matched: set[str] = set()
    direct = frozenset(gate.get("named_direct", []))
    trees = frozenset(gate.get("trees", []))
    for t in idx.tests():
        files, named = idx.closure(repo / t, direct)
        for c in changed:
            if c in files or _named(c, named, trees):
                plan.tests.add(t); plan.why.setdefault(t, c); matched.add(c)
                break
    for stage, mod in gate.get("stages", {}).items():
        mf = _mod_file(repo, mod)
        if mf is None:
            raise FileNotFoundError(f"stage {stage}: no module {mod}")
        files, named = idx.closure(mf, direct)
        for c in changed:
            if c in files or _named(c, named, trees):
                plan.stages.add(stage); plan.why.setdefault(stage, c); matched.add(c)
                break
    for rule in gate.get("rule", []):
        if rule.get("only"):
            continue
        for c in changed:
            if _rule_hit(c, rule):
                matched.add(c)
                for s in rule.get("stages", []):
                    if s not in STAGES:
                        raise ValueError(f"unknown stage {s}")
                    plan.stages.add(s); plan.why.setdefault(s, c)
                for t in rule.get("tests", []):
                    if not (repo / t).exists():
                        raise FileNotFoundError(f"map names a missing test {t}")
                    plan.tests.add(t); plan.why.setdefault(t, c)
    for reach_rel in gate.get("per_test_reach", []):
        hit, seen = per_test(changed, repo, reach_rel)
        matched |= seen
        for t, c in hit.items():
            plan.tests.add(t); plan.why.setdefault(t, c)
    unmatched = [c for c in changed if c not in matched and c not in extra]
    if unmatched:
        return Plan(full=True, reason=f"{unmatched[0]} matches no rule" + (f" (+{len(unmatched)-1})" if len(unmatched) > 1 else ""))
    # a directory named as a test covers its files
    for t in list(plan.tests):
        if (repo / t).is_dir():
            plan.tests.discard(t)
            plan.tests |= {x for x in idx.tests() if x.startswith(t.rstrip("/") + "/")}
    return plan


def per_test(changed: list[str], repo: Path, reach_rel: str) -> tuple[dict[str, str], set[str]]:
    """The tests of a slow suite a change reaches, test by test, from the suite's declared reach (a module beside it:
    DIR, the folder its paths are relative to; FILES, its test files; CORE, globs every test depends on (the page
    shell, the loader, the harness); REACH, each test's own files). A CORE path or a test file itself runs every test
    of the suite; any other path under DIR runs the tests whose REACH names it, and none when no test does.
    Returns {test file or node id: the changed path that picked it} and the changed paths it accounted for."""
    import runpy
    r = runpy.run_path(str(repo / reach_rel))
    d = r["DIR"].rstrip("/") + "/"
    out: dict[str, str] = {}
    seen: set[str] = set()
    for c in changed:
        if not c.startswith(d):
            continue
        seen.add(c)
        rel = c[len(d):]
        if rel in r["FILES"] or _glob(rel, r["CORE"]):
            out.update({d + f: c for f in r["FILES"] if d + f not in out})
            continue
        for node, files in r["REACH"].items():
            if rel in files:
                out.setdefault(d + node, c)
    whole = {t for t in out if "::" not in t}
    return {t: c for t, c in out.items() if t.split("::")[0] not in whole or "::" not in t}, seen


def base_map_text(base: str | None, repo: Path = REPO) -> str | None:
    """The map as it stood at the base ref (the merge base of a lane landing, else HEAD); None when there is none."""
    try:
        ref = subprocess.run(["git", "-C", str(repo), "merge-base", base, "HEAD"], check=True, capture_output=True,
                             text=True).stdout.strip() if base else "HEAD"
        return subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{MAP_REL}"], check=True, capture_output=True,
                              text=True).stdout
    except subprocess.CalledProcessError:
        return None


def changed_paths(base: str | None, repo: Path = REPO) -> list[str]:
    def git(*a):
        return subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, text=True).stdout.split("\n")
    if base:
        out = git("diff", "--name-only", f"{base}...HEAD") + git("diff", "--name-only", "HEAD")
    else:
        out = git("diff", "--name-only", "HEAD") + git("ls-files", "--others", "--exclude-standard")
    return [p for p in out if p]


# ---- running ------------------------------------------------------------------------------------------------

def _make(target: str) -> int:
    return subprocess.run(["make", "-s", "-C", str(REPO), target]).returncode


def _pytest(tests: list[str]) -> int:
    py = os.environ.get("GATE_PY", sys.executable)
    rc = subprocess.run([py, "-m", "pytest", "-q", *tests], cwd=REPO).returncode
    return 0 if rc in (0, 5) else rc


FULL_WHY = ("deploy", "phase-close")
FULL_REFUSED = ("refused: a full run is only for a deploy or a phase's close (WHY=deploy or WHY=phase-close); a "
                "landing runs `make check GATE_BASE=origin/main`, which picks what the change reaches")


def summary(plan: Plan, n_tests: int) -> str:
    if plan.full:
        asked = plan.reason.startswith("asked for")
        return (f"gate: FULL (all {n_tests} test files, every stage): {plan.reason}"
                + ("" if asked else "; a full run is expected only when such a file changes"))
    note = f" [{plan.reason}]" if plan.reason else ""
    ran = sorted(plan.stages)
    skipped = [s for s in STAGES if s not in plan.stages]
    files = {t.split("::")[0] for t in plan.tests}
    nodes = len([t for t in plan.tests if "::" in t])
    return (f"gate: scoped: guard, lint, {len(files)}/{n_tests} test files"
            + (f" ({nodes} of them as single tests)" if nodes else "")
            + (f", {', '.join(ran)}" if ran else "")
            + f"; skipped {', '.join(skipped) or 'nothing'} and {n_tests - len(files)} test files"
            + " (no changed path reaches them; `make check-all` runs everything)" + note)


def run(plan: Plan, all_tests: list[str]) -> int:
    rc = _make("guard") or _make("lint")
    if rc:
        return rc
    tests = all_tests if plan.full else sorted(plan.tests)
    if tests:
        rc = _pytest(list(TEST_DIRS) if plan.full else tests)
        if rc:
            return rc
    for s in STAGES:
        if plan.full or s in plan.stages:
            if s == "editsvalid":
                rc = subprocess.run([os.environ.get("GATE_PY", sys.executable), "-m", "tools.places.edits_valid",
                                     *([i for i in plan.inert if fnmatch.fnmatchcase(i, "newworld/places/*/edits/*")]
                                       or ["--all"])], cwd=REPO).returncode
            elif s == "skse":
                rc = subprocess.run(["bash", str(REPO / "skse" / "check.sh")]).returncode
            else:
                rc = _make(s)
            if rc:
                return rc
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("run", "plan"))
    ap.add_argument("--base", help="diff from this ref's merge base (a lane landing: origin/main)")
    ap.add_argument("--all", action="store_true", help="the whole gate: only with --why deploy|phase-close")
    ap.add_argument("--why", default="", help="why a full run: deploy or phase-close")
    ap.add_argument("paths", nargs="*", help="changed paths (default: from git)")
    a = ap.parse_args(argv)
    all_tests = Index(REPO).tests()
    if a.all:
        if a.why not in FULL_WHY:
            print(FULL_REFUSED, file=sys.stderr)
            return 2
        plan = Plan(full=True, reason=f"asked for ({a.why})")
    else:
        try:
            plan = pick(a.paths or changed_paths(a.base), base_map=base_map_text(a.base))
        except Exception as e:   # the picker never makes the gate weaker: any error runs everything
            plan = Plan(full=True, reason=f"the picker failed ({type(e).__name__}: {e})")
    line = summary(plan, len(all_tests))
    print(line, flush=True)
    if a.cmd == "plan":
        for t in sorted(plan.tests):
            print(f"  {t}  <- {plan.why.get(t, '')}")
        for s in sorted(plan.stages):
            print(f"  [{s}]  <- {plan.why.get(s, '')}")
        return 0
    rc = run(plan, all_tests)
    print(("CHECK GREEN" if rc == 0 else "CHECK RED") + f" ({line.split(':')[1].strip()})")
    return rc


if __name__ == "__main__":
    sys.exit(main())
