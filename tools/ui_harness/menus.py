"""The menu loop (owner play test 3, finding 6): every menu driven by a scripted pad at the four viewports.

    python -m tools.ui_harness menus [--only VIEW ...] [--no-stills]   -> out/ui/menus/report.json + stills
    python -m tools.ui_harness menus --flash [--theme <overlay>]       -> out/ui/flash/report.json + stills

--flash: every retinted Flash screen with a driven state (tools.ui_theme.flash_still.STATES) drawn from the themed
overlay by Ruffle, an L3 still and its text measure each; a text item under FLASH_MIN_CONTRAST fails. Run it on the
overlay the next deploy carries, before the deploy.

The pad is the in-game one: PrismaUI's `gamepadbuttondown` on window.prismaUi.controls (nav.ts), stood up before the
view loads, so the presses run the same code path as in game. Per menu and viewport:
- the script: each press in turn, the focused control recorded after it, a still at the opening and after the script;
- the graph: from every focusable control, each d-pad direction pressed, where focus lands recorded; the controls
  reached from the opening focus counted against all focusable ones.
A press fails when it is dead (focus stays put though a control lies that way) or jumps a column (an up/down that
lands on a control beside its column while one lay in it). Fails are the loop's verdict; a reader judges the stills.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from tools.ui_harness.build import ROOT, VIEWS, build
from tools.ui_harness.harness import VIEWPORTS, Harness, fixtures

OUT = ROOT / "out" / "ui" / "menus"
BUTTON = {"a": 0, "b": 1, "x": 2, "lb": 4, "rb": 5, "lt": 6, "rt": 7, "up": 12, "down": 13, "left": 14, "right": 15}

# (view, the fixture state it opens on, the pad script, whether the d-pad only moves focus there: the graph runs then).
# The chart's d-pad pans the map, so only its script runs. SENT: the intent types a menu's script must send (the pad's
# X drops the focused stack; B closes).
SENT = {"inventory": ["inventory.drop"], "system": [], "magic": []}
MENUS: tuple[tuple[str, str, list[str], bool], ...] = (
    ("inventory", "full", ["down", "down", "down", "right", "left", "rb", "down", "lb", "up", "x"], True),
    ("charsheet", "main", ["down", "down", "right", "left", "rb", "down", "rb", "down", "lb"], True),
    ("magic", "kit", ["down", "down", "down", "right", "left", "up", "rb", "lb"], True),
    ("system", "main", ["down", "down", "down", "up", "up", "up"], True),
    ("journal", "current", ["down", "down", "rb", "lb", "right", "left"], True),
    ("chart", "claywater", ["up", "right", "rt", "lt"], False),
    ("dialogue", "answer", ["down", "down", "down", "right", "left", "up"], True),
)

INIT = "window.prismaUi = { controls: new EventTarget() };"

# In the page: the focused control as {key, x0, x1, y0, y1}, and the pad press itself.
LIB = r"""
window.__pad = (i) => window.prismaUi.controls.dispatchEvent(
  new CustomEvent("gamepadbuttondown", { detail: { w3cButtonIndex: i } }));
