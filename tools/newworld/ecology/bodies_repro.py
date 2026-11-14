"""The sinking-people and unsearchable-bodies test (walk 2, lines 22 and 25): console batch files for the play
machine, and the reader of the logs they write.

    python3 -m tools.newworld.ecology.bodies_repro [--esm <ArgoniaNewWorld.esm>] [--out <dir>] [--load-order <file>]
    python3 -m tools.newworld.ecology.bodies_repro --read <dir with the game's bodies_repro_*.txt logs>

What a save can and cannot show: an actor outside the loaded cells is moved along its path without physics, so its
saved height is often under the land (in the walk's save 95 of 462 moved Skyrim.esm actors in Tamriel lay more than
4 units under Tamriel's land, the worst 586). Only an actor standing loaded beside the player shows a sinking fault,
so the test reads loaded actors, and it has a control for each cause:

    our bandit copy and our spider crab, in our world      (the fault as reported)
    a Skyrim person (Nazeem) brought into our world        (sinks too: the world or the mod stack, not our copies)
    a Skyrim person (Brenuin) in Whiterun                  (sinks too: the mod stack, not our world)

Each batch is one console command (`bat repro_a` ... `bat repro_g`), run in order with about ten seconds between,
because the console runs a whole file before the game moves anything:
- `repro_a` goes to the cell of a placed bandit of ours that has a spider crab within a cell of it;
- `repro_b` brings the bandit, the crab and Nazeem to the player (they are loaded by then, so `prid` finds them);
- `repro_c` logs the player's and each one's place, life and swimming, then kills the three;
- `repro_d` logs the three bodies;
- `repro_e` takes the player to Brenuin; `repro_f` logs both and kills him; `repro_g` logs his body.
The logs (`bodies_repro_c.txt`, `_d`, `_f`, `_g`, beside the game) are read by `--read`: each height against the
player's and, in our world, against the land of the same file.
"""
from __future__ import annotations

import argparse
import re
import struct
from pathlib import Path

from tools.navmesh import esm as E, land_gap

REPO = Path(__file__).resolve().parents[3]
ESM = REPO / "out/newworld/plugin/ArgoniaNewWorld.esm"
WORLD = "ArgoniaBlackMarsh"
KINDS = {"bandit": "Bandit", "crab": "SpiderCrab"}
NAZEEM, BRENUIN = "0001A6A4", "0002C90F"   # Skyrim.esm's own placed people (persistent, not essential, not Nords)
SINK = 8.0   # a standing actor more than this under the player's feet or the land has sunk (Skyrim's foot IK is under 8)
READS = {"c": ["player", "bandit", "crab", "nazeem"], "d": ["bandit", "crab", "nazeem"], "f": ["player", "brenuin"],
         "g": ["brenuin"]}
FIELDS = {"player": ["x", "y", "z"], None: ["x", "y", "z", "dead", "swimming"]}


