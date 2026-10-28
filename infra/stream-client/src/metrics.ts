// Automatic stream metrics (chunk 0.0 §c): a record every second, press-to-screen samples, a session summary.
// Nothing is recorded by hand: the page logs every session to the game machine's collector (sink.ts).

import { rtcRecord, type RtcRecord, type RtcTotals } from "./rtc_stats.ts"
import { summarize } from "./stats_math.ts"
import { MarkerDetector, PressPairer, patchTone, phaseOf, samplePoints, type PendingInput } from "./marker_detect.ts"
import { shapeOf } from "./touch_model.ts"
import { Sink } from "./sink.ts"

export const CLIENT_VERSION = "argonia-stream-client 0.1.0 on moonlight-web-stream v3.0.1"

// -- Hooks, installed before upstream's stream.js runs

const peers: RTCPeerConnection[] = []
const sockets: { ws: WebSocket, bytes: number }[] = []

export function installTransportHooks() {
    const NativePC = window.RTCPeerConnection
    if (NativePC) {
        const Hooked = function (this: unknown, ...args: ConstructorParameters<typeof RTCPeerConnection>) {
            const pc = new NativePC(...args)
            peers.push(pc)
            return pc
        } as unknown as typeof RTCPeerConnection
        Hooked.prototype = NativePC.prototype
        Object.setPrototypeOf(Hooked, NativePC)
        window.RTCPeerConnection = Hooked
    }
    const NativeWS = window.WebSocket
    const HookedWS = function (this: unknown, url: string | URL, protocols?: string | string[]) {
        const ws = new NativeWS(url, protocols)
        if (String(url).includes("/stream/web_socket")) {
            const entry = { ws, bytes: 0 }
            sockets.push(entry)
            ws.addEventListener("message", (e) => {
                const d = e.data as unknown
                entry.bytes += d instanceof ArrayBuffer ? d.byteLength : d instanceof Blob ? d.size : typeof d === "string" ? d.length : 0
            })
        }
        return ws
    } as unknown as typeof WebSocket
    HookedWS.prototype = NativeWS.prototype
    Object.setPrototypeOf(HookedWS, NativeWS)
    window.WebSocket = HookedWS
}

// -- Inputs, for the source count and the press pairing

export type InputSource = "touch" | "gamepad" | "keyboard" | "mouse"

export class InputLog {
    readonly pairer = new PressPairer(1000)
    counts: Record<InputSource, number> = { touch: 0, gamepad: 0, keyboard: 0, mouse: 0 }
    activity: Record<InputSource, number> = { touch: 0, gamepad: 0, keyboard: 0, mouse: 0 }
    presses = 0

    press(source: InputSource, what: string, at: number) {
        this.counts[source]++
        this.activity[source]++
        this.presses++
        this.pairer.input({ at, source, what } satisfies PendingInput)
    }
    active(source: InputSource) { this.activity[source]++ }

    /** The second's counts, then zeroed; the source is the one with most activity. */
    take(): { source: InputSource | "none", presses: Record<InputSource, number> } {
        let source: InputSource | "none" = "none"
        let best = 0
        for (const k of Object.keys(this.activity) as InputSource[]) if (this.activity[k] > best) { best = this.activity[k]; source = k }
        const presses = this.counts
        this.counts = { touch: 0, gamepad: 0, keyboard: 0, mouse: 0 }
        this.activity = { touch: 0, gamepad: 0, keyboard: 0, mouse: 0 }
        return { source, presses }
    }

