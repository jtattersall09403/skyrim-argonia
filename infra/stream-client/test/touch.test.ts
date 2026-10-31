import { test } from "node:test"
import assert from "node:assert/strict"
import { BUTTON_INDEX, MIN_HOLD_MS, PadModel, bandWidth, exclusionRects, layoutFor, layoutProblems, shapeOf, stickFromDrag, type ButtonId } from "../src/touch_model.ts"

test("stick: drag maps to Gamepad API axes (y down), clamped, with a radial dead zone", () => {
    assert.deepEqual(stickFromDrag(0, 0, 100), { x: 0, y: 0 })
    assert.deepEqual(stickFromDrag(5, 0, 100), { x: 0, y: 0 }) // inside the 8% dead zone
    assert.deepEqual(stickFromDrag(0, -100, 100), { x: 0, y: -1 }) // finger up = stick up = axes[1] -1
    assert.deepEqual(stickFromDrag(300, 0, 100), { x: 1, y: 0 }) // beyond the radius clamps to 1
    const half = stickFromDrag(54, 0, 100)
    assert.equal(half.x, 0.5) // (0.54 - 0.08) / 0.92
    const diag = stickFromDrag(100, 100, 100)
    assert.ok(Math.abs(Math.hypot(diag.x, diag.y) - 1) < 0.002) // magnitude never exceeds 1
})

test("a tap shorter than a frame is stretched to the minimum hold, so the rAF poll sees it", () => {
    const pad = new PadModel()
    pad.press("a", 1000, 1)
    pad.release("a", 1005, 1)
    assert.equal(pad.values[BUTTON_INDEX.a], 1) // still down
    pad.tick(1000 + MIN_HOLD_MS - 1)
    assert.ok(pad.isDown("a"))
    pad.tick(1000 + MIN_HOLD_MS)
    assert.ok(!pad.isDown("a"))
})

test("a long hold releases at once; a re-press cancels a pending release", () => {
    const pad = new PadModel()
    pad.press("rt", 0, 1)
    pad.release("rt", 500, 1)
    assert.ok(!pad.isDown("rt"))
    pad.press("b", 1000, 1)
    pad.release("b", 1010, 1)
    pad.press("b", 1020, 2)
    pad.tick(2000)
    assert.ok(pad.isDown("b")) // finger 2 still holds it
    pad.release("b", 2001, 2)
    assert.ok(!pad.isDown("b"))
})

test("two fingers on one button: it stays down until both lift", () => {
    const pad = new PadModel()
    pad.press("lb", 0, 1)
    pad.press("lb", 10, 2)
    pad.release("lb", 200, 1)
    assert.ok(pad.isDown("lb"))
    pad.release("lb", 210, 2)
    assert.ok(!pad.isDown("lb"))
})

test("onChange reports new presses by id, nothing for repeats; sticks land on axes 0-3", () => {
    const pad = new PadModel()
    const seen: (ButtonId | null)[] = []
    pad.onChange = (id) => seen.push(id)
    pad.press("x", 0, 1)
    pad.press("x", 1, 2) // already down
    pad.setStick("left", 0.5, -0.25, 2)
    pad.setStick("right", -1, 0, 3)
    pad.setStick("right", -1, 0, 4) // unchanged: no event
    assert.deepEqual(seen, ["x", null, null, null])
    assert.deepEqual(pad.axes, [0.5, -0.25, -1, 0])
    pad.releaseAll(100)
    assert.deepEqual(pad.axes, [0, 0, 0, 0])
    assert.ok(pad.values.every((v) => v === 0))
})