def cell_of(pos) -> tuple[int, int]:
    return int(pos[0] // 4096), int(pos[1] // 4096)


def pair(esm: Path) -> dict[str, tuple[int, tuple[float, float, float], str]]:
    """The placed bandit and spider crab nearest each other, at most one cell apart, so that going to the bandit's
    cell loads both: kind -> (ref form id without load index, position, base editor id)."""
    npc: dict[int, str] = {}
    placed: dict[str, list] = {k: [] for k in KINDS}
    achr = []
    for r in E.records(esm, {b"NPC_", b"ACHR"}):
        s = dict(E.subrecords(r.data))
        if r.sig == b"NPC_":
            npc[r.fid] = s.get(b"EDID", b"")[:-1].decode("cp1252")
        else:
            achr.append((r.fid, struct.unpack("<I", s[b"NAME"])[0], struct.unpack_from("<fff", s[b"DATA"])))
    for fid, base, pos in achr:
        name = npc.get(base, "")
        for kind, key in KINDS.items():
            if key in name:
                placed[kind].append((fid & 0xFFFFFF, pos, name))
    return nearest_pair(placed["bandit"], placed["crab"])


def nearest_pair(bandits: list, crabs: list) -> dict:
    best = None
    by_cell: dict = {}
    for c in crabs:
        by_cell.setdefault(cell_of(c[1]), []).append(c)
    for b in bandits:
        bx, by = cell_of(b[1])
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for c in by_cell.get((bx + dx, by + dy), ()):
                    d = (b[1][0] - c[1][0]) ** 2 + (b[1][1] - c[1][1]) ** 2
                    if best is None or d < best[0]:
                        best = (d, b, c)
    if best is None:
        raise SystemExit("no placed bandit has a placed spider crab within a cell of it")
    return {"bandit": best[1], "crab": best[2]}


def land_at(esm: Path, pos) -> float:
    """The LAND's height under pos, the lower of the quad's two splits."""
    want = cell_of(pos)
    cells: dict[int, tuple[int, int]] = {}
    for r in E.records(esm, {b"CELL", b"LAND"}, groups={b"WRLD"}):
        s = dict(E.subrecords(r.data))
        if r.sig == b"CELL" and b"XCLC" in s:
            cells[r.fid] = struct.unpack_from("<ii", s[b"XCLC"])
        elif r.sig == b"LAND" and cells.get(r.cell) == want and b"VHGT" in s:
            h = land_gap.land_heights(s[b"VHGT"])
            return min(land_gap.land_z(h, (pos[0] - want[0] * 4096) / 128, (pos[1] - want[1] * 4096) / 128))
    raise SystemExit(f"no LAND for cell {want} in {esm}")


def read_block(who: str) -> list[str]:
    if who == "player":
        return ["player.getpos x", "player.getpos y", "player.getpos z"]
    return ["getpos x", "getpos y", "getpos z", "getdead", "isswimming"]


def batches(found: dict, index: str) -> dict[str, str]:
    """The seven batch files' text by letter."""
    refs = {"bandit": f"{index}{found['bandit'][0]:06X}", "crab": f"{index}{found['crab'][0]:06X}",
            "nazeem": NAZEEM, "brenuin": BRENUIN}
    cx, cy = cell_of(found["bandit"][1])
    out = {"a": [f"cow {WORLD} {cx} {cy}"],
           "b": [l for who in ("bandit", "crab", "nazeem") for l in (f"prid {refs[who]}", "moveto player")],
           "e": [f"player.moveto {BRENUIN}"]}
    for letter, whos in READS.items():
        lines = [f"scof bodies_repro_{letter}.txt"]
        for who in whos:
            lines += ([] if who == "player" else [f"prid {refs[who]}"]) + read_block(who)
        if letter in ("c", "f"):
            for who in whos:
                if who != "player":
                    lines += [f"prid {refs[who]}", "kill"]
        out[letter] = lines + ["scof 0"]
    return {k: "\n".join(v) + "\n" for k, v in sorted(out.items())}


def load_index(lines: list[str], plugin: str = "ArgoniaNewWorld.esm") -> str:
    """The plugin's load index from the machine's Plugins.txt as `name|header flags` lines: the five base files come
    first, then every enabled full plugin with the master flag (0x1), then the rest, each group in file order; plugins
    with the light flag (0x200) take no index."""
    rows = [l.strip().rsplit("|", 1) for l in lines if "|" in l]
    full = [(n, int(f)) for n, f in rows if not int(f) & 0x200]
    order = [n for n, f in full if f & 1] + [n for n, f in full if not f & 1]
    if plugin not in order:
        raise SystemExit(f"{plugin} is not an enabled full plugin in the load order")
    return f"{5 + order.index(plugin):02X}"


def parse(letter: str, text: str) -> dict[str, dict[str, float]]:
    """One log's values by actor: the console prints each command's result as `... >> <number>`, in command order."""
    vals = [float(v) for v in re.findall(r">>\s*(-?\d+(?:\.\d+)?)", text)]
    names = [(who, f) for who in READS[letter] for f in FIELDS.get(who, FIELDS[None])]
    if len(vals) < len(names):
        raise SystemExit(f"bodies_repro_{letter}.txt holds {len(vals)} values, {len(names)} expected: a `prid` found "
                         "nothing (the batch before it was not given its ten seconds) or the log is cut short")
    out: dict[str, dict[str, float]] = {}
    for (who, f), v in zip(names, vals):
        out.setdefault(who, {})[f] = v
    return out


def verdict(c: dict, f: dict, land: dict[str, float]) -> tuple[dict[str, float], str]:
    """Each living actor's height against the lower of the player's feet and the land under it, and what it decides."""
    def under(log, who, ground=None):
        ref = log["player"]["z"] if ground is None else min(ground, log["player"]["z"])
        return log[who]["z"] - ref
    d = {"bandit": under(c, "bandit", land.get("bandit")), "crab": under(c, "crab", land.get("crab")),
         "nazeem": under(c, "nazeem", land.get("nazeem")), "brenuin": under(f, "brenuin")}
    sunk = {k: v < -SINK for k, v in d.items()}
    if sunk["brenuin"]:
        why = "a Skyrim person sinks in Skyrim's own world: the mod stack, not our world or our copies"
    elif sunk["nazeem"]:
        why = "a Skyrim person sinks in our world and not in Skyrim's: our world (its land or its distance from the origin)"
    elif sunk["bandit"]:
        why = "only our bandit copy sinks: the copy's record or kit"
    else:
        why = "nobody sinks standing loaded beside the player: the fault needs its place or its movement (ask where)"
    return d, why


def read(logs: Path, esm: Path) -> int:
    got = {l: parse(l, (logs / f"bodies_repro_{l}.txt").read_text(errors="replace")) for l in READS}
    land = {who: land_at(esm, (v["x"], v["y"])) for who, v in got["c"].items() if who != "player"}
    d, why = verdict(got["c"], got["f"], land)
    for who, v in d.items():
        print(f"{who:8s} alive: {v:+7.1f} units against the ground")
    for l, who in (("d", "bandit"), ("d", "crab"), ("d", "nazeem"), ("g", "brenuin")):
        b, a = got[l][who], got["c" if l == "d" else "f"][who]
        print(f"{who:8s} body: dead {int(b['dead'])}, {b['z'] - a['z']:+7.1f} units against where it stood")
    print(why)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--esm", type=Path, default=ESM)
    ap.add_argument("--out", type=Path, default=REPO / "out/newworld/bodies_repro")
    ap.add_argument("--index", default="06", help="ArgoniaNewWorld.esm's load index on the card")
    ap.add_argument("--load-order", type=Path, help="the machine's `name|flags` lines for Plugins.txt; sets --index from them")
    ap.add_argument("--read", type=Path, help="the folder holding the game's bodies_repro_*.txt logs: print the verdict")
    o = ap.parse_args(argv)
    if o.read:
        return read(o.read, o.esm)
    if o.load_order:
        o.index = load_index(o.load_order.read_text().splitlines())
    found = pair(o.esm)
    o.out.mkdir(parents=True, exist_ok=True)
    for letter, text in batches(found, o.index).items():
        (o.out / f"repro_{letter}.txt").write_text(text)
    for kind, (fid, pos, name) in found.items():
        print(kind, f"{o.index}{fid:06X}", name, "placed", [round(p, 1) for p in pos], "cell", cell_of(pos))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
