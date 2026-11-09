"""python -m tools.places <verb> [args]: each verb is the module tools.places.<verb> (dashes as underscores)
with a main(argv) -> int. Adding a verb is adding a module; this file does not change."""
import importlib
import pkgutil
import sys

import tools.places as pkg


def main(argv: list[str]) -> int:
    verbs = sorted(m.name.replace("_", "-") for m in pkgutil.iter_modules(pkg.__path__) if not m.name.startswith("_"))
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
    return int(mod.main(argv[1:]) or 0)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
