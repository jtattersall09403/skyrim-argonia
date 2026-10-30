"""The per-cell plane budget (2.W2): a cell holds at most BUDGET water-plane references.

The budget holds by design (design.py, steps.py, oriented.py; the owner's ruling of 2026-10-29): nothing reduces a
cell after it is planned and nothing falls back. A cell over the budget is a hard error that names the cell, and the
design is what changes.

The number is measured, not ruled (the planner's ruling of 2026-10-30, docs/research/journals/water.md): the
designed cells (-39,-43), (-32,-16) and (-58,11) at 127, 65 and 32 planes showed no frame cost against the bar
(every median on the 60 fps cap), so the budget covers the designed maximum. If the owed uncapped run shows a cost,
the budget tightens with its reason recorded there.
"""
from __future__ import annotations

from tools.argonia_world.water import plan

BUDGET = 128


def count(cp) -> int:
    return sum(len(plan.squares(p)) for p in cp.planes) + len(cp.oplanes)


def over(cells: dict, budget: int = BUDGET) -> list[str]:
    """Every cell over the budget, as `(cx,cy): planes`, worst first."""
    bad = sorted(((count(cp), k) for k, cp in cells.items() if count(cp) > budget), reverse=True)
    return [f"({k[0]},{k[1]}): {c} planes" for c, k in bad]
