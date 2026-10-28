// The on-screen gamepad (chunk 0.0 §c): DOM over upstream's stream page, feeding the VirtualPad's model.
// The layer itself takes no hits (pointer-events: none); only its buttons and the two stick zones do, so
// upstream's sidebar, menus and notifications above it keep working (the old repo's walk-11 lesson).

import { layoutFor, stickFromDrag, type ButtonId, type Layout, type ZoneSpec } from "./touch_model.ts"
import type { VirtualPad } from "./virtual_pad.ts"

const CSS = `
#argonia-touch { position: fixed; inset: 0; pointer-events: none; z-index: 900; user-select: none; -webkit-user-select: none;
  -webkit-touch-callout: none; -webkit-tap-highlight-color: transparent; font: 600 16px/1 system-ui, sans-serif; }
#argonia-touch[hidden] { display: none; }
#argonia-touch .at-zone { position: absolute; pointer-events: auto; touch-action: none; }
#argonia-touch .at-ring { position: absolute; border-radius: 50%; border: 2px solid rgba(235,230,210,.35); background: rgba(20,24,18,.18);
  pointer-events: none; transform: translate(-50%,-50%); }
#argonia-touch .at-ring.at-live { border-color: rgba(235,230,210,.7); background: rgba(20,24,18,.3); }
#argonia-touch .at-nub { position: absolute; left: 50%; top: 50%; width: 42%; height: 42%; border-radius: 50%; transform: translate(-50%,-50%);
  background: rgba(235,230,210,.35); }
#argonia-touch .at-btn { position: absolute; pointer-events: auto; touch-action: none; display: flex; align-items: center; justify-content: center;
  color: rgba(245,240,225,.92); background: rgba(20,24,18,.42); border: 2px solid rgba(235,230,210,.45); box-sizing: border-box;
  text-shadow: 0 1px 2px #000; }
#argonia-touch .at-btn.at-round { border-radius: 50%; }
#argonia-touch .at-btn:not(.at-round) { border-radius: 14px; }
#argonia-touch .at-btn.at-down { background: rgba(235,230,210,.55); color: #111; text-shadow: none; }
#argonia-touch .at-btn[data-id="a"] { border-color: rgba(120,200,90,.8); }
#argonia-touch .at-btn[data-id="b"] { border-color: rgba(220,80,70,.8); }
#argonia-touch .at-btn[data-id="x"] { border-color: rgba(80,140,230,.8); }
#argonia-touch .at-btn[data-id="y"] { border-color: rgba(230,190,60,.85); }
#argonia-touch-toggle { position: fixed; z-index: 901; pointer-events: auto; touch-action: none; border-radius: 10px; opacity: .55;
  background: rgba(20,24,18,.5); border: 2px solid rgba(235,230,210,.5); display: flex; align-items: center; justify-content: center; }
#argonia-touch-toggle[aria-pressed="true"] { opacity: .8; }
html.argonia-touch-on, html.argonia-touch-on body { touch-action: none; overscroll-behavior: none; overflow: hidden; }
`

const PAD_ICON = `<svg viewBox="0 0 24 16" width="70%" height="70%" aria-hidden="true"><rect x="1" y="1" width="22" height="14" rx="7" fill="none"
 stroke="rgba(245,240,225,.9)" stroke-width="1.6"/><path d="M6 8h4M8 6v4" stroke="rgba(245,240,225,.9)" stroke-width="1.6"/>
 <circle cx="16" cy="7" r="1.2" fill="rgba(245,240,225,.9)"/><circle cx="18.5" cy="9.5" r="1.2" fill="rgba(245,240,225,.9)"/></svg>`

export type TouchLayerHooks = {
    /** A new press from the touch pad (for the press-to-screen pairing and the input-source count). */
    onPress?: (id: ButtonId, at: number) => void
    /** Any touch activity on the pad (presses and stick drags). */
    onActivity?: () => void
    onShownChange?: (shown: boolean) => void
}

