"""The look-journey standard (lane 1.15-r6-look-journeys-standard): every journey marked `look: world` (its stills are
of the world, judged by a reader; tools/journey_lint.py `look`) is first person, HUD off, a weather forced by form id
and read back per stop, and each stand aimed by the clearance measure (tools/journeys/__init__.py `clearance`, the
plants on the eye line to the subject and the canopy over the eye; `grass_hits`, the tall grass under the first
metres) so the subject sits at the middle of the frame with nothing between. Round 6's stills (ground-materials,
road-look) were third person, HUD on, in fog, fronds over the subject.

`python3 -m tools.journeys refresh` calls these after each generator; the numbers per stand go to its log and print.
"""
from __future__ import annotations

import math
import re

from tools.argonia_world import skyrim_units as su
from tools.journeys import SEAT_U, SETANGLE, SETPOS, SUBJECT, Build, aim, clearance, eye_of, stand_bad, steps_of

try:   # lane water-stands-2's tall-grass measure; counted 0 until it lands
    from tools.journeys import grass_hits
except ImportError:  # pragma: no cover
    def grass_hits(*_a, **_k) -> int:
        return 0

U = su.UNITS_PER_METRE
CLEAR_DRY = "Argonia.esm|0x000E9B"     # ARG_Weather_clear_dry (gen.CLEAR_DRY, world-panel's and creature-spots')
WEATHER_READ = "{read: [weather], path: current.editor_id, eq: ARG_Weather_clear_dry, within: 20}"


def score(b: Build, x: float, y: float, subj: tuple) -> dict:
    """The clearance numbers of a stand looking at `subj`: plants on the line (to the subject + 2 m), canopy over the
    eye (10 m), tall grass near the eye and under the line's first 20 m (or to the subject), the stand's own faults."""
    eye = eye_of(b, x, y)
    h, p = aim(eye, subj)
    d_m = math.hypot(subj[0] - x, subj[1] - y) / U
    line, canopy = clearance(b, eye, h, line_m=d_m + 2.0)
    grass = grass_hits(b, eye, h, line_m=min(20.0, d_m))
    bad = stand_bad(b, x, y, subj)
    return {"line": line, "canopy": canopy, "grass": grass, "bad": len(bad), "wet": b.wet(x, y),
            "d_m": round(d_m, 1), "h": h, "p": p}


def _key(s: dict) -> tuple:
    return (s["wet"], s["bad"] > 0, s["line"], s["canopy"], s["grass"])   # what hides the subject most first


def clear(s: dict) -> bool:
    return _key(s) == (False, False, 0, 0, 0)


def best_stand(b: Build, subj: tuple, band_m: tuple, first_bearing: float, spread: float = 180.0, step: float = 15.0):
    """The stand off `subj` in the distance band (metres, nearest the band's middle first) on bearings from the subject
    within +-spread of first_bearing, fewest hits; the first fully clear one wins. (x, y, score)."""
    mid = (band_m[0] + band_m[1]) / 2
    ds = sorted({float(d) for d in range(int(band_m[0]), int(band_m[1]) + 1)} | {mid}, key=lambda d: abs(d - mid))
    brgs = [first_bearing] + [first_bearing + s * k * step for k in range(1, int(spread / step) + 1) for s in (1, -1)]
    best = None
    for brg in brgs:
        for d in ds:
            x = subj[0] + math.sin(math.radians(brg)) * d * U
            y = subj[1] + math.cos(math.radians(brg)) * d * U
            sc = score(b, x, y, subj)
            if clear(sc):
                return x, y, sc
            if best is None or _key(sc) < _key(best[2]):
                best = (x, y, sc)
    return best


def _numbers(s: dict) -> str:
    return (f"line {s['line']} canopy {s['canopy']} grass {s['grass']} bad {s['bad']}{' wet' if s['wet'] else ''}, "
            f"{s['d_m']} m to the subject, heading {s['h']:.0f} pitch {s['p']:.0f}")


def reaim(b: Build, text: str, name: str, log: list, band=lambda d: (max(2.0, d * 0.8), d * 1.6),
          spread: float = 180.0) -> str:
    """Each setpos step with a `# subject:` re-stood by the clearance measure when its stand is not clear: the same
    subject, a distance in band(d0), the nearest bearing; seated, aimed at the subject (the middle of the frame)."""
    lines = text.splitlines()
    for step, a, z in steps_of(text):
        blk = "\n".join(lines[a:z])
        pos = {k: float(v) for k, v in SETPOS.findall(blk)}
        m = SUBJECT.search(blk)
        if not ({"x", "y"} <= set(pos) and m):
            continue
        subj = tuple(float(v) for v in m.groups())
        x, y = pos["x"], pos["y"]
        sc = score(b, x, y, subj)
        moved = 0.0
        if not clear(sc):
            brg = math.degrees(math.atan2(x - subj[0], y - subj[1])) % 360
            nx, ny, nsc = best_stand(b, subj, band(sc["d_m"]), brg, spread)
            if _key(nsc) < _key(sc):
                moved, x, y, sc = round(math.hypot(nx - x, ny - y) / U, 1), nx, ny, nsc
        new = {"x": x, "y": y, "z": b.ground_u(x, y) + SEAT_U}
        ang = {"z": sc["h"], "x": sc["p"]}
        for i in range(a, z):
            lines[i] = SETPOS.sub(lambda mm: f"player.setpos {mm.group(1)} {new[mm.group(1)]:.0f}", lines[i])
            lines[i] = SETANGLE.sub(lambda mm: f"player.setangle {mm.group(1)} {ang[mm.group(1)]:.0f}", lines[i])
        log.append({"journey": name, "step": step, "moved_m": moved, "clear": clear(sc),
                    "why": "clearance: " + _numbers(sc)})
    return "\n".join(lines) + "\n"


