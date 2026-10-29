#!/usr/bin/env python3
r"""The gamepad in Dark Souls 1's layout (owner, 2026-10-29: "map all the buttons like they are in DS1 remastered
on nintendo switch", by position; Skyrim's own menu, journal and wait kept on spare buttons).

Reads Skyrim's own PC controlmap from the player's `Skyrim - Interface.bsa` (an uncompressed v105 archive) and
writes it with the gameplay gamepad column changed, for `C:\argonia\controls\controlmap.txt` on the game machine;
`combat-mode.ps1 on` lays it loose in Data, which Skyrim reads over its archive. Keyboard, mouse and menu bindings are untouched. Neither the archive nor
the output is committed (decision 0003).

    controlmap.py <Skyrim - Interface.bsa> <controlmap.txt>
"""
import struct
import sys

# Skyrim's gamepad codes (Xbox names; DS1's Switch positions in the comments)
DPAD_UP, DPAD_DOWN, DPAD_LEFT, DPAD_RIGHT = 0x0001, 0x0002, 0x0004, 0x0008
START, BACK, LS, RS, LB, RB = 0x0010, 0x0020, 0x0040, 0x0080, 0x0100, 0x0200
A, B, X, Y, LT, RT = 0x1000, 0x2000, 0x4000, 0x8000, 0x0009, 0x000A

GAMEPLAY = {
    "Right Attack/Block": [RB, RT],   # R1 light (hold for heavy), R2 the same until a separate heavy exists
    "Left Attack/Block": [LB, LT],    # L1 block; L1/L2 + R1 bashes, which Elden Parry turns into a parry
    "Sprint": [B],                    # the right button: tap rolls (Dodge Framework), hold runs
    "Activate": [A],                  # the bottom button: interact
    "Jump": [Y],                      # DS1 jumps from a run; Skyrim needs its own button: the top one
    "Ready Weapon": [X],              # DS1's use-item position; attacking draws the weapon anyway
    "Shout": [],                      # no shouts in Argonia
    "Tween Menu": [START],            # DS1's Start menu
    "Journal": [BACK],                # quests and the system menu (save, load, settings)
    "Wait": [DPAD_DOWN],
    "Favorites": [DPAD_UP],
    "Hotkey1": [DPAD_LEFT],           # DS1 switches the left and right weapons here
    "Hotkey2": [DPAD_RIGHT],
    "Toggle POV": [RS],               # TDM: a tap locks on (DS1's R3), a hold changes the view
    "Sneak": [LS],
}


def read_bsa_file(bsa_path: str, folder: str, name: str) -> bytes:
    with open(bsa_path, "rb") as f:
        magic, version, _, _, folders, _, _, file_names_len, _ = struct.unpack("<4sIIIIIIIH2x", f.read(36))
        if magic != b"BSA\0" or version != 105:
            raise SystemExit(f"{bsa_path}: not a Skyrim SE archive")
        counts = [struct.unpack("<QIIQ", f.read(24))[1] for _ in range(folders)]
        records = []
        for count in counts:
            folder_name = f.read(f.read(1)[0])[:-1].decode()
            for _ in range(count):
                _, size, offset = struct.unpack("<QII", f.read(16))
                records.append((folder_name, size, offset))
        names = f.read(file_names_len).split(b"\0")
        for (folder_name, size, offset), file_name in zip(records, names):
            if folder_name == folder and file_name.decode() == name:
                if size & 0x40000000:
                    raise SystemExit(f"{folder}\\{name} is compressed; this reader takes only stored files")
                f.seek(offset)
                return f.read(size)
    raise SystemExit(f"{folder}\\{name} not found in {bsa_path}")


def remap(text: str) -> str:
    out, section, done = [], None, set()
    for line in text.splitlines():
        if line.startswith("//"):
            section = line
        fields = line.split("\t")
        name = fields[0].strip()
        if section and "Main Gameplay" in section and name in GAMEPLAY:
            values = [i for i, v in enumerate(fields) if v.strip()]
            pad = values[3]   # name, keyboard, mouse, gamepad, ...
            codes = GAMEPLAY[name]
            fields[pad] = ",".join(f"0x{c:04x}" for c in codes) if codes else "0xff"
            done.add(name)
            line = "\t".join(fields)
        out.append(line)
    missing = set(GAMEPLAY) - done
    if missing:
        raise SystemExit(f"not in the gameplay section: {sorted(missing)}")
    return "\r\n".join(out) + "\r\n"


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    vanilla = read_bsa_file(sys.argv[1], "interface\\controls\\pc", "controlmap.txt").decode("latin-1")
    with open(sys.argv[2], "w", encoding="latin-1", newline="") as f:
        f.write(remap(vanilla))
