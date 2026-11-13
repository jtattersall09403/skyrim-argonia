"""Where a new game starts on each card, read from the plugins the card lays.

A new game runs MQ101 (03372B:Skyrim.esm). The load order's last plugin that overrides MQ101 owns its stage-0 fragment;
ours is Argonia.esp's ARG_QF_MQ101, which moves the player to the new world's ArgoniaNWStartMarker (0x802 of
ArgoniaNewWorld.esm) when that plugin is loaded and the marker can be found with no cell loaded, else to the barge hold's
ARG_OpeningMarker (Argonia.esp). GetFormFromFile finds a reference in an unloaded cell only when it is persistent, so
the new world's marker must be a persistent reference of the world's persistent cell. The card's order is its MO2
profile's plugins.txt, then our own plugins in stack.ps1's order ($OursPlugins).

    python3 -m tools.newworld.start_check [--out out] [--stack ~/.argonia/stack]
"""
from __future__ import annotations

import argparse
import struct
import sys
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MQ101 = 0x03372B
NW_MARKER, NW_GIVE = 0x802, 0x090000
PERSISTENT = 0x400
# stack.ps1 $OursPlugins: (name, path under out/) per card, laid after the profile's plugins
OURS = {"Argonia": [("Argonia.esp", "Argonia.esp")],
        "NewWorld": [("Argonia.esp", "Argonia.esp"), ("ArgoniaNewWorld.esm", "newworld/plugin/ArgoniaNewWorld.esm"),
                     ("ArgoniaNWPlaces.esp", "places/plugin/ArgoniaNWPlaces.esp")]}
WANT = {"Argonia": "the barge hold (ARG_OpeningMarker, Argonia.esp)",
        "NewWorld": "the new world's start (ArgoniaNWStartMarker, ArgoniaNewWorld.esm)"}


def _header(data: bytes) -> tuple[list[str], int]:
    size = struct.unpack_from("<I", data, 4)[0]
    body, o, masters = data[24:24 + size], 0, []
    while o < len(body):
        sig, n = body[o:o + 4], struct.unpack_from("<H", body, o + 4)[0]
        if sig == b"MAST":
            masters.append(body[o + 6:o + 6 + n].split(b"\0", 1)[0].decode("cp1252"))
        o += 6 + n
    return masters, 24 + size


def _subs(data: bytes, off: int) -> dict[bytes, bytes]:
    size, flags = struct.unpack_from("<II", data, off + 4)
    body = data[off + 24:off + 24 + size]
    if flags & 0x40000:
        body = zlib.decompress(body[4:])
    out, o = {}, 0
    while o < len(body):
        sig, n = body[o:o + 4], struct.unpack_from("<H", body, o + 4)[0]
        out.setdefault(sig, body[o + 6:o + 6 + n])
        o += 6 + n
    return out


def scan(path: Path) -> dict:
    """MQ101's override (its fragment script), and our start marker and give quest: what decides the start."""
    data = path.read_bytes()
    masters, off = _header(data)
    own = len(masters)
    found: dict = {"masters": masters}

    def walk(o: int, end: int, parents: tuple) -> None:
        while o < end:
            sig = data[o:o + 4]
            size = struct.unpack_from("<I", data, o + 4)[0]
            if sig == b"GRUP":
                label, gtype = data[o + 8:o + 12], struct.unpack_from("<i", data, o + 12)[0]
                top = not parents and label not in (b"QUST", b"WRLD")
                if not (top or gtype in (4, 5)):          # never the exterior blocks: the start needs no cell of them
                    walk(o + 24, o + size, parents + (gtype,))
                o += size
                continue
            flags, fid = struct.unpack_from("<II", data, o + 8)
            idx, local = fid >> 24, fid & 0xFFFFFF
            master = masters[idx] if idx < own else path.name
            if sig == b"QUST" and (master, local) == ("Skyrim.esm", MQ101):
                vmad = _subs(data, o).get(b"VMAD", b"")
                found["mq101"] = "ARG_QF_MQ101" if b"ARG_QF_MQ101" in vmad else (vmad[:80] or "no script")
            if idx >= own and local == NW_GIVE and sig == b"QUST":
                found["give"] = b"ANW_TravelGive" in _subs(data, o).get(b"VMAD", b"")
            if idx >= own and local == NW_MARKER and sig == b"REFR":
                found["marker"] = {"persistent": bool(flags & PERSISTENT), "in_persistent_cell": 8 in parents}
            o += 24 + size

    walk(off, len(data), ())
    return found


def locate(name: str, stack: Path, game: Path) -> Path | None:
    for base in [*sorted((stack / "MO2" / "mods").glob("*")), game]:
        p = base / name
        if p.exists():
            return p
        hits = [q for q in base.glob("*") if q.name.lower() == name.lower()] if base.is_dir() else []
        if hits:
            return hits[0]
    return None


def card(profile: str, out: Path, stack: Path, game: Path) -> tuple[str, list[str]]:
    """(where a new game starts, faults) for one card."""
    txt = stack / "MO2" / "profiles" / profile / "plugins.txt"
    order = ["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm"]
    order += [ln[1:].strip() for ln in txt.read_text(errors="ignore").splitlines() if ln.startswith("*")]
    paths = {}
    for name in order:
        paths[name] = locate(name, stack, game)
    for name, rel in OURS[profile]:
        order.append(name)
        paths[name] = out / rel if (out / rel).exists() else None
    faults = [f"{n}: not found" for n, p in paths.items() if p is None and n != "ArgoniaNWPlaces.esp"]
    winner, facts = None, {}
    for name in order:
        if paths.get(name) is None:
            continue
        s = scan(paths[name])
        facts[name] = s
        if "mq101" in s:
            winner = (name, s["mq101"])
    if not winner or winner != ("Argonia.esp", "ARG_QF_MQ101"):
        faults.append(f"MQ101's winner is {winner}: not Argonia.esp's ARG_QF_MQ101")
        return "not ours (the winner's own start)", faults
    nw = facts.get("ArgoniaNewWorld.esm")
    if not nw:
        return WANT["Argonia"], faults
    m = nw.get("marker")
    if not m or not nw.get("give"):
        faults.append("ArgoniaNewWorld.esm has no start marker 0x802 in the world's persistent cell (a ref of an exterior "
                      "cell is not loaded at a new game) or no give quest 0x090000 with ANW_TravelGive")
        return WANT["Argonia"], faults
    if not (m["persistent"] and m["in_persistent_cell"]):
        faults.append(f"ArgoniaNewWorld.esm's start marker is not a persistent ref of the world's persistent cell ({m}): "
                      "GetFormFromFile finds nothing at a new game")
        return WANT["Argonia"], faults
    return WANT["NewWorld"], faults


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=REPO / "out")
    ap.add_argument("--stack", type=Path, default=Path.home() / ".argonia" / "stack")
    ap.add_argument("--game", type=Path, default=Path.home() / "games" / "skyrimse" / "Data")
    a = ap.parse_args(argv)
    bad = 0
    for profile in ("Argonia", "NewWorld"):
        where, faults = card(profile, a.out, a.stack, a.game)
        ok = where == WANT[profile] and not faults
        bad += not ok
        print(f"{'PASS' if ok else 'FAIL'} {profile} card: a new game starts in {where}" + "".join(f"\n  {f}" for f in faults))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
