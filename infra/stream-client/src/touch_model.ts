// The touch gamepad's model (chunk 0.0 §c), kept free of the DOM so node tests can drive it.
// It produces exactly what a W3C "standard" mapping gamepad reports, which upstream Moonlight-Web reads with
// navigator.getGamepads() and turns into Moonlight controller packets; Sunshine then presents an Xbox 360 pad.
//
// Kept from the old repo's touch controls (world-render/player/TouchControls.tsx): one finger owns one control
// (claim on down, release only when that finger lifts), a press is held long enough that the poll never misses a
// tap (its "pulse"), stick travel as a fraction of the control, and a layer that only takes hits on its controls.
// Reworked (owner ruling 2026-10-28): the old layout changed with game state (drawn, aiming, swimming) the page
// cannot see here, and fed the old engine's actions; Skyrim reads a fixed Xbox pad, so every Xbox control is on
// screen all the time and the game decides what it does.

/** W3C standard gamepad button indices. */
export const BUTTON_INDEX = {
    a: 0, b: 1, x: 2, y: 3, lb: 4, rb: 5, lt: 6, rt: 7, back: 8, start: 9, l3: 10, r3: 11,
    up: 12, down: 13, left: 14, right: 15, guide: 16,
} as const
export type ButtonId = keyof typeof BUTTON_INDEX
export const BUTTON_COUNT = 17

/** A tap is held at least this long (or until the finger lifts, if later). 50 ms reached the pad poll but not the
 *  game: a touch tap on B left our HTML journal open and a tap on RT gave no One Click Power Attack, where a 150 ms
 *  pad press did both (lane mobile-17, 2026-10-30). */
export const MIN_HOLD_MS = 150
/** Radial dead zone of the touch sticks, as a fraction of the stick radius. */
export const STICK_DEADZONE = 0.08

/** A finger's drag from where it landed, as a stick: x right, y down (the Gamepad API's axes), each -1..1. */
export function stickFromDrag(dx: number, dy: number, radius: number, deadzone = STICK_DEADZONE): { x: number, y: number } {
    const d = Math.hypot(dx, dy)
    if (radius <= 0 || d === 0) return { x: 0, y: 0 }
    const m = Math.min(1, d / radius)
    if (m <= deadzone) return { x: 0, y: 0 }
    const scaled = (m - deadzone) / (1 - deadzone)
    const r = (v: number) => Math.round(v * 1000) / 1000
    return { x: r((dx / d) * scaled), y: r((dy / d) * scaled) }
}

/** The pad's state with tap stretching; `now` is performance.now() or a test clock. */
export class PadModel {
    readonly values: number[] = new Array(BUTTON_COUNT).fill(0)
    readonly axes: number[] = [0, 0, 0, 0]
    private downAt: number[] = new Array(BUTTON_COUNT).fill(-Infinity)
    private holders: Set<number>[] = Array.from({ length: BUTTON_COUNT }, () => new Set())
    private releaseDue: number[] = new Array(BUTTON_COUNT).fill(Infinity)
    timestamp = 0
    /** Called on every change, with the button index for a new press (else null). */
    onChange: ((pressed: ButtonId | null) => void) | null = null

    /** `holder` is the finger (pointerId); a button stays down while any finger holds it. */
    press(id: ButtonId, now: number, holder = 0, value = 1) {
        const i = BUTTON_INDEX[id]
        const wasDown = this.values[i] > 0
        this.holders[i].add(holder)
        this.releaseDue[i] = Infinity
        if (!wasDown) this.downAt[i] = now
        this.values[i] = value
        this.timestamp = now
        this.onChange?.(wasDown ? null : id)
    }

    release(id: ButtonId, now: number, holder = 0) {
        const i = BUTTON_INDEX[id]
        this.holders[i].delete(holder)
        if (this.holders[i].size > 0 || this.values[i] === 0) return
        const due = this.downAt[i] + MIN_HOLD_MS
        if (now >= due) this.clear(i, now)
        else this.releaseDue[i] = due
    }

    /** Applies releases deferred by the minimum hold; call on every frame (the getGamepads hook does). */
    tick(now: number) {
        for (let i = 0; i < BUTTON_COUNT; i++) {
            if (this.releaseDue[i] <= now) this.clear(i, now)
        }
    }

