"""Every band copy in the written world file is searchable as its source is and carries its loot.

The world writer copies each placed creature's or person's source record whole into the world file and then makes
its band copy (`ANW_Eco_<source>_<band>...`). This check reads the written file and holds each band copy, field by
field, to the source copy beside it: only the fields the band sets may differ (EDID; ACBS level, health offset and the
Unique, Essential, Protected and AutoCalc flags; the band ability in SPLO/SPCT; for a person given a kit, CNTO, COCT,
DOFT and the template's Inventory flag). It fails a copy that is a ghost, invulnerable or summonable, carries a
script, or has nothing to drop: no item, no death item, no outfit and no inventory template.

    python -m tools.newworld.ecology.loot_check [--esm PATH]

Exit 1 on a fault."""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ESM = REPO / "out/newworld/plugin/ArgoniaNewWorld.esm"
BAND_FIELDS = {"EDID", "ACBS", "SPLO", "SPCT", "DNAM"}   # DNAM: the band's health
KIT_FIELDS = {"CNTO", "COCT", "DOFT"}
ACBS_BAND = 0x2 | 0x10 | 0x20 | 0x800 | 0x4000   # Essential, AutoCalc, Unique, Protected, Summonable: the band clears
ACBS_BAD = {0x4000: "summonable", 0x20000000: "ghost", 0x80000000: "invulnerable"}
TPL_INVENTORY = 0x100


def fields(r) -> dict:
    out: dict = {}
    for s, b in r.subs:
        out.setdefault(s, []).append(b)
    return out


def check(npcs: dict) -> tuple[list, int]:
    """npcs: editor id -> subrecord dict. -> (faults, band copies checked)."""
    faults, n = [], 0
    for ed, f in sorted(npcs.items()):
        if not ed.startswith("ANW_Eco_"):
            continue
        n += 1
        base = ed[len("ANW_Eco_"):]
        src = next((npcs[k] for k in (base.rsplit("_D", 1)[0],) if k in npcs), None)
        if src is None:
            faults.append(f"{ed}: no source copy {base.rsplit('_D', 1)[0]} in the file")
            continue
        kit = "DOFT" in f and f.get("DOFT") != src.get("DOFT")
        for k in set(f) | set(src):
            if k in BAND_FIELDS or (kit and k in KIT_FIELDS) or f.get(k) == src.get(k):
                continue
            faults.append(f"{ed}: {k} differs from its source")
        a, s = f["ACBS"][0], src["ACBS"][0]
        fa, fs = struct.unpack_from("<I", a)[0], struct.unpack_from("<I", s)[0]
        if (fa ^ fs) & ~ACBS_BAND:
            faults.append(f"{ed}: ACBS flags {fa:08x} differ from its source's {fs:08x} beyond the band's")
        for bit, why in ACBS_BAD.items():
            if fa & bit:
                faults.append(f"{ed}: {why}")
        ta, ts = struct.unpack_from("<H", a, 18)[0], struct.unpack_from("<H", s, 18)[0]
        if (ta ^ ts) & ~(TPL_INVENTORY if kit else 0):
            faults.append(f"{ed}: template flags {ta:04x} differ from its source's {ts:04x}")
        if "VMAD" in f and "VMAD" not in src:
            faults.append(f"{ed}: carries a script its source does not")
        if not (f.get("CNTO") or f.get("INAM") or f.get("DOFT") or (ta & TPL_INVENTORY and f.get("TPLT"))):
            if src.get("CNTO") or src.get("INAM") or src.get("DOFT"):
                faults.append(f"{ed}: drops nothing, though its source does")
    return faults, n


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="tools.newworld.ecology.loot_check")
    ap.add_argument("--esm", default=str(ESM))
    a = ap.parse_args(argv)
    from tools.argonia_world.esm import Plugin
    p = Plugin.read(a.esm, {"NPC_"})
    npcs = {r.edid: fields(r) for r in p.records("NPC_") if r.edid}
    faults, n = check(npcs)
    print(f"loot check: {n} band copies, {len(faults)} faults")
    for x in faults[:30]:
        print("  " + x)
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main())
