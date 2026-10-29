// Our client page's additions to Moonlight-Web's stream page (chunk 0.0 §c). Loaded by stream.html before
// upstream's stream.js, so the Gamepad API and transport hooks are in place before upstream reads them.

import { VirtualPad } from "./virtual_pad.ts"
import { TouchLayer } from "./touch_layer.ts"
import { Metrics, installTransportHooks, CLIENT_VERSION } from "./metrics.ts"
import { applyStreamSettings, capturePointerOnClick } from "./stream_settings.ts"

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
    metrics.start()
    w.argonia = { version: CLIENT_VERSION, pad, layer, metrics, streamSize }
}

if (document.body) boot()
else document.addEventListener("DOMContentLoaded", boot)