    releaseAll(now: number) {
        for (let i = 0; i < BUTTON_COUNT; i++) { this.holders[i].clear(); this.releaseDue[i] = Infinity; if (this.values[i]) this.clear(i, now) }
        this.setStick("left", 0, 0, now)
        this.setStick("right", 0, 0, now)
    }

    setStick(side: "left" | "right", x: number, y: number, now: number) {
        const o = side === "left" ? 0 : 2
        if (this.axes[o] === x && this.axes[o + 1] === y) return
        this.axes[o] = x
        this.axes[o + 1] = y
        this.timestamp = now
        this.onChange?.(null)
    }

    isDown(id: ButtonId): boolean { return this.values[BUTTON_INDEX[id]] > 0 }

    private clear(i: number, now: number) {
        this.values[i] = 0
        this.releaseDue[i] = Infinity
        this.timestamp = now
        this.onChange?.(null)
    }
}

// -- Layout

export type Shape = "unfolded" | "folded-landscape" | "folded-portrait"
export type Rect = { x: number, y: number, w: number, h: number }
export type ButtonSpec = { kind: "button", id: ButtonId, label: string, rect: Rect, round: boolean, small?: boolean }
export type ZoneSpec = { kind: "stick", side: "left" | "right", rect: Rect, radius: number, rest: { x: number, y: number } }
export type Layout = { shape: Shape, unit: number, buttons: ButtonSpec[], zones: ZoneSpec[], toggle: Rect }

/** Near-square is the Magic V5 unfolded (inner 2352x2172); wider is the folded phone in landscape; taller, portrait. */
export function shapeOf(w: number, h: number): Shape {
    const a = w / h
    if (a >= 0.8 && a <= 1.3) return "unfolded"
    return a > 1.3 ? "folded-landscape" : "folded-portrait"
}

/** Pad glyphs: what Skyrim's own prompts show for an Xbox pad, so a prompt reads straight onto the button. */
const LABEL: Record<ButtonId, string> = {
    a: "A", b: "B", x: "X", y: "Y", lb: "LB", rb: "RB", lt: "LT", rt: "RT", back: "Back", start: "Start",
    l3: "L3", r3: "R3", up: "▲", down: "▼", left: "◀", right: "▶", guide: "",
}

/**
 * Every control placed for a viewport in CSS pixels, laid out as Skyrim's Xbox pad is held: triggers and bumpers
 * in the top corners (index fingers), Back and Start at the top centre, the face diamond under the right thumb with
 * R3 (lock-on in True Directional Movement) inboard of it, the d-pad and L3 (sneak) in the upper left. The two
 * stick zones fill each half below the top row: a finger landing anywhere in them becomes that stick's centre.
 * In portrait the 16:9 picture sits at the top, so the controls fill the band below it.
 */
