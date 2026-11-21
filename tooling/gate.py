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
    REPO / "newworld" / "sources" (a named directory covers everything under it);
  - the make stages adaptation, questtext, questform, reach, storyexplorer, atlas and consistency run the same way from their module;
  - the map's rules add stages and tests for path globs (story markdown -> the explorer and story tests, skse/** ->
    the C++ tests, and so on);
  - a path of a map rule marked `only` (a place's edits/, the owner's saves) picks that rule's stages and nothing else;
  - a path in the map's `full` list, or a path nothing above picks up, runs the whole gate; so does any error in
    the picker itself;
  - an edit to the map is scoped like any other change: the map at the base ref against the map now, and only the
    entries added, removed or altered count as changed (their stages, their tests, their named paths); an edit to the
    map's structural parts (`full`, `named_direct`, the `[stages]` table) runs the whole gate.
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


def scan(repo: Path, f: Path, tops: set[str]) -> tuple[set[str], set[str]]:
    """One file's imports (module names, resolved later) and the repo paths it names."""
    mods: set[str] = set()
    paths: set[str] = set()
    try:
        tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return mods, paths
    pkg = ".".join(f.relative_to(repo).with_suffix("").parts[:-1])
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            base = n.module or ""
            if n.level:
                up = pkg.split(".")[: len(pkg.split(".")) - (n.level - 1)]
                base = ".".join([*up, base] if base else up)
            mods.add(base)
            mods.update(f"{base}.{a.name}" for a in n.names)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            s = n.value.strip()
            if MOD_RE.match(s):
                mods.add(s)
            elif PATH_RE.match(s) and s.split("/")[0] in tops:
                paths.add(s.rstrip("/").split("*")[0].rstrip("/"))
        elif isinstance(n, ast.BinOp):
            parts = _chain(n)
            if parts and len(parts) >= 1:
                joined = "/".join(p.strip("/") for p in parts if p)
                if joined.split("/")[0] in tops:
                    paths.add(joined.split("*")[0].rstrip("/"))
    return {m for m in mods if m}, paths


class Index:
    """Each test file's and each stage's closure: the repo files it imports and the repo paths it names."""

    def __init__(self, repo: Path):
        self.repo = repo
        self.tops = _top(repo)
        self._scan: dict[str, tuple[set[str], set[str]]] = {}
        self._mods: dict[str, str | None] = {}

    def _deps(self, rel: str) -> tuple[set[str], set[str]]:
        """One file's direct in-repo dependencies (files, a package's __init__ included) and the paths it names."""
        if rel not in self._scan:
            mods, named = scan(self.repo, self.repo / rel, self.tops)
            files: set[str] = set()
            here = (self.repo / rel).parent
            for m in mods:
                if m.split(".")[0] not in ("tools", "tooling"):
                    # a bare import from a folder the file put on sys.path: its own folder, its parent, or one it names
                    for d in (here, here.parent, *(self.repo / n for n in named)):
                        mf = _mod_file(d, m)
                        if mf and mf.is_relative_to(self.repo):
                            files.add(mf.relative_to(self.repo).as_posix())
                            break
                    continue
                parts = m.split(".")
                for i in range(1, len(parts) + 1):     # a package's __init__ runs on import of its children
                    key = ".".join(parts[:i])
                    if key not in self._mods:
                        mf = _mod_file(self.repo, key)
                        self._mods[key] = mf.relative_to(self.repo).as_posix() if mf else None
                    if self._mods[key]:
                        files.add(self._mods[key])
            self._scan[rel] = (files, named)
        return self._scan[rel]

    def closure(self, start: Path, direct_only: frozenset[str] = frozenset()) -> tuple[set[str], set[str]]:
        """The files `start` reaches and the paths they name; the paths a `direct_only` module names count only when
        `start` itself imports that module (not through another module)."""
        files: set[str] = set()
        paths: set[str] = set()
        first = start.relative_to(self.repo).as_posix()
        todo = [first]
        while todo:
            rel = todo.pop()
            if rel in files:
                continue
            files.add(rel)
            deps, named = self._deps(rel)
            if rel not in direct_only or rel in self._deps(first)[0]:
                paths |= named
            todo.extend(deps - files)
        return files, paths

    def tests(self) -> list[str]:
        out = []
        for d in TEST_DIRS:
            out += sorted(p.relative_to(self.repo).as_posix() for p in (self.repo / d).glob("test_*.py"))
        return out


def _named(path: str, named: set[str]) -> bool:
    """A named file, or anything under a named directory of two or more parts (a bare top-level directory such as
    REPO / "docs" / name is too coarse to pick by; the map's rules cover those trees)."""
    return any(path == n or (n.count("/") >= 1 and path.startswith(n + "/")) for n in named)


def _glob(path: str, globs) -> bool:
    return any(fnmatch.fnmatchcase(path, g) for g in globs)


# ---- the picker ---------------------------------------------------------------------------------------------

MAP_REL = "tooling/gate_map.toml"


def _rule_key(r: dict) -> str:
    return repr((sorted(r["globs"]), sorted(r.get("stages", [])), sorted(r.get("tests", []))))


def map_delta(old: dict, new: dict) -> tuple[list[dict], list[str]] | None:
    """The rules added, removed or altered between two maps, and a line naming them; None when a structural part
    (`full`, `named_direct`, `[stages]`) differs, which the caller runs whole."""
    for part in ("full", "named_direct", "stages"):
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
    for t in idx.tests():
        files, named = idx.closure(repo / t, direct)
        for c in changed:
            if c in files or _named(c, named):
                plan.tests.add(t); plan.why.setdefault(t, c); matched.add(c)
                break
    for stage, mod in gate.get("stages", {}).items():
        mf = _mod_file(repo, mod)
        if mf is None:
            raise FileNotFoundError(f"stage {stage}: no module {mod}")
        files, named = idx.closure(mf, direct)
        for c in changed:
            if c in files or _named(c, named):
                plan.stages.add(stage); plan.why.setdefault(stage, c); matched.add(c)
                break
    for rule in gate.get("rule", []):
        if rule.get("only"):
            continue
        for c in changed:
            if _glob(c, rule["globs"]):
                matched.add(c)
                for s in rule.get("stages", []):
                    if s not in STAGES:
                        raise ValueError(f"unknown stage {s}")
                    plan.stages.add(s); plan.why.setdefault(s, c)
                for t in rule.get("tests", []):
                    if not (repo / t).exists():
                        raise FileNotFoundError(f"map names a missing test {t}")
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
    return (f"gate: scoped: guard, lint, {len(plan.tests)}/{n_tests} test files"
            + (f", {', '.join(ran)}" if ran else "")
            + f"; skipped {', '.join(skipped) or 'nothing'} and {n_tests - len(plan.tests)} test files"
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
                                     *(plan.inert or ["--all"])], cwd=REPO).returncode
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
