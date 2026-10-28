// The virtual controller (chunk 0.0 §c). Upstream Moonlight-Web reads pads only through the Gamepad API: it adds a
// controller on "gamepadconnected" (web/stream.ts onGamepadAdd -> input.ts onGamepadConnect -> sendControllerAdd),
// polls navigator.getGamepads() every animation frame (input.ts onGamepadUpdate -> extractGamepadState ->
// sendController) and drops it on "gamepaddisconnected". So the touch pad joins there: getGamepads() is wrapped to
// return our standard-mapping pad in a free slot, and the two events are dispatched for it. Upstream then sends it
// exactly as a real pad, and Sunshine shows Skyrim an Xbox 360 controller.

import { PadModel } from "./touch_model.ts"

export const VIRTUAL_ID = "Argonia touch gamepad (Xbox layout) (STANDARD GAMEPAD)"
export const isVirtual = (g: Gamepad | null | undefined) => !!g && g.id === VIRTUAL_ID

type PadLike = {
    id: string, index: number, connected: boolean, mapping: "standard", timestamp: number,
    axes: readonly number[], buttons: readonly { pressed: boolean, touched: boolean, value: number }[],
    vibrationActuator: unknown,
}

export class VirtualPad {
    readonly model = new PadModel()
    index = -1
    connected = false
    private readonly nativeGetGamepads: () => (Gamepad | null)[]
    private vibrating = false

    constructor() {
        const native = navigator.getGamepads ? navigator.getGamepads.bind(navigator) : () => []
        this.nativeGetGamepads = () => Array.from(native() ?? [])
        Object.defineProperty(navigator, "getGamepads", { configurable: true, writable: true, value: () => this.getGamepads() })
    }

    /** Real pads only (the GameSir X2s on the phone, an Xbox pad on a desktop). */
    realPads(): Gamepad[] { return this.nativeGetGamepads().filter((g): g is Gamepad => !!g && g.connected !== false) }

    getGamepads(): (Gamepad | null)[] {
        const list = this.nativeGetGamepads()
        if (!this.connected) return list
        this.model.tick(performance.now())
        while (list.length <= this.index) list.push(null)
        if (!list[this.index]) list[this.index] = this.snapshot(true) as unknown as Gamepad
        return list
    }

    connect() {
        if (this.connected) return
        const used = new Set(this.realPads().map((g) => g.index))
        let i = 0
        while (used.has(i)) i++
        this.index = i
        this.connected = true
        this.dispatch("gamepadconnected", true)
    }

    disconnect() {
        if (!this.connected) return
        this.model.releaseAll(performance.now())
        this.connected = false
        this.dispatch("gamepaddisconnected", false)
        this.stopVibration()
    }

    private dispatch(type: string, connected: boolean) {
        // GamepadEvent's constructor demands a real Gamepad, so a plain Event carries ours
        const ev = new Event(type)
        Object.defineProperty(ev, "gamepad", { value: this.snapshot(connected) })
        window.dispatchEvent(ev)
    }

    private snapshot(connected: boolean): PadLike {
        const m = this.model
        return {
            id: VIRTUAL_ID, index: this.index, connected, mapping: "standard", timestamp: m.timestamp,
            axes: m.axes.slice(),
            buttons: m.values.map((v) => ({ pressed: v > 0, touched: v > 0, value: v })),
            vibrationActuator: this.actuator,
        }
    }

    /** Rumble from the game (Sunshine -> upstream's rumble interval) becomes the phone's vibration motor. */
    private readonly actuator = {
        type: "dual-rumble",
        effects: ["dual-rumble"],
        playEffect: (_type: string, p: { duration?: number, weakMagnitude?: number, strongMagnitude?: number }) => {
            const strength = Math.max(p?.weakMagnitude ?? 0, p?.strongMagnitude ?? 0)
            if (strength > 0.1 && navigator.vibrate) {
                navigator.vibrate(Math.max(20, Math.min(200, p?.duration ?? 60)))
                this.vibrating = true
            } else if (this.vibrating) this.stopVibration()
            return Promise.resolve("complete")
        },
        reset: () => { this.stopVibration(); return Promise.resolve("complete") },
    }

    private stopVibration() {
        if (this.vibrating && navigator.vibrate) navigator.vibrate(0)
        this.vibrating = false
    }
}