export class TouchLayer {
    readonly root = document.createElement("div")
    readonly toggle = document.createElement("button")
    private layout: Layout | null = null
    private buttons = new Map<ButtonId, HTMLElement>()
    private override: boolean | null = null
    private shown = false
    private hasTouch: boolean
    private forced: boolean

    constructor(private pad: VirtualPad, private hooks: TouchLayerHooks = {}) {
        const q = new URLSearchParams(location.search)
        this.forced = q.get("argoniaTouch") === "1"
        this.hasTouch = this.forced || (navigator.maxTouchPoints ?? 0) > 0 || matchMedia("(pointer: coarse)").matches
        if (q.get("argoniaTouch") === "0") this.override = false
        const style = document.createElement("style")
        style.textContent = CSS
        document.head.appendChild(style)
        this.root.id = "argonia-touch"
        this.root.hidden = true
        this.root.addEventListener("contextmenu", (e) => e.preventDefault())
        // no page scroll, pinch or double-tap zoom while a finger is on the pad
        this.root.addEventListener("touchmove", (e) => e.preventDefault(), { passive: false })
        this.root.addEventListener("touchstart", (e) => { if (e.touches.length > 1) e.preventDefault() }, { passive: false })
        document.addEventListener("gesturestart", (e) => e.preventDefault())
        this.toggle.id = "argonia-touch-toggle"
        this.toggle.type = "button"
        this.toggle.setAttribute("aria-label", "Show or hide the touch gamepad")
        this.toggle.innerHTML = PAD_ICON
        this.toggle.addEventListener("pointerdown", (e) => { e.preventDefault(); e.stopPropagation() })
        this.toggle.addEventListener("click", (e) => { e.stopPropagation(); this.override = !this.shown; this.update() })
        document.body.appendChild(this.root)
        document.body.appendChild(this.toggle)
        // pads: hide the touch pad when a real one connects (ours is told apart by its id)
        window.addEventListener("gamepadconnected", (e) => { if (!(e as GamepadEvent).gamepad?.id?.startsWith("Argonia")) { this.override = null; this.update() } })
        window.addEventListener("gamepaddisconnected", (e) => { if (!(e as GamepadEvent).gamepad?.id?.startsWith("Argonia")) this.update() })
        window.addEventListener("resize", () => this.render())
        window.addEventListener("orientationchange", () => this.render())
        window.addEventListener("blur", () => this.pad.model.releaseAll(performance.now()))
        document.addEventListener("visibilitychange", () => { if (document.hidden) this.pad.model.releaseAll(performance.now()) })
        this.pad.model.onChange = () => this.paint()
        this.render()
        this.update()
    }

    isShown() { return this.shown }

    /** Auto: shown on a touch device with no real pad; the toggle overrides until a real pad connects. */
    update() {
        const auto = this.hasTouch && this.pad.realPads().length === 0
        const shown = this.override ?? auto
        this.toggle.hidden = !this.hasTouch && this.override === null
        this.toggle.setAttribute("aria-pressed", String(shown))
        if (shown === this.shown) return
        this.shown = shown
        this.root.hidden = !shown
        document.documentElement.classList.toggle("argonia-touch-on", shown)
        if (shown) this.pad.connect(); else this.pad.disconnect()
        this.hooks.onShownChange?.(shown)
    }

    private render() {
        const w = window.innerWidth, h = window.innerHeight
        const l = layoutFor(w, h)
        this.layout = l
        this.root.replaceChildren()
        this.buttons.clear()
        this.root.dataset.shape = l.shape
        for (const z of l.zones) this.root.appendChild(this.zone(z))
        for (const b of l.buttons) {
            const el = document.createElement("div")
            el.className = "at-btn" + (b.round ? " at-round" : "")
            el.dataset.id = b.id
            el.setAttribute("role", "button")
            el.setAttribute("aria-label", b.label || b.id)
            el.textContent = b.label
            Object.assign(el.style, { left: `${b.rect.x}px`, top: `${b.rect.y}px`, width: `${b.rect.w}px`, height: `${b.rect.h}px`, fontSize: `${Math.round(Math.min(b.rect.w, b.rect.h) * (b.label.length > 2 ? 0.3 : 0.42))}px` })
            this.wireButton(el, b.id)
            this.root.appendChild(el)
            this.buttons.set(b.id, el)
        }
        Object.assign(this.toggle.style, { left: `${l.toggle.x}px`, top: `${l.toggle.y}px`, width: `${l.toggle.w}px`, height: `${l.toggle.h}px` })
        this.paint()
    }

