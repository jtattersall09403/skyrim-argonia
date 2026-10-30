#!/usr/bin/env python3
"""Root motion for clip generators a behaviour patch adds but the animation data lacks (chunk 0.2 §c, the dodge).

Skyrim moves an actor by an animation's root motion only when `meshes\\animationdatasinglefile.txt` holds a motion
block for the playing clip generator's name in the actor's project. TK Dodge RE's patch (`tkuc`) plays the vanilla
dodge animations through new clip generators (TKDodgeBack, TKDodgeLeft, TKDodgeRight, TKDodgeForward) and ships no
animation-data part, and Pandora writes no entry for them, so the roll and the backstep played in place
(2026-10-30, lane game-3: backstep 0.0 units before, 130.7 after this patch). This adds each missing clip with the
triggers and motion of the clip generator that plays the same animation. A derived file, made on the player's
machine after Pandora (decision 0014); never committed.

    animdata.py patch <in> <out>     write <out> with the missing clips added; prints what it added
    animdata.py check <file>         parse it whole; print the player projects' clip and motion counts
"""
from __future__ import annotations

import sys

# new clip generator -> the clip generator that plays the same animation in the vanilla projects (tkuc's
# 1hm_behavior: TKDodgeBack plays Animations\DodgeBack.hkx, TKDodgeForward Animations\SneakRun_ForwardRoll.hkx)
COPY = {"TKDodgeBack": "DodgeBack", "TKDodgeLeft": "DodgeLeft", "TKDodgeRight": "DodgeRight",
        "TKDodgeForward": "SneakRun ForwardRoll"}
PROJECTS = ("DefaultMale.txt", "DefaultFemale.txt", "FirstPerson.txt")


def parse(text: str) -> list[list]:
    """[name, block lines, motion lines or None] per project. The file: a project count and names, then per
    project a counted block (a 1, a behaviour-file count and the files, a has-clips flag, the clips) and, when
    the flag is 1, a counted motion block."""
    lines = text.split("\r\n") if "\r\n" in text else text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    n = int(lines[0])
    i, projects = 1 + n, []
    for name in lines[1:1 + n]:
        count = int(lines[i])
        block = lines[i + 1:i + 1 + count]
        i += 1 + count
        motion = None
        if block[2 + int(block[1])] == "1":
            mc = int(lines[i])
            motion = lines[i + 1:i + 1 + mc]
            i += 1 + mc
        projects.append([name, block, motion])
    if i != len(lines):
        raise ValueError(f"animation data: {len(lines) - i} lines left after {n} projects")
    return projects


def render(projects: list[list]) -> str:
    out = [str(len(projects))] + [p[0] for p in projects]
    for _, block, motion in projects:
        out += [str(len(block))] + block
        if motion is not None:
            out += [str(len(motion))] + motion
    return "\r\n".join(out) + "\r\n"


def clips(block: list[str]) -> dict[str, tuple[int, int, str]]:
    """name -> (start, end, clip id) of each clip: name, id, speed, crop start, crop end, trigger count,
    triggers, a blank."""
    i, out = 3 + int(block[1]), {}
    while i < len(block):
        end = i + 6 + int(block[i + 5]) + 1
        out[block[i]] = (i, end, block[i + 1])
        i = end
    return out


def motions(motion: list[str]) -> dict[str, tuple[int, int]]:
    """clip id -> (start, end) of its motion: id, duration, translation count and lines, rotation count and
    lines, a blank."""
    i, out = 0, {}
    while i < len(motion):
        nt = int(motion[i + 2])
        end = i + 4 + nt + int(motion[i + 3 + nt]) + 1
        out[motion[i]] = (i, end)
        i = end
    return out


def patch(text: str, copy: dict[str, str] = COPY) -> tuple[str, list[str]]:
    """The file with every missing `copy` clip added to the player projects (lowest free ids); what was added."""
    projects, added = parse(text), []
    for p in projects:
        if p[0] not in PROJECTS or p[2] is None:
            continue
        c, mo = clips(p[1]), motions(p[2])
        used = {int(v[2]) for v in c.values()} | {int(k) for k in mo}
        free = (k for k in range(1, 1 << 20) if k not in used)
        for new, old in copy.items():
            if new in c or old not in c or c[old][2] not in mo:
                continue
            a, b, cid = c[old]
            nid = str(next(free))
            p[1] += [new, nid] + p[1][a + 2:b]
            ma, mb = mo[cid]
            p[2] += [nid] + p[2][ma + 1:mb]
            added.append(f"{p[0]} {new} = {old} (clip {cid}) as {nid}")
    return render(projects), added


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[0] == "patch":
        text = open(argv[1], newline="").read()
        out, added = patch(text)
        parse(out)
        open(argv[2], "w", newline="").write(out)
        print("\n".join(added) or "nothing missing")
        return 0
    if len(argv) == 2 and argv[0] == "check":
        for name, block, motion in parse(open(argv[1], newline="").read()):
            if name in PROJECTS:
                print(name, len(clips(block)), "clips", len(motions(motion or [])), "motions")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
