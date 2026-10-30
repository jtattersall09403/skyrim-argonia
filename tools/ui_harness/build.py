"""Bundle ui/views for the web view (1.2): esbuild per view, the theme, Pelagiad and the chart layers into out/ui/views/.

What the installer does on the player's machine (decision 0014), done here for the L3 harness:
- each view's main.ts -> <view>/main.js (one IIFE, no runtime dependency), its CSS and an index.html;
- Pelagiad from $ARGONIA_PRIVATE/fonts/pelagiad (never committed) -> fonts/Pelagiad.ttf;
- the chart's base, revealed and ink layers (out/chart, 2.W4 §c) and the cell rects of its index.json ->
  chart/assets/ (index.js sets window.ARGONIA_CHART_INDEX, so the view needs no fetch from file://).

esbuild is pinned in infra/build-vm/toolchain.lock (npm:esbuild) and lives in ~/.argonia/npm.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VIEWS = ("dialogue", "journal", "hud", "chart")
OUT = ROOT / "out" / "ui" / "views"
NPM = Path.home() / ".argonia" / "npm"
CHART_LAYER_PX = 2048


def private() -> Path:
    return Path(os.environ.get("ARGONIA_PRIVATE") or Path.home() / "argonia-private")


def lock_version(name: str) -> str:
    for line in (ROOT / "infra" / "build-vm" / "toolchain.lock").read_text().splitlines():
        if line.startswith(f"{name}="):
            return line.split("=", 1)[1].split()[0]
    raise SystemExit(f"{name} is not pinned in infra/build-vm/toolchain.lock")


def esbuild() -> Path:
    """The pinned esbuild, installed into ~/.argonia/npm on first use."""
    want = lock_version("npm:esbuild")
    exe = NPM / "node_modules" / ".bin" / "esbuild"
    have = subprocess.run([exe, "--version"], capture_output=True, text=True).stdout.strip() if exe.exists() else ""
    if have != want:
        NPM.mkdir(parents=True, exist_ok=True)
        subprocess.run(["npm", "install", "--no-audit", "--no-fund", "--prefix", str(NPM), f"esbuild@{want}"],
                       check=True, capture_output=True)
    return exe


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Argonia {view}</title>
<link rel="stylesheet" href="../core/theme.css"><link rel="stylesheet" href="{view}.css">
</head><body><div id="view"></div>{pre}<script src="main.js"></script></body></html>
"""


def chart_index(src: Path) -> dict:
    """The cell rects of out/chart/index.json, without the tile numbers the view does not need."""
    ix = json.loads(src.read_text())
    return {"size": ix["size"], "cells": {k: v[2:6] for k, v in ix["cells"].items()}}


def build(out: Path = OUT, chart_dir: Path | None = None, minify: bool = True) -> dict:
    exe = esbuild()
    out.mkdir(parents=True, exist_ok=True)
    (out / "core").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "ui/views/core/theme.css", out / "core/theme.css")
    entries = [str(ROOT / f"ui/views/{v}/main.ts") for v in VIEWS]
    cmd = [str(exe), *entries, "--bundle", "--format=iife", "--target=es2020", f"--outdir={out}",
           "--outbase=" + str(ROOT / "ui/views"), "--log-level=warning"]
    if minify:
        cmd.append("--minify")
    subprocess.run(cmd, check=True)
    for v in VIEWS:
        d = out / v
        shutil.copyfile(ROOT / f"ui/views/{v}/{v}.css", d / f"{v}.css")
        pre = '<script src="assets/index.js"></script>' if v == "chart" else ""
        (d / "index.html").write_text(PAGE.format(view=v, pre=pre))
    font = private() / "fonts" / "pelagiad" / "Pelagiad.ttf"
    (out / "fonts").mkdir(exist_ok=True)
    have_font = font.exists()
    if have_font:
        shutil.copyfile(font, out / "fonts/Pelagiad.ttf")
    chart_dir = chart_dir or ROOT / "out" / "chart"
    have_chart = (chart_dir / "index.json").exists()
    if have_chart:
        a = out / "chart" / "assets"
        a.mkdir(parents=True, exist_ok=True)
        for n in ("base", "revealed", "ink"):
            shutil.copyfile(chart_dir / f"{n}-{CHART_LAYER_PX}.png", a / f"{n}-{CHART_LAYER_PX}.png")
        (a / "index.js").write_text("window.ARGONIA_CHART_INDEX=" + json.dumps(chart_index(chart_dir / "index.json"),
                                                                                separators=(",", ":")) + ";\n")
    return {"out": str(out), "font": have_font, "chart": have_chart}


if __name__ == "__main__":
    print(json.dumps(build()))
