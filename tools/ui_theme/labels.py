"""The menu labels in sentence case (owner play test item 10; 1.12 §7), as a recipe run at install (0014).

Skyrim's own labels ("SYSTEM", "SETTINGS", "QUIT", "MAGIC", "SKILLS") are upper case in its translation table
(interface/translate_english.txt in the Interface BSA), not in the menus. This rewrites that table: every value
that is all capitals becomes sentence case ("QUIT TO MAIN MENU" -> "Quit to main menu"); the keys, the order and
every other value are kept. The input is the player's own file (the winner among the themed mods, else the BSA's),
so the output, a derived file, is made on the player's machine and never committed.
"""
from __future__ import annotations

import re
from pathlib import Path

TABLE = "interface/translate_english.txt"
BSA = "Skyrim - Interface.bsa"
KEEP = {"HP", "XP", "OK", "ID", "UI", "HUD", "NPC", "FOV", "HDR", "DOF", "SSAO", "VSYNC", "FXAA", "TAA", "LOD"}
_CAPS = re.compile(r"^[A-Z][A-Z' &/:\-.,!?()]*$")


def sentence_case(value: str) -> str:
    """"QUIT TO MAIN MENU" -> "Quit to main menu"; a value with a lower case letter, a short form ("GB", "HP",
    three letters or fewer), as it is."""
    if not _CAPS.match(value) or not re.search(r"[A-Z]{2}", value) or value.strip() in KEEP or len(value.strip()) <= 3:
        return value
    words = value.lower().split(" ")
    out = [w.upper() if w.upper() in KEEP else w for w in words]
    first = next((i for i, w in enumerate(out) if w), None)
    if first is not None and out[first] not in KEEP:
        out[first] = out[first][:1].upper() + out[first][1:]
    return " ".join(out)


def relabel(text: str) -> tuple[str, int]:
    """The table with each all-capitals value in sentence case, and how many changed (line endings kept)."""
    n = 0
    lines = text.split("\n")
    for i, line in enumerate(lines):
        key, tab, rest = line.partition("\t")
        if not tab:
            continue
        cr = "\r" if rest.endswith("\r") else ""
        value = rest[: len(rest) - len(cr)]
        new = sentence_case(value)
        if new != value:
            lines[i] = f"{key}\t{new}{cr}"
            n += 1
    return "\n".join(lines), n


def source(roots: list[Path], data: Path | None) -> bytes | None:
    """The table the player's game would load: the last mod root's loose file, else the Interface BSA's."""
    for root in reversed(roots):
        p = root / TABLE
        if p.is_file():
            return p.read_bytes()
    if data is not None and (data / BSA).is_file():
        from tools.navmesh import bsa  # noqa: PLC0415 - only the install run reads the archive

        return bsa.Archive(bsa.local(data / BSA)).get(TABLE)
    return None


def write(raw: bytes, out: Path) -> int:
    """Decode (UTF-16 LE with its BOM, as Skyrim reads it), relabel, write under `out`; the count changed."""
    text, n = relabel(raw.decode("utf-16"))
    dest = out / TABLE
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b"\xff\xfe" + text.encode("utf-16-le"))
    return n
