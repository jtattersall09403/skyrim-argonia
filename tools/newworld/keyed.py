"""A stage tool that skips on a key of its own, run for the rebuild: the run's build key folded into the tool's key.

    python3 -m tools.newworld.keyed land|landcover|place|paint [the tool's own arguments]

tools/newworld/rebuild.py runs the land shards, the landcover, the placed refs and the ground paint through this.
Each of those tools skips, or resumes by row, when the key it stored beside its output is the key it computes
today, and that key covers less than the stage reads. With `NW_STAGE_KEY` set (the rebuild sets it to the digest of
everything the stage's commands read), the tool's key has it appended: the tool skips only what it built for this
very build key, resumes when the same run is started again, and builds anew when anything the stage reads has
changed. Without it the tool runs as it does by hand, on its own key.

The fold is made here, outside the tools, because each of them hashes its own file into its key: a line added to
the tool would make its whole standing output stale. TOOLS names, for each, the module and the function that
returns the part of its key the build key is appended to, and the module whose `main` is run.
"""
from __future__ import annotations

import importlib
import os
import sys

TOOLS = {
    "land": ("tools.newworld.world.land", "code_key", "tools.newworld.world.land"),
    "landcover": ("tools.newworld.landcover", "_hash", "tools.newworld.landcover"),
    "place": ("tools.newworld.place.place", "key", "tools.newworld.place.__main__"),
    "paint": ("tools.newworld.world.texture", "code_key", "tools.newworld.world.texture"),
}


def fold(name: str, stage_key: str | None):
    """The tool's entry module, its key function wrapped to end with the build key when there is one."""
    mod_name, attr, entry = TOOLS[name]
    mod = importlib.import_module(mod_name)
    if stage_key:
        own = getattr(mod, attr)
        setattr(mod, attr, lambda *a, **k: f"{own(*a, **k)}:{stage_key}")
    return importlib.import_module(entry)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in TOOLS:
        print(f"usage: python3 -m tools.newworld.keyed {'|'.join(TOOLS)} [the tool's arguments]", file=sys.stderr)
        return 2
    return int(fold(argv[0], os.environ.get("NW_STAGE_KEY")).main(argv[1:]) or 0)


if __name__ == "__main__":
    sys.exit(main())
