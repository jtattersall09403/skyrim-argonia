"""The look audit's checks, run by truth.py in a child whose environment points the look tool at the scene."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from tools.places.look import daemon
from tools.places.look.scene import LOOK_OUT, data_out

RESULTS: list[dict] = []


def check(group: str, name: str, ok: bool, detail="", xfail: str | None = None, png: str | None = None):
    status = ("XPASS" if ok else "XFAIL") if xfail else ("PASS" if ok else "FAIL")
    RESULTS.append({"group": group, "check": name, "status": status, "detail": detail, **({"xfail": xfail} if xfail else {}),
                    **({"png": png} if png else {})})
    print(f"{status:5} {group} {name}" + (f": {detail}" if detail and status != "PASS" else "") + (f" [{xfail}]" if xfail else ""),
          flush=True)
    return ok


def boot() -> daemon.Daemon:
    LOOK_OUT.mkdir(parents=True, exist_ok=True)
    d = daemon.Daemon()
    d.shared_out = data_out()
    os.environ["PLACES_OUT"] = str(daemon.own_out(d.shared_out, LOOK_OUT / "data"))
    d.start_server()
    d.start_browser()
    return d


def main(argv: list[str]) -> int:
    root = Path(argv[0])
    d = boot()
    t0 = time.time()
    try:
        if "--fixture" in argv:
            from tools.places.look import truth_fixture
            truth_fixture.run(d, root, check)
        else:
            from tools.places.look import truth_sample
            truth_sample.run(d, argv[argv.index("--place") + 1], int(argv[argv.index("--sample") + 1]), check)
    except Exception as e:   # a crash is a failed check, with its trace
        import traceback
        check("harness", "ran to the end", False, f"{type(e).__name__}: {e}\n{traceback.format_exc()[-2000:]}")
    finally:
        d.stop()
    by: dict = {}
    for r in RESULTS:
        g = by.setdefault(r["group"], {"PASS": 0, "FAIL": 0, "XFAIL": 0, "XPASS": 0})
        g[r["status"]] += 1
    summary = {"seconds": round(time.time() - t0, 1), "groups": by, "failed": [r for r in RESULTS if r["status"] == "FAIL"],
               "expected_fail": [r for r in RESULTS if r["status"] in ("XFAIL", "XPASS")]}
    (root / "truth.json").write_text(json.dumps({"summary": summary, "results": RESULTS}, indent=1, default=str))
    print(json.dumps({k: v for k, v in summary.items() if k != "expected_fail"} | {"report": str(root / "truth.json")},
                     indent=1, default=str))
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
