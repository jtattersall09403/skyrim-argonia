#!/usr/bin/env python3
"""Fill the journey linter's vocabulary cache (lane journey-lint): the bridge's `vocab` read (console and script
function names with their parameter counts, the actor value names the `av` read accepts) and our placed refs' editor
ids from the world database, into $ARGONIA_PRIVATE/vocab.json. Game-derived names: never committed (decision 0003).
DEV ONLY; needs the game running with ArgoniaBridge.

    python3 tools/fetch_vocab.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> None:
    from tools import journey_lint, ref_ids
    from tools.bridge import Bridge
    v = Bridge().call("vocab", timeout=30)
    v["refs"] = sorted(w for w in ref_ids.ref_rows() if w.startswith("ARG_Ref_"))
    out = journey_lint.vocab_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(v, indent=1))
    print(f"{out}: {len(v['functions'])} functions, {len(v['actor_values'])} actor values, {len(v['refs'])} refs")


if __name__ == "__main__":
    main()
