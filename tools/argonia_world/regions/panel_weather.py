"""The world panel's weather and hour per land region (1.15 §d.3; tests/journeys/world-panel.yaml reads it): the noon
still under clear-dry (the sunny dry-season weather every list holds), the dawn still at 06:30 under its mist regime's weather (or,
with no regime, the same weather as noon). A form is given by EditorID and, once `make plugin` has allocated it, by
its FormKey (the console's `sw`, set without a transition after the moveto, takes the load-order id the scene resolves from it).

    python3 -m tools.argonia_world.regions.panel_weather       prints the table as JSON lines
"""
from __future__ import annotations

import json
import sys

from tools.argonia_world import db

DAWN_HOUR, NOON_HOUR = 6.5, 12.0
CLEAR = "clear-dry"


def table(w) -> list[dict]:
    keys = {r.editor_id: f"{r.form_id:06X}:{r.plugin}" for r in w.rows("formid") if r.record_type == "WTHR"}
    wx = {r["id"]: dict(r) for r in w.query("SELECT id, edid, form_key FROM weather")}

    def form(wid: str) -> dict:
        e = wx[wid]["edid"]
        return {"weather": wid, "edid": e, "form_key": wx[wid]["form_key"] or keys.get(e)}

    out = []
    for r in w.query("SELECT l.id, m.regime, mr.weather_id mist FROM land_region l JOIN region_mist m "
                     "ON m.land_region_id = l.id LEFT JOIN mist_regime mr ON mr.id = m.regime "
                     "WHERE l.border = 0 ORDER BY l.id"):
        # noon is the sunny dry-season clear weather every region's list holds (a visible sun for the god rays); the
        # dawn is the region's mist regime's weather, or clear-dry where it has none
        noon = CLEAR
        assert w.values("SELECT 1 FROM land_region_weather WHERE land_region_id = ? AND weather_id = ?", r["id"], CLEAR), \
            f"{r['id']}: no {CLEAR} in its list"
        out.append({"land_region": r["id"], "regime": r["regime"],
                    "noon": dict(form(noon), hour=NOON_HOUR), "dawn": dict(form(r["mist"] or noon), hour=DAWN_HOUR)})
    return out


def main(argv: list[str]) -> int:
    for row in table(db.open()):
        print(json.dumps(row))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