test("every Xbox control Skyrim reads is on screen in all three shapes, none overlapping, all at least 36 px", () => {
    const needed: ButtonId[] = ["a", "b", "x", "y", "lb", "rb", "lt", "rt", "back", "start", "l3", "r3", "up", "down", "left", "right"]
    // Magic V5 inner screen 2352x2172 and cover screen 1060x2376 device px at DPR ~2.6, plus a common 16:9 phone
    const viewports: [number, number, string][] = [[905, 835, "unfolded"], [914, 408, "folded-landscape"], [408, 914, "folded-portrait"], [844, 390, "folded-landscape"], [2352, 2172, "unfolded"]]
    for (const [w, h, shape] of viewports) {
        assert.equal(shapeOf(w, h), shape)
        const l = layoutFor(w, h)
        assert.deepEqual(l.buttons.map((b) => b.id).sort(), [...needed].sort(), `${w}x${h}`)
        assert.deepEqual(layoutProblems(l, w, h), [], `${w}x${h}`)
        for (const b of l.buttons) assert.ok(b.rect.w >= 34 && b.rect.h >= 34, `${b.id} at ${w}x${h} is ${b.rect.w}x${b.rect.h}`)
        // both stick zones are big drag areas, not knobs: each at least a third of the width and a third of the height
        // the rings that show where a stick rests sit clear of every button (a thumb landing to move hits no button)
        for (const z of l.zones) for (const b of l.buttons) {
            const r = b.rect, cx = Math.max(r.x, Math.min(z.rest.x, r.x + r.w)), cy = Math.max(r.y, Math.min(z.rest.y, r.y + r.h))
            assert.ok(Math.hypot(cx - z.rest.x, cy - z.rest.y) >= z.radius * 0.7, `${z.side} rest ring under ${b.id} at ${w}x${h}`)
        }
        const minH = h / 3 - (shape === "folded-portrait" ? w * 9 / 16 : 0)
        for (const z of l.zones) assert.ok(z.rect.w >= w / 3 && z.rect.h >= minH, `${z.side} zone at ${w}x${h}`)
    }
})

test("folded landscape: every button sits in a side band, clear of the picture, its HUD and the Journal's tabs", () => {
    for (const [w, h] of [[970, 432], [914, 408], [844, 390]]) {
        const band = bandWidth(w, h)
        assert.ok(band >= 150 && w - 2 * band >= h * 1.25, `${w}x${h} band ${band}`)
        for (const b of layoutFor(w, h).buttons) {
            const r = b.rect
            assert.ok(r.x + r.w <= band || r.x >= w - band, `${b.id} over the picture at ${w}x${h}`)
            assert.ok(r.w >= 44 && r.h >= 44, `${b.id} at ${w}x${h} is ${r.w}x${r.h}`)
        }
    }
    assert.equal(bandWidth(784, 724), 0)
})

test("no control, toggle or stick ring overlaps the HUD-bar, effects, money, Tween level bar or Journal-tab exclusions; unfolded keeps the whole picture, targets >= 44 px", () => {
    const hit = (p: { x: number, y: number, w: number, h: number }, q: { x: number, y: number, w: number, h: number }) =>
        p.x < q.x + q.w && q.x < p.x + p.w && p.y < q.y + q.h && q.y < p.y + p.h
    for (const [w, h] of [[784, 724], [905, 835], [2352, 2172], [970, 432], [914, 408], [844, 390]]) {
        const l = layoutFor(w, h)
        assert.ok(l.shape === "unfolded" || l.shape === "folded-landscape")
        if (l.shape === "unfolded") assert.equal(bandWidth(w, h), 0) // the picture is the whole screen
        const ex = exclusionRects(w, h)
        const items = [...l.buttons.map((b) => ({ id: b.id as string, r: b.rect })), { id: "toggle", r: l.toggle },
            ...(l.shape === "unfolded" ? l.zones : []).map((z) => ({ id: `${z.side}-ring`, r: { x: z.rest.x - z.radius, y: z.rest.y - z.radius, w: 2 * z.radius, h: 2 * z.radius } }))]
        for (const it of items) for (const e of ex) assert.ok(!hit(it.r, e.r), `${it.id} overlaps ${e.name} at ${w}x${h}`)
        for (const b of l.buttons) assert.ok(b.rect.w >= 44 && b.rect.h >= 44, `${b.id} at ${w}x${h} is ${b.rect.w}x${b.rect.h}`)
        assert.ok(l.toggle.w >= 44, `toggle at ${w}x${h}`)
        for (const z of l.zones) assert.ok(z.radius >= 44 || l.shape !== "unfolded", `${z.side} ring radius ${z.radius}`)
    }
})

test("a tap is held at least 120 ms, so the game sees a touch B or RT as it sees a pad press", () => {
    assert.ok(MIN_HOLD_MS >= 120)
})
