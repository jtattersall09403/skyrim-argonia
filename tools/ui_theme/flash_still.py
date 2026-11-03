"""L3 stills of a themed Scaleform menu movie, drawn by Ruffle's headless exporter (decision 0021: L3 before L4).

frame_stills draws a mock with its own sample text; this renders the movie itself, so its text colours, the colour
transforms on placed clips, its layout and its art are the movie's. The movie is put into a state by a DoAction we
append as extra root frames (the engine's calls, made by hand: InitExtensions, RestoreSavedSettings, startPage,
the page's state calls, sample list entries), then drawn at the last frame. A second render with every text field
hidden gives the text mask: each text item's ink colour, the background behind it and their contrast ratio.

    python -m tools.ui_theme.flash_still <swf> --state system-settings --out out/ui/flash/settings.png
    python -m tools.ui_theme.flash_still <swf> --frame 1 --out raw.png        # a frame as authored, no driving
    python -m tools.ui_theme.flash_still <swf> --label fadeIn --out x.png     # _root.gotoAndStop(label) first

Ruffle: ~/.argonia/tools/ruffle/bin/ruffle-exporter (built by tools/ui_theme/ruffle/build_exporter.sh at a pinned
nightly; sourcing register). The fonts the movie imports from gfxfontlib.swf are served from our Pelagiad library
(fonts_pelagiad.swf, re-exported under the $-names fontconfig maps); what Ruffle cannot show is in the report.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from tools.ui_theme import swf
from tools.ui_theme.avm1 import Asm, Ref, hide_text_function, translate_function

EXPORTER = Path(os.environ.get("RUFFLE_EXPORTER", Path.home() / ".argonia/tools/ruffle/bin/ruffle-exporter"))
STACK = Path.home() / ".argonia/stack/MO2/mods"
STAGE_DIR = Path.home() / ".argonia/cache/flash-stills/stage"  # must be a lowercase path
DO_ACTION, SHOW_FRAME, END = 12, 1, 0
SETTLE = 40  # frames between the driving script and the capture (the faders run 10 frames at 30 fps)

JOURNAL = "_root.QuestJournalFader.Menu_mc"
SYSTEM = JOURNAL + ".SystemFader.Page_mc"
CATEGORIES = ["Save", "Load", "Creations", "Settings", "Mod configuration", "Controls", "Help"]
SAVES = [(272, "ArgoniaWalk"), (271, "argoniabase"), (250, "Argonia Claywater"), (249, "ArgoniaSuspend"),
         (247, "Argonia Western Frontier"), (244, "Argonia Tidal Delta"), (241, "Argonia Rootland")]


def _journal_open(a: Asm) -> None:
    """What the engine does when the Journal opens on its System tab (Quest_Journal.as, SkyUI source)."""
    a.call(JOURNAL, "InitExtensions")
    a.call(JOURNAL, "SetPlatform", 0, False)
    a.call(JOURNAL, "RestoreSavedSettings", 2, False)
    a.call(SYSTEM, "startPage")
    cats = [{"text": t, "index": i} for i, t in enumerate(CATEGORIES)]
    a.set(SYSTEM + ".CategoryList", "entryList", cats)
    a.call(SYSTEM + ".CategoryList", "InvalidateData")
    a.call(SYSTEM + ".VersionText", "SetText", "1.6.1170.0.8 (SKSE64 2.2.6 rel 0)")


def _settings(a: Asm) -> None:
    _journal_open(a)
    a.set(SYSTEM + ".SettingsList", "entryList",
          [{"text": t} for t in ("Gameplay", "Display", "Audio", "WindUI", "Graphics")])
    a.call(SYSTEM + ".SettingsList", "InvalidateData")
    a.call(SYSTEM, "StartState", 3)  # SETTINGS_CATEGORY_STATE


def _load(a: Asm) -> None:
    _journal_open(a)
    holder = SYSTEM + ".SaveLoadListHolder"
    a.set(holder, "isSaving", False)
    a.set(holder + ".List_mc", "entryList",
          [{"text": n, "fileNum": k, "index": i, "level": 1, "name": "Tsleeixth", "playTime": "1 h"}
           for i, (k, n) in enumerate(SAVES)])
    a.call(holder, "onSaveLoadBatchComplete", True)


def _main(a: Asm) -> None:
    _journal_open(a)


STATES = {"system-main": _main, "system-settings": _settings, "system-load": _load}


def _set_frame_count(movie: swf.Movie, n: int) -> None:
    movie.frame = movie.frame[:-2] + struct.pack("<H", n)


def _frame_count(movie: swf.Movie) -> int:
    return struct.unpack("<H", movie.frame[-2:])[0]


def drive(movie: swf.Movie, script: Asm | None, hide_text: bool, settle: int = SETTLE,
          table: dict[str, str] | None = None) -> int:
    """Append root frames: the driving script, `settle` empty frames, then (optionally) every text field hidden and
    stop(). Returns the 1-based frame to capture."""
    # the movie's frame-1 script stops the root timeline; play on into our frames
    first_show = next(i for i, t in enumerate(movie.tags) if t.code == SHOW_FRAME)
    movie.tags.insert(first_show, swf.Tag(DO_ACTION, Asm().call("_root", "play").bytes()))
    end = next(i for i, t in enumerate(movie.tags) if t.code == END)
    tags: list[swf.Tag] = []
    if script is not None:
        tags += [swf.Tag(DO_ACTION, script.bytes()), swf.Tag(SHOW_FRAME, b"")]
    tags += [swf.Tag(SHOW_FRAME, b"") for _ in range(settle)]
    last = Asm().push("argonia: last frame").op(0x26)
    if table:
        last.out += translate_function(table).out
        last.callf("__translate", Ref("_root"))
    if hide_text:
        last.out += hide_text_function().out
        last.callf("__hideText", Ref("_root"))
    last.push("argonia: captured").op(0x26).op(0x07)  # trace (render checks it ran), stop
    tags += [swf.Tag(DO_ACTION, last.bytes()), swf.Tag(SHOW_FRAME, b"")]
    movie.tags[end:end] = tags
    total = _frame_count(movie) + (1 if script is not None else 0) + settle + 1
    _set_frame_count(movie, total)
    return total


def _translations(roots: list[Path]) -> dict[bytes, bytes]:
    """$KEY -> text from every translate_english.txt and translations/*_english.txt under the roots (UTF-16)."""
    table: dict[bytes, bytes] = {}
    for r in roots:
        for f in [*r.glob("translate_english.txt"), *r.glob("translations/*_english.txt")]:
            for line in f.read_bytes().decode("utf-16", "replace").splitlines():
                k, _, v = line.partition("\t")
                if k.startswith("$") and v:
                    table[k.strip().encode()] = v.strip().encode()
    return table


def translate_static_text(movie: swf.Movie, table: dict[bytes, bytes]) -> int:
    """Scaleform shows a field's initial "$KEY" text through the translation table; Ruffle shows it raw, so the
    copy we draw carries the translated text. The count of fields changed."""
    n = 0
    for k, t in enumerate(movie.tags):
        if t.code != 37:  # DefineEditText
            continue
        d = t.data
        nbits = d[2] >> 3
        p = 2 + (5 + 4 * nbits + 7) // 8
        f1, f2 = d[p], d[p + 1]
        p += 2
        if not f1 & 0x80:
            continue
        p += 2 if f1 & 1 else 0
        p = d.index(0, p) + 1 if f2 & 0x80 else p
        p += (2 if f1 & 1 else 0) + (4 if f1 & 4 else 0) + (2 if f1 & 2 else 0) + (9 if f2 & 0x20 else 0)
        p = d.index(0, p) + 1  # the variable name
        e = d.index(0, p)
        text = d[p:e]
        new = re.sub(rb"\$[^<>$]+?(?=<|$)", lambda m: table.get(m.group(0).strip(), m.group(0)), text)
        if new != text:
            movie.tags[k] = swf.Tag(37, d[:p] + new + d[e:], True)
            n += 1
    return n


def default_roots(src: Path) -> list[Path]:
    """The interface folders a movie loads from, lowest priority first: the stack's Dear Diary, Wood and Paper and
    SkyUI, our overlay, then the folder the movie itself sits in (a rebuilt overlay wins over the deployed one)."""
    roots = [STACK / m / "interface" for m in ("skyui", "dear-diary", "wood-and-paper", "argonia-theme")]
    parts = src.resolve().parts
    if "interface" in [x.lower() for x in parts]:
        i = max(k for k, x in enumerate(parts) if x.lower() == "interface")
        roots.append(Path(*parts[: i + 1]))
    return [r for r in roots if r.is_dir()]


def stage(roots: list[Path], into: Path) -> None:
    """A case-blind union of the roots under `into` (lowercase symlinks; later roots win)."""
    for r in roots:
        for f in r.rglob("*"):
            if f.is_file():
                dst = into / str(f.relative_to(r)).lower()
                dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.is_symlink() or dst.exists():
                    dst.unlink()
                dst.symlink_to(f.resolve())


def font_library(src: Path | None) -> bytes | None:
    """gfxfontlib.swf for Ruffle: our Pelagiad library's font exported under every $-name the menus import."""
    from tools.ui_theme.fontlib import MAP, NAME
    src = src or STACK / "argonia-theme/interface/fonts_pelagiad.swf"
    if not src.is_file():
        return None
    m = swf.read(src.read_bytes())
    fid = next(int.from_bytes(t.data[:2], "little") for t in m.tags if t.code == 75)  # DefineFont3
    names = [k for k, v in MAP.items() if v == NAME]
    blob = struct.pack("<H", len(names)) + b"".join(struct.pack("<H", fid) + k.encode() + b"\0" for k in names)
    endi = next(i for i, t in enumerate(m.tags) if t.code == END)
    m.tags.insert(endi - 1, swf.Tag(56, blob, True))  # ExportAssets before the ShowFrame
    return m.to_bytes()


def render(src: Path, out: Path, *, state: str | None = None, frame: int | None = None, label: str | None = None,
           width: int = 1920, height: int = 1080, hide_text: bool = False, fontlib: Path | None = None,
           roots: list[Path] | None = None, script: Asm | None = None) -> str:
    """Draw the movie to `out`; returns the exporter's log (AVM traces and warnings, the files it fetched)."""
    movie = swf.read(src.read_bytes())
    roots = default_roots(src) if roots is None else roots
    table = _translations(roots)
    translate_static_text(movie, table)
    blob = swf.Movie(b"FWS", movie.version, movie.frame, movie.tags).to_bytes()
    used = {k.decode(): v.decode() for k, v in table.items() if k in blob}  # the keys the movie's scripts hold
    if frame is not None and state is None and label is None and script is None:
        capture = frame
    else:
        a = script
        if state:
            a = Asm()
            STATES[state](a)
        elif label:
            a = Asm().call("_root", "gotoAndStop", label)
        capture = drive(movie, a, hide_text, table=used)
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=STAGE_DIR) as tmp:  # a lowercase path: the patched fetch lowercases
        t = Path(tmp) / "interface"
        stage(roots, t)
        name = src.name.lower()
        if (t / name).is_symlink():
            (t / name).unlink()
        (t / name).write_bytes(movie.to_bytes())
        if (lib := font_library(fontlib)) is not None:
            (t / "gfxfontlib.swf").write_bytes(lib)
        cmd = [str(EXPORTER), str(t / name), str(Path(tmp) / "shot.png"), "--silent", "--frames", "1",
               "--skipframes", str(capture + 8), "--width", str(width), "--height", str(height)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=t)
        pngs = [p for p in [Path(tmp) / "shot.png"] if p.is_file()]
        if os.environ.get("FLASH_STILL_DEBUG"):
            print("\n".join(x for x in r.stderr.splitlines() if not x.startswith("fetch:")), file=sys.stderr)
        if capture != frame and "argonia: captured" not in r.stderr:
            raise RuntimeError(f"the capture frame never ran (the movie stopped the root timeline?): {r.stderr[-800:]}")
        if r.returncode or not pngs:
            raise RuntimeError(f"ruffle-exporter failed ({r.returncode}): {r.stderr[-2000:]}")
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pngs[-1], out)
    return r.stderr


# --- the text measure -----------------------------------------------------------------------------------------

def _lum(rgb: np.ndarray) -> float:
    c = rgb / 255.0
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])


def contrast(a: np.ndarray, b: np.ndarray) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return round((la + 0.05) / (lb + 0.05), 2)


def _components(mask: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Bounding boxes (x0, y0, x1, y1) of the text items: the mask on a 4 px grid, joined across word gaps."""
    h, w = mask.shape
    g = mask[: h // 4 * 4, : w // 4 * 4].reshape(h // 4, 4, w // 4, 4).any(axis=(1, 3))
    grown = g.copy()
    for dx in range(1, 6):  # letters and words of one item sit within ~20 px
        grown[:, dx:] |= g[:, :-dx]
        grown[:, :-dx] |= g[:, dx:]
    seen = np.zeros_like(grown)
    boxes = []
    for y0, x0 in zip(*np.nonzero(grown)):
        if seen[y0, x0]:
            continue
        stack, ys, xs = [(y0, x0)], [], []
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop()
            ys.append(y)
            xs.append(x)
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < grown.shape[0] and 0 <= nx < grown.shape[1] and grown[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        boxes.append((min(xs) * 4, min(ys) * 4, max(xs) * 4 + 4, max(ys) * 4 + 4))
    return sorted(boxes, key=lambda b: (b[1], b[0]))


def measure(full: Path, bare: Path) -> list[dict]:
    """Each text item: its box, ink colour (the masked pixels farthest from the background), the background colour
    behind it and the WCAG contrast ratio between them."""
    a = np.asarray(Image.open(full).convert("RGB"), dtype=np.int32)
    b = np.asarray(Image.open(bare).convert("RGB"), dtype=np.int32)
    mask = np.abs(a - b).sum(axis=2) > 9  # low: near-black text on a dark ground is what we hunt
    items = []
    for x0, y0, x1, y1 in _components(mask):
        m = mask[y0:y1, x0:x1]
        if m.sum() < 12:
            continue
        bg = np.median(b[y0:y1, x0:x1].reshape(-1, 3), axis=0)
        px = a[y0:y1, x0:x1][m]
        far = np.abs(px - bg).sum(axis=1)
        ink = np.median(px[far >= np.percentile(far, 75)], axis=0)
        items.append({"box": [int(x0), int(y0), int(x1), int(y1)], "ink": "#%02x%02x%02x" % tuple(int(v) for v in ink),
                      "background": "#%02x%02x%02x" % tuple(int(v) for v in bg), "contrast": contrast(ink, bg)})
    return items


def still_with_measure(src: Path, out: Path, state: str, **kw) -> dict:
    render(src, out, state=state, **kw)
    bare = out.with_name(out.stem + ".notext.png")
    render(src, bare, state=state, hide_text=True, **kw)
    items = measure(out, bare)
    report = {"swf": str(src), "state": state, "png": str(out), "items": items,
              "min_contrast": min((i["contrast"] for i in items), default=None)}
    out.with_suffix(".json").write_text(json.dumps(report, indent=1))
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("swf", type=Path)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--state", choices=sorted(STATES))
    g.add_argument("--frame", type=int)
    g.add_argument("--label")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--fontlib", type=Path, help="fonts_pelagiad.swf (default: the stack's argonia-theme overlay)")
    ap.add_argument("--measure", action="store_true", help="also the text mask: ink, background, contrast (json)")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    kw = dict(width=a.width, height=a.height, fontlib=a.fontlib)
    if a.measure and a.state:
        r = still_with_measure(a.swf, a.out, a.state, **kw)
        for i in r["items"]:
            print(f"{i['box']} ink {i['ink']} on {i['background']} contrast {i['contrast']}")
        print(f"min contrast {r['min_contrast']}")
    else:
        render(a.swf, a.out, state=a.state, frame=a.frame, label=a.label, **kw)
    print(a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