export function layoutFor(w: number, h: number): Layout {
    const shape = shapeOf(w, h)
    if (shape === "folded-landscape") return bandLayout(w, h)
    if (shape === "unfolded") return stripLayout(w, h)
    const short = Math.min(w, h)
    // the button diameter: ~9.5% of the short side, never under 44 px (the touch minimum) nor over 96
    const unit = Math.round(Math.max(44, Math.min(96, short * (0.095))))
    const gap = Math.round(unit * 0.18)
    const m = Math.round(Math.max(12, unit * 0.3)) // edge margin, clear of rounded corners
    // portrait: controls live under the video (16:9 at the top)
    const top = shape === "folded-portrait" ? Math.round(w * 9 / 16) + m : 0
    const H = h - top
    const buttons: ButtonSpec[] = []
    const add = (id: ButtonId, cx: number, cy: number, size = unit, round = true, small = false) =>
        buttons.push({ kind: "button", id, label: LABEL[id], round, small, rect: { x: Math.round(cx - size / 2), y: Math.round(top + cy - size / 2), w: Math.round(size), h: Math.round(size) } })

    // right: the face diamond in the bottom-right corner
    const d = unit + gap * 0.6 // centre to centre, diamond arm
    const fx = w - m - unit / 2 - d
    const fy = H - m - unit / 2 - d
    add("y", fx, fy - d)
    add("x", fx - d, fy)
    add("b", fx + d, fy)
    add("a", fx, fy + d)
    // R3 left of the diamond, low: the lock-on in True Directional Movement
    add("r3", fx - 2 * d - gap, fy + d * 0.6, unit * 0.85)
    // shoulders and triggers in the top corners, as on a pad: the trigger outboard, the bumper inboard (stacked
    // under it where the screen is too narrow for both side by side), Back and Start between them at the top centre
    const sw = unit * 1.5
    const sh = unit * 0.8
    const ty = m + sh / 2
    const stacked = w < 6 * sw + 8 * gap
    const pill = (id: ButtonId, cx: number, cy: number, small = false) =>
        buttons.push({ kind: "button", id, label: LABEL[id], round: false, small, rect: { x: Math.round(cx - sw / 2), y: Math.round(top + cy - sh / 2), w: Math.round(sw), h: Math.round(sh) } })
    const lx = m + sw / 2
    const rx = w - m - sw / 2
    pill("lt", lx, ty)
    pill("rt", rx, ty)
    if (stacked) { pill("lb", lx, ty + sh + gap); pill("rb", rx, ty + sh + gap) }
    else { pill("lb", lx + sw + gap, ty); pill("rb", rx - sw - gap, ty) }
    const tc = w / 2
    pill("back", tc - gap / 2 - sw / 2, ty, true)
    pill("start", tc + gap / 2 + sw / 2, ty, true)
    const rowBottom = (stacked ? ty + sh + gap : ty) + sh / 2
    // the d-pad (favourites) and L3 (sneak) in the upper left, clear of where the left thumb lands to move
    const dp = Math.max(40, unit * 0.78)
    const dcx = m + dp * 1.5
    const dcy = rowBottom + gap * 1.5 + dp * 1.5
    const ds = dp * 0.92
    add("up", dcx, dcy - dp, ds, false, true)
    add("down", dcx, dcy + dp, ds, false, true)
    add("left", dcx - dp, dcy, ds, false, true)
    add("right", dcx + dp, dcy, ds, false, true)
    add("l3", dcx + dp * 2.7, dcy, unit * 0.85)

    // stick zones: each half below the top row; the buttons stack over them and take their own hits. The rings
    // show where each stick rests: the left in the bottom-left corner, the right inboard of the face diamond.
    const zoneTop = top + Math.round(ty + sh / 2 + gap)
    const radius = Math.round(unit * 1.25)
    const zones: ZoneSpec[] = [
        { kind: "stick", side: "left", radius, rect: { x: 0, y: zoneTop, w: Math.round(w / 2), h: h - zoneTop }, rest: { x: Math.round(m + radius + unit * 0.3), y: Math.round(h - m - radius) } },
        { kind: "stick", side: "right", radius, rect: { x: Math.round(w / 2), y: zoneTop, w: w - Math.round(w / 2), h: h - zoneTop }, rest: { x: Math.round(fx - 3 * d), y: Math.round(top + fy - d * 1.2) } },
    ]
    const ts = Math.round(Math.max(36, unit * 0.6))
    const toggle = { x: Math.round(tc - ts / 2), y: Math.round(top + ty + sh / 2 + gap), w: ts, h: ts }
    if (dcy + dp * 1.5 > zones[0].rest.y - radius + top) zones[0].rest.y = Math.round(Math.min(h - m - radius / 2, top + dcy + dp * 1.5 + gap + radius))
    return { shape, unit, buttons, zones, toggle }
}

/** The folded phone in landscape: the screen is too short for buttons over the picture without covering the
 *  HUD (the LB pill sat on the health and stamina bars and A on the money counter, lane mobile-17), so every button
 *  lives in a band at each side and the stream is asked for the picture between them (stream_settings.ts). */
export function bandUnit(h: number): number { return Math.round(Math.max(44, Math.min(96, h * 0.11))) }
export function bandWidth(w: number, h: number): number {
    if (shapeOf(w, h) !== "folded-landscape") return 0
    return Math.min(Math.round(w * 0.3), Math.round(bandUnit(h) * 3.8))
}