    /** Keyboard and mouse presses that upstream forwards to the host; real-pad presses by polling. */
    listen(realPads: () => Gamepad[]) {
        const toHost = (t: EventTarget | null) => {
            const el = t as Element | null
            if (!el || !el.closest) return false
            if (el.closest("#argonia-touch, #argonia-touch-toggle, .sidebar-overlay, #modal-overlay, input, textarea, select")) return false
            return true
        }
        const stamp = (e: Event) => (e.timeStamp > 0 && e.timeStamp <= performance.now() + 1 ? e.timeStamp : performance.now())
        window.addEventListener("keydown", (e) => { if (!e.repeat && toHost(e.target)) this.press("keyboard", e.code, stamp(e)) }, { capture: true })
        window.addEventListener("mousedown", (e) => { if (toHost(e.target)) this.press("mouse", `button${e.button}`, stamp(e)) }, { capture: true })
        window.addEventListener("mousemove", (e) => { if (toHost(e.target)) this.active("mouse") }, { capture: true, passive: true })
        let last: boolean[][] = []
        const poll = () => {
            const pads = realPads()
            pads.forEach((g, n) => {
                const prev = last[n] ?? []
                const now = g.buttons.map((b, i) => b.pressed || (i === 6 || i === 7 ? b.value > 0.5 : false))
                now.forEach((p, i) => { if (p && !prev[i]) this.press("gamepad", `b${i}`, performance.now()) })
                if (g.axes.some((a) => Math.abs(a) > 0.25)) this.active("gamepad")
                last[n] = now
            })
            last = last.slice(0, pads.length)
            requestAnimationFrame(poll)
        }
        requestAnimationFrame(poll)
    }
}

// -- The marker probe: samples the decoded video's top-left corner each frame

export type P2S = { at: number, source: string, what: string, ms: number, displayMs: number | null, pending: number }

export class MarkerProbe {
    readonly detector = new MarkerDetector()
    desktopWidth = 0
    markerHalf = 24
    samples: P2S[] = []
    private canvas = document.createElement("canvas")
    private ctx: CanvasRenderingContext2D | null = null
    private target: HTMLVideoElement | HTMLCanvasElement | null = null
    sampleErrors = 0
    frames = 0
    onSample: ((s: P2S) => void) | null = null

    constructor(private inputs: InputLog) { }

    /** The marker's geometry, published by the marker program through the collector. */
    async loadGeometry(baseUrl: string) {
        try {
            const r = await fetch(`${baseUrl.replace(/\/$/, "")}/marker`)
            if (!r.ok) return
            const g = await r.json()
            if (g.screenWidth > 0) this.desktopWidth = g.screenWidth
            if (g.half > 0) this.markerHalf = g.half
        } catch { /* defaults: desktop = stream size */ }
    }

    /** Finds upstream's video element (or its canvas renderer) and samples every frame. */
    watch() {
        const find = () => {
            const v = document.querySelector<HTMLVideoElement>("video.video-stream") ?? document.querySelector<HTMLVideoElement>("#root video")
            const c = v ? null : document.querySelector<HTMLCanvasElement>("#root canvas")
            const t = v ?? c
            if (t && t !== this.target) { this.target = t; this.start(t) }
        }
        setInterval(find, 500)
    }

    private start(t: HTMLVideoElement | HTMLCanvasElement) {
        const video = t instanceof HTMLVideoElement ? t : null
        if (video && "requestVideoFrameCallback" in video) {
            const cb = (_now: number, meta: VideoFrameCallbackMetadata) => {
                if (this.target !== video) return
                this.sample(video, video.videoWidth, meta.expectedDisplayTime ?? performance.now(), meta.presentationTime ?? null)
                video.requestVideoFrameCallback(cb)
            }
            video.requestVideoFrameCallback(cb)
        } else {
            const loop = () => {
                if (this.target !== t) return
                const w = t instanceof HTMLVideoElement ? t.videoWidth : (t as HTMLCanvasElement).width
                this.sample(t, w, performance.now(), null)
                requestAnimationFrame(loop)
            }
            requestAnimationFrame(loop)
        }
    }

    private sample(src: CanvasImageSource, width: number, displayAt: number, presentedAt: number | null) {
        if (!width) return
        this.frames++
        const s = samplePoints(width, this.desktopWidth || width, this.markerHalf)
        const p = s.patch
        if (this.canvas.width !== p * 2) { this.canvas.width = p * 2; this.canvas.height = p; this.ctx = this.canvas.getContext("2d", { willReadFrequently: false }) }
        const ctx = this.ctx
        if (!ctx) return
        try {
            ctx.drawImage(src, s.left[0] - p / 2, s.left[1] - p / 2, p, p, 0, 0, p, p)
            ctx.drawImage(src, s.right[0] - p / 2, s.right[1] - p / 2, p, p, p, 0, p, p)
            const img = ctx.getImageData(0, 0, p * 2, p).data
            const left = new Uint8ClampedArray(p * p * 4), right = new Uint8ClampedArray(p * p * 4)
            for (let y = 0; y < p; y++) {
                left.set(img.subarray(y * p * 8, y * p * 8 + p * 4), y * p * 4)
                right.set(img.subarray(y * p * 8 + p * 4, (y + 1) * p * 8), y * p * 4)
            }
            if (this.detector.push(phaseOf(patchTone(left), patchTone(right)))) {
                const at = presentedAt ?? displayAt
                const pair = this.inputs.pairer.detect(at)
                if (pair) {
                    const sample: P2S = { at: Date.now(), source: pair.input.source, what: pair.input.what, ms: pair.ms,
                        displayMs: Math.round((displayAt - pair.input.at) * 10) / 10, pending: pair.pending }
                    this.samples.push(sample)
                    this.onSample?.(sample)
                }
            }
        } catch {
            this.sampleErrors++
        }
    }
}

