#!/usr/bin/env python3
"""Import content data and design docs from the old project (0.1, docs/source-map.md §1, §2).

    python3 tools/import_old.py --src <old repo> --commit <sha>

Idempotent: every destination this script owns is deleted and recopied, and nothing
it writes depends on the clock, so a second run leaves `git status` unchanged.

  world/sources/**, world/schemas/**   content data and schemas, copied byte-identical
  docs/design/**                       design docs; each .md gets a source header line
  private/old-packages/**              engine-neutral rule packages (gitignored, read-only goals evidence)
  private/old-mined/**                 plugin-mined placement tables (gitignored: retail-derived, decision 0003)
  world/IMPORTED_FROM.md               every source path -> destination, and every missing path

Never copied (decision 0003): Bethesda text corpora (the Morrowind exemplar and corpus files and
any Morrowind-named UESP-fetched note), anything whose extension this repo's .gitignore names, any
binary, apps/, lanes/, tooling/, packages/ code other than the rule packages, and any file over
1 MB that no generator needs. packages/ui is a later chunk. world/README.md and
docs/design/README.md are kept.
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEXT_EXT = {".md", ".json", ".jsonl", ".yaml", ".yml", ".csv", ".txt"}
MB = 1024 * 1024

# --- never-copy rules -------------------------------------------------------------------
BETHESDA_TEXT = (  # decision 0003; owner call O-21 open
    "world/sources/dialogue/exemplars/morrowind-full.json",
    "world/sources/dialogue/exemplars/morrowind.json",
    "world/sources/lore/morrowind-dialogue-corpus-full.md",
)
# the one Morrowind-named file that is ours (a culture sheet we wrote)
OURS_MORROWIND_NAMED = ("world/sources/dialogue/cultures/factions/morrowind-veterans.json",)
# plugin-mined placement tables: derived from Bethesda and mod plugins (retail placement
# offsets), so they go to gitignored private/, never world/
MINED_PREFIXES = ("bmv-", "vanilla-", "htbm-")
MINED_NAMES = {"kit-assemblies-mined.json", "kit-designed-sink.json", "kit-mounts-mined.json",
               "kit-setting-class.json", "horses-mined.json", "traps-mined.json",
               "plugin-boarding.json", "vault-exterior-placement-survey.json",
               "depths-underwater-placement.json", "groundcover-rules.json", "spacing-floors.json",
               "settlement-asset-inventory.json"}
# >1 MB files that a generator reads (source-map §1 names these families)
BIG_OK_DIRS = ("world/sources/catalogue/", "world/sources/hydrology/", "world/sources/registries/",
               "world/sources/blueprints/", "world/sources/assets/", "world/sources/flora/",
               "world/sources/placement/exterior-interior-links.json",
               "world/sources/placement/accepted-places.json", "world/sources/placement/boats.json")

# --- §1: world data (old path prefix, kind) ---------------------------------------------
WORLD_ROOT = "world/sources"
WORLD_SKIP_NAMES = {".gitignore", "README.lock"}
WORLD_SUBDIRS = ["anchors", "assets", "audio", "blueprints", "catalogue", "climate", "demographics",
                 "dialogue", "economy", "flora", "hydrology", "lore", "placement", "quests",
                 "regions", "registries", "routes", "settlements", "sites", "sky", "terrain",
                 "text", "vocab"]
# the source-map rows that name a pattern, not the whole folder
BLUEPRINT_OK = ("*.layout.json", "place.*.json", "*.design.md", "README.md")
CATALOGUE_OK = ("*.json", "README.md")
ASSETS_OK = ("registry-*.jsonl", "registry-summary.json", "*.json", "*.md")

# --- §2: design docs (old path, destination under docs/design) ----------------------------
DESIGN = [
    ("docs/world", "world"),
    ("docs/quests", "quests"),
    ("docs/standards/text", "standards/text"),
    ("docs/standards/by-task.md", "standards/by-task.md"),
    ("docs/standards/engineering.md", "standards/engineering.md"),
    ("docs/research/combat-and-systems", "research/combat-and-systems"),
    ("docs/research/lore/creature-asset-availability.md", "research/lore/creature-asset-availability.md"),
    ("docs/phases/2-slice", "phases/2-slice"),
    ("packages/game-core/src/stats/README.md", "stats/README.md"),
    ("docs/decisions", "old-decisions"),
    ("docs/research/combat-and-systems/slice-systems-checklist.md", "slice-systems-checklist.md"),
]
DESIGN_KEEP = {"README.md", "goals.md"}
# source-map §1: the schemas
SCHEMA_SRC = "packages/world-schema/schemas"
FAMILIES_SRC = "packages/world-schema/families.json"
# source-map §1: engine-neutral rule packages (goal evidence, never built)
RULE_PACKAGES = ["dialogue", "narrative", "economy", "crafting", "save", "magic", "world-time",
                 "text-catalogue"]
GAME_CORE = ["stats", "crime", "factions", "inventory", "equipment", "scheduling", "perception",
             "traps", "travel", "encounters", "people", "rng", "validation"]
PKG_EXT = {".ts", ".tsx", ".js", ".mjs", ".json", ".md", ".py", ".css", ".yaml", ".yml", ".txt"}
PKG_SKIP_DIRS = {"node_modules", "dist", "build", "coverage", "__pycache__", ".turbo"}
PRIVATE_BIG = 4 * MB

HEADER = "<!-- imported unchanged from elder-souls-argonia {path} @ {sha} (0.1 §f) -->\n"


def gitignored_exts() -> set[str]:
    exts = set()
    gi = REPO / ".gitignore"
    if gi.exists():
        for line in gi.read_text().splitlines():
            m = re.fullmatch(r"\*(\.[A-Za-z0-9_.]+)", line.strip())
            if m:
                exts.add(m.group(1).lower())
    return exts


class Importer:
    def __init__(self, src: Path, sha: str):
        self.src, self.sha = src, sha
        self.bad_ext = gitignored_exts()
        self.rows: list[tuple[str, str, str]] = []       # (old path, new path, note)
        self.missing: list[str] = []
        self.excluded: list[tuple[str, str]] = []        # (old path, reason)
        self.private: list[tuple[str, str]] = []
        self.big: list[tuple[str, int]] = []
        self.big_skipped: list[tuple[str, int]] = []
        self.docs: list[tuple[Path, str, str]] = []      # (dest file, old rel path, kind)
        self.dir_map: list[tuple[str, str]] = []         # old dir prefix -> new dir prefix (repo-relative)
        self.file_map: dict[str, str] = {}

    # -- helpers --------------------------------------------------------------------
    def rel(self, p: Path) -> str:
        return p.relative_to(self.src).as_posix()

    def ext_ok(self, p: Path, allowed=TEXT_EXT) -> bool:
        e = p.suffix.lower()
        return e in allowed and e not in self.bad_ext

    def copy(self, old: Path, new: Path, note: str = "") -> None:
        new.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(old, new)
        o, n = self.rel(old), new.relative_to(REPO).as_posix()
        self.rows.append((o, n, note))
        self.file_map[o] = n

    def bethesda_reason(self, rel: str, p: Path) -> str | None:
        if rel in BETHESDA_TEXT:
            return "Bethesda text corpus (0003, O-21)"
        if rel in OURS_MORROWIND_NAMED:
            return None
        if "morrowind" in p.name.lower():
            return "Morrowind-named UESP-fetched reference note (Bethesda text)"
        return None

    # -- §1 world data --------------------------------------------------------------
    def world(self) -> None:
        dest_root = REPO / "world"
        for name in ("sources", "schemas", "IMPORTED_FROM.md"):
            t = dest_root / name
            if t.is_dir():
                shutil.rmtree(t)
            elif t.exists():
                t.unlink()
        for sub in ["README.md"] + WORLD_SUBDIRS:
            old = self.src / WORLD_ROOT / sub
            oldrel = f"{WORLD_ROOT}/{sub}"
            if not old.exists():
                self.missing.append(oldrel)
                continue
            if old.is_file():
                self.copy(old, dest_root / "sources" / sub)
                continue
            self.dir_map.append((oldrel, f"world/sources/{sub}"))
            for p in sorted(old.rglob("*")):
                if p.is_file():
                    self.world_file(p, oldrel, sub)
        # schemas and the family registry
        sdir = self.src / SCHEMA_SRC
        self.dir_map.append((SCHEMA_SRC, "world/schemas"))
        if sdir.is_dir():
            for p in sorted(sdir.glob("*.json")):
                self.copy(p, dest_root / "schemas" / p.name)
        else:
            self.missing.append(SCHEMA_SRC)
        fam = self.src / FAMILIES_SRC
        if fam.exists():
            self.copy(fam, dest_root / "schemas" / "families.json",
                      "family registry the integrity check reads")
        else:
            self.missing.append(FAMILIES_SRC)

    def world_file(self, p: Path, oldrel: str, sub: str) -> None:
        rel = self.rel(p)
        if p.name in WORLD_SKIP_NAMES or p.suffix == ".lock":
            return
        inner = p.relative_to(self.src / oldrel)
        # selective folders
        if sub == "blueprints" and not any(fnmatch.fnmatch(p.name, g) for g in BLUEPRINT_OK):
            self.excluded.append((rel, "not in the source-map §1 blueprint patterns (scan files are tool output)"))
            return
        if sub == "blueprints" and "fixture" in p.name:
            pass  # proving-ground fixtures are listed in the source map; copied, regenerated in 0.4
        if sub == "catalogue" and not any(fnmatch.fnmatch(p.name, g) for g in CATALOGUE_OK):
            self.excluded.append((rel, "not places-*.json"))
            return
        if sub == "assets" and not (p.parent.name == "assets" and any(fnmatch.fnmatch(p.name, g) for g in ASSETS_OK)):
            self.excluded.append((rel, "not vault metadata"))
            return
        if not self.ext_ok(p):
            self.excluded.append((rel, f"extension {p.suffix or '(none)'} is not text data (binary, code or ignored)"))
            return
        reason = self.bethesda_reason(rel, p)
        if reason:
            self.excluded.append((rel, reason))
            return
        mined = sub == "placement" and len(inner.parts) == 1 and (
            p.name.startswith(MINED_PREFIXES) or p.name in MINED_NAMES)
        # Helstrom (paused; cities are hand-built with the owner, old layouts are guides only, decision 0026 §3):
        # 23 MB of layout stays out of the public repo, read privately when 4.1 reaches the city
        if sub == "blueprints" and "helstrom" in p.name.lower():
            mined = True
        if mined:
            new = REPO / "private" / "old-mined" / p.name
            new.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, new)
            self.private.append((rel, f"private/old-mined/{p.name}"))
            return
        size = p.stat().st_size
        if size > MB:
            if not any(rel.startswith(d) for d in BIG_OK_DIRS):
                self.big_skipped.append((rel, size))
                self.excluded.append((rel, f"over 1 MB ({size} bytes) and no generator named for it"))
                return
            self.big.append((rel, size))
        self.copy(p, REPO / "world" / "sources" / sub / inner)

    # -- §2 design docs -------------------------------------------------------------
    def design(self) -> None:
        droot = REPO / "docs" / "design"
        droot.mkdir(parents=True, exist_ok=True)
        for child in sorted(droot.iterdir()):
            if child.name in DESIGN_KEEP:
                continue
            shutil.rmtree(child) if child.is_dir() else child.unlink()
        for old_rel, new_rel in DESIGN:
            old = self.src / old_rel
            if not old.exists():
                self.missing.append(old_rel)
                continue
            files = [old] if old.is_file() else sorted(q for q in old.rglob("*") if q.is_file())
            if old.is_dir():
                self.dir_map.append((old_rel, f"docs/design/{new_rel}"))
            for p in files:
                rel = self.rel(p)
                if not self.ext_ok(p):
                    self.excluded.append((rel, f"extension {p.suffix or '(none)'} is not text (image, binary or ignored)"))
                    continue
                if p.stat().st_size > MB:
                    self.big_skipped.append((rel, p.stat().st_size))
                    self.excluded.append((rel, "over 1 MB"))
                    continue
                new = droot / new_rel if old.is_file() else droot / new_rel / p.relative_to(old)
                new.parent.mkdir(parents=True, exist_ok=True)
                if p.suffix.lower() == ".md":
                    text = p.read_text(encoding="utf-8")
                    new.write_text(HEADER.format(path=rel, sha=self.sha) + text, encoding="utf-8")
                    self.docs.append((new, rel, "doc"))
                else:
                    shutil.copyfile(p, new)
                n = new.relative_to(REPO).as_posix()
                self.rows.append((rel, n, ""))
                # the first row for a source path wins for link mapping (the checklist is copied twice)
                self.file_map.setdefault(rel, n)

    # -- private/old-packages -------------------------------------------------------
    def packages(self) -> None:
        root = REPO / "private" / "old-packages"
        if root.exists():
            shutil.rmtree(root)
        targets = [f"packages/{p}" for p in RULE_PACKAGES] + [f"packages/game-core/src/{p}" for p in GAME_CORE]
        for t in targets:
            old = self.src / t
            if not old.is_dir():
                self.missing.append(t)
                continue
            n = 0
            for p in sorted(old.rglob("*")):
                if not p.is_file() or PKG_SKIP_DIRS & set(p.relative_to(old).parts):
                    continue
                if p.suffix.lower() not in PKG_EXT or p.suffix.lower() in self.bad_ext or p.stat().st_size > PRIVATE_BIG:
                    continue
                new = root / p.relative_to(self.src / "packages")
                new.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, new)
                n += 1
            self.private.append((t + "/", f"private/old-packages/{t.removeprefix('packages/')}/ ({n} files)"))

    # -- link fixing (item 4) -------------------------------------------------------
    LINK = re.compile(r"(\]\()([^)\s]+)(\))")

    def resolve_new(self, old_abs: str) -> str | None:
        if old_abs in self.file_map:
            return self.file_map[old_abs]
        for o, n in sorted(self.dir_map, key=lambda x: -len(x[0])):
            if old_abs == o or old_abs.startswith(o + "/"):
                cand = n + old_abs[len(o):]
                if (REPO / cand).exists():
                    return cand
        return None

    def fix_links(self) -> tuple[int, int]:
        fixed = unresolved = 0
        for new, oldrel, _ in self.docs:
            text = new.read_text(encoding="utf-8")
            old_dir = os.path.dirname(oldrel)
            in_fence = False
            out_lines = []
            for line in text.split("\n"):
                if line.startswith("```"):
                    in_fence = not in_fence
                if in_fence:
                    out_lines.append(line)
                    continue

                def sub(m):
                    nonlocal fixed, unresolved
                    target = m.group(2)
                    if re.match(r"^(https?:|mailto:|#|<)", target):
                        return m.group(0)
                    path, _, frag = target.partition("#")
                    if not path:
                        return m.group(0)
                    # a link that still resolves from the new place stays as written
                    if (new.parent / path).exists():
                        return m.group(0)
                    old_abs = os.path.normpath(os.path.join(old_dir, path)).replace(os.sep, "/")
                    dest = self.resolve_new(old_abs)
                    if dest is None:
                        unresolved += 1
                        return m.group(0)
                    r = os.path.relpath(REPO / dest, new.parent).replace(os.sep, "/")
                    fixed += 1
                    return f"{m.group(1)}{r}{'#' + frag if frag else ''}{m.group(3)}"
                out_lines.append(self.LINK.sub(sub, line))
            new.write_text("\n".join(out_lines), encoding="utf-8")
        return fixed, unresolved

    # -- the record -----------------------------------------------------------------
    def write_record(self, fixed: int, unresolved: int) -> None:
        by_top: dict[str, list[int]] = {}
        for o, n, _ in self.rows:
            key = o.rsplit("/", 1)[0] if "/" in o else o
            by_top.setdefault(key, [0, 0])[0] += 1
        L = [f"# Imported from elder-souls-argonia",
             "",
             f"Commit `{self.sha}` of the owner's private repo (read-only source). Written by `tools/import_old.py`; "
             "do not edit by hand. Data files are byte-identical; each design doc under `docs/design/` carries a "
             "source header line, and only relative links to other imported files were rewritten.",
             "",
             f"- Files copied: {len(self.rows)} ({sum(1 for r in self.rows if r[1].startswith('world/'))} under `world/`, "
             f"{sum(1 for r in self.rows if r[1].startswith('docs/design/'))} under `docs/design/`)",
             f"- Design-doc links rewritten to the new locations: {fixed}; left unresolved: {unresolved}",
             "", "## Missing",
             "",
             "Source-map paths that do not exist at this commit:", ""]
        L += [f"- `{m}`" for m in self.missing] or ["- none"]
        L += ["", "## Private (gitignored, never committed)", ""]
        L += [f"- `{o}` -> `{n}`" for o, n in self.private]
        L += ["", "## Not copied", ""]
        L += [f"- `{o}`: {why}" for o, why in sorted(self.excluded)]
        L += ["- `world/sources/lore/morrowind-dialogue-corpus-full.md`, `dialogue/exemplars/morrowind*.json`: "
              "Bethesda text, listed above if present at this commit; goes to `$ARGONIA_PRIVATE` only once O-21 is answered",
              "", "## Files over 1 MB copied (generator data; for the no-assets guard allowlist)", ""]
        L += [f"- `{n}` ({s:,} bytes)" for n, s in sorted(self.big)]
        L += ["", "## Every source path -> destination", "", "| Source | Destination |", "|---|---|"]
        L += [f"| `{o}` | `{n}` |" for o, n, _ in sorted(self.rows)]
        (REPO / "world" / "IMPORTED_FROM.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    def run(self) -> None:
        self.world()
        # private mined tables are owned here too
        self.design()
        self.packages()
        fixed, unresolved = self.fix_links()
        self.write_record(fixed, unresolved)
        total = sum(f.stat().st_size for f in (REPO / "world").rglob("*") if f.is_file())
        print(f"copied {len(self.rows)} files; missing {len(self.missing)}; excluded {len(self.excluded)}; "
              f"private {len(self.private)}; links fixed {fixed}, unresolved {unresolved}; world/ {total:,} bytes")
        for n, s in sorted(self.big):
            print(f"  >1MB copied: {n} {s:,}")
        for n, s in sorted(self.big_skipped):
            print(f"  >1MB skipped: {n} {s:,}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--src", required=True, help="path to the old repo checkout")
    ap.add_argument("--commit", required=True, help="the commit sha the checkout is at (recorded)")
    a = ap.parse_args()
    src = Path(a.src).resolve()
    if not (src / "world" / "sources").is_dir():
        print(f"{src} does not look like the old repo", file=sys.stderr)
        return 2
    mined = REPO / "private" / "old-mined"
    if mined.exists():
        shutil.rmtree(mined)
    Importer(src, a.commit).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
