"""tests/journeys/creature-spots.yaml and tests/scenes/creature-spots.txt from a planner run (1.15 §g.4).

Journeys stay simple (owner, 2026-11-01): the mods' creatures are checked as placed, never walked to or fought.
Six spawn points of three habitats (water, marsh, upland), two of each in different cells, one visited by day and
teleport to dry ground beside the point, wait, and read state only (owner 19:05 #41: no stills): the spawn's own
reference and the actors loaded within READ_M, their kinds against the spot's list. Then one teleport to a predator
den (the run's first den), its predator read the same way. No walking, no fighting.

    python3 -m tools.argonia_world.creatures journey [--out out/creatures]
"""
from __future__ import annotations

import json
from pathlib import Path

from tools.argonia_world import skyrim_units as su

ROOT = Path(__file__).resolve().parents[3]
HABITATS = {  # name -> (media, region classes)
    "water": (("water", "shore"), None),
    "marsh": (("land",), ("deep-sink-basin", "interior-swamp", "flooded-forest", "rootland")),
    "upland": (("land",), ("western-frontier", "northern-transition")),
}
HOURS = (("a", 13), ("b", 11))  # both by day (round 6: the round-4 night stills were unjudgeable, dark)
READ_M = 40.0
BAND_M = (15, 25)  # the stand: this far from its spawn point, facing it (round 6: the round-4 stands 8 m off saw foliage)
WAIT_S = 6


def spots(refs: list[dict]) -> list[tuple[str, str, int, dict]]:
    out = []
    for name, (media, classes) in HABITATS.items():
        pts = [r for r in refs if r["kind"] == "spawn" and r["medium"] in media
               and (classes is None or r["class"] in classes)]
        cells: list = []
        for r in sorted(pts, key=lambda r: (r["cell"], r["x"], r["y"])):
            if tuple(r["cell"]) not in [tuple(c["cell"]) for c in cells]:
                cells.append(r)
        for k, r in enumerate(cells):  # every candidate, best first: the builder keeps the first two with a stand
            out.append((name, *HOURS[k % 2], r))
    return out


def _stand(b, r: dict, refs: list[dict], log: list, name: str):
    """A dry stand BAND_M off the spawn point with a clear eye line, the point the nearest spawn to it; None if none."""
    import math
    from tools.journeys import aim, eye_of, place
    u = su.UNITS_PER_METRE
    subj = (r["x"], r["y"], b.ground_u(r["x"], r["y"]) + 0.5 * u) if r["medium"] != "water" else (r["x"], r["y"], r["z"])
    f = place(b, subj, 20 * u, [(270 + 45 * k) % 360 for k in range(8)], band=BAND_M)
    if not (f["clear"] and f["dry"]):
        return None
    d = math.hypot(f["x"] - r["x"], f["y"] - r["y"]) / u
    other = min((math.hypot(f["x"] - o["x"], f["y"] - o["y"]) / u for o in refs
                 if o is not r and o["kind"] in ("spawn", "predator")), default=1e9)
    if other < d:
        return None
    h, p = aim(eye_of(b, f["x"], f["y"]), subj)
    log.append({"journey": "creature-spots", "step": name, "moved_m": f["moved_m"], "why": f["why"], "clear": True,
                "dist_m": round(d, 1), "next_spawn_m": round(other, 1)})
    return f["x"], f["y"], b.ground_u(f["x"], f["y"]) + 4.0, h, p, subj, d, other


def _go(r: dict, x, y, z, hour: int) -> list[str]:
    cx, cy = r["cell"]
    return [f"  - console: {{line: cow ARG_Province {cx} {cy}, settle: 60}}",
            "  - wait: 8",
            f"  - console: set gamehour to {hour}",
            f"  - console: player.setpos x {x:.0f}",
            f"  - console: player.setpos y {y:.0f}",
            f"  - console: player.setpos z {z:.0f}",
            f"  - wait: {WAIT_S}"]


def ref_ids(refs: list[dict]) -> dict[int, str]:
    """id(ref) -> its placed reference as `ArgoniaWorld.esm|0x...`: the k-th ref of its cell, as records.write_shards numbers them."""
    from tools.argonia_world.creatures import records
    n: dict = {}
    out = {}
    for r in refs:
        cx, cy = r["cell"]
        k = n.get((cx, cy), 0)
        n[(cx, cy)] = k + 1
        out[id(r)] = f"{records.PLUGIN}|0x{records.ref_id(cx, cy, k):06X}"
    return out


def list_kinds(w, list_id: str) -> list[str]:
    """The kinds (roster names) of one levelled list: the region class and band's own, never a levelled one (0035)."""
    return [x["name"] for x in w.query(
        "SELECT DISTINCT c.name FROM creature_list_entry e JOIN creature_form f ON f.form_key = e.form_key "
        "JOIN creature c ON c.id = f.creature_id WHERE e.list_id = ? ORDER BY c.name", list_id)]