    private paint() {
        for (const [id, el] of this.buttons) el.classList.toggle("at-down", this.pad.model.isDown(id))
    }

    private wireButton(el: HTMLElement, id: ButtonId) {
        const model = this.pad.model
        const held = new Set<number>()
        el.addEventListener("pointerdown", (e) => {
            e.preventDefault()
            e.stopPropagation()
            try { el.setPointerCapture(e.pointerId) } catch { /* synthetic pointers */ }
            held.add(e.pointerId)
            const now = performance.now()
            const was = model.isDown(id)
            model.press(id, now, e.pointerId)
            if (!was) { navigator.vibrate?.(8); this.hooks.onPress?.(id, now) }
            this.hooks.onActivity?.()
        })
        const up = (e: PointerEvent) => {
            if (!held.delete(e.pointerId)) return
            model.release(id, performance.now(), e.pointerId)
        }
        el.addEventListener("pointerup", up)
        el.addEventListener("pointercancel", up)
        el.addEventListener("lostpointercapture", up)
    }

    /** A drag area: the finger's landing point becomes the stick's centre; a ring shows where it rests and where it is held. */
    private zone(z: ZoneSpec): HTMLElement {
        const el = document.createElement("div")
        el.className = "at-zone"
        el.dataset.side = z.side
        Object.assign(el.style, { left: `${z.rect.x}px`, top: `${z.rect.y}px`, width: `${z.rect.w}px`, height: `${z.rect.h}px` })
        const ring = document.createElement("div")
        ring.className = "at-ring"
        const nub = document.createElement("div")
        nub.className = "at-nub"
        ring.appendChild(nub)
        const size = z.radius * 2
        const place = (x: number, y: number) => Object.assign(ring.style, { left: `${x - z.rect.x}px`, top: `${y - z.rect.y}px`, width: `${size}px`, height: `${size}px` })
        place(z.rest.x, z.rest.y)
        el.appendChild(ring)
        let owner: number | null = null
        let ox = 0, oy = 0
        const model = this.pad.model
        el.addEventListener("pointerdown", (e) => {
            e.preventDefault()
            e.stopPropagation()
            if (owner !== null) return // one finger owns a stick; a second finger here does nothing
            owner = e.pointerId
            try { el.setPointerCapture(e.pointerId) } catch { /* synthetic pointers */ }
            ox = e.clientX; oy = e.clientY
            place(ox, oy)
            ring.classList.add("at-live")
            this.hooks.onActivity?.()
        })
        el.addEventListener("pointermove", (e) => {
            if (e.pointerId !== owner) return
            const dx = e.clientX - ox, dy = e.clientY - oy
            const s = stickFromDrag(dx, dy, z.radius)
            model.setStick(z.side, s.x, s.y, performance.now())
            const d = Math.hypot(dx, dy)
            const k = d > z.radius ? z.radius / d : 1
            nub.style.transform = `translate(calc(-50% + ${dx * k}px), calc(-50% + ${dy * k}px))`
            this.hooks.onActivity?.()
        })
        const end = (e: PointerEvent) => {
            if (e.pointerId !== owner) return
            owner = null
            model.setStick(z.side, 0, 0, performance.now())
            nub.style.transform = ""
            ring.classList.remove("at-live")
            place(z.rest.x, z.rest.y)
        }
        el.addEventListener("pointerup", end)
        el.addEventListener("pointercancel", end)
        el.addEventListener("lostpointercapture", end)
        return el
    }
}
