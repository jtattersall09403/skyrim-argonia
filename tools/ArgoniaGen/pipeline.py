#!/usr/bin/env python3
"""The record pipeline end to end (0.4 §a): `make plugin` and the gate's `plugin` part.

    pipeline.py plugin   scan the masters, index the pieces, write the intermediate JSON, generate Argonia.esm
                         (out/), serialise it with Spriggit into plugin/Argonia/
    pipeline.py check    the FormID table append-only; every design piece resolved; regenerate twice into
                         out/check/{a,b}: identical ESM bytes and YAML trees, and equal to the committed
                         plugin/Argonia/ (else: run `make plugin`); the Spriggit round trip: plugin/Argonia/
                         deserialised, put in canonical record order, is byte-identical to the generated ESM

Spriggit's deserialiser writes a group's records in directory-listing order, which is the filesystem's and not
the content's; `canon` puts every group in the raw-FormID order the generator writes, so the round trip
compares content. Game data: $ARGONIA_GAME_ROOT/Data, else ~/games/skyrimse/Data (read-only, never in git).
"""
from __future__ import annotations

import filecmp
import json
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"
YAML = ROOT / "plugin" / "Argonia"
PROJ = ROOT / "tools" / "ArgoniaGen"
GEN = PROJ / "bin" / "Release" / "net10.0" / "ArgoniaGen"
SPRIGGIT = ("-p", "Spriggit.Yaml", "-v", "0.41.0")  # pinned in infra/build-vm/toolchain.lock
HOME = Path.home()
ENV = dict(os.environ, DOTNET_ROOT=str(HOME / ".dotnet"), DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1",
           DOTNET_gcServer="0", DOTNET_GCHeapHardLimit="0xC0000000",  # workstation GC, 3 GB heap (memory guidance)
           PATH=f"{HOME / '.dotnet'}:{HOME / '.local/bin'}:{os.environ.get('PATH', '')}")
CAP = ["systemd-run", "--user", "--scope", "-q", "-p", "MemoryMax=3G"] if shutil.which("systemd-run") else []


def data_dir() -> Path:
    root = os.environ.get("ARGONIA_GAME_ROOT")
    d = Path(root) / "Data" if root else HOME / "games" / "skyrimse" / "Data"
    if not (d / "Skyrim.esm").exists():
        raise SystemExit(f"plugin: no Skyrim.esm under {d} (set ARGONIA_GAME_ROOT)")
    return d


def run(*cmd, capped=False, quiet=True):
    full = (CAP if capped else []) + [str(c) for c in cmd]
    r = subprocess.run(full, cwd=ROOT, env=ENV, capture_output=quiet, text=True, check=False)
    if r.returncode != 0:
        tail = ((r.stdout or "") + (r.stderr or ""))[-3000:] if quiet else ""
        raise SystemExit(f"plugin: failed: {' '.join(map(str, cmd))}\n{tail}")
    return r.stdout or ""


def build_tool():
    run("dotnet", "build", PROJ, "-c", "Release", "-nologo", "-v", "q", capped=True)


def scans(data: Path):
    """The vanilla scan and the piece index, remade only when the load order or a plugin changed."""
    sys.path.insert(0, str(ROOT))
    from tools.argonia_world.intermediate import load_order
    order = load_order(data)
    stamp = json.dumps([[p, (data / p).stat().st_size, int((data / p).stat().st_mtime)] for p in order])
    sf = OUT / "scan.stamp"
    if sf.exists() and sf.read_text() == stamp and (OUT / "vanilla-scan.json").exists() and (OUT / "pieces-index.json").exists():
        return
    plugins = ",".join(order)
    run(GEN, "quests", "--data", data, "--plugins", plugins, "--out", OUT / "vanilla-scan.json", capped=True)
    run(GEN, "index", "--data", data, "--plugins", plugins, "--out", OUT / "pieces-index.json", capped=True)
    sf.write_text(stamp)


def generate(data: Path, into: Path, frozen: bool) -> tuple[Path, Path]:
    """intermediate -> ESM -> YAML, all under `into`; returns (esm, yaml dir)."""
    into.mkdir(parents=True, exist_ok=True)
    inter, esm, yaml = into / "argonia.json", into / "Argonia.esm", into / "yaml"
    run(sys.executable, "-m", "tools.argonia_world.intermediate", "--data", data, "--out", inter,
        "--frozen", "1" if frozen else "0")
    run(GEN, "generate", "--in", inter, "--data", data, "--out", esm, capped=True)
    shutil.rmtree(yaml, ignore_errors=True)
    run("spriggit", "serialize", "-i", esm, "-o", yaml, "-g", "SkyrimSE", *SPRIGGIT, capped=True)
    return esm, yaml


