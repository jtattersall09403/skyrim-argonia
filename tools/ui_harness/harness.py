"""The L3 harness for 1.2's views: headless Chromium renders each view from each fixture at each viewport as a still.

    python -m tools.ui_harness            every view x fixture x viewport (+ variants) -> out/ui/stills/, report.json
    python -m tools.ui_harness --smoke    the gate's subset: 300 topics, the wiring, one still per view, folded

One browser, one page per viewport, reused across views and states (the build VM's memory guidance). Each still is
measured in the page: the smallest text (px, and mm on the Magic V5 at its ppi), Pelagiad loaded, nothing off the
viewport, no clipped button text, no page scroll, no refused push or script error. The dialogue window with 300
topics is checked for a layout break. The wiring check clicks and keys each control and reads what was sent.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from tools.ui_harness.build import ROOT, VIEWS, build

OUT = ROOT / "out" / "ui"


@dataclass(frozen=True)
class Viewport:
    name: str
    w: int
    h: int
    ppi: float | None   # set for the phone, where the physical text height is the readability bar


# 1.2 §b: 1920x1080, 1280x720, the Magic V5 folded (cover 6.43", 2376x1060, 404 ppi) and unfolded (inner 7.95",
# 2352x2172, 403 ppi), at 1:1 since 0.2 §d records no stream scale (infra/README.md).
VIEWPORTS = (
    Viewport("1080p", 1920, 1080, None),
    Viewport("720p", 1280, 720, None),
    Viewport("v5-folded", 2376, 1060, 404.0),
    Viewport("v5-unfolded", 2352, 2172, 403.0),
)
MIN_MM = 2.5      # the smallest text's em height on the phone (DESIGN.md; the reader's round 1 failed 1.96)
MIN_PX_DESK = 20  # and on a desktop window, at 720p

# Measured in the page after each push.
MEASURE = r"""
() => {
  const W = innerWidth, H = innerHeight;
  const out = { minFont: 1e9, minFontAt: "", offscreen: [], clipped: [], scroll: false, errors: [...window.argonia.errors],
    pelagiad: document.fonts.check("16px Pelagiad"), texts: 0 };
  const walker = document.createTreeWalker(document.getElementById("view"), NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    if (!n.textContent.trim()) continue;
    const el = n.parentElement, cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0 || cs.visibility === "hidden" || cs.display === "none") continue;
    // A row scrolled out of its list is not on screen; only what a scroller shows counts.
    let hidden = false;
    for (let p = el.parentElement; p && p.id !== "view"; p = p.parentElement) {
      const ps = getComputedStyle(p);
      if (/(auto|scroll|hidden)/.test(ps.overflowY + ps.overflowX)) {
        const pr = p.getBoundingClientRect();
        if (r.bottom <= pr.top || r.top >= pr.bottom || r.right <= pr.left || r.left >= pr.right) { hidden = true; break; }
      }
    }
    if (hidden) continue;
    out.texts++;
    const f = parseFloat(cs.fontSize);
    if (f < out.minFont) { out.minFont = f; out.minFontAt = (el.className || el.tagName) + ": " + n.textContent.trim().slice(0, 30); }
    if (r.left < -1 || r.top < -1 || r.right > W + 1 || r.bottom > H + 1) out.offscreen.push(n.textContent.trim().slice(0, 40));
  }
  for (const b of document.querySelectorAll("#view button")) {
    const r = b.getBoundingClientRect();
    if (r.width && b.scrollWidth > b.clientWidth + 1 && !b.classList.contains("kw")) out.clipped.push(b.textContent.trim().slice(0, 40));
  }
  // The chart's labels: no two shown labels' boxes overlap (the view's collision pass; 1 px of slack).
  const lab = [...document.querySelectorAll(".label:not([hidden])")].map((e) => [e.textContent.trim(), e.getBoundingClientRect()]);
  out.labelOverlaps = [];
  for (let i = 0; i < lab.length; i++) for (let j = i + 1; j < lab.length; j++) {
    const a = lab[i][1], b = lab[j][1];
    if (a.left < b.right - 1 && b.left < a.right - 1 && a.top < b.bottom - 1 && b.top < a.bottom - 1) out.labelOverlaps.push(lab[i][0] + " / " + lab[j][0]);
  }
  out.labels = lab.length;
  out.scroll = document.documentElement.scrollWidth > W + 1 || document.documentElement.scrollHeight > H + 1;
  return out;
}
"""

# The 300-topic window: the list scrolls inside its column, rows are in order and a line tall, the conversation keeps
# its room, and Goodbye and the window stay on screen.
TOPICS = r"""
() => {
  const W = innerWidth, H = innerHeight, rem = parseFloat(getComputedStyle(document.documentElement).fontSize);
  const list = document.querySelector("[data-list=topics]"), win = document.querySelector(".dialogue");
  const talk = document.querySelector(".talk"), bye = document.querySelector(".goodbye");
  const rows = [...list.querySelectorAll(".topic")];
  const tops = rows.map((b) => b.offsetTop);
  const wr = win.getBoundingClientRect(), tr = talk.getBoundingClientRect(), br = bye.getBoundingClientRect();
  const fails = [];
  if (rows.length !== 300) fails.push(`rows ${rows.length}`);
  if (!(list.scrollHeight > list.clientHeight)) fails.push("the list does not scroll");
  if (!tops.every((t, i) => i === 0 || t > tops[i - 1])) fails.push("rows out of order or overlapping");
  if (rows.some((b) => b.offsetHeight < rem)) fails.push("a row under a line tall");
  if (wr.left < 0 || wr.top < 0 || wr.right > W || wr.bottom > H) fails.push("window off screen");
  if (br.bottom > wr.bottom || br.top < wr.top) fails.push("Goodbye outside the window");
  if (tr.width < 0.45 * wr.width) fails.push(`talk squeezed to ${Math.round(100 * tr.width / wr.width)}%`);
  list.scrollTop = list.scrollHeight;
  const last = rows[299].getBoundingClientRect(), lr = list.getBoundingClientRect();
  if (last.bottom > lr.bottom + 1 || last.top < lr.top - 1) fails.push("the last topic cannot be scrolled to");
  list.scrollTop = 0;
  return { fails, visibleRows: Math.round(list.clientHeight / (rows[0].offsetHeight || 1)), listPx: list.clientHeight };
}
"""


def fixtures(view: str) -> dict:
    return json.loads((ROOT / "ui" / "fixtures" / f"{view}.json").read_text())


def stills_for(view: str) -> list[tuple[str, list[str], dict]]:
    """(still name, the pushes in order, options): each fixture state, plus the variants a state alone cannot show."""
    st = fixtures(view)["states"]
    out = []
    for name, m in st.items():
        if view == "hud" and m["type"] == "hud.bars":
            out.append((name, [json.dumps(st["play"]), json.dumps(m)], {}))   # bars update a shown HUD
            continue
        out.append((name, [json.dumps(m)], {}))
    if view == "dialogue":
        out.append(("answer+persuasion", [json.dumps(st["answer"])], {"click": ".special"}))
        out.append(("answer+focus", [json.dumps(st["answer"])], {"keys": ["ArrowDown", "ArrowDown"], "first": ".topic"}))
    if view == "hud":
        out.append(("prompt@gamepad", [json.dumps(st["prompt"])], {"device": "gamepad"}))
        out.append(("prompt@touch", [json.dumps(st["prompt"])], {"device": "touch"}))
        out.append(("effects@bright", [json.dumps(st["effects"])], {"bright": True}))
    if view == "journal":
        out.append(("questIndex+focus", [json.dumps(st["questIndex"])], {"first": ".qlink"}))
    return out


class Harness:
    def __init__(self, browser, out: Path):
        self.browser, self.out = browser, out
        self.pages: dict[str, object] = {}
        self.console: list[str] = []
        self.loaded: tuple[str, str, bool] | None = None   # (viewport, view, bright) of the clean page now open

    def page(self, vp: Viewport):
        if vp.name not in self.pages:
            p = self.browser.new_page(viewport={"width": vp.w, "height": vp.h}, device_scale_factor=1)
            p.on("console", lambda m: m.type == "error" and self.console.append(f"{vp.name}: {m.text}"))
            p.on("pageerror", lambda e: self.console.append(f"{vp.name}: {e}"))
            self.pages[vp.name] = p
        return self.pages[vp.name]

    def close(self, vp: Viewport) -> None:
        """Done with a viewport: its page goes, so one renderer is alive at a time."""
        p = self.pages.pop(vp.name, None)
        if p is not None:
            p.close()
        self.loaded = None

    def open(self, vp: Viewport, view: str, bright: bool = False, fresh: bool = True):
        p = self.page(vp)
        if not fresh and self.loaded == (vp.name, view, bright):
            return p          # the views are push-driven: a plain push needs no reload
        self.loaded = None
        p.goto((self.out / "views" / view / "index.html").as_uri())
        p.wait_for_function("() => window.argonia && document.fonts.status === 'loaded'")
        if view == "hud":
            p.evaluate(f"() => document.body.className = 'backdrop{' bright' if bright else ''}'")
        self.loaded = (vp.name, view, bright)
        return p

    def still(self, vp: Viewport, view: str, name: str, pushes: list[str], opt: dict, shoot: bool = True) -> dict:
        plain = not (opt.keys() - {"bright"})
        p = self.open(vp, view, bool(opt.get("bright")), fresh=not plain)
        if not plain:
            self.loaded = None    # clicks, keys or a device leave state behind: the next still reloads
        if opt.get("device"):
            p.evaluate(f"() => window.argonia.device('{opt['device']}')")
        p.evaluate("() => { window.argonia.errors.length = 0; }")
        for m in pushes:
            assert p.evaluate("(m) => window.argonia.push(m)", m), f"{view}.{name}: push refused"
        if view == "chart":
            p.wait_for_function("() => document.body.dataset.ready === '1' || window.argonia.errors.length", timeout=20000)
        if opt.get("click"):
            p.click(opt["click"])
        p.evaluate("() => document.fonts.ready.then(() => true)")
        if opt.get("first"):
            p.focus(opt["first"])
            p.evaluate("() => window.argonia.device('keyboard')")
        for k in opt.get("keys", []):
            p.keyboard.press(k)
        m = p.evaluate(MEASURE)
        if view == "dialogue" and name == "threeHundredTopics":
            m["topics"] = p.evaluate(TOPICS)
        path = self.out / "stills" / view / f"{name}@{vp.name}.png"
        if shoot:
            path.parent.mkdir(parents=True, exist_ok=True)
            p.screenshot(path=str(path))
        m["still"] = str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
        m["fails"] = judge(m, vp, view == "hud" and not json.loads(pushes[0])["body"].get("visible", True))
        return m

    def wiring(self, vp: Viewport) -> list[str]:
        """Each control sends its intent: read back from window.argoniaSent and checked against the fixtures."""
        fails: list[str] = []
        d = fixtures("dialogue")
        p = self.open(vp, "dialogue")
        p.evaluate("(m) => window.argonia.push(m)", json.dumps(d["states"]["answer"]))
        p.click(".topic >> nth=1")
        p.click(".kw")
        p.click(".special")
        p.click(".opt >> nth=0")
        p.keyboard.press("Escape")     # closes the persuasion panel
        p.click(".goodbye")
        p.keyboard.press("Escape")     # closes the window
        p.evaluate("(m) => window.argonia.push(m)", json.dumps(d["states"]["forced"]))
        p.keyboard.press("Escape")     # a forced conversation cannot be left
        sent = [json.loads(s) for s in p.evaluate("() => window.argoniaSent")]
        want = [d["intents"]["topic"], d["intents"]["keyword"], d["intents"]["persuade"], d["intents"]["goodbye"],
                d["intents"]["close"]]
        if sent != want:
            fails.append(f"dialogue sent {sent}, want {want}")
        # The pad: focus walks the list with the d-pad's actions, A presses.
        p.evaluate("(m) => window.argonia.push(m)", json.dumps(d["states"]["answer"]))
        p.evaluate("() => { window.argoniaSent.length = 0; document.querySelector('.topic').focus(); }")
        for a in ("down", "down", "accept"):
            p.evaluate(f"() => window.argonia.input('{a}')")
        sent = [json.loads(s) for s in p.evaluate("() => window.argoniaSent")]
        third = d["states"]["answer"]["body"]["topics"][2]["id"]
        if sent != [{"type": "dialogue.topic", "v": 1, "body": {"topic": third}}]:
            fails.append(f"pad walk sent {sent}, want the third topic")

        j = fixtures("journal")
        p = self.open(vp, "journal")
        p.evaluate("(m) => window.argonia.push(m)", json.dumps(j["states"]["entries"]))
        p.click(".turn.next")
        p.keyboard.press("PageDown")
        p.keyboard.press("Escape")
        p.evaluate("(m) => window.argonia.push(m)", json.dumps(j["states"]["questIndex"]))
        p.click(".qlink >> nth=0")
        sent = [json.loads(s) for s in p.evaluate("() => window.argoniaSent")]
        want = [j["intents"]["nextPage"], j["intents"]["nextPage"], j["intents"]["close"], j["intents"]["pickQuest"]]
        if sent != want:
            fails.append(f"journal sent {sent}, want {want}")

        if (self.out / "views" / "chart" / "assets" / "index.js").exists():
            c = fixtures("chart")
            p = self.open(vp, "chart")
            p.evaluate("(m) => window.argonia.push(m)", json.dumps(c["states"]["claywater"]))
            p.wait_for_function("() => document.body.dataset.ready === '1'", timeout=20000)
            p.keyboard.press("+")
            p.wait_for_function("() => window.argoniaSent.length > 0", timeout=5000)
            p.keyboard.press("Escape")
            sent = [json.loads(s) for s in p.evaluate("() => window.argoniaSent")]
            z = c["states"]["claywater"]["body"]["view"]["zoom"]
            if not (len(sent) == 2 and sent[0]["type"] == "chart.pan" and abs(sent[0]["body"]["view"]["zoom"] - z * 1.5) < 1e-6
                    and sent[1] == c["intents"]["close"]):
                fails.append(f"chart sent {sent}")
        return fails


def judge(m: dict, vp: Viewport, empty_ok: bool) -> list[str]:
    f = []
    if m["texts"] == 0 and not empty_ok:
        f.append("no text drawn")
    if m["texts"]:
        if vp.ppi is not None:
            mm = m["minFont"] / vp.ppi * 25.4
            m["minMm"] = round(mm, 2)
            if mm < MIN_MM:
                f.append(f"smallest text {mm:.2f} mm < {MIN_MM} ({m['minFontAt']})")
        elif m["minFont"] < MIN_PX_DESK * vp.h / 720:
            f.append(f"smallest text {m['minFont']} px ({m['minFontAt']})")
    if m["texts"] and not m["pelagiad"]:
        f.append("Pelagiad not loaded")
    if m["offscreen"]:
        f.append(f"text off screen: {m['offscreen'][:3]}")
    if m["clipped"]:
        f.append(f"button text clipped: {m['clipped'][:3]}")
    if m.get("labelOverlaps"):
        f.append(f"chart labels overlap: {m['labelOverlaps'][:3]}")
    if m["scroll"]:
        f.append("the page scrolls")
    if m["errors"]:
        f.append(f"errors: {m['errors'][:3]}")
    if m.get("topics", {}).get("fails"):
        f.append(f"300 topics: {m['topics']['fails']}")
    return f


def run(smoke: bool, out: Path = OUT, shoot: bool = True) -> dict:
    from playwright.sync_api import sync_playwright

    t0 = time.monotonic()
    info = build(out / "views")
    report: dict = {"build": info, "stills": {}, "wiring": [], "console": []}
    plan = []
    if smoke:
        st = {v: fixtures(v)["states"] for v in VIEWS}
        folded, desk = VIEWPORTS[2], VIEWPORTS[0]
        for vp in (folded, desk):
            plan.append((vp, "dialogue", "threeHundredTopics", [json.dumps(st["dialogue"]["threeHundredTopics"])], {}))
        plan += [(folded, "hud", "play", [json.dumps(st["hud"]["play"])], {}),
                 (folded, "journal", "entries", [json.dumps(st["journal"]["entries"])], {})]
        if info["chart"]:
            plan.append((folded, "chart", "claywater", [json.dumps(st["chart"]["claywater"])], {}))
    else:
        for vp in VIEWPORTS:
            for v in VIEWS:
                if v == "chart" and not info["chart"]:
                    report["console"].append("chart skipped: out/chart has no layers (make chart)")
                    continue
                plan += [(vp, v, n, pushes, o) for n, pushes, o in stills_for(v)]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--disable-gpu", "--force-color-profile=srgb", "--font-render-hinting=none"])
        h = Harness(browser, out)
        try:
            for i, (vp, v, n, pushes, o) in enumerate(plan):
                report["stills"][f"{v}/{n}@{vp.name}"] = h.still(vp, v, n, pushes, o, shoot)
                if i + 1 < len(plan) and plan[i + 1][0] != vp:
                    h.close(vp)
            h.loaded = None
            report["wiring"] = h.wiring(VIEWPORTS[2])
        finally:
            browser.close()
        report["console"] += h.console
    report["seconds"] = round(time.monotonic() - t0, 1)
    report["fails"] = [f"{k}: {x}" for k, m in report["stills"].items() for x in m["fails"]] + report["wiring"] + \
        [f"console: {c}" for c in report["console"] if not c.startswith("chart skipped")]
    if not info["font"]:
        report["fails"].append("Pelagiad missing: python -m tools.chart fetch-font")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args(argv)
    r = run(a.smoke)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ("smoke.json" if a.smoke else "report.json")).write_text(json.dumps(r, indent=1) + "\n")
    print(f"{len(r['stills'])} stills in {r['seconds']} s; {len(r['fails'])} fails")
    for f in r["fails"]:
        print("  " + f)
    return 1 if r["fails"] else 0


if __name__ == "__main__":
    sys.exit(main())
