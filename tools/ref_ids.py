"""A form's runtime id from its editor id, for the console (game-7, 2026-10-30).

The game keeps no reference's editor id, nor most base forms': `player.moveto ARG_Ref_ClaywaterStationRoadIn` and
`player.placeatme ARG_CampSpot 1` are refused ("Item ... not found") while `prid 100008E9` finds the ref. So every
`ARG_*` word in the world database's formid table is written as its runtime id: the plugin's prefix (the bridge's
`plugin` read: "10" for a full plugin, "FE001" for a light one) and its local id. Cells, worldspaces, globals and
quests keep their editor ids: `coc`, `cow`, `set <global> to` and the quest commands take those, and the game keeps
them. A calling reference is quoted: `"100008DB".GetDisabled`.

    python3 tools/ref_ids.py render <out dir>      # tests/scenes/*.txt with refs as ids, for deploy.sh to send
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WORD = re.compile(r"\bARG_\w+\b")
KEEP_NAMES = {"CELL", "WRLD", "GLOB", "QUST"}


def ref_rows() -> dict[str, tuple[str, int]]:
    """{editor id: (plugin, local id)} for every form the console must be given by id."""
    sys.path.insert(0, str(REPO))
    from tools.argonia_world import db
    from tools.argonia_world.place_build import ref_edid
    w = db.open()
    rows = {r.editor_id: (r.plugin, r.form_id) for r in w.rows("formid") if r.record_type not in KEEP_NAMES}
    # A borrowed cell's own ref (the station house's KotM door) keeps its host's id and gets no editor id; it is
    # named as ours would be, ARG_Ref_<the build_ref id>, so a journey can face it.
    for r in w.rows("build_ref"):
        if r.host_ref_form_key:
            local, plugin = r.host_ref_form_key.split(":", 1)
            rows.setdefault(ref_edid(r.id), (plugin, int(local, 16)))
    return rows


def runtime_id(prefix: str, local: int) -> str:
    if prefix.upper().startswith("FE"):
        if local > 0xFFF:
            raise ValueError(f"local id {local:X} does not fit a light plugin")
        return f"{prefix.upper()}{local:03X}"
    return f"{prefix.upper()}{local:06X}"


def resolver(prefix_of) -> "callable":
    """A function line -> line with every known ref's editor id replaced; prefix_of(plugin) gives the prefix."""
    rows, cache = ref_rows(), {}

    def one(m):
        hit = rows.get(m.group(0))
        if not hit:
            return m.group(0)
        plugin, local = hit
        if plugin not in cache:
            cache[plugin] = prefix_of(plugin)
        rid = runtime_id(cache[plugin], local)
        # as a calling reference the id is quoted: the console reads `100008DB.GetDisabled` as one unknown command
        return f'"{rid}"' if m.string[m.end():m.end() + 1] == "." else rid
    return lambda line: WORD.sub(one, line)


def render(out: Path, prefix_of) -> list[Path]:
    fix, written = resolver(prefix_of), []
    out.mkdir(parents=True, exist_ok=True)
    for sc in sorted((REPO / "tests" / "scenes").glob("*.txt")):
        dst = out / sc.name
        dst.write_text("\n".join(fix(l) for l in sc.read_text().splitlines()) + "\n")
        written.append(dst)
    return written


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] != "render":
        sys.exit(__doc__)
    sys.path.insert(0, str(REPO))
    from tools.bridge import Bridge
    b = Bridge()
    files = render(Path(sys.argv[2]), lambda p: b.call("plugin", p)["prefix"])
    print(f"{len(files)} scenes rendered to {sys.argv[2]}")