window.__focusables = () => [...document.querySelectorAll("button:not([disabled]),[data-nav]")].filter((el) => {
  const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
  return r.width > 0 && r.height > 0 && cs.visibility !== "hidden" && cs.display !== "none";
});
window.__ahead = (dx, dy) => {
  const a = document.activeElement; if (!a || a === document.body) return 0;
  const b = a.getBoundingClientRect(), cx = (b.left + b.right) / 2, cy = (b.top + b.bottom) / 2;
  return window.__focusables().filter((o) => o !== a).filter((o) => { const r = o.getBoundingClientRect();
    return ((r.left + r.right) / 2 - cx) * dx + ((r.top + r.bottom) / 2 - cy) * dy > 1; }).length;
};
window.__desc = (el) => {
  if (!el || el === document.body) return null;
  const r = el.getBoundingClientRect();
  const key = el.dataset.key || ((el.className || el.tagName) + ":" + (el.textContent || "").trim().slice(0, 24));
  return { key, x0: r.left, x1: r.right, y0: r.top, y1: r.bottom };
};
"""

# The lowest contrast of any shown text over its ground (WCAG 2 ratio): each translucent ground composited over the
# next one up, the page's bottom taken as play at its darkest (black); the text's own alpha and opacity applied.
CONTRAST = r"""
() => {
  const rgba = (c) => { const m = c.match(/[\d.]+/g).map(Number); return [m[0], m[1], m[2], m.length > 3 ? m[3] : 1]; };
  const over = (top, bot) => [0, 1, 2].map((i) => top[i] * top[3] + bot[i] * (1 - top[3])).concat([1]);
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  const ground = (el) => { const chain = []; for (let e = el; e; e = e.parentElement) chain.push(rgba(getComputedStyle(e).backgroundColor));
    return chain.reverse().reduce((g, c) => c[3] > 0 ? over(c, g) : g, [0, 0, 0, 1]); };
  let worst = { ratio: 99, text: "" };
  const w = document.createTreeWalker(document.getElementById("view"), NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    if (!n.textContent.trim()) continue;
    const el = n.parentElement, r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    let op = 1; for (let e = el; e; e = e.parentElement) op *= +getComputedStyle(e).opacity;
    const g = ground(el), c = rgba(getComputedStyle(el).color); c[3] *= op;
    const t = over(c, g), a = lum(t), b = lum(g), ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    if (ratio < worst.ratio) worst = { ratio: Math.round(ratio * 100) / 100, text: n.textContent.trim().slice(0, 30) };
  }
  return worst;
}
"""
MIN_CONTRAST = 4.5
CONTRAST_CHECKED = {"system", "inventory", "charsheet", "magic", "journal"}

GRAPH = r"""
(B) => {
  const els = window.__focusables();
  const keyOf = (el) => window.__desc(el).key;
  const start = document.activeElement && els.includes(document.activeElement) ? keyOf(document.activeElement) : null;
  const edges = {}, fails = [];
  const dirs = { up: [0, -1, B.up], down: [0, 1, B.down], left: [-1, 0, B.left], right: [1, 0, B.right] };
  for (const el of els) {
    const k = keyOf(el); edges[k] = {};
    for (const [name, [dx, dy, b]] of Object.entries(dirs)) {
      el.focus({ preventScroll: true });
      const before = window.__desc(el);
      window.__pad(b);
      const now = document.activeElement, after = window.__desc(now);
      edges[k][name] = after ? after.key : null;
      const cx = (before.x0 + before.x1) / 2, cy = (before.y0 + before.y1) / 2;
      const ahead = els.filter((o) => o !== el).map((o) => window.__desc(o)).filter((o) =>
        (((o.x0 + o.x1) / 2 - cx) * dx + ((o.y0 + o.y1) / 2 - cy) * dy) > 1);
      if (!after || after.key === k) { if (ahead.length) fails.push(`dead ${name} on ${k}`); continue; }
      if (dy !== 0) {
        const over = (o) => Math.min(o.x1, before.x1) - Math.max(o.x0, before.x0) > 0;
        if (!over(after) && ahead.some(over)) fails.push(`${name} on ${k} jumps a column to ${after.key}`);
      }
    }
  }
  return { start, count: els.length, edges, fails };
}
"""


def reach(start: str | None, edges: dict) -> set[str]:
    seen, todo = set(), [start] if start else []
    while todo:
        k = todo.pop()
        if k in seen or k not in edges:
            continue
        seen.add(k)
        todo += [t for t in edges[k].values() if t]
    return seen


class Menus(Harness):
    def page(self, vp):
        fresh = vp.name not in self.pages
        p = super().page(vp)
        if fresh:
            p.add_init_script(INIT)
            p.add_init_script(LIB)
        return p


def drive(h: Menus, vp, view: str, state: str, script: list[str], graph: bool, shoot: bool) -> dict:
    t0 = time.monotonic()
    p = h.open(vp, view, fresh=True)
    h.loaded = None
    p.evaluate("(m) => window.argonia.push(m)", json.dumps(fixtures(view)["states"][state]))
    p.evaluate("() => document.fonts.ready.then(() => true)")
    if view == "chart":
        p.wait_for_function("() => document.body.dataset.ready === '1' || window.argonia.errors.length", timeout=20000)
    p.evaluate("() => window.argonia.device('gamepad')")
    r: dict = {"fails": [], "presses": [], "stills": []}
    d = OUT / "stills" / view

    def still(tag: str) -> None:
        if shoot:
            d.mkdir(parents=True, exist_ok=True)
            path = d / f"{state}+{tag}@{vp.name}.png"
            p.screenshot(path=str(path))
            r["stills"].append(str(path.relative_to(ROOT)))

    opening = p.evaluate("() => window.__desc(document.activeElement)")
    r["opening"] = opening and opening["key"]
    still("open")
    r["contrast"] = p.evaluate(CONTRAST)
    if view in CONTRAST_CHECKED and r["contrast"]["ratio"] < MIN_CONTRAST:
        r["fails"].append(f"contrast {r['contrast']['ratio']}:1 under {MIN_CONTRAST} on '{r['contrast']['text']}'")
    if graph:
        g = p.evaluate(GRAPH, BUTTON)
        got = reach(g["start"] or (opening and opening["key"]), g["edges"])
        r["graph"] = {"focusable": g["count"], "reached": len(got),
                      "unreached": sorted(set(g["edges"]) - got)[:12], "dead": g["fails"]}
        r["fails"] += g["fails"]
        if g["count"] and len(got) < g["count"]:
            r["fails"].append(f"{g['count'] - len(got)} of {g['count']} controls unreached by the d-pad from the opening")
        # the graph left focus anywhere: reopen for the script
        p = h.open(vp, view, fresh=True)
        h.loaded = None
        p.evaluate("(m) => window.argonia.push(m)", json.dumps(fixtures(view)["states"][state]))
        p.evaluate("() => window.argonia.device('gamepad')")
    if r["opening"] is None and view != "chart":
        r["fails"].append("opens with no control focused: the pad's first press is spent finding one")
    for b in script:
        before = p.evaluate("() => window.__desc(document.activeElement)")
        v = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}.get(b)
        ahead = v and p.evaluate("([x, y]) => window.__ahead(x, y)", list(v))
        p.evaluate("(i) => window.__pad(i)", BUTTON[b])
        after = p.evaluate("() => window.__desc(document.activeElement)")
        r["presses"].append([b, after and after["key"]])
        if b in ("up", "down", "left", "right") and graph and ahead and before and after and before["key"] == after["key"]:
            r["fails"].append(f"script: {b} left focus on {after['key']}")
    still("script")
    sent = [json.loads(x)["type"] for x in p.evaluate("() => window.argoniaSent")]
    r["sent"] = sent
    for want in SENT.get(view, []):
        if want not in sent:
            r["fails"].append(f"script sent no {want} (sent {sent})")
    p.evaluate("(i) => window.__pad(i)", BUTTON["b"])
    closed = [json.loads(x) for x in p.evaluate("() => window.argoniaSent")][len(sent):]
    if view != "dialogue" and not any(c["type"] == "view.close" for c in closed):
        r["fails"].append(f"B sent no view.close (sent {[c['type'] for c in closed]})")
    errs = p.evaluate("() => window.argonia.errors")
    r["fails"] += [f"error: {e}" for e in errs]
    r["seconds"] = round(time.monotonic() - t0, 2)
    return r


def run(only: list[str] | None, shoot: bool) -> dict:
    from playwright.sync_api import sync_playwright

    t0 = time.monotonic()
    info = build(ROOT / "out" / "ui" / "views")
    menus = [m for m in MENUS if m[0] in VIEWS and (not only or m[0] in only)
             and (m[0] != "chart" or info["chart"])]
    report: dict = {"menus": {}, "skipped": sorted({m[0] for m in MENUS} - {m[0] for m in menus})}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--disable-gpu", "--force-color-profile=srgb", "--font-render-hinting=none"])
        h = Menus(browser, ROOT / "out" / "ui")
        try:
            for vp in VIEWPORTS:
                for view, state, script, graph in menus:
                    report["menus"][f"{view}@{vp.name}"] = drive(h, vp, view, state, script, graph, shoot)
                h.close(vp)
        finally:
            browser.close()
        report["console"] = h.console
    report["seconds"] = round(time.monotonic() - t0, 1)
    report["fails"] = [f"{k}: {f}" for k, m in report["menus"].items() for f in m["fails"]] + \
        [f"console: {c}" for c in report["console"]]
    return report


FLASH_OUT = ROOT / "out" / "ui" / "flash"
FLASH_MIN_CONTRAST = 2.0  # WCAG's floor for large text is 3.0; Dear Diary's unselected rows are dimmed by design
# (the movie under the overlay's interface/, its driven states)
FLASH = (("quest_journal.swf", ("system-main", "system-settings", "system-load")),)


def run_flash(theme) -> dict:
    from tools.ui_theme import flash_still

    t0 = time.monotonic()
    report: dict = {"theme": str(theme), "screens": {}, "fails": []}
    for movie, states in FLASH:
        src = theme / "interface" / movie
        if not src.is_file():
            report["fails"].append(f"{movie}: not in {theme}/interface")
            continue
        for state in states:
            r = flash_still.still_with_measure(src, FLASH_OUT / f"{src.stem}-{state}.png", state)
            report["screens"][f"{movie}@{state}"] = r
            for i in r["items"]:
                if i["contrast"] < FLASH_MIN_CONTRAST:
                    report["fails"].append(f"{movie}@{state}: text at {i['box']} ink {i['ink']} on {i['background']} "
                                           f"contrast {i['contrast']} < {FLASH_MIN_CONTRAST}")
    report["seconds"] = round(time.monotonic() - t0, 1)
    return report


def default_theme():
    from tools.ui_theme.flash_still import STACK
    built = ROOT / "out" / "ui_theme" / "argonia-theme"
    return built if (built / "interface").is_dir() else STACK / "argonia-theme"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.ui_harness menus")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--no-stills", action="store_true")
    ap.add_argument("--flash", action="store_true", help="the Flash screens' L3 stills and text contrast (Ruffle)")
    ap.add_argument("--theme", type=Path, help="the themed overlay (default out/ui_theme/argonia-theme, else the stack's)")
    a = ap.parse_args(argv)
    if a.flash:
        r = run_flash(a.theme or default_theme())
        FLASH_OUT.mkdir(parents=True, exist_ok=True)
        (FLASH_OUT / "report.json").write_text(json.dumps(r, indent=1) + "\n")
        print(f"{len(r['screens'])} flash stills in {r['seconds']} s; {len(r['fails'])} fails -> {FLASH_OUT}")
        for f in r["fails"][:60]:
            print("  " + f)
        return 1 if r["fails"] else 0
    r = run(a.only, not a.no_stills)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(json.dumps(r, indent=1) + "\n")
    print(f"{len(r['menus'])} menu runs in {r['seconds']} s; {len(r['fails'])} fails; skipped {r['skipped']}")
    for f in r["fails"][:60]:
        print("  " + f)
    return 1 if r["fails"] else 0


if __name__ == "__main__":
    sys.exit(main())
