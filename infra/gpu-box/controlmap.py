#!/usr/bin/env python3
r"""The gamepad (GameSir X2, Xbox layout) in the owner's Dark Souls layout (ruling #51, 2026-11-06: "B to be the
dodge/sprint button and LB to be block ... Rb to be normal light attack and R2 to be heavy attack/power attack ...
The Tween menu can be moved to d pad left/right ... LT can be shouts"). docs/controls.md is the player's table.

Reads Skyrim's own PC controlmap from the player's `Skyrim - Interface.bsa` (an uncompressed v105 archive) and
writes it with the gameplay gamepad column changed, for `C:\argonia\controls\controlmap.txt` on the play machine;
`stack.ps1 on` lays it loose in Data, which Skyrim reads over its archive. Keyboard, mouse and menu bindings are
untouched. Neither the archive nor the output is committed (decision 0003).

    controlmap.py <Skyrim - Interface.bsa> <controlmap.txt>
    controlmap.py --remap <controlmap.txt> <out.txt>   re-apply GAMEPLAY over a made file
"""
import struct
import sys

# Skyrim's gamepad codes (Xbox names; DS1's Switch positions in the comments)
DPAD_UP, DPAD_DOWN, DPAD_LEFT, DPAD_RIGHT = 0x0001, 0x0002, 0x0004, 0x0008
START, BACK, LS, RS, LB, RB = 0x0010, 0x0020, 0x0040, 0x0080, 0x0100, 0x0200
A, B, X, Y, LT, RT = 0x1000, 0x2000, 0x4000, 0x8000, 0x0009, 0x000A

GAMEPLAY = {
    # RB light attack. RT also sits here because One Click Power Attack reads its key (281, RT) only inside the
    # attack handler, which sees only buttons bound to an attack: unbound, RT never fired (0.2 §c, 2026-10-29)
    "Right Attack/Block": [RB, RT],
    "Left Attack/Block": [LB],        # LB block (and left-hand cast); LB held + RB is a bash, which Elden Parry
                                      # turns into the parry and Rim Parry's riposte follows on RB
    "Sprint": [B],                    # TK Dodge RE bUseSprintKey: a tap of B dodges, a hold sprints
    "Shout": [LT],                    # was RB
    "Tween Menu": [DPAD_LEFT, DPAD_RIGHT],  # was B
    "Hotkey1": [],                    # were d-pad left/right; the favourites menu (d-pad up/down) does the same job
    "Hotkey2": [],
    "Activate": [A],
    "Jump": [Y],
    "Ready Weapon": [X],
    "Journal": [START],
    "Wait": [BACK],
    "Favorites": [DPAD_UP, DPAD_DOWN],
    "Sneak": [LS],
    "Toggle POV": [RS],               # hold R3; a tap of R3 is TDM's lock-on (its own setting)
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
    if len(sys.argv) == 4 and sys.argv[1] == "--remap":
        with open(sys.argv[2], encoding="latin-1") as f:
            made = f.read().replace("\r\n", "\n")
        with open(sys.argv[3], "w", encoding="latin-1", newline="") as f:
            f.write(remap(made))
        raise SystemExit(0)
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    vanilla = read_bsa_file(sys.argv[1], "interface\\controls\\pc", "controlmap.txt").decode("latin-1")
    with open(sys.argv[2], "w", encoding="latin-1", newline="") as f:
        f.write(remap(vanilla))