def creature_name(w, cid: str) -> list[str]:
    return [x["name"] for x in w.query("SELECT name FROM creature WHERE id = ?", cid)]


def _reads(key: str, ref: str, radius: float, among: list[str]) -> list[str]:
    """The state reads of one stop: the spawn's own reference placed, enabled, loaded and of a kind of its list;
    the actors within READ_M at least one, and of the list's kinds at least one. All kept in report.json."""
    rad = f"\"{radius:.0f}\""
    a = json.dumps(among)
    return ["  - {read: [player], path: pos, keep: " + f"{key}_arrive" + "}",
            f"  - {{read: [actors, {rad}, \"{ref}\"], path: refs.0, ne: null, keep: {key}_spawn}}",
            f"  - {{read: [actors, {rad}, \"{ref}\"], path: refs.0.disabled, eq: false}}",
            f"  - {{read: [actors, {rad}, \"{ref}\"], path: refs.0.loaded_3d, eq: true}}",
            f"  - {{read: [actors, {rad}, \"{ref}\"], path: refs, kinds: {{ge: 1, among: {a}}}, keep: {key}_spawn_kind}}",
            f"  - {{read: [actors, {rad}], path: listed.0, ne: null, keep: {key}_first}}",
            f"  - {{read: [actors, {rad}], path: listed, keep: {key}}}",
            f"  - {{read: [actors, {rad}], path: listed, kinds: {{ge: 1, among: {a}}}, keep: {key}_kinds}}"]


def plugin_id(key: str) -> str:
    """`0D0044:ArgoniaWorld.esm` (a FormKey) as `ArgoniaWorld.esm|0x0D0044`, which the runner turns into this launch's runtime id."""
    local, plugin = key.split(":", 1)
    return f"{plugin}|0x{local}"


def probe_steps(w, name: str, r: dict, ref: str, go: list[str], among: list[str], subj: tuple) -> list[str]:
    """The land-spawn probe (lane 1.15-r6-land-spawn-probe): at a stop whose land spawn read nothing, three steps from the
    same stand. `<name>-probe` keeps every field of the spawn's reference as the bridge reads it (the actors read by id,
    the `refs` read of its template base: count, enabled, disabled) and the actors near. `<name>-probe-list` places the
    spot's own levelled list by console and keeps the actors within READ_M; at least one a kind of the list, else
    the list does not generate (the ACHR or zone path is then not the fault). `<name>-probe-entry` places one concrete
    NPC_ entry of that list the same way: does a concrete entry spawn. Every read is kept before the assertion."""
    from tools.argonia_world.creatures import records
    rad = f"\"{READ_M * su.UNITS_PER_METRE:.0f}\""
    a = json.dumps(among)
    tmpl = plugin_id(records.template_key(r["base"]))
    lvln = plugin_id(records.list_key(r["base"]))
    first = w.query("SELECT form_key FROM creature_list_entry WHERE list_id = ? ORDER BY form_key LIMIT 1", r["base"])[0]["form_key"]
    entry = plugin_id(records.actor_key(w, first, r["band"]))
    k = name.replace("-", "_") + "_probe"
    out = [f"- name: {name}-probe",
           f"  # the land-spawn probe, state of the spawn ref {ref} (template NPC_ {tmpl}, list {lvln}) at the {name} stand; keeps every field",
           f"  # subject: {subj[0]:.0f} {subj[1]:.0f} {subj[2]:.0f}",
           "  do:", *go, "  expect:",
           "  - {read: [player], path: pos, keep: " + k + "_arrive}",
           f"  - {{read: [actors, {rad}, \"{ref}\"], path: refs, keep: {k}_spawn}}",
           f"  - {{read: [actors, {rad}, \"{ref}\"], path: counts, keep: {k}_counts}}",
           f"  - {{read: [refs, \"{tmpl}\", {rad}], path: count, keep: {k}_template_count}}",
           f"  - {{read: [refs, \"{tmpl}\", {rad}], path: refs, keep: {k}_template_refs}}",
           f"  - {{read: [actors, {rad}], path: listed, keep: {k}_before}}"]
    for step, what, form in (("list", f"the levelled list {lvln}", lvln), ("entry", f"its first concrete entry {entry}", entry)):
        kk = f"{k}_{step}"
        out += [f"- name: {name}-probe-{step}",
                f"  # player.placeatme {what} at the stand (follows {name}-probe, no new teleport); the actors within 40 m, at least one of the list's kinds",
                "  do:", f"  - console: player.placeatme {form} 1", f"  - wait: {WAIT_S}", "  expect:",
                f"  - {{read: [actors, {rad}], path: listed, keep: {kk}}}",
                f"  - {{read: [actors, {rad}], path: listed, kinds: {{ge: 1, among: {a}}}, keep: {kk}_kinds}}"]
    return out


