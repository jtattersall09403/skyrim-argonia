"""`python -m tools.places draft wholesale <place_id> --offset <units> ...` lays a place's baseline: its source carried
whole at one transform with the chosen part of its ground (tools/places/draft/wholesale.py; skill place-site), and
with `--rooms` and `--walks` the source's rooms and walks.
`python -m tools.places draft <place_id>` runs every stage on a place with no draft yet: the people, quest spots, fit
frame and plan a baseline is laid over. A place that holds the owner's finalised studio saves is never drafted whole
again without `--force "<why no narrow stage can be correct>"`.
`draft <stage> <place_id>` runs one stage alone on the place files as they stand, changing only the rows that
stage owns and printing the rows changed per file (tools/places/draft/stages.py): fit, ground (`--dry` prints what
it would do), pieces, seating, clearance, streets (also `join`), people, lights, stations, jail, primitives, hang,
sap, add, names, quests.
`draft check <place_id>` runs the draft's self-checks; `draft plan <place_id>` prints the plan's faults; `draft
structures <place_id>` lists each major source structure against the place record; `draft render <place_id>`
writes top-down PNGs."""
from __future__ import annotations

import json
import sys

USAGE = "usage: python -m tools.places draft [<stage>|wholesale|check|plan|structures|render] <place_id> [--force \"<why>\"]"


def refusal(place_id: str, force: str | None, places=None) -> str | None:
    """Why a whole draft of this place is refused, or None. A place with the owner's finalised saves is changed by
    the stage that owns what must change; a whole draft regenerates every row, the owner's included."""
    from tools.places.draft import io, stages
    saves = stages.owner_saves((places or io.PLACES) / place_id)
    if not saves or (force and force.strip()):
        return None
    return (f"draft {place_id}: refused: the place holds the owner's finalised studio saves ({', '.join(saves)}) and a "
            f"whole draft regenerates every row. Run the stage that owns what must change, on the files as they "
            f"stand: python -m tools.places draft <{'|'.join(stages.STAGES)}> {place_id}. A whole draft only when no "
            f"stage can be correct: --force \"<why>\".")


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    if argv[0] == "check":
        from tools.places.draft.check import main as m
        return m(argv[1:])
    if argv[0] == "render":
        from tools.places.draft.render import main as m
        return m(argv[1:])
    if argv[0] == "plan":
        from tools.places.draft.plan import main as m
        return m(argv[1:])
    if argv[0] == "wholesale":
        from tools.places.draft.wholesale import main as m
        return m(argv[1:])
    if argv[0] == "structures":
        from tools.places.draft.structures import main as m
        return m(argv[1:])
    from tools.places.draft import stages
    if argv[0] == "ground" and "--dry" in argv:
        from tools.places.draft import ground
        ids = [a for a in argv[1:] if not a.startswith("--")]
        ground.apply(stages.Standing(ids[0]), dry=True)
        return 0
    if argv[0] == "join" or argv[0] in stages.STAGES:
        if len(argv) != 2:
            print(USAGE, file=sys.stderr)
            return 2
        stage = "streets" if argv[0] == "join" else argv[0]
        try:
            counts = stages.run(stage, argv[1])
        except stages.StageError as e:
            print(str(e), file=sys.stderr)
            return 1
        print(json.dumps({"stage": stage, "place": argv[1], "rows": counts,
                          "files_changed": len(counts)}, indent=1))
        return 0
    from tools.places.draft.run import draft
    force = None
    if "--force" in argv:
        k = argv.index("--force")
        force = argv[k + 1] if k + 1 < len(argv) and not argv[k + 1].startswith("--") and len(argv) > 2 else ""
        if force in argv[:k] or (force and len([a for a in argv if not a.startswith("--")]) < 2):
            force = ""
        argv = argv[:k] + argv[k + (2 if force else 1):]
    ids = [a for a in argv if not a.startswith("--")]
    if len(ids) != 1:
        print(USAGE, file=sys.stderr)
        return 2
    why = refusal(ids[0], force)
    if why:
        print(why, file=sys.stderr)
        return 1
    if force is not None:
        print(f"draft {ids[0]}: whole draft forced: {force or 'no reason given'}")
    counts = draft(ids[0], force=force is not None)
    from tools.places.draft import walk
    counts["primitives"] = stages.run("primitives", ids[0])  # before the network: a collision box is a solid of it
    # joins, rehomed sleepers, streets and patrols laid on the built network; it leaves the files seated and canonical
    counts["network"] = walk.join(ids[0])
    counts["jail"] = stages.run("jail", ids[0])  # its release point is the arrival the join lays
    print(json.dumps(counts, indent=1))
    return 0
