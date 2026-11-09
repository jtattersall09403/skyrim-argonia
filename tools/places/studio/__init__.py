"""The place studio (docs/design/place-studio.md): the server in this package, the front end in web/.

  python -m tools.places studio [--host 127.0.0.1] [--port 8765]   serve (systemd: infra/build-vm/studio.service)
"""
from __future__ import annotations

import argparse


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places studio")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args(argv)
    from aiohttp import web

    from tools.places.studio.server import make_app
    web.run_app(make_app(), host=a.host, port=a.port, access_log=None)
    return 0