def booth_standard(text: str) -> str:
    """The rock and tree booths (block YAML from vegetation/booth.py, tree_booth.py) to the standard: `look: world`,
    `hud: off` first in each step, the clear-dry weather set and forced by form id (not the editor id) and read back."""
    if not re.search(r"^look: world$", text, re.M):
        text = re.sub(r"^(id: .*)$", r"\1\nlook: world", text, count=1, flags=re.M)
    if not re.search(r"^independent_steps:", text, re.M):
        text = re.sub(r"^(runner: 1)$", r"\1\nindependent_steps: true", text, count=1, flags=re.M)
    text = re.sub(r"^  do:\n(?!  - hud: off\n)", "  do:\n  - hud: off\n", text, flags=re.M)
    text = re.sub(r"^  - console:\n      line: fw ARG_Weather_clear_dry\n",
                  f"  - console: sw {CLEAR_DRY}\n  - console: fw {CLEAR_DRY}\n  - settle: {{cap: 14, min: 3}}\n", text, flags=re.M)
    text = re.sub(r"^  expect:\n(?!  - \{read: \[weather\])", f"  expect:\n  - {WEATHER_READ}\n", text, flags=re.M)
    lines = text.splitlines()   # a step with no expect at all gets one: the weather read
    for name, a, z in reversed(steps_of(text)):
        if not any(ln.startswith("  expect:") for ln in lines[a:z]):
            lines[z:z] = ["  expect:", f"  - {WEATHER_READ}"]
    return "\n".join(lines) + "\n"


# -- ground-materials --------------------------------------------------------------------------------------------------
GROUND_AT = (("pebble-field", (-9, 27), "the ground away from the water's edge is varied forest floor, grass or moss, "
              "not one flat grey-green pebble texture over the whole view; the pebbly edge texture only in a thin strip "
              "along the water, no ground looks wet, shiny or mirror-like in the sun"),
             ("hillside", (-50, 8), "the hillside ground is matte with visible relief in its texture (stones, roots, "
              "tufts lit from one side), no shiny or reflective sheen on slopes facing the sun"))
GROUND_BAND_M = (8.0, 15.0)    # the patch 8-15 m off, pitched down at it
GROUND_PITCH_DEG = 20.0



def _ground_subject(b: Build, cell: tuple) -> tuple:
    """The dry ground patch nearest the cell's middle (on an 8 m grid out to 40 m) with a clear stand 8-15 m off that
    looks down at it at about GROUND_PITCH_DEG; (subject, x, y, score)."""
    ox, oy = su.cell_origin(*cell)
    cx, cy = ox + su.CELL_UNITS / 2, oy + su.CELL_UNITS / 2
    best = None
    pts = sorted(((i, j) for i in range(-5, 6) for j in range(-5, 6)), key=lambda c: c[0] ** 2 + c[1] ** 2)
    for i, j in pts:
        sx, sy = cx + i * 8 * U, cy + j * 8 * U
        if b.wet(sx, sy):
            continue
        subj = (sx, sy, b.ground_u(sx, sy))
        x, y, sc = best_stand(b, subj, GROUND_BAND_M, 180.0, 180.0, 30.0)
        k = (_key(sc), abs(sc["p"] - GROUND_PITCH_DEG))
        if best is None or k < best[0]:
            best = (k, subj, x, y, sc)
        if clear(sc) and abs(sc["p"] - GROUND_PITCH_DEG) <= 8:
            break
    return best[1:]


def ground_materials(b: Build, log: list, head: list[str]) -> str:
    out = head + ["id: ground-materials", "look: world",
                  'reach: [esm, "tools/argonia_world/terrain/**", data/mesh-textures.json, data/dependencies.json]   '
                  "# the pass ledger's inputs (tools/pass_ledger.py)",
                  "runner: 1", "independent_steps: true", "crash_risk: medium", "relaunch_before: false",
                  "scene: claywater", "camera: first", "steps:"]
    for name, cell, reader in GROUND_AT:
        subj, x, y, sc = _ground_subject(b, cell)
        log.append({"journey": "ground-materials", "step": name, "moved_m": 0.0, "clear": clear(sc),
                    "why": "clearance: " + _numbers(sc)})
        out += [f"  - name: {name}", f"    # cell {cell[0]} {cell[1]}: the dry patch nearest its middle with a clear stand "
                f"8-15 m off; {_numbers(sc)}",
                f"    # subject: {subj[0]:.0f} {subj[1]:.0f} {subj[2]:.0f}", "    do:", "      - hud: off",
                f"      - console: {{line: cow ARG_Province {cell[0]} {cell[1]}, settle: 60}}", "      - wait: 8",
                "      - console: set gamehour to 13", f"      - console: sw {CLEAR_DRY}", f"      - console: fw {CLEAR_DRY}",
                "      - settle: {cap: 14, min: 3}",
                f"      - console: player.setpos x {x:.0f}", f"      - console: player.setpos y {y:.0f}",
                f"      - console: player.setpos z {b.ground_u(x, y) + SEAT_U:.0f}", "      - wait: 6",
                f"      - console: player.setangle z {sc['h']:.0f}", f"      - console: player.setangle x {sc['p']:.0f}",
                "      - wait: 4",
                "    expect:", '      - {console: "player.GetInWorldspace ARG_Province", contains: ">> 1"}',
                f"      - {WEATHER_READ}", f"    reader: [{reader}]"]
    return "\n".join(out) + "\n"
