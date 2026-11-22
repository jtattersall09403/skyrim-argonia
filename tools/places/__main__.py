"""python -m tools.places <verb> [args]: each verb is the module tools.places.<verb> (dashes as underscores)
with a main(argv) -> int. Adding a verb is adding a module with a main; this file does not change. A module with no
main is a library, never listed as a verb."""
import importlib
import pkgutil
import sys
from pathlib import Path

import tools.places as pkg


def is_verb(m) -> bool:
    """A package (its __init__) or a module whose source defines main()."""
    path = Path(pkg.__path__[0]) / m.name
    src = path / "__init__.py" if m.ispkg else path.with_suffix(".py")
    return src.is_file() and "\ndef main(" in src.read_text()


def main(argv: list[str]) -> int:
    verbs = sorted(m.name.replace("_", "-") for m in pkgutil.iter_modules(pkg.__path__)
                   if not m.name.startswith("_") and is_verb(m))
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: python -m tools.places <verb> [args]\nverbs: " + " ".join(verbs))
        return 0 if argv else 2
    name = argv[0].replace("-", "_")
    try:
        mod = importlib.import_module(f"tools.places.{name}")
    except ModuleNotFoundError as e:
        if e.name != f"tools.places.{name}":
            raise
        print(f"unknown verb {argv[0]!r}; verbs: " + " ".join(verbs), file=sys.stderr)
        return 2
    from tools.places import timelog
    st, rc = timelog.begin(argv), 1
    try:
        rc = int(mod.main(argv[1:]) or 0)
        return rc
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
        raise
    finally:
        timelog.record(argv, st, rc)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