function bandLayout(w: number, h: number): Layout {
    const unit = bandUnit(h)
    const gap = Math.round(unit * 0.18)
    const m = Math.round(Math.max(12, unit * 0.3))
    const band = bandWidth(w, h)
    const buttons: ButtonSpec[] = []
    const add = (id: ButtonId, cx: number, cy: number, size = unit, round = true, small = false) =>
        buttons.push({ kind: "button", id, label: LABEL[id], round, small, rect: { x: Math.round(cx - size / 2), y: Math.round(cy - size / 2), w: Math.round(size), h: Math.round(size) } })
    const sw = Math.min(unit * 1.5, band - 2 * m), sh = Math.max(44, unit * 0.8)
    const pill = (id: ButtonId, cx: number, cy: number, small = false) =>
        buttons.push({ kind: "button", id, label: LABEL[id], round: false, small, rect: { x: Math.round(cx - sw / 2), y: Math.round(cy - sh / 2), w: Math.round(sw), h: Math.round(sh) } })
    const lc = band / 2, rc = w - band / 2
    const ty = m + sh / 2, by = ty + sh + gap
    pill("lt", lc, ty); pill("lb", lc, by)
    pill("rt", rc, ty); pill("rb", rc, by)
    // Back (journal) and Start (Tween) stay in the bands too: over the picture's top centre they sat on the
    // Journal's tabs (ui-review5). Back at the foot of the left band, Start under RB.
    pill("back", lc, h - m - sh / 2, true)
    pill("start", rc, by + sh + gap, true)
    const tc = w / 2
    // left band: the d-pad, then L3 under it
    const dp = Math.max(48, unit * 0.78)
    const dcy = by + sh / 2 + gap + dp * 1.5
    add("up", lc, dcy - dp, dp * 0.92, false, true)
    add("down", lc, dcy + dp, dp * 0.92, false, true)
    add("left", lc - dp, dcy, dp * 0.92, false, true)
    add("right", lc + dp, dcy, dp * 0.92, false, true)
    add("l3", lc, Math.min(h - m - sh - gap - unit * 0.425, dcy + dp * 1.5 + gap + unit * 0.425), Math.max(44, unit * 0.85))
    // right band: the face diamond in the bottom corner, R3 above it
    const d = unit + gap * 0.6
    const fy = h - m - unit / 2 - d
    add("y", rc, fy - d); add("x", rc - d, fy); add("b", rc + d, fy); add("a", rc, fy + d)
    add("r3", rc + d, Math.max(by + sh * 1.5 + 2 * gap + unit * 0.425, fy - d - gap - unit * 0.5), Math.max(44, unit * 0.85))
    const zoneTop = Math.round(ty + sh / 2 + gap)
    const radius = Math.round(unit * 1.25)
    // the rings rest on the picture's inner edge: bottom left (nothing of the HUD there) and mid right (the money
    // counter sits bottom right)
    const zones: ZoneSpec[] = [
        { kind: "stick", side: "left", radius, rect: { x: 0, y: zoneTop, w: Math.round(w / 2), h: h - zoneTop }, rest: { x: Math.round(band + m + radius), y: Math.round(h - m - radius) } },
        { kind: "stick", side: "right", radius, rect: { x: Math.round(w / 2), y: zoneTop, w: w - Math.round(w / 2), h: h - zoneTop }, rest: { x: Math.round(w - band - m - radius), y: Math.round(h / 2 + gap) } },
    ]
    const ts = Math.round(Math.max(36, unit * 0.6))
    const toggle = { x: Math.round(tc - ts / 2), y: Math.round(ty + sh / 2 + gap), w: ts, h: ts }
    return { shape: "folded-landscape", unit, buttons, zones, toggle }
}

/** The unfolded phone: buttons over a near-square picture sat on the HUD bars (top left, under LT/LB), the money
 *  counter (under A), the Tween level bar (under the right stick) and the Journal's tabs (ui-review5), so the
 *  controls live in a strip above and below the picture and the stream is asked for the picture between them
 *  (stream_settings.ts; upstream centres the video, so the strips are equal). Top: the shoulders, Back, Start, L3
 *  and R3; bottom: the d-pad, the two stick rings and the face diamond. */
export function stripUnit(w: number, h: number): number { return Math.round(Math.max(44, Math.min(72, Math.min(w, h) * 0.06))) }
export function stripHeight(w: number, h: number): number {
    if (shapeOf(w, h) !== "unfolded") return 0
    const unit = stripUnit(w, h), gap = Math.round(unit * 0.18), m = Math.round(Math.max(12, unit * 0.3))
    return Math.round(2 * (unit + gap * 0.6) + unit + 2 * m)
}