// -- The per-second sampler

type AppLike = { getStream?: () => { getStats?: () => any } | null }

function device() {
    const s = window.screen
    return {
        ua: navigator.userAgent,
        screen: `${s.width}x${s.height}`,
        dpr: window.devicePixelRatio,
        viewport: `${window.innerWidth}x${window.innerHeight}`,
        shape: shapeOf(window.innerWidth, window.innerHeight),
        touchPoints: navigator.maxTouchPoints ?? 0,
    }
}

function network() {
    const c = (navigator as unknown as { connection?: { type?: string, effectiveType?: string, downlink?: number, rtt?: number, saveData?: boolean } }).connection
    return c ? { type: c.type ?? null, effectiveType: c.effectiveType ?? null, downlinkMbps: c.downlink ?? null, rttMs: c.rtt ?? null } : null
}

export class Metrics {
    readonly session = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
    readonly sink = new Sink()
    readonly inputs = new InputLog()
    readonly probe = new MarkerProbe(this.inputs)
    readonly ticks: (RtcRecord & { t: number, fpsPresented: number | null })[] = []
    private totals: RtcTotals | null = null
    private wsBytes = 0
    private lastPresented = 0
    private lastAt = 0
    private started = Date.now()
    private setup: string
    touchShown = () => false

    constructor() {
        const q = new URLSearchParams(location.search)
        let stored: string | null = null
        try { stored = localStorage.getItem("argonia.setup") } catch { /* blocked */ }
        this.setup = q.get("setup") || stored || ""
    }

    start() {
        this.inputs.listen(() => (window as unknown as { __argoniaRealPads?: () => Gamepad[] }).__argoniaRealPads?.() ?? [])
        void this.probe.loadGeometry(this.sink.url)
        setInterval(() => void this.probe.loadGeometry(this.sink.url), 10_000) // the host desktop is resized by its clients
        this.probe.watch()
        this.probe.onSample = (s) => this.sink.push({ kind: "p2s", v: 1, session: this.session, setup: this.setupLabel(), t: s.at, source: s.source, what: s.what, ms: s.ms, displayMs: s.displayMs, pending: s.pending })
        const q = new URLSearchParams(location.search)
        this.sink.push({ kind: "session", v: 1, session: this.session, setup: this.setupLabel(), t: Date.now(), client: CLIENT_VERSION, page: location.pathname,
            query: Object.fromEntries([...q].filter(([k]) => !/pass|token|key/i.test(k))), device: device(), net: network() })
        setInterval(() => void this.tick(), 1000)
        setInterval(() => this.summary(false), 60_000)
        window.addEventListener("pagehide", () => this.summary(true))
    }

    private transport(): "webrtc" | "websocket" | null {
        if (peers.some((p) => p.connectionState === "connected")) return "webrtc"
        if (sockets.some((s) => s.ws.readyState === WebSocket.OPEN)) return "websocket"
        return null
    }

    private setupLabel() { return this.setup || `mlw-${this.transport() ?? "none"}` }

