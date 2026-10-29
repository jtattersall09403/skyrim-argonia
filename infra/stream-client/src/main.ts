// Our client page's additions to Moonlight-Web's stream page (chunk 0.0 §c). Loaded by stream.html before
// upstream's stream.js, so the Gamepad API and transport hooks are in place before upstream reads them.

import { VirtualPad } from "./virtual_pad.ts"
import { TouchLayer } from "./touch_layer.ts"
import { Metrics, installTransportHooks, CLIENT_VERSION } from "./metrics.ts"
import { applyStreamSettings, capturePointerOnClick, videoBacklogged, SCALE_KEY, MIN_SCALE } from "./stream_settings.ts"

// before upstream's stream.js reads its settings: a stream sized to this screen, relative mouse
const streamSize = applyStreamSettings()
capturePointerOnClick()

const pad = new VirtualPad()
installTransportHooks()
const w = window as unknown as Record<string, unknown>
w.__argoniaRealPads = () => pad.realPads()

function boot() {
    const metrics = new Metrics()
    const layer = new TouchLayer(pad, {
        onPress: (id, at) => metrics.inputs.press("touch", id, at),
        onActivity: () => metrics.inputs.active("touch"),
    })
    metrics.touchShown = () => layer.isShown()
    metrics.unmappedPads = () => pad.unmappedPads
    metrics.start()
    // The video-backlog guard: if the decoder cannot keep up, the video drifts seconds behind the sound and never
    // catches up. Reconnect (the game keeps running) with a stream 0.7x the size, down to MIN_SCALE.
    const guard = window.setInterval(() => {
        if (!videoBacklogged(metrics.ticks.map((r) => r.jitterBufferMs))) return
        const next = Math.max(MIN_SCALE, streamSize.scale * 0.7)
        if (next >= streamSize.scale) { window.clearInterval(guard); return }
        try { sessionStorage.setItem(SCALE_KEY, String(next)) } catch { return }
        window.clearInterval(guard)
        location.reload()
    }, 1000)
    w.argonia = { version: CLIENT_VERSION, pad, layer, metrics, streamSize }
}

if (document.body) boot()
else document.addEventListener("DOMContentLoaded", boot)
