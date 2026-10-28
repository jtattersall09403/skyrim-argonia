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

/** A tap is held at least this long, so a once-per-frame poll (upstream's requestAnimationFrame) always sees it. */
export const MIN_HOLD_MS = 50
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
    const short = Math.min(w, h)
    // the button diameter: ~9.5% of the short side, never under 44 px (the touch minimum) nor over 96
    const unit = Math.round(Math.max(44, Math.min(96, short * (shape === "folded-landscape" ? 0.13 : 0.095))))
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