    async tick() {
        const now = performance.now()
        const transport = this.transport()
        let rec: RtcRecord | null = null
        let upstream: Record<string, unknown> | null = null
        if (transport === "webrtc") {
            const pc = [...peers].reverse().find((p) => p.connectionState === "connected")!
            try {
                const report = await pc.getStats()
                const r = rtcRecord(report.values(), this.totals, now)
                rec = r.record
                this.totals = r.totals
            } catch { /* closed between the check and the call */ }
        } else if (transport === "websocket") {
            // no getStats() on this path: bytes from our socket hook, round trip and decode from upstream's own stats
            const bytes = sockets.reduce((a, s) => a + s.bytes, 0)
            const dt = this.lastAt ? (now - this.lastAt) / 1000 : 0
            rec = { rttMs: null, jitterMs: null, jitterBufferMs: null, lossPct: null, packetsLost: null, bitrateKbps: dt ? Math.round((bytes - this.wsBytes) * 8 / 1000 / dt) : null,
                fps: null, decodeMs: null, framesDropped: null, framesDroppedTotal: null, resolution: null, codec: null, candidate: null, availableInKbps: null }
            this.wsBytes = bytes
            try {
                const stats = (window as unknown as { app?: AppLike }).app?.getStream?.()?.getStats?.()
                const t = await stats?.transport?.getStats?.()
                const v: Record<string, unknown> = {}
                stats?.videoPipe?.reportStats?.(v)
                upstream = { ...t, ...v }
                if (typeof t?.relayToClientRttMs === "number") rec.rttMs = Math.round(t.relayToClientRttMs * 10) / 10
                if (typeof t?.codec === "string") rec.codec = t.codec
                const m = typeof t?.resolution === "string" ? /Width: (\d+), Height: (\d+)/.exec(t.resolution) : null
                if (m) rec.resolution = `${m[1]}x${m[2]}`
            } catch { /* upstream internals moved */ }
        }
        // presented frames, from the video element (both paths)
        const video = document.querySelector<HTMLVideoElement>("video.video-stream")
        let fpsPresented: number | null = null
        const q = video?.getVideoPlaybackQuality?.()
        if (q && this.lastAt) {
            fpsPresented = Math.round((q.totalVideoFrames - q.droppedVideoFrames - this.lastPresented) / ((now - this.lastAt) / 1000) * 10) / 10
        }
        if (q) this.lastPresented = q.totalVideoFrames - q.droppedVideoFrames
        this.lastAt = now
        const inputs = this.inputs.take()
        const p2s = this.probe.samples.filter((s) => s.at > Date.now() - 1000).map((s) => s.ms)
        const tick = { ...(rec ?? {}), t: Date.now(), fpsPresented } as RtcRecord & { t: number, fpsPresented: number | null }
        if (rec) this.ticks.push(tick)
        this.sink.push({
            kind: "tick", v: 1, session: this.session, setup: this.setupLabel(), transport, ...tick,
            net: network(), device: { viewport: `${window.innerWidth}x${window.innerHeight}`, shape: shapeOf(window.innerWidth, window.innerHeight) },
            input: inputs.source, presses: inputs.presses, touchShown: this.touchShown(),
            marker: { frames: this.probe.frames, detections: this.probe.detector.detections, errors: this.probe.sampleErrors }, p2s,
            ...(upstream ? { upstream } : {}),
        })
        if (this.ticks.length > 7200) this.ticks.splice(0, this.ticks.length - 7200)
    }

    summary(final: boolean) {
        const t = this.ticks
        const pick = (f: keyof (typeof t)[number]) => summarize(t.map((r) => r[f] as number | null))
        this.sink.push({
            kind: "summary", v: 1, final, session: this.session, setup: this.setupLabel(), t: Date.now(), durationS: Math.round((Date.now() - this.started) / 1000),
            device: device(), net: network(), transport: this.transport(), ticks: t.length,
            rttMs: pick("rttMs"), jitterMs: pick("jitterMs"), lossPct: pick("lossPct"), bitrateKbps: pick("bitrateKbps"), fps: pick("fps"),
            fpsPresented: pick("fpsPresented"), decodeMs: pick("decodeMs"), framesDropped: pick("framesDropped"),
            p2sMs: summarize(this.probe.samples.map((s) => s.ms)),
            p2sBySource: Object.fromEntries(["touch", "gamepad", "keyboard", "mouse"].map((k) => [k, summarize(this.probe.samples.filter((s) => s.source === k).map((s) => s.ms))])),
            resolution: t.at(-1)?.resolution ?? null, codec: t.at(-1)?.codec ?? null, candidate: t.at(-1)?.candidate ?? null,
        })
        if (final) void this.sink.flush()
    }
}