function stripLayout(w: number, h: number): Layout {
    const unit = stripUnit(w, h)
    const gap = Math.round(unit * 0.18)
    const m = Math.round(Math.max(12, unit * 0.3))
    const strip = stripHeight(w, h)
    const buttons: ButtonSpec[] = []
    const add = (id: ButtonId, cx: number, cy: number, size = unit, round = true, small = false) =>
        buttons.push({ kind: "button", id, label: LABEL[id], round, small, rect: { x: Math.round(cx - size / 2), y: Math.round(cy - size / 2), w: Math.round(size), h: Math.round(size) } })
    const sw = unit * 1.5, sh = Math.max(44, unit * 0.8)
    const pill = (id: ButtonId, cx: number, cy: number, small = false) =>
        buttons.push({ kind: "button", id, label: LABEL[id], round: false, small, rect: { x: Math.round(cx - sw / 2), y: Math.round(cy - sh / 2), w: Math.round(sw), h: Math.round(sh) } })
    // top strip: triggers outboard, bumpers inboard, Back and Start at the centre; L3 and R3 under the bumpers
    const ty = m + sh / 2
    const lx = m + sw / 2, rx = w - m - sw / 2
    pill("lt", lx, ty); pill("lb", lx + sw + gap, ty)
    pill("rt", rx, ty); pill("rb", rx - sw - gap, ty)
    const tc = w / 2
    pill("back", tc - gap / 2 - sw / 2, ty, true)
    pill("start", tc + gap / 2 + sw / 2, ty, true)
    const l3y = Math.min(strip - m - unit * 0.425, ty + sh / 2 + gap + unit * 0.425)
    add("l3", lx, l3y, Math.max(44, unit * 0.85))
    add("r3", rx, l3y, Math.max(44, unit * 0.85))
    // bottom strip: the d-pad at the left, the face diamond at the right, the stick rings between
    const base = h - strip
    const dp = Math.max(48, unit * 0.78)
    const dcx = m + dp * 1.5, dcy = base + strip / 2
    const ds = dp * 0.92
    add("up", dcx, dcy - dp, ds, false, true)
    add("down", dcx, dcy + dp, ds, false, true)
    add("left", dcx - dp, dcy, ds, false, true)
    add("right", dcx + dp, dcy, ds, false, true)
    const d = unit + gap * 0.6
    const fx = w - m - unit / 2 - d, fy = base + strip / 2
    add("y", fx, fy - d); add("x", fx - d, fy); add("b", fx + d, fy); add("a", fx, fy + d)
    const radius = Math.round(Math.min(unit * 1.25, strip / 2 - m))
    const zones: ZoneSpec[] = [
        { kind: "stick", side: "left", radius, rect: { x: 0, y: base, w: Math.round(w / 2), h: strip }, rest: { x: Math.round(dcx + dp * 1.5 + gap + radius * 1.4), y: Math.round(dcy) } },
        { kind: "stick", side: "right", radius, rect: { x: Math.round(w / 2), y: base, w: w - Math.round(w / 2), h: strip }, rest: { x: Math.round(fx - d - unit / 2 - gap - radius * 1.4), y: Math.round(fy) } },
    ]
    const ts = Math.round(Math.max(36, unit * 0.6))
    const toggle = { x: Math.round(tc - ts / 2), y: Math.round(ty + sh / 2 + gap), w: ts, h: ts }
    return { shape: "unfolded", unit, buttons, zones, toggle }
}

/** Rectangles that overlap (for the layout test): any two buttons, or a button off screen. */
export function layoutProblems(l: Layout, w: number, h: number): string[] {
    const out: string[] = []
    const all = [...l.buttons.map((b) => ({ id: b.id as string, r: b.rect })), { id: "toggle", r: l.toggle }]
    for (const a of all) {
        if (a.r.x < 0 || a.r.y < 0 || a.r.x + a.r.w > w || a.r.y + a.r.h > h) out.push(`${a.id} off screen`)
    }
    for (let i = 0; i < all.length; i++) for (let j = i + 1; j < all.length; j++) {
        const p = all[i].r, q = all[j].r
        if (p.x < q.x + q.w && q.x < p.x + p.w && p.y < q.y + q.h && q.y < p.y + p.h) out.push(`${all[i].id} overlaps ${all[j].id}`)
    }
    return out
}