def build(refs: list[dict], b, w, log: list | None = None) -> tuple[str, str]:
    log = [] if log is None else log
    radius = READ_M * su.UNITS_PER_METRE
    rid = ref_ids(refs)
    lines = ["# Creature spots (1.15 §g.4; round 6), generated by `python3 -m tools.argonia_world.creatures journey`: six",
             "# spawn points (water, marsh, upland, two each in different cells) and one predator den. A state check, no",
             "# stills (owner 19:05 #41, decision 0036 amended): teleport to dry ground 15-25 m from the point, wait, then",
             "# read by the bridge the spawn's own reference (ArgoniaWorld.esm|0x...: present, enabled, 3D loaded, its",
             "# actor a kind of the spot's list) and every actor within 40 m (at least one, at least one a kind of the",
             "# list of that region class and band, a fixed list, never levelled: 0035). The den reads its predator.",
             "# marsh-a-probe* (lane 1.15-r6-land-spawn-probe): the land spawn that read nothing, probed from the same stand.",
             "# A failure names the read; a failed step alone takes a still. No walking, no fighting (owner, 2026-11-01).",
             "id: creature-spots", "runner: 1", "independent_steps: true", "crash_risk: medium", "scene: creature-spots",
             "stills: false", "steps:"]
    done: dict = {}
    for name, when, hour, r in spots(refs):
        if done.get(name, 0) >= 2:
            continue
        st = _stand(b, r, refs, log, f"{name}-{when}")
        if st is None:
            continue
        x, y, z, h, p, subj, d, other = st
        n = done.get(name, 0)
        done[name] = n + 1
        hour = HOURS[n][1]
        step = f"{name}-{'ab'[n]}"
        log[-1]["step"] = step
        lines += [f"- name: {step}",
                  f"  # cell {tuple(r['cell'])} {r['class']} {r['band']} {r['medium']}: list {r['base']}, spawn ref {rid[id(r)]}; "
                  f"the stand {d:.0f} m from it, the next spawn point {other:.0f} m",
                  f"  # subject: {subj[0]:.0f} {subj[1]:.0f} {subj[2]:.0f}",
                  "  do:", *(["  - console: tgm"] if not lines[-1].startswith("  -") else []),
                  *_go(r, x, y, z, hour),
                  "  expect:", *_reads(step.replace("-", "_"), rid[id(r)], radius, list_kinds(w, r["base"]))]
        if step == "marsh-a":   # lane 1.15-r6-land-spawn-probe: a D3 land spawn read nothing in r6-chain23
            lines += probe_steps(w, step, r, rid[id(r)], _go(r, x, y, z, hour), list_kinds(w, r["base"]), subj)
    for den in (r for r in refs if r["kind"] == "den"):
        pred = next((o for o in refs if o["kind"] == "predator" and o["cell"] == den["cell"]
                     and o.get("creature") == den["creature"]), None)
        st = pred and _stand(b, pred, [o for o in refs if o is not den], log, "den")
        if not st:
            continue
        x, y, z, h, p, subj, d, other = st
        lines += [f"- name: den-{den['creature'].split('.')[-1]}",
                  f"  # {den['creature']} den in cell {tuple(den['cell'])}, {den['class']} {den['band']}; predator ref "
                  f"{rid[id(pred)]}; the stand {d:.0f} m from it",
                  f"  # subject: {subj[0]:.0f} {subj[1]:.0f} {subj[2]:.0f}",
                  "  do:", *_go(den, x, y, z, 12),
                  "  expect:", *_reads("den", rid[id(pred)], radius, creature_name(w, den["creature"]))]
        break
    scene = ("; Creature spots (1.15 §g.4): god mode so a bite does not end the visit; sets nothing it tests\n"
             "tgm\n")
    return "\n".join(lines) + "\n", scene


def write(out: Path) -> tuple[Path, Path]:
    """Plan the 1.15 sample on the newest frozen ground (the one the next plugin build uses) and write both files."""
    from tools.argonia_world import db
    from tools.argonia_world.creatures import build as cb
    from tools.argonia_world.terrain.grid import Sources
    from tools.argonia_world.terrain.world import SAMPLE_1_15
    from tools.argonia_world.water import solve
    g = sorted((ROOT / "out" / "terrain" / "build").glob("*/ground-f32.npy"), key=lambda p: p.stat().st_mtime)[-1]
    w = db.open()
    run = cb.run(w, Sources.load(ground=g), solve.load(w), cb.sample_cells(SAMPLE_1_15), None, log=lambda s: None,
                 veg=ROOT / "out" / "terrain" / "vegetation")
    from tools.journeys import Build
    log: list = []
    y, s = build(run["refs"], Build(), w, log)
    for r in log:
        print(f"creature-spots: {r['step']}: stand {r['dist_m']} m from its point, the next spawn point {r['next_spawn_m']} m")
    jp, sp = ROOT / "tests" / "journeys" / "creature-spots.yaml", ROOT / "tests" / "scenes" / "creature-spots.txt"
    jp.write_text(y)
    sp.write_text(s)
    return jp, sp


if __name__ == "__main__":
    print(write(ROOT / "out" / "creatures"))