# --- canonical record order -------------------------------------------------------------------------------
def canon(data: bytes) -> bytes:
    """The plugin with every group's entries in raw-FormID order; a record keeps its child group after it."""
    def entries(i: int, end: int) -> list[tuple[tuple, bytes]]:
        out = []
        while i < end:
            sig = data[i:i + 4]
            size = struct.unpack_from("<I", data, i + 4)[0]
            if sig == b"GRUP":
                body = b"".join(b for _, b in sorted(entries(i + 24, i + size)))
                blob = data[i:i + 4] + struct.pack("<I", 24 + len(body)) + data[i + 8:i + 24] + body
                gtype = struct.unpack_from("<i", data, i + 12)[0]
                if out and gtype in (1, 6, 7) and out[-1][0][0] == 0:  # a record's children follow it
                    k, b = out.pop()
                    out.append((k, b + blob))
                else:
                    label = data[i + 8:i + 12]
                    out.append(((1, gtype, label), blob))
                i += size
            else:
                fid = struct.unpack_from("<I", data, i + 12)[0]
                out.append(((0, fid), data[i:i + 24 + size]))
                i += 24 + size
        return out
    head = 24 + struct.unpack_from("<I", data, 4)[0]  # TES4 stays first
    top = entries(head, len(data))  # top groups keep their order (the game's group order)
    return data[:head] + b"".join(b for _, b in top)


def trees_equal(a: Path, b: Path) -> list[str]:
    fa = {p.relative_to(a).as_posix() for p in a.rglob("*") if p.is_file()}
    fb = {p.relative_to(b).as_posix() for p in b.rglob("*") if p.is_file()}
    diff = sorted(fa ^ fb)
    diff += sorted(f for f in fa & fb if not filecmp.cmp(a / f, b / f, shallow=False))
    return diff


def plugin() -> int:
    data = data_dir()
    build_tool()
    scans(data)
    esm, yaml = generate(data, OUT / "build", frozen=False)
    shutil.copyfile(esm, OUT / "Argonia.esm")
    shutil.rmtree(YAML, ignore_errors=True)
    shutil.copytree(yaml, YAML)
    n = sum(1 for _ in YAML.rglob("*.yaml"))
    print(f"plugin: out/Argonia.esm ({esm.stat().st_size} bytes), {n} YAML files in plugin/Argonia/")
    return 0


def check() -> int:
    data = data_dir()
    errs: list[str] = []
    r = subprocess.run([sys.executable, "-m", "tools.argonia_world.formids", "check"], cwd=ROOT, check=False, capture_output=True, text=True)
    if r.returncode:
        errs.append("formids: " + r.stdout.strip())
    build_tool()
    scans(data)
    r = subprocess.run([sys.executable, "-m", "tools.argonia_world.pieces", "check"], cwd=ROOT, check=False, capture_output=True, text=True)
    if r.returncode:
        errs.append("pieces: " + r.stdout.strip())
    a_esm, a_yaml = generate(data, OUT / "check" / "a", frozen=True)
    b_esm, b_yaml = generate(data, OUT / "check" / "b", frozen=True)
    if a_esm.read_bytes() != b_esm.read_bytes():
        errs.append("regenerate: the two ESMs differ")
    if d := trees_equal(a_yaml, b_yaml):
        errs.append(f"regenerate: the two YAML trees differ in {len(d)} files, first {d[:3]}")
    if not YAML.exists():
        errs.append("plugin/Argonia/ missing: run `make plugin`")
    elif d := trees_equal(a_yaml, YAML):
        errs.append(f"plugin/Argonia/ is stale in {len(d)} files (first {d[:3]}): run `make plugin` and commit")
    else:
        rt = OUT / "check" / "roundtrip.esm"
        run("spriggit", "deserialize", "-i", YAML, "-o", rt, *SPRIGGIT, capped=True)
        if canon(rt.read_bytes()) != a_esm.read_bytes():
            errs.append("round trip: plugin/Argonia/ deserialised is not byte-identical to the generated ESM")
    for e in errs:
        print(f"plugin: {e}")
    if not errs:
        print("plugin: regenerate twice identical; plugin/Argonia/ current; Spriggit round trip byte-identical")
    return 1 if errs else 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.exit(plugin() if cmd == "plugin" else check() if cmd == "check" else (print(__doc__) or 2))
